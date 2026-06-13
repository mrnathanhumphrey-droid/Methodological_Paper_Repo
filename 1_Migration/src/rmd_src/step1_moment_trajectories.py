"""
RMD-SRC Step 1 — per-cell moment-flow computation (PRE_REG §3.2).

For each (species cell_id, observable, year) compute the PERWT-weighted
mean μ and weighted variance σ² over the cross-PUMA events in that cell-year.
Observables: log_distance, log_dest_density, opp_deficit.

No regime classification here (that is Step 2). Output saved for Step 2.

Output: results/moment_trajectories.parquet
  cols: cell_id, observable, year, mu, var, n, sumw
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

DERIVED = Path(r"D:\Migration\data\derived")
RESULTS = Path(r"D:\Migration\results")
OBSERVABLES = ["log_distance", "log_dest_density", "opp_deficit"]
MIN_CELL = 50  # PRE_REG §2.8 estimation floor per (cell, time bin)


def wmean_wvar(x: np.ndarray, w: np.ndarray):
    sw = w.sum()
    mu = (x * w).sum() / sw
    var = (w * (x - mu) ** 2).sum() / sw
    return mu, var, sw


def main():
    ev = pd.read_parquet(DERIVED / "event_observables.parquet")
    print(f"events loaded: {len(ev):,}")

    rows = []
    for obs in OBSERVABLES:
        sub = ev[["cell_id", "YEAR", "PERWT", obs]].copy()
        # observable-specific validity (drops the 0.39% missing geo/opp rows)
        sub = sub[np.isfinite(sub[obs])]
        for (cid, yr), g in sub.groupby(["cell_id", "YEAR"]):
            mu, var, sw = wmean_wvar(g[obs].to_numpy(float), g.PERWT.to_numpy(float))
            rows.append((cid, obs, int(yr), mu, var, len(g), float(sw)))

    traj = pd.DataFrame(rows, columns=["cell_id", "observable", "year",
                                       "mu", "var", "n", "sumw"])
    RESULTS.mkdir(parents=True, exist_ok=True)
    traj.to_parquet(RESULTS / "moment_trajectories.parquet", index=False)

    n_cells = traj.cell_id.nunique()
    n_years = traj.year.nunique()
    expected = n_cells * len(OBSERVABLES) * n_years
    below = traj[traj.n < MIN_CELL]
    print(f"\ntrajectory rows: {len(traj):,}  (expected {n_cells}×{len(OBSERVABLES)}×{n_years} = {expected})")
    print(f"cells: {n_cells}, observables: {len(OBSERVABLES)}, years: {sorted(traj.year.unique())}")
    print(f"(cell,obs,year) below n={MIN_CELL} floor: {len(below)}")
    if len(below):
        print(below.to_string())
    print(f"min n across all cell-obs-years: {traj.n.min()}")

    # show one species' full trajectory across observables as a sanity check
    sample = traj.cell_id.iloc[0]
    print(f"\nsample trajectory — {sample}:")
    piv = traj[traj.cell_id == sample].pivot_table(index="year", columns="observable",
                                                   values="mu")
    print(piv.round(3).to_string())
    print(f"\nwritten: {RESULTS / 'moment_trajectories.parquet'}")


if __name__ == "__main__":
    main()
