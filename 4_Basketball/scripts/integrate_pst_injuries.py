"""Pro Sports Transactions injury integration — schema validator + chronic feature builder.

Plug-and-play once `pro_sports_injuries.parquet` lands in data/parquet/.

Steps:
  1. Schema validation against brief spec
  2. Coverage spot-checks (Embiid 50+ events, Klay ACL Jun 2019, etc.)
  3. Player ID resolution (name + team_context → nba_api_id)
  4. Chronic feature derivation (3y injury count by category, severity-weighted)
  5. Optional: integrate as feature into v6 MPG cascade and backtest

Usage:
  python scripts/integrate_pst_injuries.py --validate
  python scripts/integrate_pst_injuries.py --build-features
  python scripts/integrate_pst_injuries.py --backtest
  python scripts/integrate_pst_injuries.py --all
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(r"D:\NBA Projections")
INJURIES_PATH = REPO / "data" / "parquet" / "pro_sports_injuries.parquet"
TXNS_PATH = REPO / "data" / "parquet" / "pro_sports_transactions.parquet"
FEATURES_OUT = REPO / "data" / "parquet" / "chronic_injury_features.parquet"
META_PATH = REPO / "data" / "parquet" / "player_metadata_enriched.parquet"
OUT_DIR = REPO / "audit_runs" / "pst_integration"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_INJURY_COLS = [
    "event_date", "team_abbr", "player_name_raw", "notes_raw",
]

BODY_PART_CATEGORIES = {
    "structural": ["knee", "achilles", "acl", "meniscus", "labrum", "rotator_cuff", "spine", "back", "neck", "hip"],
    "lower_body_muscular": ["hamstring", "quad", "quadriceps", "calf", "groin", "shin"],
    "upper_body_muscular": ["shoulder", "elbow", "wrist", "oblique"],
    "extremity": ["foot", "ankle", "toe", "hand", "finger", "thumb"],
    "head_neuro": ["head", "concussion", "face", "eye", "jaw"],
    "illness_other": ["illness", "covid", "personal", "rest", "load_management", "ribs", "abdomen", "abdominal"],
}

SEVERITY_WEIGHT = {
    "out_for_season": 1.0,
    "surgery": 0.95,
    "indefinite": 0.7,
    "long_term": 0.6,
    "medium_term": 0.4,
    "short_term": 0.25,
    "day_to_day": 0.1,
    "game_time_decision": 0.05,
}

# Regex patterns for parsing notes_raw
import re
BODY_PART_PATTERNS = [
    ("achilles", r"\bachilles\b"),
    ("acl", r"\bacl\b"),
    ("meniscus", r"\bmeniscus\b"),
    ("knee", r"\bknee(s)?\b|\bpatell"),
    ("ankle", r"\bankle(s)?\b"),
    ("hamstring", r"\bhamstring(s)?\b"),
    ("quadriceps", r"\bquad(s|riceps)?\b"),
    ("calf", r"\bcalf|\bcalves\b"),
    ("groin", r"\bgroin\b|\badductor"),
    ("hip", r"\bhip(s)?\b"),
    ("back", r"\bback\b|\blumbar\b|\bspine\b"),
    ("neck", r"\bneck\b|\bcervical\b"),
    ("shoulder", r"\bshoulder(s)?\b|\brotator\b|\blabrum\b"),
    ("elbow", r"\belbow\b"),
    ("wrist", r"\bwrist\b"),
    ("hand", r"\bhand\b|\bfinger(s)?\b|\bthumb\b"),
    ("foot", r"\bfoot\b|\bfeet\b|\btoe(s)?\b"),
    ("oblique", r"\boblique\b"),
    ("ribs", r"\brib(s|cage)?\b"),
    ("abdomen", r"\babdom"),
    ("head", r"\bconcussion\b|\bhead\b"),
    ("face", r"\bface\b|\bjaw\b|\beye(s)?\b|\bnose\b"),
    ("illness", r"\billness\b|\bcovid\b|\bflu\b|\bvirus\b"),
    ("rest", r"\brest\b|\bload management\b|\bload\s+management\b"),
]

INJURY_TYPE_PATTERNS = [
    ("surgery", r"\bsurg(ery|ical)|\barthroscop"),
    ("torn", r"\btorn\b|\btore\b|\brupture(d)?\b"),
    ("fractured", r"\bfracture(d)?\b|\bbroken\b"),
    ("sprain", r"\bsprain"),
    ("strain", r"\bstrain"),
    ("contusion", r"\bcontusion|\bbruise"),
    ("soreness", r"\bsoreness|\bsore\b"),
    ("inflammation", r"\binflammation|\btendinitis|\btendonitis|\btendinopathy"),
    ("dislocation", r"\bdislocat"),
]

SEVERITY_PATTERNS = [
    ("out_for_season", r"out for (the )?season|season-ending|will miss (the rest of )?(this )?season|out indefinitely"),
    ("surgery", r"\bsurg(ery|ical)|underwent.*surg"),
    ("indefinite", r"\bindefinite|no timeline|out indefinitely"),
    ("long_term", r"\b\d+\s*(months?|month)\b|out (for )?\d+\s*months?"),
    ("medium_term", r"\bout\s+\d+\s*(weeks|wks)?\b|\d+-\d+\s*weeks?"),
    ("day_to_day", r"\bday[\s-]?to[\s-]?day\b|\bDTD\b"),
    ("game_time_decision", r"\bgame[\s-]?time\b|\bGTD\b|\bquestionable\b|\bdoubtful\b|\bprobable\b"),
]


def parse_notes(text: str | None) -> dict:
    """Extract body_part / injury_type / severity from raw notes text."""
    if text is None or pd.isna(text):
        return {"body_part": None, "injury_type": None, "severity": None}
    txt = str(text).lower()
    body_part = None
    for name, pat in BODY_PART_PATTERNS:
        if re.search(pat, txt):
            body_part = name
            break
    injury_type = None
    for name, pat in INJURY_TYPE_PATTERNS:
        if re.search(pat, txt):
            injury_type = name
            break
    severity = None
    for name, pat in SEVERITY_PATTERNS:
        if re.search(pat, txt):
            severity = name
            break
    return {"body_part": body_part, "injury_type": injury_type, "severity": severity}


def enrich_df_with_parsing(df: pd.DataFrame) -> pd.DataFrame:
    """Apply parse_notes to populate body_part/injury_type/severity columns if missing."""
    if "body_part" in df.columns and df["body_part"].notna().sum() > 0:
        return df  # already parsed
    parsed = df["notes_raw"].apply(parse_notes)
    df["body_part"] = parsed.apply(lambda x: x["body_part"])
    df["injury_type"] = parsed.apply(lambda x: x["injury_type"])
    df["severity"] = parsed.apply(lambda x: x["severity"])
    return df


def categorize_body_part(bp: str | None) -> str:
    if bp is None or pd.isna(bp):
        return "unknown"
    bp_lower = str(bp).lower().strip()
    for cat, keywords in BODY_PART_CATEGORIES.items():
        if any(k in bp_lower for k in keywords):
            return cat
    return "other"


def severity_score(sev: str | None) -> float:
    if sev is None or pd.isna(sev):
        return 0.0
    return SEVERITY_WEIGHT.get(str(sev).lower().strip(), 0.0)


def validate_schema(df: pd.DataFrame) -> dict:
    """Check incoming parquet matches brief spec. Return report dict."""
    actual = set(df.columns)
    expected = set(EXPECTED_INJURY_COLS)
    missing = expected - actual
    extra = actual - expected
    report = {
        "rows": int(len(df)),
        "columns_present": sorted(actual),
        "missing_from_brief": sorted(missing),
        "extra_beyond_brief": sorted(extra),
        "ok": len(missing) == 0,
    }
    if df.get("event_date") is not None:
        report["date_range"] = {
            "min": str(df["event_date"].min()),
            "max": str(df["event_date"].max()),
        }
    if "body_part" in df.columns:
        report["body_part_coverage_pct"] = float(df["body_part"].notna().mean() * 100)
    if "severity" in df.columns:
        report["severity_coverage_pct"] = float(df["severity"].notna().mean() * 100)
    return report


def coverage_spot_checks(df: pd.DataFrame) -> dict:
    """Run the validation criteria from the brief."""
    checks = {}
    df = df.copy()
    if "player_name_raw" in df.columns:
        df["pname_l"] = df["player_name_raw"].astype(str).str.lower()

        def count(name_pattern):
            return int(df[df["pname_l"].str.contains(name_pattern.lower(), na=False)].shape[0])

        checks["embiid_event_count"] = count("embiid")
        checks["embiid_check_pass"] = checks["embiid_event_count"] >= 50

        # Klay Thompson ACL June 2019
        if "event_date" in df.columns:
            klay = df[df["pname_l"].str.contains("klay thompson", na=False) &
                      df["event_date"].astype(str).str.contains("2019-06")]
            checks["klay_acl_2019_06_count"] = int(len(klay))
            checks["klay_check_pass"] = len(klay) >= 1

        # Joel Embiid meniscus Jan 2024
        if "event_date" in df.columns:
            embiid_men = df[df["pname_l"].str.contains("embiid", na=False) &
                            df["event_date"].astype(str).str.contains("2024-0[12]")]
            checks["embiid_2024_jan_feb_event_count"] = int(len(embiid_men))
    return checks


def resolve_player_ids(df: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """Map player_name_raw → nba_api_id. Use last-name + team context for ambiguity."""
    name_to_id = {}
    for _, r in meta.iterrows():
        if pd.notna(r.get("name")) and pd.notna(r.get("nba_api_id")):
            name_to_id[str(r["name"]).strip().lower()] = int(r["nba_api_id"])

    df = df.copy()
    df["nba_api_id"] = df["player_name_raw"].astype(str).str.strip().str.lower().map(name_to_id).astype("Int64")
    n_resolved = int(df["nba_api_id"].notna().sum())
    n_total = int(len(df))
    print(f"  Resolved {n_resolved}/{n_total} ({100*n_resolved/n_total:.1f}%) by exact name match")
    # TODO: fuzzy fallback for unresolved (hyphenated names, accents, suffixes)
    return df


def build_chronic_features(df: pd.DataFrame, target_year: int = 2023) -> pd.DataFrame:
    """For each player, compute injury features over the trailing 3 years before target_year."""
    if "event_date" not in df.columns or "nba_api_id" not in df.columns:
        raise ValueError("Need event_date and nba_api_id to build features")
    d = df.copy()
    d["event_date"] = pd.to_datetime(d["event_date"], errors="coerce")
    cutoff = pd.Timestamp(f"{target_year}-09-01")
    cutoff_3yr = cutoff - pd.DateOffset(years=3)
    d = d[(d["event_date"] >= cutoff_3yr) & (d["event_date"] < cutoff)]

    d["body_category"] = d["body_part"].apply(categorize_body_part) if "body_part" in d.columns else "unknown"
    d["sev_score"] = d["severity"].apply(severity_score) if "severity" in d.columns else 0.0

    # Per-player aggregates
    agg = d.groupby("nba_api_id").agg(
        n_events_3y=("event_date", "count"),
        weighted_severity_3y=("sev_score", "sum"),
    ).reset_index()

    # Per-player per-category counts
    cat_pivot = d.pivot_table(index="nba_api_id", columns="body_category",
                              values="event_date", aggfunc="count", fill_value=0).reset_index()
    cat_pivot.columns = [f"chronic_{c}_count_3y" if c != "nba_api_id" else "nba_api_id"
                         for c in cat_pivot.columns]

    feats = agg.merge(cat_pivot, on="nba_api_id", how="left")
    feats["target_year"] = target_year
    feats["nba_api_id"] = feats["nba_api_id"].astype(int)
    return feats


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--validate", action="store_true")
    p.add_argument("--build-features", action="store_true")
    p.add_argument("--backtest", action="store_true")
    p.add_argument("--all", action="store_true")
    args = p.parse_args()

    if not INJURIES_PATH.exists():
        print(f"❌ {INJURIES_PATH} does not exist yet. Waiting for fetcher to drop it.")
        return

    print(f"Loading {INJURIES_PATH}...")
    df = pd.read_parquet(INJURIES_PATH)
    print(f"  {len(df):,} rows, {len(df.columns)} columns")

    print("Running local parsing on notes_raw to derive body_part/injury_type/severity...")
    df = enrich_df_with_parsing(df)
    body_pct = df["body_part"].notna().mean() * 100
    inj_pct = df["injury_type"].notna().mean() * 100
    sev_pct = df["severity"].notna().mean() * 100
    print(f"  body_part extracted: {body_pct:.1f}%")
    print(f"  injury_type extracted: {inj_pct:.1f}%")
    print(f"  severity extracted: {sev_pct:.1f}%")

    if args.validate or args.all:
        print("\n=== Schema validation ===")
        rep = validate_schema(df)
        for k, v in rep.items():
            print(f"  {k}: {v}")
        if not rep["ok"]:
            print("[WARN] Schema drift from brief - investigate before proceeding")

        print("\n=== Coverage spot-checks ===")
        checks = coverage_spot_checks(df)
        for k, v in checks.items():
            print(f"  {k}: {v}")

    if args.build_features or args.all:
        print(f"\n=== Resolving player IDs ===")
        meta = pd.read_parquet(META_PATH)
        df_resolved = resolve_player_ids(df, meta)

        print(f"\n=== Building chronic features ===")
        for year in [2023, 2024]:
            feats = build_chronic_features(df_resolved, target_year=year)
            print(f"  target_year={year}: {len(feats)} players with features")
            print(f"    mean events/player: {feats['n_events_3y'].mean():.1f}")
            print(f"    mean weighted severity: {feats['weighted_severity_3y'].mean():.2f}")

            # Save the most recent year's features
            if year == 2023:
                feats.to_parquet(FEATURES_OUT, index=False)
                print(f"    saved to {FEATURES_OUT}")

    if args.backtest or args.all:
        print("\n=== Backtest integration ===")
        if not FEATURES_OUT.exists():
            print(f"  Run --build-features first. Features parquet not found.")
            return
        feats = pd.read_parquet(FEATURES_OUT)
        v6 = pd.read_csv("audit_runs/unified_ship_v6/per_player_projections_2023-24.csv")
        v6["nba_api_id"] = v6["nba_api_id"].astype(int)
        joined = v6.merge(feats, on="nba_api_id", how="left")
        joined["chronic_severity_normalized"] = joined["weighted_severity_3y"].fillna(0).clip(0, 5) / 5.0
        print(f"  v6 ship players with chronic feature: {joined['weighted_severity_3y'].notna().sum()}/{len(joined)}")
        print(f"  Top 10 chronic-severity players in v6 cohort:")
        top = joined.nlargest(10, "weighted_severity_3y")[["name", "weighted_severity_3y", "n_events_3y", "mpg"]]
        print(top.to_string(index=False))
        # TODO: actual MPG model retraining with chronic feature, MAE comparison


if __name__ == "__main__":
    sys.path.insert(0, str(REPO))
    main()
