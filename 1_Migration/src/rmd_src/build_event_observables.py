"""
Step-1 prep: attach the three observables to each cross-PUMA migration event.

Observables (PRE_REG v1.0 §2.5, MIGPUMA resolution per v1.3):
  - log_distance       : log1p great-circle km between origin & destination
                         MIGPUMA centroids (log1p handles within-MIGPUMA = 0)
  - log_dest_density   : log destination-MIGPUMA population density (persons/km2)
  - opp_deficit        : origin opportunity_index - destination opportunity_index
                         (v1.3 "origin minus destination"; both stored too)

Also computes MIGPUMA total population per year (all ages, all GQ) for density.

Inputs:
  data/derived/P0_partition.parquet            (events via is_event + cell_id)
  data/derived/puma_to_migpuma_2010.parquet    (dest PUMA -> MIGPUMA)
  data/derived/migpuma_geometry_2010.parquet   (centroids + land_km2)
  data/derived/migpuma_opportunity_2010.parquet(opportunity_index by year)
  data/raw/ipums/usa_00001.csv.gz              (population pass, all ages)

Output:
  data/derived/migpuma_population_2010.parquet
  data/derived/event_observables.parquet
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

DERIVED = Path(r"D:\Migration\data\derived")
GZ = Path(r"D:\Migration\data\raw\ipums\usa_00001.csv.gz")
YEAR_MIN, YEAR_MAX = 2012, 2021


def haversine_km(lon1, lat1, lon2, lat2):
    R = 6371.0088
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def build_population():
    print("population pass (all ages, all GQ)...")
    pop_cols = ["YEAR", "STATEFIP", "PUMA", "PERWT"]
    df = pd.read_csv(GZ, usecols=pop_cols)
    df = df[(df.YEAR >= YEAR_MIN) & (df.YEAR <= YEAR_MAX)]
    cw = pd.read_parquet(DERIVED / "puma_to_migpuma_2010.parquet").rename(
        columns={"statefip": "STATEFIP", "puma": "PUMA"})
    df = df.merge(cw, on=["STATEFIP", "PUMA"], how="left").dropna(subset=["migpuma"])
    df["migpuma"] = df.migpuma.astype(int)
    pop = (df.groupby(["STATEFIP", "migpuma", "YEAR"]).PERWT.sum()
           .reset_index().rename(columns={"STATEFIP": "statefip", "YEAR": "year",
                                           "PERWT": "population"}))
    pop.to_parquet(DERIVED / "migpuma_population_2010.parquet", index=False)
    print(f"  population cells: {len(pop):,}")
    return pop


def main():
    p0 = pd.read_parquet(DERIVED / "P0_partition.parquet")
    ev = p0[p0.is_event].copy()
    print(f"events: {len(ev):,}")

    cw = pd.read_parquet(DERIVED / "puma_to_migpuma_2010.parquet")
    geo = pd.read_parquet(DERIVED / "migpuma_geometry_2010.parquet")
    opp = pd.read_parquet(DERIVED / "migpuma_opportunity_2010.parquet")
    pop = build_population()

    # destination MIGPUMA from (STATEFIP, PUMA)
    ev = ev.merge(cw.rename(columns={"statefip": "STATEFIP", "puma": "PUMA",
                                     "migpuma": "dest_migpuma"}),
                  on=["STATEFIP", "PUMA"], how="left")
    ev["dest_state"] = ev.STATEFIP
    # origin MIGPUMA directly from IPUMS
    ev["orig_state"] = ev.MIGPLAC1
    ev["orig_migpuma"] = ev.MIGPUMA1

    miss_dest = int(ev.dest_migpuma.isna().sum())

    # centroids
    g = geo.rename(columns={"statefip": "s", "migpuma": "m"})
    cent = g.set_index(["s", "m"])[["lon", "lat", "land_km2"]]
    for who in ["orig", "dest"]:
        c = cent.rename(columns={"lon": f"{who}_lon", "lat": f"{who}_lat",
                                 "land_km2": f"{who}_land_km2"})
        ev = ev.merge(c, left_on=[f"{who}_state", f"{who}_migpuma"],
                      right_index=True, how="left")

    # population (destination) by year
    ev = ev.merge(pop.rename(columns={"statefip": "dest_state", "migpuma": "dest_migpuma",
                                      "year": "YEAR", "population": "dest_pop"}),
                  on=["dest_state", "dest_migpuma", "YEAR"], how="left")

    # opportunity index for origin & dest by year
    o = opp.rename(columns={"statefip": "orig_state", "migpuma": "orig_migpuma",
                            "year": "YEAR", "opportunity_index": "orig_opp"})
    ev = ev.merge(o, on=["orig_state", "orig_migpuma", "YEAR"], how="left")
    d = opp.rename(columns={"statefip": "dest_state", "migpuma": "dest_migpuma",
                            "year": "YEAR", "opportunity_index": "dest_opp"})
    ev = ev.merge(d, on=["dest_state", "dest_migpuma", "YEAR"], how="left")

    # observables
    ev["distance_km"] = haversine_km(ev.orig_lon, ev.orig_lat, ev.dest_lon, ev.dest_lat)
    ev["log_distance"] = np.log1p(ev.distance_km)
    ev["dest_density"] = ev.dest_pop / ev.dest_land_km2
    ev["log_dest_density"] = np.log(ev.dest_density)
    ev["opp_deficit"] = ev.orig_opp - ev.dest_opp

    # flags
    ev["within_migpuma"] = (ev.orig_state == ev.dest_state) & (ev.orig_migpuma == ev.dest_migpuma)
    ev["missing_geo"] = ev.orig_lon.isna() | ev.dest_lon.isna()
    ev["missing_opp"] = ev.orig_opp.isna() | ev.dest_opp.isna()

    keep = ["YEAR", "SERIAL", "PERNUM", "PERWT", "cell_id",
            "orig_state", "orig_migpuma", "dest_state", "dest_migpuma",
            "distance_km", "log_distance", "dest_density", "log_dest_density",
            "orig_opp", "dest_opp", "opp_deficit",
            "within_migpuma", "missing_geo", "missing_opp"]
    out = ev[keep].copy()
    out.to_parquet(DERIVED / "event_observables.parquet", index=False)

    n = len(out)
    print(f"\n=== event observables QA (n={n:,}) ===")
    print(f"missing dest_migpuma (PUMA not in crosswalk): {miss_dest:,}")
    print(f"missing_geo (orig/dest centroid absent):      {int(out.missing_geo.sum()):,}  ({100*out.missing_geo.mean():.3f}%)")
    print(f"missing_opp (orig/dest opportunity absent):   {int(out.missing_opp.sum()):,}  ({100*out.missing_opp.mean():.3f}%)")
    print(f"within_migpuma (cross-PUMA, same MIGPUMA):    {int(out.within_migpuma.sum()):,}  ({100*out.within_migpuma.mean():.2f}%)")
    clean = out[~out.missing_geo & ~out.missing_opp]
    print(f"fully-observed events:                        {len(clean):,}  ({100*len(clean)/n:.2f}%)")
    print(f"\ndistance_km: median {clean.distance_km.median():,.0f}, "
          f"p10 {clean.distance_km.quantile(.1):,.0f}, p90 {clean.distance_km.quantile(.9):,.0f}")
    print(f"dest_density (/km2): median {clean.dest_density.median():,.1f}")
    print(f"opp_deficit (orig-dest): mean {clean.opp_deficit.mean():+.3f}, median {clean.opp_deficit.median():+.3f}")
    print(f"  (negative = moved to higher opportunity; index oriented higher=better)")
    print(f"\nwritten: {DERIVED / 'event_observables.parquet'}")


if __name__ == "__main__":
    main()
