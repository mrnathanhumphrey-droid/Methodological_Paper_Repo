"""
RMD-SRC Step 2 — trajectory classification (PRE_REG §3.3, locked rule).

Slopes fit by OLS over the TRAINING window 2012-2017 (v1.1 A2).
For each (cell_id, observable):
  mu_dot, var_dot  = OLS slope of μ(t), σ²(t) vs year
  r_mu  = mu_dot / mu_bar       (per-year normalized mean rate)
  r_var = var_dot / var_bar     (per-year normalized variance rate)
  grad_corr = Pearson corr of μ(t) with ∇g(t)
  dip_p = Hartigan dip test p-value on pooled training event values

v1.4 refinement (metric-pathology fix; see PRE_REG_v1.4_amendment.md):
  - Step-2 classifies on moment-slope dynamics ONLY. Raw-value Hartigan dip
    is NOT a Step-2 Fragmenting trigger (it over-fired at ~100% because
    distance/density are intrinsically multimodal); multimodality detection
    moves to Step 3 on response-function residuals. raw_dip_p kept as a
    stored diagnostic only.
  - opp_deficit IS ∇g, so its gradient-tracking branch is skipped
    (self-referential corr≈1); it is classified by variance + mean stability.

∇g(t) := the cell's mean opp_deficit in year t.

Precedence (deterministic, v1.4):
  1. r_var < -0.05                     -> Concentrating (boson-like)
  2. r_var > +0.05                     -> Diffusing (fermion-like)
  3. |r_var| <= 0.05 (flat variance):
       |r_mu| < 0.02                   -> Stationary
       (obs != opp_deficit) & grad>0.5 -> Gradient-tracking
       else                            -> Fragmenting (none-of-above)

Output: results/trajectory_classification.parquet
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import diptest

DERIVED = Path(r"D:\Migration\data\derived")
RESULTS = Path(r"D:\Migration\results")
TRAIN_YEARS = list(range(2012, 2018))
OBSERVABLES = ["log_distance", "log_dest_density", "opp_deficit"]


def ols_slope(years, y):
    return float(np.polyfit(years, y, 1)[0])


def classify(r_mu, r_var, grad_corr, is_opp_deficit):
    # v1.4: moment-slope dynamics only; dip moved to Step 3 on residuals.
    if r_var < -0.05:
        return "Concentrating"
    if r_var > 0.05:
        return "Diffusing"
    # flat variance
    if abs(r_mu) < 0.02:
        return "Stationary"
    if (not is_opp_deficit) and grad_corr > 0.5:
        return "Gradient-tracking"
    return "Fragmenting"


def main():
    traj = pd.read_parquet(RESULTS / "moment_trajectories.parquet")
    traj = traj[traj.year.isin(TRAIN_YEARS)].copy()
    ev = pd.read_parquet(DERIVED / "event_observables.parquet")
    ev = ev[ev.YEAR.isin(TRAIN_YEARS)]

    # ∇g(t): per-cell mean opp_deficit by year (training window)
    grad = (traj[traj.observable == "opp_deficit"]
            .set_index(["cell_id", "year"]).mu)

    rows = []
    for (cid, obs), g in traj.groupby(["cell_id", "observable"]):
        g = g.sort_values("year")
        yrs = g.year.to_numpy(float)
        mu, var = g.mu.to_numpy(float), g["var"].to_numpy(float)
        mu_dot, var_dot = ols_slope(yrs, mu), ols_slope(yrs, var)
        mu_bar, var_bar = mu.mean(), var.mean()
        r_mu = mu_dot / mu_bar if abs(mu_bar) > 1e-9 else np.inf
        r_var = var_dot / var_bar if abs(var_bar) > 1e-12 else np.inf
        gvals = np.array([grad.get((cid, int(y)), np.nan) for y in g.year])
        if np.isfinite(gvals).all() and np.std(gvals) > 1e-9 and np.std(mu) > 1e-9:
            grad_corr = float(np.corrcoef(mu, gvals)[0, 1])
        else:
            grad_corr = np.nan
        evv = ev.loc[(ev.cell_id == cid) & np.isfinite(ev[obs]), obs].to_numpy(float)
        raw_dip_p = float(diptest.diptest(evv)[1]) if len(evv) >= 4 else 1.0  # diagnostic only
        regime = classify(r_mu, r_var, grad_corr if np.isfinite(grad_corr) else 0.0,
                          obs == "opp_deficit")
        rows.append((cid, obs, mu_dot, var_dot, mu_bar, var_bar, r_mu, r_var,
                     grad_corr, raw_dip_p, regime))

    out = pd.DataFrame(rows, columns=["cell_id", "observable", "mu_dot", "var_dot",
                                      "mu_bar", "var_bar", "r_mu", "r_var",
                                      "grad_corr", "raw_dip_p", "regime"])
    RESULTS.mkdir(parents=True, exist_ok=True)
    out.to_parquet(RESULTS / "trajectory_classification.parquet", index=False)

    print(f"classified {len(out)} (cell,observable) pairs over train {TRAIN_YEARS[0]}-{TRAIN_YEARS[-1]} (v1.4 rule)\n")
    print("regime counts (overall):")
    print(out.regime.value_counts().to_string())
    print("\nregime x observable:")
    print(pd.crosstab(out.observable, out.regime).to_string())
    print(f"\nraw_dip_p<0.05 (DIAGNOSTIC only, not a classifier in v1.4): "
          f"{int((out.raw_dip_p<0.05).sum())} / {len(out)}  "
          f"-- intrinsic multimodality of distance/density, tested on residuals in Step 3")
    print(f"written: {RESULTS / 'trajectory_classification.parquet'}")


if __name__ == "__main__":
    main()
