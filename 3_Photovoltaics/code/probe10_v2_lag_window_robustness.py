"""Probe 10 — V2 lag-window robustness sweep.

Probe 9 reported the operational signal at lag 2-4 days post-rain. That window
was specified before running the binomial test BUT after observing Probe 8's
fuzz-2/3 hints that operational events tail rain by a few days. So the
window choice is partially data-influenced.

This probe tests whether the lag-shift signal is robust to alternative window
choices, or whether it's window-tuned.

Test windows:
- {1-3}: narrower, earlier  - tests if signal is mostly at lag 1-3
- {2-3}: very narrow, original "site-visit core"
- {2-4}: as in Probe 9 (memo 36 baseline)
- {3-5}: shifted later - tests if peak is actually at 3-5
- {1-5}: wider symmetric
- {0-7}: very wide (includes natural-cleaning lag 0-1 mixed with operational)
- {5-7}: late-lag control - shouldn't show operational signal if mechanism is correct
- {8-14}: far-late control - definitely shouldn't show operational signal

For each window, compute:
- Fraction of events in window at each K (1, 8, 11, 12, 13)
- Random climatology baseline fraction in same window
- Binomial p-value for high-K (combined K>=11) vs baseline

Decision criteria (pre-specified):
- ROBUST: combined K>=11 enrichment p<0.01 across all of {1-3, 2-3, 2-4, 3-5, 1-5}
- WINDOW-TUNED: signal fires only at {2-4} (Probe 9 choice)
- LATE-CONTROL must show NS at {5-7} and {8-14} for mechanism to be plausible
"""
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
LAG_TABLE = ROOT / "data/processed/probe9_lag_table.csv"
WEATHER = ROOT / "data/raw/dka/101-Site_DKA-WeatherStation.csv"
OUT = ROOT / "data/processed/probe10_lag_window_robustness.csv"

RAIN_THR = 1.0


def load_rain():
    df = pd.read_csv(WEATHER, usecols=["timestamp", "Weather_Daily_Rainfall"],
                     engine="python", on_bad_lines="skip")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["Weather_Daily_Rainfall"] = pd.to_numeric(df["Weather_Daily_Rainfall"], errors="coerce")
    df = df.dropna().set_index("timestamp").sort_index()
    return df["Weather_Daily_Rainfall"].resample("D").max().fillna(0)


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
    print("Loading on-site rain (for baseline computation)...")
    rain = load_rain()
    rain_days = sorted(set(d.normalize() for d in rain.index[rain >= RAIN_THR]))
    rain_days_arr = np.array(rain_days)
    span_start = rain.index.min().normalize()
    span_end = rain.index.max().normalize()
    span_days = pd.date_range(span_start, span_end, freq="D")

    # Recompute random-null lag distribution
    rng = np.random.default_rng(seed=20260530)  # same seed as Probe 9
    random_dates = pd.to_datetime(rng.choice(span_days.normalize(), size=2000, replace=False))
    random_lags = days_since_last_rain(sorted(random_dates), rain_days_arr)
    random_lags = random_lags[~np.isnan(random_lags)]
    print(f"random-null sample: n={len(random_lags)}")

    print("\nLoading Probe 9 lag table...")
    lt = pd.read_csv(LAG_TABLE)
    print(f"  rows={len(lt)}, K values: {sorted(lt['K'].unique())}")
    lags_by_k = {K: lt[lt["K"] == K]["lag_days_since_rain"].values for K in lt["K"].unique()}

    # Define test windows
    windows = [
        ("lag 1-3", 1, 3),
        ("lag 2-3", 2, 3),
        ("lag 2-4", 2, 4),   # Probe 9 baseline
        ("lag 3-5", 3, 5),
        ("lag 1-5", 1, 5),
        ("lag 0-7", 0, 7),
        ("lag 5-7", 5, 7),   # late-lag control
        ("lag 8-14", 8, 14), # far-late control
    ]

    ks = [1, 8, 11, 12, 13]
    rows = []

    print(f"\n=== LAG-WINDOW ROBUSTNESS SWEEP ===")
    print(f"{'window':<10} {'K':>3} {'n':>4} {'obs':>3} {'obs_pct':>8} {'base_pct':>9} {'lift':>5} {'p_one_high':>11}")

    for label, lo, hi in windows:
        # Baseline fraction in this window
        base_in = np.mean((random_lags >= lo) & (random_lags <= hi))
        for K in ks:
            lags = lags_by_k.get(K, np.array([]))
            if len(lags) == 0: continue
            n = int(len(lags))
            obs = int(np.sum((lags >= lo) & (lags <= hi)))
            obs_pct = obs / n if n > 0 else 0
            lift = obs_pct / base_in if base_in > 0 else float("nan")
            # One-sided binomial test for enrichment
            p_high = 1 - stats.binom.cdf(obs - 1, n, base_in) if n > 0 else np.nan
            rows.append({"window": label, "lo": lo, "hi": hi, "K": K, "n": n,
                         "obs": obs, "obs_pct": obs_pct, "base_pct": base_in,
                         "lift": lift, "p_one_sided_high": p_high})
            print(f"  {label:<10} {K:>3d} {n:>4d} {obs:>3d} {obs_pct*100:>6.1f}% {base_in*100:>7.1f}% {lift:>4.2f}x {p_high:>10.5f}")

        # Combined K>=11
        kcomb_lags = np.concatenate([lags_by_k.get(K, np.array([])) for K in [11, 12, 13]])
        n = int(len(kcomb_lags))
        obs = int(np.sum((kcomb_lags >= lo) & (kcomb_lags <= hi)))
        obs_pct = obs / n if n > 0 else 0
        lift = obs_pct / base_in if base_in > 0 else float("nan")
        p_high = 1 - stats.binom.cdf(obs - 1, n, base_in) if n > 0 else np.nan
        rows.append({"window": label, "lo": lo, "hi": hi, "K": "K>=11", "n": n,
                     "obs": obs, "obs_pct": obs_pct, "base_pct": base_in,
                     "lift": lift, "p_one_sided_high": p_high})
        print(f"  {label:<10} {'K>=11':>5} {n:>4d} {obs:>3d} {obs_pct*100:>6.1f}% {base_in*100:>7.1f}% {lift:>4.2f}x {p_high:>10.5f}")
        print()

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nWrote {OUT.name}")

    # ===================================================================
    # Verdict summary
    # ===================================================================
    df = pd.DataFrame(rows)
    print("\n=== VERDICT: combined K>=11 enrichment p-values ===")
    print(f"{'window':<10} {'obs_pct':>9} {'base_pct':>10} {'lift':>5} {'p':>11} {'verdict':>10}")
    for label, lo, hi in windows:
        r = df[(df["window"] == label) & (df["K"] == "K>=11")].iloc[0]
        verdict = "SIG" if r["p_one_sided_high"] < 0.01 else ("marginal" if r["p_one_sided_high"] < 0.05 else "NS")
        print(f"  {label:<10} {r['obs_pct']*100:>7.1f}% {r['base_pct']*100:>8.1f}% {r['lift']:>4.2f}x {r['p_one_sided_high']:>10.5f}  {verdict}")

    # Cross-check: control windows (5-7, 8-14) should be NS
    print("\n=== Late-lag controls (should be NS if mechanism is real 2-4d lag) ===")
    for label, lo, hi in [("lag 5-7", 5, 7), ("lag 8-14", 8, 14)]:
        r = df[(df["window"] == label) & (df["K"] == "K>=11")].iloc[0]
        passes = "PASS (NS)" if r["p_one_sided_high"] >= 0.05 else "FAIL (SIG)"
        print(f"  {label}: K>=11 obs {r['obs_pct']*100:.1f}% vs baseline {r['base_pct']*100:.1f}%, p={r['p_one_sided_high']:.4f}  {passes}")

    # Robustness of operational window choice
    print("\n=== Robustness of 2-4 vs alternatives ===")
    operational_windows = ["lag 1-3", "lag 2-3", "lag 2-4", "lag 3-5", "lag 1-5"]
    sig_count = 0
    for label in operational_windows:
        r = df[(df["window"] == label) & (df["K"] == "K>=11")].iloc[0]
        if r["p_one_sided_high"] < 0.01: sig_count += 1
    print(f"  Significant (p<0.01) at K>=11 in {sig_count}/{len(operational_windows)} operational-candidate windows")
    if sig_count >= 4:
        print("  ROBUST: signal holds across multiple reasonable window choices")
    elif sig_count >= 2:
        print("  PARTIALLY ROBUST: signal holds across some windows; choice of 2-4 was reasonable but not unique")
    else:
        print("  WINDOW-TUNED: signal only fires at specific window — claim is fragile")


if __name__ == "__main__":
    main()
