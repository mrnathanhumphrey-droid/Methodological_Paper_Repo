"""
Pull SPEIbase v2.10 (CSIC/SPEI/2_10) December area-means over ETH/SOM/BRA
for PRE_REG_036 (P8-F), via the Earth Engine Python API. Server-side reduce,
one getInfo, writes a small CSV. Covers 1901-2023 -> includes the 2017-2023
Horn-drought events the displacement test (PRE_REG_034) used.

Usage:  python paper8_gee_spei210_pull.py <EE_PROJECT_ID>
        (or set env EE_PROJECT)
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

import pandas as pd
import ee

OUT = Path("D:/IDP/data/spei/spei210_dec_ETH_SOM_BRA_1950_2023.csv")

# bbox = [west, south, east, north]
BOXES = {
    "ETH": [33, 3, 48, 15],
    "SOM": [41, -2, 51, 12],
    "BRA": [-73, -12, -50, 5],   # Amazon basin
}
BANDS = ["SPEI_12_month", "SPEI_03_month"]  # 12 = locked primary, 03 = OND short-rains secondary
SCALE = 55660  # ~0.5 deg native grid
Y0, Y1 = 1950, 2023


def main():
    project = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("EE_PROJECT", "")).strip()
    if not project:
        print("ERROR: need EE project id as argv[1] or env EE_PROJECT"); sys.exit(2)
    ee.Initialize(project=project)
    print(f"EE initialized (project={project})")

    boxes = {k: ee.Geometry.Rectangle(v) for k, v in BOXES.items()}
    coll = ee.ImageCollection("CSIC/SPEI/2_10")
    years = ee.List.sequence(Y0, Y1)

    def per_year(y):
        y = ee.Number(y)
        start = ee.Date.fromYMD(y, 12, 1)
        img = coll.filterDate(start, start.advance(1, "month")).first()
        # defensive: drop land/no-data sentinel (1e30) and any out-of-range leakage
        props = {"year": y}
        for band in BANDS:
            b = ee.Image(img).select(band)
            b = b.updateMask(b.abs().lt(10))
            for name, g in boxes.items():
                val = b.reduceRegion(reducer=ee.Reducer.mean(), geometry=g,
                                     scale=SCALE, maxPixels=1e9).get(band)
                short = band.split("_")[1]  # '12' or '03'
                props[f"{name}_{short}"] = val
        return ee.Feature(None, props)

    fc = ee.FeatureCollection(years.map(per_year))
    print("requesting getInfo (server-side reduce over 74 years x 3 boxes x 2 bands)...")
    info = fc.getInfo()

    rows = []
    for feat in info["features"]:
        rows.append(feat["properties"])
    df = pd.DataFrame(rows).sort_values("year").reset_index(drop=True)
    # order columns
    cols = ["year"] + [f"{c}_{b}" for b in ("12", "03") for c in ("ETH", "SOM", "BRA")]
    df = df[[c for c in cols if c in df.columns]]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"\nSaved {len(df)} rows -> {OUT}")
    print(df.head(8).to_string(index=False))
    print("...")
    print(df.tail(8).to_string(index=False))
    # quick sanity: min SPEI per region (drought depth)
    for c in df.columns:
        if c != "year":
            print(f"  {c}: min={df[c].min():.2f} median={df[c].median():.2f} n={df[c].notna().sum()}")


if __name__ == "__main__":
    main()
