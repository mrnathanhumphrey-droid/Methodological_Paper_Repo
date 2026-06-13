"""
Paper 9 Phase 1 - v3 7-track cross-walk (the full PRE_REG_042 spec).

Adds 3 new tracks to v2 4-track:
 - Asylum-granted: EOIR FY2024 grants by nationality, scaled 7x to approximate
   cumulative grants 2018-2024 stock; allocated to states proportional to
   ACS-foreign-born-of-origin per state.
 - SIV (Afghan + Iraqi): cumulative SIV numbers used (DOS quarterly reports);
   allocated to states proportional to ACS-foreign-born-of-origin per state.
 - Parole-with-EAD (UFU + CHNV): national cumulative arrivals; allocated to
   states proportional to ACS-foreign-born-of-origin in the eligible cohort
   ranges (UFU: 2022-23 + 2024; CHNV: 2022-23 + 2024).

Final 7 tracks: {Refugee, TPS, Asylum-granted, SIV, Parole, Undocumented, Residual}

Output: D:/IDP/data/paper9/crosswalk/crosswalk_v3_state_origin_cohort_7track.csv
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
EOIR = Path("D:/IDP/data/paper9/eoir/eoir_fy2024_asylum_by_nationality.csv")
SIV = Path("D:/IDP/data/paper9/siv/siv_cumulative_2026_05_30.csv")
PAROLE = Path("D:/IDP/data/paper9/chnv/parole_cumulative_2026_05_30.csv")
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

PAROLE_ELIGIBLE_COHORTS = {"2022-2023", "2024"}  # UFU + CHNV both launched 2022 or 2023

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
    "Ukraine":["Ukraine"], "Venezuela":["Venezuela_2021","Venezuela_2023"],
    "Honduras":["Honduras"], "El Salvador":["El Salvador"], "Haiti":["Haiti"],
    "Afghanistan":["Afghanistan"], "Syria":["Syria"], "Myanmar":["Burma"],
    "Somalia":["Somalia"], "Sudan":["Sudan"],
}


def load_acs() -> pd.DataFrame:
    df = pd.read_csv(ACS)
    df["state_name"] = df["state_fips"].astype(str).str.zfill(2).map(FIPS_TO_STATE)
    bins = [1988, 2017, 2019, 2021, 2023, 2025]
    labels = ["pre-2018","2018-2019","2020-2021","2022-2023","2024"]
    df["cohort"] = pd.cut(df["YOEP"], bins=bins, labels=labels, include_lowest=True)
    return df


def tps_pop_for_origin(tps_df, origin):
    if origin not in TPS_ORIGIN_MAP: return 0
    total = 0
    for m in TPS_ORIGIN_MAP[origin]:
        r = tps_df[tps_df["country"] == m]
        if len(r): total += int(r.iloc[0]["tps_holders_mar2025"])
    return total


def tps_eligible_cohorts(tps_df, origin):
    if origin not in TPS_ORIGIN_MAP: return set()
    cutoffs = []
    for m in TPS_ORIGIN_MAP[origin]:
        r = tps_df[tps_df["country"] == m]
        if not len(r): continue
        init = pd.to_datetime(r.iloc[0]["initial_designation"])
        raw = r.iloc[0].get("latest_designation","")
        latest = pd.to_datetime(raw) if (pd.notna(raw) and str(raw).strip()) else init
        cutoffs.append(max(init.year, latest.year))
    if not cutoffs: return set()
    mx = max(cutoffs)
    return {lbl for lbl, lo, hi, _ in COHORTS if lo <= mx}


def main():
    print("Loading inputs...")
    acs = load_acs()
    wraps = pd.read_csv(WRAPS)
    tps   = pd.read_csv(TPS)
    mpi   = pd.read_csv(MPI)
    eoir  = pd.read_csv(EOIR)
    siv   = pd.read_csv(SIV)
    parole= pd.read_csv(PAROLE)

    cells = acs.groupby(["state_name","origin","cohort"], observed=False)["PWGTP"].sum().reset_index()
    cells.columns = ["state","origin","cohort","acs_pop_weighted"]
    cells = cells[cells["acs_pop_weighted"] > 0]
    print(f"Cells: {len(cells)}")

    # Pre-aggregates
    state_origin_pop = acs.groupby(["state_name","origin"], observed=False)["PWGTP"].sum().reset_index()
    state_origin_pop.columns = ["state","origin","origin_state_pop"]

    # ACS state-origin pop restricted to PAROLE-eligible cohorts
    parole_eligible_cells = cells[cells["cohort"].astype(str).isin(PAROLE_ELIGIBLE_COHORTS)]
    state_origin_pop_parole = parole_eligible_cells.groupby(["state","origin"])["acs_pop_weighted"].sum().reset_index()
    state_origin_pop_parole.columns = ["state","origin","origin_state_pop_parole_eligible"]

    # MPI undocumented: state × origin
    mpi_so = mpi[mpi["origin"].isin(P9_ORIGINS)][["state","origin","mpi_undoc_est"]].rename(
        columns={"mpi_undoc_est":"mpi_undoc_total"})

    # EOIR asylum: scale FY2024 grants by 7 to approximate cumulative 2018-2024
    eoir["asylum_granted_stock"] = eoir["grants"] * 7
    eoir_stock = dict(zip(eoir["origin"], eoir["asylum_granted_stock"]))

    # SIV: cumulative national stock
    siv_stock = dict(zip(siv["origin"], siv["siv_holders_cumulative"]))

    # Parole: cumulative national stock by origin
    parole_stock = dict(zip(parole["origin"], parole["parolees_cumulative"]))

    # National stocks for proportional allocations
    nat_pop = state_origin_pop.groupby("origin")["origin_state_pop"].sum().to_dict()
    nat_pop_parole = state_origin_pop_parole.groupby("origin")["origin_state_pop_parole_eligible"].sum().to_dict()

    # TPS precomputes
    elig_cohorts = {o: tps_eligible_cohorts(tps, o) for o in P9_ORIGINS}
    tps_pop = {o: tps_pop_for_origin(tps, o) for o in P9_ORIGINS}
    elig_total = {}
    for o in P9_ORIGINS:
        if not elig_cohorts[o]:
            elig_total[o] = 0; continue
        s = cells[(cells["origin"]==o) & (cells["cohort"].astype(str).isin(elig_cohorts[o]))]
        elig_total[o] = int(s["acs_pop_weighted"].sum())

    rows = []
    for _, c in cells.iterrows():
        st = c["state"]; orig = c["origin"]; coh = str(c["cohort"])
        if coh == "nan": continue
        acs_pop = float(c["acs_pop_weighted"])

        # 1) Refugee
        fys = next((cfg[3] for cfg in COHORTS if cfg[0]==coh), None)
        refugee_n = 0
        if fys is not None:
            r = wraps[(wraps["state"]==st) & (wraps["nationality"]==orig) & (wraps["fy"].isin(fys))]
            refugee_n = int(r["arrivals"].sum())

        # 2) TPS (proportional, cohort-eligible)
        tps_n = 0.0
        if coh in elig_cohorts.get(orig, set()) and elig_total.get(orig, 0) > 0:
            tps_n = tps_pop[orig] * (acs_pop / elig_total[orig])

        # 3) Asylum-granted (EOIR scaled, allocated by state-origin pop share)
        asy_n = 0.0
        nat = nat_pop.get(orig, 0)
        if nat > 0:
            origin_state_share = state_origin_pop[
                (state_origin_pop["state"]==st) & (state_origin_pop["origin"]==orig)
            ]["origin_state_pop"].iloc[0] if len(state_origin_pop[
                (state_origin_pop["state"]==st) & (state_origin_pop["origin"]==orig)
            ]) else 0
            if origin_state_share > 0:
                asy_n = eoir_stock.get(orig, 0) * (acs_pop / nat)

        # 4) SIV (Afghan + Iraqi only, state-proportional)
        siv_n = 0.0
        if orig in siv_stock and nat > 0:
            siv_n = siv_stock[orig] * (acs_pop / nat)

        # 5) Parole-with-EAD (Ukraine UFU + Cuba/Haiti/Venezuela CHNV, cohort-restricted)
        parole_n = 0.0
        if orig in parole_stock and coh in PAROLE_ELIGIBLE_COHORTS:
            denom = nat_pop_parole.get(orig, 0)
            if denom > 0:
                parole_n = parole_stock[orig] * (acs_pop / denom)

        # 6) Undocumented (MPI state x origin, cohort-proportional)
        undoc_n = 0.0
        m = mpi_so[(mpi_so["state"]==st) & (mpi_so["origin"]==orig)]
        if len(m):
            so_total = state_origin_pop[(state_origin_pop["state"]==st) &
                                         (state_origin_pop["origin"]==orig)]["origin_state_pop"].iloc[0] \
                if len(state_origin_pop[(state_origin_pop["state"]==st) &
                                         (state_origin_pop["origin"]==orig)]) else 0
            if so_total > 0:
                undoc_n = float(m.iloc[0]["mpi_undoc_total"]) * (acs_pop / so_total)

        # 7) Residual + normalization
        admin_total = refugee_n + tps_n + asy_n + siv_n + parole_n + undoc_n
        if admin_total > acs_pop and acs_pop > 0:
            scale = acs_pop / admin_total
            refugee_n_n = refugee_n * scale
            tps_n_n     = tps_n * scale
            asy_n_n     = asy_n * scale
            siv_n_n     = siv_n * scale
            parole_n_n  = parole_n * scale
            undoc_n_n   = undoc_n * scale
            residual    = 0.0
        else:
            refugee_n_n, tps_n_n, asy_n_n, siv_n_n, parole_n_n, undoc_n_n = \
                refugee_n, tps_n, asy_n, siv_n, parole_n, undoc_n
            residual = max(0.0, acs_pop - admin_total)
        total = refugee_n_n + tps_n_n + asy_n_n + siv_n_n + parole_n_n + undoc_n_n + residual
        if total > 0:
            p = lambda x: x / total
            p_ref, p_tps, p_asy, p_siv, p_par, p_und, p_res = (
                p(refugee_n_n), p(tps_n_n), p(asy_n_n), p(siv_n_n),
                p(parole_n_n), p(undoc_n_n), p(residual)
            )
        else:
            p_ref = p_tps = p_asy = p_siv = p_par = p_und = p_res = 0.0

        rows.append({
            "state": st, "origin": orig, "cohort": coh, "acs_pop_weighted": acs_pop,
            "refugee_n":  refugee_n_n,
            "tps_n":      tps_n_n,
            "asylum_n":   asy_n_n,
            "siv_n":      siv_n_n,
            "parole_n":   parole_n_n,
            "undoc_n":    undoc_n_n,
            "residual_n": residual,
            "p_refugee": p_ref, "p_tps": p_tps, "p_asylum": p_asy,
            "p_siv": p_siv, "p_parole": p_par, "p_undoc": p_und, "p_residual": p_res,
        })

    cw = pd.DataFrame(rows)
    out = OUT_DIR / "crosswalk_v3_state_origin_cohort_7track.csv"
    cw.to_csv(out, index=False)
    print(f"\nSaved {len(cw):,} cells -> {out}")

    print("\n=== v3 7-TRACK SHARES BY ORIGIN (P-weighted by acs_pop) ===")
    summ = (cw.groupby("origin")
              .apply(lambda d: pd.Series({
                  "acs_total":   d["acs_pop_weighted"].sum(),
                  "refugee":     d["refugee_n"].sum(),
                  "tps":         d["tps_n"].sum(),
                  "asylum":      d["asylum_n"].sum(),
                  "siv":         d["siv_n"].sum(),
                  "parole":      d["parole_n"].sum(),
                  "undoc":       d["undoc_n"].sum(),
                  "residual":    d["residual_n"].sum(),
              }), include_groups=False)
              .reset_index())
    for k in ["refugee","tps","asylum","siv","parole","undoc","residual"]:
        summ[f"p_{k[:3]}"] = summ[k] / summ["acs_total"]
    summ = summ.sort_values("acs_total", ascending=False)
    cols = ["origin","acs_total","p_ref","p_tps","p_asy","p_siv","p_par","p_und","p_res"]
    print(summ[cols].to_string(index=False, float_format=lambda x: f"{x:.3f}" if isinstance(x,float) else str(x)))


if __name__ == "__main__":
    main()
