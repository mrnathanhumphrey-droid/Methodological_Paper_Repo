"""Apply cross-season-validated variance multipliers to v6 ship's posterior SDs.

Companion to apply_v61_validated_offsets.py — that one shifts means, this one
widens (or tightens) intervals. For Wonka, wider posterior intervals on a
class subgroup translates to discount auction pricing for that subgroup
because uncertainty drives bid spread.

Reads: data/parquet/cross_season_validated_variances.parquet (built by
       cross_season_full_validation.py)

Writes: audit_runs/unified_ship_v6_1/per_player_projections_2023-24.csv
        with {stat}_sd columns updated.
        Plus: data/parquet/wonka_variance_multiplier_v2.parquet — extends
        existing chronic-only variance multiplier with these new combinations.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")

import argparse
from pathlib import Path
import json
import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"
SHIP_PATH = REPO / "audit_runs" / "unified_ship_v6_1" / "per_player_projections_2023-24.csv"
VAR_TABLE_PATH = PQ / "cross_season_validated_variances.parquet"


from _class_features import attach_class_features


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--target-year", type=int, default=2023)
    p.add_argument("--ship", default=str(SHIP_PATH))
    args = p.parse_args()

    if not VAR_TABLE_PATH.exists():
        print(f"MISSING: {VAR_TABLE_PATH}")
        print("Run scripts/cross_season_full_validation.py first (needs 2+ seasons of audits).")
        sys.exit(1)

    var_table = pd.read_parquet(VAR_TABLE_PATH)
    print(f"Validated variance multipliers: {len(var_table)} entries")
    if len(var_table) == 0:
        print("  (Empty — no entries cleared cross-season variance validation.)")
        return

    print(var_table.to_string(index=False))

    ship = pd.read_csv(args.ship)
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    feat = attach_class_features(ship, target_year=args.target_year)

    # SD columns: {stat}_sd or {stat}_per_game_sd
    print("\n--- Applying variance multipliers ---")
    applied_log = []
    for _, row in var_table.iterrows():
        stat = row["stat"]
        cls = row["class"]
        cls_val = row["class_value"]
        direction = row["direction"]
        ratio = row["geom_mean_ratio"]
        # SD multiplier = sqrt(variance_ratio)
        sd_mult = float(np.sqrt(ratio))

        # Find SD column
        sd_col = None
        for cand in [f"{stat}_sd", f"{stat}_per_game_sd"]:
            if cand in ship.columns:
                sd_col = cand
                break
        if sd_col is None:
            continue
        if cls not in feat.columns:
            continue

        # Match class value (handle bool stringified)
        if cls_val == "True":
            mask = feat[cls] == True
        elif cls_val == "False":
            mask = feat[cls] == False
        else:
            mask = feat[cls].astype(str) == cls_val
        n = mask.sum()
        if n == 0:
            continue
        ship.loc[mask, sd_col] = ship.loc[mask, sd_col] * sd_mult
        applied_log.append((stat, cls, cls_val, sd_mult, n))
        print(f"  {stat}_sd | {cls}={cls_val} | sd_mult x{sd_mult:.3f} | n={n}")

    out_path = Path(args.ship)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ship.to_csv(out_path, index=False)
    print(f"\nWrote {out_path}")

    # Build wonka variance multiplier v2 (extends chronic-only)
    if (PQ / "wonka_variance_multiplier.parquet").exists():
        chronic = pd.read_parquet(PQ / "wonka_variance_multiplier.parquet")
        # chronic has nba_api_id + variance_mult etc — we'll combine via multiplication
        # For the v2 table, we provide PER-PLAYER-PER-STAT multipliers
        rows = []
        for _, ship_row in feat.iterrows():
            pid = int(ship_row["nba_api_id"])
            chronic_mult = 1.0
            cm = chronic[chronic["nba_api_id"] == pid]
            if len(cm) > 0:
                chronic_mult = float(cm.iloc[0]["variance_mult"])
            for _, vrow in var_table.iterrows():
                stat = vrow["stat"]
                cls = vrow["class"]
                cls_val = vrow["class_value"]
                if cls not in feat.columns:
                    continue
                if cls_val == "True":
                    matches = ship_row[cls] == True
                elif cls_val == "False":
                    matches = ship_row[cls] == False
                else:
                    matches = str(ship_row[cls]) == cls_val
                if matches:
                    sd_mult = float(np.sqrt(vrow["geom_mean_ratio"]))
                    rows.append({
                        "nba_api_id": pid,
                        "stat": stat,
                        "class_source": f"{cls}={cls_val}",
                        "sd_multiplier": sd_mult,
                        "chronic_multiplier": chronic_mult,
                        "combined_sd_multiplier": sd_mult * chronic_mult,
                    })
        if rows:
            v2 = pd.DataFrame(rows)
            v2.to_parquet(PQ / "wonka_variance_multiplier_v2.parquet", index=False)
            print(f"Wrote {PQ / 'wonka_variance_multiplier_v2.parquet'}  ({len(v2)} rows)")


if __name__ == "__main__":
    main()
