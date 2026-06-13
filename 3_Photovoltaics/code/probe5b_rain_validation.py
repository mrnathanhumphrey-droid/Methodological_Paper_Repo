"""Probe 5b — Rain-event validation of SRR soiling recoveries.

For each DKA system, extract SRR's detected soiling-interval boundaries (= recovery
events) and check what fraction coincide with on-site rain (>= 1 mm) within +/-N
days. Compare to the baseline rain-day rate. If recovery alignment >> baseline →
the SRR sawtooth is mechanistically real, not noise."""
import os, glob, warnings, sys
from pathlib import Path
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))
from probe4_dka_run import parse_file, m_number, phase_label, CATALOG, POA_COL, PWR_COL
from probe5_dka_soiling import daily_pr_and_insol
import rdtools.soiling as rsoil

DKA = ROOT / "data/raw/dka"
WEATHER = DKA / "101-Site_DKA-WeatherStation.csv"
OUT = ROOT / "data/processed/probe5b_rain_validation.csv"

WINDOW_DAYS = 2   # +/- days to count a recovery as rain-aligned
RAIN_THR_MM = 1.0  # rain >= 1mm/day counts as a real rain day


def load_rainfall():
    """Daily rainfall (mm) from on-site weather station."""
    df = pd.read_csv(WEATHER, usecols=["timestamp", "Weather_Daily_Rainfall"],
                     engine="python", on_bad_lines="skip")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["Weather_Daily_Rainfall"] = pd.to_numeric(df["Weather_Daily_Rainfall"], errors="coerce")
    df = df.dropna(subset=["timestamp", "Weather_Daily_Rainfall"]).set_index("timestamp").sort_index()
    # the station reports daily-accumulation that resets; take max-per-day as the day's rainfall
    daily_rain = df["Weather_Daily_Rainfall"].resample("D").max().fillna(0)
    return daily_rain


def srr_recovery_dates(pr, ins):
    """Run SRR and extract interval-boundary dates (= recovery events)."""
    sr, sr_ci, info = rsoil.soiling_srr(pr, ins, reps=200)
    summary = info.get("soiling_interval_summary") if isinstance(info, dict) else None
    if summary is None and isinstance(info, (list, tuple)):
        for item in info:
            if isinstance(item, pd.DataFrame) and "end" in item.columns:
                summary = item
                break
    if summary is None:
        return None, sr
    # interval END = recovery boundary (cleaning event candidate)
    ends = pd.to_datetime(summary["end"]).dropna().unique()
    return pd.Series(ends), sr


def coincidence(recovery_dates, rain_days_set, window):
    """Fraction of recovery events with a rain-day within +/-window."""
    if len(recovery_dates) == 0:
        return None, 0
    hits = 0
    for d in recovery_dates:
        d = pd.Timestamp(d).normalize()
        for k in range(-window, window + 1):
            if (d + pd.Timedelta(days=k)).normalize() in rain_days_set:
                hits += 1
                break
    return hits / len(recovery_dates), len(recovery_dates)


def main():
    rain = load_rainfall()
    rain_days = rain.index[rain >= RAIN_THR_MM]
    rain_days_set = set(pd.Timestamp(d).normalize() for d in rain_days)
    # baseline = fraction of days in span that are within +/-window of a rain day
    all_days = pd.date_range(rain.index.min(), rain.index.max(), freq="D")
    baseline_set = set()
    for d in rain_days_set:
        for k in range(-WINDOW_DAYS, WINDOW_DAYS + 1):
            baseline_set.add((d + pd.Timedelta(days=k)).normalize())
    baseline_rate = len(baseline_set.intersection(set(all_days.normalize()))) / len(all_days)
    print(f"Weather span: {rain.index.min().date()} to {rain.index.max().date()} ({len(all_days)} days)")
    print(f"Rain-days (>= {RAIN_THR_MM} mm): {len(rain_days_set)} ({len(rain_days_set)/len(all_days)*100:.1f}% of days)")
    print(f"Baseline coincidence rate (random recovery would hit within +/-{WINDOW_DAYS}d of rain): {baseline_rate*100:.1f}%")
    print()
    print(f"{'M':>3s} {'phase':>5s} {'tech':>9s} {'mount':>11s} | "
          f"{'n_rec':>5s} {'rain-align%':>11s} {'baseline%':>9s} {'lift':>5s}")
    print("-" * 80)
    rows = []
    for p in sorted(glob.glob(str(DKA / "*Site_DKA-M*.csv"))):
        fname = os.path.basename(p)
        mnum = m_number(fname)
        if mnum is None:
            continue
        phase = phase_label(fname)
        cat = CATALOG.get(mnum, ("?", "?", "?", None))
        brand, tech, mount, vint = cat
        pr, ins, st = daily_pr_and_insol(p)
        if st != "ok":
            continue
        try:
            recs, sr = srr_recovery_dates(pr, ins)
            if recs is None or len(recs) == 0:
                print(f"M{mnum:<2d} {phase:>5s} {tech:>9s} {mount:>11s} | no recovery events")
                continue
            rate, n = coincidence(recs, rain_days_set, WINDOW_DAYS)
            lift = rate / baseline_rate if baseline_rate > 0 else float("nan")
            row = {"file": fname, "M_num": mnum, "phase": phase, "technology": tech,
                   "mount": mount, "n_recoveries": int(n),
                   "rain_alignment_pct": rate * 100,
                   "baseline_pct": baseline_rate * 100, "lift": lift}
            rows.append(row)
            print(f"M{mnum:<2d} {phase:>5s} {tech:>9s} {mount:>11s} | "
                  f"{n:5d} {rate*100:10.1f}% {baseline_rate*100:8.1f}% {lift:5.2f}x")
        except Exception as e:
            print(f"M{mnum:<2d} {phase:>5s} {tech:>9s} {mount:>11s} | ERR {type(e).__name__}: {str(e)[:50]}")
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT, index=False)
    if len(df_out):
        print(f"\n=== Summary (n_systems={len(df_out)}) ===")
        print(f"  median rain-alignment: {df_out['rain_alignment_pct'].median():.1f}% "
              f"(baseline {baseline_rate*100:.1f}%, lift {df_out['lift'].median():.2f}x)")
        print(f"  range: {df_out['rain_alignment_pct'].min():.1f}% - {df_out['rain_alignment_pct'].max():.1f}%")
        print(f"  systems with >2x lift over baseline: {(df_out['lift']>2).sum()}/{len(df_out)}")
    print(f"\nWrote {OUT}")

if __name__ == "__main__":
    main()
