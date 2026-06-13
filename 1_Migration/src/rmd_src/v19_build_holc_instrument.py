"""
PRE_REG v1.9 instrument — HOLC redline share per origin MIGPUMA (2010 vintage).

HOLC areas (Mapping Inequality, graded 1930s) carry real polygon geometry, so we
spatially join each graded piece to its 2010 PUMA polygon (no tract crosswalk
needed), roll PUMA -> MIGPUMA via the locked crosswalk, and compute the
area-weighted redline share among graded area:
    redline_D_share  = area(D) / area(A+B+C+D)
    redline_CD_share = area(C+D) / area(A+B+C+D)
MIGPUMAs with no HOLC coverage are absent (HOLC arm is restricted to graded origins).

Output: data/derived/migpuma_holc_2010.parquet
"""
from __future__ import annotations
from pathlib import Path
import glob
import numpy as np
import pandas as pd
import geopandas as gpd

DERIVED = Path(r"D:\Migration\data\derived")
HOLC = Path(r"D:\Food Deserts\data_raw\HOLC\MIv3Areas_2010TractCrosswalk.geojson")
PUMA_DIR = Path(r"D:\Migration\data\raw\tiger\puma_2010")


def main():
    holc = gpd.read_file(HOLC)
    holc["grade"] = holc.grade.astype(str).str.strip().str.upper()
    holc = holc[holc.grade.isin(["A", "B", "C", "D"])].copy()
    holc = holc[holc.geometry.notna() & (holc.calc_area > 0)].copy()
    holc = holc.to_crs(4326)
    # representative point guaranteed inside the piece polygon
    pts = holc.copy()
    pts["geometry"] = holc.geometry.representative_point()
    print(f"HOLC graded pieces: {len(holc):,}")

    # all 2010 PUMA polygons
    frames = []
    for z in sorted(glob.glob(str(PUMA_DIR / "tl_2019_*_puma10.zip"))):
        p = gpd.read_file(z)[["STATEFP10", "PUMACE10", "geometry"]]
        frames.append(p)
    puma = pd.concat(frames, ignore_index=True)
    puma = gpd.GeoDataFrame(puma, geometry="geometry", crs=frames[0].crs).to_crs(4326)
    puma["statefip"] = puma.STATEFP10.astype(int)
    puma["puma"] = puma.PUMACE10.astype(int)
    print(f"2010 PUMA polygons: {len(puma):,}")

    j = gpd.sjoin(pts, puma[["statefip", "puma", "geometry"]], how="left", predicate="within")
    miss = int(j.statefip.isna().sum())
    j = j.dropna(subset=["statefip"]).copy()
    j["statefip"] = j.statefip.astype(int)
    j["puma"] = j.puma.astype(int)
    print(f"HOLC pieces matched to a PUMA: {len(j):,}  (unmatched: {miss:,})")

    cw = pd.read_parquet(DERIVED / "puma_to_migpuma_2010.parquet")
    j = j.merge(cw, on=["statefip", "puma"], how="left").dropna(subset=["migpuma"])
    j["migpuma"] = j.migpuma.astype(int)

    area = (j.pivot_table(index=["statefip", "migpuma"], columns="grade",
                          values="calc_area", aggfunc="sum", fill_value=0.0)
            .reset_index())
    for g in ["A", "B", "C", "D"]:
        if g not in area.columns:
            area[g] = 0.0
    area["graded_area"] = area[["A", "B", "C", "D"]].sum(axis=1)
    area = area[area.graded_area > 0].copy()
    area["redline_D_share"] = area.D / area.graded_area
    area["redline_CD_share"] = (area.C + area.D) / area.graded_area
    out = area[["statefip", "migpuma", "graded_area", "A", "B", "C", "D",
                "redline_D_share", "redline_CD_share"]].copy()
    out.to_parquet(DERIVED / "migpuma_holc_2010.parquet", index=False)

    cwn = cw.groupby("statefip").ngroups
    print(f"\nMIGPUMAs with HOLC coverage: {len(out):,}  of {cw.groupby(['statefip','migpuma']).ngroups:,} total")
    print(f"redline_D_share : mean {out.redline_D_share.mean():.3f}  median {out.redline_D_share.median():.3f}  "
          f"[{out.redline_D_share.min():.3f}, {out.redline_D_share.max():.3f}]")
    print(f"redline_CD_share: mean {out.redline_CD_share.mean():.3f}  median {out.redline_CD_share.median():.3f}")
    print(f"\nwritten: {DERIVED / 'migpuma_holc_2010.parquet'}")


if __name__ == "__main__":
    main()
