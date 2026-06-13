"""
Full migration flow taxonomy (discovery): two pull-moments + one push-axis.

Pull (opportunity moments):
  tmean = opp_deficit < 0      -> toward higher MEAN opportunity (center mass)
  tup   = upside_deficit < 0   -> toward higher UPSIDE (variance/ceiling)
  quadrants: DREAMER (hi-sigma,lo-mu) / STABILITY (hi-mu,lo-sigma) /
             BOTH (up both) / NEITHER (down both)
Push (displacement):
  origin rent-burden = 12*median_rent / median_hhinc at ORIGIN MIGPUMA-year.
  Within NEITHER (down both, no opportunity target), high origin rent-burden =
  DESPERATION (pushed out, displaced); low = CLEARING (left with agency).

The desperation flow is the migration-observable precursor of the homelessness
substrate (SDP): same rent-displacement funnel. Movers who don't land are the
SDP inflow (not observable here; cross-substrate bridge).

Read-only discovery. Output: results/flow_taxonomy.parquet
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

DERIVED = Path(r"D:\Migration\data\derived")
RESULTS = Path(r"D:\Migration\results")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ev = pd.read_parquet(DERIVED / "event_observables.parquet")
    ev = ev[~ev.missing_geo & ~ev.missing_opp].copy()
    p0 = pd.read_parquet(DERIVED / "P0_partition.parquet")[
        ["YEAR", "SERIAL", "PERNUM", "age_bin", "income_bin", "family_bin", "educ_bin"]]
    ev = ev.merge(p0, on=["YEAR", "SERIAL", "PERNUM"], how="left")

    up = pd.read_parquet(DERIVED / "migpuma_upside_2010.parquet")[
        ["statefip", "migpuma", "year", "upside_index"]]
    ev = ev.merge(up.rename(columns={"statefip": "orig_state", "migpuma": "orig_migpuma",
                                     "year": "YEAR", "upside_index": "ou"}),
                  on=["orig_state", "orig_migpuma", "YEAR"], how="left")
    ev = ev.merge(up.rename(columns={"statefip": "dest_state", "migpuma": "dest_migpuma",
                                     "year": "YEAR", "upside_index": "du"}),
                  on=["dest_state", "dest_migpuma", "YEAR"], how="left")

    # origin rent-burden = 12*med_rent / med_hhinc  (push axis)
    soc = pd.read_parquet(DERIVED / "migpuma_socioecon_2010.parquet")
    soc["rent_burden"] = 12.0 * soc.med_rent / soc.med_hhinc
    ev = ev.merge(soc[["statefip", "migpuma", "year", "rent_burden"]].rename(
        columns={"statefip": "orig_state", "migpuma": "orig_migpuma", "year": "YEAR",
                 "rent_burden": "orig_rent_burden"}),
        on=["orig_state", "orig_migpuma", "YEAR"], how="left")

    ev = ev.dropna(subset=["ou", "du", "orig_rent_burden"]).copy()
    ev["tmean"] = ev.opp_deficit < 0
    ev["tup"] = (ev.ou - ev.du) < 0

    # push threshold: top tercile of origin rent-burden (pooled)
    hi = ev.orig_rent_burden.quantile(2/3)

    def flow(r):
        if r.tup and not r.tmean: return "1 DREAMER"
        if r.tmean and not r.tup:  return "2 STABILITY"
        if r.tmean and r.tup:      return "3 BOTH(up)"
        # NEITHER (down both) -> split by push
        return "5 DESPERATION" if r.orig_rent_burden >= hi else "4 CLEARING"

    ev["flow"] = ev.apply(flow, axis=1)
    ev[["YEAR", "SERIAL", "PERNUM", "PERWT", "flow", "opp_deficit",
        "orig_rent_burden"]].to_parquet(RESULTS / "flow_taxonomy.parquet", index=False)

    tot = ev.PERWT.sum()
    print(f"origin rent-burden top-tercile threshold: {hi:.3f}  (rent = {100*hi:.0f}% of income)\n")
    print(f"{'flow':<16}{'share':>7}{'young':>7}{'kids':>7}{'BA+':>7}{'inc_lo':>7}{'o_rentburden':>13}{'d_dens':>8}")
    for f, g in ev.groupby("flow"):
        w = g.PERWT.sum()
        def pct(col, lvl): return 100 * g[g[col] == lvl].PERWT.sum() / w
        print(f"{f:<16}{100*w/tot:6.1f}%{pct('age_bin','18-29'):6.1f}%{pct('family_bin','kids'):6.1f}%"
              f"{pct('educ_bin','BA+'):6.1f}%{pct('income_bin','inc_lo'):6.1f}%"
              f"{g.orig_rent_burden.mean():12.3f}{np.exp(g.log_dest_density).mean():8.0f}")

    print("\n--- CLEARING vs DESPERATION (the Q4 split, the SDP seam) ---")
    cl = ev[ev.flow == "4 CLEARING"]; de = ev[ev.flow == "5 DESPERATION"]
    for col, lvl, lab in [("income_bin", "inc_lo", "low-income"),
                          ("age_bin", "18-29", "young"),
                          ("family_bin", "kids", "with-kids"),
                          ("educ_bin", "<BA", "less-than-BA")]:
        c = 100*cl[cl[col]==lvl].PERWT.sum()/cl.PERWT.sum()
        d = 100*de[de[col]==lvl].PERWT.sum()/de.PERWT.sum()
        print(f"  {lab:<13} clearing {c:5.1f}%   desperation {d:5.1f}%   Δ {d-c:+5.1f}")
    print(f"  origin rent-burden: clearing {cl.orig_rent_burden.mean():.3f}  "
          f"desperation {de.orig_rent_burden.mean():.3f}")


if __name__ == "__main__":
    main()
