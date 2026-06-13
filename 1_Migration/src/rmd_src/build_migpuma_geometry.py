"""
Build MIGPUMA (2010-vintage) geometry table: centroid lon/lat + land area.

For each (statefip, migpuma):
  - centroid = ALAND-weighted mean of component PUMA internal points
    (TIGER INTPTLON10/INTPTLAT10); projection-free, robust for AK/HI/PR.
  - land_km2 = sum of component PUMA ALAND10 (Census official land area).

Source: data/raw/tiger/puma_2010/*.zip  +  data/derived/puma_to_migpuma_2010.parquet
Output: data/derived/migpuma_geometry_2010.parquet
  cols: statefip, migpuma, lon, lat, land_km2, n_pumas
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd

PUMA_DIR = Path(r"D:\Migration\data\raw\tiger\puma_2010")
CW = Path(r"D:\Migration\data\derived\puma_to_migpuma_2010.parquet")
OUT = Path(r"D:\Migration\data\derived\migpuma_geometry_2010.parquet")


def main():
    zips = sorted(PUMA_DIR.glob("tl_2019_*_puma10.zip"))
    print(f"reading {len(zips)} PUMA shapefiles...")
    frames = []
    for z in zips:
        g = gpd.read_file(z, columns=["STATEFP10", "PUMACE10", "ALAND10",
                                      "INTPTLON10", "INTPTLAT10"])
        frames.append(pd.DataFrame({
            "statefip": g.STATEFP10.astype(int),
            "puma": g.PUMACE10.astype(int),
            "aland": g.ALAND10.astype(float),
            "lon": g.INTPTLON10.astype(float),
            "lat": g.INTPTLAT10.astype(float),
        }))
    pumas = pd.concat(frames, ignore_index=True)
    print(f"total PUMAs from shapefiles: {len(pumas)}")

    cw = pd.read_parquet(CW)
    m = pumas.merge(cw, on=["statefip", "puma"], how="left")
    unmatched = int(m.migpuma.isna().sum())
    if unmatched:
        print(f"WARN: {unmatched} PUMAs not in crosswalk:")
        print(m[m.migpuma.isna()][["statefip", "puma"]].to_string())
    m = m.dropna(subset=["migpuma"]).copy()
    m["migpuma"] = m.migpuma.astype(int)
    m["w"] = m.aland.clip(lower=1.0)  # all-water PUMAs get tiny weight, not zero

    def agg(d):
        return pd.Series({
            "lon": np.average(d.lon, weights=d.w),
            "lat": np.average(d.lat, weights=d.w),
            "land_km2": d.aland.sum() / 1e6,
            "n_pumas": len(d),
        })

    geo = m.groupby(["statefip", "migpuma"], as_index=False).apply(
        agg, include_groups=False)
    geo["n_pumas"] = geo.n_pumas.astype(int)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    geo.to_parquet(OUT, index=False)

    print(f"\nMIGPUMAs: {len(geo)}")
    print(f"lon range: [{geo.lon.min():.2f}, {geo.lon.max():.2f}]  "
          f"lat range: [{geo.lat.min():.2f}, {geo.lat.max():.2f}]")
    print(f"land_km2: median {geo.land_km2.median():,.0f}, "
          f"min {geo.land_km2.min():,.0f}, max {geo.land_km2.max():,.0f}")
    print(f"PUMAs per MIGPUMA: mean {geo.n_pumas.mean():.2f}, max {geo.n_pumas.max()}")
    print(f"written: {OUT}")


if __name__ == "__main__":
    main()
