"""
Paper 7 + Paper 2 data acquisition — fire all sources.
Auto-pullable sources fire; harder sources attempted; manual-only sources documented.
"""
import sys, os, requests, time
from pathlib import Path
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding="utf-8")

DATA_DIR = Path("D:/IDP/data")
DATA_DIR.mkdir(exist_ok=True)
OUT = DATA_DIR / "paper7"
OUT.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
}

def try_pull(name, urls, target_dir):
    """Try each URL until one succeeds."""
    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n[{name}]")
    for url in urls:
        fname = Path(urlparse(url).path).name or f"{name.lower()}.bin"
        out_path = target_dir / fname
        print(f"  Trying: {url}")
        try:
            r = requests.get(url, headers=HEADERS, timeout=60, allow_redirects=True)
            if r.status_code == 200 and len(r.content) > 1000:
                out_path.write_bytes(r.content)
                # Check if it's HTML (error page) vs binary
                head = r.content[:200].decode("utf-8", errors="ignore").lower()
                if "<html" in head or "<!doctype" in head:
                    print(f"    [HTML] received error page or login page ({len(r.content):,} bytes)")
                    out_path.unlink()
                    continue
                print(f"    [OK] {fname} -> {out_path} ({len(r.content):,} bytes)")
                return True
            else:
                print(f"    [FAIL] HTTP {r.status_code}, {len(r.content)} bytes")
        except Exception as e:
            print(f"    [ERR] {e}")
        time.sleep(0.5)
    return False

# ============================================================================
# 1. NOAA HURDAT2 — Atlantic hurricane tracks
# ============================================================================
hurdat_ok = try_pull("HURDAT2", [
    "https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2024-053124.txt",
    "https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2023-051624.txt",
    "https://www.nhc.noaa.gov/data/hurdat/hurdat2-atlantic.txt",
], DATA_DIR / "hurdat2")

# ============================================================================
# 2. Eviction Lab — public S3 buckets
# ============================================================================
print("\n[Eviction Lab]")
ev_dir = OUT / "eviction_lab"
ev_dir.mkdir(exist_ok=True)
# Eviction Lab data downloads
ev_files = {
    "ets_states.csv": "https://eviction-lab-data-downloads.s3.amazonaws.com/ets/states_monthly_2020_2024.csv",
    "ets_counties.csv": "https://eviction-lab-data-downloads.s3.amazonaws.com/ets/counties_monthly_2020_2024.csv",
    "ets_cities.csv": "https://eviction-lab-data-downloads.s3.amazonaws.com/ets/cities_monthly_2020_2024.csv",
}
for fname, url in ev_files.items():
    out_path = ev_dir / fname
    try:
        r = requests.get(url, headers=HEADERS, timeout=60)
        if r.status_code == 200:
            out_path.write_bytes(r.content)
            print(f"  [OK] {fname} ({len(r.content):,} bytes)")
        else:
            print(f"  [FAIL] {fname} HTTP {r.status_code}")
    except Exception as e:
        print(f"  [ERR] {fname} -> {e}")

# ============================================================================
# 3. OECD Stat — SOCX + Affordable Housing via SDMX API
# ============================================================================
print("\n[OECD SOCX via SDMX]")
oecd_dir = OUT / "oecd"
oecd_dir.mkdir(exist_ok=True)
# OECD SDMX endpoints (no auth required)
oecd_urls = {
    "socx_agg_csv.csv": "https://sdmx.oecd.org/public/rest/data/OECD.ELS.SAE,DSD_SOCX_AGG@DF_SOCX_AGG,1.0/all?format=csvfilewithlabels",
    "milex_share_gdp.csv": "https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,DSD_GOV@DF_GOV_FUNC,1.0/all?format=csvfilewithlabels",
    "homeless_hc16.csv": "https://sdmx.oecd.org/public/rest/data/OECD.ELS.SAE,DSD_HOMELESS@DF_HOMELESS,1.0/all?format=csvfilewithlabels",
}
for fname, url in oecd_urls.items():
    out_path = oecd_dir / fname
    print(f"  Trying {fname}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=120)
        if r.status_code == 200 and len(r.content) > 500:
            out_path.write_bytes(r.content)
            print(f"    [OK] {len(r.content):,} bytes")
        else:
            print(f"    [FAIL] HTTP {r.status_code}")
    except Exception as e:
        print(f"    [ERR] {e}")

# ============================================================================
# 4. SIPRI — direct Excel attempt
# ============================================================================
sipri_ok = try_pull("SIPRI Military Expenditure", [
    "https://www.sipri.org/sites/default/files/SIPRI-Milex-data-1949-2024_2.xlsx",
    "https://www.sipri.org/sites/default/files/SIPRI-Milex-data-1949-2024.xlsx",
    "https://www.sipri.org/sites/default/files/SIPRI-Milex-data-1949-2023.xlsx",
], OUT / "sipri")

# ============================================================================
# 5. HUD AHAR — direct PDF/Excel attempts
# ============================================================================
hud_ok = try_pull("HUD AHAR 2024", [
    "https://www.huduser.gov/portal/sites/default/files/pdf/2024-AHAR-Part-1.pdf",
    "https://www.huduser.gov/portal/sites/default/files/xls/2007-2024-PIT-Estimates-by-CoC.xlsx",
    "https://www.huduser.gov/portal/sites/default/files/xls/2007-2024-PIT-Estimates-by-State.xlsx",
], OUT / "hud_ahar")

# ============================================================================
# 6. World Bank — Costa Rica + Mauritius indicators
# ============================================================================
print("\n[World Bank API]")
wb_dir = OUT / "world_bank"
wb_dir.mkdir(exist_ok=True)
# World Bank API is fully public
indicators = {
    "military_pct_gdp": "MS.MIL.XPND.GD.ZS",
    "life_expectancy": "SP.DYN.LE00.IN",
    "gdp_per_capita": "NY.GDP.PCAP.CD",
    "education_pct_gdp": "SE.XPD.TOTL.GD.ZS",
    "health_pct_gdp": "SH.XPD.CHEX.GD.ZS",
}
countries = "CRI;MUS;USA;GBR;FRA;DEU;JPN;NOR;FIN;ISL;PAN;HND;NIC;SLV;MDG;MOZ"
for name, indicator in indicators.items():
    url = f"https://api.worldbank.org/v2/country/{countries}/indicator/{indicator}?date=1980:2024&format=json&per_page=2000"
    out_path = wb_dir / f"{name}.json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=60)
        if r.status_code == 200:
            out_path.write_bytes(r.content)
            print(f"  [OK] {name} ({len(r.content):,} bytes)")
        else:
            print(f"  [FAIL] {name} HTTP {r.status_code}")
    except Exception as e:
        print(f"  [ERR] {name} -> {e}")

# ============================================================================
# 7. Finland ARA + Y-Foundation — attempt direct
# ============================================================================
fin_ok = try_pull("Finland ARA Housing Statistics", [
    "https://www.ara.fi/download/noname/%7B59B05DCF-2C04-4DC2-8095-D7D6DBDA9BFF%7D/195681",
    "https://ysaatio.fi/wp-content/uploads/2024/03/Y-Saatio-vuosikertomus-2023.pdf",
], OUT / "finland")

# ============================================================================
# 8. Status summary
# ============================================================================
print("\n" + "=" * 80)
print("DATA ACQUISITION SUMMARY")
print("=" * 80)

results = {
    "HURDAT2": hurdat_ok,
    "Eviction Lab": (ev_dir / "ets_states.csv").exists() if ev_dir.exists() else False,
    "OECD SDMX": bool(list(oecd_dir.glob("*.csv"))),
    "SIPRI": sipri_ok,
    "HUD AHAR": hud_ok,
    "World Bank": bool(list(wb_dir.glob("*.json"))),
    "Finland ARA": fin_ok,
}
for source, ok in results.items():
    flag = "[OK]" if ok else "[MANUAL NEEDED]"
    print(f"  {flag} {source}")

print(f"\nFiles written under: {OUT}")
print(f"HURDAT2 written to: {DATA_DIR / 'hurdat2'}")

# Manual sources reminder
print("\nManual download required for:")
manual = []
if not hud_ok: manual.append("HUD AHAR — https://www.huduser.gov/portal/datasets/ahar.html")
if not sipri_ok: manual.append("SIPRI Milex — https://www.sipri.org/databases/milex (Excel)")
if not fin_ok: manual.append("Finland ARA — https://www.ara.fi/en-US/Materials/Statistics")
manual.append("HadISST — https://www.metoffice.gov.uk/hadobs/hadisst/ (requires Met Office login)")
for m in manual:
    print(f"  - {m}")
