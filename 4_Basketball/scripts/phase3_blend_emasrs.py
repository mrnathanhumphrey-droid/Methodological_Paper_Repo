"""Phase 3: blend Tier 1B+EMA with SRS predictions.

EMA captures recency (half-life 6.6g, single team snapshot).
SRS captures strength-of-schedule (all prior games, no recency weight).

Hypothesis: combining gives both signals' strengths. Test blend weight grid.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from pathlib import Path

PQ = Path("data/parquet")
SEASONS = ["2024-25", "2025-26"]
ALPHA = 0.10
MIN_GAMES_FOR_SRS = 5


def aggregate_team_game(box):
    agg = box.groupby(["season", "game_id", "team_abbr", "game_date", "is_home"]).agg(
        pts=("PTS", "sum"),
        fga=("FGA", "sum"), fta=("FTA", "sum"),
        oreb=("OREB", "sum"), tov=("TOV", "sum"),
    ).reset_index()
    agg["poss"] = agg["fga"] + 0.44 * agg["fta"] - agg["oreb"] + agg["tov"]
    agg["ortg"] = agg["pts"] / agg["poss"] * 100
    return agg


def attach_opp(tg):
    opp = tg[["season", "game_id", "team_abbr", "pts", "poss"]].rename(
        columns={"team_abbr": "opp_team", "pts": "opp_pts", "poss": "opp_poss"})
    j = tg.merge(opp, on=["season", "game_id"], how="left")
    j = j[j["team_abbr"] != j["opp_team"]].copy()
    j["drtg"] = j["opp_pts"] / j["opp_poss"] * 100
    j["margin"] = j["pts"] - j["opp_pts"]
    return j


def add_ema(df, alpha):
    df = df.sort_values(["season", "team_abbr", "game_date"]).copy()
    grp = df.groupby(["season", "team_abbr"])
    for c in ["ortg", "drtg", "poss"]:
        df[f"ema_{c}"] = grp[c].transform(
            lambda x: x.shift().ewm(alpha=alpha, min_periods=3, adjust=False).mean())
    return df


def attach_opp_ema(df):
    opp = df[["season", "game_id", "team_abbr", "ema_ortg", "ema_drtg", "ema_poss"]].rename(
        columns={"team_abbr": "opp_team",
                 "ema_ortg": "opp_ema_ortg", "ema_drtg": "opp_ema_drtg", "ema_poss": "opp_ema_poss"})
    return df.merge(opp, on=["season", "game_id", "opp_team"], how="left")


def solve_srs(tg_before, reg=0.01):
    teams = sorted(set(tg_before["team_abbr"]) | set(tg_before["opp_team"]))
    n = len(teams)
    idx = {t: i for i, t in enumerate(teams)}
    A = np.eye(n)
    m = np.zeros(n)
    means = tg_before.groupby("team_abbr")["margin"].mean()
    for t, i in idx.items():
        if t in means.index:
            m[i] = means[t]
        sub = tg_before[tg_before["team_abbr"] == t]
        if len(sub) > 0:
            opp_counts = sub.groupby("opp_team").size()
            n_t = len(sub)
            for opp, c in opp_counts.items():
                if opp in idx:
                    A[i, idx[opp]] -= c / n_t
    A_reg = A + reg * np.eye(n)
    r = np.linalg.solve(A_reg, m)
    r = r - r.mean()
    return {teams[i]: float(r[i]) for i in range(n)}


def main():
    print("Loading multi-season box ...")
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box = box[(box["season"].isin(SEASONS)) & (box["season_type"] == "Regular Season")].copy()
    box["game_date"] = pd.to_datetime(box["game_date"])

    tg = aggregate_team_game(box)
    tg = attach_opp(tg)
    tg = tg.sort_values(["season", "game_date", "game_id"]).reset_index(drop=True)

    hc_per_season = {}
    for s in SEASONS:
        ss = tg[tg["season"] == s]
        h = ss[ss["is_home"]].set_index("game_id")["pts"]
        a = ss[~ss["is_home"]].set_index("game_id")["pts"]
        hc_per_season[s] = float((h - a).dropna().mean())
    print(f"HC per season: {hc_per_season}")

    # 1. Build EMA predictions
    tg_ema = add_ema(tg, ALPHA)
    tg_ema = attach_opp_ema(tg_ema)
    tg_ema = tg_ema.dropna(subset=["ema_ortg", "ema_drtg", "ema_poss",
                                    "opp_ema_ortg", "opp_ema_drtg", "opp_ema_poss"]).copy()
    tg_ema["hc_half"] = tg_ema["season"].map({s: v / 2 for s, v in hc_per_season.items()})
    tg_ema["game_pace"] = (tg_ema["ema_poss"] + tg_ema["opp_ema_poss"]) / 2
    tg_ema["team_eff"] = (tg_ema["ema_ortg"] + tg_ema["opp_ema_drtg"]) / 2
    tg_ema["pred_pts_ema"] = tg_ema["team_eff"] * tg_ema["game_pace"] / 100 + np.where(
        tg_ema["is_home"], tg_ema["hc_half"], -tg_ema["hc_half"])

    # 2. Build SRS predictions per game_date
    print("Computing SRS at each date ...")
    srs_lookup = {}
    for season in SEASONS:
        season_tg = tg[tg["season"] == season]
        dates = sorted(season_tg["game_date"].unique())
        for d in dates:
            before = season_tg[season_tg["game_date"] < d]
            counts = before.groupby("team_abbr").size()
            if len(counts) < 30 or (counts < MIN_GAMES_FOR_SRS).any():
                continue
            try:
                srs_lookup[(season, d)] = solve_srs(before)
            except np.linalg.LinAlgError:
                continue

    # Attach SRS team and opp ratings
    def get_srs_rating(row, which):
        key = (row["season"], row["game_date"])
        s = srs_lookup.get(key, {})
        return s.get(row[which], np.nan)

    tg_ema["r_team"] = tg_ema.apply(lambda r: get_srs_rating(r, "team_abbr"), axis=1)
    tg_ema["r_opp"] = tg_ema.apply(lambda r: get_srs_rating(r, "opp_team"), axis=1)

    # SRS pred_margin from team's perspective:
    # pred_margin = r_team - r_opp + (home_court if home else -home_court)
    sign = np.where(tg_ema["is_home"], 1, -1)
    tg_ema["srs_pred_margin"] = (tg_ema["r_team"] - tg_ema["r_opp"]) + sign * tg_ema["hc_half"] * 2  # full hc, not half
    # Convert SRS margin to team_pts equivalent: team_pts_srs = (game_pace * 110 / 100) + srs_pred_margin / 2
    # Simpler: predict team_pts as (own + opp) / 2 + srs_margin / 2 where (own + opp) / 2 = total / 2
    # league avg total per team ≈ 115. Use 115 + srs_margin/2
    LEAGUE_AVG_PTS = float(tg_ema["pts"].mean())
    tg_ema["pred_pts_srs"] = LEAGUE_AVG_PTS + tg_ema["srs_pred_margin"] / 2

    # Drop rows without SRS
    tg_with_srs = tg_ema.dropna(subset=["pred_pts_srs"]).copy()
    print(f"Predictable team-games: {len(tg_with_srs)}")

    # 3. Blend grid
    def evaluate_blend(df, w_srs):
        df = df.copy()
        df["pred_pts_blend"] = (1 - w_srs) * df["pred_pts_ema"] + w_srs * df["pred_pts_srs"]
        df["err"] = df["pred_pts_blend"] - df["pts"]
        home = df[df["is_home"]].copy()
        away = df[~df["is_home"]].copy()
        g = home[["season", "game_id", "pred_pts_blend", "pts"]].rename(
            columns={"pred_pts_blend": "h", "pts": "ha"}).merge(
            away[["game_id", "pred_pts_blend", "pts"]].rename(
                columns={"pred_pts_blend": "a", "pts": "aa"}),
            on="game_id", how="inner")
        g["pm"] = g["h"] - g["a"]
        g["am"] = g["ha"] - g["aa"]
        g["c"] = (g["pm"] > 0) == (g["am"] > 0)
        return {
            "w_srs": w_srs,
            "n": len(g),
            "team_pts_mae": df["err"].abs().mean(),
            "margin_rmse": float(np.sqrt(((g["pm"] - g["am"]) ** 2).mean())),
            "win_pct": float(g["c"].mean()),
            "g_24": float(g[g["season"] == "2024-25"]["c"].mean()) if (g["season"] == "2024-25").any() else float("nan"),
            "g_25": float(g[g["season"] == "2025-26"]["c"].mean()) if (g["season"] == "2025-26").any() else float("nan"),
        }

    print()
    print("=" * 80)
    print("Blend grid: w_srs * SRS + (1 - w_srs) * Tier 1B+EMA")
    print("=" * 80)
    print(f"  {'w_srs':>6} {'win_combined':>13} {'win_24-25':>10} {'win_25-26':>10} {'rmse':>9} {'team_mae':>9}")
    results = []
    for w in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        r = evaluate_blend(tg_with_srs, w)
        results.append(r)
        marker = ""
        if w == 0.0:
            marker = "  <-- pure EMA"
        elif w == 1.0:
            marker = "  <-- pure SRS"
        print(f"  {w:>6.2f} {r['win_pct']:>13.4f} {r['g_24']:>10.4f} {r['g_25']:>10.4f} {r['margin_rmse']:>9.4f} {r['team_pts_mae']:>9.4f}{marker}")

    df_res = pd.DataFrame(results)
    best_win = df_res.loc[df_res["win_pct"].idxmax()]
    print()
    print(f"BEST blend (win pct): w_srs={best_win['w_srs']:.2f} -> {best_win['win_pct']:.4f}")
    best_rmse = df_res.loc[df_res["margin_rmse"].idxmin()]
    print(f"BEST blend (RMSE):    w_srs={best_rmse['w_srs']:.2f} -> {best_rmse['margin_rmse']:.4f}")


if __name__ == "__main__":
    main()
