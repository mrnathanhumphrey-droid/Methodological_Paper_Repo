"""
CLTR fractal level 3 (b) — does the SHELTERED sub-leaf split again?
State n~51, 2024. SH-D1 need(cold)+capacity(RTS); SH-D2 ES vs TH distinct rules.
Authentic jan_temp (NOAA climdiv 1991-2020; HI/DC filled from policy_block). Rules locked in
CLTR_PRE_REG_fractal_level3_sheltered_2026_05_29.md. Correlational; cross-sectional.
"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
ROOT = Path(r"D:/IDP"); sys.path.insert(0, str(ROOT/"_scripts"))
from paper7_policy_block import policy_frame, JAN_TEMP as APPROX
OUT = ROOT/"analysis/CLTR_paper7_fractal_sheltered_results_2026_05_29.json"

CD = {1:'AL',2:'AZ',3:'AR',4:'CA',5:'CO',6:'CT',7:'DE',8:'FL',9:'GA',10:'ID',11:'IL',12:'IN',13:'IA',
14:'KS',15:'KY',16:'LA',17:'ME',18:'MD',19:'MA',20:'MI',21:'MN',22:'MS',23:'MO',24:'MT',25:'NE',26:'NV',
27:'NH',28:'NJ',29:'NM',30:'NY',31:'NC',32:'ND',33:'OH',34:'OK',35:'OR',36:'PA',37:'RI',38:'SC',39:'SD',
40:'TN',41:'TX',42:'UT',43:'VT',44:'VA',45:'WA',46:'WV',47:'WI',48:'WY',50:'AK'}
jan = {}
for ln in open(ROOT/"data/paper7/climate/CLTR_climdiv_tmpcst_v1.0.0_20260506.txt"):
    sc=int(ln[0:3]); yr=int(ln[6:10])
    if sc in CD and 1991<=yr<=2020:
        v=float(ln[10:].split()[0])
        if v>-50: jan.setdefault(CD[sc],[]).append(v)
AUTH = {s: float(np.mean(vs)) for s,vs in jan.items() if len(vs)>=25}
filled = {s: AUTH.get(s, APPROX.get(s)) for s in APPROX}

sp = pd.read_csv(ROOT/"analysis/paper7_sdp_state_year_panel.csv"); sp = sp[sp.year==2024].copy()
sp["sheltered_per_10k"] = (sp.overall_homeless-sp.unsheltered)/sp.population*1e4
sp["es_per_10k"] = sp.shelt_es/sp.population*1e4
sp["th_per_10k"] = sp.shelt_th/sp.population*1e4
pol = policy_frame(); mp = pd.read_csv(ROOT/"analysis/paper7_metro_coc_panel_2024.csv"); mp["st"]=mp.coc_number.str[:2]
def pw(g,c):
    m=g[c].notna()&g.total_population.notna(); return np.average(g.loc[m,c],weights=g.loc[m,"total_population"]) if m.any() else np.nan
rf = mp.groupby("st").apply(lambda g: pw(g,"rent_coc")).rename("rent_floor").reset_index().rename(columns={"st":"state"})
d = sp.merge(pol[["state","rts","medicaid_exp"]],on="state",how="inner").merge(rf,on="state",how="left")
d["jan_auth"] = d.state.map(filled)
d = d.dropna(subset=["sheltered_per_10k","es_per_10k","th_per_10k","jan_auth","rts","rent_floor","medicaid_exp"])

def z(s): return (s-s.mean())/s.std()
def model(y, xs):
    Z=pd.DataFrame({x:z(d[x]) for x in xs}); m=sm.OLS(d[y].values,sm.add_constant(Z.values)).fit(cov_type="HC1")
    return {xs[i]:{"b":round(float(m.params[i+1]),3),"p":round(float(m.pvalues[i+1]),4)} for i in range(len(xs))}, round(float(m.rsquared),3)
def dom(c, among):
    sig={k:c[k] for k in among if c[k]["p"]<0.05}
    return max(sig, key=lambda k: abs(sig[k]["b"])) if sig else None

# SH-D1: need(cold) + capacity(RTS)
sh_c, sh_r = model("sheltered_per_10k", ["jan_auth","rts","rent_floor"])
SH_D1 = (sh_c["jan_auth"]["b"]<0 and sh_c["jan_auth"]["p"]<0.05) and (sh_c["rts"]["b"]>0 and sh_c["rts"]["p"]<0.05)

# SH-D2: ES vs TH distinct dominant rules
es_c, es_r = model("es_per_10k", ["jan_auth","rts","rent_floor","medicaid_exp"])
th_c, th_r = model("th_per_10k", ["jan_auth","rts","rent_floor","medicaid_exp"])
among = ["jan_auth","rts","rent_floor","medicaid_exp"]
es_dom, th_dom = dom(es_c, among), dom(th_c, among)
def clean(c,dm,r2): return dm is not None and c[dm]["p"]<0.05 and r2>=0.25
SH_D2 = (es_dom is not None and th_dom is not None and es_dom != th_dom and clean(es_c,es_dom,es_r) and clean(th_c,th_dom,th_r))

res = {"pre_reg":"CLTR_fractal_sheltered","framing":"correlational; state; authentic NOAA climate; RTS/cold confounded (low power)",
       "n": int(len(d)),
       "SH_D1_need_plus_capacity": {"model_sheltered": sh_c, "R2": sh_r, "pass": bool(SH_D1),
            "note":"needs cold(jan_temp<0) AND rts(>0) both sig"},
       "SH_D2_ES_vs_TH_split": {"ES_model": es_c, "ES_R2": es_r, "ES_dominant": es_dom,
            "TH_model": th_c, "TH_R2": th_r, "TH_dominant": th_dom, "pass": bool(SH_D2)},
       "SHELTERED_FRACTAL_CONTINUES": bool(SH_D1 or SH_D2),
       "disposition": ("SHELTERED FRACTAL-CONTINUES" if (SH_D1 or SH_D2) else
            "SHELTERED TERMINAL — RTS/rent dominates; no clean further split (ASYMMETRY: street recurses, sheltered terminal)")}
OUT.write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2)); print("\nwrote",OUT)
