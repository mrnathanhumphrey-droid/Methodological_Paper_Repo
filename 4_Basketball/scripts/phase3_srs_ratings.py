"""Phase 3 lever #2: SRS (Simple Rating System) ratings.

For each game G:
  - Use all team-games strictly before G's date in same season
  - For each team, compute mean point-differential
  - Solve SRS: r_i = mean_margin_i + mean(r_j for j in opponents played)
  - r = (I - S)^{-1} · m  where S is row-normalized opponent matrix
  - Center so sum(r) = 0

Predict: pred_margin = r_home - r_away + home_court

Compare to current Tier 1B + EMA α=0.10 baseline (66.71% combined win pct).
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from pathlib import Path

PQ = Path("data/parquet")
SEASONS = ["2024-25", "2025-26"]
MIN_GAMES_FOR_SRS = 5  # don't predict until each team has at least 5 games


def aggregate_team_game(box):
    agg = box.groupby(["season", "game_id", "team_abbr", "game_date", "is_home"]).agg(
        pts=("PTS", "sum"),
        fga=("FGA", "sum"), fta=("FTA", "sum"), oreb=("OREB", "sum"), tov=("TOV", "sum"),
    ).reset_index()
    return agg


def attach_opponent(tg):
    opp = tg[["season", "game_id", "team_abbr", "pts"]].rename(
        columns={"team_abbr": "opp_team", "pts": "opp_pts"})
    j = tg.merge(opp, on=["season", "game_id"], how="left")
    j = j[j["team_abbr"] != j["opp_team"]].copy()
    j["margin"] = j["pts"] - j["opp_pts"]
    return j


def solve_srs(team_games_before: pd.DataFrame, regularization: float = 0.01):
    """SRS solver.
    team_games_before: rows for all (team, game) BEFORE prediction date, with team_abbr, opp_team, margin.
    Returns dict team_abbr -> rating.
    """
    teams = sorted(set(team_games_before["team_abbr"]) | set(team_games_before["opp_team"]))
    n = len(teams)
    idx = {t: i for i, t in enumerate(teams)}

    # Build A = I - S where S[i, j] = 1/n_games_i if team i played team j else 0
    A = np.eye(n)
    m = np.zeros(n)
    counts = team_games_before.groupby("team_abbr").size()
    means = team_games_before.groupby("team_abbr")["margin"].mean()

    for t, i in idx.items():
        if t in means.index:
            m[i] = means[t]
        # Build S row: for each game played, opp gets 1/n_games_i
        sub = team_games_before[team_games_before["team_abbr"] == t]
        if len(sub) > 0:
            opp_counts = sub.groupby("opp_team").size()
            n_games_t = len(sub)
            for opp, c in opp_counts.items():
                if opp in idx:
                    A[i, idx[opp]] -= c / n_games_t

    # Solve (I - S + reg*I) r = m  for numerical stability
    A_reg = A + regularization * np.eye(n)
    r = np.linalg.solve(A_reg, m)
    # Center
    r = r - r.mean()
    return {teams[i]: float(r[i]) for i in range(n)}


def main():
    print("Loading multi-season box ...")
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box = box[(box["season"].isin(SEASONS)) & (box["season_type"] == "Regular Season")].copy()
    box["game_date"] = pd.to_datetime(box["game_date"])

    tg = aggregate_team_game(box)
    tg = attach_opponent(tg)
    tg = tg.sort_values(["season", "game_date", "game_id"]).reset_index(drop=True)
    print(f"Team-games: {len(tg)}")

    # Per-season home court
    hc_per_season = {}
    for s in SEASONS:
        ss = tg[tg["season"] == s]
        h = ss[ss["is_home"]].set_index("game_id")["pts"]
        a = ss[~ss["is_home"]].set_index("game_id")["pts"]
        hc_per_season[s] = float((h - a).dropna().mean())
    print(f"Home court per season: {hc_per_season}")

    # For each unique (season, game_date), compute SRS once from all prior games
    print("Computing SRS at each unique date ...")
    unique_dates = tg[["season", "game_date"]].drop_duplicates().sort_values(["season", "game_date"])
    print(f"  Unique dates: {len(unique_dates)}")

    srs_lookup = {}  # (season, game_date) -> {team: rating}
    for season in SEASONS:
        season_tg = tg[tg["season"] == season].copy()
        dates = sorted(season_tg["game_date"].unique())
        for d in dates:
            before = season_tg[season_tg["game_date"] < d]
            if len(before) == 0:
                continue
            counts = before.groupby("team_abbr").size()
            if (counts < MIN_GAMES_FOR_SRS).any() or len(counts) < 30:
                continue
            try:
                srs = solve_srs(before)
                srs_lookup[(season, d)] = srs
            except np.linalg.LinAlgError:
                continue
        print(f"  {season}: {sum(1 for k in srs_lookup if k[0] == season)} dates with SRS")

    # Predict each game using SRS as of its date
    print("Building predictions ...")
    preds = []
    for _, row in tg.iterrows():
        key = (row["season"], row["game_date"])
        if key not in srs_lookup:
            continue
        srs = srs_lookup[key]
        if row["team_abbr"] not in srs or row["opp_team"] not in srs:
            continue
        r_team = srs[row["team_abbr"]]
        r_opp = srs[row["opp_team"]]
        hc = hc_per_season[row["season"]]
        # Predict from THIS team's perspective: margin = r_team - r_opp ± home_court/2
        sign = 1 if row["is_home"] else -1
        pred_margin = r_team - r_opp + sign * (hc / 2) * 2
        # Predict team's PTS via implied: actually we don't predict pts here, only margin
        # For margin RMSE we use pred_margin directly
        preds.append({
            "season": row["season"], "game_id": row["game_id"],
            "team_abbr": row["team_abbr"], "is_home": row["is_home"],
            "pts": row["pts"], "margin": row["margin"],
            "r_team": r_team, "r_opp": r_opp, "pred_margin": pred_margin,
        })

    pred_df = pd.DataFrame(preds)
    print(f"Predictable team-games: {len(pred_df)}")

    # Aggregate to game-level. Just use HOME row's pred_margin = home perspective.
    home_pred = pred_df[pred_df["is_home"]].copy()
    home_pred = home_pred.rename(columns={"margin": "actual_margin"})
    home_pred["correct"] = (home_pred["pred_margin"] > 0) == (home_pred["actual_margin"] > 0)
    home_pred["err"] = home_pred["pred_margin"] - home_pred["actual_margin"]

    # Per-season + combined
    print()
    print("=" * 75)
    print("SRS-based game prediction")
    print("=" * 75)
    for s in SEASONS + ["combined"]:
        sub = home_pred if s == "combined" else home_pred[home_pred["season"] == s]
        if len(sub) == 0:
            continue
        rmse = np.sqrt((sub["err"] ** 2).mean())
        print(f"\n{s} (n={len(sub)} games):")
        print(f"  Margin RMSE: {rmse:.4f}  MAE: {sub['err'].abs().mean():.4f}  bias: {sub['err'].mean():+.4f}")
        print(f"  Win pct:     {sub['correct'].mean():.2%}")


if __name__ == "__main__":
    main()
