"""
Paper 9 Phase 1 - v6 variance decomposition on the v3 7-track cross-walk.

THIS IS THE LOAD-BEARING FIRE OF PRE_REG_042 H1 + H2.

7-track variables: p_refugee, p_tps, p_asylum, p_siv, p_parole, p_undoc
(p_residual = reference category).

Specifications run (per PRE_REG_042 sec 3 sensitivity reporting):
 - v6a: state + origin + cohort + age FE (full per-pre-reg)
 - v6b: no state FE (lets cross-state track variation enter)
 - v6c: no origin FE (lets origin variation enter via track shares)

The H2 differential test (load-bearing):
 - work-auth-dep outcomes (LFP/employment/wages/SNAP/Medicaid): track > origin
 - human-cap-dep outcomes (English/education): origin > track
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
CW  = Path("D:/IDP/data/paper9/crosswalk/crosswalk_v3_state_origin_cohort_7track.csv")
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

TRACK = "p_refugee + p_tps + p_asylum + p_siv + p_parole + p_undoc"


def load_individual():
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
    return df


def fit_R2(formula, data):
    try: return smf.ols(formula, data=data).fit().rsquared
    except: return np.nan


def run_spec(df, label, base_fe):
    """base_fe is the FE block to include (e.g., 'C(origin) + C(cohort) + C(state)')."""
    outcomes = {
        "in_lf":"work_auth","employed":"work_auth","formal_emp":"work_auth",
        "log_wagp":"work_auth","snap":"work_auth","medicaid":"work_auth",
        "eng_well":"human_cap","edu_years":"human_cap",
    }
    fe_parts = base_fe.split(" + ")
    results = []
    for y, otype in outcomes.items():
        sub = df[[y,"p_refugee","p_tps","p_asylum","p_siv","p_parole","p_undoc",
                   "origin","cohort","state","age_c"]].dropna()

        full_formula = f"{y} ~ {TRACK} + age_c + {base_fe}"
        r2_full = fit_R2(full_formula, sub)
        r2_no_track = fit_R2(f"{y} ~ age_c + {base_fe}", sub)
        dR2_track = max(0.0, r2_full - r2_no_track)

        # Drop origin (if present)
        if "C(origin)" in base_fe:
            no_orig = " + ".join(x for x in fe_parts if x != "C(origin)")
            r2_no_orig = fit_R2(f"{y} ~ {TRACK} + age_c{(' + '+no_orig) if no_orig else ''}", sub)
            dR2_origin = max(0.0, r2_full - r2_no_orig)
        else:
            dR2_origin = np.nan

        results.append({
            "spec": label, "outcome": y, "out_type": otype, "n_indiv": len(sub),
            "r2_full": r2_full, "dR2_track": dR2_track, "dR2_origin": dR2_origin,
            "track_gt_origin": (not np.isnan(dR2_origin)) and (dR2_track > dR2_origin),
        })
    return pd.DataFrame(results)


def main():
    df = load_individual()
    cw = pd.read_csv(CW)
    df = df.merge(cw[["state","origin","cohort","p_refugee","p_tps","p_asylum",
                       "p_siv","p_parole","p_undoc","p_residual"]],
                  on=["state","origin","cohort"], how="left").dropna(subset=["p_refugee"])
    print(f"N individuals: {len(df):,}")

    specs = [
        ("v6a_full_FE",     "C(origin) + C(cohort) + C(state)"),
        ("v6b_no_state_FE", "C(origin) + C(cohort)"),
        ("v6c_no_origin_FE","C(cohort) + C(state)"),
    ]

    all_results = []
    for label, fe in specs:
        print(f"\n=== {label}: {fe} ===")
        r = run_spec(df, label, fe)
        all_results.append(r)
        print(r[["outcome","out_type","n_indiv","r2_full","dR2_track","dR2_origin","track_gt_origin"]]
              .to_string(index=False, float_format=lambda x: f"{x:.4f}" if isinstance(x,float) else str(x)))

    full = pd.concat(all_results, ignore_index=True)
    full.to_csv(OUT_DIR / "v6_7track_partial_R2_all_specs.csv", index=False)

    # H1 + H2 check per spec
    print("\n" + "="*60)
    print("*** PRE_REG_042 H1/H2 LOAD-BEARING FIRE (v3 7-track) ***")
    print("="*60)
    for label, fe in specs:
        r = full[full["spec"]==label]
        work = r[r["out_type"]=="work_auth"]
        hc   = r[r["out_type"]=="human_cap"]
        h1_hits = (work["dR2_track"] >= 0.15).sum()
        h2_work = work["track_gt_origin"].sum() if "C(origin)" in fe else float('nan')
        h2_hc = (~hc["track_gt_origin"]).sum() if "C(origin)" in fe else float('nan')
        print(f"\n{label}:")
        print(f"  H1: track dR2 >= 0.15 on {h1_hits}/{len(work)} work-auth outcomes (bar: >= 3)")
        if "C(origin)" in fe:
            print(f"  H2 work-auth: track > origin on {h2_work}/{len(work)} (bar: >= 3 of 5)")
            print(f"  H2 human-cap: origin > track on {h2_hc}/{len(hc)} (bar: >= 1 of 2)")

    # Across all specs, did ANY of them satisfy H1 or H2?
    h1_any = (full[full["out_type"]=="work_auth"]["dR2_track"] >= 0.15).any()
    h2_any = full[full["out_type"]=="work_auth"]["track_gt_origin"].any()
    print(f"\n>>> Across ANY of the 3 specs: H1 (track>=0.15) anywhere? {h1_any}; track>origin anywhere? {h2_any}")


if __name__ == "__main__":
    main()
