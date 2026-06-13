"""Write 25-26 v6.1 LOCKED ship to Wonka's audit-CSV contract.

Reads:    audit_runs/unified_ship_v6_1_2025_26/per_player_projections_2025-26.csv
Writes:   D:/Wonka Resolve/audit/data/parsed/nba_projections_projections.csv

Contract (per export_to_wonka_v2.py and Wonka's multi_source_csv ingester):
  - Header line: # contract_version=1.0 mode=production target_season=2025-26 ...
  - Columns: source, player_name, team, position, nba_api_id, games_proj,
             minutes_proj, then per-stat <STAT>_proj + <STAT>_stddev_per_game,
             plus FG_pct_proj / FT_pct_proj / 3P_pct_proj.

games_proj: 24-25 actual GP (last-known healthy/role; the natural prior at
  draft time absent 25-26 data).
team: 24-25 last-known team_abbr (most-played team in 24-25).
position: from player_metadata_enriched.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
import csv
from pathlib import Path

import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"
# DEPLOYED: v6.1 LOCKED. v6.2 de-shrinkage exists at unified_ship_v6_2_deshrunk_2025_26
# but is HELD as research artifact pending v6.3 (per-cohort γ) — see paper §6 for
# the rationale (deferring to preserve clean blind-validation headline at vet PTS MAE 2.48).
SHIP_V61 = REPO / "audit_runs" / "unified_ship_v6_1_2025_26" / "per_player_projections_2025-26.csv"
WONKA_OUT = Path("D:/Wonka Resolve/audit/data/parsed/nba_projections_projections.csv")

CONTRACT_VERSION = "1.0"
SOURCE_NAME = "nba_projections"
MODE = "production"
TARGET_SEASON = "2025-26"
TRAIN_TAG = "2019-20-2020-21-2021-22-2022-23-2023-24-2024-25"
PRIOR_SEASON = "2024-25"

WONKA_FIELDS = [
    "source", "player_name", "team", "position", "nba_api_id",
    "games_proj", "minutes_proj",
    "PTS_proj", "PTS_stddev_per_game",
    "REB_proj", "REB_stddev_per_game",
    "AST_proj", "AST_stddev_per_game",
    "STL_proj", "STL_stddev_per_game",
    "BLK_proj", "BLK_stddev_per_game",
    "TOV_proj", "TOV_stddev_per_game",
    "FGM_proj", "FGM_stddev_per_game",
    "FGA_proj", "FGA_stddev_per_game",
    "FG_pct_proj",
    "FTM_proj", "FTM_stddev_per_game",
    "FTA_proj", "FTA_stddev_per_game",
    "FT_pct_proj",
    "3PM_proj", "3PM_stddev_per_game",
    "3PA_proj", "3PA_stddev_per_game",
    "3P_pct_proj",
]

# Map ship-CSV per_game columns to Wonka contract column names
SHIP_TO_WONKA = {
    "PTS_per_game": "PTS_proj", "PTS_per_game_sd": "PTS_stddev_per_game",
    "REB_per_game": "REB_proj", "REB_per_game_sd": "REB_stddev_per_game",
    "AST_per_game": "AST_proj", "AST_per_game_sd": "AST_stddev_per_game",
    "STL_per_game": "STL_proj", "STL_per_game_sd": "STL_stddev_per_game",
    "BLK_per_game": "BLK_proj", "BLK_per_game_sd": "BLK_stddev_per_game",
    "TOV_per_game": "TOV_proj", "TOV_per_game_sd": "TOV_stddev_per_game",
    "FGM_per_game": "FGM_proj", "FGM_per_game_sd": "FGM_stddev_per_game",
    "FGA_per_game": "FGA_proj", "FGA_per_game_sd": "FGA_stddev_per_game",
    "FTM_per_game": "FTM_proj", "FTM_per_game_sd": "FTM_stddev_per_game",
    "FTA_per_game": "FTA_proj", "FTA_per_game_sd": "FTA_stddev_per_game",
    "FG3M_per_game": "3PM_proj", "FG3M_per_game_sd": "3PM_stddev_per_game",
    "FG3A_per_game": "3PA_proj", "FG3A_per_game_sd": "3PA_stddev_per_game",
}


def main():
    print(f"Reading v6.1 ship: {SHIP_V61}")
    df = pd.read_csv(SHIP_V61)
    df["nba_api_id"] = df["nba_api_id"].astype(int)
    print(f"  rows: {len(df)}")

    # Player metadata for team / position / name
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    name_lookup = dict(zip(meta["nba_api_id"].astype(int), meta["name"]))
    pos_lookup = dict(zip(meta["nba_api_id"].astype(int),
                          meta["position"].fillna("")))

    # Augment with rookie supplement (2025 draft picks have synthetic IDs).
    sup_path = REPO / "audit_runs" / "cohort_widening_v0_2025_26" / "rookie_metadata_supplement.parquet"
    if sup_path.exists():
        sup = pd.read_parquet(sup_path)
        for _, r in sup.iterrows():
            pid = int(r["nba_api_id"])
            name_lookup[pid] = r["name"]
            pos_lookup[pid] = r["position"]

    # Team + games-played from 24-25 box scores (last-known)
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    sub = box[box["season"] == PRIOR_SEASON].copy()
    sub["minutes"] = pd.to_numeric(sub["minutes"], errors="coerce")
    sub = sub.dropna(subset=["minutes"])
    sub = sub[sub["minutes"] > 0]
    team_lookup = (sub.groupby("nba_api_id")["team_abbr"]
                   .agg(lambda s: s.value_counts().index[0])
                   .to_dict())
    team_lookup = {int(k): v for k, v in team_lookup.items()}
    games_lookup = sub.groupby("nba_api_id")["game_id"].count().to_dict()
    games_lookup = {int(k): int(v) for k, v in games_lookup.items()}

    # Rookies don't have 24-25 box scores; supplement team from drafted_by_team
    # and games from log-pick mpg regression baseline (use 70 as placeholder
    # season GP for full rookie season).
    if sup_path.exists():
        sup = pd.read_parquet(sup_path)
        for _, r in sup.iterrows():
            pid = int(r["nba_api_id"])
            if pid not in team_lookup and pd.notna(r.get("drafted_by_team")):
                team_lookup[pid] = r["drafted_by_team"]
            if pid not in games_lookup:
                games_lookup[pid] = 70  # Placeholder for unplayed rookie season

    # Compute derived percentages from FGM/FGA, FTM/FTA, FG3M/FG3A per-game means
    if "FGA_per_game" in df.columns and "FGM_per_game" in df.columns:
        df["FG_pct_proj"] = (df["FGM_per_game"] /
                             df["FGA_per_game"].replace(0, pd.NA))
    if "FTA_per_game" in df.columns and "FTM_per_game" in df.columns:
        df["FT_pct_proj"] = (df["FTM_per_game"] /
                             df["FTA_per_game"].replace(0, pd.NA))
    if "FG3A_per_game" in df.columns and "FG3M_per_game" in df.columns:
        df["3P_pct_proj"] = (df["FG3M_per_game"] /
                             df["FG3A_per_game"].replace(0, pd.NA))

    WONKA_OUT.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with WONKA_OUT.open("w", encoding="utf-8", newline="") as f:
        f.write(f"# contract_version={CONTRACT_VERSION} mode={MODE} "
                f"target_season={TARGET_SEASON} train_seasons={TRAIN_TAG} "
                f"source=v6.1_LOCKED_forward note=as_if_25-26_unplayed\n")
        writer = csv.DictWriter(f, fieldnames=WONKA_FIELDS)
        writer.writeheader()

        for _, r in df.iterrows():
            pid = int(r["nba_api_id"])
            row = {k: "" for k in WONKA_FIELDS}
            row["source"] = SOURCE_NAME
            row["player_name"] = name_lookup.get(pid, r.get("name", ""))
            row["team"] = team_lookup.get(pid, "")
            row["position"] = pos_lookup.get(pid, "")
            row["nba_api_id"] = str(pid)
            row["games_proj"] = f"{games_lookup.get(pid, 70):.1f}"
            row["minutes_proj"] = f"{float(r.get('mpg', 0.0)):.4f}"

            for ship_col, wonka_col in SHIP_TO_WONKA.items():
                if ship_col in df.columns and pd.notna(r[ship_col]):
                    row[wonka_col] = f"{float(r[ship_col]):.4f}"

            for pct_col in ("FG_pct_proj", "FT_pct_proj", "3P_pct_proj"):
                if pct_col in df.columns and pd.notna(r.get(pct_col)):
                    row[pct_col] = f"{float(r[pct_col]):.4f}"

            writer.writerow(row)
            written += 1

    print(f"Wrote {written} rows -> {WONKA_OUT}")


if __name__ == "__main__":
    main()
