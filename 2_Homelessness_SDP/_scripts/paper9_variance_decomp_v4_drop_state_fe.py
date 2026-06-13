"""
Paper 9 Phase 1 - v4 sensitivity: drop state FE, see if track effect surfaces.

Diagnosis of v2/v3: with state + origin + cohort all as FE, the (state, origin,
cohort)-deterministic track shares get absorbed by the FE block. State FE in
particular ate ~all the cross-state track variation that WRAPS + MPI provide
(both vary primarily by state).

Sensitivity: drop state FE; let cross-state variation enter via track shares
instead of state dummies. Controls remain: origin + cohort + age. This is one
of three pre-reg-acknowledged variants ("report under multiple FE specifications";
PRE_REG_042 sec 3 acknowledges cross-walk + ID uncertainty).
"""
from __future__ import annotations
import sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

ACS = Path("D:/IDP/data/paper9/acs/acs5_2024_pums_origins.csv")
CW  = Path("D:/IDP/data/paper9/crosswalk/crosswalk_v2_state_origin_cohort_4track.csv")
OUT_DIR = Path("D:/IDP/data/paper9/variance_decomp")

FIPS_TO_STATE = {
    "01":"Alabama","02":"Alaska","04":"Arizona","05":"Arkansas","06":"California",
    "08":"Colorado","09":"Connecticut","10":"Delaware","11":"District of Columbia",
    "12":"Florida","13":"Georgia","15":"Hawaii","16":"Idaho","17":"Illinois",
    "18":"Indiana","19":"Iowa","20":"Kansas","21":"Kentucky","22":"Louisiana",
    "23":"Maine","24":"Maryland","25":"Massachusetts","26":"Michigan","27":"Minnesota",
    "28":"Mississippi","29":"Missouri","30":"Montana","31":"Nebraska","32":"Nevada",
    "33":"New Hampshire","34":"New Jersey","35":"New Mexico","36":"New York",
    "37":"North Carolina","38":"North Dakota","39":"Ohio","40":"Oklahoma","41":"Oregon",
    "42":"Pennsylvania","44":"Rhode Island","45":"South Carolina","46":"South Dakota",
    "47":"Tennessee","48":"Texas","49":"Utah","50":"Vermont","51":"Virginia",
    "53":"Washington","54":"West Virginia","55":"Wisconsin","56":"Wyoming",
}
SCHL_TO_YEARS = {1:0,2:0,3:1,4:2,5:3,6:4,7:5,8:6,9:7,10:8,11:9,12:10,13:11,14:12,15:12,
                  16:12,17:12,18:13,19:14,20:14,21:16,22:18,23:20,24:22}


def main():
    df = pd.read_csv(ACS)
    df["state"] = df["state_fips"].astype(str).str.zfill(2).map(FIPS_TO_STATE)
    bins = [1988,2017,2019,2021,2023,2025]
    labels = ["pre-2018","2018-2019","2020-2021","2022-2023","2024"]
    df["cohort"] = pd.cut(df["YOEP"], bins=bins, labels=labels, include_lowest=True).astype(str)
    df = df[(df["AGEP"]>=16) & (df["AGEP"]<=64)].copy()
    df["edu_years"] = df["SCHL"].map(SCHL_TO_YEARS).fillna(0).astype(float)
    df["in_lf"]    = df["ESR"].isin([1,2,3,4,5]).astype(int)
    df["employed"] = df["ESR"].isin([1,2,4,5]).astype(int)
    df["formal_emp"] = ((df["ESR"].isin([1,2])) & (df["COW"].isin([1,2,3,4,5]))).astype(int)
    df["snap"]     = (df["FS"]==1).astype(int)
    df["medicaid"] = (df["HINS4"]==1).astype(int)
    df["eng_well"] = (df["ENG"].isin([0,1,2]) | df["ENG"].isna()).astype(int)
    df["log_wagp"] = np.log1p(df["WAGP"].clip(lower=0))
    df["age_c"] = df["AGEP"] - 40

    cw = pd.read_csv(CW)
    df = df.merge(cw[["state","origin","cohort","p_refugee","p_tps","p_undoc","p_residual"]],
                  on=["state","origin","cohort"], how="left").dropna(subset=["p_refugee","p_tps","p_undoc"])

    print(f"N={len(df):,}")
    outcomes = {
        "in_lf":"work_auth","employed":"work_auth","formal_emp":"work_auth",
        "log_wagp":"work_auth","snap":"work_auth","medicaid":"work_auth",
        "eng_well":"human_cap","edu_years":"human_cap",
    }
    TRACK = "p_refugee + p_tps + p_undoc"

    def R2(f, d):
        try: return smf.ols(f, data=d).fit().rsquared
        except: return np.nan

    results = []
    for y, otype in outcomes.items():
        sub = df[[y,"p_refugee","p_tps","p_undoc","origin","cohort","state","age_c"]].dropna()

        # Spec WITHOUT state FE
        r2_full   = R2(f"{y} ~ {TRACK} + age_c + C(origin) + C(cohort)", sub)
        r2_no_track  = R2(f"{y} ~ age_c + C(origin) + C(cohort)", sub)
        r2_no_origin = R2(f"{y} ~ {TRACK} + age_c + C(cohort)", sub)
        r2_no_cohort = R2(f"{y} ~ {TRACK} + age_c + C(origin)", sub)

        dR2_track  = max(0.0, r2_full - r2_no_track)
        dR2_origin = max(0.0, r2_full - r2_no_origin)
        dR2_cohort = max(0.0, r2_full - r2_no_cohort)

        results.append({
            "outcome": y, "out_type": otype, "n_indiv": len(sub),
            "r2_full": r2_full,
            "dR2_track":  dR2_track,
            "dR2_origin": dR2_origin,
            "dR2_cohort": dR2_cohort,
            "track_gt_origin": dR2_track > dR2_origin,
        })
        print(f"  {y:>12s}: r2={r2_full:.4f}  dR2_track={dR2_track:.4f}  dR2_origin={dR2_origin:.4f}  track>origin={dR2_track>dR2_origin}")

    res = pd.DataFrame(results)
    res.to_csv(OUT_DIR / "v4_4track_no_state_FE_partial_R2.csv", index=False)

    print("\n=== v4: WITHOUT STATE FE (track gets cross-state lift) ===")
    print(res.to_string(index=False, float_format=lambda x: f"{x:.4f}" if isinstance(x,float) else str(x)))

    work = res[res["out_type"]=="work_auth"]
    hc = res[res["out_type"]=="human_cap"]

    h1_hits = (work["dR2_track"] >= 0.15).sum()
    h2_w = work["track_gt_origin"].sum()
    h2_h = (~hc["track_gt_origin"]).sum()
    print(f"\nH1 (track dR2 >= 0.15 work-auth): {h1_hits}/{len(work)}")
    print(f"H2 (work-auth: track > origin):   {h2_w}/{len(work)} (bar: >=3)")
    print(f"H2 (human-cap: origin > track):   {h2_h}/{len(hc)} (bar: >=1)")


if __name__ == "__main__":
    main()
