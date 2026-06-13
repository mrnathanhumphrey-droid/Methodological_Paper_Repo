"""
Two-flow exploratory remeasurement (post-theory): split migration into
  ASPIRATIONAL (up-gradient, opp_deficit<0 -> toward higher opportunity)
  CLEARING     (down-gradient, opp_deficit>0 -> toward availability/affordability)
and characterize each separately. Clean non-circular test = do the two flows
differ DEMOGRAPHICALLY as theory predicts (dreamers young/childless vs
clearers older/with-kids)?

Exploratory (discovery), not a locked falsification. Read-only.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

DERIVED = Path(r"D:\Migration\data\derived")


def comp(d, col, w):
    t = d.groupby(col).apply(lambda g: g[w].sum(), include_groups=False)
    return (t / t.sum() * 100).round(1)


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

    ev["flow"] = np.where(ev.opp_deficit < 0, "ASPIRATIONAL(up)",
                          np.where(ev.opp_deficit > 0, "CLEARING(down)", "lateral"))

    tot = ev.PERWT.sum()
    print("=== two-flow split (weighted) ===")
    for f, g in ev.groupby("flow"):
        print(f"  {f:<18} {100*g.PERWT.sum()/tot:5.1f}%   n_events={len(g):>8,}   "
              f"mean dist_km={np.expm1(g.log_distance).mean():>6.0f}   "
              f"mean dest_density={np.exp(g.log_dest_density).mean():>7.0f}")

    asp = ev[ev.flow == "ASPIRATIONAL(up)"]; cle = ev[ev.flow == "CLEARING(down)"]
    print("\n=== DEMOGRAPHIC composition (clean non-circular test) ===")
    for col in ["age_bin", "income_bin", "family_bin", "educ_bin"]:
        print(f"\n{col}:")
        a = comp(asp, col, "PERWT"); c = comp(cle, col, "PERWT")
        idx = sorted(set(a.index) | set(c.index), key=str)
        print(f"  {'level':<10} {'ASPIRATIONAL':>13} {'CLEARING':>10}   delta(A-C)")
        for k in idx:
            av = a.get(k, 0.0); cv = c.get(k, 0.0)
            print(f"  {str(k):<10} {av:>12.1f}% {cv:>9.1f}%   {av-cv:+6.1f}")

    # headline predictions
    print("\n=== theory checks ===")
    yng = lambda d: 100*d[d.age_bin=='18-29'].PERWT.sum()/d.PERWT.sum()
    kids = lambda d: 100*d[d.family_bin=='kids'].PERWT.sum()/d.PERWT.sum()
    print(f"  young (18-29):   aspirational {yng(asp):.1f}%  vs clearing {yng(cle):.1f}%  "
          f"(theory: dreamers younger)")
    print(f"  with-kids:       aspirational {kids(asp):.1f}%  vs clearing {kids(cle):.1f}%  "
          f"(theory: clearers more families)")


if __name__ == "__main__":
    main()
