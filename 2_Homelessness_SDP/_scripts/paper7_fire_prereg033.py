"""
PRE_REG_033 — culture-wars push test. Does a culture/politics/social-fabric block
explain homelessness NET OF RENT (cross-section) and does CHANGING culture drive
CHANGING homelessness (dynamic)? PI prior: it does NOT (it's rent).

H1 cross-section: culture dLOO-R2 over (rent+income). F1 if <0.05.
H2 dynamic: d_homeless ~ d_rent + d_income + d_dem_share + d_single_person.
Correlational. push=cultural would SURPRISE PI; null CONFIRMS.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import r2_score

ROOT=Path(r"D:/IDP"); OUT=ROOT/"analysis/paper7_prereg033_results_2026_05_28.json"
def loo(X,y):
    Xs=StandardScaler().fit_transform(X); p=np.zeros(len(y))
    for tr,te in LeaveOneOut().split(Xs): p[te]=LinearRegression().fit(Xs[tr],y[tr]).predict(Xs[te])
    return float(r2_score(y,p))
def ols(y,Xc,d):
    X=sm.add_constant(StandardScaler().fit_transform(d[Xc].values))
    m=sm.OLS(d[y].values,X).fit()
    return {Xc[i]:{"coef":round(float(m.params[i+1]),3),"p":round(float(m.pvalues[i+1]),4)} for i in range(len(Xc))}, round(float(m.rsquared),3)

def main():
    c=pd.read_csv(ROOT/"analysis/paper7_culture_block_coc.csv")
    c=c.loc[:,~c.columns.str.endswith('.1')]
    m=pd.read_csv(ROOT/"analysis/paper7_metro_coc_panel_2024.csv").merge(c,on="coc_number",how="inner")
    econ=["rent_coc","income_coc"]
    culture=["dem_share_2020","single_person_hh_share_2024","never_married_share_2024","social_capital_index"]
    d=m.dropna(subset=["homeless_per_10k"]+econ+culture)
    res={"pre_reg":"PRE_REG_033","framing":"correlational; PI prior=culture push does NOT exist",
         "religiosity":"NOT obtained (ARDA JS-gated) - culture block = politics+family+social-capital"}
    y=d["homeless_per_10k"].values
    r_econ=loo(d[econ].values,y); r_full=loo(d[econ+culture].values,y)
    cult_co,_=ols("homeless_per_10k",econ+culture,d)
    res["H1_cross_section"]={"n":int(len(d)),
        "loo_econ_only":round(r_econ,4),"loo_econ_plus_culture":round(r_full,4),
        "dR2_culture_over_econ":round(r_full-r_econ,4),
        "culture_coefs_net_of_rent":{k:cult_co[k] for k in culture},
        "raw_dem_corr":round(float(np.corrcoef(d["dem_share_2020"],y)[0,1]),3)}
    res["H1_disposition"]=("CULTURE PUSH EXISTS" if (r_full-r_econ)>=0.10 else
                           "FALSIFIED (no cultural push net of rent)" if (r_full-r_econ)<0.05 else "MIXED")
    # H2 dynamic
    ld=pd.read_csv(ROOT/"analysis/paper7_coc_longdiff_2012_2024.csv").merge(
        c[["coc_number","d_dem_share","d_single_person"]],on="coc_number",how="inner")
    dd=ld.dropna(subset=["d_homeless","d_rent","d_income","d_dem_share","d_single_person"])
    dco,dr2=ols("d_homeless",["d_rent","d_income","d_dem_share","d_single_person"],dd)
    res["H2_dynamic"]={"n":int(len(dd)),"model_r2":dr2,"coefs":dco,
        "changing_culture_pushes":bool(dco["d_dem_share"]["p"]<0.05 or dco["d_single_person"]["p"]<0.05)}
    res["H2_disposition"]=("CHANGING CULTURE PUSHES" if res["H2_dynamic"]["changing_culture_pushes"]
                           else "FALSIFIED (changing culture does not push)")
    # robustness: drop NYC/LA/SF + political-only
    d2=d[~d.coc_number.isin(["NY-600","CA-600","CA-501"])]
    r_e2=loo(d2[econ].values,d2["homeless_per_10k"].values); r_f2=loo(d2[econ+culture].values,d2["homeless_per_10k"].values)
    res["robust_drop_big3"]={"n":int(len(d2)),"dR2_culture":round(r_f2-r_e2,4)}
    polco,_=ols("homeless_per_10k",econ+["dem_share_2020"],d)
    res["robust_politics_net_of_rent"]={"dem_coef":polco["dem_share_2020"],
        "dR2_politics_over_econ":round(loo(d[econ+["dem_share_2020"]].values,y)-r_econ,4)}
    OUT.write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2)); print("\nwrote",OUT)

if __name__=="__main__": main()
