"""
PROBE (not a locked pre-reg): does land-use/zoning restrictiveness (WRLURI 2018)
explain the LEVEL of US homelessness (homeless_per_10k) net of climate, and does it
SURVIVE dropping the three right-to-shelter states (NY, MA, DC) where rent did NOT?

Correlational framing only. Creates only new files. Does not touch any locked artifact.

WRLURI source: HAND-CODED state averages (flagged). No state-level WRLURI table exists
in the published NBER w26573 / JUE papers (community + CBSA level only); no clean state
CSV was web-obtainable. See data/paper7/wharton_zoning/wrluri2018_state_avg_HANDCODED.csv.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import r2_score

import importlib.util
spec = importlib.util.spec_from_file_location("pb", r"D:/IDP/_scripts/paper7_policy_block.py")
pb = importlib.util.module_from_spec(spec); spec.loader.exec_module(pb)

ROOT = Path(r"D:/IDP")
OUT = ROOT / "analysis/paper7_probe_zoning_2026_05_28.json"
WZ = ROOT / "data/paper7/wharton_zoning/wrluri2018_state_avg_HANDCODED.csv"

FIPS2USPS = {"01":"AL","02":"AK","04":"AZ","05":"AR","06":"CA","08":"CO","09":"CT",
"10":"DE","11":"DC","12":"FL","13":"GA","15":"HI","16":"ID","17":"IL","18":"IN",
"19":"IA","20":"KS","21":"KY","22":"LA","23":"ME","24":"MD","25":"MA","26":"MI",
"27":"MN","28":"MS","29":"MO","30":"MT","31":"NE","32":"NV","33":"NH","34":"NJ",
"35":"NM","36":"NY","37":"NC","38":"ND","39":"OH","40":"OK","41":"OR","42":"PA",
"44":"RI","45":"SC","46":"SD","47":"TN","48":"TX","49":"UT","50":"VT","51":"VA",
"53":"WA","54":"WV","55":"WI","56":"WY"}


def loo_r2(X, y):
    Xs = StandardScaler().fit_transform(X)
    pred = np.zeros(len(y))
    for tr, te in LeaveOneOut().split(Xs):
        pred[te] = LinearRegression().fit(Xs[tr], y[tr]).predict(Xs[te])
    return float(r2_score(y, pred))


def build():
    panel = pd.read_parquet(ROOT / "analysis/paper7_sdp_state_year_panel.parquet")
    acs = pd.DataFrame(json.loads((ROOT / "data/paper7/acs_structural/acs_structural_state_year.json").read_text()))
    acs["state"] = acs["state_fips"].map(FIPS2USPS)
    pol = pb.policy_frame()
    wz = pd.read_csv(WZ, comment="#")[["state", "wrluri2018_state_avg"]].rename(
        columns={"wrluri2018_state_avg": "zoning"})

    base = panel.merge(acs[["year", "state", "median_gross_rent", "median_hh_income",
                            "poverty_rate", "rental_vacancy_rate"]],
                       on=["year", "state"], how="left")
    base = base.merge(pol, on="state", how="left")
    base = base.merge(wz, on="state", how="left")
    return base


def fit(cx, predictors, outcome="homeless_per_10k"):
    cx2 = cx.dropna(subset=[outcome] + predictors).copy()
    return loo_r2(cx2[predictors].values, cx2[outcome].values), len(cx2)


def ols_block(cx, predictors, outcome="homeless_per_10k"):
    cx2 = cx.dropna(subset=[outcome] + predictors).copy()
    X = sm.add_constant(StandardScaler().fit_transform(cx2[predictors].values))
    m = sm.OLS(cx2[outcome].values, X).fit()
    names = ["const"] + predictors
    return {n: {"coef": round(float(m.params[i]), 3), "p": round(float(m.pvalues[i]), 4)}
            for i, n in enumerate(names)}, round(float(m.rsquared), 4), len(cx2)


def run_sample(cx, tag):
    climate = ["jan_temp"]
    rent = ["median_gross_rent"]
    vac = ["rental_vacancy_rate"]
    zon = ["zoning"]

    out = {}
    # nested LOO R^2 (LEVEL)
    cset = {
        "climate": climate,
        "climate+rent": climate + rent,
        "climate+rent+zoning": climate + rent + vac + zon,
        "climate+zoning_norent": climate + vac + zon,
        "climate+rent+vac": climate + rent + vac,
    }
    loo = {}
    n_used = None
    for name, preds in cset.items():
        r, n = fit(cx, preds)
        loo[name] = round(r, 4)
        n_used = n if name == "climate+rent+zoning" else n_used
    out["loo_r2"] = loo
    out["n_used_full_model"] = n_used
    out["dR2_zoning_over_rent"] = round(loo["climate+rent+zoning"] - loo["climate+rent+vac"], 4)
    out["dR2_zoning_alone_over_climate"] = round(loo["climate+zoning_norent"] - loo["climate"], 4)
    out["dR2_rent_alone_over_climate"] = round(loo["climate+rent"] - loo["climate"], 4)

    # OLS standardized: [zoning, rent, vacancy, jan_temp] on LEVEL
    coefs, r2, n = ols_block(cx, zon + rent + vac + climate, "homeless_per_10k")
    out["ols_level_standardized"] = {"coefs": coefs, "model_r2": r2, "n": n}
    out["zoning_coef"] = coefs["zoning"]["coef"]
    out["zoning_p"] = coefs["zoning"]["p"]
    out["rent_coef"] = coefs["median_gross_rent"]["coef"]
    out["rent_p"] = coefs["median_gross_rent"]["p"]
    return out


def main():
    d = build()
    cx_all = d[d.year == 2024].copy()
    # report merge coverage
    n_zoning = int(cx_all["zoning"].notna().sum())
    n_total = int(cx_all["state"].nunique())

    full = run_sample(cx_all, "n51")

    drop = cx_all[~cx_all["state"].isin(["NY", "MA", "DC"])].copy()
    dropres = run_sample(drop, "drop_RTS")

    # Secondary: zoning vs FORM (unsheltered_share)
    form = cx_all.dropna(subset=["unsheltered_share", "zoning"])
    corr_form = float(np.corrcoef(form["zoning"], form["unsheltered_share"])[0, 1])
    coefs_f, r2_f, n_f = ols_block(
        cx_all, ["zoning", "median_gross_rent", "rental_vacancy_rate", "jan_temp"],
        "unsheltered_share")
    # raw zoning-rent correlation (is rent the shadow of zoning?)
    zr = cx_all.dropna(subset=["zoning", "median_gross_rent"])
    corr_zoning_rent = float(np.corrcoef(zr["zoning"], zr["median_gross_rent"])[0, 1])

    # dispositions
    def disp(res):
        z_pos = res["zoning_coef"] > 0
        z_sig = res["zoning_p"] < 0.10
        adds = res["dR2_zoning_over_rent"] > 0.02
        return {"zoning_positive": z_pos, "zoning_p<0.10": z_sig,
                "zoning_adds_dR2_over_rent": adds}

    survives = (dropres["zoning_coef"] > 0 and dropres["zoning_p"] < 0.10
                and dropres["dR2_zoning_alone_over_climate"] > 0.05)

    out = {
        "probe": "paper7 zoning (WRLURI2018) on the LEVEL",
        "framing": "correlational only; never causal",
        "wrluri_provenance": "HAND-CODED state averages; flagged. No state-level WRLURI table "
                             "in published NBER w26573 / JUE papers (community+CBSA only); no "
                             "clean state CSV web-obtainable. See wharton_zoning/.",
        "merge_coverage": {"states_with_zoning_2024": n_zoning, "states_total_2024": n_total},
        "full_sample_n51": full,
        "drop_RTS_n48": dropres,
        "secondary_zoning_vs_FORM": {
            "pearson_r_zoning_unsheltered": round(corr_form, 4),
            "ols_unsheltered": {"coefs": coefs_f, "model_r2": r2_f, "n": n_f},
        },
        "zoning_rent_correlation": round(corr_zoning_rent, 4),
        "dispositions": {
            "full_sample": disp(full),
            "drop_RTS": disp(dropres),
            "ZONING_SURVIVES_DROP_RTS": bool(survives),
            "criterion_survives": "zoning coef>0 AND p<0.10 AND dR2_zoning_alone_over_climate>0.05 in n=48",
        },
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    print(f"\n[probe-zoning] wrote {OUT}")


if __name__ == "__main__":
    main()
