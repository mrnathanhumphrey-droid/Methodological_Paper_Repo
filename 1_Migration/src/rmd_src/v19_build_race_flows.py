"""
PRE_REG v1.9 build step — race-tagged corridor flows + race-specific MIGPUMA masses.

One pass over the raw IPUMS extract (8 cols) produces:
  data/derived/migpuma_population_by_race_2010.parquet  (statefip,migpuma,year,race_group,population)
  data/derived/race_corridor_flows_2010.parquet         (orig/dest state+migpuma, race_group, YEAR, flow)

Race groups collapse RACE+HISPAN (general codes):
  Hispanic     = HISPAN in {1,2,3,4} (any race)
  NH_White     = HISPAN not-Hispanic & RACE==1
  NH_Black     = ... RACE==2
  NH_AIAN      = ... RACE==3
  NH_AsianPI   = ... RACE in {4,5,6}
  NH_Other     = ... RACE in {7,8,9}    (incl two/three+ major races)
  HISPAN==9 (not reported, tiny) folded into non-Hispanic. Logged.

Reuses the locked event layer (event_observables) and the same PUMA->MIGPUMA
crosswalk + between-MIGPUMA / missing_geo filters as netfield_stageA.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

DERIVED = Path(r"D:\Migration\data\derived")
GZ = Path(r"D:\Migration\data\raw\ipums\usa_00001.csv.gz")
YEAR_MIN, YEAR_MAX = 2012, 2021


def race_group(race: pd.Series, hisp: pd.Series) -> np.ndarray:
    is_hisp = hisp.isin([1, 2, 3, 4]).to_numpy()
    r = race.to_numpy()
    out = np.empty(len(r), dtype=object)
    out[:] = "NH_Other"
    out[np.isin(r, [4, 5, 6])] = "NH_AsianPI"
    out[r == 3] = "NH_AIAN"
    out[r == 2] = "NH_Black"
    out[r == 1] = "NH_White"
    out[is_hisp] = "Hispanic"
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    cols = ["YEAR", "SERIAL", "PERNUM", "PERWT", "STATEFIP", "PUMA", "RACE", "HISPAN"]
    print("reading raw IPUMS (8 cols)...")
    df = pd.read_csv(GZ, usecols=cols)
    df = df[(df.YEAR >= YEAR_MIN) & (df.YEAR <= YEAR_MAX)].copy()
    df["race_group"] = race_group(df.RACE, df.HISPAN)
    print(f"  persons {len(df):,}")
    print("  race_group person shares:")
    for g, s in (df.groupby("race_group").PERWT.sum() / df.PERWT.sum()).sort_values(ascending=False).items():
        print(f"    {g:12s} {100*s:5.2f}%")

    # --- race-specific residence population by MIGPUMA-year ---
    cw = pd.read_parquet(DERIVED / "puma_to_migpuma_2010.parquet")
    m = df.merge(cw.rename(columns={"statefip": "STATEFIP", "puma": "PUMA"}),
                 on=["STATEFIP", "PUMA"], how="left").dropna(subset=["migpuma"])
    m["migpuma"] = m.migpuma.astype(int)
    pop = (m.groupby(["STATEFIP", "migpuma", "YEAR", "race_group"]).PERWT.sum()
           .reset_index().rename(columns={"STATEFIP": "statefip", "YEAR": "year",
                                          "PERWT": "population"}))
    pop.to_parquet(DERIVED / "migpuma_population_by_race_2010.parquet", index=False)
    print(f"\nrace-population cells (statefip,migpuma,year,race): {len(pop):,}")

    # --- race-tagged events -> per-year corridor flows ---
    ev = pd.read_parquet(DERIVED / "event_observables.parquet")
    key = df[["YEAR", "SERIAL", "PERNUM", "race_group"]]
    ev = ev.merge(key, on=["YEAR", "SERIAL", "PERNUM"], how="left")
    miss_race = int(ev.race_group.isna().sum())
    ev = ev[~ev.missing_geo & ~ev.within_migpuma & ev.race_group.notna()].copy()
    flows = (ev.groupby(["orig_state", "orig_migpuma", "dest_state", "dest_migpuma",
                         "race_group", "YEAR"]).PERWT.sum()
             .reset_index().rename(columns={"PERWT": "flow"}))
    flows["orig_state"] = flows.orig_state.astype(int)
    flows["orig_migpuma"] = flows.orig_migpuma.astype(int)
    flows["dest_state"] = flows.dest_state.astype(int)
    flows["dest_migpuma"] = flows.dest_migpuma.astype(int)
    flows.to_parquet(DERIVED / "race_corridor_flows_2010.parquet", index=False)

    print(f"events matched to race: {len(ev):,}  (unmatched race: {miss_race:,})")
    print(f"per-(corridor,race,year) rows: {len(flows):,}")
    print("\nevent (PERWT-weighted) share by race, between-MIGPUMA movers:")
    for g, s in (ev.groupby("race_group").PERWT.sum() / ev.PERWT.sum()).sort_values(ascending=False).items():
        print(f"    {g:12s} {100*s:5.2f}%")
    print(f"\nwritten:\n  {DERIVED/'migpuma_population_by_race_2010.parquet'}\n  {DERIVED/'race_corridor_flows_2010.parquet'}")


if __name__ == "__main__":
    main()
