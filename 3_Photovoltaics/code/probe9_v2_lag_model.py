"""Probe 9 — V2 LAG-AWARE OPERATIONAL MODEL

Skeptic-pass corollary (Probe 8 / memo 35): K=12-13 events at DKA show
suggestive but fuzz-fragile crash at ±1d. Reframe: instead of treating events
as either coincident with rain or not, model the LAG between rain and the
consensus event explicitly.

Pre-specified hypothesis (before running):
- H_NATURAL: at moderate K (say K=4-8), consensus events are coincident with
  or immediately after rain (lag 0-1 days dominant)
- H_OPERATIONAL: at high K (K=12-13), consensus events show a SHIFTED lag
  distribution — peak at 2-4 days post-rain (matching site-visit scheduling)
- H_NULL: high-K events show the same lag distribution as random days
  (i.e., just climatology)

Discrimination:
- If high-K lag distribution PEAKS at 2-4 days AND differs significantly from
  both random and from K=8 lag distribution -> OPERATIONAL HYPOTHESIS SUPPORTED
- If high-K distribution matches random -> H_NULL (no operational signal)
- If high-K distribution matches K=8 (peak at 0-1) -> just stronger natural
  signal, not operational

Tests:
- Kolmogorov-Smirnov: K=13 lag distribution vs K=8 lag distribution
- KS: K=13 vs random-day baseline (climatology)
- Visual: lag histograms for K=1, K=8, K=12, K=13, random
- Median lag at each K
- Fraction of events at lag 2-4 days

Uses cached probe8 DKA per-system recovery dates.
"""
import os, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
DKA = ROOT / "data/raw/dka"
WEATHER = DKA / "101-Site_DKA-WeatherStation.csv"
CACHE = ROOT / "data/processed/probe8_dka_recovery_dates_cache.csv"
OUT_LAGS = ROOT / "data/processed/probe9_lag_table.csv"
OUT_SUM  = ROOT / "data/processed/probe9_lag_summary.csv"

RAIN_THR = 1.0
FUZZ = 1   # for K-consensus aggregation only; lag computation is exact-date


def load_rain():
    df = pd.read_csv(WEATHER, usecols=["timestamp", "Weather_Daily_Rainfall"],
                     engine="python", on_bad_lines="skip")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["Weather_Daily_Rainfall"] = pd.to_numeric(df["Weather_Daily_Rainfall"], errors="coerce")
    df = df.dropna().set_index("timestamp").sort_index()
    return df["Weather_Daily_Rainfall"].resample("D").max().fillna(0)


def days_since_last_rain(target_dates, rain_days_sorted):
    """For each target date, return days since the most recent rain day <= target.
    Returns +inf if no rain has occurred before target.
    rain_days_sorted must be a numpy array of pd.Timestamp sorted ascending."""
    out = []
    for d in target_dates:
        # Find latest rain_day <= d
        idx = np.searchsorted(rain_days_sorted, d, side="right") - 1
        if idx < 0:
            out.append(np.nan)
        else:
            lag = (d - rain_days_sorted[idx]).days
            out.append(lag)
    return np.array(out)


def main():
    print("Loading on-site rain...")
    rain = load_rain()
    rain_days = sorted(set(d.normalize() for d in rain.index[rain >= RAIN_THR]))
    rain_days_arr = np.array(rain_days)
    print(f"Rain days >= {RAIN_THR}mm: {len(rain_days)}")
    span_start = rain.index.min().normalize()
    span_end = rain.index.max().normalize()
    print(f"Span: {span_start.date()} - {span_end.date()}")

    print("\nLoading cached recovery dates...")
    df = pd.read_csv(CACHE)
    df["recovery_date"] = pd.to_datetime(df["recovery_date"])
    sys_recs = {k: set(g["recovery_date"]) for k, g in df.groupby("system")}
    n_sys = len(sys_recs)
    print(f"Systems: {n_sys}")

    # Build K-consensus day mapping (using FUZZ=1 like Probes 5d/6/6b)
    day_count = {}
    for key, dates in sys_recs.items():
        for d in dates:
            for k in range(-FUZZ, FUZZ + 1):
                day_count.setdefault(d + pd.Timedelta(days=k), set()).add(key)

    # Random-null lag distribution: pick equal-N random days within span
    span_days = pd.date_range(span_start, span_end, freq="D")
    rng = np.random.default_rng(seed=20260530)

    # ===================================================================
    # Per-K lag distributions
    # ===================================================================
    ks = [1, 4, 8, 11, 12, 13]
    lag_table_rows = []
    summary_rows = []

    print(f"\n{'K':>3s} {'n_days':>7s} {'med_lag':>8s} {'mean_lag':>9s} {'frac_lag_0-1':>13s} {'frac_lag_2-4':>13s} {'KS_vs_random_p':>15s}")

    # Pre-compute random-null lag distribution (one large sample)
    random_dates = pd.to_datetime(rng.choice(span_days.normalize(), size=2000, replace=False))
    random_lags = days_since_last_rain(sorted(random_dates), rain_days_arr)
    random_lags = random_lags[~np.isnan(random_lags)]

    summary_rows.append({
        "label": "random_climatology", "n": int(len(random_lags)),
        "median_lag": float(np.median(random_lags)),
        "mean_lag": float(np.mean(random_lags)),
        "frac_lag_0_1": float(np.mean((random_lags >= 0) & (random_lags <= 1))),
        "frac_lag_2_4": float(np.mean((random_lags >= 2) & (random_lags <= 4))),
        "ks_vs_random_p": np.nan,
    })

    for K in ks:
        days_at_k = sorted(set(d for d, syss in day_count.items() if len(syss) >= K))
        if not days_at_k: continue
        lags = days_since_last_rain(days_at_k, rain_days_arr)
        lags = lags[~np.isnan(lags)]
        if len(lags) < 5: continue
        med = float(np.median(lags))
        mean = float(np.mean(lags))
        frac_01 = float(np.mean((lags >= 0) & (lags <= 1)))
        frac_24 = float(np.mean((lags >= 2) & (lags <= 4)))
        ks_stat, ks_p = stats.ks_2samp(lags, random_lags)
        summary_rows.append({
            "label": f"K={K}", "n": int(len(lags)),
            "median_lag": med, "mean_lag": mean,
            "frac_lag_0_1": frac_01, "frac_lag_2_4": frac_24,
            "ks_vs_random_p": float(ks_p),
        })
        print(f"{K:>3d} {len(lags):>7d} {med:>8.1f} {mean:>9.2f} {frac_01*100:>11.1f}% {frac_24*100:>11.1f}% {ks_p:>14.4f}")
        # Save lag tables
        for lag in lags:
            lag_table_rows.append({"K": K, "lag_days_since_rain": int(lag)})

    print(f"\nrandom_climatology: n={len(random_lags)}, "
          f"median={np.median(random_lags):.1f}, mean={np.mean(random_lags):.2f}, "
          f"frac_lag_0-1={np.mean((random_lags>=0)&(random_lags<=1))*100:.1f}%, "
          f"frac_lag_2-4={np.mean((random_lags>=2)&(random_lags<=4))*100:.1f}%")

    pd.DataFrame(lag_table_rows).to_csv(OUT_LAGS, index=False)
    pd.DataFrame(summary_rows).to_csv(OUT_SUM, index=False)
    print(f"\nWrote {OUT_LAGS.name}, {OUT_SUM.name}")

    # ===================================================================
    # Hypothesis verdicts
    # ===================================================================
    print("\n=== HYPOTHESIS TESTS ===")
    sdf = pd.DataFrame(summary_rows)

    # Test 1: K=13 lag distribution vs random
    k13 = sdf[sdf["label"] == "K=13"].iloc[0] if len(sdf[sdf["label"] == "K=13"]) else None
    k8  = sdf[sdf["label"] == "K=8"].iloc[0]  if len(sdf[sdf["label"] == "K=8"])  else None
    rnd = sdf[sdf["label"] == "random_climatology"].iloc[0]

    if k13 is not None:
        print(f"K=13 vs random: KS p = {k13['ks_vs_random_p']:.4f}")
        print(f"  K=13 fraction at lag 0-1 days: {k13['frac_lag_0_1']*100:.1f}%  (random {rnd['frac_lag_0_1']*100:.1f}%)")
        print(f"  K=13 fraction at lag 2-4 days: {k13['frac_lag_2_4']*100:.1f}%  (random {rnd['frac_lag_2_4']*100:.1f}%)")
        print(f"  K=13 median lag: {k13['median_lag']:.1f} days  (random {rnd['median_lag']:.1f})")
    if k8 is not None and k13 is not None:
        # KS test K=13 vs K=8
        k13_lags = [r["lag_days_since_rain"] for r in lag_table_rows if r["K"] == 13]
        k8_lags  = [r["lag_days_since_rain"] for r in lag_table_rows if r["K"] == 8]
        ks_138 = stats.ks_2samp(k13_lags, k8_lags)
        print(f"\nK=13 vs K=8 lag distributions: KS p = {ks_138.pvalue:.4f}")
        print(f"  K=8 fraction at lag 0-1: {k8['frac_lag_0_1']*100:.1f}%")
        print(f"  K=13 fraction at lag 0-1: {k13['frac_lag_0_1']*100:.1f}%")

    print("\n=== INTERPRETATION SCAFFOLD ===")
    if k13 is not None:
        if k13['ks_vs_random_p'] < 0.05 and k13['frac_lag_2_4'] > rnd['frac_lag_2_4'] * 1.3:
            print("OPERATIONAL HYPOTHESIS SUPPORTED: K=13 lag distribution differs significantly from random AND")
            print("  fraction at lag 2-4 days is materially elevated -> consistent with post-rain operational visits")
        elif k13['ks_vs_random_p'] < 0.05 and k13['frac_lag_0_1'] > rnd['frac_lag_0_1'] * 1.3:
            print("STRONGER NATURAL signal: K=13 differs from random but peak is at lag 0-1 (natural cleaning, not operational lag)")
        elif k13['ks_vs_random_p'] >= 0.05:
            print("H_NULL: K=13 lag distribution is statistically indistinguishable from random climatology -> no operational signature")
        else:
            print("Mixed / unclear pattern - inspect lag histogram for K=13 manually")

    # Print compact lag histogram for K=13
    print("\n=== K=13 LAG HISTOGRAM (days since last rain >= 1mm) ===")
    if k13 is not None:
        k13_lags = [r["lag_days_since_rain"] for r in lag_table_rows if r["K"] == 13]
        bins = list(range(0, 15)) + [999]
        labels = [f"{i}" for i in range(15)] + ["15+"]
        counts = pd.cut(k13_lags, bins=bins + [10**9], labels=labels + [None])  # ignore overflow
        for i in range(15):
            c = sum(1 for L in k13_lags if L == i)
            pct = c / len(k13_lags) * 100
            bar = "#" * int(pct / 2)
            print(f"  lag={i:>2d}d: {c:>3d} ({pct:>5.1f}%)  {bar}")
        c_overflow = sum(1 for L in k13_lags if L >= 15)
        if c_overflow:
            pct = c_overflow / len(k13_lags) * 100
            print(f"  lag>=15d: {c_overflow:>3d} ({pct:>5.1f}%)")


if __name__ == "__main__":
    main()
