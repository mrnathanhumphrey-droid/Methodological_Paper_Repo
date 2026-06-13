"""Cheap PTS-only forward validation.

Uses the existing 22-23 PTS v4-lite audit to derive class offsets, then applies
them to the 23-24 v6 ship's PTS column. Measures whether the
'offseason_traded x PTS' (and other class) signals from 23-24 actually
replicate when learned on 22-23.

This is the cheapest possible forward test — no fits, no chain rebuild,
single-stat. PTS is the largest residual and our highest-SNR class signal,
so this answers ~80% of "do the offsets generalize across seasons" with
zero CPU.
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
AUDIT_2223_PTS = REPO / "audit_runs" / "20260501T222551Z" / "skill_backtest_PTS_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22__2022-23" / "per_player_projections.csv"
SHIP_2324 = REPO / "audit_runs" / "unified_ship_v6" / "per_player_projections_2023-24.csv"


def attach_class_features(df, target_year):
    """target_year: 2022 -> 22-23 season; 2023 -> 23-24 season."""
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
    draft = pd.read_parquet(PQ / "nba_draft_data.parquet")
    pick_map = dict(zip(draft["nba_api_id"].dropna().astype(int),
                         draft.dropna(subset=["nba_api_id"])["draft_pick"]))
    df["draft_pick"] = df["nba_api_id"].astype(int).map(pick_map)
    def pick_bucket(p):
        if pd.isna(p): return "undrafted"
        p = int(p)
        if p <= 5: return "top5"
        if p <= 14: return "lottery"
        if p <= 30: return "late_first"
        return "second"
    df["draft_pick_tier"] = df["draft_pick"].apply(pick_bucket)
    # Offseason traded for the target season
    tx = pd.read_parquet(PQ / "pro_sports_transactions.parquet")
    tx["event_date"] = pd.to_datetime(tx["event_date"])
    traded = set(tx[(tx["transaction_type"] == "trade") &
                    (tx["event_date"] >= pd.Timestamp(f"{target_year}-04-15")) &
                    (tx["event_date"] <= pd.Timestamp(f"{target_year}-10-24")) &
                    (tx["nba_api_id"].notna())]["nba_api_id"].astype(int)) if "nba_api_id" in tx.columns else set()
    df["offseason_traded"] = df["nba_api_id"].astype(int).isin(traded)
    return df


def noise_floor(df, class_col, res_col):
    sub = df.dropna(subset=[class_col, res_col]).copy()
    grouped = sub.groupby(class_col, observed=True)[res_col].agg(
        ["mean", "count"]).reset_index()
    grouped = grouped[grouped["count"] >= 2]
    if len(grouped) < 2:
        return None
    sd_obs = grouped["mean"].std(ddof=1)
    overall_var = sub[res_col].var(ddof=1)
    n_per_class = grouped["count"].mean()
    se_samp = np.sqrt(overall_var / n_per_class)
    snr = sd_obs / se_samp if se_samp > 0 else np.nan
    return {"snr": snr, "n_classes": len(grouped),
            "class_means": dict(zip(grouped[class_col], grouped["mean"]))}


def main():
    if not AUDIT_2223_PTS.exists():
        print(f"MISSING audit: {AUDIT_2223_PTS}")
        sys.exit(1)
    print("Loading 22-23 PTS v4-lite audit...")
    a = pd.read_csv(AUDIT_2223_PTS)
    a["nba_api_id"] = a["nba_api_id"].astype(int)
    print(f"  audit rows: {len(a)}")
    a = a.dropna(subset=["actual", "proj_mean"]).copy()
    print(f"  with actuals: {len(a)}")
    a["PTS_residual"] = a["actual"] - a["proj_mean"]
    print(f"  mean residual: {a['PTS_residual'].mean():+.4f}")
    print(f"  SD residual:   {a['PTS_residual'].std(ddof=1):.4f}")

    a = attach_class_features(a, target_year=2022)

    # ============== Run noise-floor on PTS residual x classes for 22-23 ==============
    classes = ["position", "age_bucket", "offseason_traded",
               "years_pro_bucket", "draft_pick_tier"]
    print("\n" + "=" * 70)
    print("PTS residual SNR on 22-23 cohort (looking for 'real' classes)")
    print("=" * 70)
    survivors = []
    for c in classes:
        r = noise_floor(a, c, "PTS_residual")
        if r is None:
            continue
        verdict = ("REAL" if r["snr"] >= 1.5
                   else "marginal" if r["snr"] >= 1.05
                   else "noise")
        print(f"  {c:<22} SNR={r['snr']:.2f}  classes={r['n_classes']}  {verdict}")
        if r["snr"] >= 1.5:
            survivors.append((c, r["snr"], r["class_means"]))
    survivors.sort(key=lambda x: -x[1])

    if not survivors:
        print("\n  No PTS class survived SNR>=1.5 in 22-23. Forward validation: REJECTED.")
        return

    # Pick top-1 (parsimony rule)
    top_cls, top_snr, top_means = survivors[0]
    print(f"\n  TOP-1 class for PTS: {top_cls} (SNR={top_snr:.2f})")
    print(f"  Class means (22-23): {top_means}")

    # ============== Apply 22-23 offsets to 23-24 ship PTS ==============
    print("\nLoading 23-24 v6 ship + actuals...")
    ship = pd.read_csv(SHIP_2324)
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    ship = ship.dropna(subset=["PTS_actual"]).copy()
    print(f"  cohort: {len(ship)}")

    ship = attach_class_features(ship, target_year=2023)

    # Apply offset: add class mean residual (22-23) to projection (because residual
    # was actual - projection, so mean residual = how much we under-projected)
    ship["PTS_offset"] = ship[top_cls].map(top_means).fillna(0.0)
    ship["PTS_proj_corrected"] = ship["PTS_proj"] + ship["PTS_offset"]

    # MAE before/after
    base_mae = (ship["PTS_actual"] - ship["PTS_proj"]).abs().mean()
    new_mae = (ship["PTS_actual"] - ship["PTS_proj_corrected"]).abs().mean()
    delta = new_mae - base_mae
    pct = 100 * delta / base_mae

    print("\n" + "=" * 70)
    print("FORWARD VALIDATION: 22-23 -> 23-24 PTS only (CHEAP test)")
    print("=" * 70)
    print(f"\n  Class used:           {top_cls}")
    print(f"  22-23 SNR:            {top_snr:.2f}")
    print(f"  23-24 baseline PTS MAE:        {base_mae:.4f}")
    print(f"  23-24 corrected PTS MAE:       {new_mae:.4f}")
    print(f"  Delta:                {delta:+.4f}")
    print(f"  Pct change:           {pct:+.2f}%")

    # Per-class breakdown of correction effect
    print("\n  Per-class correction details (23-24 cohort):")
    for cls_val, off in sorted(top_means.items(), key=lambda x: x[1]):
        n = (ship[top_cls] == cls_val).sum()
        if n == 0:
            continue
        sub = ship[ship[top_cls] == cls_val]
        b = (sub["PTS_actual"] - sub["PTS_proj"]).abs().mean()
        a = (sub["PTS_actual"] - sub["PTS_proj_corrected"]).abs().mean()
        print(f"    {str(cls_val):<14}  offset={off:+.3f}  n={n:>3}  "
              f"base={b:.3f}  corr={a:.3f}  delta={a-b:+.3f}")

    # Verdict
    print("\n" + "=" * 70)
    print("VERDICT (PTS-only)")
    print("=" * 70)
    if pct < -2.0:
        print(f"  STRONG forward generalization on PTS ({pct:+.2f}%).")
        print(f"  v6.1 PTS offset table from 22-23 -> 23-24 is ship-ready.")
    elif pct < -0.5:
        print(f"  MODERATE forward generalization ({pct:+.2f}%).")
        print(f"  Consider shrinkage; offsets shrink across seasons but persist.")
    elif pct < 0.5:
        print(f"  WASH ({pct:+.2f}%). PTS class effect is season-specific.")
    else:
        print(f"  REJECTED ({pct:+.2f}%). 22-23 offsets actively hurt 23-24 PTS.")

    # Compare to in-sample LOO from earlier
    print(f"\n  Reference: in-sample LOO on 23-24 gave PTS -4.08% via offseason_traded class.")

    # Also test second-best survivor for robustness
    if len(survivors) > 1:
        second_cls, second_snr, second_means = survivors[1]
        print(f"\n  --- Sensitivity: testing 2nd-highest 22-23 class ({second_cls}, SNR={second_snr:.2f}) ---")
        ship["off2"] = ship[second_cls].map(second_means).fillna(0.0)
        ship["PTS_proj_corr2"] = ship["PTS_proj"] + ship["off2"]
        b2 = base_mae
        a2 = (ship["PTS_actual"] - ship["PTS_proj_corr2"]).abs().mean()
        p2 = 100 * (a2 - b2) / b2
        print(f"  23-24 PTS MAE with {second_cls} offsets: {a2:.4f} ({p2:+.2f}%)")


if __name__ == "__main__":
    main()
