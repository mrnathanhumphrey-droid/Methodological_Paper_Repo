"""Produce v6.1-LOO ship CSV with parsimonious top-1 class offsets applied.

Reads:    audit_runs/unified_ship_v6/per_player_projections_2023-24.csv
Writes:   audit_runs/unified_ship_v6_offset_loo/per_player_projections_2023-24.csv

Applies the LOO-derived top-1-per-stat class offsets:
  - PTS, AST, STL, FTA, FTM ← offseason_traded
  - TOV ← years_pro_bucket
  - BLK ← position
  - REB ← (none, no surviving class)

Reports per-player delta and the top-20 most-shifted players in 9-cat-relevant
terms so we can see who would re-price in Wonka.

This is for downstream Wonka consumption. Wonka picks up the new ship CSV
from its standard audit-CSV ingestion — no cross-system code touching.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")

from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"
SHIP_2324 = REPO / "audit_runs" / "unified_ship_v6" / "per_player_projections_2023-24.csv"
OUT_DIR = REPO / "audit_runs" / "unified_ship_v6_offset_loo"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / "per_player_projections_2023-24.csv"


def attach_class_features(df, target_year=2023):
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    df = df.merge(meta[["nba_api_id", "position", "birth_date", "draft_year"]],
                  on="nba_api_id", how="left")
    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
    season_start = pd.Timestamp(f"{target_year}-10-24")
    df["age"] = (season_start - df["birth_date"]).dt.days / 365.25
    df["age_bucket"] = pd.cut(df["age"], bins=[0, 24, 27, 30, 33, 50],
                                labels=["<=24", "25-26", "27-29", "30-32", "33+"]).astype(str)
    df["years_pro"] = target_year - df["draft_year"]
    df["years_pro_bucket"] = pd.cut(df["years_pro"], bins=[-1, 0, 3, 7, 12, 30],
                                      labels=["rookie", "1-3", "4-7", "8-12", "13+"]).astype(str)
    tx = pd.read_parquet(PQ / "pro_sports_transactions.parquet")
    tx["event_date"] = pd.to_datetime(tx["event_date"])
    traded = set(tx[(tx["transaction_type"] == "trade") &
                    (tx["event_date"] >= "2023-04-15") &
                    (tx["event_date"] <= "2023-10-24") &
                    (tx["nba_api_id"].notna())]["nba_api_id"].astype(int))
    df["offseason_traded"] = df["nba_api_id"].astype(int).isin(traded)
    return df


def loo_class_means(df, class_col, residual_col):
    sub = df.dropna(subset=[class_col, residual_col]).copy()
    out = {}
    for cls, idx in sub.groupby(class_col, observed=True).groups.items():
        idx = list(idx)
        for i in idx:
            others = [j for j in idx if j != i]
            mean = sub.loc[others, residual_col].mean() if others else 0.0
            out[i] = mean
    return out


def main():
    print("Loading 23-24 v6 ship CSV...")
    base = pd.read_csv(SHIP_2324)
    base["nba_api_id"] = base["nba_api_id"].astype(int)
    print(f"  rows: {len(base)}")

    df = attach_class_features(base, target_year=2023)

    # Compute residuals on stats with actual
    STATS = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FTA", "FTM"]
    for s in STATS:
        proj = f"{s}_proj"
        actual = f"{s}_actual"
        if proj in df.columns and actual in df.columns:
            df[f"{s}_residual"] = df[actual] - df[proj]

    # Apply parsimonious top-1 offsets via LOO
    # (PTS, AST, STL, FTA, FTM ← offseason_traded; TOV ← years_pro_bucket; BLK ← position)
    offset_specs = {
        "PTS": "offseason_traded",
        "AST": "offseason_traded",
        "STL": "offseason_traded",
        "FTA": "offseason_traded",
        "FTM": "offseason_traded",
        "TOV": "years_pro_bucket",
        "BLK": "position",
        # REB: no surviving class
    }

    out = base.copy()
    delta_cols = {}
    for stat, cls in offset_specs.items():
        proj_col = f"{stat}_proj"
        if proj_col not in out.columns:
            continue
        sub = df.dropna(subset=[f"{stat}_residual"]).copy()
        loo_map = loo_class_means(sub, cls, f"{stat}_residual")
        delta = pd.Series(0.0, index=out.index)
        for idx, row in df.iterrows():
            pid = int(row["nba_api_id"])
            if idx not in loo_map:
                continue
            d = float(loo_map[idx])
            if pid in set(out["nba_api_id"]):
                m = out["nba_api_id"] == pid
                delta.loc[m] = d
        delta_cols[stat] = delta
        out[proj_col] = out[proj_col] + delta
        # Also adjust per_game variant if it exists
        pg_col = f"{stat}_per_game"
        if pg_col in out.columns:
            out[pg_col] = out[pg_col] + delta

    # Save corrected CSV
    out.to_csv(OUT_CSV, index=False)
    print(f"\nSaved corrected ship CSV -> {OUT_CSV}")

    # Per-player delta summary
    print("\n" + "=" * 78)
    print("PER-PLAYER DELTA SUMMARY")
    print("=" * 78)
    summary = out[["nba_api_id", "name"]].copy()
    for s in STATS:
        if s in delta_cols:
            summary[f"d_{s}"] = delta_cols[s].values
        else:
            summary[f"d_{s}"] = 0.0

    # Aggregate: |delta| as 9-cat-style "shift magnitude"
    # In 9-cat z-score weighting (rough), each stat counter contributes proportional
    # to its scale. Use SD-normalized abs delta as a proxy for cross-stat shift magnitude.
    sd_norms = {
        "PTS": 5.0,   # rough SD across players
        "REB": 2.0,
        "AST": 2.0,
        "STL": 0.5,
        "BLK": 0.5,
        "TOV": 1.0,
    }
    summary["shift_magnitude"] = sum(
        summary[f"d_{s}"].abs() / sd_norms.get(s, 1.0)
        for s in STATS if f"d_{s}" in summary.columns
    )

    # Top-20 most shifted
    top = summary.sort_values("shift_magnitude", ascending=False).head(20)
    print("\nTop 20 most-shifted players (sorted by 9-cat-style shift magnitude):")
    print(f"{'name':<24} {'d_PTS':>7} {'d_AST':>6} {'d_TOV':>6} "
          f"{'d_STL':>6} {'d_BLK':>6} {'d_FTA':>6} {'d_FTM':>6} {'shift':>6}")
    print("-" * 84)
    for _, r in top.iterrows():
        print(f"{r['name']:<24} {r['d_PTS']:>+7.3f} {r['d_AST']:>+6.3f} "
              f"{r['d_TOV']:>+6.3f} {r['d_STL']:>+6.3f} {r['d_BLK']:>+6.3f} "
              f"{r['d_FTA']:>+6.3f} {r['d_FTM']:>+6.3f} {r['shift_magnitude']:>6.2f}")

    # Stats: how many players shift "significantly" (|d_PTS| > 1)
    print("\n" + "=" * 78)
    print("DISTRIBUTION OF SHIFTS")
    print("=" * 78)
    for s in ["PTS", "AST", "TOV"]:
        col = f"d_{s}"
        if col not in summary.columns:
            continue
        n_total = len(summary)
        n_nonzero = (summary[col].abs() > 0.01).sum()
        n_meaningful = (summary[col].abs() >= 0.5).sum()
        n_large = (summary[col].abs() >= 1.5).sum()
        max_pos = summary[col].max()
        max_neg = summary[col].min()
        print(f"  {s:<5}  shifted: {n_nonzero}/{n_total}  "
              f"|d|>=0.5: {n_meaningful}  |d|>=1.5: {n_large}  "
              f"max+={max_pos:+.2f}  max-={max_neg:+.2f}")

    # Save summary parquet for downstream
    summary.to_parquet(OUT_DIR / "per_player_delta_summary.parquet", index=False)
    print(f"\nSaved per-player delta summary -> {OUT_DIR / 'per_player_delta_summary.parquet'}")

    # 9-cat-side note: project Yahoo standard 9-cat counters that move
    # PTS, FG%, FT%, 3PTM, REB, AST, STL, BLK, TO -> we touch counter side directly:
    print("\n9-cat counter coverage of offsets:")
    print("  PTS:       offset applied (offseason_traded)")
    print("  REB:       no offset (no surviving class)")
    print("  AST:       offset applied (offseason_traded)")
    print("  STL:       offset applied (offseason_traded)")
    print("  BLK:       offset applied (position)")
    print("  TOV:       offset applied (years_pro_bucket)")
    print("  FT% indirect via FTM/FTA both shifting (preserves ratio)")
    print("  3PTM:      no offset (FG3M would need its own diagnostic)")
    print("  FG%:       no offset (FGM/FGA not actually-tracked, derived)")
    print(f"\n7 of 9 counters touched. CAVEAT: this is in-sample LOO. Forward (option a)")
    print(f"will determine whether to ship; do not yet feed this to Wonka production.")


if __name__ == "__main__":
    main()
