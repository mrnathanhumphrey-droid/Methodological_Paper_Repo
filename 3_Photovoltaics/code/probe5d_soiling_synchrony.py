"""Probe 5d — Inter-system soiling-recovery synchrony at DKA Alice Springs.

All 13 systems share one site. If rain/scheduled cleaning is the dominant
cleaner, recovery events should be SYNCHRONIZED across systems. Test:
1. Pairwise Jaccard similarity of recovery dates (with +/-1 day fuzz)
2. Find 'consensus days' where >=K systems have a recovery (within +/-1 day)
3. Check what % of consensus days have rain (vs per-system 28% from Probe 5b)
   -> if consensus days are FAR more rain-aligned, common-cause mechanism confirmed."""
import os, glob, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from itertools import combinations
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))
from probe4_dka_run import parse_file, m_number, phase_label, CATALOG
from probe5_dka_soiling import daily_pr_and_insol
import rdtools.soiling as rsoil

DKA = ROOT / "data/raw/dka"
WEATHER = DKA / "101-Site_DKA-WeatherStation.csv"
OUT_CONS = ROOT / "data/processed/probe5d_consensus_days.csv"
OUT_JACC = ROOT / "data/processed/probe5d_pairwise_jaccard.csv"

FUZZ = 1     # +/-1 day for matching recovery dates across systems
RAIN_THR = 1.0


def load_rain():
    df = pd.read_csv(WEATHER, usecols=["timestamp", "Weather_Daily_Rainfall"],
                     engine="python", on_bad_lines="skip")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["Weather_Daily_Rainfall"] = pd.to_numeric(df["Weather_Daily_Rainfall"], errors="coerce")
    df = df.dropna().set_index("timestamp").sort_index()
    return df["Weather_Daily_Rainfall"].resample("D").max().fillna(0)


def get_recoveries(p):
    pr, ins, st = daily_pr_and_insol(p)
    if st != "ok": return None
    sr, sr_ci, info = rsoil.soiling_srr(pr, ins, reps=100)
    summary = info.get("soiling_interval_summary") if isinstance(info, dict) else None
    if summary is None and isinstance(info, (list, tuple)):
        for it in info:
            if isinstance(it, pd.DataFrame) and "end" in it.columns:
                summary = it; break
    if summary is None: return None
    ends = pd.to_datetime(summary["end"]).dropna().dt.normalize().unique()
    return set(ends)


def fuzzy_intersection(a, b, fuzz):
    """Count of dates in a that have any date in b within +/-fuzz days."""
    b_expanded = set()
    for d in b:
        for k in range(-fuzz, fuzz + 1):
            b_expanded.add(d + pd.Timedelta(days=k))
    return sum(1 for d in a if d in b_expanded)


def jaccard_fuzzy(a, b, fuzz):
    inter = fuzzy_intersection(a, b, fuzz)
    inter_sym = max(inter, fuzzy_intersection(b, a, fuzz))
    union = len(a) + len(b) - inter_sym  # approximate
    return inter_sym / union if union > 0 else 0.0


def main():
    rain = load_rain()
    rain_days = set(d.normalize() for d in rain.index[rain >= RAIN_THR])
    span_days = pd.date_range(rain.index.min(), rain.index.max(), freq="D")
    base_rain_aligned_set = set()
    for d in rain_days:
        for k in range(-FUZZ, FUZZ + 1):
            base_rain_aligned_set.add(d + pd.Timedelta(days=k))
    baseline_rain = len(base_rain_aligned_set & set(span_days.normalize())) / len(span_days)

    print(f"Span {rain.index.min().date()} - {rain.index.max().date()} ({len(span_days)} days)")
    print(f"Rain days >= {RAIN_THR} mm: {len(rain_days)}; baseline rain-alignment +/-{FUZZ}d = {baseline_rain*100:.1f}%\n")

    # ---- recoveries per system ----
    sys_recs = {}
    for p in sorted(glob.glob(str(DKA / "*Site_DKA-M*.csv"))):
        fname = os.path.basename(p); mnum = m_number(fname)
        if mnum is None: continue
        phase = phase_label(fname)
        key = f"M{mnum}_{phase}"
        recs = get_recoveries(p)
        if recs is None or len(recs) < 5: continue
        sys_recs[key] = recs
        print(f"  {key:>10s}: {len(recs)} recovery dates")
    print(f"Systems: {len(sys_recs)}\n")
    if len(sys_recs) < 2:
        print("not enough systems"); return

    # ---- pairwise Jaccard ----
    print("=== Pairwise Jaccard similarity of recovery dates (+/-1 day fuzz) ===")
    jrows = []
    for a, b in combinations(sys_recs.keys(), 2):
        j = jaccard_fuzzy(sys_recs[a], sys_recs[b], FUZZ)
        jrows.append({"a": a, "b": b, "jaccard": j,
                      "n_a": len(sys_recs[a]), "n_b": len(sys_recs[b])})
    jdf = pd.DataFrame(jrows)
    jdf.to_csv(OUT_JACC, index=False)
    print(f"  n_pairs = {len(jdf)}")
    print(f"  Jaccard median = {jdf['jaccard'].median():.3f}, mean = {jdf['jaccard'].mean():.3f}")
    print(f"  Jaccard range = [{jdf['jaccard'].min():.3f}, {jdf['jaccard'].max():.3f}]")
    # baseline: if recoveries were uniformly random, expected jaccard ~ (3*median_n/span)
    med_n = np.median([len(s) for s in sys_recs.values()])
    p_recov_day = (med_n * (2*FUZZ + 1)) / len(span_days)
    j_random = p_recov_day**2 / (2*p_recov_day - p_recov_day**2)
    print(f"  baseline (random) Jaccard ~ {j_random:.3f} (p_recovery_day = {p_recov_day:.3f})")
    print(f"  -> observed/random ratio: {jdf['jaccard'].median()/j_random:.2f}x")

    # ---- consensus days ----
    print("\n=== Consensus-day analysis (>=K systems recover on same +/-1d window) ===")
    # collect all (sys, date) and bin by day
    day_count = {}
    for key, dates in sys_recs.items():
        for d in dates:
            for k in range(-FUZZ, FUZZ + 1):
                day_count[d + pd.Timedelta(days=k)] = day_count.get(d + pd.Timedelta(days=k), set())
                day_count[d + pd.Timedelta(days=k)].add(key)
    consensus_rows = []
    for K in range(1, len(sys_recs) + 1):
        days_at_k = [d for d, syss in day_count.items() if len(syss) >= K]
        n_days = len(set(days_at_k))
        rain_hits = sum(1 for d in set(days_at_k) if d in base_rain_aligned_set)
        rate = rain_hits / n_days if n_days else 0
        consensus_rows.append({"K_min_systems": K, "n_consensus_days": n_days,
                               "rain_aligned_pct": rate * 100, "lift_vs_baseline": rate / baseline_rain if baseline_rain else None})
    cdf = pd.DataFrame(consensus_rows)
    cdf.to_csv(OUT_CONS, index=False)
    print(f"{'K':>3s} {'n_days':>7s} {'rain%':>6s} {'lift':>5s}")
    for _, r in cdf.iterrows():
        K = int(r["K_min_systems"]); n = int(r["n_consensus_days"])
        rp = r["rain_aligned_pct"]; lf = r["lift_vs_baseline"]
        print(f"{K:>3d} {n:>7d} {rp:>5.1f}% {lf:>4.2f}x")
    print(f"\n=> per-system rain-alignment (Probe 5b): 28%, baseline {baseline_rain*100:.1f}%")
    print(f"=> consensus-day rain alignment for K={len(sys_recs)//2}+ systems: see above")

if __name__ == "__main__":
    main()
