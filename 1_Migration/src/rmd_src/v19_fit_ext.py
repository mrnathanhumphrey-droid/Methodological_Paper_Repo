"""
PRE_REG v1.9 extension — FARA arm (national), FOODPUSH_F4 instrument coherence,
and density-control robustness on the redline effect.

Per race group g, between-MIGPUMA corridors, flow>=50, offset=log(window yrs),
origin-MIGPUMA-clustered SE. Origin covariates merged:
  redline_D_share   (HOLC, urban-graded origins only)
  fara_lowaccess_share (FARA 1mi/10mi low-access pop share, national)
  log_dens_o        (TOTAL origin population density = urbanicity confound)

Models per group:
  FARA  (national origins): M0 + bF*fara_lowaccess_share
  HOLC  (graded origins):   M0 + bR*redline_D_share                  [recap]
  HOLC+density:             M0 + bR*redline_D_share + bD*log_dens_o  [robustness]
  F4 coherence:             on HOLC origins, sign(bR) vs sign(bF)

Output: results/v19_foodpush_ext.json
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.special import gammaln

DERIVED = Path(r"D:\Migration\data\derived")
RESULTS = Path(r"D:\Migration\results")
TRAIN = list(range(2012, 2018))
HOLD = list(range(2018, 2022))
MIN_FLOW = 50
GROUPS = ["NH_White", "NH_Black", "Hispanic", "NH_AsianPI", "NH_Other"]


def haversine(lo1, la1, lo2, la2):
    R = 6371.0088
    lo1, la1, lo2, la2 = map(np.radians, [lo1, la1, lo2, la2])
    a = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def poisson_ll(y, mu):
    mu = np.clip(np.asarray(mu, float), 1e-9, None)
    y = np.asarray(y, float)
    return float(np.sum(y * np.log(mu) - mu - gammaln(y + 1)))


FLOWS = pd.read_parquet(DERIVED / "race_corridor_flows_2010.parquet")
POPR = pd.read_parquet(DERIVED / "migpuma_population_by_race_2010.parquet")
GEO = pd.read_parquet(DERIVED / "migpuma_geometry_2010.parquet")
HOLC = pd.read_parquet(DERIVED / "migpuma_holc_2010.parquet")
FARA = pd.read_parquet(DERIVED / "migpuma_fara_2010.parquet")
POPTOT = pd.read_parquet(DERIVED / "migpuma_population_2010.parquet")
CENT = GEO.set_index(["statefip", "migpuma"])[["lon", "lat"]]
LAND = GEO.set_index(["statefip", "migpuma"])["land_km2"]


def build(years, race):
    f = FLOWS[(FLOWS.race_group == race) & (FLOWS.YEAR.isin(years))]
    od = (f.groupby(["orig_state", "orig_migpuma", "dest_state", "dest_migpuma"])
          .flow.sum().reset_index())
    pr = (POPR[(POPR.race_group == race) & (POPR.year.isin(years))]
          .groupby(["statefip", "migpuma"]).population.mean().reset_index())
    od = od.merge(pr.rename(columns={"statefip": "orig_state", "migpuma": "orig_migpuma", "population": "mass_o"}),
                  on=["orig_state", "orig_migpuma"], how="inner")
    od = od.merge(pr.rename(columns={"statefip": "dest_state", "migpuma": "dest_migpuma", "population": "mass_d"}),
                  on=["dest_state", "dest_migpuma"], how="inner")
    # total-density (urbanicity) at origin
    ptot = (POPTOT[POPTOT.year.isin(years)].groupby(["statefip", "migpuma"]).population.mean()
            .reset_index().rename(columns={"population": "totpop"}))
    ptot["land_km2"] = ptot.set_index(["statefip", "migpuma"]).index.map(LAND).to_numpy()
    ptot["dens"] = ptot.totpop / ptot.land_km2
    od = od.merge(ptot[["statefip", "migpuma", "dens"]].rename(
        columns={"statefip": "orig_state", "migpuma": "orig_migpuma", "dens": "dens_o"}),
        on=["orig_state", "orig_migpuma"], how="left")
    od = od.merge(HOLC[["statefip", "migpuma", "redline_D_share"]].rename(
        columns={"statefip": "orig_state", "migpuma": "orig_migpuma"}), on=["orig_state", "orig_migpuma"], how="left")
    od = od.merge(FARA[["statefip", "migpuma", "fara_lowaccess_share"]].rename(
        columns={"statefip": "orig_state", "migpuma": "orig_migpuma"}), on=["orig_state", "orig_migpuma"], how="left")
    od = od.join(CENT.rename(columns={"lon": "o_lon", "lat": "o_lat"}), on=["orig_state", "orig_migpuma"])
    od = od.join(CENT.rename(columns={"lon": "d_lon", "lat": "d_lat"}), on=["dest_state", "dest_migpuma"])
    od = od.dropna(subset=["o_lon", "d_lon", "mass_o", "mass_d"])
    od = od[(od.mass_o > 0) & (od.mass_d > 0) & (od.flow >= MIN_FLOW)].copy()
    od["dist"] = haversine(od.o_lon, od.o_lat, od.d_lon, od.d_lat).clip(lower=1)
    od["log_mass_o"] = np.log(od.mass_o); od["log_mass_d"] = np.log(od.mass_d)
    od["log_dist"] = np.log(od.dist); od["log_dens_o"] = np.log(od.dens_o.clip(lower=1e-3))
    od["offset"] = np.log(len(years)); od["grp"] = od.orig_state * 1000 + od.orig_migpuma
    return od


def fit(od, extra):
    cols = ["log_mass_o", "log_mass_d", "log_dist"] + extra
    X = sm.add_constant(od[cols].to_numpy(float))
    res = sm.GLM(od.flow.to_numpy(float), X, family=sm.families.Poisson(),
                 offset=od.offset.to_numpy(float)).fit(
        cov_type="cluster", cov_kwds={"groups": od.grp.to_numpy()})
    return res


def beta(res, k):  # k = index from end
    return float(res.params[k]), float(res.pvalues[k]), float(res.bse[k])


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    out = {"groups": {}}
    for g in GROUPS:
        tr = build(TRAIN, g); ho = build(HOLD, g)
        rec = {"n_train": int(len(tr))}
        # FARA national
        trf = tr.dropna(subset=["fara_lowaccess_share"]); hof = ho.dropna(subset=["fara_lowaccess_share"])
        mF = fit(trf, ["fara_lowaccess_share"]); mFh = fit(hof, ["fara_lowaccess_share"])
        bF, pF, sF = beta(mF, -1); bFh, pFh, _ = beta(mFh, -1)
        rec["FARA_national"] = {"n": int(len(trf)), "n_origins": int(trf.grp.nunique()),
                                "beta_train": bF, "p_train": pF, "beta_holdout": bFh, "p_holdout": pFh}
        # HOLC origins subset
        trh = tr.dropna(subset=["redline_D_share"]); hoh = ho.dropna(subset=["redline_D_share"])
        mR = fit(trh, ["redline_D_share"]); bR, pR, sR = beta(mR, -1)
        # HOLC + density
        mRD = fit(trh, ["redline_D_share", "log_dens_o"])
        bRd, pRd, _ = beta(mRD, -2); bD, pD, _ = beta(mRD, -1)
        # FARA on HOLC origins (for F4 coherence, same sample)
        mFonH = fit(trh.dropna(subset=["fara_lowaccess_share"]), ["fara_lowaccess_share"])
        bFonH, pFonH, _ = beta(mFonH, -1)
        rec["HOLC"] = {"n": int(len(trh)), "beta_redline": bR, "p_redline": pR}
        rec["HOLC_plus_density"] = {"beta_redline": bRd, "p_redline": pRd,
                                    "beta_logdens": bD, "p_logdens": pD,
                                    "redline_survives_density": bool(pRd < 0.05 and bRd > 0)}
        rec["F4_on_holc_origins"] = {"beta_redline": bR, "beta_fara": bFonH, "p_fara": pFonH,
                                     "sign_agree": bool(np.sign(bR) == np.sign(bFonH))}
        out["groups"][g] = rec
        print(f"=== {g:11s} ===")
        print(f"  FARA national    bF={bF:+.4f} p={pF:.2e} | holdout {bFh:+.4f} p={pFh:.2e}  (n={len(trf):,}, {trf.grp.nunique()} origins)")
        print(f"  HOLC redline     bR={bR:+.4f} p={pR:.2e}")
        print(f"  +density         bR={bRd:+.4f} p={pRd:.2e}  bDens={bD:+.4f} p={pD:.2e}  -> redline {'SURVIVES' if rec['HOLC_plus_density']['redline_survives_density'] else 'killed'}")
        print(f"  F4 (HOLC origins) redline {bR:+.3f} vs FARA {bFonH:+.3f}  -> {'AGREE' if rec['F4_on_holc_origins']['sign_agree'] else 'DISAGREE'}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "v19_foodpush_ext.json").write_text(json.dumps(out, indent=2))
    print(f"\nwritten: {RESULTS / 'v19_foodpush_ext.json'}")


if __name__ == "__main__":
    main()
