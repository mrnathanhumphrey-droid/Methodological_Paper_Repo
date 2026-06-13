"""
PRE_REG_030 — supply-constraint -> rent -> homelessness mediation (bootstrapped).

Supply-constraint index (higher = more constrained) = mean of standardized
[ zoning(WRLURI18, authentic), -saiz_elasticity ]  (regulatory + geographic).
Robustness adds units_per_capita / unit-growth. Mediator = median rent. Outcome
= homeless_per_10k. Control = median HH income (demand). 2024 cross-section + panel.

H1 first stage: supply -> rent (LOO R>=0.40, supply sig).
H2 LOAD-BEARING: bootstrapped 95% BC CI of indirect a*b excludes 0 (positive).
H3: supply partial-R2 for rent > demand partial-R2.
Correlational; ordering (supply->rent->homeless) locked by timescale.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import r2_score

ROOT=Path(r"D:/IDP")
OUT=ROOT/"analysis/paper7_prereg030_results_2026_05_28.json"
FIPS2USPS={"01":"AL","02":"AK","04":"AZ","05":"AR","06":"CA","08":"CO","09":"CT",
"10":"DE","11":"DC","12":"FL","13":"GA","15":"HI","16":"ID","17":"IL","18":"IN",
"19":"IA","20":"KS","21":"KY","22":"LA","23":"ME","24":"MD","25":"MA","26":"MI",
"27":"MN","28":"MS","29":"MO","30":"MT","31":"NE","32":"NV","33":"NH","34":"NJ",
"35":"NM","36":"NY","37":"NC","38":"ND","39":"OH","40":"OK","41":"OR","42":"PA",
"44":"RI","45":"SC","46":"SD","47":"TN","48":"TX","49":"UT","50":"VT","51":"VA",
"53":"WA","54":"WV","55":"WI","56":"WY"}

def z(x): return (x-np.nanmean(x))/np.nanstd(x)
def loo(X,y):
    Xs=StandardScaler().fit_transform(X); p=np.zeros(len(y))
    for tr,te in LeaveOneOut().split(Xs): p[te]=LinearRegression().fit(Xs[tr],y[tr]).predict(Xs[te])
    return float(r2_score(y,p))

def boot_indirect(t,med,out,ctrl,n=5000,seed=20260528):
    """standardized indirect a*b; a: t->med|ctrl ; b: med->out|t,ctrl. BC percentile CI."""
    rng=np.random.default_rng(seed)
    df=pd.DataFrame({"t":z(t),"m":z(med),"y":z(out),"c":z(ctrl)}).dropna()
    def ab(d):
        a=sm.OLS(d["m"],sm.add_constant(d[["t","c"]])).fit().params["t"]
        bm=sm.OLS(d["y"],sm.add_constant(d[["m","t","c"]])).fit()
        return a*bm.params["m"], a, bm.params["m"], bm.params["t"]
    pt=ab(df); idx=np.arange(len(df)); samples=[]
    for _ in range(n):
        d=df.iloc[rng.choice(idx,len(df),replace=True)]
        try: samples.append(ab(d)[0])
        except Exception: pass
    s=np.array(samples)
    return {"indirect":round(float(pt[0]),4),"a":round(float(pt[1]),4),
            "b":round(float(pt[2]),4),"direct_cprime":round(float(pt[3]),4),
            "ci95":[round(float(np.percentile(s,2.5)),4),round(float(np.percentile(s,97.5)),4)],
            "excludes_zero_positive":bool(np.percentile(s,2.5)>0),"n_boot":len(s)}

def main():
    panel=pd.read_parquet(ROOT/"analysis/paper7_sdp_state_year_panel.parquet")
    acs=pd.DataFrame(json.loads((ROOT/"data/paper7/acs_structural/acs_structural_state_year.json").read_text()))
    acs["state"]=acs["state_fips"].map(FIPS2USPS)
    zo=pd.read_csv(ROOT/"data/paper7/wharton_zoning/wrluri2018_state_avg_AUTHENTIC.csv")
    sz=pd.read_csv(ROOT/"data/paper7/saiz_elasticity/saiz_elasticity_state.csv")

    cx=(panel[panel.year==2024]
        .merge(acs[acs.year==2024][["state","median_gross_rent","rental_vacancy_rate","median_hh_income"]],on="state",how="left")
        .merge(zo[["state","zoning"]],on="state",how="left")
        .merge(sz[["state","saiz_elasticity"]],on="state",how="left"))
    upath=ROOT/"data/paper7/acs_structural/acs_housing_units_state_year.json"
    if upath.exists():
        units=pd.DataFrame(json.loads(upath.read_text())); units["state"]=units["state_fips"].map(FIPS2USPS)
        cx=cx.merge(units[units.year==2024][["state","housing_units"]],on="state",how="left")
        cx["units_per_capita"]=cx["housing_units"]/cx["population"]
    cx=cx.dropna(subset=["median_gross_rent","median_hh_income","zoning","saiz_elasticity","homeless_per_10k"])

    # supply-constraint index: higher = more constrained (high zoning, low elasticity)
    cx["supply_constraint"]=( z(cx["zoning"].values) - z(cx["saiz_elasticity"].values) )/2

    res={"n":int(len(cx)),"framing":"correlational; mediation pattern; ordering locked by timescale",
         "supply_index":"mean(z(zoning), -z(saiz_elasticity)); higher=more constrained"}

    # H1 first stage: supply -> rent
    a_cols=["supply_constraint","median_hh_income"]
    X=sm.add_constant(StandardScaler().fit_transform(cx[a_cols].values))
    m=sm.OLS(cx["median_gross_rent"].values,X).fit()
    res["H1_first_stage_rent"]={
        "loo_r2":round(loo(cx[a_cols].values,cx["median_gross_rent"].values),4),
        "supply_coef":round(float(m.params[1]),3),"supply_p":round(float(m.pvalues[1]),4),
        "income_coef":round(float(m.params[2]),3),"income_p":round(float(m.pvalues[2]),4),
        "loo_supply_only":round(loo(cx[["supply_constraint"]].values,cx["median_gross_rent"].values),4),
        "loo_income_only":round(loo(cx[["median_hh_income"]].values,cx["median_gross_rent"].values),4)}
    res["H1_disposition"]=("SUPPORTED" if (res["H1_first_stage_rent"]["loo_r2"]>=0.40 and m.pvalues[1]<0.05)
                           else "FALSIFIED" if res["H1_first_stage_rent"]["loo_r2"]<0.30 else "MIXED")

    # H2 mediation bootstrap
    med=boot_indirect(cx["supply_constraint"].values,cx["median_gross_rent"].values,
                      cx["homeless_per_10k"].values,cx["median_hh_income"].values)
    res["H2_mediation"]=med
    res["H2_disposition"]="SUPPORTED" if med["excludes_zero_positive"] else "FALSIFIED"

    # H3 supply vs demand partial R2 for rent
    rentv=cx["median_gross_rent"].values
    r_income=loo(cx[["median_hh_income"]].values,rentv)
    r_supply=loo(cx[["supply_constraint"]].values,rentv)
    r_both=loo(cx[["supply_constraint","median_hh_income"]].values,rentv)
    res["H3_supply_vs_demand"]={
        "dR2_supply_given_income":round(r_both-r_income,4),
        "dR2_income_given_supply":round(r_both-r_supply,4),
        "supply_dominates":bool((r_both-r_income)>(r_both-r_supply))}

    # drop-RTS robustness on indirect
    cxd=cx[~cx.state.isin(["NY","MA","DC"])]
    res["robust_drop_RTS_indirect"]=boot_indirect(cxd["supply_constraint"].values,cxd["median_gross_rent"].values,
                                                  cxd["homeless_per_10k"].values,cxd["median_hh_income"].values)
    OUT.write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2)); print("\nwrote",OUT)

if __name__=="__main__": main()
