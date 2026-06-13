"""
PRE-REG 039 seam closure — SENTINEL-CLEAN (supersedes the contaminated first run).

FEA carries sentinels (CT food = -8888; 11 POVRATE counties <0, min -9999; 8 food
out-of-range). All FEA percentage columns are filtered to valid [0,100] BEFORE state
aggregation. State level n=51. Output: analysis/FOOD_seam_closure_039.json

Sections:
  A. seam correlations + D1-D4 falsifiers (food insecurity = poverty's display = push gauge)
  B. FLOW test: does origin food-insec/poverty drive OUT-MIGRATION? (Migration ACS events)
  C. recursive decomposition: homelessness -> street vs sheltered (different drivers => fractal)
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

IDP = Path(r"D:\IDP")
FEAX = r"D:\Food Deserts\data_raw\FEA\2025-food-environment-atlas-data.xlsx"
EV = r"D:\Migration\data\derived\event_observables.parquet"
POP = r"D:\Migration\data\derived\migpuma_population_2010.parquet"
COC = IDP / "analysis" / "paper7_coc_timepanel_2012_2024.csv"
PULSE = IDP / "analysis" / "paper7_pulse_housing_precarity.csv"
FIPS2USPS = {1:'AL',2:'AK',4:'AZ',5:'AR',6:'CA',8:'CO',9:'CT',10:'DE',11:'DC',12:'FL',13:'GA',15:'HI',16:'ID',17:'IL',18:'IN',19:'IA',20:'KS',21:'KY',22:'LA',23:'ME',24:'MD',25:'MA',26:'MI',27:'MN',28:'MS',29:'MO',30:'MT',31:'NE',32:'NV',33:'NH',34:'NJ',35:'NM',36:'NY',37:'NC',38:'ND',39:'OH',40:'OK',41:'OR',42:'PA',44:'RI',45:'SC',46:'SD',47:'TN',48:'TX',49:'UT',50:'VT',51:'VA',53:'WA',54:'WV',55:'WI',56:'WY'}
NAME2USPS = {v.lower(): v for v in FIPS2USPS.values()}
NAME2USPS.update({'alabama':'AL','alaska':'AK','arizona':'AZ','arkansas':'AR','california':'CA','colorado':'CO','connecticut':'CT','delaware':'DE','district of columbia':'DC','florida':'FL','georgia':'GA','hawaii':'HI','idaho':'ID','illinois':'IL','indiana':'IN','iowa':'IA','kansas':'KS','kentucky':'KY','louisiana':'LA','maine':'ME','maryland':'MD','massachusetts':'MA','michigan':'MI','minnesota':'MN','mississippi':'MS','missouri':'MO','montana':'MT','nebraska':'NE','nevada':'NV','new hampshire':'NH','new jersey':'NJ','new mexico':'NM','new york':'NY','north carolina':'NC','north dakota':'ND','ohio':'OH','oklahoma':'OK','oregon':'OR','pennsylvania':'PA','rhode island':'RI','south carolina':'SC','south dakota':'SD','tennessee':'TN','texas':'TX','utah':'UT','vermont':'VT','virginia':'VA','washington':'WA','west virginia':'WV','wisconsin':'WI','wyoming':'WY'})


def valid_pct(s):
    return pd.to_numeric(s, errors="coerce").where(lambda x: (x >= 0) & (x <= 100))


def wm(d, v, w):
    x = d.dropna(subset=[v, w])
    return np.average(x[v], weights=x[w]) if len(x) else np.nan


def corr(df, a, b):
    x = df.dropna(subset=[a, b])
    r, p = stats.pearsonr(x[a], x[b])
    return {"r": round(float(r), 3), "p": round(float(p), 4), "n": int(len(x))}


def main():
    out = {"note": "sentinel-clean: FEA pct cols filtered to [0,100] before aggregation", "sentinels": {}}
    ins = pd.read_excel(FEAX, sheet_name="INSECURITY", header=1)
    soc = pd.read_excel(FEAX, sheet_name="SOCIOECONOMIC", header=1)
    out["sentinels"]["food_out_of_range_counties"] = int(((ins.FOODINSEC_21_23 < 0) | (ins.FOODINSEC_21_23 > 100)).sum())
    out["sentinels"]["pov_negative_counties"] = int((soc.POVRATE21 < 0).sum())
    ins["fi"] = valid_pct(ins.FOODINSEC_21_23)
    soc["pv"] = valid_pct(soc.POVRATE21)
    food = ins.groupby("State").fi.mean().rename("food_insec")
    pov = soc.groupby("State").pv.mean().rename("poverty")

    coc = pd.read_csv(COC)
    yr = int(coc.dropna(subset=["homeless_per_10k"]).year.max())
    c = coc[coc.year == yr].copy()
    c["st"] = c.coc_number.str[:2]
    rent = c.groupby("st").apply(lambda d: wm(d, "rent_coc", "total_population")).rename("rent_floor")
    hom = c.groupby("st").apply(lambda d: wm(d, "homeless_per_10k", "total_population")).rename("homeless")

    pul = pd.read_csv(PULSE)
    ps = pul[pul.geo_type.astype(str).str.lower().str.contains("state")].copy()
    if len(ps) == 0:
        ps = pul.copy()
    ps["st"] = ps.geography.map(lambda g: g.strip().upper() if str(g).strip().upper() in FIPS2USPS.values() else NAME2USPS.get(str(g).strip().lower()))
    prec = ps.groupby("st").agg(behind_on_rent=("behind_on_rent_share", "mean"),
                                eviction_risk=("eviction_risk_share", "mean"))

    # FARA food floor (state) + out-migration (Migration events)
    ev = pd.read_parquet(EV); nyr = ev.YEAR.nunique()
    oos = (ev[ev.orig_state != ev.dest_state].groupby("orig_state").PERWT.sum() / nyr)
    spop = pd.read_parquet(POP).groupby(["statefip", "year"]).population.sum().groupby("statefip").mean()
    om = pd.DataFrame({"oos": oos, "pop": spop}).dropna()
    om["st"] = om.index.map(FIPS2USPS)
    om = om.dropna(subset=["st"]).set_index("st")
    om["outmig_oos_per1k"] = 1000 * om.oos / om["pop"]

    M = pd.concat([food, pov, rent, hom, prec, om.outmig_oos_per1k], axis=1).dropna(subset=["food_insec", "poverty", "homeless", "rent_floor"])
    out["n"] = int(len(M)); out["homeless_year"] = yr
    out["poverty_range"] = [round(M.poverty.min(), 1), round(M.poverty.max(), 1)]
    out["food_range"] = [round(M.food_insec.min(), 1), round(M.food_insec.max(), 1)]

    # ---- A. seam correlations ----
    out["corr"] = {f"{a}~{b}": corr(M, a, b) for a, b in [
        ("poverty", "food_insec"), ("food_insec", "homeless"), ("rent_floor", "homeless"),
        ("poverty", "homeless"), ("behind_on_rent", "food_insec"), ("behind_on_rent", "homeless"),
        ("eviction_risk", "homeless"), ("food_insec", "outmig_oos_per1k"),
        ("poverty", "outmig_oos_per1k"), ("rent_floor", "outmig_oos_per1k")]}

    def reg(y, xs, d=M):
        x = d.dropna(subset=[y] + xs); X = sm.add_constant(x[xs])
        r = sm.OLS(x[y], X).fit(cov_type="HC1")
        return {k: {"b": round(float(r.params[k]), 4), "p": round(float(r.pvalues[k]), 4)} for k in xs} | {"r2": round(float(r.rsquared), 3)}
    out["reg_homeless"] = reg("homeless", ["rent_floor", "poverty"])
    out["reg_food"] = reg("food_insec", ["poverty", "rent_floor"])

    # ---- C. recursive decomposition: street vs sheltered (CoC level) ----
    cc = coc[coc.year == yr].dropna(subset=["homeless_per_10k", "unsheltered_per_10k", "rent_coc", "income_coc"]).copy()
    cc["sheltered_per_10k"] = (cc.homeless_per_10k - cc.unsheltered_per_10k).clip(lower=0)

    def reg_coc(y):
        X = sm.add_constant(cc[["rent_coc", "income_coc"]].astype(float))
        r = sm.OLS(np.log1p(cc[y]), X).fit(cov_type="HC1")
        return {"rent_b": round(float(r.params["rent_coc"]), 5), "rent_p": round(float(r.pvalues["rent_coc"]), 4), "r2": round(float(r.rsquared), 3)}
    out["decomp_street_sheltered"] = {"n_coc": int(len(cc)),
                                      "unsheltered": reg_coc("unsheltered_per_10k"),
                                      "sheltered": reg_coc("sheltered_per_10k")}

    (IDP / "analysis" / "FOOD_seam_closure_039.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({k: out[k] for k in ["n", "sentinels", "poverty_range", "food_range", "corr"]}, indent=2))
    print("reg homeless~rent+pov:", out["reg_homeless"])
    print("reg food~pov+rent:", out["reg_food"])
    print("decomp street/sheltered:", out["decomp_street_sheltered"])


if __name__ == "__main__":
    main()
