"""
PRE_REG_037 pull: SPEI v2.10 spatially-resolved drought metrics over ETH/SOM/BRA
via GEE. Per year/box/band: area-fraction of land in drought (SPEI <= -0.8/-1.0/-1.5)
+ areal 10th-percentile SPEI. December images, 1950-2023.

frac_drought = mean of (spei<=thr) over land-masked pixels = fraction of region land
area in moderate+ drought (the spatial metric that doesn't dilute concentrated drought).

Usage: python paper8_gee_spei210_spatial_pull.py app-api-489906
"""
from __future__ import annotations
import os, sys
from pathlib import Path
import pandas as pd
import ee

OUT = Path("D:/IDP/data/spei/spei210_spatial_ETH_SOM_BRA_1950_2023.csv")
BOXES = {"ETH": [33, 3, 48, 15], "SOM": [41, -2, 51, 12], "BRA": [-73, -12, -50, 5]}
BANDS = {"SPEI_12_month": "12", "SPEI_03_month": "03"}
THRS = {"f08": -0.8, "f10": -1.0, "f15": -1.5}
SCALE = 55660
Y0, Y1 = 1950, 2023


def main():
    project = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("EE_PROJECT", "")).strip()
    ee.Initialize(project=project)
    print(f"EE init (project={project})")
    boxes = {k: ee.Geometry.Rectangle(v) for k, v in BOXES.items()}
    coll = ee.ImageCollection("CSIC/SPEI/2_10")
    years = ee.List.sequence(Y0, Y1)

    def per_year(y):
        y = ee.Number(y)
        start = ee.Date.fromYMD(y, 12, 1)
        img = coll.filterDate(start, start.advance(1, "month")).first()
        props = {"year": y}
        for band, short in BANDS.items():
            b = ee.Image(img).select(band)
            b = b.updateMask(b.abs().lt(10))  # land only
            for rg, g in boxes.items():
                for fkey, thr in THRS.items():
                    fd = b.lte(thr).reduceRegion(ee.Reducer.mean(), g, SCALE, maxPixels=1e9)
                    props[f"{rg}_{short}_{fkey}"] = ee.Dictionary(fd).values().get(0)
                pd_ = b.reduceRegion(ee.Reducer.percentile([10]), g, SCALE, maxPixels=1e9)
                props[f"{rg}_{short}_p10"] = ee.Dictionary(pd_).values().get(0)
        return ee.Feature(None, props)

    fc = ee.FeatureCollection(years.map(per_year))
    print("getInfo (server-side: 74 yrs x 3 boxes x 2 bands x [3 frac + p10])...")
    info = fc.getInfo()
    df = pd.DataFrame([f["properties"] for f in info["features"]]).sort_values("year").reset_index(drop=True)
    front = ["year"]
    rest = [c for c in df.columns if c != "year"]
    df = df[front + sorted(rest)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Saved {len(df)} rows -> {OUT}\n")
    # show Horn frac_drought (f10) + recent years to check 2020-22 registers
    cols = ["year", "ETH_12_f10", "SOM_12_f10", "BRA_12_f10", "ETH_03_f10", "SOM_03_f10", "BRA_03_f10"]
    print(df[cols].tail(12).to_string(index=False))


if __name__ == "__main__":
    main()
