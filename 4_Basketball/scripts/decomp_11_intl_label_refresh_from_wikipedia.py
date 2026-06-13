"""Refresh intl league labels from wikipedia_pre_nba_career substrate.

The current rookies_outcome_training has 28 rows labeled "unknown" because we
couldn't tell what intl league they came from. wikipedia_pre_nba_career.parquet
already has 135 prospects' league trajectory inferred (acb_spain, kls_serbia,
lnb_france, nbl_australia, gbl_greece, bbl_germany, etc.).

For each historical prospect, determine their PRIMARY pre-NBA league:
  - Take the latest non-NCAA stint before NBA debut
  - If all stints are NCAA, leave as NCAA_*
  - If latest stint is intl, use that league
  - Tag with league_canonical (intl_acb_spain / intl_kls_serbia / etc.)

Then refit outcome GBM with new labels.

Outputs:
    data/parquet/rookies_outcome_training_v2.parquet
    data/models/outcome_gbm_v2_*.txt
"""
from __future__ import annotations
import sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

PQ = Path("D:/NBA Projections/data/parquet")
OUT = PQ / "rookies_outcome_training_v2.parquet"


def canonicalize(label: str) -> str:
    if pd.isna(label): return None
    s = str(label).lower()
    if "acb" in s and "spain" in s: return "intl_acb_spain"
    if "kls" in s and "serbia" in s: return "intl_kls_serbia"
    if "lnb" in s and "france" in s: return "intl_lnb_france"
    if "nbl" in s and "australia" in s: return "intl_nbl_australia"
    if "gbl" in s and "greece" in s: return "intl_gbl_greece"
    if "bbl" in s and "germany" in s: return "intl_bbl_germany"
    if "bsl" in s and "israel" in s: return "intl_bsl_israel"
    if "tbsl" in s and "turkey" in s: return "intl_tbsl_turkey"
    if "lega" in s and "italy" in s: return "intl_lega_italy"
    if "g_league" in s or "gleague" in s: return "g_league"
    if "ote" in s: return "g_league_ote"
    return None


def main():
    wp = pd.read_parquet(PQ / "wikipedia_pre_nba_career.parquet")
    train = pd.read_parquet(PQ / "rookies_outcome_training.parquet")
    print(f"  wikipedia rows: {len(wp):,}  unique players: {wp['player_name_raw'].nunique()}")
    print(f"  training rows: {len(train):,}")

    wp = wp.copy()
    wp["league_canonical"] = wp["league_inferred"].apply(canonicalize)

    primary = (wp.dropna(subset=["league_canonical"])
                            .sort_values(["player_name_raw", "year_end"])
                            .groupby("player_name_raw")
                            .agg(primary_intl_league=("league_canonical", "last"),
                                       last_intl_year=("year_end", "last")))

    print(f"\n=== primary intl league distribution (historical pool) ===")
    print(primary["primary_intl_league"].value_counts().to_string())

    train = train.merge(primary, left_on="player_name_raw", right_index=True, how="left")

    def updated_label(row):
        current = row["pre_nba_league_label"]
        primary_intl = row.get("primary_intl_league")
        if pd.notna(primary_intl) and current in ("unknown", "intl_g_league"):
            return primary_intl
        if current == "unknown" and pd.notna(primary_intl):
            return primary_intl
        return current
    train["pre_nba_league_label_v2"] = train.apply(updated_label, axis=1)

    print(f"\n=== label distribution before vs after ===")
    before = train["pre_nba_league_label"].value_counts()
    after = train["pre_nba_league_label_v2"].value_counts()
    summary = pd.DataFrame({"before": before, "after": after}).fillna(0).astype(int)
    print(summary.to_string())

    train["pre_nba_league_label"] = train["pre_nba_league_label_v2"]
    train = train.drop(columns=["pre_nba_league_label_v2"])

    train.to_parquet(OUT, index=False)
    print(f"\nwrote: {OUT}")
    print(f"  total prospects: {len(train):,}")
    print(f"  prospects whose label changed: {(before != after).sum() if isinstance(before, pd.Series) else 'computed in summary above'}")


if __name__ == "__main__":
    main()
