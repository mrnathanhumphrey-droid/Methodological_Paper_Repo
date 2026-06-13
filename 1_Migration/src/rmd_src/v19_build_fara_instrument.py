"""
PRE_REG v1.9 instrument (FARA arm) — low-access population share per origin MIGPUMA.

Income-free structural-distance measure (NOT the LILA whitelist):
    fara_lowaccess_share = sum(LAPOP1_10) / sum(Pop2010)   over tracts in MIGPUMA
LAPOP1_10 = population beyond 1 mi (urban) / 10 mi (rural) from a supermarket.

Crosswalk: FARA 2010 tract GEOID -> 2010 PUMA (Census rel file) -> MIGPUMA (locked cw).
FARA read straight from the Food Deserts zip (provenance). National coverage.

Output: data/derived/migpuma_fara_2010.parquet
"""
from __future__ import annotations
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd

DERIVED = Path(r"D:\Migration\data\derived")
FARA_ZIP = Path(r"D:\Food Deserts\data_raw\FARA\2019_Food_Access_Research_Atlas_Data.zip")
TRACT_PUMA = Path(r"D:\Migration\data\raw\crosswalks\2010_Census_Tract_to_2010_PUMA.txt")


def main():
    with zipfile.ZipFile(FARA_ZIP) as z:
        with z.open("Food Access Research Atlas.csv") as f:
            fara = pd.read_csv(f, usecols=["CensusTract", "Pop2010", "LAPOP1_10", "lapophalf"],
                               dtype={"CensusTract": str})
    fara["geoid"] = fara.CensusTract.str.zfill(11)
    for c in ["Pop2010", "LAPOP1_10", "lapophalf"]:
        fara[c] = pd.to_numeric(fara[c], errors="coerce").fillna(0.0)
    print(f"FARA tracts: {len(fara):,}")

    xw = pd.read_csv(TRACT_PUMA, dtype=str)
    xw["geoid"] = xw.STATEFP.str.zfill(2) + xw.COUNTYFP.str.zfill(3) + xw.TRACTCE.str.zfill(6)
    xw["statefip"] = xw.STATEFP.astype(int)
    xw["puma"] = xw.PUMA5CE.astype(int)

    m = fara.merge(xw[["geoid", "statefip", "puma"]], on="geoid", how="left")
    miss = int(m.statefip.isna().sum())
    m = m.dropna(subset=["statefip"]).copy()
    m["statefip"] = m.statefip.astype(int); m["puma"] = m.puma.astype(int)

    cw = pd.read_parquet(DERIVED / "puma_to_migpuma_2010.parquet")
    m = m.merge(cw, on=["statefip", "puma"], how="left").dropna(subset=["migpuma"])
    m["migpuma"] = m.migpuma.astype(int)

    agg = (m.groupby(["statefip", "migpuma"])
           .agg(pop=("Pop2010", "sum"), la1_10=("LAPOP1_10", "sum"), lahalf=("lapophalf", "sum"))
           .reset_index())
    agg = agg[agg["pop"] > 0].copy()
    agg["fara_lowaccess_share"] = agg.la1_10 / agg["pop"]
    agg["fara_lowaccesshalf_share"] = agg.lahalf / agg["pop"]
    agg.to_parquet(DERIVED / "migpuma_fara_2010.parquet", index=False)

    print(f"FARA tracts unmatched to PUMA: {miss:,}")
    print(f"MIGPUMAs with FARA: {len(agg):,} of {cw.groupby(['statefip','migpuma']).ngroups:,}")
    print(f"fara_lowaccess_share (1mi/10mi): mean {agg.fara_lowaccess_share.mean():.3f}  "
          f"median {agg.fara_lowaccess_share.median():.3f}  [{agg.fara_lowaccess_share.min():.3f}, {agg.fara_lowaccess_share.max():.3f}]")
    print(f"written: {DERIVED / 'migpuma_fara_2010.parquet'}")


if __name__ == "__main__":
    main()
