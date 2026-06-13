"""
PRE_REG_041 — compound-destination burden + temporal co-occurrence (Phase 4 capstone).
Parses IDU DESTINATION locations per channel per cell per YEAR (figure-weighted).
Shared-destination cells = top tercile of BOTH conflict-dest and disaster-dest.
H1: burden share absorbed by shared cells (+ Gini, top-decile).
H2: within shared cells, same-year co-occurrence of conflict-dest & disaster-dest.
Set C: lag -1/0/+1 (contemporaneous?).
"""
from __future__ import annotations
import glob, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
IDU = Path("D:/IDP/data/idmc_gidd/idu")
OUT = Path("D:/IDP/analysis/paper8_prereg041_burden_2026_05_29.json")
GRID = 0.5
MIN_EV = 30


def cell(lat, lon):
    return (float(np.floor(lat / GRID) * GRID), float(np.floor(lon / GRID) * GRID))


def dest_locations(types_s, coords_s):
    if not isinstance(types_s, str) or not isinstance(coords_s, str):
        return []
    types = [t.strip() for t in types_s.split(";")]
    coords = [c.strip() for c in coords_s.split(";")]
    if len(types) != len(coords):
        return []
    out = []
    for t, c in zip(types, coords):
        if "Destination" not in t:
            continue
        try:
            lat, lon = [float(x) for x in c.split(",")[:2]]
        except Exception:
            continue
        if abs(lat) <= 90 and abs(lon) <= 180:
            out.append((lat, lon))
    return out


def gini(x):
    x = np.sort(np.asarray(x, float)); n = len(x)
    if n == 0 or x.sum() == 0:
        return None
    return round(float((2 * np.sum((np.arange(1, n + 1)) * x) / (n * x.sum())) - (n + 1) / n), 3)


def load_country(path):
    for kw in (dict(low_memory=False), dict(engine="python", on_bad_lines="skip")):
        try:
            return pd.read_csv(path, **kw)
        except Exception:
            continue
    return None


def main():
    seen, rows = set(), {}
    for f in sorted(glob.glob(str(IDU / "*.csv"))):
        df = load_country(f)
        if df is None or "iso3" not in df.columns or not df["iso3"].notna().any():
            continue
        iso = df["iso3"].dropna().iloc[0]
        if iso in seen:
            continue
        seen.add(iso)
        if "id" in df.columns:
            df = df.drop_duplicates(subset=["id"])
        df["figure"] = pd.to_numeric(df["figure"], errors="coerce")
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
        df = df[df["displacement_type"].isin(["Conflict", "Disaster"]) & df["figure"].gt(0) & df["year"].notna()]
        if len(df) < 2 * MIN_EV:
            continue
        # per (cell, year, channel) destination figure
        cy = {"Conflict": {}, "Disaster": {}}     # cumulative per cell
        cyy = {"Conflict": {}, "Disaster": {}}    # per (cell, year)
        nch = {"Conflict": 0, "Disaster": 0}
        for _, r in df.iterrows():
            ch = r["displacement_type"]; fig = float(r["figure"]); yr = int(r["year"])
            for (lat, lon) in dest_locations(r.get("locations_type"), r.get("locations_coordinates")):
                c = cell(lat, lon)
                cy[ch][c] = cy[ch].get(c, 0.0) + fig
                cyy[ch][(c, yr)] = cyy[ch].get((c, yr), 0.0) + fig
                nch[ch] += 1
        if nch["Conflict"] < MIN_EV or nch["Disaster"] < MIN_EV:
            continue
        all_cells = sorted(set(cy["Conflict"]) | set(cy["Disaster"]))
        conf = np.array([cy["Conflict"].get(c, 0.0) for c in all_cells])
        dis = np.array([cy["Disaster"].get(c, 0.0) for c in all_cells])
        if len(all_cells) < 8:
            continue
        # shared-destination cells: top tercile of BOTH
        ct, dt = np.quantile(conf, 2 / 3), np.quantile(dis, 2 / 3)
        shared = [c for c, cf, ds in zip(all_cells, conf, dis) if cf >= ct and ds >= dt and cf > 0 and ds > 0]
        total = conf.sum() + dis.sum()
        shared_disp = sum(cy["Conflict"].get(c, 0) + cy["Disaster"].get(c, 0) for c in shared)
        burden = round(shared_disp / total, 3) if total else None
        # top-decile share
        tot_per_cell = conf + dis
        dec = np.quantile(tot_per_cell, 0.9)
        topdec_share = round(float(tot_per_cell[tot_per_cell >= dec].sum() / total), 3) if total else None

        # H2: same-year co-occurrence within shared cells
        def cooc(cells_set, lag=0):
            xs, ys = [], []
            years = range(2008, 2027)
            for c in cells_set:
                for y in years:
                    a = cyy["Conflict"].get((c, y), 0.0)
                    b = cyy["Disaster"].get((c, y + lag), 0.0)
                    if a > 0 or b > 0:
                        xs.append(a); ys.append(b)
            if len(xs) >= 8 and np.std(xs) > 0 and np.std(ys) > 0:
                r, p = stats.spearmanr(xs, ys)
                return (round(float(r), 3), round(float(p), 4), len(xs))
            return None
        h2_shared = cooc(shared, 0)
        nonshared = [c for c in all_cells if c not in set(shared)]
        h2_non = cooc(nonshared, 0)
        lags = {lag: cooc(shared, lag) for lag in (-1, 0, 1)}

        rows[iso] = {"n_conf": nch["Conflict"], "n_dis": nch["Disaster"], "n_cells": len(all_cells),
                     "n_shared": len(shared), "burden_share": burden, "topdecile_share": topdec_share,
                     "gini": gini(tot_per_cell), "h2_shared_lag0": h2_shared, "h2_nonshared_lag0": h2_non,
                     "lags": lags, "yr_min": int(df["year"].min()), "yr_max": int(df["year"].max())}
        print(f"  {iso}: cells={len(all_cells)} shared={len(shared)} burden={burden} "
              f"topdec={topdec_share} gini={gini(tot_per_cell)} | H2shared={h2_shared} H2non={h2_non} lags={lags}")

    print("\n" + "=" * 80); print("VERDICTS (SOM decisive)"); print("=" * 80)
    som = rows.get("SOM", {})
    b = som.get("burden_share"); h2 = som.get("h2_shared_lag0"); h2n = som.get("h2_nonshared_lag0")
    setA = b is not None and b >= 0.40
    setB = h2 is not None and h2[0] > 0 and (h2n is None or h2[0] > h2n[0])
    lags = som.get("lags", {})
    print(f"  Set A (shared-dest burden >=40%): SOM burden={b} (topdecile={som.get('topdecile_share')}, gini={som.get('gini')}) -> {'SUPPORTED' if setA else 'NOT'}")
    print(f"  Set B (same-year co-occurrence>0 & >nonshared): shared={h2} nonshared={h2n} -> {'SUPPORTED' if setB else 'NOT'}")
    print(f"  Set C (contemporaneous lag0 strongest): {lags}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"grid": GRID, "rows": rows, "setA": bool(setA), "setB": bool(setB)},
                              indent=2, default=str), encoding="utf-8")
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
