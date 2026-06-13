"""Probe 6 — V2 SECOND-SITE GENERALIZATION

Apply the multi-system synchrony decomposition (Jaccard + K-sweep) from Probe 5d
to a SECOND multi-system co-located PV fleet.

Test site: MA Pvoutput cluster — 21 residential rooftop systems within ~1 km
of each other in the Concord/Acton MA area (lat 42.46, lon -71.37), PVCZ 33
(temperate-humid, sub-tropical-humid US Northeast). Polar opposite of DKA
Alice Springs (PVCZ 41 arid).

Hypothesis (substrate-internal pre-decided before running):
- H_SYNC: if V2 methodology generalizes, pairwise SRR-recovery-event Jaccard
  among 21 co-located systems will be > random null
- H_SCALE: if methodology is data-scale-insensitive, the K-sweep will show the
  same monotone-rise-then-crash signature as DKA (low K → moderate K alignment
  rises; very-high K → alignment behavior reveals operational regime)

Caveats logged upfront:
- PVDAQ daily energy + modeled POA has the ~32% measurement noise floor that
  killed Probe 3 SRR on n=3 PVDAQ systems
- Low-soiling temperate-humid climate has fewer recovery events per system
  than DKA arid (less signal)
- No on-site precipitation; can't validate natural-cleaning regime here
  (defer to follow-up if synchrony generalizes)
- Outcome FEASIBILITY-NULL is admissible (per substrate convention L3)

This script outputs:
- probe6_recovery_dates.csv  (per-system recovery date list)
- probe6_pairwise_jaccard.csv
- probe6_consensus_days.csv
"""
import os, sys, warnings
from pathlib import Path
from itertools import combinations
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))
from probe2_plr_pipeline import (get_daily_energy, load_nsrdb, pull_nsrdb_year,
                                 model_expected_daily, WINDOW_START, WINDOW_END)
from probe3_soiling_feasibility import daily_poa_insolation
import rdtools.soiling as rsoil

FUZZ = 1   # +/- 1 day fuzz on recovery-date matching (matches Probe 5d)
OUT_REC  = ROOT / "data/processed/probe6_recovery_dates.csv"
OUT_JACC = ROOT / "data/processed/probe6_pairwise_jaccard.csv"
OUT_CONS = ROOT / "data/processed/probe6_consensus_days.csv"

# MA Pvoutput cluster (lat 42.457201, lon -71.37478)
MA_LAT, MA_LON = 42.457201, -71.37478


def srr_recoveries(sid, lat, lon, tilt, az, pdc0):
    """Adapted from probe3.feas(): returns set of recovery dates (or status)."""
    E = get_daily_energy(sid)
    if E is None: return ("no_energy", None)
    E = E[(E.index.year >= WINDOW_START) & (E.index.year <= WINDOW_END)]
    years = sorted(set(E.index.year))
    wx = [load_nsrdb(p) for y in years if (p := pull_nsrdb_year(lat, lon, y)) is not None]
    if not wx: return ("no_nsrdb", None)
    weather = pd.concat(wx).sort_index(); weather = weather[~weather.index.duplicated()]
    Emod = model_expected_daily(weather, lat, lon, tilt, az, pdc0)
    ins  = daily_poa_insolation(weather, lat, lon, tilt, az)
    df = pd.DataFrame({"meas": E, "mod": Emod, "ins": ins}).dropna()
    df = df[df["mod"] > 0.1 * df["mod"].median()]
    pi = (df["meas"] / df["mod"]); m = (pi > 0.2) & (pi < 1.8)
    pi, insol = pi[m], df["ins"][m]
    pi = pi / pi.quantile(0.98)  # normalize ~ 1 (SRR convention)
    if len(pi) < 365 * 2: return (f"short:n={len(pi)}", None)
    pi.index = pd.to_datetime(pi.index); insol.index = pd.to_datetime(insol.index)
    pi = pi.asfreq("D"); insol = insol.reindex(pi.index)
    try:
        sr, sr_ci, info = rsoil.soiling_srr(pi, insol, reps=100)
    except Exception as e:
        return (f"srr_err:{type(e).__name__}", None)
    summary = info.get("soiling_interval_summary") if isinstance(info, dict) else None
    if summary is None and isinstance(info, (list, tuple)):
        for it in info:
            if isinstance(it, pd.DataFrame) and "end" in it.columns:
                summary = it; break
    if summary is None: return ("no_summary", None)
    ends = pd.to_datetime(summary["end"]).dropna().dt.normalize().unique()
    return ("ok", set(ends))


def fuzzy_intersection(a, b, fuzz):
    b_expanded = set()
    for d in b:
        for k in range(-fuzz, fuzz + 1):
            b_expanded.add(d + pd.Timedelta(days=k))
    return sum(1 for d in a if d in b_expanded)


def jaccard_fuzzy(a, b, fuzz):
    inter = fuzzy_intersection(a, b, fuzz)
    inter_sym = max(inter, fuzzy_intersection(b, a, fuzz))
    union = len(a) + len(b) - inter_sym
    return inter_sym / union if union > 0 else 0.0


def main():
    idx = pd.read_csv(ROOT / "data/raw/datasets/PVDAQ_systems_20250729.csv").iloc[:, :26]
    ma = idx[(idx["latitude"] == MA_LAT) & (idx["longitude"] == MA_LON)].copy()
    print(f"MA Pvoutput cluster: {len(ma)} systems")

    sys_recs = {}
    fail_log = []
    for _, r in ma.iterrows():
        sid = int(r["system_id"])
        tilt = float(r["tilt"]) if pd.notna(r["tilt"]) else 30.0
        az = float(r["azimuth"]) if (pd.notna(r["azimuth"]) and r["azimuth"] >= 0) else 180.0
        pdc0 = float(r["dc_capacity_kW"])
        status, recs = srr_recoveries(sid, float(r["latitude"]), float(r["longitude"]),
                                       tilt, az, pdc0)
        if status == "ok" and recs is not None and len(recs) >= 5:
            key = f"sys{sid}"
            sys_recs[key] = recs
            print(f"  {key}: n_recoveries={len(recs)}  tilt={tilt:.0f} az={az:.0f}  cap={pdc0:.2f}kW")
        else:
            fail_log.append({"sid": sid, "status": status, "n_recs": len(recs) if recs else 0})
            print(f"  sys{sid}: {status} (n={len(recs) if recs else 0})")

    print(f"\nSystems usable: {len(sys_recs)}/{len(ma)}")
    if len(sys_recs) < 4:
        print("INSUFFICIENT systems for synchrony test — FEASIBILITY-NULL.")
        return

    # Save per-system recovery dates
    recs_long = []
    for key, dates in sys_recs.items():
        for d in dates:
            recs_long.append({"system": key, "recovery_date": d.strftime("%Y-%m-%d")})
    pd.DataFrame(recs_long).to_csv(OUT_REC, index=False)

    # Span (use union of all systems' window)
    all_dates = sorted(set.union(*sys_recs.values()))
    if not all_dates:
        print("NO recoveries; FEASIBILITY-NULL.")
        return
    span_start = pd.Timestamp(WINDOW_START, 1, 1)
    span_end = pd.Timestamp(WINDOW_END, 12, 31)
    span_days = pd.date_range(span_start, span_end, freq="D")
    print(f"\nSpan: {span_start.date()} - {span_end.date()} ({len(span_days)} days)")

    # ---- pairwise Jaccard ----
    print("\n=== Pairwise Jaccard similarity of recovery dates (+/-1 day fuzz) ===")
    jrows = []
    for a, b in combinations(sys_recs.keys(), 2):
        j = jaccard_fuzzy(sys_recs[a], sys_recs[b], FUZZ)
        jrows.append({"a": a, "b": b, "jaccard": j,
                      "n_a": len(sys_recs[a]), "n_b": len(sys_recs[b])})
    jdf = pd.DataFrame(jrows)
    jdf.to_csv(OUT_JACC, index=False)
    print(f"  n_pairs       = {len(jdf)}")
    print(f"  Jaccard median = {jdf['jaccard'].median():.3f}")
    print(f"  Jaccard mean   = {jdf['jaccard'].mean():.3f}")
    print(f"  Jaccard range  = [{jdf['jaccard'].min():.3f}, {jdf['jaccard'].max():.3f}]")

    med_n = float(np.median([len(s) for s in sys_recs.values()]))
    p_recov_day = (med_n * (2*FUZZ + 1)) / len(span_days)
    j_random = p_recov_day**2 / (2*p_recov_day - p_recov_day**2)
    print(f"  baseline (random) Jaccard ~ {j_random:.4f} (p_recovery_day = {p_recov_day:.4f})")
    if j_random > 0:
        print(f"  -> observed/random ratio: {jdf['jaccard'].median() / j_random:.2f}x")
    print(f"  -> for reference: DKA had 4.78x random (Jaccard 0.259 vs 0.054)")

    # ---- consensus days ----
    print("\n=== Consensus-day analysis (>=K systems recover on same +/-1d window) ===")
    day_count = {}
    for key, dates in sys_recs.items():
        for d in dates:
            for k in range(-FUZZ, FUZZ + 1):
                day_count.setdefault(d + pd.Timedelta(days=k), set()).add(key)
    consensus_rows = []
    for K in range(1, len(sys_recs) + 1):
        days_at_k = [d for d, syss in day_count.items() if len(syss) >= K]
        n_days = len(set(days_at_k))
        consensus_rows.append({"K_min_systems": K, "n_consensus_days": n_days})
    cdf = pd.DataFrame(consensus_rows)
    cdf.to_csv(OUT_CONS, index=False)
    print(f"{'K':>3s} {'n_days':>7s}")
    for _, r in cdf.iterrows():
        print(f"{int(r['K_min_systems']):>3d} {int(r['n_consensus_days']):>7d}")

    print("\n=== Verdict on V2 generalization ===")
    ratio = jdf['jaccard'].median() / j_random if j_random > 0 else 0.0
    if ratio >= 2.0:
        print(f"GENERALIZES: observed/random Jaccard {ratio:.2f}x >= 2x threshold; methodology survives at MA Pvoutput")
    elif ratio >= 1.2:
        print(f"PARTIAL: observed/random Jaccard {ratio:.2f}x; methodology direction holds but weaker than DKA 4.78x")
    else:
        print(f"NULL: observed/random Jaccard {ratio:.2f}x < 1.2x; methodology does NOT generalize to MA at this data scale")

    if fail_log:
        print(f"\nFailures logged: {len(fail_log)}/{len(ma)} systems")
        for f in fail_log:
            print(f"  sys{f['sid']}: {f['status']}")


if __name__ == "__main__":
    main()
