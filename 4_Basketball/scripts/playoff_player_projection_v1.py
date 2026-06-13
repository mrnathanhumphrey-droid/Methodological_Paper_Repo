"""Playoff Player Projection v1 — simplified playoff-regime adjustment layer.

DESIGN: full Stan refit on playoff-only cohort is a multi-hour build (deferred to v2).
v1 ships a regression-anchored adjustment: historical playoff vs regular-season per-min
rate ratios per (stat × position × usage tier), applied to the regular-season v4-lite
posterior to produce playoff-mode projections.

Inputs:
  - Regular-season player projections (proxy: historical player per-min rates from
    historical_box_scores.parquet 2022-23 to 2024-25)
  - Playoff player per-game stats from 2022-23 to 2024-25 (per_player_playoff_box.parquet
    if exists; else derive from `traditional_t0` in playoffs/round1+extra_rounds)
  - Active 2025-26 playoff roster (from this season's playoff data)

Output:
  - per_player_playoff_projection.csv: for each active 2025-26 playoff player,
    projected per-game stats in PLAYOFF regime
    (PTS, REB, AST, STL, BLK, TOV, FGA, FG3A, FTA, MIN)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:/NBA Projections")
HBS = ROOT / "data/parquet/historical_box_scores.parquet"
PLAYOFFS = ROOT / "data/parquet/playoffs"
PLAYER_META = ROOT / "data/parquet/player_metadata_enriched.parquet"
OUT_DIR = ROOT / "audit_runs/playoff_player_projection_v1"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_playoff_player_games() -> pd.DataFrame:
    parts = []
    for sub in ("round1", "extra_rounds"):
        p = PLAYOFFS / sub / "traditional_t0.parquet"
        if p.exists():
            df = pd.read_parquet(p)
            df["round_sub"] = sub
            parts.append(df)
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)


def normalize_minutes(min_str):
    if pd.isna(min_str):
        return np.nan
    if isinstance(min_str, (int, float)):
        return float(min_str)
    s = str(min_str)
    if ":" in s:
        try:
            mm, ss = s.split(":")
            return float(mm) + float(ss) / 60
        except Exception:
            return np.nan
    try:
        return float(s)
    except Exception:
        return np.nan


def main():
    print("=" * 80)
    print("PLAYOFF PLAYER PROJECTION v1 — regime-adjustment over regular-season rates")
    print("=" * 80)
    print()

    # Step 1: build regular-season per-min rate baseline (last full season = 2024-25)
    hbs = pd.read_parquet(HBS)
    hbs["game_date"] = pd.to_datetime(hbs["game_date"], errors="coerce")
    hbs["minutes_num"] = hbs["minutes"].apply(normalize_minutes)
    rs_25 = hbs[hbs["season"] == "2024-25"].copy() if "season" in hbs.columns else \
                hbs[hbs["game_date"].between("2024-10-01", "2025-05-01")].copy()
    print(f"Regular season 2024-25 rows: {len(rs_25)}")
    # Per-player per-min rates (aggregate across season)
    rs_player = rs_25.groupby("nba_api_id").agg(
        games=("game_id", "nunique"),
        min_total=("minutes_num", "sum"),
        PTS=("PTS", "sum"),
        REB=("REB", "sum"),
        AST=("AST", "sum"),
        STL=("STL", "sum"),
        BLK=("BLK", "sum"),
        TOV=("TOV", "sum"),
        FGA=("FGA", "sum"),
        FG3A=("FG3A", "sum"),
        FTA=("FTA", "sum"),
    ).reset_index()
    rs_player = rs_player[rs_player["games"] >= 10].copy()  # require 10+ games for stable rates
    for stat in ("PTS", "REB", "AST", "STL", "BLK", "TOV", "FGA", "FG3A", "FTA"):
        rs_player[f"{stat}_per36_rs"] = (rs_player[stat] /
                                            rs_player["min_total"].replace(0, np.nan) * 36)
    rs_player["MPG_rs"] = rs_player["min_total"] / rs_player["games"]
    print(f"  Regular-season players (≥10g): {len(rs_player)}")

    # Step 2: load 2025-26 playoff games (this season's playoff cohort)
    po = load_playoff_player_games()
    if po.empty:
        print("No playoff data loaded — abort")
        return
    po["minutes_num"] = po["minutes"].apply(normalize_minutes)
    po_player = po.groupby("personId").agg(
        games=("gameId", "nunique"),
        min_total=("minutes_num", "sum"),
        PTS=("points", "sum"),
        REB=("reboundsTotal", "sum"),
        AST=("assists", "sum"),
        STL=("steals", "sum") if "steals" in po.columns else ("blocks", lambda x: np.nan),
        BLK=("blocks", "sum"),
        TOV=("turnovers", "sum") if "turnovers" in po.columns else ("blocks", lambda x: np.nan),
        FGA=("fieldGoalsAttempted", "sum") if "fieldGoalsAttempted" in po.columns else ("blocks", lambda x: np.nan),
        FG3A=("threePointersAttempted", "sum") if "threePointersAttempted" in po.columns else ("blocks", lambda x: np.nan),
        FTA=("freeThrowsAttempted", "sum") if "freeThrowsAttempted" in po.columns else ("blocks", lambda x: np.nan),
    ).reset_index()
    po_player = po_player[(po_player["games"] >= 3) & (po_player["min_total"] >= 30)].copy()
    print(f"  Active 2025-26 playoff players (≥3g, ≥30min): {len(po_player)}")
    for stat in ("PTS", "REB", "AST", "STL", "BLK", "TOV", "FGA", "FG3A", "FTA"):
        po_player[f"{stat}_per36_po"] = (po_player[stat] /
                                            po_player["min_total"].replace(0, np.nan) * 36)
    po_player["MPG_po"] = po_player["min_total"] / po_player["games"]

    # Step 3: compute playoff/regular-season ratios per player (within-player adjustment)
    joined = po_player.merge(rs_player, left_on="personId", right_on="nba_api_id",
                                suffixes=("_po", "_rs"), how="left")
    print(f"  Playoff players with RS baseline: {joined['nba_api_id'].notna().sum()}")

    # Population-level ratio per stat (use eligible players with both seasons)
    elig_both = joined[joined["nba_api_id"].notna()]
    pop_ratios = {}
    for stat in ("PTS", "REB", "AST", "STL", "BLK", "TOV", "FGA", "FG3A", "FTA"):
        po_rate = elig_both[f"{stat}_per36_po"]
        rs_rate = elig_both[f"{stat}_per36_rs"]
        ratios = po_rate / rs_rate.replace(0, np.nan)
        pop_ratios[stat] = float(ratios.median())
    pop_ratios["MPG"] = float((elig_both["MPG_po"] / elig_both["MPG_rs"].replace(0, np.nan)).median())
    print(f"  Population playoff/RS rate ratios (median): {pop_ratios}")

    # Step 4: produce projections
    # For each active playoff player with RS baseline:
    #   projected_per36_po = RS per36 × pop ratio (regime adjustment)
    #   projected_per_game = projected_per36 × projected_MPG (RS MPG × MPG ratio)
    proj_rows = []
    meta = pd.read_parquet(PLAYER_META)
    meta_keep = meta[["nba_api_id", "name", "position"]].drop_duplicates("nba_api_id")
    for _, p in elig_both.iterrows():
        meta_row = meta_keep[meta_keep["nba_api_id"] == p["nba_api_id"]]
        name = meta_row["name"].iloc[0] if len(meta_row) else f"Player_{int(p['personId'])}"
        pos = meta_row["position"].iloc[0] if len(meta_row) else "Unknown"
        proj_mpg = p["MPG_rs"] * pop_ratios["MPG"]
        row = {
            "nba_api_id": int(p["nba_api_id"]),
            "name": name,
            "position": pos,
            "games_in_2526_playoffs": int(p["games_po"] if "games_po" in p else p["games"]),
            "actual_2526_po_mpg": float(p["MPG_po"]),
            "rs_2425_mpg": float(p["MPG_rs"]),
            "projected_po_mpg": float(proj_mpg),
        }
        for stat in ("PTS", "REB", "AST", "STL", "BLK", "TOV", "FGA", "FG3A", "FTA"):
            rs_per36 = p[f"{stat}_per36_rs"]
            proj_per36 = rs_per36 * pop_ratios[stat]
            proj_per_game = proj_per36 * proj_mpg / 36
            row[f"projected_{stat}_per_game"] = float(proj_per_game)
            row[f"actual_2526_po_{stat}_per_game"] = float(
                p[f"{stat}_per36_po"] * p["MPG_po"] / 36)
        proj_rows.append(row)

    proj_df = pd.DataFrame(proj_rows)
    proj_df["projected_fantasy_points_simple"] = (
        proj_df["projected_PTS_per_game"] +
        proj_df["projected_REB_per_game"] * 1.2 +
        proj_df["projected_AST_per_game"] * 1.5 +
        proj_df["projected_STL_per_game"] * 3 +
        proj_df["projected_BLK_per_game"] * 3 -
        proj_df["projected_TOV_per_game"]
    )
    proj_df = proj_df.sort_values("projected_fantasy_points_simple", ascending=False)
    proj_df.to_csv(OUT_DIR / "per_player_playoff_projection.csv", index=False)
    print(f"\n  Top 15 by projected fantasy points (simple):")
    cols_show = ["name", "position", "projected_po_mpg",
                  "projected_PTS_per_game", "projected_REB_per_game",
                  "projected_AST_per_game", "projected_fantasy_points_simple"]
    print(proj_df.head(15)[cols_show].to_string(index=False))

    summary = {
        "version": "v1 (simplified — regime ratio adjustment, not Stan refit)",
        "n_projections": int(len(proj_df)),
        "population_playoff_vs_rs_ratios": pop_ratios,
        "method": ("For each playoff player: project per-min rate = RS per-min × "
                    "(playoff cohort median ratio per stat). Project minutes = RS MPG × "
                    "playoff MPG ratio. Project per-game = per-min × minutes."),
        "deviation_from_pre_reg": ("No pre-reg locked for v1; this is a regime-adjustment "
                                     "layer pending a separate Stan playoff refit (v2)."),
    }
    with open(OUT_DIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nWrote outputs to {OUT_DIR}")


if __name__ == "__main__":
    main()
