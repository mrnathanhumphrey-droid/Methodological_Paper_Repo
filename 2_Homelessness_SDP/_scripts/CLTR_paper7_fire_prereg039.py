"""
PRE_REG_039 — Seam closure: two discharge axes of one displacement system.
State level (n~51). All decision rules + data pinned by the locked pre-reg.

CLOSE_D1: corr(precarity, food_insec) > 0, p<0.05
CLOSE_D2: corr(precarity, homeless_per_10k) NOT significantly positive
CLOSE_D3: corr(food_insec, homeless_per_10k) <= 0 (NOT significantly positive)
CLOSE_D4: homeless ~ rent_floor + poverty  -> rent_floor pos & sig
          food_insec ~ poverty + food_floor + rent_floor -> (poverty|food_floor) pos&sig AND rent_floor NOT sig
SEAM_CLOSED = D1 & D2 & D3 & D4.   Correlational; cross-sectional; state resolution.
"""
import json
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy.stats import pearsonr

ROOT = Path(r"D:/IDP"); FD = Path(r"D:/Food Deserts/data_raw")
OUT = ROOT/"analysis/CLTR_paper7_prereg039_results_2026_05_29.json"

NAME2AB = {'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA','Colorado':'CO',
'Connecticut':'CT','Delaware':'DE','District of Columbia':'DC','Florida':'FL','Georgia':'GA','Hawaii':'HI',
'Idaho':'ID','Illinois':'IL','Indiana':'IN','Iowa':'IA','Kansas':'KS','Kentucky':'KY','Louisiana':'LA',
'Maine':'ME','Maryland':'MD','Massachusetts':'MA','Michigan':'MI','Minnesota':'MN','Mississippi':'MS',
'Missouri':'MO','Montana':'MT','Nebraska':'NE','Nevada':'NV','New Hampshire':'NH','New Jersey':'NJ',
'New Mexico':'NM','New York':'NY','North Carolina':'NC','North Dakota':'ND','Ohio':'OH','Oklahoma':'OK',
'Oregon':'OR','Pennsylvania':'PA','Rhode Island':'RI','South Carolina':'SC','South Dakota':'SD',
'Tennessee':'TN','Texas':'TX','Utah':'UT','Vermont':'VT','Virginia':'VA','Washington':'WA',
'West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY'}

def corr(a, b):
    m = a.notna() & b.notna()
    r, p = pearsonr(a[m], b[m])
    return round(float(r), 4), round(float(p), 4), int(m.sum())

def ols(df, y, xs):
    d = df.dropna(subset=[y]+xs)
    X = sm.add_constant(d[xs]); m = sm.OLS(d[y], X).fit()
    return {x: {"coef": round(float(m.params[x]), 4), "p": round(float(m.pvalues[x]), 4)} for x in xs}, int(len(d))

# --- food_insec: FEA INSECURITY (state-broadcast; one value/state) ---
ins = pd.read_excel(FD/"FEA/2025-food-environment-atlas-data.xlsx", sheet_name="INSECURITY", skiprows=1)
ins["FOODINSEC_21_23"] = pd.to_numeric(ins["FOODINSEC_21_23"], errors="coerce")
ins.loc[ins["FOODINSEC_21_23"] < 0, "FOODINSEC_21_23"] = np.nan  # FEA missing sentinels (-8888 / -4177 etc.)
food_insec = ins.groupby("State")["FOODINSEC_21_23"].mean().rename("food_insec")

# --- poverty: FEA SOCIOECONOMIC POVRATE21 county -> state, pop-weighted by ACS B01003 ---
soc = pd.read_excel(FD/"FEA/2025-food-environment-atlas-data.xlsx", sheet_name="SOCIOECONOMIC", skiprows=1)
soc["FIPS5"] = soc["FIPS"].apply(lambda x: str(int(x)).zfill(5))
acs = pd.read_json(ROOT/"data/paper7/demand_drivers/acs5_2024_B01003_county.json")
acs.columns = acs.iloc[0]; acs = acs.iloc[1:]
acs["FIPS5"] = acs["state"].str.zfill(2) + acs["county"].str.zfill(3)
acs["pop"] = pd.to_numeric(acs["B01003_001E"], errors="coerce")
soc = soc.merge(acs[["FIPS5","pop"]], on="FIPS5", how="left")
soc["POVRATE21"] = pd.to_numeric(soc["POVRATE21"], errors="coerce")
soc.loc[soc["POVRATE21"] < 0, "POVRATE21"] = np.nan  # FEA missing sentinels (-8888 etc.)
soc = soc.dropna(subset=["POVRATE21","pop"])
poverty = (soc.assign(wp=soc.POVRATE21*soc["pop"]).groupby("State")
           .apply(lambda g: g.wp.sum()/g["pop"].sum()).rename("poverty"))

# --- food_floor: FARA sum(LAPOP1_10)/sum(Pop2010) by state ---
fara = pd.read_excel(FD/"FoodAccessResearchAtlasData2019.xlsx" if (FD/"FoodAccessResearchAtlasData2019.xlsx").exists()
                     else FD/"FARA/FoodAccessResearchAtlasData2019.xlsx",
                     sheet_name="Food Access Research Atlas", usecols=["State","Pop2010","LAPOP1_10"])
fara["ab"] = fara["State"].map(NAME2AB)
food_floor = (fara.groupby("ab").apply(lambda g: g.LAPOP1_10.sum()/g.Pop2010.sum()).rename("food_floor"))

# --- homeless + rent_floor: timepanel CoC -> state pop-weighted, latest year 2024 ---
tp = pd.read_csv(ROOT/"analysis/paper7_coc_timepanel_2012_2024.csv")
tp = tp[tp.year == 2024].copy(); tp["st"] = tp.coc_number.str[:2]
def pw(g, col):
    m = g[col].notna() & g.total_population.notna()
    return np.average(g.loc[m, col], weights=g.loc[m, "total_population"]) if m.any() else np.nan
homeless = tp.groupby("st").apply(lambda g: pw(g,"homeless_per_10k")).rename("homeless_per_10k")
rent_floor = tp.groupby("st").apply(lambda g: pw(g,"rent_coc")).rename("rent_floor")

# --- precarity: Pulse state means over periods ---
pu = pd.read_csv(ROOT/"analysis/paper7_pulse_housing_precarity.csv")
pu = pu[pu.geo_type == "state"]
behind = pu.groupby("geography")["behind_on_rent_share"].mean().rename("behind_on_rent")
evrisk = pu.groupby("geography")["eviction_risk_share"].mean().rename("eviction_risk")

df = pd.concat([food_insec, poverty, food_floor, homeless, rent_floor, behind, evrisk], axis=1)
df.index.name = "state"; df = df.reset_index()
df = df[df.state.isin(NAME2AB.values())]  # 50 + DC, drop territories
full = df.dropna(subset=["food_insec","homeless_per_10k","rent_floor","poverty","food_floor","behind_on_rent"])

res = {"pre_reg": "PRE_REG_039", "framing": "correlational; cross-sectional; state resolution; no person-linkage",
       "n_merged": int(len(full)), "precarity_primary": "behind_on_rent_share (Pulse state mean)"}

# D1
r,p,n = corr(full.behind_on_rent, full.food_insec)
r2,p2,_ = corr(full.eviction_risk, full.food_insec)
D1 = (r > 0 and p < 0.05)
res["CLOSE_D1_precarity_to_foodinsec"] = {"behind_corr": r, "p": p, "n": n,
    "evrisk_corr": r2, "evrisk_p": p2, "predict": ">0 sig", "pass": bool(D1)}
# D2
r,p,n = corr(full.behind_on_rent, full.homeless_per_10k)
r2,p2,_ = corr(full.eviction_risk, full.homeless_per_10k)
D2 = not (r > 0 and p < 0.05)
res["CLOSE_D2_precarity_NOT_homeless"] = {"behind_corr": r, "p": p, "n": n,
    "evrisk_corr": r2, "evrisk_p": p2, "predict": "NOT sig positive", "pass": bool(D2)}
# D3
r,p,n = corr(full.food_insec, full.homeless_per_10k)
D3 = not (r > 0 and p < 0.05)
res["CLOSE_D3_axes_dissociate"] = {"foodinsec_homeless_corr": r, "p": p, "n": n,
    "predict": "<=0 / not sig positive", "pass": bool(D3)}
# D4
hco, hn = ols(full, "homeless_per_10k", ["rent_floor","poverty"])
fco, fn = ols(full, "food_insec", ["poverty","food_floor","rent_floor"])
rent_drives_homeless = hco["rent_floor"]["coef"] > 0 and hco["rent_floor"]["p"] < 0.05
food_by_pov_or_floor = ((fco["poverty"]["coef"] > 0 and fco["poverty"]["p"] < 0.05) or
                        (fco["food_floor"]["coef"] > 0 and fco["food_floor"]["p"] < 0.05))
rent_not_in_food = fco["rent_floor"]["p"] >= 0.05
D4 = rent_drives_homeless and food_by_pov_or_floor and rent_not_in_food
res["CLOSE_D4_rent_floor_is_switch"] = {"homeless_model": hco, "food_insec_model": fco,
    "rent_drives_homeless": bool(rent_drives_homeless), "food_by_poverty_or_floor": bool(food_by_pov_or_floor),
    "rent_NOT_in_food": bool(rent_not_in_food), "pass": bool(D4)}

res["SEAM_CLOSED"] = bool(D1 and D2 and D3 and D4)
res["disposition"] = ("SEAM CLOSED — one system, rent-floor switch, two dissociated discharge axes"
                      if res["SEAM_CLOSED"] else
                      "SEAM NOT fully closed — see which D-rule failed")
res["context"] = {"corr_rent_homeless": corr(full.rent_floor, full.homeless_per_10k)[0],
                  "median_food_insec": round(float(full.food_insec.median()),2),
                  "median_homeless_per_10k": round(float(full.homeless_per_10k.median()),2)}
OUT.write_text(json.dumps(res, indent=2)); print(json.dumps(res, indent=2)); print("\nwrote", OUT)
