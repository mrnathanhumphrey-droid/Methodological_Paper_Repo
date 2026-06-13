"""Apply v6.1 LOCKED offsets to the 25-26 v6 ship CSV.

Locked spec (per audit_runs/unified_ship_v6_1/metadata.json, dated 2026-05-02):

Mean offsets:
  - PTS | position=Center | -0.587 ADDITIVE         (3-season validated)
  - PTS | mid_season_change=True | x0.9382 MULT     (3-season; INERT for 25-26 — no coaching data)
  - AST | years_pro_bucket=13+ | x0.9278 MULT       (3-season validated)

Variance multipliers (all TIGHTEN):
  - REB | position=Guard   | sd x 0.723
  - AST | position=Forward | sd x 0.819
  - BLK | position=Guard   | sd x 0.662

Applied to: audit_runs/unified_ship_v6_2025_26/per_player_projections_2025-26.csv
Written to: audit_runs/unified_ship_v6_1_2025_26/per_player_projections_2025-26.csv

Position class derivation: _primary_position_class (G/F/C from first-listed
component of "Forward-Center" etc.).

Years_pro for 25-26: target_year=2025, derived from metadata's debut_year
(falls back to draft_year + 1 if debut_year missing).
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
import json
from pathlib import Path

import pandas as pd

from models.skill.data_prep import _primary_position_class

REPO = Path(".")
PQ = REPO / "data" / "parquet"
SHIP_2526_V6 = REPO / "audit_runs" / "unified_ship_v6_2025_26" / "per_player_projections_2025-26.csv"
OUT_DIR = REPO / "audit_runs" / "unified_ship_v6_1_2025_26"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / "per_player_projections_2025-26.csv"

TARGET_YEAR = 2025

# Locked v6.1 spec (per v6.1 LOCKED postmortem)
PTS_CENTER_OFFSET = -0.587  # additive, per-game PTS
AST_VET_MULT = 0.9278       # multiplicative, per-game AST
REB_GUARD_VAR_MULT = 0.723  # tightens REB sd for Guards
AST_FWD_VAR_MULT = 0.819    # tightens AST sd for Forwards
BLK_GUARD_VAR_MULT = 0.662  # tightens BLK sd for Guards

# mid_season_change INERT for 25-26 (no 25-26 coaching data, and the
# offset would represent forward info-leakage at draft time anyway).


def attach_class_features(df: pd.DataFrame, target_year: int) -> pd.DataFrame:
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    meta_cols = ["nba_api_id", "position", "draft_year", "debut_year"]
    # Augment with rookie supplement if cohort widening produced one.
    sup_path = REPO / "audit_runs" / "cohort_widening_v0_2025_26" / "rookie_metadata_supplement.parquet"
    if sup_path.exists():
        sup = pd.read_parquet(sup_path)
        meta = pd.concat([meta[meta_cols], sup[meta_cols]], ignore_index=True)
    df = df.merge(
        meta[meta_cols],
        on="nba_api_id", how="left",
    )
    df["pos_class"] = df["position"].apply(_primary_position_class)
    # years_pro: prefer debut_year (handles pre-2014 vets cleaner per v6.1
    # session 2 cleanup), fall back to draft_year + 1.
    df["years_pro"] = df["debut_year"].where(
        df["debut_year"].notna(),
        df["draft_year"] + 1,
    )
    df["years_pro"] = target_year - df["years_pro"]
    df["years_pro_bucket"] = pd.cut(
        df["years_pro"], bins=[-1, 0, 3, 7, 12, 30],
        labels=["rookie", "1-3", "4-7", "8-12", "13+"],
    ).astype(str)
    return df


def main():
    print(f"Reading 25-26 v6 ship CSV: {SHIP_2526_V6}")
    df = pd.read_csv(SHIP_2526_V6)
    df["nba_api_id"] = df["nba_api_id"].astype(int)
    print(f"  rows: {len(df)}")
    n_pre = len(df)

    df = attach_class_features(df, target_year=TARGET_YEAR)
    print(f"  pos_class counts: {df['pos_class'].value_counts(dropna=False).to_dict()}")
    print(f"  years_pro_bucket counts: {df['years_pro_bucket'].value_counts(dropna=False).to_dict()}")

    delta_log = {}

    # Mean offset 1: Center × PTS (additive, per-game)
    if "PTS_per_game" in df.columns:
        center_mask = df["pos_class"] == "C"
        n_center = int(center_mask.sum())
        df.loc[center_mask, "PTS_per_game"] += PTS_CENTER_OFFSET
        delta_log["PTS_Center_additive"] = {
            "offset": PTS_CENTER_OFFSET, "n_carriers": n_center,
        }
        print(f"  Applied PTS Center offset {PTS_CENTER_OFFSET:+.3f} to {n_center} players")

    # Mean offset 2: 13+ vets × AST (mult, per-game)
    if "AST_per_game" in df.columns:
        vet_mask = df["years_pro_bucket"] == "13+"
        n_vets = int(vet_mask.sum())
        df.loc[vet_mask, "AST_per_game"] *= AST_VET_MULT
        delta_log["AST_13+_mult"] = {
            "mult": AST_VET_MULT, "n_carriers": n_vets,
        }
        print(f"  Applied AST 13+ mult {AST_VET_MULT:.4f} to {n_vets} players")

    # Variance tighten 1: REB sd × 0.723 for Guards
    if "REB_per_game_sd" in df.columns:
        guard_mask = df["pos_class"] == "G"
        n_guards = int(guard_mask.sum())
        df.loc[guard_mask, "REB_per_game_sd"] *= REB_GUARD_VAR_MULT
        delta_log["REB_Guard_var_mult"] = {
            "mult": REB_GUARD_VAR_MULT, "n_carriers": n_guards,
        }
        print(f"  Tightened REB sd by {REB_GUARD_VAR_MULT:.3f} for {n_guards} Guards")

    # Variance tighten 2: AST sd × 0.819 for Forwards
    if "AST_per_game_sd" in df.columns:
        fwd_mask = df["pos_class"] == "F"
        n_fwds = int(fwd_mask.sum())
        df.loc[fwd_mask, "AST_per_game_sd"] *= AST_FWD_VAR_MULT
        delta_log["AST_Forward_var_mult"] = {
            "mult": AST_FWD_VAR_MULT, "n_carriers": n_fwds,
        }
        print(f"  Tightened AST sd by {AST_FWD_VAR_MULT:.3f} for {n_fwds} Forwards")

    # Variance tighten 3: BLK sd × 0.662 for Guards
    if "BLK_per_game_sd" in df.columns:
        guard_mask = df["pos_class"] == "G"
        n_guards = int(guard_mask.sum())
        df.loc[guard_mask, "BLK_per_game_sd"] *= BLK_GUARD_VAR_MULT
        delta_log["BLK_Guard_var_mult"] = {
            "mult": BLK_GUARD_VAR_MULT, "n_carriers": n_guards,
        }
        print(f"  Tightened BLK sd by {BLK_GUARD_VAR_MULT:.3f} for {n_guards} Guards")

    # Drop the temporary class-feature columns from output
    drop_cols = ["position", "draft_year", "debut_year", "pos_class",
                 "years_pro", "years_pro_bucket"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    df.to_csv(OUT_CSV, index=False)
    print(f"\nWrote {OUT_CSV} ({len(df)} rows)")
    assert len(df) == n_pre, "row count drift after offset application"

    meta = {
        "version": "v6.1_LOCKED_2025-26",
        "source_ship": str(SHIP_2526_V6).replace("\\", "/"),
        "target_season": "2025-26",
        "target_year": TARGET_YEAR,
        "applied_offsets": delta_log,
        "inert_offsets": {
            "PTS_mid_season_change_mult": {
                "reason": "no 25-26 coaching data; would be forward-info leakage "
                          "at draft time anyway",
                "spec_value": 0.9382,
            },
        },
        "note": "v6.1 LOCKED spec from audit_runs/unified_ship_v6_1/metadata.json "
                "(dated 2026-05-02). Forward-projected 25-26 ship — 'as if 25-26 "
                "did not occur' for tuning Wonka draft greedies.",
    }
    with open(OUT_DIR / "metadata.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Metadata -> {OUT_DIR}/metadata.json")


if __name__ == "__main__":
    main()
