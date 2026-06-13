"""
FOOD-edge firm-up: WHY is the L3 street interaction (climate-gate x supply-magnitude)
West-Coast-dependent? Three reads to separate:
  (a) POWER artifact  - effect same size, just loses significance when CA/HI/OR/WA dropped
  (b) WC QUIRK        - a West-Coast-specific factor, not the condition
  (c) CONDITION = REGION - "warm + tight-supply" only co-occurs on the West Coast,
                          so dropping WC removes the condition itself, not a region effect

Reuses the parallel agent's exact L3 spec (metro CoC panel, supply_tight=-saiz, policy_frame).
Output: analysis/FOOD_l3_westcoast_firm.json
"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm

ROOT = Path(r"D:/IDP"); sys.path.insert(0, str(ROOT/"_scripts"))
from paper7_policy_block import policy_frame

WC = {"CA","OR","WA","HI"}

m = pd.read_csv(ROOT/"analysis/paper7_metro_coc_panel_2024.csv")
m["state"] = m.coc_number.str[:2]
pol = policy_frame()[["state","jan_temp","rts"]]
m = m.merge(pol, on="state", how="left")
m["supply_tight"] = -m["saiz_elasticity"]
d = m.dropna(subset=["unsheltered_per_10k","jan_temp","supply_tight","rent_coc","rts"]).copy()
d["wc"] = d.state.isin(WC).astype(int)

def z(s): return (s - s.mean())/s.std()
for c in ["jan_temp","supply_tight","rent_coc","rts"]:
    d["z_"+c] = z(d[c])
d["z_janXtight"] = d.z_jan_temp*d.z_supply_tight

warm = d.jan_temp > d.jan_temp.median()
tight = d.supply_tight > d.supply_tight.median()
out = {"n": int(len(d)), "n_wc": int(d.wc.sum())}

# T1 — condition vs region: is warm+tight ~ West-Coast-exclusive?
wt = d[warm & tight]
out["T1_condition_region"] = {
    "n_warm_and_tight": int(len(wt)),
    "frac_warm_tight_that_are_WC": round(float(wt.wc.mean()), 3),
    "corr_supply_tight_with_WC": round(float(np.corrcoef(d.supply_tight, d.wc)[0,1]), 3),
    "non_WC_warm_tight_CoCs": int(len(wt[wt.wc == 0])),
    "non_WC_warm_tight_examples": wt[wt.wc==0].sort_values("unsheltered_per_10k", ascending=False)
        [["coc_number","state","unsheltered_per_10k","supply_tight"]].head(8)
        .round(2).to_dict("records")}

# T2 — supply->street slope among WARM CoCs, WC vs non-WC (does the rule exist off WC?)
def slope(sub):
    if len(sub) < 15: return {"n": int(len(sub)), "note": "too few"}
    X = sm.add_constant(sub[["z_supply_tight","z_rent_coc"]].values)
    r = sm.OLS(sub.unsheltered_per_10k.values, X).fit(cov_type="HC1")
    return {"n": int(len(sub)), "supply_tight_b": round(float(r.params[1]),3),
            "p": round(float(r.pvalues[1]),4), "R2": round(float(r.rsquared),3)}
warm_d = d[warm]
out["T2_supply_slope_among_warm"] = {"warm_WC": slope(warm_d[warm_d.wc==1]),
                                     "warm_nonWC": slope(warm_d[warm_d.wc==0])}

# T3 — interaction coef + 95% CI, full vs drop-WC (power vs genuine-zero)
def inter(sub):
    xs=["z_jan_temp","z_supply_tight","z_rent_coc","z_rts","z_janXtight"]
    r=sm.OLS(sub.unsheltered_per_10k.values, sm.add_constant(sub[xs].values)).fit(cov_type="HC1")
    b=float(r.params[5]); se=float(r.bse[5])
    return {"n":int(len(sub)),"janXtight_b":round(b,3),"p":round(float(r.pvalues[5]),4),
            "ci95":[round(b-1.96*se,3),round(b+1.96*se,3)]}
out["T3_interaction_power"] = {"full": inter(d), "drop_WC": inter(d[d.wc==0])}
full_b = out["T3_interaction_power"]["full"]["janXtight_b"]
lo,hi = out["T3_interaction_power"]["drop_WC"]["ci95"]
out["T3_read"] = ("UNDERPOWERED: drop-WC CI still includes the full estimate ("+str(full_b)+") -> can't rule out same effect"
                  if lo <= full_b <= hi else
                  "GENUINE: drop-WC CI excludes the full estimate -> effect really is WC-concentrated, not just power")

(ROOT/"analysis/FOOD_l3_westcoast_firm.json").write_text(json.dumps(out, indent=2, default=str))
print(json.dumps(out, indent=2, default=str))
