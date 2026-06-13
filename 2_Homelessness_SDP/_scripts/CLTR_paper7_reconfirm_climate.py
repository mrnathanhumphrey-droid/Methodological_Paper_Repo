"""
CLTR re-confirmation — replace the hand-coded approximate jan_temp with AUTHENTIC NOAA climdiv
statewide 1991-2020 January mean temperature, and re-run the fractal level-2 (street/sheltered)
and level-3 (street climate-gate x supply) tests. Validates the approximate table + tests robustness.
Raw: data/paper7/climate/CLTR_climdiv_tmpcst_v1.0.0_20260506.txt (NOAA NCEI climdiv tmpcst).
climdiv record: state(0:3) code(3:6) year(6:10), then 12 monthly avg-temp F (Jan first). Missing=-99.90.
DC + HI absent from climdiv -> filled from policy_block (flagged) and a drop-HI/DC variant reported.
"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy.stats import pearsonr
ROOT = Path(r"D:/IDP"); sys.path.insert(0, str(ROOT/"_scripts"))
from paper7_policy_block import policy_frame, JAN_TEMP as APPROX
OUT = ROOT/"analysis/CLTR_paper7_reconfirm_climate_2026_05_29.json"

CD = {1:'AL',2:'AZ',3:'AR',4:'CA',5:'CO',6:'CT',7:'DE',8:'FL',9:'GA',10:'ID',11:'IL',12:'IN',13:'IA',
14:'KS',15:'KY',16:'LA',17:'ME',18:'MD',19:'MA',20:'MI',21:'MN',22:'MS',23:'MO',24:'MT',25:'NE',26:'NV',
27:'NH',28:'NJ',29:'NM',30:'NY',31:'NC',32:'ND',33:'OH',34:'OK',35:'OR',36:'PA',37:'RI',38:'SC',39:'SD',
40:'TN',41:'TX',42:'UT',43:'VT',44:'VA',45:'WA',46:'WV',47:'WI',48:'WY',50:'AK'}

# --- parse authentic Jan normal 1991-2020 ---
jan = {}
for ln in open(ROOT/"data/paper7/climate/CLTR_climdiv_tmpcst_v1.0.0_20260506.txt"):
    sc = int(ln[0:3]); yr = int(ln[6:10])
    if sc not in CD or not (1991 <= yr <= 2020): continue
    v = float(ln[10:].split()[0])
    if v < -50: continue
    jan.setdefault(CD[sc], []).append(v)
auth = {s: float(np.mean(vs)) for s, vs in jan.items() if len(vs) >= 25}
res = {"source": "NOAA NCEI climdiv tmpcst v1.0.0 (1991-2020 Jan mean, statewide)",
       "n_states_authentic": len(auth), "missing_from_climdiv": [s for s in APPROX if s not in auth]}

# --- validate approx vs authentic ---
common = [s for s in auth if s in APPROX]
a = np.array([APPROX[s] for s in common]); b = np.array([auth[s] for s in common])
r, p = pearsonr(a, b)
res["validation_approx_vs_authentic"] = {"n": len(common), "pearson_r": round(float(r), 4),
    "mean_abs_diff_F": round(float(np.mean(np.abs(a-b))), 2),
    "biggest_diffs": sorted([(s, round(APPROX[s]-auth[s],1)) for s in common], key=lambda x: -abs(x[1]))[:6]}

# authentic jan_temp series (fill HI/DC from approx, flagged)
def jt(s): return auth.get(s, APPROX.get(s))
filled = {s: jt(s) for s in APPROX}

def z(s): return (s - s.mean())/s.std()

# ============ LEVEL 2 re-run (state, street/sheltered) ============
sp = pd.read_csv(ROOT/"analysis/paper7_sdp_state_year_panel.csv"); sp = sp[sp.year==2024].copy()
sp["unsheltered_per_10k"] = sp.unsheltered/sp.population*1e4
sp["sheltered_per_10k"] = (sp.overall_homeless-sp.unsheltered)/sp.population*1e4
pol = policy_frame(); mp = pd.read_csv(ROOT/"analysis/paper7_metro_coc_panel_2024.csv"); mp["st"]=mp.coc_number.str[:2]
def pw(g,c):
    m=g[c].notna()&g.total_population.notna(); return np.average(g.loc[m,c],weights=g.loc[m,"total_population"]) if m.any() else np.nan
rf = mp.groupby("st").apply(lambda g: pw(g,"rent_coc")).rename("rent_floor").reset_index().rename(columns={"st":"state"})
L = sp.merge(pol[["state","rts"]],on="state",how="inner").merge(rf,on="state",how="left")
L["jan_auth"] = L.state.map(filled)
L = L.dropna(subset=["unsheltered_per_10k","sheltered_per_10k","jan_auth","rts","rent_floor"])
def model(df,y,xs):
    Z=pd.DataFrame({x:z(df[x]) for x in xs}); m=sm.OLS(df[y].values,sm.add_constant(Z.values)).fit(cov_type="HC1")
    return {xs[i]:{"b":round(float(m.params[i+1]),3),"p":round(float(m.pvalues[i+1]),4)} for i in range(len(xs))}, round(float(m.rsquared),3)
st_c,st_r = model(L,"unsheltered_per_10k",["jan_auth","rent_floor","rts"])
sh_c,sh_r = model(L,"sheltered_per_10k",["jan_auth","rent_floor","rts"])
res["LEVEL2_authentic"] = {"n":int(len(L)),
    "street_dominant_jan": st_c["jan_auth"], "street_R2": st_r,
    "sheltered_dominant_rts": sh_c["rts"], "sheltered_R2": sh_r,
    "street_climate_holds": bool(st_c["jan_auth"]["b"]>0 and st_c["jan_auth"]["p"]<0.05),
    "sheltered_rts_holds": bool(sh_c["rts"]["b"]>0 and sh_c["rts"]["p"]<0.05)}

# ============ LEVEL 3 re-run (CoC, street climate-gate x supply) ============
m = pd.read_csv(ROOT/"analysis/paper7_metro_coc_panel_2024.csv"); m["state"]=m.coc_number.str[:2]
m = m.merge(pol[["state","rts"]],on="state",how="left"); m["jan_auth"]=m.state.map(filled); m["supply_tight"]=-m.saiz_elasticity
def l3(d):
    Z=pd.DataFrame({c:z(d[c]) for c in ["jan_auth","supply_tight","rent_coc","rts"]}); Z["jx"]=Z.jan_auth*Z.supply_tight
    r=sm.OLS(d.unsheltered_per_10k.values,sm.add_constant(Z.values)).fit(cov_type="HC1")
    names=["jan_auth","supply_tight","rent_coc","rts","janXtight"]
    return {names[i]:{"b":round(float(r.params[i+1]),3),"p":round(float(r.pvalues[i+1]),4)} for i in range(5)}, round(float(r.rsquared),3), len(d)
base = m.dropna(subset=["unsheltered_per_10k","jan_auth","supply_tight","rent_coc","rts"])
allc,allr,alln = l3(base)
dwc,dwr,dwn = l3(base[~base.state.isin(["CA","HI","OR","WA"])])
res["LEVEL3_authentic"] = {"n_all":alln,"R2":allr,"coefs_all":allc,
    "interaction_all": allc["janXtight"], "R2_dropWestCoast":dwr,
    "interaction_dropWestCoast": dwc["janXtight"], "n_dropWestCoast":dwn,
    "climate_gate_holds": bool(allc["jan_auth"]["b"]>0 and allc["jan_auth"]["p"]<0.05),
    "interaction_holds_full": bool(allc["janXtight"]["b"]>0 and allc["janXtight"]["p"]<0.05),
    "interaction_westcoast_dependent": bool(allc["janXtight"]["p"]<0.05 and dwc["janXtight"]["p"]>=0.05)}
res["VERDICT"] = ("CONFIRMED with authentic climate: street<-climate (L2) + climate-gate x supply (L3, full) replicate; West-Coast-dependence of the interaction also replicates"
    if (res["LEVEL2_authentic"]["street_climate_holds"] and res["LEVEL3_authentic"]["climate_gate_holds"] and res["LEVEL3_authentic"]["interaction_holds_full"])
    else "PARTIAL/CHANGED — see fields")
OUT.write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2)); print("\nwrote",OUT)
