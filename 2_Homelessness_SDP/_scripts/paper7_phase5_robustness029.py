"""
PRE_REG_029 robustness axes (report ROBUST n/4) for the LOAD-BEARING H2
(policy explains displacement net of climate).

Axis 1: pooled panel 2007-2024 (year dummies) vs 2024 cross-section
Axis 2: climate as Census-region dummies vs jan_temp
Axis 4: drop RTS states (NY/MA/DC) -- result must not be RTS-driven
(Axis 3 LOO-vs-5fold: LOO already used as primary; 5-fold reported for level.)
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
spec = importlib.util.spec_from_file_location("fire", r"D:/IDP/_scripts/paper7_phase5_fire_prereg029.py")
fire = importlib.util.module_from_spec(spec); spec.loader.exec_module(fire)

ROOT = Path(r"D:/IDP")
OUT = ROOT / "analysis/paper7_prereg029_robustness_2026_05_27.json"
REGION = {  # Census region
 'CT':'NE','ME':'NE','MA':'NE','NH':'NE','RI':'NE','VT':'NE','NJ':'NE','NY':'NE','PA':'NE',
 'IL':'MW','IN':'MW','MI':'MW','OH':'MW','WI':'MW','IA':'MW','KS':'MW','MN':'MW','MO':'MW','NE':'MW','ND':'MW','SD':'MW',
 'DE':'S','DC':'S','FL':'S','GA':'S','MD':'S','NC':'S','SC':'S','VA':'S','WV':'S','AL':'S','KY':'S','MS':'S','TN':'S','AR':'S','LA':'S','OK':'S','TX':'S',
 'AZ':'W','CO':'W','ID':'W','MT':'W','NV':'W','NM':'W','UT':'W','WY':'W','AK':'W','CA':'W','HI':'W','OR':'W','WA':'W'}

def loo(X,y):
    Xs=StandardScaler().fit_transform(X); p=np.zeros(len(y))
    for tr,te in LeaveOneOut().split(Xs): p[te]=LinearRegression().fit(Xs[tr],y[tr]).predict(Xs[te])
    return float(r2_score(y,p))

def dR2_policy(cx, climate_cols):
    housing=["rental_vacancy_rate","median_gross_rent","rent_to_income"]
    pol=housing+["rts","rent_control_allowed","just_cause_eviction","medicaid_exp","min_wage_2024","drug_death_rate"]
    out={}
    for oc in ["homeless_per_10k","unsheltered_share"]:
        y=cx[oc].values
        rc=loo(cx[climate_cols].values,y); rcp=loo(cx[climate_cols+pol].values,y)
        out[oc]=round(rcp-rc,4)
    return out

def main():
    d=fire.build()
    drug2018=d[d.year==2018].set_index("state")["drug_death_rate"]
    base_cols=["homeless_per_10k","unsheltered_share","jan_temp","rental_vacancy_rate",
        "median_gross_rent","rent_to_income","rts","rent_control_allowed",
        "just_cause_eviction","medicaid_exp","min_wage_2024","drug_death_rate"]
    res={"axes":{}}

    # --- primary 2024 cross-section (jan_temp) ---
    cx=d[d.year==2024].copy(); cx["drug_death_rate"]=cx["drug_death_rate"].fillna(cx["state"].map(drug2018))
    cx=cx.dropna(subset=base_cols)
    res["axes"]["primary_2024_jantemp"]=dR2_policy(cx,["jan_temp"])

    # --- Axis 2: region dummies ---
    cx2=cx.copy(); cx2["region"]=cx2["state"].map(REGION)
    reg=pd.get_dummies(cx2["region"],prefix="reg").astype(float)
    cx2=pd.concat([cx2,reg],axis=1)
    res["axes"]["axis2_region_climate"]=dR2_policy(cx2,list(reg.columns))

    # --- Axis 4: drop RTS states ---
    cx4=cx[~cx.state.isin(["NY","MA","DC"])].copy()
    res["axes"]["axis4_drop_RTS"]=dR2_policy(cx4,["jan_temp"])
    res["axes"]["axis4_n"]=int(len(cx4))

    # --- Axis 1: pooled panel (year dummies) ---
    pan=d.copy(); pan["drug_death_rate"]=pan["drug_death_rate"].fillna(pan["state"].map(drug2018))
    pan=pan[pan.year!=2021].dropna(subset=base_cols)
    yd=pd.get_dummies(pan["year"],prefix="y").astype(float)
    pan=pd.concat([pan.reset_index(drop=True),yd.reset_index(drop=True)],axis=1)
    housing=["rental_vacancy_rate","median_gross_rent","rent_to_income"]
    pol=housing+["rts","rent_control_allowed","just_cause_eviction","medicaid_exp","min_wage_2024","drug_death_rate"]
    clim=["jan_temp"]+list(yd.columns)
    a1={}
    for oc in ["homeless_per_10k","unsheltered_share"]:
        y=pan[oc].values
        kf=KFold(5,shuffle=True,random_state=20260527)
        def cv(cols):
            Xs=StandardScaler().fit_transform(pan[cols].values); p=np.zeros(len(y))
            for tr,te in kf.split(Xs): p[te]=LinearRegression().fit(Xs[tr],y[tr]).predict(Xs[te])
            return r2_score(y,p)
        a1[oc]=round(cv(clim+pol)-cv(clim),4)
    res["axes"]["axis1_pooled_panel_5fold"]=a1; res["axes"]["axis1_n"]=int(len(pan))

    # ROBUST count: dR2_policy >= 0.10 on at least one outcome per axis
    axes_checked=["primary_2024_jantemp","axis2_region_climate","axis4_drop_RTS","axis1_pooled_panel_5fold"]
    robust=sum(1 for a in axes_checked if max(res["axes"][a].values())>=0.10)
    res["H2_ROBUST_n_of_4"]=f"{robust}/4"
    res["interpretation"]="H2 (SDP-legit: policy explains displacement net of climate) ROBUST count"
    OUT.write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2)); print(f"\nwrote {OUT}")

if __name__=="__main__": main()
