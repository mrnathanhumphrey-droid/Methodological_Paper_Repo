"""
Paper 9 Phase 1 - v7 WITHIN-ORIGIN variance decomposition.

PURPOSE: The F3 fire on the population-level test (v6) could reflect (a) genuine
F3 (origin dominates because it's the true mechanism) OR (b) origin-track
collinearity-by-design absorbing track signal into origin FE. To distinguish:
subset to ONE ORIGIN at a time, drop origin FE (vacuous when subset is single
origin), and ask whether track shares explain outcomes.

Within-origin test: for each origin with sufficient n + within-origin track
variation, run
    outcome_i ~ p_refugee + p_tps + p_asylum + p_siv + p_parole + p_undoc
                + age + C(state) + C(cohort)
on the individuals of that origin alone. Compute track partial-R^2 (drop track
block, compare R^2).

If track dR^2 lifts substantially when origin variation is removed (i.e., within
some single origin like Ukrainians or Afghans, track shares explain real
variation in LFP/wages/SNAP), then F3 is the population-level collinearity,
not the underlying mechanism failing. If track dR^2 stays small even within-origin
(e.g., within-Ukraine still 0.01), the F3 fire generalizes one level deeper.
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

# Track variables — pick subset of 6 with the most cross-cell variation within each origin
ALL_TRACKS = ["p_refugee","p_tps","p_asylum","p_siv","p_parole","p_undoc"]


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


def main():
    df = load_individual()
    cw = pd.read_csv(CW)
    df = df.merge(cw[["state","origin","cohort"] + ALL_TRACKS],
                  on=["state","origin","cohort"], how="left").dropna(subset=["p_refugee"])
    print(f"Total N: {len(df):,}")

    # Pick origins with enough sample AND meaningful within-origin track variation.
    # Skip origins where ALL track shares are uniform across cells.
    origin_summary = []
    for o in df["origin"].unique():
        sub = df[df["origin"]==o]
        n = len(sub)
        # Within-origin variance of each track share (cell-aggregated, weighted)
        cell_vars = []
        for t in ALL_TRACKS:
            std = sub[t].std()
            cell_vars.append(std)
        origin_summary.append({
            "origin": o, "n": n,
            "std_max_track": max(cell_vars),
            "tracks_with_std>0.02": sum(1 for s in cell_vars if s > 0.02),
        })
    print("\nOrigin selection table:")
    osum = pd.DataFrame(origin_summary).sort_values("n", ascending=False)
    print(osum.to_string(index=False, float_format=lambda x: f"{x:.3f}" if isinstance(x,float) else str(x)))

    # Keep origins with n >= 1500 AND >= 1 track with std > 0.02
    keep = osum[(osum["n"] >= 1500) & (osum["tracks_with_std>0.02"] >= 1)]["origin"].tolist()
    print(f"\nOrigins selected for within-origin variance decomp: {keep}")

    outcomes = {
        "in_lf":"work_auth","employed":"work_auth","formal_emp":"work_auth",
        "log_wagp":"work_auth","snap":"work_auth","medicaid":"work_auth",
        "eng_well":"human_cap","edu_years":"human_cap",
    }

    all_results = []
    for orig in keep:
        sub = df[df["origin"]==orig].copy()
        n = len(sub)
        # Identify which tracks have nonzero variation in this origin's cells
        tracks_used = [t for t in ALL_TRACKS if sub[t].std() > 0.001]
        if len(tracks_used) < 2:
            print(f"\n{orig}: insufficient track variation ({tracks_used}), skip")
            continue
        track_formula = " + ".join(tracks_used)
        print(f"\n=== ORIGIN: {orig}  (n={n:,}, tracks={tracks_used}) ===")
        for y, otype in outcomes.items():
            s = sub[[y] + tracks_used + ["state","cohort","age_c"]].dropna()
            if len(s) < 300:
                continue
            r2_full = fit_R2(f"{y} ~ {track_formula} + age_c + C(state) + C(cohort)", s)
            r2_no_track = fit_R2(f"{y} ~ age_c + C(state) + C(cohort)", s)
            r2_no_state = fit_R2(f"{y} ~ {track_formula} + age_c + C(cohort)", s)
            r2_no_cohort = fit_R2(f"{y} ~ {track_formula} + age_c + C(state)", s)

            dR2_track = max(0.0, r2_full - r2_no_track)
            dR2_state = max(0.0, r2_full - r2_no_state)
            dR2_cohort = max(0.0, r2_full - r2_no_cohort)

            all_results.append({
                "origin": orig, "outcome": y, "out_type": otype, "n_indiv": len(s),
                "r2_full": r2_full,
                "dR2_track": dR2_track, "dR2_state": dR2_state, "dR2_cohort": dR2_cohort,
                "tracks_used": ",".join(tracks_used),
            })
            print(f"  {y:>12s}: r2={r2_full:.4f}  dR2_track={dR2_track:.4f}  dR2_state={dR2_state:.4f}  dR2_cohort={dR2_cohort:.4f}")

    res = pd.DataFrame(all_results)
    res.to_csv(OUT_DIR / "v7_within_origin_partial_R2.csv", index=False)

    # Cross-origin summary
    print("\n" + "="*70)
    print("WITHIN-ORIGIN H1 PROXY: track dR^2 >= 0.15 on work-auth outcomes")
    print("="*70)
    for orig in res["origin"].unique():
        sub = res[(res["origin"]==orig) & (res["out_type"]=="work_auth")]
        h1 = (sub["dR2_track"] >= 0.15).sum()
        max_track = sub["dR2_track"].max()
        print(f"  {orig:>14s}: {h1}/{len(sub)} (max track dR2 on work-auth = {max_track:.4f})")

    # Headline: any origin where track dR^2 > 0.10 on a work-auth outcome?
    print("\n>>> Any origin × work-auth outcome with track dR^2 > 0.10?")
    big = res[(res["out_type"]=="work_auth") & (res["dR2_track"] > 0.10)]
    if len(big):
        print(big[["origin","outcome","dR2_track"]].to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    else:
        print("    NONE.")
    print("\n>>> Any origin × work-auth outcome with track dR^2 > 0.05?")
    mid = res[(res["out_type"]=="work_auth") & (res["dR2_track"] > 0.05)]
    if len(mid):
        print(mid[["origin","outcome","dR2_track"]].to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    else:
        print("    NONE.")


if __name__ == "__main__":
    main()
