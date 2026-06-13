"""
PRE_REG_032 — Gentrification dynamics + what drives rent demand.
H1 dynamic: within-CoC (CoC FE + year FE) homeless~rent+income; AND long-difference concurs.
H2 demand drivers: demand block (emp growth, wage, in-migration, pop growth) predicts rent; R2>=.30, >=1 driver sig correct sign.
H3 rent-outpaces-income: CoCs where rent rises faster than income show larger d_homeless.
Correlational; ordering by timescale. SE clustered by CoC for the panel.
"""
import json
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy.stats import ttest_ind, pearsonr

ROOT = Path(r"D:/IDP")
OUT = ROOT/"analysis/CLTR_paper7_prereg032_results_2026_05_29.json"

tp = pd.read_csv(ROOT/"analysis/paper7_coc_timepanel_2012_2024.csv")
ld = pd.read_csv(ROOT/"analysis/paper7_coc_longdiff_2012_2024.csv")
dd = pd.read_csv(ROOT/"analysis/paper7_demand_drivers_coc.csv")

res = {"pre_reg": "PRE_REG_032", "framing": "correlational; ordering by timescale; panel SE clustered by CoC"}

# ---------- H1: two-way FE (CoC + year), levels, clustered by CoC ----------
p = tp.dropna(subset=["rent_coc","income_coc","homeless_per_10k"]).copy()
for v in ["homeless_per_10k","rent_coc","income_coc"]:
    cm = p.groupby("coc_number")[v].transform("mean")
    ym = p.groupby("year")[v].transform("mean")
    p[v+"_w"] = p[v] - cm - ym + p[v].mean()
m = sm.OLS(p["homeless_per_10k_w"], sm.add_constant(p[["rent_coc_w","income_coc_w"]])).fit(
        cov_type="cluster", cov_kwds={"groups": p["coc_number"]})
twfe = {x: {"coef": round(float(m.params[x]),4), "p": round(float(m.pvalues[x]),4)} for x in ["rent_coc_w","income_coc_w"]}
# long-difference concurrence
l = ld.dropna(subset=["d_rent","d_income","d_homeless"])
ml = sm.OLS(l["d_homeless"], sm.add_constant(l[["d_rent","d_income"]])).fit(cov_type="HC1")
longdiff = {x: {"coef": round(float(ml.params[x]),4), "p": round(float(ml.pvalues[x]),4)} for x in ["d_rent","d_income"]}
within_sig = (twfe["rent_coc_w"]["p"]<0.05 and twfe["rent_coc_w"]["coef"]>0) or \
             (twfe["income_coc_w"]["p"]<0.05)
ld_concurs = (longdiff["d_rent"]["p"]<0.05 and longdiff["d_rent"]["coef"]>0) or \
             (longdiff["d_income"]["p"]<0.05)
res["H1_dynamic_within_place"] = {"n_coc_years": int(len(p)), "n_coc": int(p.coc_number.nunique()),
    "twoway_FE_clustered": twfe, "long_difference_HC1": longdiff,
    "within_significant": bool(within_sig), "longdiff_concurs": bool(ld_concurs),
    "disposition": ("H1 SUPPORTED — within-place dynamic displacement" if (within_sig and ld_concurs)
                    else "F1 FIRES — within-CoC null; cross-section was between-place" if not within_sig
                    else "H1 PARTIAL — within sig but long-diff does not concur")}

# ---------- H2: demand drivers -> rent (level 2024 and change) ----------
drivers = ["employment_growth_12_23","avg_weekly_wage_2023","in_migration_rate","population_growth_12_24"]
d2 = dd.merge(ld[["coc_number","rent_2024","d_rent"]], on="coc_number", how="inner").dropna(subset=drivers+["rent_2024","d_rent"])
def fit_block(y):
    mm = sm.OLS(d2[y], sm.add_constant(d2[drivers])).fit(cov_type="HC1")
    sds = d2[drivers].std()
    return {"r2": round(float(mm.rsquared),4),
            "drivers": {x: {"coef": round(float(mm.params[x]),5), "p": round(float(mm.pvalues[x]),4),
                            "std_beta": round(float(mm.params[x]*sds[x]/d2[y].std()),4)} for x in drivers}}
rent_level = fit_block("rent_2024"); rent_change = fit_block("d_rent")
sig_correct = [x for x in drivers if rent_level["drivers"][x]["p"]<0.05 and rent_level["drivers"][x]["coef"]>0]
res["H2_demand_drivers"] = {"n": int(len(d2)), "rent_LEVEL_2024_model": rent_level, "rent_CHANGE_model": rent_change,
    "level_R2>=0.30": bool(rent_level["r2"]>=0.30), "level_sig_positive_drivers": sig_correct,
    "disposition": ("H2 SUPPORTED — demand block predicts rent, >=1 driver sig" if (rent_level["r2"]>=0.30 and sig_correct)
                    else "F2 FIRES — rent demand not explained by these drivers" if not sig_correct
                    else "H2 PARTIAL — drivers sig but R2<0.30")}

# ---------- H3: rent-outpaces-income -> larger d_homeless ----------
h = ld.dropna(subset=["rent_2012","rent_2024","income_2012","income_2024","d_homeless"]).copy()
h["rent_g"] = (h.rent_2024-h.rent_2012)/h.rent_2012
h["inc_g"] = (h.income_2024-h.income_2012)/h.income_2012
h["gap"] = h.rent_g - h.inc_g
outpace = h[h.gap>0]["d_homeless"]; keep = h[h.gap<=0]["d_homeless"]
t,pt = ttest_ind(outpace, keep, equal_var=False)
mg = sm.OLS(h["d_homeless"], sm.add_constant(h[["gap"]])).fit(cov_type="HC1")
res["H3_rent_outpaces_income"] = {"n": int(len(h)), "n_outpace": int((h.gap>0).sum()),
    "mean_d_homeless_outpace": round(float(outpace.mean()),3), "mean_d_homeless_keep": round(float(keep.mean()),3),
    "welch_t": round(float(t),3), "welch_p": round(float(pt),4),
    "gap_coef": round(float(mg.params["gap"]),4), "gap_p": round(float(mg.pvalues["gap"]),4),
    "disposition": ("H3 SUPPORTED — incumbent-outbidding signature" if (pt<0.05 and outpace.mean()>keep.mean())
                    else "H3 n.s. — no rent-outpaces-income signature")}

OUT.write_text(json.dumps(res, indent=2)); print(json.dumps(res, indent=2)); print("\nwrote", OUT)
