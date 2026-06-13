"""
P7-O REDO with AUTHENTIC WRLURI 2018 microdata (replaces hand-coded probe).

Source: Gyourko faculty page -> Dropbox WHARTON-LAND-REGULATION-DATA_01_15_2020.dta
(2,844 communities; 2,472 with valid WRLURI18). State average = weight_full-weighted
community mean (the paper's nationally-representative weight). HI + DC NOT in the
2018 survey (n=0) -> genuinely missing, not imputed.

Test (PRE_REG_029 P7-O): does AUTHENTIC zoning explain the homelessness LEVEL, and
crucially SURVIVE dropping the right-to-shelter states (NY/MA/DC) where rent did not?
Correlational only.
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

ROOT = Path(r"D:/IDP")
DTA = ROOT/"data/paper7/wharton_zoning/WHARTON-LAND-REGULATION-DATA_01_15_2020.dta"
OUT = ROOT/"analysis/paper7_probe_zoning_AUTHENTIC_2026_05_28.json"
CSV = ROOT/"data/paper7/wharton_zoning/wrluri2018_state_avg_AUTHENTIC.csv"
FIPS2USPS={"01":"AL","02":"AK","04":"AZ","05":"AR","06":"CA","08":"CO","09":"CT",
"10":"DE","11":"DC","12":"FL","13":"GA","15":"HI","16":"ID","17":"IL","18":"IN",
"19":"IA","20":"KS","21":"KY","22":"LA","23":"ME","24":"MD","25":"MA","26":"MI",
"27":"MN","28":"MS","29":"MO","30":"MT","31":"NE","32":"NV","33":"NH","34":"NJ",
"35":"NM","36":"NY","37":"NC","38":"ND","39":"OH","40":"OK","41":"OR","42":"PA",
"44":"RI","45":"SC","46":"SD","47":"TN","48":"TX","49":"UT","50":"VT","51":"VA",
"53":"WA","54":"WV","55":"WI","56":"WY"}

def loo_r2(X,y):
    Xs=StandardScaler().fit_transform(X); p=np.zeros(len(y))
    for tr,te in LeaveOneOut().split(Xs): p[te]=LinearRegression().fit(Xs[tr],y[tr]).predict(Xs[te])
    return float(r2_score(y,p))

def main():
    df=pd.read_stata(DTA).dropna(subset=["WRLURI18"])
    df["w"]=df["weight_full"].fillna(0)
    def wm(g):
        return np.average(g["WRLURI18"],weights=g["w"]) if g["w"].sum()>0 else g["WRLURI18"].mean()
    agg=df.groupby("statecode_str").apply(wm,include_groups=False)
    n=df.groupby("statecode_str").size()
    z=pd.DataFrame({"fips":agg.index,"zoning":agg.values,"n_communities":n.values})
    z["state"]=z["fips"].map(FIPS2USPS)
    z=z[z["state"].notna()]
    z[["state","zoning","n_communities"]].sort_values("zoning",ascending=False).to_csv(CSV,index=False)

    panel=pd.read_parquet(ROOT/"analysis/paper7_sdp_state_year_panel.parquet")
    acs=pd.DataFrame(json.loads((ROOT/"data/paper7/acs_structural/acs_structural_state_year.json").read_text()))
    acs["state"]=acs["state_fips"].map(FIPS2USPS)
    import importlib.util
    spec=importlib.util.spec_from_file_location("pb",str(ROOT/"_scripts/paper7_policy_block.py"))
    pb=importlib.util.module_from_spec(spec); spec.loader.exec_module(pb)

    cx=panel[panel.year==2024].merge(
        acs[acs.year==2024][["state","median_gross_rent","rental_vacancy_rate","median_hh_income"]],
        on="state",how="left").merge(pb.policy_frame()[["state","jan_temp"]],on="state",how="left")\
        .merge(z[["state","zoning","n_communities"]],on="state",how="left")
    res={"probe":"P7-O AUTHENTIC WRLURI2018","framing":"correlational only",
         "data":"Gyourko Dropbox .dta; weight_full-weighted state mean; HI+DC absent from survey",
         "top5_states":z.nlargest(5,"zoning")[["state","zoning","n_communities"]].to_dict("records"),
         "bottom5_states":z.nsmallest(5,"zoning")[["state","zoning","n_communities"]].to_dict("records")}

    cols=["homeless_per_10k","zoning","median_gross_rent","rental_vacancy_rate","jan_temp"]
    for label,frame in [("full",cx),("drop_RTS",cx[~cx.state.isin(["NY","MA","DC"])])]:
        d=frame.dropna(subset=cols)
        y=d["homeless_per_10k"].values
        r={"n":int(len(d)),
           "loo_climate":round(loo_r2(d[["jan_temp"]].values,y),4),
           "loo_climate+rent":round(loo_r2(d[["jan_temp","median_gross_rent"]].values,y),4),
           "loo_climate+zoning":round(loo_r2(d[["jan_temp","zoning"]].values,y),4),
           "loo_climate+zoning+rent":round(loo_r2(d[["jan_temp","zoning","median_gross_rent"]].values,y),4)}
        X=sm.add_constant(StandardScaler().fit_transform(d[["zoning","median_gross_rent","rental_vacancy_rate","jan_temp"]].values))
        m=sm.OLS(y,X).fit()
        nm=["const","zoning","rent","vacancy","jan_temp"]
        r["ols"]={nm[i]:{"coef":round(float(m.params[i]),3),"p":round(float(m.pvalues[i]),4)} for i in range(len(nm))}
        r["ols_r2"]=round(float(m.rsquared),4)
        res[label]=r

    zc_full=res["full"]["ols"]["zoning"]; zc_drop=res["drop_RTS"]["ols"]["zoning"]
    survives=(zc_drop["coef"]>0 and zc_drop["p"]<0.10 and
              res["drop_RTS"]["loo_climate+zoning"]>res["drop_RTS"]["loo_climate"]+0.05)
    res["disposition"]={
        "zoning_full":zc_full,"zoning_drop_RTS":zc_drop,
        "survives_drop_RTS":bool(survives),
        "verdict":("AUTHENTIC zoning explains LEVEL and SURVIVES drop-RTS" if survives
                   else "AUTHENTIC zoning does NOT robustly survive drop-RTS — level stays fragile")}
    OUT.write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2)); print("\nwrote",OUT,CSV)

if __name__=="__main__": main()
