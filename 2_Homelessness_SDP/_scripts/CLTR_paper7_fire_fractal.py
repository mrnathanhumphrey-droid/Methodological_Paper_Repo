"""
CLTR fractal test — do the PRE_REG_039 discharge leaves recursively split into clean sub-leaves?
Leaf 1 (homelessness -> street/sheltered): distinct-rule + cleanness. State n~50, 2024.
Leaf 2 (food insecurity -> rural-access/urban-income): coarse interaction (state-only food data).
Rules locked in CLTR_PRE_REG_fractal_leaf_decomposition_2026_05_29.md. Correlational; cross-sectional.
"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy.stats import pearsonr

ROOT = Path(r"D:/IDP"); FD = Path(r"D:/Food Deserts/data_raw")
sys.path.insert(0, str(ROOT/"_scripts"))
from paper7_policy_block import policy_frame
OUT = ROOT/"analysis/CLTR_paper7_fractal_results_2026_05_29.json"

NAME2AB = {'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA','Colorado':'CO',
'Connecticut':'CT','Delaware':'DE','District of Columbia':'DC','Florida':'FL','Georgia':'GA','Hawaii':'HI',
'Idaho':'ID','Illinois':'IL','Indiana':'IN','Iowa':'IA','Kansas':'KS','Kentucky':'KY','Louisiana':'LA',
'Maine':'ME','Maryland':'MD','Massachusetts':'MA','Michigan':'MI','Minnesota':'MN','Mississippi':'MS',
'Missouri':'MO','Montana':'MT','Nebraska':'NE','Nevada':'NV','New Hampshire':'NH','New Jersey':'NJ',
'New Mexico':'NM','New York':'NY','North Carolina':'NC','North Dakota':'ND','Ohio':'OH','Oklahoma':'OK',
'Oregon':'OR','Pennsylvania':'PA','Rhode Island':'RI','South Carolina':'SC','South Dakota':'SD',
'Tennessee':'TN','Texas':'TX','Utah':'UT','Vermont':'VT','Virginia':'VA','Washington':'WA',
'West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY'}

def zols(df, y, xs):
    d = df.dropna(subset=[y]+xs).copy()
    Z = (d[xs]-d[xs].mean())/d[xs].std()
    m = sm.OLS(d[y].values, sm.add_constant(Z.values)).fit()
    out = {xs[i]: {"std_coef": round(float(m.params[i+1]),3), "p": round(float(m.pvalues[i+1]),4)} for i in range(len(xs))}
    return out, round(float(m.rsquared),3), int(len(d))

def dominant(coefs, among):
    sig = {k: coefs[k] for k in among if coefs[k]["p"] < 0.05}
    if not sig: return None
    return max(sig, key=lambda k: abs(sig[k]["std_coef"]))

res = {"pre_reg": "CLTR_fractal", "framing": "correlational; cross-sectional; state; leaf1 confirmatory, leaf2 coarse/data-limited"}

# ================= LEAF 1: homelessness -> street / sheltered =================
sp = pd.read_csv(ROOT/"analysis/paper7_sdp_state_year_panel.csv")
sp = sp[sp.year == 2024].copy()
sp["unsheltered_per_10k"] = sp["unsheltered"]/sp["population"]*1e4
sp["sheltered_per_10k"] = (sp["overall_homeless"]-sp["unsheltered"])/sp["population"]*1e4
pol = policy_frame()
# rent_floor: pop-weighted rent_coc CoC->state, 2024
mp = pd.read_csv(ROOT/"analysis/paper7_metro_coc_panel_2024.csv"); mp["st"] = mp.coc_number.str[:2]
def pw(g,c):
    m=g[c].notna()&g.total_population.notna()
    return np.average(g.loc[m,c],weights=g.loc[m,"total_population"]) if m.any() else np.nan
rent_floor = mp.groupby("st").apply(lambda g: pw(g,"rent_coc")).rename("rent_floor").reset_index().rename(columns={"st":"state"})
L1 = sp.merge(pol, on="state", how="inner").merge(rent_floor, on="state", how="left")
L1 = L1.dropna(subset=["unsheltered_per_10k","sheltered_per_10k","unsheltered_share","jan_temp","rts","rent_floor"])

drivers = ["jan_temp","rent_floor","rts"]; theory = drivers
share_c, share_r, _ = zols(L1, "unsheltered_share", drivers)
street_c, street_r, n1 = zols(L1, "unsheltered_per_10k", drivers+["medicaid_exp","rent_control_allowed"])
shelt_c, shelt_r, _ = zols(L1, "sheltered_per_10k", drivers+["medicaid_exp","rent_control_allowed"])
street_dom = dominant(street_c, theory); shelt_dom = dominant(shelt_c, theory)

rent_on_split = share_c["rent_floor"]
clim_split = share_c["jan_temp"]; rts_split = share_c["rts"]
L1_D1 = (rent_on_split["p"] >= 0.05) or (abs(rent_on_split["std_coef"]) < max(abs(clim_split["std_coef"]), abs(rts_split["std_coef"])))
L1_D2 = (street_dom is not None and shelt_dom is not None and street_dom != shelt_dom)
def clean(coefs, dom, r2):
    return dom is not None and coefs[dom]["p"] < 0.05 and r2 >= 0.25
L1_D3 = clean(street_c, street_dom, street_r) and clean(shelt_c, shelt_dom, shelt_r)
res["LEAF1_homeless_street_vs_sheltered"] = {
    "n": n1,
    "split_model_unsheltered_share": {"R2": share_r, "std_coefs": share_c},
    "street_model_unsheltered_per_10k": {"R2": street_r, "std_coefs": street_c, "dominant": street_dom},
    "sheltered_model_per_10k": {"R2": shelt_r, "std_coefs": shelt_c, "dominant": shelt_dom},
    "L1_D1_rent_sets_level_not_split": bool(L1_D1),
    "L1_D2_distinct_dominant_drivers": bool(L1_D2),
    "L1_D3_children_clean": bool(L1_D3),
    "FRACTAL_POSITIVE": bool(L1_D1 and L1_D2 and L1_D3)}

# ================= LEAF 2: food insecurity -> rural-access / urban-income =================
ins = pd.read_excel(FD/"FEA/2025-food-environment-atlas-data.xlsx", sheet_name="INSECURITY", skiprows=1)
ins["FOODINSEC_21_23"] = pd.to_numeric(ins["FOODINSEC_21_23"], errors="coerce")
ins.loc[ins["FOODINSEC_21_23"] < 0, "FOODINSEC_21_23"] = np.nan
food_insec = ins.groupby("State")["FOODINSEC_21_23"].mean().rename("food_insec")
soc = pd.read_excel(FD/"FEA/2025-food-environment-atlas-data.xlsx", sheet_name="SOCIOECONOMIC", skiprows=1)
soc["FIPS5"] = soc["FIPS"].apply(lambda x: str(int(x)).zfill(5))
soc["POVRATE21"] = pd.to_numeric(soc["POVRATE21"], errors="coerce")
soc.loc[soc["POVRATE21"] < 0, "POVRATE21"] = np.nan
acs = pd.read_json(ROOT/"data/paper7/demand_drivers/acs5_2024_B01003_county.json")
acs.columns = acs.iloc[0]; acs = acs.iloc[1:]
acs["FIPS5"] = acs["state"].str.zfill(2)+acs["county"].str.zfill(3); acs["pop"] = pd.to_numeric(acs["B01003_001E"], errors="coerce")
soc = soc.merge(acs[["FIPS5","pop"]], on="FIPS5", how="left").dropna(subset=["POVRATE21","pop"])
poverty = (soc.assign(wp=soc.POVRATE21*soc["pop"]).groupby("State").apply(lambda g: g.wp.sum()/g["pop"].sum()).rename("poverty"))
fara = pd.read_excel(FD/"FARA/FoodAccessResearchAtlasData2019.xlsx", sheet_name="Food Access Research Atlas",
                     usecols=["State","Pop2010","LAPOP1_10","Urban"])
fara["ab"] = fara["State"].map(NAME2AB)
food_floor = fara.groupby("ab").apply(lambda g: g.LAPOP1_10.sum()/g.Pop2010.sum()).rename("food_floor")
rural_share = fara.groupby("ab").apply(lambda g: g.loc[g.Urban==0,"Pop2010"].sum()/g.Pop2010.sum()).rename("rural_share")
L2 = pd.concat([food_insec, poverty, food_floor, rural_share], axis=1).reset_index().rename(columns={"index":"state"})
L2 = L2[L2.state.isin(NAME2AB.values())].dropna(subset=["food_insec","poverty","food_floor","rural_share"])
L2["ffxrural"] = ((L2.food_floor-L2.food_floor.mean())/L2.food_floor.std())*((L2.rural_share-L2.rural_share.mean())/L2.rural_share.std())
l2c, l2r, n2 = zols(L2, "food_insec", ["poverty","food_floor","rural_share","ffxrural"])
L2_D1 = (l2c["poverty"]["std_coef"]>0 and l2c["poverty"]["p"]<0.05) and \
        ((l2c["food_floor"]["p"]<0.05) or (l2c["ffxrural"]["p"]<0.05))
L2_D2 = (l2c["ffxrural"]["std_coef"]>0 and l2c["ffxrural"]["p"]<0.05)
res["LEAF2_food_rural_vs_urban"] = {"n": n2, "R2": l2r, "std_coefs": l2c,
    "L2_D1_two_channels": bool(L2_D1), "L2_D2_access_rural_concentrated": bool(L2_D2),
    "FRACTAL_SUGGESTIVE": bool(L2_D1 and L2_D2),
    "note": "COARSE/data-limited: FEA food insecurity is state-only; clean split needs county food insecurity (Map-the-Meal-Gap, not on disk)"}

# ================= overall =================
l1 = res["LEAF1_homeless_street_vs_sheltered"]["FRACTAL_POSITIVE"]
res["VERDICT"] = {"leaf1_fractal_positive": bool(l1),
    "leaf2_suggestive": bool(res["LEAF2_food_rural_vs_urban"]["FRACTAL_SUGGESTIVE"]),
    "reading": ("SELF-SIMILAR at level 2 (fractal motif repeats once): homelessness leaf splits into street/sheltered governed by a NEW orthogonal rule, children clean"
                if l1 else "leaf1 TERMINAL — same rule governs children; finite hierarchy, not fractal")}
OUT.write_text(json.dumps(res, indent=2)); print(json.dumps(res, indent=2)); print("\nwrote", OUT)
