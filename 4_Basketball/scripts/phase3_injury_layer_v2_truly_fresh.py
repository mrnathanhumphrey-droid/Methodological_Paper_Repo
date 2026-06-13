"""Phase 3 injury layer v2 — truly-fresh filter.

For each (team, game N):
  1. Identify team's previous game N-1 (the game before this one, same team)
  2. Find players who played N-1 with positive minutes (in_box_N_minus_1 set)
  3. Find players who are in injury feed with OUT events dated in (N-1, N] OR currently OUT-status
     AND NOT in this game N's box scores
  4. truly_fresh_set = (in_box_N_minus_1) AND (out_event_between_or_currently_out) AND (NOT in_box_N)
  5. For each truly-fresh player, use their pre-game-N rolling 5g MPG × per-min PTS as expected loss
  6. Sum to get fresh-OUT team production loss for this game

Validation: rerun walk-forward backtest, compare to base 65.31%.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from pathlib import Path

PQ = Path("data/parquet")
OUT_DIR = Path("audit_runs/walkforward_injury_layer_v2")
OUT_DIR.mkdir(parents=True, exist_ok=True)

KEEP_SEASONS = ["2018-19", "2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]
ALPHA = 0.10
MIN_GAMES_FOR_SRS = 5
W_SRS = 0.60
OUT_STATUSES = {"out_indefinitely", "placed_on_il"}
RETURN_STATUSES = {"activated_from_il", "returned_to_lineup"}


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
    try:
        r = np.linalg.solve(A_reg, m)
    except np.linalg.LinAlgError:
        return None
    r = r - r.mean()
    return {teams[i]: float(r[i]) for i in range(n)}


def home_court_advantage(tg):
    out = {}
    for s, g in tg.groupby("season"):
        h = g[g["is_home"]].set_index("game_id")["pts"]
        a = g[~g["is_home"]].set_index("game_id")["pts"]
        out[s] = float((h - a).dropna().mean())
    return out


def build_truly_fresh_layer(box, inj):
    """For each (team, game_date), compute pre-game rolling per-min PTS for players who:
       - played in team's previous game with positive minutes
       - have an OUT event during the window (prev_game_date, game_date]
       - did NOT play in current game's box

    Returns per-team-game DataFrame with fresh_out_pts_loss column.
    """
    box = box.sort_values(["nba_api_id", "game_date"]).copy()
    box["pts_per_min"] = np.where(box["minutes"] > 0, box["PTS"] / box["minutes"], np.nan)
    grp = box.groupby("nba_api_id")
    box["roll_ppm"] = grp["pts_per_min"].transform(
        lambda x: x.shift().rolling(5, min_periods=2).mean())
    box["roll_mpg"] = grp["minutes"].transform(
        lambda x: x.shift().rolling(5, min_periods=2).mean())

    # Build team game schedule
    team_schedule = box[["team_abbr", "game_date"]].drop_duplicates().sort_values(
        ["team_abbr", "game_date"]).reset_index(drop=True)
    team_schedule["prev_game_date"] = team_schedule.groupby("team_abbr")["game_date"].shift(1)

    # OUT events: (player, team, out_date)
    inj_out = inj[inj["relinquished_status"].isin(OUT_STATUSES)].dropna(subset=["nba_api_id"]).copy()
    inj_out["event_date"] = pd.to_datetime(inj_out["event_date"])
    inj_out = inj_out[["nba_api_id", "team_abbr", "event_date"]].rename(
        columns={"event_date": "out_date"})
    print(f"  OUT events in feed: {len(inj_out)}")

    # For each (team, game_date) in team_schedule, build sets
    print("  Iterating team-game records ...")
    box_indexed = box.set_index(["team_abbr", "game_date"])
    inj_indexed = inj_out.groupby(["team_abbr"])

    fresh_records = []
    for _, row in team_schedule.iterrows():
        team = row["team_abbr"]
        game_date = row["game_date"]
        prev_date = row["prev_game_date"]
        if pd.isna(prev_date):
            fresh_records.append({
                "team_abbr": team, "game_date": game_date,
                "truly_fresh_out_pts_loss": 0.0, "truly_fresh_count": 0,
            })
            continue

        # Players in N-1 box (with positive minutes + valid rolling stats)
        prev_box = box[(box["team_abbr"] == team) & (box["game_date"] == prev_date) &
                       (box["minutes"] > 0)]
        prev_player_ids = set(prev_box["nba_api_id"].unique())

        # Players in N box (filter out so we only count truly absent)
        curr_box = box[(box["team_abbr"] == team) & (box["game_date"] == game_date)]
        curr_player_ids = set(curr_box["nba_api_id"].unique())

        # Players who played N-1 but not N
        missing_today = prev_player_ids - curr_player_ids

        # Filter to those with OUT event between (prev_date, game_date]
        try:
            team_out_events = inj_indexed.get_group(team)
        except KeyError:
            team_out_events = pd.DataFrame(columns=["nba_api_id", "team_abbr", "out_date"])

        if len(team_out_events) == 0:
            fresh_records.append({
                "team_abbr": team, "game_date": game_date,
                "truly_fresh_out_pts_loss": 0.0, "truly_fresh_count": 0,
            })
            continue

        # Events in window
        window_events = team_out_events[(team_out_events["out_date"] > prev_date) &
                                         (team_out_events["out_date"] <= game_date)]
        fresh_out_ids = set(window_events["nba_api_id"].unique()) & missing_today

        if len(fresh_out_ids) == 0:
            fresh_records.append({
                "team_abbr": team, "game_date": game_date,
                "truly_fresh_out_pts_loss": 0.0, "truly_fresh_count": 0,
            })
            continue

        # Sum their last-N-1 roll_mpg × roll_ppm contribution
        loss = 0.0
        for pid in fresh_out_ids:
            player_prev = prev_box[prev_box["nba_api_id"] == pid]
            if len(player_prev) == 0:
                continue
            r = player_prev.iloc[0]
            if pd.isna(r["roll_mpg"]) or pd.isna(r["roll_ppm"]):
                continue
            loss += r["roll_mpg"] * r["roll_ppm"]

        fresh_records.append({
            "team_abbr": team, "game_date": game_date,
            "truly_fresh_out_pts_loss": loss,
            "truly_fresh_count": len(fresh_out_ids),
        })

    return pd.DataFrame(fresh_records)


def main():
    print("Loading box + injuries ...")
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box = box[(box["season_type"] == "Regular Season") & (box["season"].isin(KEEP_SEASONS))].copy()
    box["game_date"] = pd.to_datetime(box["game_date"])

    inj = pd.read_parquet(PQ / "pro_sports_injuries.parquet")

    print()
    print("=" * 70)
    print("Building truly-fresh injury layer ...")
    print("=" * 70)
    fout = build_truly_fresh_layer(box, inj)
    fout.to_csv(OUT_DIR / "truly_fresh_per_team_game.csv", index=False)

    print()
    print("Truly-fresh-OUT distribution per team-game:")
    print(fout["truly_fresh_out_pts_loss"].describe())
    n_any = (fout["truly_fresh_count"] > 0).sum()
    print(f"Team-games with truly-fresh OUT: {n_any} ({n_any / len(fout):.2%})")
    print(f"Mean PTS loss (when any): {fout[fout['truly_fresh_count'] > 0]['truly_fresh_out_pts_loss'].mean():.3f}")

    # Build base prediction model
    print()
    print("Building base model (Tier 1B+EMA + SRS blend) ...")
    tg = aggregate_team_game(box)
    tg = attach_opp(tg)
    tg = tg.sort_values(["season", "game_date", "game_id"]).reset_index(drop=True)
    hc_per_season = home_court_advantage(tg)
    tg["hc_half"] = tg["season"].map({s: v / 2 for s, v in hc_per_season.items()})

    tg = add_ema(tg, ALPHA)
    tg = attach_opp_ema(tg)

    print("Computing SRS ...")
    srs_lookup = {}
    for season in KEEP_SEASONS:
        season_tg = tg[tg["season"] == season]
        dates = sorted(season_tg["game_date"].unique())
        for d in dates:
            before = season_tg[season_tg["game_date"] < d]
            counts = before.groupby("team_abbr").size()
            if len(counts) < 28 or (counts < MIN_GAMES_FOR_SRS).any():
                continue
            sol = solve_srs(before)
            if sol is not None:
                srs_lookup[(season, d)] = sol

    def get_srs(row, which):
        s = srs_lookup.get((row["season"], row["game_date"]), {})
        return s.get(row[which], np.nan)

    tg["r_team"] = tg.apply(lambda r: get_srs(r, "team_abbr"), axis=1)
    tg["r_opp"] = tg.apply(lambda r: get_srs(r, "opp_team"), axis=1)
    sign = np.where(tg["is_home"], 1, -1)
    tg["srs_pred_margin"] = (tg["r_team"] - tg["r_opp"]) + sign * tg["hc_half"] * 2
    LEAGUE_AVG_PTS = tg.groupby("season")["pts"].mean().to_dict()
    tg["league_avg_pts"] = tg["season"].map(LEAGUE_AVG_PTS)
    tg["pred_pts_srs"] = tg["league_avg_pts"] + tg["srs_pred_margin"] / 2

    tg["pred_pts_ema"] = (tg["ema_ortg"] + tg["opp_ema_drtg"]) / 2 * \
                          ((tg["ema_poss"] + tg["opp_ema_poss"]) / 2) / 100 + \
                          np.where(tg["is_home"], tg["hc_half"], -tg["hc_half"])

    tg_v = tg.dropna(subset=["pred_pts_srs", "pred_pts_ema"]).copy()
    tg_v["pred_pts_base"] = W_SRS * tg_v["pred_pts_srs"] + (1 - W_SRS) * tg_v["pred_pts_ema"]

    # Merge truly-fresh OUT
    tg_v = tg_v.merge(fout, on=["team_abbr", "game_date"], how="left")
    tg_v["truly_fresh_out_pts_loss"] = tg_v["truly_fresh_out_pts_loss"].fillna(0.0)
    tg_v["truly_fresh_count"] = tg_v["truly_fresh_count"].fillna(0).astype(int)

    # Walk-forward with adjustment scales
    print()
    print("=" * 78)
    print("Walk-forward with truly-fresh injury layer")
    print("=" * 78)
    home_v = tg_v[tg_v["is_home"]].copy()
    away_v = tg_v[~tg_v["is_home"]].copy()

    def evaluate_at_scale(scale):
        h = home_v.copy()
        a = away_v.copy()
        h["pred_pts"] = h["pred_pts_base"] - scale * h["truly_fresh_out_pts_loss"]
        a["pred_pts"] = a["pred_pts_base"] - scale * a["truly_fresh_out_pts_loss"]
        g = h[["season", "game_id", "pred_pts", "pts", "truly_fresh_out_pts_loss",
               "truly_fresh_count"]].rename(
            columns={"pred_pts": "h", "pts": "ha", "truly_fresh_out_pts_loss": "h_inj",
                     "truly_fresh_count": "h_inj_n"}
        ).merge(
            a[["game_id", "pred_pts", "pts", "truly_fresh_out_pts_loss", "truly_fresh_count"]].rename(
                columns={"pred_pts": "a", "pts": "aa", "truly_fresh_out_pts_loss": "a_inj",
                         "truly_fresh_count": "a_inj_n"}),
            on="game_id", how="inner")
        g["pm"] = g["h"] - g["a"]
        g["am"] = g["ha"] - g["aa"]
        g["correct"] = (g["pm"] > 0) == (g["am"] > 0)
        return g

    print(f"  {'scale':>7} {'win_pct':>10} {'18-19':>8} {'19-20':>8} {'20-21':>8} {'21-22':>8} "
          f"{'22-23':>8} {'23-24':>8} {'24-25':>8} {'25-26':>8} {'rmse':>8}")
    for scale in [0.0, 0.3, 0.5, 0.7, 1.0, 1.3]:
        g = evaluate_at_scale(scale)
        wp_all = g["correct"].mean()
        err = g["pm"] - g["am"]
        rmse = np.sqrt((err ** 2).mean())
        wp_by_season = g.groupby("season")["correct"].mean()
        marker = "  <-- baseline" if scale == 0.0 else ""
        print(f"  {scale:>7.2f} {wp_all:>10.4f} ", end="")
        for s in KEEP_SEASONS:
            val = wp_by_season.get(s, float("nan"))
            print(f"{val:>8.4f} ", end="")
        print(f"{rmse:>8.4f}{marker}")

    # Best scale: also check restricted-subset performance
    print()
    print("=" * 78)
    print("Effect on games WITH any fresh-OUT player (the actionable subset)")
    print("=" * 78)
    g_best = evaluate_at_scale(0.5)  # try mid-scale
    has_inj = (g_best["h_inj_n"] > 0) | (g_best["a_inj_n"] > 0)
    print(f"  Games with any fresh-OUT (n={has_inj.sum()}):")
    print(f"    win_pct at scale 0.0: {evaluate_at_scale(0.0)[has_inj]['correct'].mean():.4f}")
    for s in [0.3, 0.5, 0.7, 1.0]:
        g_s = evaluate_at_scale(s)
        print(f"    win_pct at scale {s}: {g_s[has_inj]['correct'].mean():.4f}")
    print(f"  Games with NO fresh-OUT (n={(~has_inj).sum()}):")
    print(f"    win_pct at scale 0.0: {evaluate_at_scale(0.0)[~has_inj]['correct'].mean():.4f}")


if __name__ == "__main__":
    main()
