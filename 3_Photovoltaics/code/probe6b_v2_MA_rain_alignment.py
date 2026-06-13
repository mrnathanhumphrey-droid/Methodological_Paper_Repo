"""Probe 6b — V2 second-site rain alignment at MA Pvoutput cluster.

Probe 6 showed Jaccard 2.01x random null at MA (synchrony detected) and K=17-18
crash pattern matching DKA's K=12-13. But couldn't test natural-vs-operational
without precipitation data.

This probe pulls ERA5 precipitation (Open-Meteo backend) for the cluster
centroid (lat 42.457, lon -71.375), then re-runs the K-consensus analysis with
rain-alignment scoring.

Expected outcomes:
- If methodology fully generalizes: alignment rises with K then CRASHES at very
  high K (just like DKA K=12-13 crash). This would mean even at MA, the
  highest-consensus events are operational not natural.
- If methodology is climate-floored: alignment stays at baseline across all K
  (no separation possible at humid sites because baseline is too high).
- Either is informative; the latter is a substrate-discovered limit on V2.

CAVEAT: ERA5 precipitation at 0.25 deg grid is regional, not on-site like DKA
weather station. Possible discrepancy with what individual rooftops experienced.

Output:
- probe6b_rain_precip.csv (cached daily precip)
- probe6b_K_rain_alignment.csv (K vs alignment %)
"""
import os, sys, json, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import requests
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))

PRECIP_CACHE = ROOT / "data/raw/precip"
PRECIP_CACHE.mkdir(parents=True, exist_ok=True)
PRECIP_FILE = PRECIP_CACHE / "MA_Concord_42.457_-71.375_2018-2023_ERA5.csv"

OUT_PRECIP = ROOT / "data/processed/probe6b_rain_precip.csv"
OUT_KRAIN  = ROOT / "data/processed/probe6b_K_rain_alignment.csv"

MA_LAT, MA_LON = 42.457201, -71.37478
FUZZ = 1
RAIN_THR = 1.0  # mm/day, matches probe5b convention


def pull_era5_precip():
    """Pull daily precipitation from Open-Meteo (ERA5 reanalysis backend). Cached."""
    if PRECIP_FILE.exists():
        return pd.read_csv(PRECIP_FILE, parse_dates=["date"]).set_index("date")["precip_mm"]
    url = "https://archive-api.open-meteo.com/v1/era5"
    params = {
        "latitude": MA_LAT, "longitude": MA_LON,
        "start_date": "2018-01-01", "end_date": "2023-12-31",
        "daily": "precipitation_sum", "timezone": "America/New_York"
    }
    r = requests.get(url, params=params, timeout=120)
    r.raise_for_status()
    d = r.json()
    df = pd.DataFrame({
        "date": pd.to_datetime(d["daily"]["time"]),
        "precip_mm": d["daily"]["precipitation_sum"]
    })
    df.to_csv(PRECIP_FILE, index=False)
    return df.set_index("date")["precip_mm"]


def main():
    print("Loading ERA5 daily precipitation for MA Pvoutput cluster centroid...")
    precip = pull_era5_precip()
    precip = precip.fillna(0)
    rain_days = set(d.normalize() for d in precip.index[precip >= RAIN_THR])
    span_days = pd.date_range(precip.index.min(), precip.index.max(), freq="D")

    # Baseline: fraction of span days within +/-FUZZ of any rain day
    base_rain_aligned_set = set()
    for d in rain_days:
        for k in range(-FUZZ, FUZZ + 1):
            base_rain_aligned_set.add(d + pd.Timedelta(days=k))
    baseline_rain = len(base_rain_aligned_set & set(span_days.normalize())) / len(span_days)

    print(f"Span: {precip.index.min().date()} - {precip.index.max().date()} ({len(span_days)} days)")
    print(f"Rain days >= {RAIN_THR} mm: {len(rain_days)} ({len(rain_days)/len(span_days)*100:.1f}%)")
    print(f"Baseline rain-alignment (+/-{FUZZ}d): {baseline_rain*100:.1f}%")
    print(f"(DKA arid baseline was 21%; MA humid baseline is much higher -> test discriminating power is REDUCED)\n")

    # Save precip alongside processed outputs
    pd.DataFrame({"date": span_days, "precip_mm": precip.reindex(span_days).fillna(0).values,
                  "is_rainy": [d in rain_days for d in span_days]}).to_csv(OUT_PRECIP, index=False)

    # Load Probe 6 recovery dates
    recs = pd.read_csv(ROOT / "data/processed/probe6_recovery_dates.csv")
    recs["recovery_date"] = pd.to_datetime(recs["recovery_date"])
    sys_recs = {sys_: set(g["recovery_date"]) for sys_, g in recs.groupby("system")}
    n_sys = len(sys_recs)
    print(f"Loaded recoveries: {n_sys} systems")

    # K-consensus + rain alignment
    day_count = {}
    for key, dates in sys_recs.items():
        for d in dates:
            for k in range(-FUZZ, FUZZ + 1):
                day_count.setdefault(d + pd.Timedelta(days=k), set()).add(key)

    print(f"\n=== K-consensus rain alignment (baseline {baseline_rain*100:.1f}%) ===")
    rows = []
    print(f"{'K':>3s} {'n_days':>7s} {'n_rainy':>8s} {'pct':>6s} {'lift':>5s}")
    for K in range(1, n_sys + 1):
        days_at_k = sorted(set(d for d, syss in day_count.items() if len(syss) >= K))
        n_days = len(days_at_k)
        rain_hits = sum(1 for d in days_at_k if d in base_rain_aligned_set)
        pct = rain_hits / n_days * 100 if n_days else 0
        lift = (rain_hits / n_days) / baseline_rain if (n_days and baseline_rain) else None
        rows.append({"K_min_systems": K, "n_consensus_days": n_days,
                     "n_rain_aligned": rain_hits, "pct_rain_aligned": pct,
                     "lift_vs_baseline": lift})
        if n_days > 0:
            print(f"{K:>3d} {n_days:>7d} {rain_hits:>8d} {pct:>5.1f}% {lift:>4.2f}x")

    pd.DataFrame(rows).to_csv(OUT_KRAIN, index=False)
    print(f"\nWrote {OUT_KRAIN.name}")

    # Verdict
    print("\n=== VERDICT ===")
    # Look for: alignment rises in mid-K then crashes at high K
    df = pd.DataFrame(rows)
    df_alive = df[df["n_consensus_days"] > 0].copy()
    if len(df_alive) >= 3:
        peak_K = df_alive.iloc[df_alive["pct_rain_aligned"].idxmax()]
        max_K = df_alive["K_min_systems"].max()
        high_K = df_alive[df_alive["K_min_systems"] >= max_K - 2]
        high_K_pct = high_K["pct_rain_aligned"].mean()
        print(f"Peak rain-alignment: K={int(peak_K['K_min_systems'])} at {peak_K['pct_rain_aligned']:.1f}% (lift {peak_K['lift_vs_baseline']:.2f}x)")
        print(f"High-K (K>={int(max_K-2)}) mean alignment: {high_K_pct:.1f}% (baseline {baseline_rain*100:.1f}%)")
        if high_K_pct < baseline_rain * 100 * 0.85:
            print("OPERATIONAL CRASH at high K: alignment falls below baseline -> operational regime detected; methodology FULLY GENERALIZES")
        elif high_K_pct < peak_K['pct_rain_aligned'] * 0.85:
            print("HIGH-K DECLINE present (but not below baseline): partial operational signature; methodology partially generalizes")
        else:
            print("NO HIGH-K CRASH: alignment stays elevated across all K -> humid-climate baseline-saturation, V2 climate-floored at temperate-humid")


if __name__ == "__main__":
    main()
