"""
Paper 9 Phase 1 - v5: refugee-heavy origin subset analysis.

Restrict to origins where p_refugee is the dominant or substantial track share:
DRC (24%), Syria (8%), Myanmar (7%), Eritrea (6%), Afghanistan (5%). For these
5, the Refugee track has REAL cross-state variation (WRAPS gives state x origin
x FY directly). Test whether track ΔR² lifts when origin variation is restricted
to a refugee-dominated subset.

Identification logic: if track effect is real but obscured by origin colinearity
in the full 15-origin sample, the refugee-heavy subset reveals it because (a)
all 5 origins have substantial refugee shares (track variation is REAL within
subset), (b) origin effects vary less starkly within subset (all 5 are MENA/Africa
refugee-origins with similar baseline characteristics), (c) state-level WRAPS
variation is the cleanest exogenous source.
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

REFUGEE_HEAVY = ["DRC","Syria","Myanmar","Eritrea","Afghanistan"]


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
                  on=["state","origin","cohort"], how="left").dropna(subset=["p_refugee"])

    # Subset: refugee-heavy origins
    sub = df[df["origin"].isin(REFUGEE_HEAVY)].copy()
    print(f"All P9: N={len(df):,}; refugee-heavy subset: N={len(sub):,} (origins: {sorted(sub['origin'].unique())})")

    # Show per-origin p_refugee variation
    print("\np_refugee variation (cell-level summary) by origin in subset:")
    cw_sub = cw[cw["origin"].isin(REFUGEE_HEAVY)]
    print(cw_sub.groupby("origin")["p_refugee"].describe()[["mean","std","min","max"]].round(3).to_string())

    outcomes = {
        "in_lf":"work_auth","employed":"work_auth","formal_emp":"work_auth",
        "log_wagp":"work_auth","snap":"work_auth","medicaid":"work_auth",
        "eng_well":"human_cap","edu_years":"human_cap",
    }
    TRACK = "p_refugee + p_tps + p_undoc"

    def R2(f, d):
        try: return smf.ols(f, data=d).fit().rsquared
        except: return np.nan

    print("\n=== REFUGEE-HEAVY SUBSET: variance decomp WITHOUT state FE ===")
    results = []
    for y, otype in outcomes.items():
        s = sub[[y,"p_refugee","p_tps","p_undoc","origin","cohort","state","age_c"]].dropna()
        r2_full   = R2(f"{y} ~ {TRACK} + age_c + C(origin) + C(cohort)", s)
        r2_no_track  = R2(f"{y} ~ age_c + C(origin) + C(cohort)", s)
        r2_no_origin = R2(f"{y} ~ {TRACK} + age_c + C(cohort)", s)
        r2_no_cohort = R2(f"{y} ~ {TRACK} + age_c + C(origin)", s)

        dR2_track  = max(0.0, r2_full - r2_no_track)
        dR2_origin = max(0.0, r2_full - r2_no_origin)
        dR2_cohort = max(0.0, r2_full - r2_no_cohort)

        results.append({
            "outcome": y, "out_type": otype, "n_indiv": len(s),
            "r2_full": r2_full,
            "dR2_track": dR2_track, "dR2_origin": dR2_origin, "dR2_cohort": dR2_cohort,
            "track_gt_origin": dR2_track > dR2_origin,
        })
        print(f"  {y:>12s}: n={len(s):>5d}  r2={r2_full:.4f}  dR2_track={dR2_track:.4f}  dR2_origin={dR2_origin:.4f}  track>origin={dR2_track>dR2_origin}")

    res = pd.DataFrame(results)
    res.to_csv(OUT_DIR / "v5_refugee_heavy_subset_partial_R2.csv", index=False)

    work = res[res["out_type"]=="work_auth"]
    hc = res[res["out_type"]=="human_cap"]
    h2_w = work["track_gt_origin"].sum()
    h2_h = (~hc["track_gt_origin"]).sum()
    print(f"\nH2 (work-auth: track > origin): {h2_w}/{len(work)}")
    print(f"H2 (human-cap: origin > track): {h2_h}/{len(hc)}")


if __name__ == "__main__":
    main()
