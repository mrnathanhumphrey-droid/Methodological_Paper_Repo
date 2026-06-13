"""Walk-forward backtest of locked model (60% SRS + 40% Tier 1B+EMA alpha=0.10) over all
available seasons in historical_box_scores.parquet.

Each season is validated INDEPENDENTLY using within-season rolling/SRS (no cross-season
leakage). Walk-forward in the strict sense: at each game G in season S, predictions use
only game data with game_date < G's date within season S.

Per-season + combined metrics: win pct, margin RMSE, team PTS MAE, home-court advantage.
Outputs:
  audit_runs/walkforward_allseasons/per_game_predictions.csv
  audit_runs/walkforward_allseasons/per_season_summary.csv
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from pathlib import Path

PQ = Path("data/parquet")
OUT_DIR = Path("audit_runs/walkforward_allseasons")
OUT_DIR.mkdir(parents=True, exist_ok=True)

ALPHA = 0.10
MIN_GAMES_FOR_SRS = 5
SRS_REG = 0.01
W_SRS = 0.60


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
    cols = ["ema_ortg", "ema_drtg", "ema_poss"]
    opp = df[["season", "game_id", "team_abbr"] + cols].rename(
        columns={"team_abbr": "opp_team", **{c: f"opp_{c}" for c in cols}})
    return df.merge(opp, on=["season", "game_id", "opp_team"], how="left")


def solve_srs(tg_before, reg=SRS_REG):
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
    try:
        r = np.linalg.solve(A_reg, m)
    except np.linalg.LinAlgError:
        return None
    r = r - r.mean()
    return {teams[i]: float(r[i]) for i in range(n)}


def home_court_advantage(tg):
    """Compute home court advantage per season."""
    out = {}
    for s, g in tg.groupby("season"):
        h = g[g["is_home"]].set_index("game_id")["pts"]
        a = g[~g["is_home"]].set_index("game_id")["pts"]
        out[s] = float((h - a).dropna().mean())
    return out


def main():
    print("Loading historical box scores (18-19 onward; pre-2018 is a different era) ...")
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box = box[box["season_type"] == "Regular Season"].copy()
    box["game_date"] = pd.to_datetime(box["game_date"])
    KEEP = ["2018-19", "2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]
    box = box[box["season"].isin(KEEP)].copy()
    SEASONS = sorted(box["season"].unique())
    print(f"Seasons: {SEASONS}")

    tg = aggregate_team_game(box)
    tg = attach_opp(tg)
    tg = tg.sort_values(["season", "game_date", "game_id"]).reset_index(drop=True)
    print(f"Team-games total: {len(tg)}")

    hc_per_season = home_court_advantage(tg)
    print(f"Home court per season:")
    for s, v in sorted(hc_per_season.items()):
        print(f"  {s}: {v:+.3f}")
    tg["hc_half"] = tg["season"].map({s: v / 2 for s, v in hc_per_season.items()})

    # EMA
    print("\nBuilding EMA stats ...")
    tg = add_ema(tg, ALPHA)
    tg = attach_opp_ema(tg)

    # SRS per (season, game_date)
    print("Computing SRS at each (season, date) ...")
    srs_lookup = {}
    for season in SEASONS:
        season_tg = tg[tg["season"] == season]
        dates = sorted(season_tg["game_date"].unique())
        ok = 0
        for d in dates:
            before = season_tg[season_tg["game_date"] < d]
            counts = before.groupby("team_abbr").size()
            if len(counts) < 28 or (counts < MIN_GAMES_FOR_SRS).any():
                continue
            sols = solve_srs(before)
            if sols is not None:
                srs_lookup[(season, d)] = sols
                ok += 1
        print(f"  {season}: {ok} dates with SRS solution")

    # Per-game predictions
    print("\nGenerating per-game predictions ...")

    def get_srs(row, which):
        s = srs_lookup.get((row["season"], row["game_date"]), {})
        return s.get(row[which], np.nan)

    tg["r_team"] = tg.apply(lambda r: get_srs(r, "team_abbr"), axis=1)
    tg["r_opp"] = tg.apply(lambda r: get_srs(r, "opp_team"), axis=1)

    sign = np.where(tg["is_home"], 1, -1)
    # SRS pred margin from team's perspective
    tg["srs_pred_margin"] = (tg["r_team"] - tg["r_opp"]) + sign * tg["hc_half"] * 2
    LEAGUE_AVG_PTS_PER_SEASON = tg.groupby("season")["pts"].mean().to_dict()
    tg["league_avg_pts"] = tg["season"].map(LEAGUE_AVG_PTS_PER_SEASON)
    tg["pred_pts_srs"] = tg["league_avg_pts"] + tg["srs_pred_margin"] / 2

    # EMA pred pts (additive defense + EMA pace)
    tg["pred_pts_ema"] = (tg["ema_ortg"] + tg["opp_ema_drtg"]) / 2 \
                          * ((tg["ema_poss"] + tg["opp_ema_poss"]) / 2) / 100 \
                          + np.where(tg["is_home"], tg["hc_half"], -tg["hc_half"])

    # Drop predictions that lack EMA or SRS
    tg_v = tg.dropna(subset=["pred_pts_srs", "pred_pts_ema"]).copy()

    # Locked blend
    tg_v["pred_pts"] = W_SRS * tg_v["pred_pts_srs"] + (1 - W_SRS) * tg_v["pred_pts_ema"]

    # Pivot home/away to game-level
    home = tg_v[tg_v["is_home"]].copy()
    away = tg_v[~tg_v["is_home"]].copy()
    games = home[["season", "game_id", "team_abbr", "pred_pts", "pts", "pred_pts_srs", "pred_pts_ema"]].rename(
        columns={"team_abbr": "home_team", "pred_pts": "home_pred",
                 "pts": "home_actual", "pred_pts_srs": "home_pred_srs", "pred_pts_ema": "home_pred_ema"}
    ).merge(
        away[["game_id", "team_abbr", "pred_pts", "pts", "pred_pts_srs", "pred_pts_ema"]].rename(
            columns={"team_abbr": "away_team", "pred_pts": "away_pred",
                     "pts": "away_actual", "pred_pts_srs": "away_pred_srs",
                     "pred_pts_ema": "away_pred_ema"}),
        on="game_id", how="inner")
    games["pred_margin"] = games["home_pred"] - games["away_pred"]
    games["actual_margin"] = games["home_actual"] - games["away_actual"]
    games["correct"] = (games["pred_margin"] > 0) == (games["actual_margin"] > 0)
    # Variants for inspection
    games["srs_correct"] = (games["home_pred_srs"] > games["away_pred_srs"]) == (games["actual_margin"] > 0)
    games["ema_correct"] = (games["home_pred_ema"] > games["away_pred_ema"]) == (games["actual_margin"] > 0)

    # Per-season summary
    print()
    print("=" * 100)
    print("Per-season results: 60% SRS + 40% Tier 1B+EMA (alpha=0.10) blend")
    print("=" * 100)
    print(f"{'season':<10} {'n_games':>8} {'win_pct':>10} {'srs_only':>10} {'ema_only':>10} "
          f"{'margin_rmse':>13} {'margin_mae':>12} {'home_pts_bias':>14}")
    print("-" * 100)
    rows = []
    for s in SEASONS:
        sub = games[games["season"] == s]
        if len(sub) == 0:
            continue
        err_m = sub["pred_margin"] - sub["actual_margin"]
        home_bias = (sub["home_pred"] - sub["home_actual"]).mean()
        row = {
            "season": s, "n_games": len(sub),
            "win_pct": sub["correct"].mean(),
            "srs_only_winpct": sub["srs_correct"].mean(),
            "ema_only_winpct": sub["ema_correct"].mean(),
            "margin_rmse": np.sqrt((err_m ** 2).mean()),
            "margin_mae": err_m.abs().mean(),
            "margin_bias": err_m.mean(),
            "home_pred_bias": home_bias,
            "home_court": hc_per_season[s],
        }
        rows.append(row)
        print(f"{s:<10} {row['n_games']:>8} {row['win_pct']:>10.4f} {row['srs_only_winpct']:>10.4f} "
              f"{row['ema_only_winpct']:>10.4f} {row['margin_rmse']:>13.4f} "
              f"{row['margin_mae']:>12.4f} {home_bias:>+14.3f}")

    # Combined (all seasons)
    sub = games
    err_m = sub["pred_margin"] - sub["actual_margin"]
    home_bias = (sub["home_pred"] - sub["home_actual"]).mean()
    print("-" * 100)
    print(f"{'COMBINED':<10} {len(sub):>8} {sub['correct'].mean():>10.4f} "
          f"{sub['srs_correct'].mean():>10.4f} {sub['ema_correct'].mean():>10.4f} "
          f"{np.sqrt((err_m**2).mean()):>13.4f} {err_m.abs().mean():>12.4f} {home_bias:>+14.3f}")

    summary = pd.DataFrame(rows)
    summary.to_csv(OUT_DIR / "per_season_summary.csv", index=False)
    games.to_csv(OUT_DIR / "per_game_predictions.csv", index=False)
    print(f"\nWrote: {OUT_DIR}/per_game_predictions.csv ({len(games)} games)")
    print(f"Wrote: {OUT_DIR}/per_season_summary.csv ({len(summary)} seasons)")


if __name__ == "__main__":
    main()
