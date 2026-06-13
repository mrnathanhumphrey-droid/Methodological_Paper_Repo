"""
CLTR fractal leaf 2 at COUNTY resolution — does food insecurity split into rural-access vs urban-income?
Outcome: MMG county Overall Food Insecurity Rate (2023; 2021-23 for validation/stability).
Drivers: FEA POVRATE21 (county), FARA LAPOP1_10/Pop2010 (tract->county access), RUCC2023 (rural>=4).
Rules locked in CLTR_PRE_REG_fractal_leaf2_county_2026_05_29.md. Correlational; ecological (county).
"""
import json
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy.stats import pearsonr
ROOT = Path(r"D:/IDP"); FD = Path(r"D:/Food Deserts/data_raw")
OUT = ROOT/"analysis/CLTR_paper7_leaf2_county_results_2026_05_29.json"
NAME2AB = {'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA','Colorado':'CO','Connecticut':'CT','Delaware':'DE','District of Columbia':'DC','Florida':'FL','Georgia':'GA','Hawaii':'HI','Idaho':'ID','Illinois':'IL','Indiana':'IN','Iowa':'IA','Kansas':'KS','Kentucky':'KY','Louisiana':'LA','Maine':'ME','Maryland':'MD','Massachusetts':'MA','Michigan':'MI','Minnesota':'MN','Mississippi':'MS','Missouri':'MO','Montana':'MT','Nebraska':'NE','Nevada':'NV','New Hampshire':'NH','New Jersey':'NJ','New Mexico':'NM','New York':'NY','North Carolina':'NC','North Dakota':'ND','Ohio':'OH','Oklahoma':'OK','Oregon':'OR','Pennsylvania':'PA','Rhode Island':'RI','South Carolina':'SC','South Dakota':'SD','Tennessee':'TN','Texas':'TX','Utah':'UT','Vermont':'VT','Virginia':'VA','Washington':'WA','West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY'}

# ---- MMG county ----
mmg = pd.read_excel(ROOT/"data/paper7/mmg/MMG2025_2019-2023_Data_To_Share.xlsx", sheet_name="County")
mmg.columns = [str(c) for c in mmg.columns]
FI=[c for c in mmg.columns if "Overall Food Insecurity Rate" in c][0]
NFI=[c for c in mmg.columns if "Food Insecure Persons Overall" in c][0]
RUCC=[c for c in mmg.columns if "Continuum Code (2023)" in c][0]
mmg["FIPS5"]=mmg["FIPS"].astype(int).astype(str).str.zfill(5)
mmg["fi_pct"]=mmg[FI]*100.0
mmg["pop_est"]=mmg[NFI]/mmg[FI]            # implied population
mmg["rural"]=(mmg[RUCC]>=4).astype(int)
mmg["ab"]=mmg["State"].map(lambda s: NAME2AB.get(s, s if s in NAME2AB.values() else None))

# ---- FEA poverty (county) ----
soc=pd.read_excel(FD/"FEA/2025-food-environment-atlas-data.xlsx", sheet_name="SOCIOECONOMIC", skiprows=1)
soc["FIPS5"]=soc["FIPS"].apply(lambda x: str(int(x)).zfill(5))
soc["POVRATE21"]=pd.to_numeric(soc["POVRATE21"],errors="coerce")
soc.loc[soc.POVRATE21<0,"POVRATE21"]=np.nan
pov=soc[["FIPS5","POVRATE21"]].rename(columns={"POVRATE21":"poverty"})

# ---- FARA access (tract -> county) ----
fara=pd.read_excel(FD/"FARA/FoodAccessResearchAtlasData2019.xlsx", sheet_name="Food Access Research Atlas",
                   usecols=["CensusTract","Pop2010","LAPOP1_10"])
fara["FIPS5"]=fara["CensusTract"].astype(np.int64).astype(str).str.zfill(11).str[:5]
acc=fara.groupby("FIPS5").apply(lambda g: g.LAPOP1_10.sum()/g.Pop2010.sum()).rename("access").reset_index()

# ===== VALIDATION: county FI 2021-23 -> state, vs FEA FOODINSEC_21_23 =====
ins=pd.read_excel(FD/"FEA/2025-food-environment-atlas-data.xlsx", sheet_name="INSECURITY", skiprows=1)
ins["FOODINSEC_21_23"]=pd.to_numeric(ins["FOODINSEC_21_23"],errors="coerce")
ins.loc[ins.FOODINSEC_21_23<0,"FOODINSEC_21_23"]=np.nan
fea_state=ins.groupby("State")["FOODINSEC_21_23"].mean()
v=mmg[mmg.Year.isin([2021,2022,2023])].dropna(subset=["ab","fi_pct","pop_est"])
st_year=v.groupby(["ab","Year"]).apply(lambda g: np.average(g.fi_pct,weights=g.pop_est))
st_mmg=st_year.groupby(level=0).mean()
val=pd.concat([st_mmg.rename("mmg"),fea_state.rename("fea")],axis=1).dropna()
val=val[val.index.isin(NAME2AB.values())]
vr,vp=pearsonr(val.mmg,val.fea)
validation={"n_states":int(len(val)),"pearson_r":round(float(vr),4),
    "mean_abs_diff_pp":round(float((val.mmg-val.fea).abs().mean()),2),
    "ok": bool(vr>0.95)}

# ===== SPLIT TEST (2023) =====
d=mmg[mmg.Year==2023][["FIPS5","fi_pct","rural",RUCC]].merge(pov,on="FIPS5",how="inner").merge(acc,on="FIPS5",how="inner")
d=d.dropna(subset=["fi_pct","poverty","access","rural"])
def z(s): return (s-s.mean())/s.std()
def fit(df,xs):
    Z=pd.DataFrame({x:z(df[x]) for x in xs},index=df.index)
    m=sm.OLS(df["fi_pct"].values, sm.add_constant(Z.values)).fit(cov_type="HC1")
    return {xs[i]:{"b":round(float(m.params[i+1]),3),"p":round(float(m.pvalues[i+1]),4)} for i in range(len(xs))}, round(float(m.rsquared),3)
# full interaction model
dd=d.copy(); dd["zp"]=z(dd.poverty); dd["za"]=z(dd.access)
dd["zpR"]=dd.zp*dd.rural; dd["zaR"]=dd.za*dd.rural
mf=sm.OLS(dd.fi_pct.values, sm.add_constant(dd[["zp","za","rural","zpR","zaR"]].values)).fit(cov_type="HC1")
nm=["poverty","access","rural","poverty_x_rural","access_x_rural"]
full={nm[i]:{"b":round(float(mf.params[i+1]),3),"p":round(float(mf.pvalues[i+1]),4)} for i in range(5)}
# subsamples
metro=d[d.rural==0]; nonmetro=d[d.rural==1]
mc,mr=fit(metro,["poverty","access"]); nc,nr=fit(nonmetro,["poverty","access"])

F2_D1=(mc["poverty"]["b"]>0 and mc["poverty"]["p"]<0.05) and (nc["poverty"]["b"]>0 and nc["poverty"]["p"]<0.05)
F2_D2=(full["access_x_rural"]["b"]>0 and full["access_x_rural"]["p"]<0.05) and (nc["access"]["b"]>mc["access"]["b"])

# stability
stab={}
for y in [2021,2022,2023]:
    dy=mmg[mmg.Year==y][["FIPS5","fi_pct","rural"]].merge(pov,on="FIPS5").merge(acc,on="FIPS5").dropna()
    dy["zp"]=z(dy.poverty); dy["za"]=z(dy.access); dy["zaR"]=dy.za*dy.rural; dy["zpR"]=dy.zp*dy.rural
    my=sm.OLS(dy.fi_pct.values, sm.add_constant(dy[["zp","za","rural","zpR","zaR"]].values)).fit(cov_type="HC1")
    stab[str(y)]={"access_x_rural_b":round(float(my.params[5]),3),"p":round(float(my.pvalues[5]),4),"n":int(len(dy))}

res={"pre_reg":"CLTR_fractal_leaf2_county","framing":"correlational; ecological (county); n large -> judge effect size",
 "validation_mmg_vs_fea":validation,
 "n_counties_2023":int(len(d)),
 "full_interaction_model":full,
 "metro_subsample":{"n":int(len(metro)),"R2":mr,"std_coefs":mc,"dominant":"poverty" if abs(mc["poverty"]["b"])>abs(mc["access"]["b"]) else "access"},
 "nonmetro_subsample":{"n":int(len(nonmetro)),"R2":nr,"std_coefs":nc,"dominant":"poverty" if abs(nc["poverty"]["b"])>abs(nc["access"]["b"]) else "access"},
 "F2_D1_income_universal":bool(F2_D1),
 "F2_D2_access_rural_specific":bool(F2_D2),
 "FRACTAL_SPLIT":bool(F2_D1 and F2_D2),
 "stability_access_x_rural":stab,
 "disposition":("FRACTAL-SPLIT: food insecurity decomposes into urban-income + rural-access sub-leaves (distinct rules)"
   if (F2_D1 and F2_D2) else
   "TERMINAL: food insecurity is poverty-ruled in both metro and nonmetro; access not a distinct rural channel (leaf does not split)")}
OUT.write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2)); print("\nwrote",OUT)
