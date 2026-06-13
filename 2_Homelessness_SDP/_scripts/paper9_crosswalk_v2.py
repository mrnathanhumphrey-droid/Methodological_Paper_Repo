"""
Paper 9 Phase 1 - v2 Cross-walk: 4-track (Refugee + TPS + Undocumented + Residual).

Adds MPI 2023 state x origin unauthorized-immigrant estimates as the 4th track,
splitting the v1 "Residual" into "Undocumented" and "Residual" (= LPR / Asylum
/ SIV / Parole / other status mixed). MPI uses 2019-23 ACS + SIPP imputation
weighted to mid-2023 control totals.

For the 5 P9 origins with MPI state-level data (El Salvador, Guatemala, Honduras,
Venezuela, Cuba), Undocumented is a direct state x origin count. For the 10
origins below MPI per-state top-5 thresholds (Ukraine, Haiti, Afghanistan,
Syria, Iraq, Myanmar, DRC, Eritrea, Somalia, Sudan), Undocumented = 0 in the
v2 cross-walk (consistent with MPI's per-state reporting threshold).

Output: D:/IDP/data/paper9/crosswalk/crosswalk_v2_state_origin_cohort_4track.csv
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ACS = Path("D:/IDP/data/paper9/acs/acs5_2024_pums_origins.csv")
WRAPS = Path("D:/IDP/data/paper9/orr_wraps/wraps_arrivals_by_state_nationality_FY_long.csv")
TPS = Path("D:/IDP/data/paper9/tps/tps_designations_2026_05_30.csv")
MPI = Path("D:/IDP/data/paper9/mpi/mpi_2023_unauthorized_state_origin_top5.csv")
OUT_DIR = Path("D:/IDP/data/paper9/crosswalk")
OUT_DIR.mkdir(parents=True, exist_ok=True)

P9_ORIGINS = [
    "Ukraine","Venezuela","Cuba","Honduras","El Salvador","Guatemala","Haiti",
    "Afghanistan","Syria","Iraq","Myanmar","DRC","Eritrea","Somalia","Sudan",
]

COHORTS = [
    ("pre-2018", 1989, 2017, None),
    ("2018-2019", 2018, 2019, ["FY2018","FY2019"]),
    ("2020-2021", 2020, 2021, ["FY2020","FY2021"]),
    ("2022-2023", 2022, 2023, ["FY2022","FY2023"]),
    ("2024",      2024, 2024, ["FY2024"]),
]

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

TPS_ORIGIN_MAP = {
    "Ukraine":       ["Ukraine"],
    "Venezuela":     ["Venezuela_2021","Venezuela_2023"],
    "Honduras":      ["Honduras"],
    "El Salvador":   ["El Salvador"],
    "Haiti":         ["Haiti"],
    "Afghanistan":   ["Afghanistan"],
    "Syria":         ["Syria"],
    "Myanmar":       ["Burma"],
    "Somalia":       ["Somalia"],
    "Sudan":         ["Sudan"],
}


def load_acs() -> pd.DataFrame:
    df = pd.read_csv(ACS)
    df["state_name"] = df["state_fips"].astype(str).str.zfill(2).map(FIPS_TO_STATE)
    bins = [1988, 2017, 2019, 2021, 2023, 2025]
    labels = ["pre-2018","2018-2019","2020-2021","2022-2023","2024"]
    df["cohort"] = pd.cut(df["YOEP"], bins=bins, labels=labels, include_lowest=True)
    return df


def tps_pop_for_origin(tps: pd.DataFrame, origin: str) -> int:
    if origin not in TPS_ORIGIN_MAP: return 0
    total = 0
    for m in TPS_ORIGIN_MAP[origin]:
        rows = tps[tps["country"] == m]
        if len(rows): total += int(rows.iloc[0]["tps_holders_mar2025"])
    return total


def tps_eligible_cohorts_for_origin(tps: pd.DataFrame, origin: str) -> set[str]:
    if origin not in TPS_ORIGIN_MAP: return set()
    cutoffs = []
    for m in TPS_ORIGIN_MAP[origin]:
        rows = tps[tps["country"] == m]
        if not len(rows): continue
        init = pd.to_datetime(rows.iloc[0]["initial_designation"])
        latest_raw = rows.iloc[0].get("latest_designation", "")
        latest_dt = pd.to_datetime(latest_raw) if (pd.notna(latest_raw) and str(latest_raw).strip()) else init
        cutoffs.append(max(init.year, latest_dt.year))
    if not cutoffs: return set()
    max_cutoff = max(cutoffs)
    return {label for label, lo, hi, _ in COHORTS if lo <= max_cutoff}


def refugee_count_for_cell(wraps: pd.DataFrame, state: str, origin: str, fys) -> int:
    if fys is None: return 0
    sub = wraps[(wraps["state"]==state) & (wraps["nationality"]==origin) & (wraps["fy"].isin(fys))]
    return int(sub["arrivals"].sum())


def main():
    print("Loading inputs...")
    acs = load_acs()
    wraps = pd.read_csv(WRAPS)
    tps = pd.read_csv(TPS)
    mpi = pd.read_csv(MPI)

    cells = acs.groupby(["state_name","origin","cohort"], observed=False)["PWGTP"].sum().reset_index()
    cells.columns = ["state","origin","cohort","acs_pop_weighted"]
    cells = cells[cells["acs_pop_weighted"] > 0]
    print(f"Cells: {len(cells)}")

    # MPI undocumented: state x origin table. Allocate to cohorts proportional to
    # ACS-foreign-born of origin in each cohort within the state. MPI estimates
    # are 2023 stock; cohort split via ACS YOEP distribution.
    mpi_state_origin = mpi[mpi["origin"].isin(P9_ORIGINS)][["state","origin","mpi_undoc_est"]].copy()
    mpi_state_origin.columns = ["state","origin","mpi_undoc_total"]
    print(f"MPI state-origin rows: {len(mpi_state_origin)}")
    print(f"MPI P9-origins covered: {sorted(mpi_state_origin['origin'].unique())}")

    # ACS state x origin totals (for MPI proportional cohort split)
    state_origin_acs = acs.groupby(["state_name","origin"], observed=False)["PWGTP"].sum().reset_index()
    state_origin_acs.columns = ["state","origin","origin_state_total"]

    # TPS pre-compute
    eligible_by_origin = {o: tps_eligible_cohorts_for_origin(tps, o) for o in P9_ORIGINS}
    tps_pop_by_origin = {o: tps_pop_for_origin(tps, o) for o in P9_ORIGINS}
    eligible_total_by_origin = {}
    for o in P9_ORIGINS:
        if not eligible_by_origin[o]:
            eligible_total_by_origin[o] = 0; continue
        sub = cells[(cells["origin"]==o) & (cells["cohort"].isin(eligible_by_origin[o]))]
        eligible_total_by_origin[o] = int(sub["acs_pop_weighted"].sum())

    # Build cross-walk
    rows = []
    for _, c in cells.iterrows():
        st = c["state"]; orig = c["origin"]; coh = c["cohort"]
        if pd.isna(coh): continue
        coh = str(coh)
        acs_pop = float(c["acs_pop_weighted"])

        # 1) Refugee
        fys = next((cfg[3] for cfg in COHORTS if cfg[0]==coh), None)
        refugee_n = refugee_count_for_cell(wraps, st, orig, fys)

        # 2) TPS (proportional)
        tps_n = 0.0
        if coh in eligible_by_origin.get(orig, set()):
            denom = eligible_total_by_origin.get(orig, 0)
            if denom > 0:
                tps_n = tps_pop_by_origin[orig] * (acs_pop / denom)

        # 3) Undocumented (MPI state x origin; cohort split proportional to ACS YOEP)
        undoc_n = 0.0
        mpi_match = mpi_state_origin[(mpi_state_origin["state"]==st) &
                                      (mpi_state_origin["origin"]==orig)]
        if len(mpi_match):
            state_origin_total_acs = state_origin_acs[
                (state_origin_acs["state"]==st) & (state_origin_acs["origin"]==orig)
            ]["origin_state_total"].iloc[0] if len(state_origin_acs[
                (state_origin_acs["state"]==st) & (state_origin_acs["origin"]==orig)
            ]) else 0
            if state_origin_total_acs > 0:
                cohort_share_of_state_origin = acs_pop / state_origin_total_acs
                undoc_n = float(mpi_match.iloc[0]["mpi_undoc_total"]) * cohort_share_of_state_origin

        # 4) Residual + normalization
        # If admin tracks (refugee + tps + undoc) exceed ACS-counted population for
        # this cell, scale them down proportionally so the sum = acs_pop (i.e., the
        # admin estimates can exceed ACS due to undercount adjustment in MPI's
        # control totals + Van Hook scaling; here we absorb that into a clean
        # probability vector summing to 1.0).
        admin_total = refugee_n + tps_n + undoc_n
        if admin_total > acs_pop and acs_pop > 0:
            scale = acs_pop / admin_total
            refugee_n_norm = refugee_n * scale
            tps_n_norm     = tps_n * scale
            undoc_n_norm   = undoc_n * scale
            residual = 0.0
        else:
            refugee_n_norm = refugee_n
            tps_n_norm     = tps_n
            undoc_n_norm   = undoc_n
            residual = max(0.0, acs_pop - admin_total)
        total = refugee_n_norm + tps_n_norm + undoc_n_norm + residual
        if total > 0:
            p_ref = refugee_n_norm / total
            p_tps = tps_n_norm / total
            p_undoc = undoc_n_norm / total
            p_res = residual / total
        else:
            p_ref = p_tps = p_undoc = p_res = 0.0

        rows.append({
            "state": st, "origin": orig, "cohort": coh,
            "acs_pop_weighted": acs_pop,
            "refugee_n":  refugee_n_norm,
            "tps_n":      tps_n_norm,
            "undoc_n":    undoc_n_norm,
            "residual_n": residual,
            "p_refugee": p_ref,
            "p_tps": p_tps,
            "p_undoc": p_undoc,
            "p_residual": p_res,
        })

    cw = pd.DataFrame(rows)
    out = OUT_DIR / "crosswalk_v2_state_origin_cohort_4track.csv"
    cw.to_csv(out, index=False)
    print(f"\nSaved {len(cw):,} cells -> {out}")

    # Summary by origin
    print("\n=== v2 TRACK SHARES BY ORIGIN (P-weighted by acs_pop) ===")
    summ = (cw.groupby("origin")
              .apply(lambda d: pd.Series({
                  "acs_total":   d["acs_pop_weighted"].sum(),
                  "refugee_n":   d["refugee_n"].sum(),
                  "tps_n":       d["tps_n"].sum(),
                  "undoc_n":     d["undoc_n"].sum(),
                  "residual_n":  d["residual_n"].sum(),
              }), include_groups=False)
              .reset_index())
    for col in ["refugee","tps","undoc","residual"]:
        summ[f"p_{col[:3]}"] = summ[f"{col}_n"] / summ["acs_total"]
    summ = summ.sort_values("acs_total", ascending=False)
    print(summ.to_string(index=False, float_format=lambda x: f"{x:.3f}" if isinstance(x,float) else str(x)))


if __name__ == "__main__":
    main()
