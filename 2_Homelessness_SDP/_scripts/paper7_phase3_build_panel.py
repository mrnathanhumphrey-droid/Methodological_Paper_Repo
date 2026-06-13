"""
Paper 7 Phase 3 — build US state x year SDP panel.

Inputs (already fetched):
- data/paper7/hud_pit/2007-2024-PIT-Counts-by-CoC.xlsb  (18 year-sheets)
- data/paper7/acs_cost_burden/acs_b25070_cost_burden_state_year.json

Outputs:
- analysis/paper7_sdp_state_year_panel.parquet
- analysis/paper7_sdp_state_year_panel.csv

Observable vector (25-col cross-year-stable HUD intersection -> derived shares):
- overall_homeless (level)            rate per 10k via Census B01003 population
- unsheltered_share = Unsheltered / Overall            (street/enforcement/climate)
- chronic_share     = Chronic Individuals / Overall    (institutional-discharge/disability)
- family_share      = People in Families / Overall     (economic/eviction shock)
- es_share          = Sheltered ES / Overall           (emergency-shelter program mix)
- th_share          = Sheltered TH / Overall           (transitional-housing program mix)
Covariates (mechanism gradient fields):
- cb_share, severe_share   (ACS renter cost-burden -> unaffordability gradient)

State parsed from CoC Number prefix (USPS 2-letter). Non-state rows dropped.
2020 ACS 1-yr gap carried as NaN (flagged, not imputed here).
"""
from __future__ import annotations

import json
import re
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:/IDP")
PIT = ROOT / "data/paper7/hud_pit/2007-2024-PIT-Counts-by-CoC.xlsb"
ACS = ROOT / "data/paper7/acs_cost_burden/acs_b25070_cost_burden_state_year.json"
OUT_PARQUET = ROOT / "analysis/paper7_sdp_state_year_panel.parquet"
OUT_CSV = ROOT / "analysis/paper7_sdp_state_year_panel.csv"

CORE = {
    "overall_homeless": "Overall Homeless",
    "unsheltered": "Unsheltered Homeless",
    "chronic_ind": "Overall Chronically Homeless Individuals",
    "ppl_in_families": "Overall Homeless People in Families",
    "individuals": "Overall Homeless Individuals",
    "shelt_es": "Sheltered ES Homeless",
    "shelt_th": "Sheltered TH Homeless",
}
COC_RE = re.compile(r"^([A-Z]{2})-\d")
UA = "Mozilla/5.0 (research; IDP Paper 7)"
FIPS2USPS = {  # FIPS -> USPS for population join
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO",
    "09": "CT", "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI",
    "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
    "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
    "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
    "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
    "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
    "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
    "54": "WV", "55": "WI", "56": "WY", "72": "PR",
}


def load_key() -> str:
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("CENSUS_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no key")


def fetch_population() -> pd.DataFrame:
    """Census B01003 total population, state x year (ACS 1-yr; 2020 -> 5-yr fallback)."""
    key = load_key()
    rows = []
    for y in range(2007, 2025):
        if y == 2020:
            url = (f"https://api.census.gov/data/2020/acs/acs5?get=NAME,B01003_001E"
                   f"&for=state:*&key={key}")
        else:
            url = (f"https://api.census.gov/data/{y}/acs/acs1?get=NAME,B01003_001E"
                   f"&for=state:*&key={key}")
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                payload = json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001
            print(f"[pop] {y} FAILED {e}")
            continue
        h, *data = payload
        i = {c: j for j, c in enumerate(h)}
        for rec in data:
            usps = FIPS2USPS.get(rec[i["state"]])
            if usps:
                rows.append({"year": y, "state": usps,
                             "population": float(rec[i["B01003_001E"]] or 0)})
        time.sleep(0.2)
    return pd.DataFrame(rows)


def build_hud() -> pd.DataFrame:
    frames = []
    for y in range(2007, 2025):
        df = pd.read_excel(PIT, sheet_name=str(y), engine="pyxlsb")
        df = df[list(CORE.values()) + ["CoC Number"]].copy()
        df.rename(columns={v: k for k, v in CORE.items()}, inplace=True)
        df["state"] = df["CoC Number"].astype(str).str.extract(COC_RE)[0]
        df = df[df["state"].notna()].copy()
        for c in CORE:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        agg = df.groupby("state", as_index=False)[list(CORE)].sum(min_count=1)
        agg["year"] = y
        frames.append(agg)
        print(f"[hud] {y}: {agg['state'].nunique()} states, "
              f"{int(agg['overall_homeless'].sum()):,} overall homeless")
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    hud = build_hud()
    acs = pd.DataFrame(json.loads(ACS.read_text()))
    acs["state"] = acs["state_fips"].map(FIPS2USPS)
    acs = acs[acs["state"].notna()][["year", "state", "cb_share", "severe_share",
                                     "renter_hh_total"]]
    pop = fetch_population()

    panel = hud.merge(pop, on=["year", "state"], how="left")
    panel = panel.merge(acs, on=["year", "state"], how="left")

    # derived shares (guard divide-by-zero)
    oh = panel["overall_homeless"].replace(0, np.nan)
    panel["unsheltered_share"] = panel["unsheltered"] / oh
    panel["chronic_share"] = panel["chronic_ind"] / oh
    panel["family_share"] = panel["ppl_in_families"] / oh
    panel["es_share"] = panel["shelt_es"] / oh
    panel["th_share"] = panel["shelt_th"] / oh
    panel["homeless_per_10k"] = panel["overall_homeless"] / panel["population"] * 1e4

    panel = panel.sort_values(["state", "year"]).reset_index(drop=True)
    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(OUT_PARQUET, index=False)
    panel.to_csv(OUT_CSV, index=False)
    print(f"\n[panel] {panel.shape[0]} state-years x {panel.shape[1]} cols")
    print(f"[panel] states={panel['state'].nunique()} years={panel['year'].min()}-{panel['year'].max()}")
    print(f"[panel] cost-burden coverage: {panel['cb_share'].notna().sum()}/{len(panel)} "
          f"(2020 gap = {panel[panel['year']==2020]['cb_share'].isna().sum()} states)")
    print(f"[panel] wrote {OUT_PARQUET}")
    # quick sanity: 2024 national total
    t2024 = panel[panel["year"] == 2024]["overall_homeless"].sum()
    print(f"[panel] 2024 national overall homeless = {int(t2024):,} (AHAR 2024 ~771k expected)")


if __name__ == "__main__":
    main()
