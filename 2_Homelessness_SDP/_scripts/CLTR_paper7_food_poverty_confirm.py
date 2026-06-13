"""
CLTR tie-up #2 — is food insecurity a rent-precarity vent, or does it just ride POVERTY?
PRE_REG_039 D1 found precarity(behind_on_rent)->food +0.33. Leaf-2 (county) found food=poverty, access n.s.
TEST: does precarity->food survive controlling for poverty? If it vanishes net of poverty, 039 D1 was a
poverty confound and food sits on the poverty axis (not the rent-soft branch). State n~50. Correlational.
"""
import json
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy.stats import pearsonr
ROOT = Path(r"D:/IDP"); FD = Path(r"D:/Food Deserts/data_raw")
OUT = ROOT/"analysis/CLTR_paper7_food_poverty_confirm_2026_05_29.json"
AB=set(['AL','AK','AZ','AR','CA','CO','CT','DE','DC','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY'])

ins=pd.read_excel(FD/"FEA/2025-food-environment-atlas-data.xlsx",sheet_name="INSECURITY",skiprows=1)
ins["FOODINSEC_21_23"]=pd.to_numeric(ins["FOODINSEC_21_23"],errors="coerce"); ins.loc[ins.FOODINSEC_21_23<0,"FOODINSEC_21_23"]=np.nan
food=ins.groupby("State")["FOODINSEC_21_23"].mean().rename("food_insec")
soc=pd.read_excel(FD/"FEA/2025-food-environment-atlas-data.xlsx",sheet_name="SOCIOECONOMIC",skiprows=1)
soc["FIPS5"]=soc["FIPS"].apply(lambda x:str(int(x)).zfill(5)); soc["POVRATE21"]=pd.to_numeric(soc["POVRATE21"],errors="coerce"); soc.loc[soc.POVRATE21<0,"POVRATE21"]=np.nan
acs=pd.read_json(ROOT/"data/paper7/demand_drivers/acs5_2024_B01003_county.json"); acs.columns=acs.iloc[0]; acs=acs.iloc[1:]
acs["FIPS5"]=acs["state"].str.zfill(2)+acs["county"].str.zfill(3); acs["pop"]=pd.to_numeric(acs["B01003_001E"],errors="coerce")
soc=soc.merge(acs[["FIPS5","pop"]],on="FIPS5",how="left").dropna(subset=["POVRATE21","pop"])
pov=(soc.assign(wp=soc.POVRATE21*soc["pop"]).groupby("State").apply(lambda g:g.wp.sum()/g["pop"].sum()).rename("poverty"))
pu=pd.read_csv(ROOT/"analysis/paper7_pulse_housing_precarity.csv"); pu=pu[pu.geo_type=="state"]
behind=pu.groupby("geography")["behind_on_rent_share"].mean().rename("behind_on_rent")
ev=pu.groupby("geography")["eviction_risk_share"].mean().rename("eviction_risk")
d=pd.concat([food,pov,behind,ev],axis=1).reset_index().rename(columns={"index":"state"})
d=d[d.state.isin(AB)].dropna(subset=["food_insec","poverty","behind_on_rent","eviction_risk"])

def z(s): return (s-s.mean())/s.std()
def ols(y,xs):
    Z=pd.DataFrame({x:z(d[x]) for x in xs}); m=sm.OLS(d[y].values,sm.add_constant(Z.values)).fit()
    return {xs[i]:{"std_b":round(float(m.params[i+1]),3),"p":round(float(m.pvalues[i+1]),4)} for i in range(len(xs))}, round(float(m.rsquared),3)

res={"pre_reg":"CLTR_food_poverty_confirm","n":int(len(d)),
 "bivariate": {
   "precarity_behind_to_food_r": round(float(pearsonr(d.behind_on_rent,d.food_insec)[0]),3),
   "precarity_evrisk_to_food_r": round(float(pearsonr(d.eviction_risk,d.food_insec)[0]),3),
   "poverty_to_food_r": round(float(pearsonr(d.poverty,d.food_insec)[0]),3)},
}
m1,r1=ols("food_insec",["behind_on_rent","poverty"])
m2,r2=ols("food_insec",["eviction_risk","poverty"])
res["food~behind+poverty"]={"R2":r1,"coefs":m1}
res["food~evrisk+poverty"]={"R2":r2,"coefs":m2}
precarity_survives = (m1["behind_on_rent"]["p"]<0.05) or (m2["eviction_risk"]["p"]<0.05)
poverty_dominates = (m1["poverty"]["p"]<0.05 and abs(m1["poverty"]["std_b"])>abs(m1["behind_on_rent"]["std_b"]))
res["VERDICT"]=("CONFIRMED: food rides POVERTY, not rent-precarity — precarity->food vanishes net of poverty (039 D1 was a poverty confound); food sits on the poverty axis, NOT the rent-soft branch"
   if (not precarity_survives and poverty_dominates) else
   "MIXED — precarity retains independent association net of poverty; food may have a rent-precarity component")
res["precarity_survives_net_of_poverty"]=bool(precarity_survives)
res["poverty_dominates"]=bool(poverty_dominates)
OUT.write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2)); print("\nwrote",OUT)
