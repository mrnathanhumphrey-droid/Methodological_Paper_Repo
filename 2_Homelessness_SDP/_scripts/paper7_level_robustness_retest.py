"""
Re-test: how robust is the homelessness LEVEL explanation, really?

PRE_REG_029 robustness axis4 reported the LEVEL "collapses" on drop-RTS
(dR2(9-var policy | climate) = -0.14 at n=48). The authentic-zoning probe
suggested that was partly OVERFITTING of the 9-variable block, and that a
parsimonious rent model survives drop-RTS. This settles it with a transparent
MODEL LADDER (parsimonious -> full), TWO CV estimators (LOO + 5-fold), BOTH
samples (full / drop-RTS), plus per-year stability and the pooled panel.

No model is cherry-picked: the whole ladder is reported. Correlational only.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import LeaveOneOut, KFold
from sklearn.metrics import r2_score
import importlib.util
spec=importlib.util.spec_from_file_location("fire", r"D:/IDP/_scripts/paper7_phase5_fire_prereg029.py")
fire=importlib.util.module_from_spec(spec); spec.loader.exec_module(fire)

ROOT=Path(r"D:/IDP")
OUT=ROOT/"analysis/paper7_level_robustness_retest_2026_05_28.json"

LADDER={
 "M1_rent": ["median_gross_rent"],
 "M2_rent+vac": ["median_gross_rent","rental_vacancy_rate"],
 "M3_climate+rent+vac": ["jan_temp","median_gross_rent","rental_vacancy_rate"],
 "M4_parsimonious_policy": ["jan_temp","median_gross_rent","rental_vacancy_rate",
                            "medicaid_exp","min_wage_2024","rent_control_allowed"],
 "M5_full9block_029": ["jan_temp","median_gross_rent","rental_vacancy_rate","rent_to_income",
                       "rts","rent_control_allowed","just_cause_eviction","medicaid_exp",
                       "min_wage_2024","drug_death_rate"],
}

def loo(X,y):
    Xs=StandardScaler().fit_transform(X); p=np.zeros(len(y))
    for tr,te in LeaveOneOut().split(Xs): p[te]=LinearRegression().fit(Xs[tr],y[tr]).predict(Xs[te])
    return float(r2_score(y,p))

def kfold(X,y,k=5,seed=20260528):
    Xs=StandardScaler().fit_transform(X); p=np.zeros(len(y)); kf=KFold(k,shuffle=True,random_state=seed)
    for tr,te in kf.split(Xs): p[te]=LinearRegression().fit(Xs[tr],y[tr]).predict(Xs[te])
    return float(r2_score(y,p))

def main():
    d=fire.build()
    drug2018=d[d.year==2018].set_index("state")["drug_death_rate"]
    res={"outcome":"homeless_per_10k","framing":"correlational; full ladder reported, no cherry-pick"}

    # ---------- 2024 cross-section ladder: full vs drop-RTS, LOO + 5fold ----------
    cx=d[d.year==2024].copy(); cx["drug_death_rate"]=cx["drug_death_rate"].fillna(cx["state"].map(drug2018))
    cx=cx.dropna(subset=sorted({c for v in LADDER.values() for c in v}|{"homeless_per_10k"}))
    cxd=cx[~cx.state.isin(["NY","MA","DC"])]
    rungs={}
    for name,cols in LADDER.items():
        yf=cx["homeless_per_10k"].values; yd=cxd["homeless_per_10k"].values
        rungs[name]={"k":len(cols),
            "full_n":int(len(cx)),"full_loo":round(loo(cx[cols].values,yf),4),"full_5fold":round(kfold(cx[cols].values,yf),4),
            "dropRTS_n":int(len(cxd)),"dropRTS_loo":round(loo(cxd[cols].values,yd),4),"dropRTS_5fold":round(kfold(cxd[cols].values,yd),4)}
    res["ladder_2024"]=rungs

    # ---------- per-year stability of parsimonious climate+rent+vac (2015-2024) ----------
    stab={}
    for yr in range(2015,2025):
        sub=d[d.year==yr].dropna(subset=["jan_temp","median_gross_rent","rental_vacancy_rate","homeless_per_10k"])
        if len(sub)>=40:
            stab[yr]={"n":int(len(sub)),"loo":round(loo(sub[["jan_temp","median_gross_rent","rental_vacancy_rate"]].values,sub["homeless_per_10k"].values),4)}
    res["per_year_climate_rent_vac"]=stab

    # ---------- pooled panel (year dummies), 5-fold, full vs drop-RTS ----------
    pan=d[d.year!=2021].copy(); pan["drug_death_rate"]=pan["drug_death_rate"].fillna(pan["state"].map(drug2018))
    pan=pan.dropna(subset=["jan_temp","median_gross_rent","rental_vacancy_rate","homeless_per_10k"])
    yd_=pd.get_dummies(pan["year"],prefix="y").astype(float)
    panx=pd.concat([pan.reset_index(drop=True),yd_.reset_index(drop=True)],axis=1)
    base=["jan_temp","median_gross_rent","rental_vacancy_rate"]+list(yd_.columns)
    pand=panx[~panx.state.isin(["NY","MA","DC"])]
    res["pooled_panel_climate_rent_vac"]={
        "full_n":int(len(panx)),"full_5fold":round(kfold(panx[base].values,panx["homeless_per_10k"].values),4),
        "dropRTS_n":int(len(pand)),"dropRTS_5fold":round(kfold(pand[base].values,pand["homeless_per_10k"].values),4)}

    # ---------- verdict ----------
    pars=rungs["M3_climate+rent+vac"]; full=rungs["M5_full9block_029"]
    overfit = pars["dropRTS_loo"] > full["dropRTS_loo"] + 0.05
    survives = pars["dropRTS_loo"] >= 0.10
    res["verdict"]={
        "parsimonious_M3_dropRTS_loo":pars["dropRTS_loo"],
        "full9block_M5_dropRTS_loo":full["dropRTS_loo"],
        "parsimony_helps_dropRTS":bool(overfit),
        "level_survives_dropRTS_parsimonious":bool(survives),
        "reading":("LEVEL is robustly explained by parsimonious rent model; 029's collapse was overfitting"
                   if (overfit and survives) else
                   "LEVEL stays fragile on drop-RTS even when parsimonious — genuinely RTS/coastal-leaning"
                   if not survives else
                   "mixed: parsimony helps but level still weak")}
    OUT.write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2)); print("\nwrote",OUT)

if __name__=="__main__": main()
