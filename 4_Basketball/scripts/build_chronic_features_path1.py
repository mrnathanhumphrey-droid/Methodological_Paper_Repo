"""Rebuild chronic_injury_features using Path 1 derived severity.

Source: pro_sports_injuries_with_derived_severity.parquet (100% coverage on
resolved-id relinquished events).

Output:
    data/parquet/chronic_injury_features_path1.parquet
        Per (nba_api_id, target_year), trailing 3-year window:
            n_events_3y, total_games_missed_3y, pct_games_missed_3y,
            weighted_severity_3y, n_long_term_3y, n_out_for_season_3y,
            body-part counts.

    data/parquet/wonka_variance_multiplier.parquet
        Per nba_api_id (latest target_year), the variance multiplier to apply
        to v6 posterior width: variance_mult = 1.0 + alpha * pct_games_missed_3y.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"

OUT_FEATURES = PQ / "chronic_injury_features_path1.parquet"
OUT_WONKA = PQ / "wonka_variance_multiplier.parquet"

# Severity score mapping for path-1 derived severity
SEVERITY_SCORE = {
    "single_game": 0,
    "short_term": 1,
    "medium_term": 2,
    "long_term": 3,
    "out_for_season": 4,
}

TEAM_GAMES_PER_SEASON = 82
WINDOW_YEARS = 3
TARGET_YEARS = [2022, 2023, 2024, 2025]
ALPHA_VARIANCE = 0.6  # variance_mult = 1 + alpha * pct_games_missed (capped)
VARIANCE_MULT_CAP = 1.40

# Body-part categorization (regex-based, matched against notes_raw)
BODY_PART_PATTERNS = {
    "lower_body_muscular": r"\b(hamstring|calf|quad|groin|adductor|hip flexor|achilles)\b",
    "upper_body_muscular": r"\b(shoulder|rotator|deltoid|bicep|tricep|pectoral|lat)\b",
    "extremity": r"\b(ankle|foot|toe|knee|wrist|hand|finger|elbow)\b",
    "structural": r"\b(back|spine|lumbar|disc|hip|pelvis|rib|abdominal)\b",
    "head_neuro": r"\b(concussion|head|neck|cervical|migraine|nerve)\b",
    "illness_other": r"\b(flu|illness|virus|infection|covid|cold|fever|stomach|gi)\b",
}


def categorize_body_part(notes: str) -> str:
    """Return first matching body-part category, or 'unknown'."""
    if pd.isna(notes):
        return "unknown"
    s = str(notes).lower()
    import re
    for cat, pat in BODY_PART_PATTERNS.items():
        if re.search(pat, s):
            return cat
    return "unknown"


def main():
    print("Loading PST with path-1 derived severity...")
    pst = pd.read_parquet(PQ / "pro_sports_injuries_with_derived_severity.parquet")
    pst["event_date"] = pd.to_datetime(pst["event_date"])
    pst["event_year"] = pst["event_date"].dt.year

    # Filter to resolved-id relinquished events with derived severity
    rel = pst[(pst["side"] == "relinquished") &
              (pst["nba_api_id"].notna()) &
              (pst["derived_severity"].notna())].copy()
    rel["nba_api_id"] = rel["nba_api_id"].astype(int)
    rel["games_missed"] = pd.to_numeric(rel["games_missed"], errors="coerce")
    # Path 1 uses 999 as a sentinel for "no return this season" — clip to one
    # season so a single out_for_season event doesn't dominate a 3y sum
    rel["games_missed"] = rel["games_missed"].clip(upper=TEAM_GAMES_PER_SEASON)
    rel["severity_score"] = rel["derived_severity"].map(SEVERITY_SCORE).fillna(0)

    # Body-part categorization
    print("Categorizing body parts from notes_raw...")
    notes_col = "notes_raw" if "notes_raw" in rel.columns else "notes"
    if notes_col in rel.columns:
        rel["body_part_category"] = rel[notes_col].apply(categorize_body_part)
    else:
        rel["body_part_category"] = "unknown"
    print(f"Resolved relinquished events: {len(rel)}")
    print(rel["derived_severity"].value_counts().to_string())

    # Build per-(player, target_year) features over trailing 3-year window
    print("\nBuilding chronic features per target year...")
    all_feats = []
    for ty in TARGET_YEARS:
        # Window: events in [ty-3, ty-1] calendar years -> features for predicting ty season
        window = rel[(rel["event_year"] >= ty - WINDOW_YEARS) &
                     (rel["event_year"] <= ty - 1)].copy()
        if len(window) == 0:
            continue
        grp = window.groupby("nba_api_id").agg(
            n_events_3y=("event_date", "count"),
            total_games_missed_3y=("games_missed", "sum"),
            weighted_severity_3y=("severity_score", "sum"),
            n_long_term_3y=("derived_severity",
                            lambda x: (x == "long_term").sum()),
            n_out_for_season_3y=("derived_severity",
                                 lambda x: (x == "out_for_season").sum()),
        ).reset_index()
        # Body-part counts (pivot)
        bp = window.groupby(["nba_api_id", "body_part_category"]).size().unstack(
            fill_value=0).reset_index()
        for cat in ["lower_body_muscular", "upper_body_muscular", "extremity",
                    "structural", "head_neuro", "illness_other", "unknown"]:
            col = f"chronic_{cat}_count_3y"
            if cat in bp.columns:
                bp = bp.rename(columns={cat: col})
            else:
                bp[col] = 0
        bp = bp[["nba_api_id"] + [f"chronic_{c}_count_3y" for c in
                                    ["lower_body_muscular", "upper_body_muscular",
                                     "extremity", "structural", "head_neuro",
                                     "illness_other", "unknown"]]]
        grp = grp.merge(bp, on="nba_api_id", how="left").fillna(0)
        # Pct games missed (denom = 3*82 team games)
        denom = WINDOW_YEARS * TEAM_GAMES_PER_SEASON
        grp["pct_games_missed_3y"] = (grp["total_games_missed_3y"] / denom).clip(0, 1)
        grp["target_year"] = ty
        all_feats.append(grp)

    feats = pd.concat(all_feats, ignore_index=True)
    print(f"\nChronic feature rows: {len(feats)}")
    print(f"  Distinct players: {feats['nba_api_id'].nunique()}")
    print(f"  Per target_year: {feats['target_year'].value_counts().sort_index().to_dict()}")
    print()
    print("--- weighted_severity_3y distribution (path-1) ---")
    print(feats["weighted_severity_3y"].describe().to_string())
    print()
    print("--- pct_games_missed_3y distribution ---")
    print(feats["pct_games_missed_3y"].describe().to_string())

    feats.to_parquet(OUT_FEATURES, index=False)
    print(f"\nSaved -> {OUT_FEATURES}")

    # ---- Build Wonka variance multiplier for current target year (latest available)
    latest_ty = feats["target_year"].max()
    print(f"\nBuilding Wonka variance multiplier for target_year={latest_ty}...")
    latest = feats[feats["target_year"] == latest_ty][
        ["nba_api_id", "n_events_3y", "total_games_missed_3y",
         "pct_games_missed_3y", "weighted_severity_3y",
         "n_long_term_3y", "n_out_for_season_3y"]
    ].copy()
    latest["variance_mult_pct"] = 1.0 + ALPHA_VARIANCE * latest["pct_games_missed_3y"]
    latest["variance_mult_pct"] = latest["variance_mult_pct"].clip(upper=VARIANCE_MULT_CAP)

    # Alternative multiplier: severity-anchored (gives long-term injuries more punch)
    sev_norm = (latest["weighted_severity_3y"] / 12).clip(0, 1)  # 12 = ~3 long-term/year
    latest["variance_mult_severity"] = (1.0 + ALPHA_VARIANCE * sev_norm).clip(upper=VARIANCE_MULT_CAP)

    # Recommended multiplier: max of the two (whichever is higher = more conservative)
    latest["variance_mult"] = np.maximum(latest["variance_mult_pct"],
                                          latest["variance_mult_severity"])

    latest.to_parquet(OUT_WONKA, index=False)
    print(f"Saved -> {OUT_WONKA}")
    print(f"  rows: {len(latest)}")

    # Headlines
    print("\n=== Top 15 highest-variance players (most chronic) ===")
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    name_map = dict(zip(meta["nba_api_id"].astype(int), meta["name"]))
    top = latest.sort_values("variance_mult", ascending=False).head(15).copy()
    top["name"] = top["nba_api_id"].map(name_map)
    for _, r in top.iterrows():
        print(f"  {r['name']!s:<24} variance_mult={r['variance_mult']:.3f}  "
              f"games_missed_3y={int(r['total_games_missed_3y']):>3}  "
              f"pct={100*r['pct_games_missed_3y']:.1f}%  "
              f"long_term={int(r['n_long_term_3y'])}  "
              f"out_for_season={int(r['n_out_for_season_3y'])}")

    # Sanity check known chronics
    print("\n=== Known chronics spot-check ===")
    for name in ["Embiid", "Kawhi", "Zion", "Lillard", "Anthony Davis",
                 "Kyrie", "Williamson", "Paul George"]:
        m = top[top["name"].astype(str).str.contains(name, na=False, case=False)]
        if len(m) == 0:
            # search in latest
            full = latest.copy()
            full["name"] = full["nba_api_id"].map(name_map)
            m = full[full["name"].astype(str).str.contains(name, na=False, case=False)]
        if len(m) > 0:
            r = m.iloc[0]
            print(f"  {r['name']!s:<24} variance_mult={r['variance_mult']:.3f}  "
                  f"games_missed_3y={int(r['total_games_missed_3y']):>3}")
        else:
            print(f"  {name}: not found")


if __name__ == "__main__":
    main()
