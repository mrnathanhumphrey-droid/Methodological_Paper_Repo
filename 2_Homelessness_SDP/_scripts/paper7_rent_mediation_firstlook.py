"""
First-look (EXPLORATORY, read-only): is there a structural driver of RENT, and
does it reach homelessness THROUGH rent (mediation)?

Chain tested:  zoning (supply constraint) --a--> rent --b--> homelessness
Direct zoning->homelessness was ~null (-2.69, p=0.24). If a>0 and b>0, zoning has
an INDIRECT effect via rent even with null direct effect = full mediation.

Data in hand: authentic WRLURI zoning, ACS rent/vacancy/income, homeless_per_10k.
Saiz supply elasticity + building permits NOT yet pulled (full pre-reg adds them).
Correlational only; "mediation pattern consistent with causal chain", not proof.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler

ROOT=Path(r"D:/IDP")
FIPS2USPS={"01":"AL","02":"AK","04":"AZ","05":"AR","06":"CA","08":"CO","09":"CT",
"10":"DE","11":"DC","12":"FL","13":"GA","15":"HI","16":"ID","17":"IL","18":"IN",
"19":"IA","20":"KS","21":"KY","22":"LA","23":"ME","24":"MD","25":"MA","26":"MI",
"27":"MN","28":"MS","29":"MO","30":"MT","31":"NE","32":"NV","33":"NH","34":"NJ",
"35":"NM","36":"NY","37":"NC","38":"ND","39":"OH","40":"OK","41":"OR","42":"PA",
"44":"RI","45":"SC","46":"SD","47":"TN","48":"TX","49":"UT","50":"VT","51":"VA",
"53":"WA","54":"WV","55":"WI","56":"WY"}

def ols(y,Xcols,d):
    X=sm.add_constant(StandardScaler().fit_transform(d[Xcols].values))
    m=sm.OLS(d[y].values,X).fit()
    names=["const"]+Xcols
    return {names[i]:{"coef":round(float(m.params[i]),3),"p":round(float(m.pvalues[i]),4)} for i in range(len(names))}, round(float(m.rsquared),4)

def main():
    panel=pd.read_parquet(ROOT/"analysis/paper7_sdp_state_year_panel.parquet")
    acs=pd.DataFrame(json.loads((ROOT/"data/paper7/acs_structural/acs_structural_state_year.json").read_text()))
    acs["state"]=acs["state_fips"].map(FIPS2USPS)
    z=pd.read_csv(ROOT/"data/paper7/wharton_zoning/wrluri2018_state_avg_AUTHENTIC.csv")
    cx=(panel[panel.year==2024]
        .merge(acs[acs.year==2024][["state","median_gross_rent","rental_vacancy_rate","median_hh_income"]],on="state",how="left")
        .merge(z[["state","zoning"]],on="state",how="left")
        .dropna(subset=["median_gross_rent","rental_vacancy_rate","median_hh_income","zoning","homeless_per_10k"]))
    res={"n":int(len(cx)),"framing":"EXPLORATORY first-look; correlational; mediation PATTERN not proof"}

    # stage a: zoning -> rent (control income, vacancy)
    a_coefs,a_r2=ols("median_gross_rent",["zoning","median_hh_income","rental_vacancy_rate"],cx)
    res["stage_a_zoning_to_rent"]={"coefs":a_coefs,"r2":a_r2}

    # stage b: rent -> homelessness (control zoning) ; and zoning direct
    b_coefs,b_r2=ols("homeless_per_10k",["median_gross_rent","zoning","rental_vacancy_rate"],cx)
    res["stage_b_rent_to_homeless_ctrl_zoning"]={"coefs":b_coefs,"r2":b_r2}

    # simple mediation decomposition (standardized): total c (zoning->homeless), direct c', indirect a*b
    zc=StandardScaler().fit_transform(cx[["zoning"]])
    rc=StandardScaler().fit_transform(cx[["median_gross_rent"]])
    hc=StandardScaler().fit_transform(cx[["homeless_per_10k"]])
    a=sm.OLS(rc,sm.add_constant(zc)).fit().params[1]            # zoning->rent
    full=sm.OLS(hc,sm.add_constant(np.column_stack([zc,rc]))).fit()
    cprime=full.params[1]; b=full.params[2]                      # direct zoning, rent->homeless
    ctot=sm.OLS(hc,sm.add_constant(zc)).fit().params[1]          # total zoning->homeless
    indirect=a*b
    res["mediation_standardized"]={
        "a_zoning_to_rent":round(float(a),3),
        "b_rent_to_homeless":round(float(b),3),
        "indirect_a_times_b":round(float(indirect),3),
        "c_total_zoning_to_homeless":round(float(ctot),3),
        "cprime_direct_zoning":round(float(cprime),3),
        "prop_mediated":round(float(indirect/ctot),3) if abs(ctot)>1e-6 else None,
        "reading":("zoning reaches homelessness THROUGH rent (indirect>0, direct~0) = mediation pattern"
                   if (indirect>0 and abs(cprime)<abs(indirect)) else
                   "no clean mediation pattern at this variable set")}
    OUT=ROOT/"analysis/paper7_rent_mediation_firstlook_2026_05_28.json"
    OUT.write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2)); print("\nwrote",OUT)

if __name__=="__main__": main()
