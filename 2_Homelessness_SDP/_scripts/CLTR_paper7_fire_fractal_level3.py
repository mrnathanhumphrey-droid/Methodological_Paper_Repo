"""
CLTR fractal level 3 — does the STREET (unsheltered) sub-leaf split again?
CoC, 2024, n~302. unsheltered_per_10k ~ jan_temp + supply_tight + rent_coc + rts + jan_temp*supply_tight.
L3-D1 new rule beyond climate; L3-D2 climate*supply interaction (gate*magnitude). Rules locked in
CLTR_PRE_REG_fractal_level3_street_2026_05_29.md. Correlational; jan_temp state-broadcast (coarse climate).
"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm

ROOT = Path(r"D:/IDP"); sys.path.insert(0, str(ROOT/"_scripts"))
from paper7_policy_block import policy_frame
OUT = ROOT/"analysis/CLTR_paper7_fractal_level3_results_2026_05_29.json"

m = pd.read_csv(ROOT/"analysis/paper7_metro_coc_panel_2024.csv")
m["state"] = m.coc_number.str[:2]
pol = policy_frame()[["state","jan_temp","rts"]]
m = m.merge(pol, on="state", how="left")
m["supply_tight"] = -m["saiz_elasticity"]   # higher = more supply-constrained
d = m.dropna(subset=["unsheltered_per_10k","jan_temp","supply_tight","rent_coc","rts"]).copy()

def z(s): return (s - s.mean())/s.std()
for c in ["jan_temp","supply_tight","rent_coc","rts"]:
    d["z_"+c] = z(d[c])
d["z_janXtight"] = d["z_jan_temp"]*d["z_supply_tight"]

xs = ["z_jan_temp","z_supply_tight","z_rent_coc","z_rts","z_janXtight"]
mod = sm.OLS(d["unsheltered_per_10k"].values, sm.add_constant(d[xs].values)).fit(cov_type="HC1")
label = {"z_jan_temp":"jan_temp","z_supply_tight":"supply_tight","z_rent_coc":"rent_coc","z_rts":"rts","z_janXtight":"jan_temp_x_supply_tight"}
coefs = {label[xs[i]]: {"std_coef": round(float(mod.params[i+1]),3), "p": round(float(mod.pvalues[i+1]),4)} for i in range(len(xs))}

new_rule = (coefs["supply_tight"]["std_coef"]>0 and coefs["supply_tight"]["p"]<0.05) or \
           (coefs["rent_coc"]["std_coef"]>0 and coefs["rent_coc"]["p"]<0.05)
interaction = (coefs["jan_temp_x_supply_tight"]["std_coef"]>0 and coefs["jan_temp_x_supply_tight"]["p"]<0.05)

res = {"pre_reg":"CLTR_fractal_level3","framing":"correlational; CoC; jan_temp state-broadcast (coarse)",
       "n": int(len(d)), "outcome":"unsheltered_per_10k (the street sub-leaf)", "R2": round(float(mod.rsquared),3),
       "std_coefs": coefs,
       "L3_D1_new_rule_beyond_climate": bool(new_rule),
       "L3_D2_climate_x_supply_interaction": bool(interaction),
       "FRACTAL_REPEATS_level3": bool(new_rule and interaction),
       "disposition": ("FRACTAL REPEATS at level 3 — street splits into climate-gate x supply-magnitude (genuinely fractal, motif at >=3 levels)"
                       if (new_rule and interaction) else
                       "NEW RULE but no gate-x-magnitude interaction (street = climate + additive supply, not a clean self-similar split)"
                       if new_rule else
                       "STREET CLIMATE-TERMINAL — recursion bottoms out; finite (two-level) hierarchy, not fractal")}
OUT.write_text(json.dumps(res, indent=2)); print(json.dumps(res, indent=2)); print("\nwrote", OUT)
