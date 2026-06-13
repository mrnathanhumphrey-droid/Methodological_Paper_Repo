"""Probe 11 — V2 cross-climate lag-aware operational test at MA Pvoutput.

Mirror of Probe 9 (DKA lag-aware operational model), now applied to MA Pvoutput
cluster (n=19 co-located residential rooftop systems in Concord/Acton MA,
temperate-humid PVCZ 33).

Pre-specified hypothesis (decision matrix laid out before running):

If MA shows lag-2-4 enrichment at high K (K≥16 ≈ 85% of fleet, matching DKA's K≥11):
- CROSS-CLIMATE OPERATIONAL VALIDATION: V2 lag-2-4 mechanism generalizes;
  paper claim is stronger; residential homeowners ARE getting cleanings on a
  weekly cadence (surprising, would prompt investigation)

If MA shows NO lag-2-4 enrichment at high K:
- Supports CLM-101 interpretation (a): residential homeowners don't pay
  cleaning crews; all cleaning at MA is natural rain. The METHODOLOGY
  generalizes (synchrony detected per Probe 6) but the OPERATIONAL DECOMPOSITION
  correctly produces a null at a site with no operational signal.
- This is also a valid result - it demonstrates the methodology
  CORRECTLY DISTINGUISHES sites with vs without operational cleaning.

Either outcome strengthens V2 publication track 1:
- Validation gives cross-climate replication
- Correctly-null gives methodology-discriminability proof
"""
import os, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))

RECS = ROOT / "data/processed/probe6_recovery_dates.csv"
PRECIP = ROOT / "data/processed/probe6b_rain_precip.csv"
OUT_LAGS = ROOT / "data/processed/probe11_MA_lag_table.csv"
OUT_SUM  = ROOT / "data/processed/probe11_MA_lag_summary.csv"
OUT_WIN  = ROOT / "data/processed/probe11_MA_lag_windows.csv"

RAIN_THR = 1.0
FUZZ = 1


def days_since_last_rain(target_dates, rain_days_sorted):
    out = []
    for d in target_dates:
        idx = np.searchsorted(rain_days_sorted, d, side="right") - 1
        if idx < 0:
            out.append(np.nan)
        else:
            out.append((d - rain_days_sorted[idx]).days)
    return np.array(out)


def main():
    print("Loading ERA5 precip cache (Probe 6b)...")
    precip = pd.read_csv(PRECIP, parse_dates=["date"]).set_index("date")["precip_mm"]
    rain_days = sorted(set(d.normalize() for d in precip.index[precip >= RAIN_THR]))
    rain_days_arr = np.array(rain_days)
    span_start = precip.index.min().normalize()
    span_end = precip.index.max().normalize()
    span_days = pd.date_range(span_start, span_end, freq="D")
    print(f"  Span {span_start.date()} - {span_end.date()}, rain days={len(rain_days)} ({len(rain_days)/len(span_days)*100:.1f}%)")

    print("\nLoading Probe 6 MA recovery dates...")
    df = pd.read_csv(RECS)
    df["recovery_date"] = pd.to_datetime(df["recovery_date"])
    sys_recs = {k: set(g["recovery_date"]) for k, g in df.groupby("system")}
    n_sys = len(sys_recs)
    print(f"  systems: {n_sys}")

    # K-consensus
    day_count = {}
    for key, dates in sys_recs.items():
        for d in dates:
            for k in range(-FUZZ, FUZZ + 1):
                day_count.setdefault(d + pd.Timedelta(days=k), set()).add(key)

    # Random null
    rng = np.random.default_rng(seed=20260531)
    random_dates = pd.to_datetime(rng.choice(span_days.normalize(), size=2000, replace=False))
    random_lags = days_since_last_rain(sorted(random_dates), rain_days_arr)
    random_lags = random_lags[~np.isnan(random_lags)]

    # K-thresholds: at DKA K≥11 of 13 = 85% of fleet. At MA: 85% of 19 = 16.
    # We test K = 1, 8, 11, 13, 15, 16, 17 — including 16/17 as high-K equivalents
    ks = [1, 4, 8, 11, 13, 15, 16, 17]

    print(f"\n=== MA Lag Analysis ===")
    print(f"{'K':>3} {'n_days':>7} {'med_lag':>8} {'mean_lag':>9} {'frac_lag_0-1':>13} {'frac_lag_2-4':>13}")

    lag_table_rows = []
    summary_rows = []

    rnd_frac_01 = float(np.mean((random_lags >= 0) & (random_lags <= 1)))
    rnd_frac_24 = float(np.mean((random_lags >= 2) & (random_lags <= 4)))
    summary_rows.append({
        "label": "random_climatology", "n": int(len(random_lags)),
        "median_lag": float(np.median(random_lags)),
        "mean_lag": float(np.mean(random_lags)),
        "frac_lag_0_1": rnd_frac_01, "frac_lag_2_4": rnd_frac_24,
        "ks_vs_random_p": np.nan,
    })
    print(f"  baseline (random): frac_lag_0-1={rnd_frac_01*100:.1f}%, frac_lag_2-4={rnd_frac_24*100:.1f}%")

    for K in ks:
        days_at_k = sorted(set(d for d, syss in day_count.items() if len(syss) >= K))
        if not days_at_k: continue
        lags = days_since_last_rain(days_at_k, rain_days_arr)
        lags = lags[~np.isnan(lags)]
        if len(lags) < 3: continue
        med = float(np.median(lags))
        mean = float(np.mean(lags))
        frac_01 = float(np.mean((lags >= 0) & (lags <= 1)))
        frac_24 = float(np.mean((lags >= 2) & (lags <= 4)))
        ks_stat, ks_p = stats.ks_2samp(lags, random_lags) if len(lags) >= 5 else (np.nan, np.nan)
        summary_rows.append({
            "label": f"K={K}", "n": int(len(lags)),
            "median_lag": med, "mean_lag": mean,
            "frac_lag_0_1": frac_01, "frac_lag_2_4": frac_24,
            "ks_vs_random_p": float(ks_p) if not np.isnan(ks_p) else np.nan,
        })
        print(f"{K:>3d} {len(lags):>7d} {med:>8.1f} {mean:>9.2f} {frac_01*100:>11.1f}% {frac_24*100:>11.1f}%")
        for lag in lags:
            lag_table_rows.append({"K": K, "lag_days_since_rain": int(lag)})

    pd.DataFrame(lag_table_rows).to_csv(OUT_LAGS, index=False)
    pd.DataFrame(summary_rows).to_csv(OUT_SUM, index=False)
    print(f"\nWrote {OUT_LAGS.name}, {OUT_SUM.name}")

    # ===================================================================
    # Window robustness sweep at MA (mirror of Probe 10)
    # ===================================================================
    print("\n=== Window robustness at MA (combined K>=16 ≈ 85% of fleet) ===")
    # Aggregate K=16,17
    high_K_lags = np.concatenate([
        np.array([r["lag_days_since_rain"] for r in lag_table_rows if r["K"] == K])
        for K in [16, 17]
        if any(r["K"] == K for r in lag_table_rows)
    ])
    # Also K=13 (≈DKA K=11 level proportionally)
    mid_K_lags = np.array([r["lag_days_since_rain"] for r in lag_table_rows if r["K"] == 13])

    windows = [("lag 1-3", 1, 3), ("lag 2-3", 2, 3), ("lag 2-4", 2, 4),
               ("lag 3-5", 3, 5), ("lag 1-5", 1, 5), ("lag 0-7", 0, 7),
               ("lag 5-7", 5, 7), ("lag 8-14", 8, 14)]
    print(f"\n{'window':<10} {'K-group':>10} {'n':>4} {'obs':>4} {'obs_pct':>8} {'base_pct':>9} {'lift':>5} {'p_high':>9} {'p_low':>9}")
    win_rows = []
    for label, lo, hi in windows:
        base_in = float(np.mean((random_lags >= lo) & (random_lags <= hi)))
        for grp_name, lags in [("K=16-17", high_K_lags), ("K=13", mid_K_lags)]:
            n = int(len(lags))
            obs = int(np.sum((lags >= lo) & (lags <= hi)))
            obs_pct = obs / n if n > 0 else 0
            lift = obs_pct / base_in if base_in > 0 else float("nan")
            p_high = 1 - stats.binom.cdf(obs - 1, n, base_in) if n > 0 else np.nan
            p_low = stats.binom.cdf(obs, n, base_in) if n > 0 else np.nan
            print(f"  {label:<10} {grp_name:>10} {n:>4d} {obs:>4d} {obs_pct*100:>6.1f}% {base_in*100:>7.1f}% {lift:>4.2f}x {p_high:>8.4f} {p_low:>8.4f}")
            win_rows.append({"window": label, "lo": lo, "hi": hi, "K_group": grp_name,
                             "n": n, "obs": obs, "obs_pct": obs_pct, "base_pct": base_in,
                             "lift": lift, "p_one_sided_high": p_high, "p_one_sided_low": p_low})
        print()

    pd.DataFrame(win_rows).to_csv(OUT_WIN, index=False)
    print(f"Wrote {OUT_WIN.name}")

    # ===================================================================
    # Decision matrix readout
    # ===================================================================
    print("\n=== VERDICT ===")
    # Focus on K=16-17 lag 2-4
    k1617_24 = [r for r in win_rows if r["window"] == "lag 2-4" and r["K_group"] == "K=16-17"][0]
    if k1617_24["n"] >= 5:
        if k1617_24["p_one_sided_high"] < 0.05:
            print(f"OPERATIONAL SIGNAL AT MA: K=16-17 lag-2-4 enrichment {k1617_24['lift']:.2f}x, p={k1617_24['p_one_sided_high']:.4f}")
            print(f"  Cross-climate validation: V2 operational mechanism generalizes")
        else:
            print(f"NO OPERATIONAL SIGNAL at MA K=16-17 lag-2-4 (lift {k1617_24['lift']:.2f}x, p={k1617_24['p_one_sided_high']:.4f})")
            print(f"  Supports CLM-101 (a): residential cluster has no operational cleaning")
            print(f"  Methodology CORRECTLY produces null at site without operational signal")
    else:
        print(f"MA K=16-17 n={k1617_24['n']} too small for confident verdict; fall back to K=13")

    # K=13 secondary
    k13_24 = [r for r in win_rows if r["window"] == "lag 2-4" and r["K_group"] == "K=13"][0]
    print(f"  Secondary check K=13 lag-2-4: lift {k13_24['lift']:.2f}x, p_high={k13_24['p_one_sided_high']:.4f}")

    # Late-lag control
    k1617_814 = [r for r in win_rows if r["window"] == "lag 8-14" and r["K_group"] == "K=16-17"][0]
    print(f"  Late-lag control K=16-17 lag 8-14: obs {k1617_814['obs_pct']*100:.1f}% vs baseline {k1617_814['base_pct']*100:.1f}%")


if __name__ == "__main__":
    main()
