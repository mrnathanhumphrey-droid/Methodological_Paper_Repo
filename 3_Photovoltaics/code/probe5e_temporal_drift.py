"""Probe 5e — Temporal drift of soiling rate over 12-year DKA record.

Has the soiling regime at Alice Springs changed? Tests for trends in annual
daily-soiling-rate, per system and pooled. Climate-change angle: Australian
dust intensification under drought, or improving cleaning protocols, would
both show up as a non-zero year-vs-rate slope.

Reuses Probe 5c's cached intervals (no SRR re-run needed)."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
INT = ROOT / "data/processed/probe5c_seasonal_soiling.csv"
OUT = ROOT / "data/processed/probe5e_temporal_drift.csv"


def main():
    df = pd.read_csv(INT, parse_dates=["start", "end", "mid_date"])
    print(f"Loaded {len(df)} intervals from {df['M_num'].nunique()} systems × phases\n")
    # filter to actual soiling intervals (negative slope = PR declining)
    soil = df[df["soiling_rate"] < 0].copy()
    soil["daily_loss_pct"] = -soil["soiling_rate"] * 100  # %/day positive
    soil["year"] = soil["mid_date"].dt.year
    print(f"Soiling-classified intervals (negative slope): {len(soil)}\n")
    print(f"Year range: {soil['year'].min()} - {soil['year'].max()}\n")

    # --- per-system per-year mean daily loss rate ---
    per = soil.groupby(["M_num", "phase", "year"])["daily_loss_pct"].agg(["mean", "count"]).reset_index()
    per.columns = ["M_num", "phase", "year", "mean_pct_day", "n_intervals"]
    per = per[per["n_intervals"] >= 3]  # require >=3 intervals/year/system
    print(f"Per-system-year observations (≥3 intervals): {len(per)}\n")

    # per-system temporal slope
    print("=== Per-system temporal slope (annual rate vs year) ===")
    print(f"{'sys':>10s} {'n_yr':>4s} {'mean':>8s} {'slope/yr':>9s} {'p':>7s} {'verdict':>10s}")
    sys_rows = []
    for (m, ph), g in per.groupby(["M_num", "phase"]):
        if len(g) < 5: continue
        slope, intercept, r, p, _ = stats.linregress(g["year"], g["mean_pct_day"])
        verdict = ("worsening" if (slope > 0 and p < 0.05)
                   else "improving" if (slope < 0 and p < 0.05)
                   else "flat")
        sys_rows.append({"M_num": m, "phase": ph, "n_years": len(g),
                         "mean_pct_day": float(g["mean_pct_day"].mean()),
                         "slope_pct_day_per_yr": float(slope), "p_value": float(p),
                         "verdict": verdict})
        print(f"M{m}_{ph:<4s} {len(g):4d} {g['mean_pct_day'].mean():7.4f} "
              f"{slope:+.5f} {p:7.4f} {verdict:>10s}")
    sdf = pd.DataFrame(sys_rows)

    # sign test on per-system slopes
    n_pos = int((sdf["slope_pct_day_per_yr"] > 0).sum())
    n_neg = int((sdf["slope_pct_day_per_yr"] < 0).sum())
    n_tot = len(sdf)
    p_sign = stats.binomtest(n_pos, n_tot, 0.5).pvalue if n_tot else None
    print(f"\nSign test on slopes: {n_pos} positive (worsening), {n_neg} negative (improving), n={n_tot}")
    print(f"Two-sided binomial p = {p_sign:.4f}")

    # pooled regression: all (system-year) observations -> regress mean rate on year
    print("\n=== Pooled temporal slope (all sys-yrs combined) ===")
    slope_p, intercept, r_p, p_p, _ = stats.linregress(per["year"], per["mean_pct_day"])
    print(f"  slope = {slope_p:+.5f} %/day/yr  (intercept {intercept:.3f} at yr 0)")
    print(f"  r^2 = {r_p**2:.4f}, p = {p_p:.4f}, n = {len(per)}")
    annual_pct = slope_p * 365 * 100  # convert daily-rate-change to annual-rate-change in pp
    print(f"  -> equivalent annual soiling rate change: {annual_pct:+.3f} percentage points per year")

    # mixed-model-lite: yearly grand mean
    print("\n=== Yearly grand mean (median across systems, daily rate) ===")
    yearly = per.groupby("year")["mean_pct_day"].agg(["median", "mean", "count"]).reset_index()
    print(yearly.round(4).to_string(index=False))
    # trend on grand-mean (yearly medians, less noisy)
    slope_g, intercept_g, r_g, p_g, _ = stats.linregress(yearly["year"], yearly["median"])
    print(f"\nGrand-median-yearly slope: {slope_g:+.5f} %/day/yr (p={p_g:.4f})")

    sdf.to_csv(OUT, index=False)
    print(f"\nWrote {OUT}")

if __name__ == "__main__":
    main()
