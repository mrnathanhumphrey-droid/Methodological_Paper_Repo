"""
Build MIGPUMA x year socioeconomic aggregates (PRE_REG v1.0 §2.5 opportunity
index inputs), at MIGPUMA resolution per v1.3 amendment.

For each (statefip, migpuma, year) over in-scope persons (2012-2021, age>=18,
households), current residence mapped PUMA->MIGPUMA:
  - med_hhinc      : HHWT-weighted median HHINCOME over householders (PERNUM==1)
  - emp_pop_2554   : PERWT-weighted employment rate (EMPSTAT==1) among ages 25-54
  - ba_share       : PERWT-weighted BA+ share (EDUCD>=101) among ages 25+
  - med_rent       : HHWT-weighted median RENTGRS over renter householders
  - affordability  : med_hhinc / (12 * med_rent)   [higher = more affordable]

Output: data/derived/migpuma_socioecon_2010.parquet
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

GZ = Path(r"D:\Migration\data\raw\ipums\usa_00001.csv.gz")
CW = Path(r"D:\Migration\data\derived\puma_to_migpuma_2010.parquet")
OUT = Path(r"D:\Migration\data\derived\migpuma_socioecon_2010.parquet")
COLS = ["YEAR", "SERIAL", "PERNUM", "PERWT", "HHWT", "STATEFIP", "PUMA", "GQ",
        "AGE", "EDUCD", "HHINCOME", "EMPSTAT", "OWNERSHP", "RENTGRS"]
YEAR_MIN, YEAR_MAX = 2012, 2021
HHINCOME_NA = 9999999


def wmedian(v: np.ndarray, w: np.ndarray) -> float:
    if len(v) == 0:
        return np.nan
    o = np.argsort(v)
    v, w = v[o], w[o]
    cw = np.cumsum(w)
    return float(v[np.searchsorted(cw, 0.5 * cw[-1])])


def wmean(x: np.ndarray, w: np.ndarray) -> float:
    s = w.sum()
    return float((x * w).sum() / s) if s > 0 else np.nan


def main():
    print("loading IPUMS columns...")
    df = pd.read_csv(GZ, usecols=COLS)
    df = df[(df.YEAR >= YEAR_MIN) & (df.YEAR <= YEAR_MAX)
            & (df.AGE >= 18) & (df.GQ.isin([1, 2, 5]))].copy()
    cw = pd.read_parquet(CW).rename(columns={"statefip": "STATEFIP", "puma": "PUMA"})
    df = df.merge(cw, on=["STATEFIP", "PUMA"], how="left")
    miss = int(df.migpuma.isna().sum())
    print(f"rows in scope: {len(df):,}; unmapped to MIGPUMA: {miss:,}")
    df = df.dropna(subset=["migpuma"]).copy()
    df["migpuma"] = df.migpuma.astype(int)

    keys = ["STATEFIP", "migpuma", "YEAR"]
    hh = df[df.PERNUM == 1]
    renters = hh[(hh.OWNERSHP == 2) & (hh.RENTGRS > 0)]
    a2554 = df[(df.AGE >= 25) & (df.AGE <= 54)]
    a25 = df[df.AGE >= 25]

    print("aggregating per (state, migpuma, year)...")
    rows = []
    # iterate over the union of group keys via the householder frame (always present)
    grp_inc = {k: g for k, g in hh.groupby(keys)}
    grp_rent = {k: g for k, g in renters.groupby(keys)}
    grp_emp = {k: g for k, g in a2554.groupby(keys)}
    grp_ba = {k: g for k, g in a25.groupby(keys)}

    for k, g in grp_inc.items():
        med_inc = wmedian(g.HHINCOME.to_numpy(float), g.HHWT.to_numpy(float))
        gr = grp_rent.get(k)
        med_rent = (wmedian(gr.RENTGRS.to_numpy(float), gr.HHWT.to_numpy(float))
                    if gr is not None else np.nan)
        ge = grp_emp.get(k)
        emp = (wmean((ge.EMPSTAT == 1).to_numpy(float), ge.PERWT.to_numpy(float))
               if ge is not None else np.nan)
        gb = grp_ba.get(k)
        ba = (wmean((gb.EDUCD >= 101).to_numpy(float), gb.PERWT.to_numpy(float))
              if gb is not None else np.nan)
        afford = med_inc / (12.0 * med_rent) if med_rent and med_rent > 0 else np.nan
        rows.append((k[0], k[1], k[2], med_inc, emp, ba, med_rent, afford,
                     len(g), len(ge) if ge is not None else 0))

    out = pd.DataFrame(rows, columns=["statefip", "migpuma", "year", "med_hhinc",
                                      "emp_pop_2554", "ba_share", "med_rent",
                                      "affordability", "n_hh", "n_adults_2554"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT, index=False)

    print(f"\nrows (migpuma-year cells): {len(out):,}")
    print(f"distinct migpuma: {out.groupby(['statefip','migpuma']).ngroups}, years: {sorted(out.year.unique())}")
    print("NaN counts:", out[["med_hhinc", "emp_pop_2554", "ba_share", "affordability"]].isna().sum().to_dict())
    print("\nindicator medians (pooled):")
    print(out[["med_hhinc", "emp_pop_2554", "ba_share", "med_rent", "affordability"]].median().to_string())
    print(f"written: {OUT}")


if __name__ == "__main__":
    main()
