"""Apply v6.1 cross-season-validated offsets to a v6 ship CSV.

CURRENT VALIDATED OFFSETS (as of 2026-05-02, validated 22-23 + 23-24 + 24-25 3-season pool):
  PTS ← Center position: -0.587 PTS additive (softened from -0.70)
  PTS ← mid_season_change: -6.18% multiplicative (softened from -8.4%)
  AST ← years_pro 13+: -7.08% multiplicative (softened from -9.1%)

DROPPED at 3-season validation (failed strict cross-season test):
  REB ← mid_season_change: -0.543 additive — sign/magnitude didn't replicate in 24-25
  TOV ← years_pro 13+: -10.0% multiplicative — sign/magnitude didn't replicate in 24-25

Magnitude softening: signal magnitudes faded in 24-25 across the board.
The 3-season combined regression gives honest, drift-aware magnitudes.

Usage:
  python scripts/apply_v61_validated_offsets.py --in <input_ship_csv> --out <output_csv>
  Defaults to v6 23-24 ship -> v6.1 23-24 ship.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"

# === VALIDATED OFFSET TABLE ===
# Format: {stat: {class_name: {class_value: offset_in_per_game_units}}}
# Add new entries here when validation surfaces them.
VALIDATED_OFFSETS = {
    "PTS": {
        "position": {
            "Center": -0.587,  # ADDITIVE: 3-season combined alpha (was -0.70 at 2-season)
        },
    },
    # REB x mid_season DROPPED at 3-season validation (didn't replicate in 24-25)
}

# Multiplicative offsets (residual scales with projection size)
# Format: {stat: {class_name: {class_value: multiplier}}}
# Applied as: proj *= multiplier  (e.g., 0.9382 = -6.18% reduction)
VALIDATED_MULTIPLIERS = {
    "PTS": {
        "mid_season_change": {
            True: 1.0 - 0.0618,  # MULT: 3-season c=-6.18% (was -8.4% at 2-season)
        },
    },
    "AST": {
        "years_pro_bucket": {
            "13+": 1.0 - 0.0722,  # MULT: 3-season c=-7.22% (refreshed 2026-05-02 post-class-cleanup)
        },
    },
    # TOV x years_pro 13+ DROPPED at 3-season validation
}

# Validation provenance for each entry (for audit trail)
PROVENANCE = {
    ("PTS", "position", "Center"): {
        "validated_seasons": ["2022-23", "2023-24", "2024-25"],
        "season_22_23_residual": -0.722,
        "season_23_24_residual": -0.684,
        "season_24_25_residual": -0.292,
        "n_per_season": [25, 23, 19],
        "scaling": "ADDITIVE",
        "magnitude_2season": -0.70,
        "magnitude_3season": -0.587,
        "discovered_via": "Collatz residual-class noise-floor protocol; refit on 3-season cohort 2026-05-02",
        "notes": "Centers over-projected on PTS. 24-25 magnitude (-0.292) ~half of prior years; signal fading as base model improves. 3-season combined alpha = -0.587. SSE for additive vs mult nearly identical (382 vs 385) — keeping additive form per original mechanism.",
    },
    ("PTS", "mid_season_change", True): {
        "validated_seasons": ["2022-23", "2023-24", "2024-25"],
        "scaling": "MULTIPLICATIVE",
        "multiplier_2season": 1.0 - 0.084,
        "multiplier_3season": 1.0 - 0.0618,
        "season_22_23_residual": -1.896,
        "season_23_24_residual": -1.207,
        "season_24_25_residual": -0.301,
        "n_per_season": [9, 16, 16],
        "regression_slope_t_3season": -2.39,
        "regression_slope_p_3season": 0.022,
        "discovered_via": "Worst-miss decomposition + cross-season validation + add-vs-mult regression refit at 3-season",
        "notes": "Players on teams with mid-season HC change over-projected on PTS. Multiplicative form (residual scales with proj_PTS) confirmed at 3-season. Magnitude faded -1.896 -> -1.207 -> -0.301 across years. 3-season c = -6.18% (was -8.4% at 2-season).",
    },
    ("AST", "years_pro_bucket", "13+"): {
        "validated_seasons": ["2022-23", "2023-24", "2024-25"],
        "scaling": "MULTIPLICATIVE",
        "multiplier_2season": 1.0 - 0.091,
        "multiplier_3season_initial": 1.0 - 0.0708,
        "multiplier_3season_refreshed": 1.0 - 0.0722,
        "season_22_23_residual": -0.146,
        "season_23_24_residual": -0.562,
        "season_24_25_residual": -0.120,
        "n_per_season": [18, 18, 26],
        "regression_slope_t_3season": -3.72,
        "regression_slope_p_3season": 0.000,
        "discovered_via": "Cross-season full validation + add-vs-mult regression refit at 3-season; refreshed post class-feature cleanup",
        "notes": "Veterans (13+ years pro) over-projected on AST. Mult form strong at 3-season (slope p<0.001). 24-25 magnitude refreshed from -0.088 to -0.120 after class cleanup (pre-2014 vets that were leaking into 'undrafted' bucket returned to 13+ where they belong). 3-season c = -7.22% (was -9.1% at 2-season).",
    },
    # DROPPED at 3-season validation (preserved in metadata for history):
    # ("REB", "mid_season_change", True): didn't replicate in 24-25
    # ("TOV", "years_pro_bucket", "13+"): didn't replicate in 24-25
}


from _class_features import attach_class_features  # canonical, supports all classes


def apply_offsets(ship_df, target_year):
    """Apply VALIDATED_OFFSETS to ship_df's projection columns. Returns new df."""
    out = ship_df.copy()
    out["nba_api_id"] = out["nba_api_id"].astype(int)

    feat = attach_class_features(out, target_year)

    applied_log = []

    # Apply additive offsets first
    for stat, class_specs in VALIDATED_OFFSETS.items():
        proj_col = f"{stat}_proj"
        if proj_col not in out.columns:
            continue
        for class_name, value_to_offset in class_specs.items():
            if class_name not in feat.columns:
                print(f"  WARN: class column {class_name} not found in features")
                continue
            for cls_val, offset in value_to_offset.items():
                mask = feat[class_name] == cls_val
                n = mask.sum()
                if n == 0:
                    continue
                out.loc[mask, proj_col] = out.loc[mask, proj_col] + offset
                pg_col = f"{stat}_per_game"
                if pg_col in out.columns:
                    out.loc[mask, pg_col] = out.loc[mask, pg_col] + offset
                applied_log.append((stat, class_name, cls_val, f"add {offset:+.3f}", n))

    # Apply multiplicative offsets after additive (order matters — but for our case
    # the multiplicative class (mid_season_change) is mostly disjoint from Center class,
    # so order doesn't materially affect output)
    for stat, class_specs in VALIDATED_MULTIPLIERS.items():
        proj_col = f"{stat}_proj"
        if proj_col not in out.columns:
            continue
        for class_name, value_to_mult in class_specs.items():
            if class_name not in feat.columns:
                continue
            for cls_val, mult in value_to_mult.items():
                mask = feat[class_name] == cls_val
                n = mask.sum()
                if n == 0:
                    continue
                out.loc[mask, proj_col] = out.loc[mask, proj_col] * mult
                pg_col = f"{stat}_per_game"
                if pg_col in out.columns:
                    out.loc[mask, pg_col] = out.loc[mask, pg_col] * mult
                applied_log.append((stat, class_name, cls_val,
                                     f"mult x{mult:.3f} (= {(mult-1)*100:+.1f}%)", n))

    print("\n--- Offsets applied ---")
    for stat, cn, cv, op, n in applied_log:
        prov = PROVENANCE.get((stat, cn, cv), {})
        print(f"  {stat} | {cn}={cv} | {op} | n={n} | "
              f"validated on: {prov.get('validated_seasons', '?')}")

    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="input_csv", default="audit_runs/unified_ship_v6/per_player_projections_2023-24.csv")
    p.add_argument("--out", dest="output_csv", default="audit_runs/unified_ship_v6_1/per_player_projections_2023-24.csv")
    p.add_argument("--target-year", type=int, default=2023)
    args = p.parse_args()

    in_path = Path(args.input_csv)
    out_path = Path(args.output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Reading {in_path}...")
    df = pd.read_csv(in_path)
    print(f"  rows: {len(df)}")

    corrected = apply_offsets(df, target_year=args.target_year)

    corrected.to_csv(out_path, index=False)
    print(f"\nWrote {out_path}")
    print(f"  rows: {len(corrected)}")

    # Before/after MAE summary across all stats with offsets/multipliers
    print("\n--- Before/after MAE on offset-touched stats ---")
    affected = sorted(set(VALIDATED_OFFSETS.keys()) | set(VALIDATED_MULTIPLIERS.keys()))
    for stat in affected:
        actual_col = f"{stat}_actual"
        proj_col = f"{stat}_proj"
        if actual_col not in df.columns or proj_col not in df.columns:
            continue
        b_mask = df[actual_col].notna() & df[proj_col].notna()
        b = (df.loc[b_mask, actual_col] - df.loc[b_mask, proj_col]).abs().mean()
        a_mask = corrected[actual_col].notna() & corrected[proj_col].notna()
        a = (corrected.loc[a_mask, actual_col] - corrected.loc[a_mask, proj_col]).abs().mean()
        pct = 100 * (a - b) / b if b > 0 else 0
        print(f"  {stat:>4} MAE: {b:.4f} -> {a:.4f}  ({pct:+.2f}%)  n={b_mask.sum()}")

    # Also write metadata.json
    import json
    meta = {
        "version": "v6.1",
        "delta_vs_v6": "Added forward-validated class offsets (currently only Center×PTS).",
        "source_ship": str(in_path),
        "validated_offsets": {
            f"{stat} | {cn}": {str(k): v for k, v in cd.items()}
            for stat, sp in VALIDATED_OFFSETS.items()
            for cn, cd in sp.items()
        },
        "provenance": {
            f"{stat}|{cn}|{cv}": prov
            for (stat, cn, cv), prov in PROVENANCE.items()
        },
        "validation_protocol": "Collatz residual-class noise-floor protocol (per feedback_collatz_protocol_for_projections.md). SNR>=1.5 gate, LOO honesty, top-1 class per stat, then forward across-season validation required before ship.",
        "next_validation_date": "When 26-27 ship CSV available — re-derive offsets from 25-26 backtest residuals and verify against 26-27 cohort.",
    }
    meta_path = out_path.parent / "metadata.json"
    meta_path.write_text(json.dumps(meta, indent=2, default=str))
    print(f"  Metadata: {meta_path}")


if __name__ == "__main__":
    main()
