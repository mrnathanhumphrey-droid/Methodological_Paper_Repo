"""Probe 12 — V2 inverter-swap confound check.

DKA Notes-on-Data (public) lists 4 known operational events 2022-2024:
- 2023-02-03: SMA Site 21 Inverter -> Fronius (per-system)
- 2023-01-24: DKASC offline ~08:00 (site-wide network shutdown)
- 2022-12-15: Original SMA inverters replaced (multiple systems, batch swap)
- 2022-06-01: Site 10 + 12 intermittent inverter issues (per-system)

Inverter swaps cause sudden power-step changes that SRR could detect as
recovery events. If our V2 "operational" K=12-13 events at DKA fall within
+/-7 days of these known inverter operations, the V2 operational claim is
partially confounded.

Test:
- For each known operational date, count K>=11, K=12, K=13 events within +/-7d
- Compare to the random expectation if our 169 K>=11 events were uniformly
  distributed across the 17-year span
- If material clustering (>5x random expectation), flag as confound

If NO clustering: V2 strengthens. The K=12-13 events are NOT explained by
the publicly-noted inverter operations.

Also test: do K=12-13 events cluster in the YEARS 2022-2023 (when the
known operations occurred)? If yes -> potential confound period. If no ->
events are spread across all years, consistent with annual cleaning regime.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data/processed/probe8_dka_recovery_dates_cache.csv"
WEATHER = ROOT / "data/raw/dka/101-Site_DKA-WeatherStation.csv"
OUT = ROOT / "data/processed/probe12_inverter_swap_check.csv"

FUZZ = 1
WINDOW_DAYS = 7  # +/-7d around known operational events

KNOWN_EVENTS = [
    ("2023-02-03", "SMA Site 21 -> Fronius (per-system)"),
    ("2023-01-24", "DKASC offline network shutdown (site-wide)"),
    ("2022-12-15", "Original SMA inverters replaced (batch)"),
    ("2022-06-01", "Site 10 + 12 intermittent inverter issues"),
]


def load_rain_span():
    df = pd.read_csv(WEATHER, usecols=["timestamp", "Weather_Daily_Rainfall"],
                     engine="python", on_bad_lines="skip")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna().set_index("timestamp").sort_index()
    return df.index.min().normalize(), df.index.max().normalize()


def main():
    span_start, span_end = load_rain_span()
    span_days = (span_end - span_start).days + 1
    print(f"Substrate span: {span_start.date()} to {span_end.date()} ({span_days} days)")

    df = pd.read_csv(CACHE)
    df["recovery_date"] = pd.to_datetime(df["recovery_date"])
    sys_recs = {k: set(g["recovery_date"]) for k, g in df.groupby("system")}
    n_sys = len(sys_recs)
    print(f"Systems: {n_sys}\n")

    day_count = {}
    for key, dates in sys_recs.items():
        for d in dates:
            for k in range(-FUZZ, FUZZ + 1):
                day_count.setdefault(d + pd.Timedelta(days=k), set()).add(key)

    # Per-K event sets
    k_events = {K: sorted(set(d for d, syss in day_count.items() if len(syss) >= K))
                for K in [11, 12, 13]}
    for K, evs in k_events.items():
        print(f"K>={K}: {len(evs)} total events across {span_days/365:.1f} years")

    # ===================================================================
    # Per-known-event window check
    # ===================================================================
    print(f"\n=== K=12,13 events within +/-{WINDOW_DAYS}d of known operational events ===")
    rows = []
    for ev_date_str, label in KNOWN_EVENTS:
        ev = pd.Timestamp(ev_date_str)
        print(f"\n{ev_date_str}: {label}")
        for K in [11, 12, 13]:
            nearby = [d for d in k_events[K] if abs((d - ev).days) <= WINDOW_DAYS]
            # Expected by chance: density × (2W+1)
            density = len(k_events[K]) / span_days
            expected_nearby = density * (2 * WINDOW_DAYS + 1)
            ratio = len(nearby) / expected_nearby if expected_nearby > 0 else float("inf")
            print(f"  K>={K}: {len(nearby)} events nearby (expected by chance {expected_nearby:.2f}, ratio {ratio:.2f}x)")
            for d in nearby:
                delta = (d - ev).days
                k_actual = len(day_count[d])
                print(f"    {d.date()} (delta {delta:+d}d, actual K={k_actual})")
            rows.append({"known_event": ev_date_str, "known_label": label,
                         "K_thresh": K, "n_nearby": len(nearby),
                         "expected_chance": expected_nearby, "ratio": ratio})

    # ===================================================================
    # Year-by-year distribution of K=12,13 events
    # ===================================================================
    print(f"\n=== Year-by-year K=12,13 event counts ===")
    print(f"If K=12-13 events are dominated by 2022-2023 inverter operations,")
    print(f"that period should be heavily over-represented.\n")
    print(f"{'year':>5} {'K>=11':>6} {'K>=12':>6} {'K>=13':>6}")
    years = list(range(2009, 2026))
    yearly_rows = []
    for y in years:
        counts = {K: sum(1 for d in k_events[K] if d.year == y) for K in [11, 12, 13]}
        print(f"{y:>5d} {counts[11]:>6d} {counts[12]:>6d} {counts[13]:>6d}")
        yearly_rows.append({"year": y, **{f"K_ge_{K}": counts[K] for K in [11, 12, 13]}})

    # Concentration metric: what fraction of K=12-13 events fall in 2022-2023?
    print(f"\n=== Confound period check (2022-2023) ===")
    for K in [11, 12, 13]:
        events_22_23 = sum(1 for d in k_events[K] if d.year in [2022, 2023])
        total = len(k_events[K])
        frac = events_22_23 / total
        expected_frac = 2 / (span_days / 365)  # 2 years out of ~17
        print(f"K>={K}: {events_22_23}/{total} = {frac*100:.1f}% in 2022-2023 (expected {expected_frac*100:.1f}% by uniform)")

    # ===================================================================
    # Verdict
    # ===================================================================
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nWrote {OUT.name}")

    print("\n=== VERDICT ===")
    # Sum nearby events for K=12,13 within +/-7d of any known event
    union_k12 = set()
    union_k13 = set()
    for ev_date_str, _ in KNOWN_EVENTS:
        ev = pd.Timestamp(ev_date_str)
        for d in k_events[12]:
            if abs((d - ev).days) <= WINDOW_DAYS:
                union_k12.add(d)
        for d in k_events[13]:
            if abs((d - ev).days) <= WINDOW_DAYS:
                union_k13.add(d)
    print(f"K=12: {len(union_k12)}/{len(k_events[12])} = {len(union_k12)/len(k_events[12])*100:.1f}% within +/-7d of ANY known operational event")
    print(f"K=13: {len(union_k13)}/{len(k_events[13])} = {len(union_k13)/len(k_events[13])*100:.1f}% within +/-7d of ANY known operational event")
    expected_pct = (len(KNOWN_EVENTS) * (2 * WINDOW_DAYS + 1)) / span_days * 100
    print(f"Expected by chance if uniform: {expected_pct:.1f}%")


if __name__ == "__main__":
    main()
