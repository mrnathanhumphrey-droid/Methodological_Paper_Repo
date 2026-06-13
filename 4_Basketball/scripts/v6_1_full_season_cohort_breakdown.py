"""v6.1 LOCKED full-season blind validation — cohort × position × career-stage breakdowns.

Stats: PTS, REB, AST, BLK, STL per game.
Filter: players with >=10 GP in 25-26.
Source: v6.1 LOCKED ship + 25-26 RS box scores for full-season actuals.

Output: audit_runs/v6_1_full_season_cohort/
  cohort_breakdown.csv  -- per-cell MAE table (long format)
  per_player_validation.csv  -- per-player projections vs actuals
  summary.md  -- narrative summary
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"
OUT_DIR = REPO / "audit_runs" / "v6_1_full_season_cohort"
OUT_DIR.mkdir(parents=True, exist_ok=True)

V6_1_SHIP = REPO / "audit_runs" / "unified_ship_v6_1_2025_26" / "per_player_projections_2025-26.csv"
ROOKIE_SUP = REPO / "audit_runs" / "cohort_widening_v0_2025_26" / "rookie_metadata_supplement.parquet"

STATS = ["PTS", "REB", "AST", "BLK", "STL"]
MIN_GP = 10


def position_class(p):
    if pd.isna(p) or not p or str(p).strip() == "":
        return "Forward"
    s = str(p).lower()
    if "center" in s: return "Center"
    if "guard" in s: return "Guard"
    return "Forward"


def main():
    print("[load] v6.1 LOCKED ship + box scores + metadata")
    ship = pd.read_csv(V6_1_SHIP)
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)

    bx = pd.read_parquet(PQ / "historical_box_scores.parquet")
    bx_25_26 = bx[(bx["season"] == "2025-26") &
                    (bx["season_type"] == "Regular Season")].copy()
    bx_25_26["minutes"] = pd.to_numeric(bx_25_26["minutes"], errors="coerce")
    bx_25_26 = bx_25_26[bx_25_26["minutes"] > 0]
    bx_25_26["nba_api_id"] = bx_25_26["nba_api_id"].astype(int)

    actuals = bx_25_26.groupby("nba_api_id").agg(
        gp_actual=("game_id", "nunique"),
        PTS_actual=("PTS", "mean"), REB_actual=("REB", "mean"),
        AST_actual=("AST", "mean"), BLK_actual=("BLK", "mean"),
        STL_actual=("STL", "mean"),
    ).reset_index()
    print(f"  25-26 RS players w/ any minutes: {len(actuals)}")

    # Map synthetic rookie IDs -> real IDs by name match
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    if ROOKIE_SUP.exists():
        sup = pd.read_parquet(ROOKIE_SUP)
        cols = ["nba_api_id", "name", "position", "draft_year", "debut_year"]
        meta = pd.concat([meta[cols], sup[cols]], ignore_index=True)
        # Build name -> real_id from base meta only
        meta_base = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
        real_name_id = dict(zip(meta_base["name"].str.lower().fillna(""),
                                  meta_base["nba_api_id"].astype(int)))
        rookie_real_id = {}
        for _, r in sup.iterrows():
            nm = (r["name"] or "").strip().lower()
            if nm in real_name_id:
                rookie_real_id[int(r["nba_api_id"])] = real_name_id[nm]
    else:
        rookie_real_id = {}
    meta["nba_api_id"] = meta["nba_api_id"].astype(int)

    ship["real_id"] = ship["nba_api_id"].map(
        lambda x: rookie_real_id.get(int(x), int(x))).astype(int)

    # Drop stale ship-side actuals (only filled for vets) before merging fresh
    stale_cols = [c for c in ship.columns if c.endswith("_actual")]
    ship = ship.drop(columns=stale_cols)

    # Join actuals via real_id
    df = ship.merge(actuals, left_on="real_id", right_on="nba_api_id",
                      how="left", suffixes=("", "_act"))

    # Filter to >=10 GP
    df = df[df["gp_actual"].fillna(0) >= MIN_GP].copy()
    print(f"  ship players w/ >=10 GP actuals: {len(df)} of {len(ship)}")

    # Compute residuals
    for stat in STATS:
        df[f"{stat}_resid"] = df[f"{stat}_actual"] - df[f"{stat}_per_game"]

    # Attach cohort/position/career-stage tags
    df = df.merge(meta[["nba_api_id", "position", "draft_year", "debut_year"]],
                    left_on="real_id", right_on="nba_api_id",
                    how="left", suffixes=("", "_m"))
    df["years_pro"] = df["debut_year"].where(df["debut_year"].notna(),
                                                df["draft_year"] + 1)
    df["years_pro"] = 2025 - df["years_pro"]

    # User-spec cohort: rookie = 0-1 prior NBA seasons (years_pro <= 1)
    df["cohort_simple"] = df["years_pro"].apply(
        lambda y: "rookie" if pd.isna(y) or y <= 1 else "vet")
    # Career stage: early 0-3, mid 4-9, late 10+
    df["career_stage"] = df["years_pro"].apply(
        lambda y: "early" if pd.isna(y) or y <= 3
        else ("mid" if y <= 9 else "late"))
    df["pos_class"] = df["position"].apply(position_class)
    # Positional ambiguity flag
    df["pos_ambig"] = df["position"].fillna("").str.contains("-")

    print(f"\n  cohort_simple: {df['cohort_simple'].value_counts().to_dict()}")
    print(f"  career_stage: {df['career_stage'].value_counts().to_dict()}")
    print(f"  pos_class: {df['pos_class'].value_counts().to_dict()}")
    print(f"  pos_ambig: {df['pos_ambig'].sum()} of {len(df)}")

    # ── Per-cell MAE/bias ──────────────────────────────────────────────
    rows = []

    def compute_cell(label, sub):
        for stat in STATS:
            r = sub[f"{stat}_resid"].dropna()
            if len(r) < 5:
                continue
            mae = r.abs().mean()
            bias = r.mean()
            sd = r.std(ddof=1)
            actual_mean = sub[f"{stat}_actual"].mean()
            rel_mae = mae / actual_mean * 100 if actual_mean else np.nan
            rows.append({
                "split": label["split"],
                "cell": label["cell"],
                "stat": stat,
                "n": len(r),
                "actual_mean": float(actual_mean),
                "MAE": float(mae),
                "bias": float(bias),
                "sd": float(sd),
                "MAE_pct_of_actual": float(rel_mae),
            })

    # Overall
    compute_cell({"split": "overall", "cell": "all"}, df)

    # By cohort_simple (vet vs rookie)
    for c in ["vet", "rookie"]:
        sub = df[df["cohort_simple"] == c]
        compute_cell({"split": "cohort_simple", "cell": c}, sub)

    # By position
    for p in ["Center", "Forward", "Guard"]:
        sub = df[df["pos_class"] == p]
        compute_cell({"split": "position", "cell": p}, sub)

    # By career stage
    for cs in ["early", "mid", "late"]:
        sub = df[df["career_stage"] == cs]
        compute_cell({"split": "career_stage", "cell": cs}, sub)

    # Cohort × position
    for c in ["vet", "rookie"]:
        for p in ["Center", "Forward", "Guard"]:
            sub = df[(df["cohort_simple"] == c) & (df["pos_class"] == p)]
            compute_cell({"split": "cohort_x_position",
                          "cell": f"{c}_{p}"}, sub)

    # Career stage × position
    for cs in ["early", "mid", "late"]:
        for p in ["Center", "Forward", "Guard"]:
            sub = df[(df["career_stage"] == cs) & (df["pos_class"] == p)]
            compute_cell({"split": "career_x_position",
                          "cell": f"{cs}_{p}"}, sub)

    # Positional-ambiguity flagged separately
    sub = df[df["pos_ambig"]]
    compute_cell({"split": "ambiguity", "cell": "pos_ambig_yes"}, sub)
    sub = df[~df["pos_ambig"]]
    compute_cell({"split": "ambiguity", "cell": "pos_ambig_no"}, sub)

    out = pd.DataFrame(rows)
    out_path = OUT_DIR / "cohort_breakdown.csv"
    out.to_csv(out_path, index=False)
    print(f"\n[save] {out_path}")

    # Per-player CSV
    out_cols = ["nba_api_id", "real_id", "name", "position", "pos_class",
                  "years_pro", "cohort_simple", "career_stage", "gp_actual"]
    for stat in STATS:
        out_cols += [f"{stat}_per_game", f"{stat}_actual", f"{stat}_resid"]
    df[out_cols].to_csv(OUT_DIR / "per_player_validation.csv", index=False)
    print(f"[save] {OUT_DIR / 'per_player_validation.csv'}")

    # Pretty-print summary
    print("\n" + "=" * 80)
    print("FULL-SEASON v6.1 LOCKED BLIND VALIDATION  (>=10 GP, 25-26 RS)")
    print("=" * 80)
    print(f"\nTotal eligible: {len(df)} players")
    print(f"  vets: {(df['cohort_simple']=='vet').sum()}, "
          f"rookies: {(df['cohort_simple']=='rookie').sum()}")
    print(f"  early: {(df['career_stage']=='early').sum()}, "
          f"mid: {(df['career_stage']=='mid').sum()}, "
          f"late: {(df['career_stage']=='late').sum()}")
    print(f"  Center: {(df['pos_class']=='Center').sum()}, "
          f"Forward: {(df['pos_class']=='Forward').sum()}, "
          f"Guard: {(df['pos_class']=='Guard').sum()}")

    print("\n--- OVERALL MAE per stat ---")
    for stat in STATS:
        r = df[f"{stat}_resid"].dropna()
        mae = r.abs().mean()
        bias = r.mean()
        am = df[f"{stat}_actual"].mean()
        print(f"  {stat}: n={len(r):4} MAE={mae:.3f}  bias={bias:+.3f}  "
              f"actual_mean={am:.3f}  rel={mae/am*100:.1f}%")

    print("\n--- BY COHORT_SIMPLE ---")
    for c in ["vet", "rookie"]:
        sub = df[df["cohort_simple"] == c]
        print(f"  {c} (n={len(sub)}):")
        for stat in STATS:
            r = sub[f"{stat}_resid"].dropna()
            if len(r) < 5: continue
            print(f"    {stat}: MAE={r.abs().mean():.3f}  "
                  f"bias={r.mean():+.3f}")

    print("\n--- BY POSITION ---")
    for p in ["Center", "Forward", "Guard"]:
        sub = df[df["pos_class"] == p]
        print(f"  {p} (n={len(sub)}):")
        for stat in STATS:
            r = sub[f"{stat}_resid"].dropna()
            if len(r) < 5: continue
            print(f"    {stat}: MAE={r.abs().mean():.3f}  "
                  f"bias={r.mean():+.3f}")

    print("\n--- BY CAREER STAGE ---")
    for cs in ["early", "mid", "late"]:
        sub = df[df["career_stage"] == cs]
        print(f"  {cs} (n={len(sub)}):")
        for stat in STATS:
            r = sub[f"{stat}_resid"].dropna()
            if len(r) < 5: continue
            print(f"    {stat}: MAE={r.abs().mean():.3f}  "
                  f"bias={r.mean():+.3f}")

    print("\nDONE.")


if __name__ == "__main__":
    main()
