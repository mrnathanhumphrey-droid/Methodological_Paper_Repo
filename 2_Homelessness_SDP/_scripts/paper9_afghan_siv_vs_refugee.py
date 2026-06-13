"""
Paper 9 Phase 1 - Afghan SIV vs Afghan Refugee parallel-track contrast.

PURPOSE: Afghans have TWO parallel admin tracks running side-by-side since 2014:
 - SIV (Special Immigrant Visa): full work auth + LPR-on-arrival, 40,488 cumulative
 - Refugee (USRAP): full work auth + LPR-after-1-year, ~14,000 ACS-window arrivals

Both are "full-rights" admin tracks but with different bureaucratic origins
(SIV = DOS/embassy-based for USG-affiliated; Refugee = USRAP/UNHCR-based for
generic-displacement). If the rights-bundle differs in subtle ways (e.g., SIVs
preserve more pre-displacement professional credentials; refugees go through
the cultural orientation pipeline), within-Afghan outcome differences should
track which channel they came through.

This is the cleanest TWO-TRACK CONTRAST inside Paper 9: same origin, two
admin-defined tracks with theoretically similar rights but operationally
different selection + landing.

Method:
 1. Subset to Afghans only (n ~ 6K working-age in ACS)
 2. For each (state, cohort) cell, p_siv and p_refugee shares vary independently
    (different geographic + temporal allocations)
 3. Run individual-level: outcome ~ p_siv + p_refugee + C(state) + C(cohort) + age
 4. Compare per-track coefficients (which is bigger?) + their joint dR^2
 5. Also: stratified analysis at cell level (cells with high-p_siv vs high-p_refugee)
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


def main():
    df = pd.read_csv(ACS)
    df["state"] = df["state_fips"].astype(str).str.zfill(2).map(FIPS_TO_STATE)
    bins = [1988,2017,2019,2021,2023,2025]
    labels = ["pre-2018","2018-2019","2020-2021","2022-2023","2024"]
    df["cohort"] = pd.cut(df["YOEP"], bins=bins, labels=labels, include_lowest=True).astype(str)
    df = df[(df["AGEP"]>=16) & (df["AGEP"]<=64)].copy()
    df = df[df["origin"] == "Afghanistan"].copy()
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
    df = df.merge(cw[["state","origin","cohort","p_refugee","p_siv","p_tps","p_asylum"]],
                  on=["state","origin","cohort"], how="left").dropna(subset=["p_refugee","p_siv"])
    print(f"Afghan working-age individuals: {len(df):,}")

    # Cell-level summary of p_siv vs p_refugee variation
    cell_summary = df.groupby(["state","cohort"]).agg(
        n=("AGEP","count"), p_siv=("p_siv","first"), p_refugee=("p_refugee","first"),
        p_tps=("p_tps","first"), p_asylum=("p_asylum","first"),
    ).reset_index()
    print(f"\nDistinct Afghan cells: {len(cell_summary)}")
    print(f"\np_siv variation: mean={df['p_siv'].mean():.3f}, std={df['p_siv'].std():.3f}, max={df['p_siv'].max():.3f}")
    print(f"p_refugee variation: mean={df['p_refugee'].mean():.3f}, std={df['p_refugee'].std():.3f}, max={df['p_refugee'].max():.3f}")
    print(f"Correlation(p_siv, p_refugee) at individual level: {df[['p_siv','p_refugee']].corr().iloc[0,1]:.3f}")

    print("\nCells where p_siv > p_refugee (SIV-dominant):")
    siv_dom = cell_summary[cell_summary["p_siv"] > cell_summary["p_refugee"]]
    print(f"  {len(siv_dom)} cells, total n={siv_dom['n'].sum()}")
    print("Cells where p_refugee > p_siv (Refugee-dominant):")
    ref_dom = cell_summary[cell_summary["p_refugee"] > cell_summary["p_siv"]]
    print(f"  {len(ref_dom)} cells, total n={ref_dom['n'].sum()}")

    outcomes = {
        "in_lf":"work_auth","employed":"work_auth","formal_emp":"work_auth",
        "log_wagp":"work_auth","snap":"work_auth","medicaid":"work_auth",
        "eng_well":"human_cap","edu_years":"human_cap",
    }

    print("\n=== AFGHAN SIV vs REFUGEE: coefficient & ΔR² test ===")
    results = []
    for y, otype in outcomes.items():
        sub = df[[y,"p_siv","p_refugee","p_tps","p_asylum","state","cohort","age_c"]].dropna()
        if len(sub) < 300: continue
        # Full: SIV + Refugee + other tracks + FE
        full_fit = smf.ols(f"{y} ~ p_siv + p_refugee + p_tps + p_asylum + age_c + C(state) + C(cohort)", data=sub).fit()
        r2_full = full_fit.rsquared
        # Drop track block
        r2_no_tracks = smf.ols(f"{y} ~ age_c + C(state) + C(cohort)", data=sub).fit().rsquared
        dR2_track = max(0.0, r2_full - r2_no_tracks)

        # Drop SIV only
        r2_no_siv = smf.ols(f"{y} ~ p_refugee + p_tps + p_asylum + age_c + C(state) + C(cohort)", data=sub).fit().rsquared
        dR2_siv = max(0.0, r2_full - r2_no_siv)

        # Drop Refugee only
        r2_no_ref = smf.ols(f"{y} ~ p_siv + p_tps + p_asylum + age_c + C(state) + C(cohort)", data=sub).fit().rsquared
        dR2_ref = max(0.0, r2_full - r2_no_ref)

        # Coefficients (semi-elasticities)
        beta_siv = full_fit.params.get("p_siv", np.nan)
        beta_ref = full_fit.params.get("p_refugee", np.nan)
        se_siv = full_fit.bse.get("p_siv", np.nan)
        se_ref = full_fit.bse.get("p_refugee", np.nan)
        t_siv = beta_siv / se_siv if se_siv > 0 else np.nan
        t_ref = beta_ref / se_ref if se_ref > 0 else np.nan

        results.append({
            "outcome": y, "out_type": otype, "n": len(sub),
            "r2_full": r2_full,
            "dR2_track_block": dR2_track,
            "dR2_siv": dR2_siv,
            "dR2_refugee": dR2_ref,
            "beta_siv": beta_siv, "t_siv": t_siv,
            "beta_refugee": beta_ref, "t_refugee": t_ref,
        })
        print(f"  {y:>12s}: r2={r2_full:.4f}  dR2_track={dR2_track:.4f}  dR2_siv={dR2_siv:.4f}  dR2_ref={dR2_ref:.4f}  beta_siv={beta_siv:.4f}(t={t_siv:.2f})  beta_ref={beta_ref:.4f}(t={t_ref:.2f})")

    res = pd.DataFrame(results)
    res.to_csv(OUT_DIR / "v7_afghan_siv_vs_refugee.csv", index=False)

    # Headline tests
    print("\n" + "="*60)
    print("AFGHAN SIV vs REFUGEE — interpretation")
    print("="*60)
    work = res[res["out_type"]=="work_auth"]
    # If routing matters: at least ONE work-auth outcome should show significant track effect
    sig_siv = ((work["t_siv"].abs() >= 1.96) & (work["dR2_siv"] >= 0.005)).sum()
    sig_ref = ((work["t_refugee"].abs() >= 1.96) & (work["dR2_refugee"] >= 0.005)).sum()
    print(f"  Significant SIV effect (|t|>=1.96 + dR2>=0.005): {sig_siv}/{len(work)} work-auth outcomes")
    print(f"  Significant Refugee effect: {sig_ref}/{len(work)} work-auth outcomes")
    # SIV-vs-Refugee direct sign comparison
    work_diff = work[work["beta_siv"].abs() > work["beta_refugee"].abs()]
    print(f"  SIV |effect| > Refugee |effect|: {len(work_diff)}/{len(work)} work-auth outcomes")


if __name__ == "__main__":
    main()
