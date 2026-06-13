"""
Paper 9 Phase 1 - v1 Cross-walk (Refugee + TPS + Residual, 3-track first-pass).

Per PRE_REG_042 §3: build (state x origin x entry-cohort) -> probability vector
over tracks. v1 uses only ORR/WRAPS (Refugee) + USCIS TPS + Residual.
Subsequent versions add EOIR Asylum, DOS SIV, CHNV/UFU Parole, MPI Undocumented.

Allocation rules (per PRE_REG_042 §3):
 1. Refugee track: WRAPS gives (state x origin x FY) directly -> use as count.
 2. TPS track: USCIS gives national x origin x period. Allocate to states
    proportionally to ACS foreign-born of that origin per state, but only for
    cohorts that arrived BEFORE the relevant TPS termination notice and on/after
    the country's initial TPS designation.
 3. Residual = ACS_pop_in_cell - Refugee_count - TPS_alloc (floored at 0).

Output: D:/IDP/data/paper9/crosswalk/crosswalk_v1_state_origin_cohort_3track.csv
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
OUT_DIR = Path("D:/IDP/data/paper9/crosswalk")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 15 P9 origins (ACS POBP codes already mapped during extract)
P9_ORIGINS = [
    "Ukraine","Venezuela","Cuba","Honduras","El Salvador","Guatemala","Haiti",
    "Afghanistan","Syria","Iraq","Myanmar","DRC","Eritrea","Somalia","Sudan",
]

# Cohort definitions: ACS YOEP (year of entry) bins
# pre-2018 = entered 1989-2017 (long-resident); 2018-2019, 2020-2021, 2022-2023, 2024
COHORTS = [
    ("pre-2018", 1989, 2017, None),                    # no WRAPS-FY match (treat pre-data)
    ("2018-2019", 2018, 2019, ["FY2018","FY2019"]),
    ("2020-2021", 2020, 2021, ["FY2020","FY2021"]),
    ("2022-2023", 2022, 2023, ["FY2022","FY2023"]),
    ("2024",      2024, 2024, ["FY2024"]),             # FY2024 GAP (parser cid-encoded)
]

# State FIPS -> state name (50 + DC)
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

# TPS-designated origins (subset of P9 with TPS):
# El Salvador, Honduras, Haiti, Afghanistan, Syria, Myanmar (Burma), Somalia, Sudan,
# Ukraine, Venezuela. NOT TPS-designated in P9: Cuba, Guatemala, Iraq, DRC, Eritrea.
TPS_ORIGIN_MAP = {
    "Ukraine":       ["Ukraine"],
    "Venezuela":     ["Venezuela_2021", "Venezuela_2023"],
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
    # Cohort bins consistent with COHORTS
    bins = [1988, 2017, 2019, 2021, 2023, 2025]
    labels = ["pre-2018","2018-2019","2020-2021","2022-2023","2024"]
    df["cohort"] = pd.cut(df["YOEP"], bins=bins, labels=labels, include_lowest=True)
    # working-age
    df["working_age"] = ((df["AGEP"] >= 16) & (df["AGEP"] <= 64)).astype(int)
    return df


def acs_pop_by_cell(acs: pd.DataFrame) -> pd.DataFrame:
    """ACS weighted population per (state, origin, cohort) cell."""
    g = acs.groupby(["state_name","origin","cohort"], observed=False)["PWGTP"].sum().reset_index()
    g.columns = ["state","origin","cohort","acs_pop_weighted"]
    return g[g["acs_pop_weighted"] > 0]


def load_wraps() -> pd.DataFrame:
    return pd.read_csv(WRAPS)


def refugee_count_for_cell(wraps: pd.DataFrame, state: str, origin: str, fys: list[str] | None) -> int:
    if fys is None:
        return 0  # pre-2018 cohort has no WRAPS coverage
    sub = wraps[(wraps["state"] == state) &
                (wraps["nationality"] == origin) &
                (wraps["fy"].isin(fys))]
    return int(sub["arrivals"].sum())


def load_tps() -> pd.DataFrame:
    return pd.read_csv(TPS)


def tps_pop_for_origin(tps: pd.DataFrame, origin: str) -> int:
    """National TPS holders for this origin (sum across designations like Venezuela 2021+2023)."""
    if origin not in TPS_ORIGIN_MAP:
        return 0
    matches = TPS_ORIGIN_MAP[origin]
    total = 0
    for m in matches:
        rows = tps[tps["country"] == m]
        if len(rows):
            total += int(rows.iloc[0]["tps_holders_mar2025"])
    return total


def tps_eligible_cohorts_for_origin(tps: pd.DataFrame, origin: str) -> set[str]:
    """Cohorts whose entry-year range overlaps with TPS continuous-residence eligibility.

    A cohort is "potentially eligible" if its START year is at-or-before the latest
    TPS continuous-residence cutoff (proxy: year of latest re-designation, since
    re-designations reset the CRR window to a recent date).

    For old TPS designations (e.g., Honduras 1999) only the pre-2018 cohort meets
    the original CRR (Dec 1998). For recent re-designations (e.g., Haiti 2024),
    cohorts through 2022-2023 are partially eligible.

    Refines later via individual-level YOEP < CRR date in Phase 2.
    """
    if origin not in TPS_ORIGIN_MAP:
        return set()
    matches = TPS_ORIGIN_MAP[origin]
    cutoffs = []
    for m in matches:
        rows = tps[tps["country"] == m]
        if not len(rows): continue
        init = pd.to_datetime(rows.iloc[0]["initial_designation"])
        latest_raw = rows.iloc[0].get("latest_designation", "")
        if pd.notna(latest_raw) and str(latest_raw).strip():
            latest_dt = pd.to_datetime(latest_raw)
        else:
            latest_dt = init
        cutoffs.append(max(init.year, latest_dt.year))
    if not cutoffs:
        return set()
    max_cutoff = max(cutoffs)
    # Cohort eligible if its START year <= cutoff (any part of cohort qualifies)
    eligible = {label for label, lo, hi, _ in COHORTS if lo <= max_cutoff}
    return eligible


def main():
    print("Loading inputs...")
    acs = load_acs()
    wraps = load_wraps()
    tps = load_tps()

    # ACS pop per cell
    cells = acs_pop_by_cell(acs)
    print(f"Total cells (state x origin x cohort, non-zero): {len(cells)}")
    print(f"States: {cells['state'].nunique()}; origins: {cells['origin'].nunique()}; cohorts: {cells['cohort'].nunique()}")

    # State foreign-born pop for each origin (used for TPS proportional allocation)
    state_origin_pop = acs.groupby(["state_name","origin"], observed=False)["PWGTP"].sum().reset_index()
    state_origin_pop.columns = ["state","origin","origin_state_pop"]

    # National TPS allocation: distribute origin's TPS holders to states proportionally
    # to that origin's ACS foreign-born stock per state.
    # Restrict to TPS-eligible cohorts within each cell.

    # Pre-compute, per origin, the eligible cohort set
    eligible_by_origin = {o: tps_eligible_cohorts_for_origin(tps, o) for o in P9_ORIGINS}
    tps_pop_by_origin = {o: tps_pop_for_origin(tps, o) for o in P9_ORIGINS}

    print("\nTPS national populations by origin (P9):")
    for o in P9_ORIGINS:
        print(f"  {o}: {tps_pop_by_origin[o]:>7,} (eligible cohorts: {sorted(eligible_by_origin[o])})")

    # For each origin, total ACS pop in eligible cells (denominator for proportional alloc)
    eligible_total_by_origin = {}
    for o in P9_ORIGINS:
        elig = eligible_by_origin[o]
        if not elig:
            eligible_total_by_origin[o] = 0
            continue
        sub = cells[(cells["origin"] == o) & (cells["cohort"].isin(elig))]
        eligible_total_by_origin[o] = int(sub["acs_pop_weighted"].sum())

    # Build the crosswalk
    rows = []
    for _, c in cells.iterrows():
        st = c["state"]; orig = c["origin"]; coh = c["cohort"]
        if pd.isna(coh):
            continue
        coh = str(coh)
        acs_pop = float(c["acs_pop_weighted"])

        # FYs for this cohort
        fys = next((cfg[3] for cfg in COHORTS if cfg[0] == coh), None)
        refugee_n = refugee_count_for_cell(wraps, st, orig, fys)

        # TPS allocation: only if this origin x cohort is TPS-eligible
        tps_n = 0.0
        if coh in eligible_by_origin.get(orig, set()):
            denom = eligible_total_by_origin.get(orig, 0)
            if denom > 0:
                tps_n = tps_pop_by_origin[orig] * (acs_pop / denom)

        residual = max(0.0, acs_pop - refugee_n - tps_n)
        total_track = refugee_n + tps_n + residual

        if total_track > 0:
            p_ref = refugee_n / total_track
            p_tps = tps_n / total_track
            p_res = residual / total_track
        else:
            p_ref = p_tps = p_res = 0.0

        rows.append({
            "state": st, "origin": orig, "cohort": coh,
            "acs_pop_weighted": acs_pop,
            "refugee_n": refugee_n,
            "tps_n": tps_n,
            "residual_n": residual,
            "p_refugee": p_ref,
            "p_tps": p_tps,
            "p_residual": p_res,
        })

    cw = pd.DataFrame(rows)
    out = OUT_DIR / "crosswalk_v1_state_origin_cohort_3track.csv"
    cw.to_csv(out, index=False)
    print(f"\nSaved {len(cw):,} cells -> {out}")

    # SUMMARY: track shares by origin (weighted by ACS pop)
    print("\n=== TRACK SHARES BY ORIGIN (P-weighted by acs_pop) ===")
    summ = (cw.groupby("origin")
              .apply(lambda d: pd.Series({
                  "acs_total":   d["acs_pop_weighted"].sum(),
                  "refugee_n":   d["refugee_n"].sum(),
                  "tps_n":       d["tps_n"].sum(),
                  "residual_n":  d["residual_n"].sum(),
              }), include_groups=False)
              .reset_index())
    summ["p_ref"] = summ["refugee_n"] / summ["acs_total"]
    summ["p_tps"] = summ["tps_n"] / summ["acs_total"]
    summ["p_res"] = summ["residual_n"] / summ["acs_total"]
    summ = summ.sort_values("acs_total", ascending=False)
    print(summ.to_string(index=False))

    # SUMMARY: cohort-level
    print("\n=== TRACK SHARES BY COHORT (P9 origins, all states) ===")
    coh_summ = (cw.groupby("cohort", observed=False)
                  .apply(lambda d: pd.Series({
                      "acs_total":   d["acs_pop_weighted"].sum(),
                      "refugee_n":   d["refugee_n"].sum(),
                      "tps_n":       d["tps_n"].sum(),
                      "residual_n":  d["residual_n"].sum(),
                  }), include_groups=False)
                  .reset_index())
    coh_summ["p_ref"] = coh_summ["refugee_n"] / coh_summ["acs_total"]
    coh_summ["p_tps"] = coh_summ["tps_n"] / coh_summ["acs_total"]
    coh_summ["p_res"] = coh_summ["residual_n"] / coh_summ["acs_total"]
    print(coh_summ.to_string(index=False))


if __name__ == "__main__":
    main()
