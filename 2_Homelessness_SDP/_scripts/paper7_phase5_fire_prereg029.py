"""
PRE_REG_029 — fire structural-determination / SDP-legitimacy test.

Primary: 2024 cross-section (climate varies cross-sectionally; panel FE would
absorb both climate and time-invariant policy, so cross-section is the right unit
for "policy net of climate"). Secondary: pooled panel (year dummies) for power.

H1 full structural explanation: LOO R^2 on LEVEL (per10k) + FORM (unsheltered).
H2 LOAD-BEARING: policy-block dLOO-R^2 after climate partialled (>=0.10 => SDP legit).
H3 housing-supply mechanism: vacancy(-)/rent(+)/rent-to-income(+) sign+significance on LEVEL.

WRLURI zoning DEFERRED to v2 (pre-cond 4.3): not cleanly extractable; housing-
supply captured by vacancy+rent+rent/income per Colburn & Aldern (the cited prior).
Opioid 1999-2018 clean; 2018 value used as flagged proxy for 2024 cross-section.
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
OUT = ROOT / "analysis/paper7_prereg029_results_2026_05_27.json"

FIPS2USPS = {"01":"AL","02":"AK","04":"AZ","05":"AR","06":"CA","08":"CO","09":"CT",
"10":"DE","11":"DC","12":"FL","13":"GA","15":"HI","16":"ID","17":"IL","18":"IN",
"19":"IA","20":"KS","21":"KY","22":"LA","23":"ME","24":"MD","25":"MA","26":"MI",
"27":"MN","28":"MS","29":"MO","30":"MT","31":"NE","32":"NV","33":"NH","34":"NJ",
"35":"NM","36":"NY","37":"NC","38":"ND","39":"OH","40":"OK","41":"OR","42":"PA",
"44":"RI","45":"SC","46":"SD","47":"TN","48":"TX","49":"UT","50":"VT","51":"VA",
"53":"WA","54":"WV","55":"WI","56":"WY"}
NAME2USPS = {  # CDC uses full names
    'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA',
    'Colorado':'CO','Connecticut':'CT','Delaware':'DE','District of Columbia':'DC',
    'Florida':'FL','Georgia':'GA','Hawaii':'HI','Idaho':'ID','Illinois':'IL',
    'Indiana':'IN','Iowa':'IA','Kansas':'KS','Kentucky':'KY','Louisiana':'LA',
    'Maine':'ME','Maryland':'MD','Massachusetts':'MA','Michigan':'MI','Minnesota':'MN',
    'Mississippi':'MS','Missouri':'MO','Montana':'MT','Nebraska':'NE','Nevada':'NV',
    'New Hampshire':'NH','New Jersey':'NJ','New Mexico':'NM','New York':'NY',
    'North Carolina':'NC','North Dakota':'ND','Ohio':'OH','Oklahoma':'OK','Oregon':'OR',
    'Pennsylvania':'PA','Rhode Island':'RI','South Carolina':'SC','South Dakota':'SD',
    'Tennessee':'TN','Texas':'TX','Utah':'UT','Vermont':'VT','Virginia':'VA',
    'Washington':'WA','West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY'}


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
    drug = pd.DataFrame(json.loads((ROOT / "data/paper7/cdc_drug/cdc_drug_poisoning_state_year.json").read_text()))
    drug["state"] = drug["state"].map(NAME2USPS)
    pol = pb.policy_frame()

    base = panel.merge(acs[["year","state","median_gross_rent","median_hh_income",
                            "poverty_rate","renter_share","rental_vacancy_rate"]],
                       on=["year","state"], how="left")
    base = base.merge(drug[["year","state","drug_death_rate"]], on=["year","state"], how="left")
    base = base.merge(pol, on="state", how="left")
    base["rent_to_income"] = base["median_gross_rent"]*12 / base["median_hh_income"]
    return base


def fit_cross_section(d, year=2024):
    cx = d[d.year == year].copy()
    # 2018-proxy drug deaths for 2024 (flagged): backfill from last available
    drug2018 = d[d.year == 2018].set_index("state")["drug_death_rate"]
    cx["drug_death_rate"] = cx["drug_death_rate"].fillna(cx["state"].map(drug2018))
    cols = ["homeless_per_10k","unsheltered_share","jan_temp","rental_vacancy_rate",
            "median_gross_rent","rent_to_income","rts","rent_control_allowed",
            "just_cause_eviction","medicaid_exp","min_wage_2024","drug_death_rate",
            "poverty_rate","median_hh_income"]
    cx = cx.dropna(subset=cols)
    res = {"year": year, "n_states": int(len(cx))}

    climate = ["jan_temp"]
    housing = ["rental_vacancy_rate","median_gross_rent","rent_to_income"]
    tenure_welfare_health = ["rts","rent_control_allowed","just_cause_eviction",
                             "medicaid_exp","min_wage_2024","drug_death_rate"]
    policy_all = housing + tenure_welfare_health
    full = climate + policy_all + ["poverty_rate","median_hh_income"]

    for outcome in ["homeless_per_10k","unsheltered_share"]:
        y = cx[outcome].values
        r_clim = loo_r2(cx[climate].values, y)
        r_clim_house = loo_r2(cx[climate+housing].values, y)
        r_clim_pol = loo_r2(cx[climate+policy_all].values, y)
        r_full = loo_r2(cx[full].values, y)
        res[outcome] = {
            "loo_r2_climate": round(r_clim,4),
            "loo_r2_climate_plus_housing": round(r_clim_house,4),
            "loo_r2_climate_plus_allpolicy": round(r_clim_pol,4),
            "loo_r2_full": round(r_full,4),
            "dR2_housing_given_climate": round(r_clim_house - r_clim,4),
            "dR2_policy_given_climate": round(r_clim_pol - r_clim,4),
        }

    # H3: OLS housing-supply on LEVEL, signs + significance
    X = sm.add_constant(StandardScaler().fit_transform(cx[housing+climate].values))
    m = sm.OLS(cx["homeless_per_10k"].values, X).fit()
    names = ["const"]+housing+climate
    res["H3_housing_ols_on_level"] = {
        n: {"coef": round(float(m.params[i]),3), "p": round(float(m.pvalues[i]),4)}
        for i,n in enumerate(names)}
    res["H3_model_r2"] = round(float(m.rsquared),4)
    return res, cx


def main():
    d = build()
    cx_res, cx = fit_cross_section(d, 2024)

    # dispositions vs locked thresholds
    lvl = cx_res["homeless_per_10k"]; frm = cx_res["unsheltered_share"]
    h1_best = max(lvl["loo_r2_full"], frm["loo_r2_full"])
    h1 = "SUPPORTED" if h1_best>=0.40 else ("FALSIFIED" if (lvl["loo_r2_full"]<0.20 and frm["loo_r2_full"]<0.20) else "MIXED")
    dR2_pol = max(lvl["dR2_policy_given_climate"], frm["dR2_policy_given_climate"])
    h2 = "SUPPORTED" if dR2_pol>=0.10 else ("FALSIFIED" if dR2_pol<0.05 else "MIXED")
    h3blk = cx_res["H3_housing_ols_on_level"]
    vac = h3blk["rental_vacancy_rate"]; rent = h3blk["median_gross_rent"]
    h3_ok = (vac["coef"]<0) and (rent["coef"]>0) and (min(vac["p"],rent["p"])<0.10)
    h3 = "SUPPORTED" if h3_ok else "MIXED/FALSIFIED"

    out = {
        "pre_reg":"PRE_REG_029","framing":"correlational; SDP-legit = structure explains net of climate",
        "deferred":"WRLURI zoning (v2); opioid 2018-proxy for 2024 (flagged)",
        "cross_section_2024": cx_res,
        "dispositions": {
            "H1_structural_explanation": {"verdict":h1,"best_full_loo_r2":round(h1_best,4),
                "threshold":">=0.40 support; <0.20 both => F1"},
            "H2_policy_net_of_climate_LOADBEARING": {"verdict":h2,"max_dR2_policy_given_climate":round(dR2_pol,4),
                "threshold":">=0.10 support; <0.05 => F2 (weather artifact)"},
            "H3_housing_supply_mechanism": {"verdict":h3,
                "vacancy_coef":vac["coef"],"vacancy_p":vac["p"],
                "rent_coef":rent["coef"],"rent_p":rent["p"],
                "rent_to_income":h3blk["rent_to_income"],
                "threshold":"vacancy<0 & rent>0 & p<0.10"},
        },
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    print(f"\n[prereg029] wrote {OUT}")


if __name__ == "__main__":
    main()
