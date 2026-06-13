"""
PRE_REG_042 / Paper 9 Phase 1 — ACS 5-yr 2024 PUMS extract for displacement origins.

Pulls per-person records for the 15 pre-locked origins across all states, with
variables needed for the variance-decomposition + differential-outcome test
(state, origin, year-of-entry cohort, citizenship, employment, wage, edu, English,
SNAP, Medicaid, poverty ratio, class-of-worker).
"""
from __future__ import annotations
import json, os, sys, time, urllib.parse, urllib.request
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()
KEY = os.environ["CENSUS_API_KEY"]
YEAR = 2024  # ACS 5-yr 2020-2024
OUT_DIR = Path("D:/IDP/data/paper9/acs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

ORIGIN_TO_POBP = {
    "Ukraine": "164", "Venezuela": "373", "Cuba": "327", "Honduras": "314",
    "El Salvador": "312", "Guatemala": "313", "Haiti": "332",
    "Afghanistan": "200", "Syria": "239", "Iraq": "213", "Myanmar": "205",
    "DRC": "459", "Eritrea": "417", "Somalia": "448", "Sudan": "451",
}
POBP_LIST = list(ORIGIN_TO_POBP.values())
POBP_TO_ORIGIN = {v: k for k, v in ORIGIN_TO_POBP.items()}

# Person-level PUMS variables. CIT=citizenship; ESR=employment status; WAGP=wages;
# SCHL=education; ENG=English ability; FS=food stamps; HINS4=Medicaid; POVPIP=poverty %;
# COW=class of worker; NATIVITY=native/foreign-born; YOEP=year of entry.
VARS = ["POBP", "YOEP", "CIT", "AGEP", "PWGTP", "ESR", "WAGP",
        "SCHL", "ENG", "FS", "HINS4", "POVPIP", "COW", "NATIVITY"]
# Note: state arrives as 'state' column via &for=state:XX (no need to GET it)

STATE_FIPS = [f"{i:02d}" for i in [
    1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23,
    24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41,
    42, 44, 45, 46, 47, 48, 49, 50, 51, 53, 54, 55, 56,
]]


def fetch(url, retries=3, wait=2.0):
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read())
        except Exception as e:
            if i == retries - 1:
                raise
            time.sleep(wait * (2 ** i))


def query_state(st: str):
    """Pull PUMS for one state, filtered to the 15 origin POBPs.

    Census API quirk: the comma-list filter (POBP=A,B,C) silently drops the first
    and last values. Use repeated &POBP=A&POBP=B... instead.
    """
    get = ",".join(VARS)
    base = f"https://api.census.gov/data/{YEAR}/acs/acs5/pums"
    parts = [("get", get), ("for", f"state:{st}")]
    for code in POBP_LIST:
        parts.append(("POBP", code))
    parts.append(("key", KEY))
    qs = urllib.parse.urlencode(parts)
    url = f"{base}?{qs}"
    data = fetch(url)
    df = pd.DataFrame(data[1:], columns=data[0])
    return df


def main():
    all_frames = []
    print(f"ACS 5-yr {YEAR} PUMS extract — {len(STATE_FIPS)} states × {len(POBP_LIST)} POBPs")
    for st in STATE_FIPS:
        try:
            df = query_state(st)
            df["state_fips"] = st
            all_frames.append(df)
            print(f"  ST {st}: {len(df):>6} records")
        except Exception as e:
            print(f"  ST {st}: FAIL {type(e).__name__} {str(e)[:80]}")
    if not all_frames:
        print("No data; aborting."); return
    full = pd.concat(all_frames, ignore_index=True)
    # dedupe columns (Census API echoes filter predicates → duplicate POBP)
    full = full.loc[:, ~full.columns.duplicated()]
    # numeric coercion
    for c in ["YOEP", "CIT", "AGEP", "PWGTP", "ESR", "WAGP", "SCHL",
              "ENG", "FS", "HINS4", "POVPIP", "COW", "NATIVITY"]:
        if c in full.columns:
            full[c] = pd.to_numeric(full[c], errors="coerce")
    full["origin"] = full["POBP"].map(POBP_TO_ORIGIN)
    print(f"\nTotal records: {len(full):,}")
    print("\nBy origin:")
    print(full.groupby("origin", dropna=False).size().sort_values(ascending=False).to_string())
    print("\nBy origin (PWGTP-weighted, est foreign-born population):")
    wpop = full.groupby("origin", dropna=False).apply(
        lambda d: int(d["PWGTP"].sum()), include_groups=False
    ).sort_values(ascending=False)
    print(wpop.to_string())
    print("\nBy entry-cohort (PWGTP-weighted, all origins):")
    full["cohort"] = pd.cut(full["YOEP"],
                            bins=[1989, 2017, 2019, 2021, 2023, 2025],
                            labels=["pre-2018", "2018-2019", "2020-2021", "2022-2023", "2024"])
    print(full.groupby("cohort", observed=False).apply(
        lambda d: int(d["PWGTP"].sum()), include_groups=False
    ).to_string())
    out = OUT_DIR / f"acs5_{YEAR}_pums_origins.csv"
    full.to_csv(out, index=False)
    print(f"\nSaved {len(full):,} records -> {out}")
    print(f"({out.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
