"""
RMD-SRC Step 3 — response-function validation (PRE_REG §3.3/§3.4 + v1.4 A3).

Response function per (cell, observable):
  x_j = alpha + beta_g*opp_deficit + beta_s*rho_s + beta_x*rho_x + eps
  (for the opp_deficit observable itself, beta_g term dropped — opp_deficit IS
   the gradient; v1.4 treatment. Fit: opp_deficit ~ rho_s + rho_x.)

  rho_s = prior-year (t-1) SAME-species resident density at dest MIGPUMA (per km2)
  rho_x = prior-year (t-1) CROSS-species resident density at dest MIGPUMA (per km2)

OLS, cluster-robust SE on ORIGIN MIGPUMA (origin-PUMA unavailable; v1.3 geography).
beta_s significant = |t| > 2.0.

Cleanness (§3.4 + v1.4 A3):
  R^2 >= 0.30  AND  Shapiro resid p > 0.01  AND  Hartigan dip resid p >= 0.05
  AND no sign-contradiction with the Step-2 regime:
    Stationary / Gradient-tracking -> predict beta_s ~ 0 (contradiction if |t|>2)
    Concentrating                  -> predict beta_s > 0 significant
    Diffusing                      -> predict beta_s < 0 significant
    Fragmenting                    -> response ill-fit expected (not "clean";
                                       flagged for Step-4 decomposition)

Shapiro on a reproducible <=5000 residual subsample (scipy limit).
2012 events dropped (no t-1 stock). Fit window = training 2013-2017.

Outputs: results/step3_validation.parquet, console F1/F3 summary.
"""
from __future__ import annotations
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import shapiro
import diptest

DERIVED = Path(r"D:\Migration\data\derived")
RESULTS = Path(r"D:\Migration\results")
TRAIN_YEARS = list(range(2012, 2018))
OBSERVABLES = ["log_distance", "log_dest_density", "opp_deficit"]
RNG = np.random.default_rng(0)


def attach_density(ev: pd.DataFrame) -> pd.DataFrame:
    stock = pd.read_parquet(DERIVED / "migpuma_species_stock_2010.parquet")
    geo = pd.read_parquet(DERIVED / "migpuma_geometry_2010.parquet")[
        ["statefip", "migpuma", "land_km2"]]
    tot = (stock.groupby(["statefip", "migpuma", "year"]).stock.sum()
           .reset_index().rename(columns={"stock": "tot_stock"}))

    ev = ev.copy()
    ev["py"] = ev.YEAR - 1
    # same-species prior-year stock at destination
    s = stock.rename(columns={"statefip": "dest_state", "migpuma": "dest_migpuma",
                              "year": "py", "cell_id": "cell_id", "stock": "same_stock"})
    ev = ev.merge(s, on=["dest_state", "dest_migpuma", "py", "cell_id"], how="left")
    t = tot.rename(columns={"statefip": "dest_state", "migpuma": "dest_migpuma",
                            "year": "py"})
    ev = ev.merge(t, on=["dest_state", "dest_migpuma", "py"], how="left")
    g = geo.rename(columns={"statefip": "dest_state", "migpuma": "dest_migpuma"})
    ev = ev.merge(g, on=["dest_state", "dest_migpuma"], how="left")

    ev["same_stock"] = ev.same_stock.fillna(0.0)
    ev["cross_stock"] = ev.tot_stock - ev.same_stock
    ev["rho_s"] = ev.same_stock / ev.land_km2
    ev["rho_x"] = ev.cross_stock / ev.land_km2
    ev["orig_cluster"] = ev.orig_state.astype(int) * 100000 + ev.orig_migpuma.astype(int)
    return ev


def predicted(regime):
    # §3.3 validation table: Gradient-tracking(Classical)->beta_s~0;
    # Stationary->INCONCLUSIVE (equilibrium, no sign prediction);
    # Concentrating(boson)->+; Diffusing(fermion)->-; Fragmenting->ill-fit.
    if regime == "Gradient-tracking":
        return "zero"
    if regime == "Stationary":
        return "inconclusive"
    if regime == "Concentrating":
        return "pos"
    if regime == "Diffusing":
        return "neg"
    return "illfit"  # Fragmenting


def main():
    ev = pd.read_parquet(DERIVED / "event_observables.parquet")
    ev = ev[~ev.missing_geo & ~ev.missing_opp].copy()
    ev = ev[ev.YEAR.isin(TRAIN_YEARS)]
    ev = attach_density(ev)
    # need valid prior-year stock (drops 2012) and finite densities
    ev = ev[ev.tot_stock.notna() & np.isfinite(ev.rho_s) & np.isfinite(ev.rho_x)]
    print(f"fit events (training, with t-1 density): {len(ev):,}  "
          f"years {sorted(ev.YEAR.unique())}")

    cls = pd.read_parquet(RESULTS / "trajectory_classification.parquet")
    regime_of = {(r.cell_id, r.observable): r.regime for r in cls.itertuples()}

    rows = []
    for cid in sorted(ev.cell_id.unique()):
        d_all = ev[ev.cell_id == cid]
        for obs in OBSERVABLES:
            d = d_all[np.isfinite(d_all[obs])].copy()
            d = d.rename(columns={obs: "y"})
            if len(d) < 50:
                continue
            formula = "y ~ rho_s + rho_x" if obs == "opp_deficit" \
                else "y ~ opp_deficit + rho_s + rho_x"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m = smf.ols(formula, data=d).fit(
                    cov_type="cluster", cov_kwds={"groups": d.orig_cluster})
            beta_s = float(m.params.get("rho_s", np.nan))
            t_s = float(m.tvalues.get("rho_s", np.nan))
            r2 = float(m.rsquared)
            resid = m.resid.to_numpy()
            # v1.5 C1: Shapiro on fixed n=300 subsample (practical scale, not large-n)
            samp = resid if len(resid) <= 300 else RNG.choice(resid, 300, replace=False)
            sh_p = float(shapiro(samp).pvalue)
            dip_p = float(diptest.diptest(resid)[1])

            regime = regime_of.get((cid, obs), "NA")
            pred = predicted(regime)
            sig = abs(t_s) > 2.0
            # sign agreement (Stationary=inconclusive & Fragmenting=ill-fit -> no contradiction)
            if pred == "zero":
                contradiction = sig
            elif pred == "pos":
                contradiction = not (sig and beta_s > 0)
            elif pred == "neg":
                contradiction = not (sig and beta_s < 0)
            else:  # inconclusive or illfit
                contradiction = False
            inconclusive = pred == "inconclusive"
            resid_ok = (r2 >= 0.05) and (sh_p > 0.01) and (dip_p >= 0.05)  # v1.5 C2: R2 floor 0.05
            clean = resid_ok and (not contradiction) and (regime != "Fragmenting")
            rows.append((cid, obs, regime, pred, len(d), beta_s, t_s, sig,
                         r2, sh_p, dip_p, resid_ok, inconclusive, contradiction, clean))

    res = pd.DataFrame(rows, columns=["cell_id", "observable", "regime", "pred_beta_s",
                                      "n", "beta_s", "t_s", "beta_s_sig", "r2",
                                      "shapiro_p", "dip_p", "resid_ok",
                                      "inconclusive", "contradiction", "clean"])
    RESULTS.mkdir(parents=True, exist_ok=True)
    res.to_parquet(RESULTS / "step3_validation.parquet", index=False)

    n = len(res)
    n_clean = int(res.clean.sum())
    n_contra = int(res.contradiction.sum())
    print(f"\n=== Step 3 validation ({n} cell-observable fits) ===")
    print(f"R2 >=0.05: {int((res.r2>=0.05).sum())}/{n}   "
          f"Shapiro(n=300) p>0.01: {int((res.shapiro_p>0.01).sum())}/{n}   "
          f"resid dip p>=0.05: {int((res.dip_p>=0.05).sum())}/{n}")
    print(f"resid_ok (all three): {int(res.resid_ok.sum())}/{n}")
    n_incon = int(res.inconclusive.sum())
    print(f"\nclean leaves: {n_clean}/{n} = {100*n_clean/n:.1f}%")
    print(f"inconclusive (Stationary/equilibrium): {n_incon}/{n}")
    print(f"contradictions (trajectory vs beta_s sign): {n_contra}/{n} = {100*n_contra/n:.1f}%")
    print(f"\n--- FALSIFIER CHECKS ---")
    print(f"RMD_F1 (>=80% clean WITHOUT decomposition -> substrate is classical): "
          f"{100*n_clean/n:.1f}% clean -> {'FIRES' if n_clean/n>=0.80 else 'does not fire (substrate needs RMD)'}")
    print(f"RMD_F3 PREVIEW (formally evaluated AFTER Step-4 decomposition): "
          f"{100*n_contra/n:.1f}% disagree -> {'would fire' if n_contra/n>=0.30 else 'would not fire'}")
    print(f"\nclean x observable:")
    print(pd.crosstab(res.observable, res.clean).to_string())
    print(f"\nbeta_s sign among significant fits (network effect):")
    sig = res[res.beta_s_sig]
    print(f"  significant beta_s: {len(sig)}/{n};  positive: {int((sig.beta_s>0).sum())}, negative: {int((sig.beta_s<0).sum())}")
    print(f"\nwritten: {RESULTS / 'step3_validation.parquet'}")


if __name__ == "__main__":
    main()
