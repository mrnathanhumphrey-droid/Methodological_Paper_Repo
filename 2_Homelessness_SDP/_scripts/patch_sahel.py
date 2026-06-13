"""Sahel patch: HAPI DTM + IDMC IDU + GDELT refilter for BFA/MLI/BEN/NER.

- HAPI DTM: paginated pull per Sahel country (admin-2 IDP figures)
- IDMC IDU: HDX direct search for each Sahel country, fetch CSV if found
- GDELT: refilter existing _raw/ 2014-2024 daily files for Sahel FIPS codes
  (no re-download — cache already has 4012 files)
"""
import base64
import io
import json
import pathlib
import time
import urllib.parse
import urllib.request
import zipfile

ROOT = pathlib.Path("D:/IDP")
DATA = ROOT / "data"

SAHEL = {
    "BFA": {"name": "Burkina Faso", "fips": "UV"},
    "MLI": {"name": "Mali",         "fips": "ML"},
    "BEN": {"name": "Benin",        "fips": "BN"},
    "NER": {"name": "Niger",        "fips": "NG"},
}

APP_ID = base64.b64encode(b"IDP_Study:mr.nathanhumphrey@gmail.com").decode()
UA = "IDP-Study/1.0 (research; mr.nathanhumphrey@gmail.com)"

# === 1. HAPI DTM for 4 Sahel countries (paginated) ===
print(f"[{time.strftime('%H:%M:%S')}] === HAPI DTM Sahel ===")
out = DATA / "dtm"
for iso3 in SAHEL:
    sub = out / iso3.lower()
    sub.mkdir(parents=True, exist_ok=True)
    offset = 0
    total = 0
    while True:
        url = (f"https://hapi.humdata.org/api/v2/affected-people/idps"
               f"?location_code={iso3}&admin_level=2&output_format=json"
               f"&limit=10000&offset={offset}&app_identifier={APP_ID}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = json.load(resp)
        except Exception as e:
            print(f"  {iso3} offset={offset}: FAIL {type(e).__name__}")
            break
        data = payload.get("data", [])
        if not data:
            break
        target = sub / f"page_{offset // 10000:04d}.json"
        target.write_text(json.dumps(payload))
        total += len(data)
        if len(data) < 10000:
            break
        offset += 10000
        time.sleep(0.5)
    print(f"  {iso3}: {total:,} admin-2 IDP records")

# === 2. IDMC IDU Sahel — direct HDX search per country ===
print(f"\n[{time.strftime('%H:%M:%S')}] === IDMC IDU Sahel ===")
idu_dir = DATA / "idmc_gidd" / "idu"
idu_dir.mkdir(parents=True, exist_ok=True)
for iso3 in SAHEL:
    iso3l = iso3.lower()
    target = idu_dir / f"{iso3l}_{iso3l}.csv"
    if target.exists() and target.stat().st_size > 1000:
        print(f"  {iso3}: already on disk ({target.stat().st_size:,} bytes)")
        continue
    # Query HDX search directly
    search_url = f"https://data.humdata.org/api/3/action/package_search?q={iso3l}+idmc+idu&rows=10"
    try:
        req = urllib.request.Request(search_url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as resp:
            results = json.load(resp).get("result", {}).get("results", [])
    except Exception as e:
        print(f"  {iso3} search: FAIL {type(e).__name__}")
        continue
    csv_url = None
    for r in results:
        if iso3l in r.get("name", "").lower() and "idu" in r.get("name", "").lower():
            for res in r.get("resources", []):
                if res.get("url", "").endswith(".csv"):
                    csv_url = res["url"]
                    break
            if csv_url:
                break
    if not csv_url:
        print(f"  {iso3}: no IDU CSV found on HDX")
        continue
    try:
        req = urllib.request.Request(csv_url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as resp:
            target.write_bytes(resp.read())
        print(f"  {iso3}: {target.stat().st_size:,} bytes")
    except Exception as e:
        print(f"  {iso3} csv: FAIL {type(e).__name__}")
    time.sleep(0.5)

# === 3. GDELT refilter — Sahel FIPS codes from existing _raw/ ===
print(f"\n[{time.strftime('%H:%M:%S')}] === GDELT refilter for Sahel ===")
raw_dir = DATA / "gdelt" / "_raw"
out_dir = DATA / "gdelt"

# country -> open file handle
out_files = {}
out_paths = {}
for iso3, info in SAHEL.items():
    p = out_dir / f"gdelt-{info['name'].lower().replace(' ', '_')}-2014_2024.csv"
    if p.exists() and p.stat().st_size > 100:
        print(f"  {iso3}: existing file {p.name} ({p.stat().st_size:,} bytes) — skipping refilter")
        continue
    out_paths[iso3] = p
    out_files[iso3] = open(p, "w", encoding="utf-8", newline="")

# Use header from existing file or hard-coded
HEADER = ("globaleventid|sqldate|monthyear|year|fractiondate|actor1code|actor1name|actor1countrycode|actor1knowngroupcode|"
          "actor1ethniccode|actor1religion1code|actor1religion2code|actor1type1code|actor1type2code|actor1type3code|"
          "actor2code|actor2name|actor2countrycode|actor2knowngroupcode|actor2ethniccode|actor2religion1code|"
          "actor2religion2code|actor2type1code|actor2type2code|actor2type3code|isrootevent|eventcode|eventbasecode|"
          "eventrootcode|quadclass|goldsteinscale|nummentions|numsources|numarticles|avgtone|actor1geo_type|"
          "actor1geo_fullname|actor1geo_countrycode|actor1geo_adm1code|actor1geo_lat|actor1geo_long|actor1geo_featureid|"
          "actor2geo_type|actor2geo_fullname|actor2geo_countrycode|actor2geo_adm1code|actor2geo_lat|actor2geo_long|"
          "actor2geo_featureid|actiongeo_type|actiongeo_fullname|actiongeo_countrycode|actiongeo_adm1code|"
          "actiongeo_lat|actiongeo_long|actiongeo_featureid|dateadded|sourceurl\n")
for f in out_files.values():
    f.write(HEADER)

ACTIONGEO_COUNTRY_COL = 51  # 0-indexed: column 52 in 1-based is index 51
FIPS_TO_ISO3 = {info["fips"]: iso3 for iso3, info in SAHEL.items()}

zip_files = sorted(raw_dir.glob("*.export.CSV.zip"))
print(f"  scanning {len(zip_files)} GDELT daily files for FIPS in {list(FIPS_TO_ISO3)}")

processed = 0
match_counts = {iso3: 0 for iso3 in SAHEL}
for zf_path in zip_files:
    try:
        with zipfile.ZipFile(zf_path) as zf:
            for name in zf.namelist():
                with zf.open(name) as f:
                    for raw in f:
                        line = raw.decode("utf-8", errors="ignore").rstrip("\n")
                        parts = line.split("\t")
                        if len(parts) < 58:
                            continue
                        ag_cc = parts[ACTIONGEO_COUNTRY_COL] if len(parts) > ACTIONGEO_COUNTRY_COL else ""
                        if ag_cc in FIPS_TO_ISO3:
                            iso3 = FIPS_TO_ISO3[ag_cc]
                            if iso3 in out_files:
                                # Write pipe-separated for consistency
                                out_files[iso3].write("|".join(parts) + "\n")
                                match_counts[iso3] += 1
    except Exception as e:
        pass
    processed += 1
    if processed % 200 == 0:
        print(f"    [{time.strftime('%H:%M:%S')}] {processed}/{len(zip_files)} files; matches: {match_counts}")

for f in out_files.values():
    f.close()

print(f"\n[{time.strftime('%H:%M:%S')}] === Sahel patch complete ===")
print(f"  GDELT match counts: {match_counts}")
for iso3, p in out_paths.items():
    sz = p.stat().st_size
    print(f"  {p.name}: {sz:,} bytes")
