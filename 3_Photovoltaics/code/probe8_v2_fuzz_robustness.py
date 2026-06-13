"""Probe 8 — V2 fuzz-robustness sweep on DKA.

Skeptic-pass concern (CLM-103 + memo 31 §8.3): the ±1 day fuzz used in Probe 5d
+ Probe 6 was copied from Probe 5b convention (which actually used ±2 days) but
was not formally pre-registered. If the K=12-13 crash at DKA depends on the
specific fuzz choice, the methodology is p-hacked.

This probe re-runs the K-consensus + rain-alignment analysis at DKA across
fuzz values {0, 1, 2, 3} days. Reports K=12, K=13 alignment % + binomial
p-values vs the corresponding baseline for each fuzz.

Robustness criterion:
- If the K=13 crash (alignment < baseline) appears across multiple fuzz values
  with consistent p<0.05, the result is robust to the fuzz choice
- If the crash only appears at fuzz=1 (the chosen value), it's a tuning
  artifact

Notes:
- SRR is stochastic (reps=100); for fair comparison we cache the recovery
  dates and reuse them across fuzz values
- The Jaccard random null also depends on fuzz; recomputed per fuzz
"""
import os, glob, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))
from probe4_dka_run import parse_file, m_number, phase_label
from probe5_dka_soiling import daily_pr_and_insol
import rdtools.soiling as rsoil

DKA = ROOT / "data/raw/dka"
WEATHER = DKA / "101-Site_DKA-WeatherStation.csv"
CACHE_RECS = ROOT / "data/processed/probe8_dka_recovery_dates_cache.csv"
OUT = ROOT / "data/processed/probe8_fuzz_robustness.csv"

RAIN_THR = 1.0
FUZZ_VALUES = [0, 1, 2, 3]


def load_rain():
    df = pd.read_csv(WEATHER, usecols=["timestamp", "Weather_Daily_Rainfall"],
                     engine="python", on_bad_lines="skip")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["Weather_Daily_Rainfall"] = pd.to_numeric(df["Weather_Daily_Rainfall"], errors="coerce")
    df = df.dropna().set_index("timestamp").sort_index()
    return df["Weather_Daily_Rainfall"].resample("D").max().fillna(0)


def get_recoveries_for_file(p):
    pr, ins, st = daily_pr_and_insol(p)
    if st != "ok": return None
    try:
        sr, sr_ci, info = rsoil.soiling_srr(pr, ins, reps=100)
    except Exception:
        return None
    summary = info.get("soiling_interval_summary") if isinstance(info, dict) else None
    if summary is None and isinstance(info, (list, tuple)):
        for it in info:
            if isinstance(it, pd.DataFrame) and "end" in it.columns:
                summary = it; break
    if summary is None: return None
    ends = pd.to_datetime(summary["end"]).dropna().dt.normalize().unique()
    return set(ends)


def load_or_compute_recs():
    if CACHE_RECS.exists():
        df = pd.read_csv(CACHE_RECS)
        df["recovery_date"] = pd.to_datetime(df["recovery_date"])
        sys_recs = {k: set(g["recovery_date"]) for k, g in df.groupby("system")}
        return sys_recs
    sys_recs = {}
    for p in sorted(glob.glob(str(DKA / "*Site_DKA-M*.csv"))):
        fname = os.path.basename(p); mnum = m_number(fname)
        if mnum is None: continue
        phase = phase_label(fname)
        key = f"M{mnum}_{phase}"
        recs = get_recoveries_for_file(p)
        if recs is None or len(recs) < 5: continue
        sys_recs[key] = recs
        print(f"  {key}: {len(recs)} recoveries")
    rows = []
    for k, dates in sys_recs.items():
        for d in dates:
            rows.append({"system": k, "recovery_date": d.strftime("%Y-%m-%d")})
    pd.DataFrame(rows).to_csv(CACHE_RECS, index=False)
    return sys_recs


def compute_fuzz_K(sys_recs, rain, fuzz, ks_of_interest):
    """Return: baseline_rain, list of (K, n_days, n_rainy, pct, lift, p_value)."""
    rain_days = set(d.normalize() for d in rain.index[rain >= RAIN_THR])
    span_days = pd.date_range(rain.index.min(), rain.index.max(), freq="D")
    # Baseline: fraction of span days within +/-fuzz of any rainy day
    base_rain_aligned_set = set()
    for d in rain_days:
        for k in range(-fuzz, fuzz + 1):
            base_rain_aligned_set.add(d + pd.Timedelta(days=k))
    baseline_rain = len(base_rain_aligned_set & set(span_days.normalize())) / len(span_days)

    # Day-count by K with this fuzz
    day_count = {}
    for key, dates in sys_recs.items():
        for d in dates:
            for k in range(-fuzz, fuzz + 1):
                day_count.setdefault(d + pd.Timedelta(days=k), set()).add(key)
    out = []
    for K in ks_of_interest:
        days_at_k = set(d for d, syss in day_count.items() if len(syss) >= K)
        n_days = len(days_at_k)
        n_rainy = sum(1 for d in days_at_k if d in base_rain_aligned_set)
        pct = n_rainy / n_days * 100 if n_days else 0
        lift = (n_rainy / n_days) / baseline_rain if (n_days and baseline_rain) else None
        # Two-sided binomial test vs baseline_rain
        if n_days > 0:
            # one-sided LOW (testing for crash)
            p_low = stats.binom.cdf(n_rainy, n_days, baseline_rain)
            p_high = 1 - stats.binom.cdf(n_rainy - 1, n_days, baseline_rain)
            p_two = 2 * min(p_low, p_high)
        else:
            p_low = p_high = p_two = np.nan
        out.append({"K": K, "n_days": n_days, "n_rainy": n_rainy, "pct": pct,
                    "lift": lift, "baseline_pct": baseline_rain * 100,
                    "p_one_sided_low": p_low, "p_one_sided_high": p_high,
                    "p_two_sided": p_two})
    return baseline_rain, out


def main():
    print("Loading DKA on-site rain...")
    rain = load_rain()
    print(f"Rain span: {rain.index.min().date()} - {rain.index.max().date()}")

    print("\nLoading / computing per-system recovery dates (cached after first run)...")
    sys_recs = load_or_compute_recs()
    n_sys = len(sys_recs)
    print(f"Usable systems: {n_sys}")

    ks_of_interest = [1, 8, 11, 12, 13]
    print(f"\n=== Fuzz robustness sweep at DKA ===")
    print(f"Fuzz | K | n_days | n_rainy |  pct%  | baseline% | lift  | p_one_low | p_two_sided")
    rows_out = []
    for fuzz in FUZZ_VALUES:
        baseline_rain, results = compute_fuzz_K(sys_recs, rain, fuzz, ks_of_interest)
        for r in results:
            r["fuzz"] = fuzz
            rows_out.append(r)
            print(f"  {fuzz:>2d}  | {r['K']:>2d} | {r['n_days']:>6d} | {r['n_rainy']:>7d} | {r['pct']:>5.1f}% |  {r['baseline_pct']:>5.1f}%   | {r['lift']:>4.2f}x | {r['p_one_sided_low']:>7.4f}   | {r['p_two_sided']:>7.4f}")
        print()
    df = pd.DataFrame(rows_out)
    df.to_csv(OUT, index=False)
    print(f"Wrote {OUT}")

    print("\n=== ROBUSTNESS VERDICT on K=13 crash ===")
    k13 = df[df["K"] == 13].sort_values("fuzz")
    print(f"{'Fuzz':>5} {'pct':>7} {'baseline':>10} {'p_low':>8} {'verdict':<20}")
    for _, r in k13.iterrows():
        below = r["pct"] < r["baseline_pct"]
        sig = r["p_one_sided_low"] < 0.05
        verdict = "BELOW + sig" if (below and sig) else ("below not sig" if below else ("above baseline" if not below else "?"))
        print(f"{int(r['fuzz']):>5d} {r['pct']:>6.1f}% {r['baseline_pct']:>9.1f}% {r['p_one_sided_low']:>7.4f}  {verdict}")

    print("\n=== K=12 ===")
    k12 = df[df["K"] == 12].sort_values("fuzz")
    for _, r in k12.iterrows():
        below = r["pct"] < r["baseline_pct"]
        sig = r["p_one_sided_low"] < 0.05
        verdict = "BELOW + sig" if (below and sig) else ("below not sig" if below else "above baseline")
        print(f"  fuzz={int(r['fuzz']):>1d}: {r['pct']:>5.1f}% vs baseline {r['baseline_pct']:>5.1f}%, p_low={r['p_one_sided_low']:.4f}  {verdict}")


if __name__ == "__main__":
    main()
