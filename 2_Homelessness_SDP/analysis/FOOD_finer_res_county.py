"""
FOOD-edge finer-res: trapped-push at COUNTY level (n~3100) with STATE FIXED EFFECTS.

State-level (n=51) showed food_insec->outmig -0.37 (trap) but poverty->outmig null.
County food insecurity = Map the Meal Gap (gated, not on disk), so here we use the
on-disk deprivation driver (poverty) + food-access floor (FARA), and ask the WITHIN-STATE
question state-level couldn't: do higher-deprivation counties out-migrate LESS than other
counties in the same state? State FE removes all state-level confounds.

Outcome: out-of-county out-migration rate (IRS, sentinel n2<=0 filtered) / county pop.
Output: analysis/FOOD_finer_res_county.json
"""
from __future__ import annotations
import glob, json
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.formula.api as smf

IDP = Path(r"D:\IDP")
IRS = r"D:\Migration\data\raw\irs_soi\countyoutflow{}.csv"
FARA_ZIP = r"D:\Food Deserts\data_raw\FARA\2019_Food_Access_Research_Atlas_Data.zip"
FEAX = r"D:\Food Deserts\data_raw\FEA\2025-food-environment-atlas-data.xlsx"
YEARS = ["1213","1314","1415","1516","1617","1718","1819","1920","2021","2122"]


def main():
    # IRS out-of-county out-migration per origin county (sentinel-filtered)
    parts, supp = [], 0
    for yy in YEARS:
        f = IRS.format(yy)
        if not glob.glob(f):
            continue
        d = pd.read_csv(f, encoding="latin-1", dtype={"y1_statefips":int,"y1_countyfips":int,"y2_statefips":int,"y2_countyfips":int})
        supp += int((d.n2 <= 0).sum())
        d = d[(d.y1_countyfips!=0)&(d.y2_countyfips!=0)&(d.y2_statefips.between(1,56))&(d.n2>0)]
        ooc = d[~((d.y1_statefips==d.y2_statefips)&(d.y1_countyfips==d.y2_countyfips))]
        ooc = ooc.assign(fips=ooc.y1_statefips*1000+ooc.y1_countyfips)
        parts.append(ooc.groupby("fips").n2.sum().rename(yy))
    irs = pd.concat(parts, axis=1)
    irs = irs.mean(axis=1).rename("ooc_annual").reset_index()

    # county pop + food-access floor (FARA)
    import zipfile
    with zipfile.ZipFile(FARA_ZIP) as z, z.open("Food Access Research Atlas.csv") as fp:
        fara = pd.read_csv(fp, usecols=["CensusTract","Pop2010","LAPOP1_10"], dtype={"CensusTract":str})
    fara["fips"]=fara.CensusTract.str.zfill(11).str[:5].astype(int)
    for c in ["Pop2010","LAPOP1_10"]: fara[c]=pd.to_numeric(fara[c],errors="coerce").fillna(0.0)
    cf = fara.groupby("fips").agg(pop=("Pop2010","sum"), la=("LAPOP1_10","sum")).reset_index()
    cf["food_floor"]=cf.la/cf["pop"].replace(0,np.nan)

    # county poverty + metro (FEA, sentinel-filtered)
    soc=pd.read_excel(FEAX,sheet_name="SOCIOECONOMIC",header=1)[["FIPS","POVRATE21","METRO23"]].rename(columns={"FIPS":"fips"})
    soc["poverty"]=pd.to_numeric(soc.POVRATE21,errors="coerce").where(lambda x:(x>=0)&(x<=100))
    soc["metro"]=pd.to_numeric(soc.METRO23,errors="coerce")

    M=irs.merge(cf[["fips","pop","food_floor"]],on="fips").merge(soc[["fips","poverty","metro"]],on="fips")
    M=M[(M["pop"]>0)].dropna(subset=["ooc_annual","poverty","food_floor","metro"])
    M["outmig_per1k"]=1000*M.ooc_annual/M["pop"]
    M=M[(M.outmig_per1k>0)&(M.outmig_per1k<1000)]      # drop degenerate
    M["state"]=(M.fips//1000).astype(int)
    M["log_outmig"]=np.log(M.outmig_per1k)

    out={"n_counties":int(len(M)),"irs_suppressed_filtered":int(supp),
         "outmig_per1k_median":round(float(M.outmig_per1k.median()),1)}
    # raw (no FE) vs within-state (state FE)
    r0=smf.ols("log_outmig ~ poverty + food_floor + metro", data=M).fit(cov_type="HC1")
    rFE=smf.ols("log_outmig ~ poverty + food_floor + metro + C(state)", data=M).fit(cov_type="cluster",cov_kwds={"groups":M.state})
    def grab(r,ks): return {k:{"b":round(float(r.params[k]),4),"p":round(float(r.pvalues[k]),4)} for k in ks}
    out["raw_no_FE"]=grab(r0,["poverty","food_floor","metro"]) | {"r2":round(float(r0.rsquared),3)}
    out["within_state_FE"]=grab(rFE,["poverty","food_floor","metro"]) | {"r2":round(float(rFE.rsquared),3)}
    # simple within-state correlation of poverty vs outmig (partial out state means)
    M["pov_demean"]=M.poverty-M.groupby("state").poverty.transform("mean")
    M["om_demean"]=M.log_outmig-M.groupby("state").log_outmig.transform("mean")
    from scipy import stats
    rw,pw=stats.pearsonr(M.pov_demean,M.om_demean)
    out["within_state_partial_corr_poverty_outmig"]={"r":round(float(rw),3),"p":round(float(pw),6)}

    (IDP/"analysis"/"FOOD_finer_res_county.json").write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))


if __name__=="__main__":
    main()
