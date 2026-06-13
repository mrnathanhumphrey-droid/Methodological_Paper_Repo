"""
Paper 9 Phase 1 - v3 individual-level variance decomp on the v2 4-track cross-walk.

Adds MPI Undocumented as a 4th track to the v1 (3-track: Refugee + TPS + Residual).
Now 4-track: Refugee + TPS + Undocumented + Residual (LPR-other / Asylum / SIV /
Parole / etc. — still pooled; full 7-track waits for EOIR + SIV + CHNV/UFU).

PRE_REG_042 first-pass check: does track variation increase materially over v1
(track dR^2 ~0.0001-0.0008)? Does the differential (work-auth vs human-cap) now
become visible?
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
OUT_DIR.mkdir(parents=True, exist_ok=True)

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
SCHL_TO_YEARS = {
    1:0,2:0,3:1,4:2,5:3,6:4,7:5,8:6,9:7,10:8,11:9,12:10,13:11,14:12,15:12,
    16:12,17:12,18:13,19:14,20:14,21:16,22:18,23:20,24:22,
}


def load_individual():
    df = pd.read_csv(ACS)
    df["state"] = df["state_fips"].astype(str).str.zfill(2).map(FIPS_TO_STATE)
    bins = [1988, 2017, 2019, 2021, 2023, 2025]
    labels = ["pre-2018","2018-2019","2020-2021","2022-2023","2024"]
    df["cohort"] = pd.cut(df["YOEP"], bins=bins, labels=labels, include_lowest=True).astype(str)
    df = df[(df["AGEP"] >= 16) & (df["AGEP"] <= 64)].copy()
    df["edu_years"] = df["SCHL"].map(SCHL_TO_YEARS).fillna(0).astype(float)
    df["in_lf"]    = df["ESR"].isin([1,2,3,4,5]).astype(int)
    df["employed"] = df["ESR"].isin([1,2,4,5]).astype(int)
    df["formal_emp"] = ((df["ESR"].isin([1,2])) & (df["COW"].isin([1,2,3,4,5]))).astype(int)
    df["snap"]     = (df["FS"] == 1).astype(int)
    df["medicaid"] = (df["HINS4"] == 1).astype(int)
    df["eng_well"] = (df["ENG"].isin([0,1,2]) | df["ENG"].isna()).astype(int)
    df["log_wagp"] = np.log1p(df["WAGP"].clip(lower=0))
    df["age_c"] = df["AGEP"] - 40
    return df


def main():
    df = load_individual()
    cw = pd.read_csv(CW)
    df = df.merge(cw[["state","origin","cohort","p_refugee","p_tps","p_undoc","p_residual"]],
                  on=["state","origin","cohort"], how="left")
    df = df.dropna(subset=["p_refugee","p_tps","p_undoc"])
    print(f"N individuals: {len(df):,}")

    outcomes = {
        "in_lf":      ("work_auth", "Labor-force participation"),
        "employed":   ("work_auth", "Employed"),
        "formal_emp": ("work_auth", "Formal employment"),
        "log_wagp":   ("work_auth", "Log(wage+1)"),
        "snap":       ("work_auth", "SNAP receipt"),
        "medicaid":   ("work_auth", "Medicaid receipt"),
        "eng_well":   ("human_cap", "English well/native"),
        "edu_years":  ("human_cap", "Years of education"),
    }

    def fit_R2(formula: str, data: pd.DataFrame) -> float:
        try:
            return smf.ols(formula, data=data).fit().rsquared
        except Exception:
            return np.nan

    # 3 track variables: p_refugee, p_tps, p_undoc (p_residual is reference)
    TRACK = "p_refugee + p_tps + p_undoc"

    results = []
    for y, (otype, label) in outcomes.items():
        sub = df[[y,"p_refugee","p_tps","p_undoc","origin","cohort","state","age_c"]].dropna()
        if len(sub) < 500:
            continue

        r2_full = fit_R2(f"{y} ~ {TRACK} + age_c + C(origin) + C(cohort) + C(state)", sub)
        r2_no_track  = fit_R2(f"{y} ~ age_c + C(origin) + C(cohort) + C(state)", sub)
        r2_no_origin = fit_R2(f"{y} ~ {TRACK} + age_c + C(cohort) + C(state)", sub)
        r2_no_cohort = fit_R2(f"{y} ~ {TRACK} + age_c + C(origin) + C(state)", sub)
        r2_no_state  = fit_R2(f"{y} ~ {TRACK} + age_c + C(origin) + C(cohort)", sub)
        r2_no_age    = fit_R2(f"{y} ~ {TRACK} + C(origin) + C(cohort) + C(state)", sub)

        dR2_track  = max(0.0, r2_full - r2_no_track)
        dR2_origin = max(0.0, r2_full - r2_no_origin)
        dR2_cohort = max(0.0, r2_full - r2_no_cohort)
        dR2_state  = max(0.0, r2_full - r2_no_state)
        dR2_age    = max(0.0, r2_full - r2_no_age)

        results.append({
            "outcome": y, "label": label, "out_type": otype,
            "n_indiv": len(sub),
            "r2_full": r2_full,
            "dR2_track":  dR2_track,
            "dR2_origin": dR2_origin,
            "dR2_cohort": dR2_cohort,
            "dR2_state":  dR2_state,
            "dR2_age":    dR2_age,
            "track_gt_origin": dR2_track > dR2_origin,
        })
        print(f"  {y:>12s}: r2={r2_full:.4f}  dR2_track={dR2_track:.4f}  dR2_origin={dR2_origin:.4f}  track>origin={dR2_track>dR2_origin}")

    res = pd.DataFrame(results)
    res.to_csv(OUT_DIR / "v3_4track_individual_partial_R2_table.csv", index=False)

    print("\n=== v3 4-TRACK INDIVIDUAL-LEVEL PARTIAL-R^2 TABLE ===")
    print(res[["outcome","out_type","n_indiv","r2_full","dR2_track","dR2_origin","dR2_cohort","dR2_state","track_gt_origin"]].to_string(index=False, float_format=lambda x: f"{x:.4f}" if isinstance(x,float) else str(x)))

    work = res[res["out_type"]=="work_auth"]
    hc = res[res["out_type"]=="human_cap"]

    h1_hits = (work["dR2_track"] >= 0.15).sum()
    print(f"\n*** PRE_REG_042 H1 v2 4-track ***")
    print(f"  track dR2 >= 0.15 on {h1_hits} of {len(work)} work-auth-dep outcomes (bar: >= 3)")

    h2_work_hits = work["track_gt_origin"].sum()
    h2_hc_hits = (~hc["track_gt_origin"]).sum()
    print(f"\n*** PRE_REG_042 H2 LOAD-BEARING DIFFERENTIAL v2 4-track ***")
    print(f"  work-auth: track > origin on {h2_work_hits}/{len(work)} (bar: >= 3 of 5)")
    print(f"  human-cap: origin > track on {h2_hc_hits}/{len(hc)} (bar: >= 1 of 2)")

    # Direction comparison vs v1
    print(f"\n=== v1 -> v2 LIFT IN TRACK dR^2 ===")
    try:
        v1 = pd.read_csv(OUT_DIR / "v2_individual_partial_R2_table.csv")
        joined = res.merge(v1[["outcome","dR2_track"]].rename(columns={"dR2_track":"dR2_track_v1"}),
                            on="outcome", how="left")
        joined["lift"] = joined["dR2_track"] - joined["dR2_track_v1"]
        print(joined[["outcome","out_type","dR2_track_v1","dR2_track","lift"]].to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    except Exception:
        pass


if __name__ == "__main__":
    main()
