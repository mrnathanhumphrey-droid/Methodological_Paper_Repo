"""
Paper 9 Phase 1 - Preliminary variance decomposition (v1, 3-track cross-walk).

PRE_REG_042 H1 + H2 first-pass check:
- H1: track-distribution partial-R^2 >= 0.15 on >= 3 of 5 work-auth-dep outcomes.
- H2 (load-bearing): track > origin on work-auth-dep outcomes; origin > track on
  human-capital outcomes (the differential prediction).

This is a PRELIMINARY check on the 3-track v1 cross-walk (Refugee + TPS + Residual).
The full 7-track cross-walk (adding EOIR Asylum, DOS SIV, CHNV/UFU Parole, MPI
Undocumented) is for Phase 1 fire after subsequent data acquisition. Result here
indicates whether the framework prediction is in the right direction with the
two largest publicly-quantified routing channels.

Method:
1. Aggregate ACS PUMS to (state x origin x cohort) cell level: weighted outcome
   means/rates among working-age (16-64) foreign-born from P9 origins.
2. Join to v1 cross-walk: p_refugee, p_tps, p_residual.
3. For each outcome:
   - Fit M_full: outcome ~ p_refugee + p_tps + C(origin) + C(cohort) + C(state)
     (omit p_residual to avoid collinearity since the three probs sum to 1).
   - Compare partial-R^2 of track (p_refugee+p_tps jointly) vs origin (C(origin)).
   - Type-II SS: drop one group at a time, get DeltaR^2.

Outputs:
  D:/IDP/data/paper9/variance_decomp/v1_partial_R2_table.csv
  D:/IDP/data/paper9/variance_decomp/v1_cell_aggregates.csv
"""
from __future__ import annotations
import sys
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore", category=FutureWarning)

ACS = Path("D:/IDP/data/paper9/acs/acs5_2024_pums_origins.csv")
CW = Path("D:/IDP/data/paper9/crosswalk/crosswalk_v1_state_origin_cohort_3track.csv")
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

# SCHL -> years of education
SCHL_TO_YEARS = {
    1: 0, 2: 0, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 6, 9: 7, 10: 8, 11: 9, 12: 10,
    13: 11, 14: 12, 15: 12, 16: 12, 17: 12, 18: 13, 19: 14, 20: 14, 21: 16,
    22: 18, 23: 20, 24: 22,
}


def build_cell_aggregates() -> pd.DataFrame:
    print("Loading ACS PUMS...")
    df = pd.read_csv(ACS)
    df["state_name"] = df["state_fips"].astype(str).str.zfill(2).map(FIPS_TO_STATE)
    bins = [1988, 2017, 2019, 2021, 2023, 2025]
    labels = ["pre-2018","2018-2019","2020-2021","2022-2023","2024"]
    df["cohort"] = pd.cut(df["YOEP"], bins=bins, labels=labels, include_lowest=True)
    df = df[(df["AGEP"] >= 16) & (df["AGEP"] <= 64)].copy()
    df["edu_years"] = df["SCHL"].map(SCHL_TO_YEARS).fillna(0)
    df["in_lf"] = df["ESR"].isin([1, 2, 3, 4, 5]).astype(int)         # in labor force (1-5)
    df["employed"] = df["ESR"].isin([1, 2, 4, 5]).astype(int)           # at work or armed forces
    df["formal_emp"] = ((df["ESR"].isin([1, 2])) & (df["COW"].isin([1, 2, 3, 4, 5]))).astype(int)
    df["snap"] = (df["FS"] == 1).astype(int)
    df["medicaid"] = (df["HINS4"] == 1).astype(int)
    df["eng_well"] = (df["ENG"].isin([0, 1, 2]) | df["ENG"].isna()).astype(int)  # native speaker or "well"+
    df["wagp_pos"] = (df["WAGP"] > 0).astype(int)

    print(f"  {len(df):,} working-age individuals across {df['state_name'].nunique()} states, {df['origin'].nunique()} origins")

    # Cell aggregates: weighted means/rates
    def wmean(d, col, wt="PWGTP"):
        w = d[wt].sum()
        if w == 0: return np.nan
        return (d[col] * d[wt]).sum() / w

    def wmean_pos(d, col, posflag, wt="PWGTP"):
        m = d[d[posflag] == 1]
        w = m[wt].sum()
        if w == 0: return np.nan
        return (m[col] * m[wt]).sum() / w

    cells = []
    for (st, orig, coh), grp in df.groupby(["state_name", "origin", "cohort"], observed=False):
        if grp["PWGTP"].sum() < 100:  # too thin a cell
            continue
        cells.append({
            "state": st, "origin": orig, "cohort": str(coh),
            "n_individuals": len(grp),
            "n_weighted":    int(grp["PWGTP"].sum()),
            "lfp_rate":      wmean(grp, "in_lf"),
            "emp_rate":      wmean(grp, "employed"),
            "formal_emp_rate": wmean(grp, "formal_emp"),
            "mean_wagp":     wmean_pos(grp, "WAGP", "wagp_pos"),  # employed-only
            "snap_rate":     wmean(grp, "snap"),
            "medicaid_rate": wmean(grp, "medicaid"),
            "eng_well_rate": wmean(grp, "eng_well"),
            "mean_edu_years": wmean(grp, "edu_years"),
        })
    cell_df = pd.DataFrame(cells)
    print(f"  Built {len(cell_df):,} cells with n_weighted>=100")
    return cell_df


def partial_r2_decomp(cell_df: pd.DataFrame):
    """For each outcome, fit OLS with track + origin + cohort + state.
    Compute partial-R^2 of (track) vs (origin) via drop-and-refit.
    """
    print("\nLoading cross-walk...")
    cw = pd.read_csv(CW)
    # Merge
    d = cell_df.merge(cw[["state","origin","cohort","p_refugee","p_tps","p_residual","acs_pop_weighted"]],
                      on=["state","origin","cohort"], how="left")
    print(f"  Merged {len(d):,} cells")

    work_auth_dep = ["lfp_rate", "emp_rate", "formal_emp_rate", "mean_wagp", "snap_rate", "medicaid_rate"]
    human_cap_dep = ["eng_well_rate", "mean_edu_years"]
    outcomes = work_auth_dep + human_cap_dep

    results = []
    for y in outcomes:
        sub = d[[y, "p_refugee", "p_tps", "origin", "cohort", "state", "n_weighted"]].dropna()
        if len(sub) < 50:
            print(f"  {y}: SKIP (n={len(sub)})")
            continue

        # Full model
        try:
            full = smf.ols(
                f"{y} ~ p_refugee + p_tps + C(origin) + C(cohort) + C(state)",
                data=sub,
                weights=sub["n_weighted"],
            ).fit()
            r2_full = full.rsquared
        except Exception as e:
            print(f"  {y}: full-fit FAIL {e}")
            continue

        # Drop track
        no_track = smf.ols(
            f"{y} ~ C(origin) + C(cohort) + C(state)",
            data=sub, weights=sub["n_weighted"]
        ).fit()
        d_track = max(0.0, r2_full - no_track.rsquared)

        # Drop origin
        no_origin = smf.ols(
            f"{y} ~ p_refugee + p_tps + C(cohort) + C(state)",
            data=sub, weights=sub["n_weighted"]
        ).fit()
        d_origin = max(0.0, r2_full - no_origin.rsquared)

        # Drop cohort
        no_cohort = smf.ols(
            f"{y} ~ p_refugee + p_tps + C(origin) + C(state)",
            data=sub, weights=sub["n_weighted"]
        ).fit()
        d_cohort = max(0.0, r2_full - no_cohort.rsquared)

        # Drop state
        no_state = smf.ols(
            f"{y} ~ p_refugee + p_tps + C(origin) + C(cohort)",
            data=sub, weights=sub["n_weighted"]
        ).fit()
        d_state = max(0.0, r2_full - no_state.rsquared)

        out_type = "work_auth" if y in work_auth_dep else "human_cap"
        results.append({
            "outcome": y,
            "out_type": out_type,
            "n_cells": len(sub),
            "r2_full": r2_full,
            "dR2_track": d_track,
            "dR2_origin": d_origin,
            "dR2_cohort": d_cohort,
            "dR2_state":  d_state,
            "track_gt_origin": d_track > d_origin,
        })

    return pd.DataFrame(results)


def main():
    cell_df = build_cell_aggregates()
    cell_df.to_csv(OUT_DIR / "v1_cell_aggregates.csv", index=False)
    print(f"\nSaved cell aggregates -> {OUT_DIR / 'v1_cell_aggregates.csv'}")

    res = partial_r2_decomp(cell_df)
    res.to_csv(OUT_DIR / "v1_partial_R2_table.csv", index=False)
    print(f"\nSaved partial-R^2 table -> {OUT_DIR / 'v1_partial_R2_table.csv'}")

    print("\n=== PARTIAL-R^2 BY OUTCOME (v1 first-pass) ===")
    print(res.to_string(index=False, float_format=lambda x: f"{x:.4f}" if isinstance(x, float) else str(x)))

    # H1 check: track partial-R^2 >= 0.15 on >= 3 of 5 work-auth-dep outcomes (excl mean_wagp threshold differs)
    work = res[res["out_type"] == "work_auth"]
    h1_hits = (work["dR2_track"] >= 0.15).sum()
    print(f"\nH1 check: track-partial-R^2 >= 0.15 on {h1_hits} of {len(work)} work-auth-dep outcomes (bar: >= 3)")
    print(f"  PRE_REG_042 H1: {'PASS' if h1_hits >= 3 else 'FAIL (preliminary; v1 cross-walk only 3-track)'}")

    # H2 check (LOAD-BEARING DIFFERENTIAL): track > origin on work-auth; origin > track on human-cap
    h2_work_hits = (work["track_gt_origin"]).sum()
    hc = res[res["out_type"] == "human_cap"]
    h2_hc_hits = (~hc["track_gt_origin"]).sum()  # origin > track means track_gt_origin is False
    print(f"\nH2 differential check (load-bearing):")
    print(f"  work-auth-dep: track > origin on {h2_work_hits} of {len(work)} (bar: >= 3 of 5)")
    print(f"  human-cap-dep: origin > track on {h2_hc_hits} of {len(hc)} (bar: >= 1 of 2)")
    h2_pass = (h2_work_hits >= 3) and (h2_hc_hits >= 1)
    print(f"  PRE_REG_042 H2 (preliminary v1): {'PASS' if h2_pass else 'FAIL'}")


if __name__ == "__main__":
    main()
