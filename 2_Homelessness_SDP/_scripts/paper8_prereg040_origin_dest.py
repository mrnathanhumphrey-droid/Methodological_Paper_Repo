"""
PRE_REG_040 — IDU origin-vs-destination co-location (Phase 3).
Splits each IDU displacement event's locations into Origin / Destination (via
locations_type || locations_coordinates), bins to 0.5deg cells per channel
(Conflict/Disaster) per role, and tests whether conflict-IDP & disaster-IDP
co-locate MORE at destinations than origins (the Phase 2 reframe).

Set A: SOM rho_destination > rho_origin AND rho_destination > +0.3
Set B: across both-channel countries, rho_dest > rho_origin (paired)
Set C: origins distinct (gap >= +0.15)
"""
from __future__ import annotations
import glob, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
IDU = Path("D:/IDP/data/idmc_gidd/idu")
OUT = Path("D:/IDP/analysis/paper8_prereg040_origin_dest_2026_05_29.json")
GRID = 0.5
MIN_EV = 30


def cell(lat, lon):
    return (float(np.floor(lat / GRID) * GRID), float(np.floor(lon / GRID) * GRID))


def parse_event_locations(types_s, coords_s):
    """Return (origins:list[(lat,lon)], dests:list[(lat,lon)])."""
    if not isinstance(types_s, str) or not isinstance(coords_s, str):
        return [], []
    types = [t.strip() for t in types_s.split(";")]
    coords = [c.strip() for c in coords_s.split(";")]
    if len(types) != len(coords) or not types:
        return [], []
    origins, dests = [], []
    for t, c in zip(types, coords):
        try:
            lat, lon = [float(x) for x in c.split(",")[:2]]
        except Exception:
            continue
        if abs(lat) > 90 or abs(lon) > 180:
            continue
        if "Origin" in t:
            origins.append((lat, lon))
        if "Destination" in t:
            dests.append((lat, lon))
    return origins, dests


def load_country(path):
    for kw in (dict(low_memory=False), dict(engine="python", on_bad_lines="skip")):
        try:
            return pd.read_csv(path, **kw)
        except Exception:
            continue
    return None


def colocate(conf_cells, dis_cells):
    """conf_cells, dis_cells: dict cell->figure. Spearman across union of nonzero cells."""
    cells = sorted(set(conf_cells) | set(dis_cells))
    if len(cells) < 8:
        return None, len(cells)
    cv = np.array([conf_cells.get(c, 0.0) for c in cells])
    dv = np.array([dis_cells.get(c, 0.0) for c in cells])
    if cv.std() == 0 or dv.std() == 0:
        return None, len(cells)
    r, p = stats.spearmanr(cv, dv)
    return (round(float(r), 3), round(float(p), 4)), len(cells)


def main():
    seen = set()
    rows = {}
    for f in sorted(glob.glob(str(IDU / "*.csv"))):
        df = load_country(f)
        if df is None or "iso3" not in df.columns:
            continue
        iso = df["iso3"].dropna().iloc[0] if df["iso3"].notna().any() else None
        if iso in seen or iso is None:
            continue
        seen.add(iso)
        df = df.drop_duplicates(subset=["id"]) if "id" in df.columns else df
        df["figure"] = pd.to_numeric(df["figure"], errors="coerce")
        df = df[df["displacement_type"].isin(["Conflict", "Disaster"]) & df["figure"].gt(0)]
        if len(df) < 2 * MIN_EV:
            continue
        # build per-role per-channel cell maps
        maps = {(ch, role): {} for ch in ("Conflict", "Disaster") for role in ("O", "D")}
        nparsed = {"Conflict": 0, "Disaster": 0}
        combo = 0
        for _, r in df.iterrows():
            ch = r["displacement_type"]
            origins, dests = parse_event_locations(r.get("locations_type"), r.get("locations_coordinates"))
            if not origins and not dests:
                continue
            if isinstance(r.get("locations_type"), str) and "Origin and destination" in r["locations_type"]:
                combo += 1
            nparsed[ch] += 1
            fig = float(r["figure"])
            for (lat, lon) in origins:
                c = cell(lat, lon); maps[(ch, "O")][c] = maps[(ch, "O")].get(c, 0.0) + fig
            for (lat, lon) in dests:
                c = cell(lat, lon); maps[(ch, "D")][c] = maps[(ch, "D")].get(c, 0.0) + fig
        if nparsed["Conflict"] < MIN_EV or nparsed["Disaster"] < MIN_EV:
            continue
        rho_o, no = colocate(maps[("Conflict", "O")], maps[("Disaster", "O")])
        rho_d, nd = colocate(maps[("Conflict", "D")], maps[("Disaster", "D")])
        rows[iso] = {"n_conf": nparsed["Conflict"], "n_dis": nparsed["Disaster"],
                     "rho_origin": rho_o, "rho_dest": rho_d, "n_origin_cells": no, "n_dest_cells": nd,
                     "combo_share": round(combo / max(1, nparsed['Conflict'] + nparsed['Disaster']), 2)}
        ro = rho_o[0] if rho_o else None; rd = rho_d[0] if rho_d else None
        gap = round(rd - ro, 3) if (ro is not None and rd is not None) else None
        rows[iso]["gap_dest_minus_origin"] = gap
        print(f"  {iso}: conf={nparsed['Conflict']} dis={nparsed['Disaster']} | "
              f"rho_origin={ro} rho_dest={rd} gap={gap}")

    # ---- verdicts ----
    print("\n" + "=" * 80); print("VERDICTS"); print("=" * 80)
    som = rows.get("SOM", {})
    so, sd = (som.get("rho_origin") or [None])[0] if som.get("rho_origin") else None, \
             (som.get("rho_dest") or [None])[0] if som.get("rho_dest") else None
    setA = sd is not None and so is not None and sd > so and sd > 0.3
    print(f"  Set A (SOM rho_dest>rho_origin & rho_dest>+0.3): origin={so} dest={sd} -> {'SUPPORTED' if setA else 'NOT'}")
    # Set B paired
    pairs = [(r["rho_dest"][0], r["rho_origin"][0], iso) for iso, r in rows.items()
             if r["rho_dest"] and r["rho_origin"]]
    setB = None
    if len(pairs) >= 4:
        dests = [p[0] for p in pairs]; origs = [p[1] for p in pairs]
        diffs = np.array(dests) - np.array(origs)
        try:
            w, pw = stats.wilcoxon(diffs)
        except Exception:
            w, pw = None, None
        setB = {"n": len(pairs), "median_gap": round(float(np.median(diffs)), 3),
                "frac_dest_gt_origin": round(float(np.mean(diffs > 0)), 2),
                "wilcoxon_p": round(float(pw), 4) if pw is not None else None,
                "by_country": {p[2]: (p[0], p[1]) for p in pairs}}
        print(f"  Set B (paired dest>origin, n={len(pairs)}): median_gap={setB['median_gap']} "
              f"frac={setB['frac_dest_gt_origin']} p={setB['wilcoxon_p']}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"grid": GRID, "rows": rows, "setA": bool(setA), "setB": setB},
                              indent=2, default=str), encoding="utf-8")
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
