"""Probe 4 — DKA Alice Springs degradation across all distinct arrays.
Self-normalizing (per-file 99th-pct peak as Pdc0), robust to corrupt rows.
Uses on-site Radiation_Global_Tilted (measured POA) — no NSRDB needed."""
import os, glob, json, warnings, re
from pathlib import Path
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")
from rdtools import degradation_year_on_year

ROOT = Path(__file__).resolve().parent.parent
DKA = ROOT / "data/raw/dka"
OUT = ROOT / "data/processed/probe4_dka_plr.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

# Best-guess M# -> (catalog_label, technology, mount, vintage) per user catalog
# (peak power & dates will verify or flag mismatches)
CATALOG = {
    1:  ("Trina",        "mono-Si", "Dual",   2009),
    2:  ("eco-Kinetics", "mono-Si", "Dual",   2010),
    3:  ("BP Solar",     "poly-Si", "Fixed-roof", 2008),
    4:  ("Kyocera",      "poly-Si", "Dual",   2008),
    5:  ("Kyocera",      "poly-Si", "Single", 2008),
    6:  ("Kyocera",      "poly-Si", "Dual",   2008),
    7:  ("First Solar",  "CdTe",    "Fixed",  2008),
    8:  ("Kaneka",       "a-Si",    "Fixed",  2008),
    11: ("BP Solar",     "poly-Si", "Fixed",  2008),
    15: ("Archived UMG", "unknown", "Fixed",  2010),
    16: ("BP Solar",     "poly-Si", "Fixed",  2008),  # 16A-D 4 orientations
    17: ("Sanyo",        "HIT",     "Fixed",  2010),
    19: ("Sungrid",      "mono-Si", "Fixed",  2010),
}

POA_COL = "Radiation_Global_Tilted"
PWR_COL = "Active_Power"

def parse_file(p):
    """Read DKA per-array file robustly; return tidy DataFrame (ts, power, poa)."""
    try:
        df = pd.read_csv(p, usecols=lambda c: c in ("timestamp", PWR_COL, POA_COL),
                         engine="python", on_bad_lines="skip")
    except Exception as e:
        return None, f"parse_err:{type(e).__name__}"
    if PWR_COL not in df.columns or POA_COL not in df.columns:
        return None, "missing_col"
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df[PWR_COL] = pd.to_numeric(df[PWR_COL], errors="coerce")
    df[POA_COL] = pd.to_numeric(df[POA_COL], errors="coerce")
    df = df.dropna(subset=["timestamp", PWR_COL, POA_COL]).set_index("timestamp").sort_index()
    return df, "ok"


def compute_plr(df, fname):
    if df is None or len(df) < 100000:
        return {"file": fname, "status": "too_short"}
    # robust Pdc0 = 99th pct of positive power, after clipping wild outliers
    pwr = df[PWR_COL].clip(lower=0, upper=df[PWR_COL].quantile(0.9999))
    pdc0 = float(pwr.quantile(0.99))
    if pdc0 <= 0.1:
        return {"file": fname, "status": "no_power"}
    poa = df[POA_COL].clip(lower=0, upper=2000)  # W/m^2 plausible cap
    # 5-min interval: dt = 1/12 hr. energy = power*dt; insolation = poa/1000 * dt (kWh/m^2)
    dt_h = 1 / 12
    daily_e = (pwr * dt_h).resample("D").sum()                # kWh/day
    daily_ins = (poa / 1000.0 * dt_h).resample("D").sum()     # kWh/m^2/day
    # performance ratio (unitless); ~0.7-0.95 for healthy systems
    pr = daily_e / (daily_ins * pdc0)
    pr = pr[(daily_ins > 0.5) & (pr.between(0.2, 1.3))]       # drop near-zero-insolation + outlier days
    if len(pr) < 365 * 2:
        return {"file": fname, "status": "short_clean", "n_days": int(len(pr))}
    try:
        rd, ci, info = degradation_year_on_year(pr, recenter=True, confidence_level=68.2)
    except Exception as e:
        return {"file": fname, "status": f"rdtools_err:{type(e).__name__}"}
    return {
        "file": fname, "status": "ok",
        "plr_pct_yr": float(rd), "ci_low": float(ci[0]), "ci_high": float(ci[1]),
        "n_days": int(len(pr)), "pdc0_kw_99pct": pdc0, "pr_median": float(pr.median()),
        "first": str(pr.index.min().date()), "last": str(pr.index.max().date()),
    }


def m_number(fname):
    m = re.search(r"-M(\d+)_", fname)
    return int(m.group(1)) if m else None


def phase_label(fname):
    m = re.search(r"_([A-C0-9]+)-Phase", fname) or re.search(r"_(3-Phase)", fname)
    return m.group(1) if m else "?"


def main():
    files = sorted(glob.glob(str(DKA / "*Site_DKA-M*.csv")))
    rows = []
    print(f"{'M':>3s} {'phase':>5s} {'tech':>9s} {'mount':>11s} {'vint':>4s} | "
          f"{'pdc0':>6s} {'PLR%/yr':>9s} {'CI':>14s} {'n_days':>6s} {'PR':>5s} {'span':>22s}")
    print("-" * 130)
    for p in files:
        fname = os.path.basename(p)
        mnum = m_number(fname)
        if mnum is None:
            continue  # MasterMeter, WeatherStation, etc.
        phase = phase_label(fname)
        df, st = parse_file(p)
        res = compute_plr(df, fname)
        cat = CATALOG.get(mnum, ("?", "?", "?", None))
        brand, tech, mount, vint = cat
        res.update({"M_num": mnum, "phase": phase, "brand": brand,
                    "technology": tech, "mount": mount, "vintage": vint})
        rows.append(res)
        mlabel = f"M{mnum:<2d}"
        if res.get("status") == "ok":
            print(f"{mlabel:>4s} {phase:>5s} {tech:>9s} {mount:>11s} {vint!s:>4s} | "
                  f"{res['pdc0_kw_99pct']:6.2f} {res['plr_pct_yr']:+9.3f} "
                  f"[{res['ci_low']:+.2f},{res['ci_high']:+.2f}] {res['n_days']:6d} "
                  f"{res['pr_median']:.3f} {res['first']}-{res['last']}")
        else:
            print(f"{mlabel:>4s} {phase:>5s} {tech:>9s} {mount:>11s} {vint!s:>4s} | -- {res['status']}")
    df_out = pd.DataFrame(rows)
    df_out.to_csv(OUT, index=False)
    print(f"\nWrote {OUT} ({len(df_out)} rows)")

    # ---- technology summary (ok rows) ----
    ok = df_out[df_out["status"] == "ok"]
    if len(ok):
        print("\n=== PLR by technology (median across arrays/phases) ===")
        for tech, g in ok.groupby("technology"):
            med = g["plr_pct_yr"].median()
            print(f"  {tech:>10s}  n={len(g):2d}  median PLR = {med:+.3f} %/yr  "
                  f"[range {g['plr_pct_yr'].min():+.2f}, {g['plr_pct_yr'].max():+.2f}]")

if __name__ == "__main__":
    main()
