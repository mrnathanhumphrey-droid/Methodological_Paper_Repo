"""
PRE_REG_031 — metro/CoC-level supply + demand -> rent -> homelessness mediation.

Powered version of PRE_REG_030 (n~300 CoCs vs 47 states). Parallel-treatment
mediation: supply_constraint AND demand(income) both -> rent -> homeless.
H2  (load-bearing): supply indirect CI excludes 0.
H2b (PI addition):  demand indirect CI excludes 0.
H3: which dominates. Correlational; ordering locked by timescale.

supply_constraint = mean( -z(saiz_elasticity), z(wrluri_coc) ); higher=more constrained.
Robustness: saiz-only supply. Mediator=rent. Control set rotates per path.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score

ROOT=Path(r"D:/IDP")
OUT=ROOT/"analysis/paper7_prereg031_results_2026_05_28.json"

def z(x): x=np.asarray(x,float); return (x-np.nanmean(x))/np.nanstd(x)

def kfold_r2(X,y,k=5,seed=20260528):
    Xs=StandardScaler().fit_transform(X); p=np.zeros(len(y)); kf=KFold(k,shuffle=True,random_state=seed)
    for tr,te in kf.split(Xs): p[te]=LinearRegression().fit(Xs[tr],y[tr]).predict(Xs[te])
    return float(r2_score(y,p))

def parallel_mediation(d, treatments, mediator, outcome, n=5000, seed=20260528):
    """d standardized. For each treatment T: a_T = T->M | other treatments;
       b = M->Y | all treatments; indirect_T = a_T*b. BC bootstrap CIs."""
    rng=np.random.default_rng(seed)
    cols=treatments+[mediator,outcome]
    D=d[cols].dropna().reset_index(drop=True)
    for c in cols: D[c]=z(D[c])
    def fit(df):
        # a-paths: mediator ~ all treatments
        am=sm.OLS(df[mediator],sm.add_constant(df[treatments])).fit()
        a={t:am.params[t] for t in treatments}
        # b-path: outcome ~ mediator + all treatments
        bm=sm.OLS(df[outcome],sm.add_constant(df[treatments+[mediator]])).fit()
        b=bm.params[mediator]
        return {t:a[t]*b for t in treatments}, a, b, {t:bm.params[t] for t in treatments}
    pt_ind,pt_a,pt_b,pt_direct=fit(D)
    idx=np.arange(len(D)); boot={t:[] for t in treatments}
    for _ in range(n):
        s=D.iloc[rng.choice(idx,len(D),replace=True)]
        try:
            ind,_,_,_=fit(s)
            for t in treatments: boot[t].append(ind[t])
        except Exception: pass
    res={}
    for t in treatments:
        arr=np.array(boot[t]); lo,hi=np.percentile(arr,[2.5,97.5])
        res[t]={"indirect":round(float(pt_ind[t]),4),"a":round(float(pt_a[t]),4),
                "b":round(float(pt_b),4),"direct":round(float(pt_direct[t]),4),
                "ci95":[round(float(lo),4),round(float(hi),4)],
                "excludes_zero":bool(lo>0 or hi<0),"n_boot":len(arr)}
    return res,len(D)

def main():
    p=pd.read_csv(ROOT/"analysis/paper7_metro_coc_panel_2024.csv")
    p["supply_saiz"]=-z(p["saiz_elasticity"])         # higher=more constrained
    p["supply_composite"]=np.nanmean(np.column_stack([-z(p["saiz_elasticity"]),z(p["wrluri_coc"])]),axis=1)
    res={"pre_reg":"PRE_REG_031","framing":"correlational; parallel mediation; ordering locked by timescale",
         "panel":"CoC 2024; ACS5yr county->CoC; Saiz MSA->CoC (88.8% match); WRLURI county->CoC"}

    # ---- H1 first stages: supply->rent, demand->rent ----
    base=p.dropna(subset=["rent_coc","income_coc","saiz_elasticity"])
    X=sm.add_constant(StandardScaler().fit_transform(base[["supply_saiz","income_coc"]].values))
    m=sm.OLS(base["rent_coc"].values,X).fit()
    res["H1_first_stage_rent"]={"n":int(len(base)),
        "loo5_r2":round(kfold_r2(base[["supply_saiz","income_coc"]].values,base["rent_coc"].values),4),
        "supply_coef":round(float(m.params[1]),3),"supply_p":round(float(m.pvalues[1]),4),
        "income_coef":round(float(m.params[2]),3),"income_p":round(float(m.pvalues[2]),4)}
    res["H1_disposition"]=("SUPPORTED" if (res["H1_first_stage_rent"]["loo5_r2"]>=0.40 and m.pvalues[1]<0.05 and m.pvalues[2]<0.05) else "MIXED")

    # ---- H2 + H2b: parallel mediation (supply_saiz + income) -> rent -> homeless ----
    med_saiz,n1=parallel_mediation(p,["supply_saiz","income_coc"],"rent_coc","homeless_per_10k")
    res["H2_H2b_mediation_saiz_supply"]={"n":n1,
        "supply_indirect":med_saiz["supply_saiz"],"demand_indirect":med_saiz["income_coc"]}
    res["H2_supply_disposition"]="SUPPORTED" if med_saiz["supply_saiz"]["excludes_zero"] and med_saiz["supply_saiz"]["indirect"]>0 else "FALSIFIED"
    res["H2b_demand_disposition"]="SUPPORTED" if med_saiz["income_coc"]["excludes_zero"] and med_saiz["income_coc"]["indirect"]>0 else "FALSIFIED"

    # robustness: composite supply (saiz+wrluri)
    med_comp,n2=parallel_mediation(p,["supply_composite","income_coc"],"rent_coc","homeless_per_10k")
    res["robust_composite_supply"]={"n":n2,"supply_indirect":med_comp["supply_composite"],"demand_indirect":med_comp["income_coc"]}

    # robustness: drop NYC+LA
    p2=p[~p.coc_number.isin(["NY-600","CA-600"])]
    med_drop,n3=parallel_mediation(p2,["supply_saiz","income_coc"],"rent_coc","homeless_per_10k")
    res["robust_drop_NYC_LA"]={"n":n3,"supply_indirect":med_drop["supply_saiz"],"demand_indirect":med_drop["income_coc"]}

    # robustness: outcome = unsheltered_per_10k
    med_uns,n4=parallel_mediation(p,["supply_saiz","income_coc"],"rent_coc","unsheltered_per_10k")
    res["robust_unsheltered_outcome"]={"n":n4,"supply_indirect":med_uns["supply_saiz"],"demand_indirect":med_uns["income_coc"]}

    # ---- H3 dominance ----
    si=med_saiz["supply_saiz"]["indirect"]; di=med_saiz["income_coc"]["indirect"]
    res["H3_dominance"]={"supply_indirect":si,"demand_indirect":di,
        "dominant":("supply" if abs(si)>abs(di) else "demand"),
        "both_significant":bool(med_saiz["supply_saiz"]["excludes_zero"] and med_saiz["income_coc"]["excludes_zero"])}
    OUT.write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2)); print("\nwrote",OUT)

if __name__=="__main__": main()
