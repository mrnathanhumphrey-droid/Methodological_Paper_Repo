"""
PRE_REG_039 — sub-national drought x conflict co-location (Phase 2).
Dense SPEI drought channel (GEE CSIC/SPEI/2_10, 0.5deg cells) x UCDP-GED conflict.

Per country (extent = UCDP event bbox + 2deg margin), at 0.5deg cells:
  drought_freq = # years (1990-2023) Dec SPEI_12 <= -1.0   (sampled at all cells)
  conflict     = sum UCDP 'best' fatalities               (binned locally)
H1 spatial: conflict cells vs non-conflict cells drought_freq (Mann-Whitney);
            Spearman(conflict_intensity, drought_freq) among conflict cells.
H2 spatio-temporal: within conflict cells, conflict in drought-years vs non (Wilcoxon).
Set B: per-country spatial signal vs national coupling (GIDD pooled).
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import ee

sys.stdout.reconfigure(encoding="utf-8")
GED = Path("D:/IDP/data/ucdp/GEDEvent_v25_1.csv")  # full history 1989-2024 (v26 is 2026-candidate only)
GIDD_DIS = Path("D:/IDP/data/idmc_gidd/IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx")
GIDD_CONF = Path("D:/IDP/data/idmc_gidd/IDMC_GIDD_Conflict_Violence_Disasters.xlsx")
OUT = Path("D:/IDP/analysis/paper8_prereg039_grid_2026_05_29.json")
GRID = 0.5
Y0, Y1 = 1990, 2023
DTHR = -1.0

# UCDP country_id (Gleditsch-Ward) -> (iso, coupling?)
CSET = {
    530: ("ETH", True), 520: ("SOM", True), 140: ("BRA", True), 490: ("COD", True),
    771: ("BGD", True), 70: ("MEX", True), 369: ("UKR", True), 640: ("TUR", True),
    840: ("PHL", False), 475: ("NGA", False), 432: ("MLI", False), 436: ("NER", False),
    625: ("SDN", False), 652: ("SYR", False), 700: ("AFG", False), 645: ("IRQ", False),
    100: ("COL", False), 471: ("CMR", False), 775: ("MMR", False), 541: ("MOZ", False),
}


def cellkey(lat, lon):
    return (float(np.floor(lat / GRID) * GRID), float(np.floor(lon / GRID) * GRID))


def build_spei_images():
    coll = ee.ImageCollection("CSIC/SPEI/2_10").select("SPEI_12_month")
    def dec(y):
        img = coll.filterDate(f"{y}-12-01", f"{y}-12-31").first().rename(f"y{y}")
        return img.updateMask(img.abs().lt(10))
    years = list(range(Y0, Y1 + 1))
    stack = ee.Image.cat([dec(y) for y in years])
    dfreq = ee.Image.cat([dec(y).lte(DTHR).rename(f"d{y}") for y in years]).reduce(ee.Reducer.sum()).rename("dfreq")
    return stack, dfreq, years


def sample_points(image, cells, scale=55660, batch=2000):
    """cells: list of (lat,lon) centroids. Returns dict (lat,lon)->properties. Batched (<5000 GEE cap)."""
    res = {}
    for i in range(0, len(cells), batch):
        chunk = cells[i:i + batch]
        feats = [ee.Feature(ee.Geometry.Point([lon + GRID / 2, lat + GRID / 2]), {"clat": lat, "clon": lon})
                 for (lat, lon) in chunk]
        fc = ee.FeatureCollection(feats)
        out = image.sampleRegions(collection=fc, properties=["clat", "clon"], scale=scale,
                                  geometries=False).getInfo()
        for f in out["features"]:
            p = f["properties"]
            res[(round(p["clat"], 3), round(p["clon"], 3))] = p
    return res


def national_coupling():
    d = pd.read_excel(GIDD_DIS); d.columns = [c.strip() for c in d.columns]
    d["idp"] = pd.to_numeric(d["Disaster Internal Displacements"], errors="coerce")
    dis = d[d["Year"].between(2008, 2024)].groupby(["ISO3", "Year"])["idp"].sum()
    c = pd.read_excel(GIDD_CONF); c.columns = [x.strip() for x in c.columns]
    c["idp"] = pd.to_numeric(c["Conflict Internal Displacements"], errors="coerce")
    con = c[c["Year"].between(2008, 2024)].groupby(["ISO3", "Year"])["idp"].sum()
    out = {}
    for iso in {i for i, _ in dis.index} | {i for i, _ in con.index}:
        yrs = list(range(2008, 2025))
        av = dis.reindex([(iso, y) for y in yrs], fill_value=0).values
        bv = con.reindex([(iso, y) for y in yrs], fill_value=0).values
        if np.std(av) > 0 and np.std(bv) > 0:
            r, _ = stats.spearmanr(av, bv)
            out[iso] = None if np.isnan(r) else round(float(r), 3)
    return out


def main():
    ee.Initialize(project="app-api-489906")
    print("EE init")
    stack, dfreq, years = build_spei_images()

    print("loading UCDP-GED...")
    ged = pd.read_csv(GED, low_memory=False)
    ged = ged[(ged["year"].between(Y0, Y1))].dropna(subset=["latitude", "longitude", "best", "country_id"])
    ged["best"] = pd.to_numeric(ged["best"], errors="coerce").fillna(0)
    natl = national_coupling()

    rows = {}
    for gw, (iso, coupling) in CSET.items():
        g = ged[ged["country_id"] == gw]
        if len(g) < 30:
            print(f"  {iso}: only {len(g)} events, skip"); continue
        g = g.copy()
        g["cell"] = [cellkey(a, b) for a, b in zip(g["latitude"], g["longitude"])]
        conf_cell = g.groupby("cell")["best"].sum()
        conf_cell_year = g.groupby(["cell", "year"])["best"].sum()
        conf_cells = list(conf_cell.index)
        # extent for full-grid drought sampling
        lats = g["latitude"]; lons = g["longitude"]
        lo_lat = np.floor((lats.min() - 2) / GRID) * GRID; hi_lat = np.ceil((lats.max() + 2) / GRID) * GRID
        lo_lon = np.floor((lons.min() - 2) / GRID) * GRID; hi_lon = np.ceil((lons.max() + 2) / GRID) * GRID
        grid_cells = [(float(la), float(lo))
                      for la in np.arange(lo_lat, hi_lat, GRID)
                      for lo in np.arange(lo_lon, hi_lon, GRID)]
        # GEE pull 1: drought_freq at all grid cells (batched)
        df_dfreq = sample_points(dfreq, grid_cells)
        # GEE pull 2: annual stack at conflict cells (for H2)
        df_stack = sample_points(stack, conf_cells)

        # assemble cell table
        recs = []
        for cell, props in df_dfreq.items():
            d = props.get("dfreq")
            if d is None:
                continue
            recs.append({"cell": cell, "dfreq": d, "conf": float(conf_cell.get(cell, 0.0)),
                         "is_conf": cell in conf_cell.index})
        cdf = pd.DataFrame(recs)
        if cdf.empty or cdf["is_conf"].sum() < 5:
            print(f"  {iso}: insufficient land/conflict cells"); continue

        # H1a: Mann-Whitney drought_freq conflict vs non-conflict cells
        a = cdf.loc[cdf["is_conf"], "dfreq"]; b = cdf.loc[~cdf["is_conf"], "dfreq"]
        mw = None
        if len(a) >= 5 and len(b) >= 5 and (a.std() + b.std()) > 0:
            u, pmw = stats.mannwhitneyu(a, b, alternative="greater")
            mw = (round(float(a.median()), 2), round(float(b.median()), 2), round(float(pmw), 4))
        # H1b: Spearman conflict-intensity vs dfreq among conflict cells
        cc = cdf[cdf["is_conf"]]
        rho_h1 = None
        if len(cc) >= 8 and cc["conf"].std() > 0 and cc["dfreq"].std() > 0:
            r, p = stats.spearmanr(np.log1p(cc["conf"]), cc["dfreq"])
            rho_h1 = (round(float(r), 3), round(float(p), 4))

        # H2: within-cell conflict in drought-years vs non-drought-years
        diffs = []
        for cell in conf_cells:
            props = df_stack.get((round(cell[0], 3), round(cell[1], 3)))
            if not props:
                continue
            dyr, ndyr = [], []
            for y in years:
                spei = props.get(f"y{y}")
                if spei is None:
                    continue
                c = float(conf_cell_year.get((cell, y), 0.0))
                (dyr if spei <= DTHR else ndyr).append(c)
            if len(dyr) >= 3 and len(ndyr) >= 3:
                diffs.append(np.mean(dyr) - np.mean(ndyr))
        h2 = None
        if len(diffs) >= 8:
            diffs = np.array(diffs)
            w, pw = stats.wilcoxon(diffs) if np.any(diffs != 0) else (None, None)
            h2 = {"n_cells": len(diffs), "median_diff": round(float(np.median(diffs)), 1),
                  "frac_positive": round(float(np.mean(diffs > 0)), 3),
                  "wilcoxon_p": round(float(pw), 4) if pw is not None else None}

        rows[iso] = {"coupling": coupling, "n_events": len(g), "n_conf_cells": int(cdf["is_conf"].sum()),
                     "n_land_cells": int(len(cdf)), "mw_drought_conf_vs_non": mw,
                     "rho_h1_intensity": rho_h1, "h2": h2, "rho_national": natl.get(iso)}
        print(f"  {iso} ({'CPL' if coupling else 'ctl'}): conf_cells={cdf['is_conf'].sum()} "
              f"MW={mw} rhoH1={rho_h1} H2={h2}")

    # ---- Set B cross-country: spatial signal vs national coupling ----
    print("\n" + "=" * 80)
    pairs = []
    for iso, r in rows.items():
        # spatial signal = MW effect direction (median diff conf - nonconf), use rho_h1 r if available else MW sign
        sig = r["rho_h1_intensity"][0] if r["rho_h1_intensity"] else None
        if sig is not None and r["rho_national"] is not None:
            pairs.append((sig, r["rho_national"], iso))
    setB = None
    if len(pairs) >= 5:
        xs, ys, _ = zip(*pairs)
        rb, pb = stats.spearmanr(xs, ys)
        setB = (round(float(rb), 3), round(float(pb), 4), len(pairs))
    print(f"Set B (per-country H1 rho vs national coupling, n={len(pairs)}): {setB}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"rows": rows, "setB": setB, "grid": GRID}, indent=2, default=str), encoding="utf-8")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
