"""
Two-flow test on the UPSIDE gradient (option b): does moving toward higher
opportunity-UPSIDE (the ceiling/variance) separate dreamers from clearers,
where the mean-opportunity gradient could not (it gave only +2.8pp on age)?

upside_deficit = orig_upside - dest_upside ; <0 = moving TOWARD higher upside
(aspirational/dreamer). Compare demographic separation to the mean-split, both
on the sign split and on the extreme deciles (purest dreamers vs clearers).
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

DERIVED = Path(r"D:\Migration\data\derived")


def sep_table(asp, cle, label):
    print(f"\n--- {label} ---")
    for col, lvl in [("age_bin", "18-29"), ("family_bin", "kids"),
                     ("educ_bin", "BA+"), ("income_bin", "inc_hi")]:
        a = 100 * asp[asp[col] == lvl].PERWT.sum() / asp.PERWT.sum()
        c = 100 * cle[cle[col] == lvl].PERWT.sum() / cle.PERWT.sum()
        print(f"  {col}={lvl:<7} aspirational {a:5.1f}%  clearing {c:5.1f}%  Δ {a-c:+5.1f}")


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
    o = up.rename(columns={"statefip": "orig_state", "migpuma": "orig_migpuma",
                           "year": "YEAR", "upside_index": "orig_upside"})
    d = up.rename(columns={"statefip": "dest_state", "migpuma": "dest_migpuma",
                           "year": "YEAR", "upside_index": "dest_upside"})
    ev = ev.merge(o, on=["orig_state", "orig_migpuma", "YEAR"], how="left")
    ev = ev.merge(d, on=["dest_state", "dest_migpuma", "YEAR"], how="left")
    ev = ev.dropna(subset=["orig_upside", "dest_upside"]).copy()
    ev["upside_deficit"] = ev.orig_upside - ev.dest_upside   # <0 = toward higher upside
    print(f"events with upside on both ends: {len(ev):,}")

    # sign split on upside gradient
    asp = ev[ev.upside_deficit < 0]; cle = ev[ev.upside_deficit > 0]
    print(f"\nupside sign-split: aspirational(toward upside) {100*asp.PERWT.sum()/ev.PERWT.sum():.1f}%  "
          f"clearing {100*cle.PERWT.sum()/ev.PERWT.sum():.1f}%")
    sep_table(asp, cle, "UPSIDE sign-split demographic separation")

    # extreme deciles (purest dreamers vs purest clearers)
    lo = ev.upside_deficit.quantile(0.10); hi = ev.upside_deficit.quantile(0.90)
    pa = ev[ev.upside_deficit <= lo]; pc = ev[ev.upside_deficit >= hi]
    sep_table(pa, pc, "UPSIDE extreme-decile (purest dreamers vs clearers)")

    # reference: the mean-gradient sign split for comparison
    ma = ev[ev.opp_deficit < 0]; mc = ev[ev.opp_deficit > 0]
    sep_table(ma, mc, "MEAN-gradient sign-split (reference, was weak)")

    # do the two gradients disagree? (dreamers = toward upside but maybe not toward mean)
    ev["up_toward"] = ev.upside_deficit < 0
    ev["mean_toward"] = ev.opp_deficit < 0
    xt = pd.crosstab(ev.up_toward, ev.mean_toward, normalize=True).round(3)
    print(f"\ntoward-upside (rows) x toward-mean (cols) joint share:")
    print(xt.to_string())
    disagree = ev[(ev.up_toward) & (~ev.mean_toward)]
    print(f"\n'pure dreamer' quadrant (toward upside, NOT toward mean): {100*len(disagree)/len(ev):.1f}% of moves")
    if len(disagree):
        y = 100*disagree[disagree.age_bin=='18-29'].PERWT.sum()/disagree.PERWT.sum()
        print(f"  their young(18-29) share: {y:.1f}%  (vs ~41% overall)")


if __name__ == "__main__":
    main()
