"""Ablation: roster composition change (Desktop's #1 priority lever).

For each player p in 23-24 cohort:
  position(p) = from player_metadata_enriched (Guard/Forward/Center)
  team(p, 23-24) = first team appearance in 23-24 box scores (post-trade)

  same_pos_departed = players who were on team(p) in 22-23 but NOT in 23-24,
                       at the same position. Sum their 22-23 mpg.

  same_pos_arrived = players who were NOT on team(p) in 22-23 but ARE in 23-24,
                       at the same position. Sum their 22-23 mpg (their threat).

  net_position_churn = same_pos_departed - same_pos_arrived
                       (positive = more minutes available; negative = more competition)

Sweep beta over the harness, then jointly with preseason_blend + trade_dampen.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
from ablation_harness import load_baseline, run_ablation, per_stat_mae

REPO = Path(".")
PQ = REPO / "data" / "parquet"


def parse_min(x):
    if pd.isna(x): return np.nan
    s = str(x)
    if ":" in s:
        try:
            a, b = s.split(":")
            return float(a) + float(b) / 60.0
        except Exception:
            return np.nan
    try:
        return float(s)
    except Exception:
        return np.nan


def build_player_position_map():
    """nba_api_id -> 'Guard'|'Forward'|'Center' from metadata."""
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    return dict(zip(meta["nba_api_id"].astype(int),
                    meta["position"]))


def build_team_seasons_from_box():
    """Returns dict (player_id -> {season -> [team_abbr, mpg, total_min, gp]})."""
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["minutes"] = pd.to_numeric(box["minutes"], errors="coerce")
    box = box.dropna(subset=["minutes"])
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    # Per (player, season, team) aggregate
    agg = box.groupby(["nba_api_id", "season", "team_abbr"]).agg(
        gp=("game_id", "nunique"),
        total_min=("minutes", "sum"),
    ).reset_index()
    agg["mpg"] = agg["total_min"] / agg["gp"]
    return agg


def build_offseason_churn(box_player_team, position_map):
    """Per (team, position) compute departed_mpg and arrived_mpg between 22-23 and 23-24.

    A player "departed team T" if they appeared in T's 22-23 roster but not in T's 23-24 roster.
    Their value is their 22-23 mpg on T (only counting if they played meaningful min).
    """
    # 22-23 roster per team (player, mpg-on-team)
    s22 = box_player_team[box_player_team["season"] == "2022-23"].copy()
    s23 = box_player_team[box_player_team["season"] == "2023-24"].copy()

    # For each player, find their dominant team per season (most games)
    s22 = s22.sort_values("gp", ascending=False).drop_duplicates("nba_api_id").rename(
        columns={"team_abbr": "team_22", "mpg": "mpg_22", "gp": "gp_22", "total_min": "min_22"})
    s23 = s23.sort_values("gp", ascending=False).drop_duplicates("nba_api_id").rename(
        columns={"team_abbr": "team_23", "mpg": "mpg_23", "gp": "gp_23", "total_min": "min_23"})
    s22 = s22[["nba_api_id", "team_22", "mpg_22", "gp_22", "min_22"]]
    s23 = s23[["nba_api_id", "team_23", "mpg_23", "gp_23", "min_23"]]

    # Outer join
    j = s22.merge(s23, on="nba_api_id", how="outer")

    # Position lookup
    j["position"] = j["nba_api_id"].astype(int).map(position_map)

    # Departure: player on team_22 but team_23 != team_22 (or absent in 23-24)
    j["departed_from"] = np.where((j["team_22"].notna()) &
                                   (j["team_22"] != j["team_23"]),
                                   j["team_22"], None)
    # Arrival: on team_23 but team_22 != team_23 (or absent in 22-23)
    j["arrived_at"] = np.where((j["team_23"].notna()) &
                                (j["team_22"] != j["team_23"]),
                                j["team_23"], None)

    # Filter to meaningful contributors (>= 200 min in 22-23 to count as departure threat)
    departures = j[(j["departed_from"].notna()) &
                   (j["min_22"] >= 200.0) &
                   (j["position"].notna())].copy()
    # Same for arrivals — what they brought from 22-23 (or previous season if rookie)
    arrivals = j[(j["arrived_at"].notna()) &
                 (j["min_22"] >= 200.0) &
                 (j["position"].notna())].copy()

    # Aggregate by (team, position)
    dep_agg = departures.groupby(["departed_from", "position"]).agg(
        departed_mpg=("mpg_22", "sum"),
        n_departed=("nba_api_id", "count"),
    ).reset_index().rename(columns={"departed_from": "team"})

    arr_agg = arrivals.groupby(["arrived_at", "position"]).agg(
        arrived_mpg=("mpg_22", "sum"),
        n_arrived=("nba_api_id", "count"),
    ).reset_index().rename(columns={"arrived_at": "team"})

    churn = dep_agg.merge(arr_agg, on=["team", "position"], how="outer").fillna(0)
    churn["net_churn_mpg"] = churn["departed_mpg"] - churn["arrived_mpg"]

    return churn, j


def build_player_team_2324(box_player_team):
    """Player -> their dominant team in 23-24."""
    s23 = box_player_team[box_player_team["season"] == "2023-24"].copy()
    s23 = s23.sort_values("gp", ascending=False).drop_duplicates("nba_api_id")
    return dict(zip(s23["nba_api_id"].astype(int), s23["team_abbr"]))


def build_churn_adjustment(base, position_map, team_2324_map, churn_df, beta):
    """For each player: adjustment = beta * net_churn(team, position)."""
    churn_lookup = {(r["team"], r["position"]): r["net_churn_mpg"]
                    for _, r in churn_df.iterrows()}
    adj = {}
    for _, row in base.iterrows():
        pid = int(row["nba_api_id"])
        pos = position_map.get(pid)
        team = team_2324_map.get(pid)
        if pos is None or team is None:
            continue
        churn = churn_lookup.get((team, pos), 0.0)
        delta = beta * churn
        if delta != 0.0:
            adj[pid] = delta
    return adj


def main():
    print("Loading...")
    base = load_baseline()
    position_map = build_player_position_map()
    box_player_team = build_team_seasons_from_box()
    team_2324_map = build_player_team_2324(box_player_team)

    print(f"\nShip cohort: {len(base)}")
    print(f"With position lookup: {sum(1 for p in base['nba_api_id'] if position_map.get(int(p)))}")
    print(f"With 23-24 team lookup: {sum(1 for p in base['nba_api_id'] if team_2324_map.get(int(p)))}")

    print("\nBuilding offseason churn (22-23 -> 23-24)...")
    churn, joined = build_offseason_churn(box_player_team, position_map)
    print(f"Churn rows (team x position): {len(churn)}")
    print(f"\nTop 15 most-departed (team, position):")
    print(churn.sort_values("departed_mpg", ascending=False).head(15).to_string(index=False))
    print(f"\nTop 15 most net-positive churn (most opportunity):")
    print(churn.sort_values("net_churn_mpg", ascending=False).head(15).to_string(index=False))
    print(f"\nTop 15 most net-negative churn (most threat acquired):")
    print(churn.sort_values("net_churn_mpg", ascending=True).head(15).to_string(index=False))

    base_mae = per_stat_mae(base)
    base_pts = base_mae["PTS"]
    print(f"\nBaseline PTS MAE: {base_pts:.4f}")

    print("\n" + "=" * 78)
    print("ROSTER CHURN ABLATION SWEEP")
    print("=" * 78)
    betas = [0.00, 0.025, 0.05, 0.075, 0.10, 0.125, 0.15, 0.20, 0.30]
    rows = []
    for beta in betas:
        adj = build_churn_adjustment(base, position_map, team_2324_map, churn, beta)
        result = run_ablation(base, adj, label=f"churn_beta_{beta}")
        mae = result["mae_table"].set_index("stat")["ablated_mae"]
        deltas = result["mae_table"].set_index("stat")["pct_change"]
        comp = np.mean([deltas[s] for s in ["PTS", "AST", "TOV", "REB", "STL", "BLK", "FTA", "FTM"]])
        rows.append({
            "beta": beta,
            "n_adj": result["n_players_adjusted"],
            "PTS": mae["PTS"], "PTS_pct": deltas["PTS"],
            "AST": mae["AST"], "AST_pct": deltas["AST"],
            "TOV": mae["TOV"], "TOV_pct": deltas["TOV"],
            "REB": mae["REB"], "REB_pct": deltas["REB"],
            "STL": mae["STL"], "STL_pct": deltas["STL"],
            "BLK": mae["BLK"], "BLK_pct": deltas["BLK"],
            "composite_pct": comp,
        })
    df = pd.DataFrame(rows)
    print("\n--- Churn-only sweep ---")
    cols_to_show = ["beta", "n_adj", "PTS", "PTS_pct", "AST_pct", "TOV_pct",
                    "REB_pct", "STL_pct", "BLK_pct", "composite_pct"]
    fmt_df = df[cols_to_show].copy()
    fmt_df["PTS"] = fmt_df["PTS"].apply(lambda x: f"{x:.4f}")
    for c in ["PTS_pct", "AST_pct", "TOV_pct", "REB_pct", "STL_pct", "BLK_pct", "composite_pct"]:
        fmt_df[c] = fmt_df[c].apply(lambda x: f"{x:+.2f}%")
    print(fmt_df.to_string(index=False))

    # Save churn matrix as artifact
    churn.to_parquet(PQ / "offseason_roster_churn_2023_24.parquet", index=False)
    print(f"\nSaved churn matrix -> {PQ / 'offseason_roster_churn_2023_24.parquet'}")


if __name__ == "__main__":
    main()
