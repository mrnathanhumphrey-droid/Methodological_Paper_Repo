"""
Paper 7 data acquisition stub — staged but NOT fired.
Pulls HUD AHAR + Eviction Lab + SIPRI + OECD SOCX + OECD Affordable Housing + Finland Housing First data.

Run individually or all-at-once after user approval. Each source documented separately for transparency.

USAGE: python paper7_data_acquisition_stub.py [source]
   where source in: hud, eviction_lab, sipri, oecd_socx, oecd_housing, finland, all
"""
import sys
import os
import requests
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
OUT_DIR = Path("D:/IDP/data/paper7")
OUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "ResolveResearch+IDP+jpofjd$% (Paper 7 SDP framework research; contact: mr.nathanhumphrey@gmail.com)"
}

def pull_hud_ahar():
    """HUD Annual Homeless Assessment Report (PIT counts).
    Source: HUD User HUD Open Data Portal.
    URL: https://www.huduser.gov/portal/datasets/ahar.html
    Files needed:
    - 2007-2024 Point-in-Time (PIT) Estimates by CoC
    - Long-term trends dataset
    """
    print("[HUD AHAR] — manual download required")
    print("  URL: https://www.huduser.gov/portal/datasets/ahar/2024-ahar-part-1-pit-estimates-of-homelessness-in-the-us.html")
    print("  Place files in:", OUT_DIR / "hud_ahar")
    (OUT_DIR / "hud_ahar").mkdir(exist_ok=True)
    # Note: HUD AHAR requires manual download from HUD User portal
    # Can be automated via huduser.gov API if API key obtained

def pull_eviction_lab():
    """Eviction Lab (Princeton) — county-level eviction filings.
    Source: evictionlab.org
    URL: https://evictionlab.org/eviction-tracking/
    """
    print("[Eviction Lab] — checking public data downloads")
    # Eviction Lab has tract-level + city-level + state-level CSVs
    base_url = "https://eviction-lab-data-downloads.s3.amazonaws.com/"
    files_to_try = [
        "ets/all_sites_monthly_2020_2024.csv",
        "states.csv",
        "counties.csv",
    ]
    target_dir = OUT_DIR / "eviction_lab"
    target_dir.mkdir(exist_ok=True)
    for f in files_to_try:
        url = base_url + f
        out_file = target_dir / Path(f).name
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 200:
                out_file.write_bytes(r.content)
                print(f"  [OK] {f} -> {out_file} ({len(r.content):,} bytes)")
            else:
                print(f"  [FAIL] {f} -> HTTP {r.status_code}")
        except Exception as e:
            print(f"  [ERR] {f} -> {e}")

def pull_sipri():
    """SIPRI Military Expenditure Database.
    Source: sipri.org
    URL: https://www.sipri.org/databases/milex
    Files: SIPRI-Milex-data-1949-2024.xlsx
    """
    print("[SIPRI] — manual download required")
    print("  URL: https://www.sipri.org/databases/milex")
    print("  Look for: SIPRI Milex Excel — 'Constant 2022 USD'")
    print("  Place files in:", OUT_DIR / "sipri")
    (OUT_DIR / "sipri").mkdir(exist_ok=True)

def pull_oecd_socx():
    """OECD Social Expenditure Database (SOCX).
    Source: oecd.org SOCX
    URL: https://www.oecd.org/social/expenditure.htm
    Files: SOCX_AGG (aggregated data by country-year-category)
    """
    print("[OECD SOCX] — OECD.Stat API available")
    print("  Endpoint: https://stats.oecd.org/SDMX-JSON/data/SOCX_AGG/")
    print("  Place files in:", OUT_DIR / "oecd_socx")
    (OUT_DIR / "oecd_socx").mkdir(exist_ok=True)

def pull_oecd_housing():
    """OECD Affordable Housing Database.
    Source: oecd.org/housing
    URL: https://www.oecd.org/housing/data/affordable-housing-database/
    Files: HC1.6 Homeless rate; HC3 Housing conditions
    """
    print("[OECD Affordable Housing] — direct CSV downloads available")
    print("  URL: https://www.oecd.org/housing/data/affordable-housing-database/")
    print("  Place files in:", OUT_DIR / "oecd_housing")
    (OUT_DIR / "oecd_housing").mkdir(exist_ok=True)

def pull_finland():
    """Finland Housing First data — ARA + Y-Foundation.
    Source: ara.fi statistics
    URL: https://www.ara.fi/en-US/Materials/Statistics
    Files: long-term homelessness time series 2008-2024
    """
    print("[Finland ARA] — manual download required")
    print("  URL: https://www.ara.fi/en-US/Materials/Statistics")
    print("  Place files in:", OUT_DIR / "finland")
    (OUT_DIR / "finland").mkdir(exist_ok=True)

def pull_paper2_climate():
    """Paper 2 PRE_REG_015 climate-attribution data — HURDAT2 + HadISST.
    HURDAT2: NHC NOAA hurricane track database (Atlantic 1851-2024)
    HadISST: Hadley Centre Sea Surface Temperature 1870-2024
    """
    print("[NOAA HURDAT2] — direct download available")
    hurdat2_url = "https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2024-053124.txt"
    target = OUT_DIR.parent / "hurdat2"
    target.mkdir(exist_ok=True)
    try:
        r = requests.get(hurdat2_url, headers=HEADERS, timeout=60)
        if r.status_code == 200:
            (target / "hurdat2-1851-2024.txt").write_bytes(r.content)
            print(f"  [OK] HURDAT2 ({len(r.content):,} bytes)")
        else:
            print(f"  [FAIL] HURDAT2 HTTP {r.status_code}")
    except Exception as e:
        print(f"  [ERR] HURDAT2 -> {e}")

    print("[HadISST] — manual download (requires Met Office login)")
    print("  URL: https://www.metoffice.gov.uk/hadobs/hadisst/")

if __name__ == "__main__":
    source = sys.argv[1] if len(sys.argv) > 1 else "all"
    if source in ("all", "hud"):
        pull_hud_ahar()
    if source in ("all", "eviction_lab"):
        pull_eviction_lab()
    if source in ("all", "sipri"):
        pull_sipri()
    if source in ("all", "oecd_socx"):
        pull_oecd_socx()
    if source in ("all", "oecd_housing"):
        pull_oecd_housing()
    if source in ("all", "finland"):
        pull_finland()
    if source in ("all", "paper2_climate", "climate"):
        pull_paper2_climate()

    print("\nDone. Manual-download sources require user action.")
    print("Re-run with specific source name to skip others.")
