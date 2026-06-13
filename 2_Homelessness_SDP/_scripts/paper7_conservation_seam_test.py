"""
Seam / "one object?" test (EXPLORATORY; predictions pre-stated below).

Hypothesis: migration(pull) + homelessness(push) are one rent-displacement object,
sorted by RESOURCES. Resourced facing rent pressure CLEAR (out-migrate, visible in
IRS); unresourced fall into HOMELESSNESS (visible in PIT). Same force (rent),
outcome split by income.

Stock-vs-flow caveat: out-migration is an annual FLOW, PIT homelessness a one-night
STOCK -> NOT additively comparable. So we DROP literal sum-mass-balance and test the
resource-bifurcation signature instead:

PRE-STATED PREDICTIONS (one-object, resource-sorted):
 P1  rent -> out_migration > 0  AND  rent -> homelessness > 0  (both rent-driven)
 P2a income -> homelessness | rent  < 0   (suppression; resourced don't go homeless)
 P2b income -> out_migration | rent > 0   (resourced clear out instead)
 P3  log(homeless/outmig) ~ income | rent : income coef < 0 (mix tilts AWAY from
     homelessness as income rises = displacement routed to clean exit)
 -> P2a<0 AND P2b>0 together = the bifurcation = strongest "one object" evidence.
FALSIFIER: rent NOT driving out-migration, OR income NOT routing the split
 (P2b<=0 or P2a>=0) -> coupled-but-distinct, NOT one resource-sorted object.

Correlational; cross-sectional; cannot prove person-conservation (no linkage).
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler

ROOT=Path(r"D:/IDP")
OUTFLOW=Path(r"D:/Migration/data/raw/irs_soi/countyoutflow2223.csv")
XWALK=ROOT/"data/paper7/coc_crosswalk/county_coc_match.csv"
PANEL=ROOT/"analysis/paper7_metro_coc_panel_2024.csv"
OUT=ROOT/"analysis/paper7_conservation_seam_2026_05_28.json"

def zc(s): s=np.asarray(s,float); return (s-np.nanmean(s))/np.nanstd(s)

def main():
    o=pd.read_csv(OUTFLOW,encoding="latin-1")
    # origin-county total out-migrants = "Total Migration-US and Foreign" (y2 96/0), n2=exemptions
    tot=o[(o["y2_statefips"]==96)&(o["y2_countyfips"]==0)].copy()
    tot["county_fips"]=(tot["y1_statefips"].astype(int).map("{:02d}".format)
                        +tot["y1_countyfips"].astype(int).map("{:03d}".format))
    tot=tot[["county_fips","n2"]].rename(columns={"n2":"out_migrants"})

    xw=pd.read_csv(XWALK,encoding="latin-1")
    xw=xw.dropna(subset=["county_fips","pct_cnty_pop_coc"]).copy()
    xw["county_fips"]=xw["county_fips"].astype(float).map(lambda x:f"{int(round(x)):05d}")
    xw["w"]=xw["pct_cnty_pop_coc"].astype(float)/100.0
    m=xw.merge(tot,on="county_fips",how="left")
    m["alloc_out"]=m["out_migrants"]*m["w"]
    coc_out=m.groupby("coc_number",as_index=False)["alloc_out"].sum().rename(columns={"alloc_out":"coc_out_migrants"})

    p=pd.read_csv(PANEL).merge(coc_out,on="coc_number",how="left")
    p["out_migration_per_10k"]=p["coc_out_migrants"]/p["total_population"]*1e4
    d=p.dropna(subset=["homeless_per_10k","out_migration_per_10k","rent_coc","income_coc"]).copy()
    d=d[(d["out_migration_per_10k"]>0)&(d["homeless_per_10k"]>0)]

    res={"n":int(len(d)),"framing":"EXPLORATORY; predictions pre-stated; correlational; no person-linkage",
         "note":"out-migration=annual flow, homelessness=PIT stock -> tested resource-bifurcation, not additive mass-balance"}

    def ols(y,Xcols):
        X=sm.add_constant(np.column_stack([zc(d[c]) for c in Xcols]))
        mm=sm.OLS(zc(d[y]),X).fit()
        return {Xcols[i]:{"coef":round(float(mm.params[i+1]),3),"p":round(float(mm.pvalues[i+1]),4)} for i in range(len(Xcols))},round(float(mm.rsquared),3)

    # P1
    c_out,_=ols("out_migration_per_10k",["rent_coc","income_coc"])
    c_hl,_=ols("homeless_per_10k",["rent_coc","income_coc"])
    res["P1_both_rent_driven"]={"rent_to_outmig":c_out["rent_coc"],"rent_to_homeless":c_hl["rent_coc"],
        "pass":bool(c_out["rent_coc"]["coef"]>0 and c_hl["rent_coc"]["coef"]>0)}
    # P2a + P2b (the bifurcation): income at fixed rent
    res["P2a_income_to_homeless_neg"]={**c_hl["income_coc"],"pass":bool(c_hl["income_coc"]["coef"]<0 and c_hl["income_coc"]["p"]<0.05)}
    res["P2b_income_to_outmig_pos"]={**c_out["income_coc"],"pass":bool(c_out["income_coc"]["coef"]>0 and c_out["income_coc"]["p"]<0.05)}
    # P3 mix
    d["log_mix"]=np.log(d["homeless_per_10k"]/d["out_migration_per_10k"])
    c_mix,r2mix=ols("log_mix",["income_coc","rent_coc"])
    res["P3_mix_tilts_away_from_homeless_with_income"]={**c_mix["income_coc"],"r2":r2mix,
        "pass":bool(c_mix["income_coc"]["coef"]<0 and c_mix["income_coc"]["p"]<0.05)}

    bifurcation = res["P2a_income_to_homeless_neg"]["pass"] and res["P2b_income_to_outmig_pos"]["pass"]
    res["VERDICT"]={
        "bifurcation_holds":bool(bifurcation),
        "both_rent_driven":res["P1_both_rent_driven"]["pass"],
        "reading":(
            "CONSISTENT WITH ONE RESOURCE-SORTED OBJECT: rent drives both displacement modes; "
            "income routes the outcome (protective vs homelessness, predicts clean out-migration)."
            if (bifurcation and res["P1_both_rent_driven"]["pass"]) else
            "NOT one resource-sorted object at this resolution: " +
            ("rent does not drive out-migration; " if not res["P1_both_rent_driven"]["pass"] else "")+
            ("income does not route the split (bifurcation fails)" if not bifurcation else "")
        )}
    # extra context: raw correlations + scales
    res["context"]={
        "median_out_migration_per_10k":round(float(d["out_migration_per_10k"].median()),1),
        "median_homeless_per_10k":round(float(d["homeless_per_10k"].median()),1),
        "corr_rent_outmig":round(float(np.corrcoef(d["rent_coc"],d["out_migration_per_10k"])[0,1]),3),
        "corr_rent_homeless":round(float(np.corrcoef(d["rent_coc"],d["homeless_per_10k"])[0,1]),3)}
    OUT.write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2)); print("\nwrote",OUT)

if __name__=="__main__": main()
