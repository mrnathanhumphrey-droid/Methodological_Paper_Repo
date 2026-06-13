"""Fetch UCDP-GED (Uppsala Conflict Data Program Georeferenced Event Dataset).

Pulls UCDP-GED v25.1 (or latest available) for the 4 study countries:
Colombia, Sudan, DRC, Yemen. Country-filtered events 1989-present.

Output: data/ucdp/ucdp-ged-{country}-{year_range}.csv + manifest_entry.

UCDP-GED is the canonical georeferenced conflict event dataset. Each row =
one violent event with lat/long, date, fatality counts (best/low/high
estimates), conflict type code.
"""
import pathlib, sys, hashlib, json, urllib.request, urllib.error, time, io, csv, gzip
import warnings; warnings.filterwarnings("ignore")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
except Exception:
    pass

ROOT = pathlib.Path(r"D:/IDP")
OUT_DIR = ROOT / "data" / "ucdp"
MANIFEST = ROOT / "manifest.json"

# UCDP-GED v25.1 (or latest) candidate URLs. The UCDP downloads page is at
# https://ucdp.uu.se/downloads/index.html#armedconflict. Direct file URLs
# follow the pattern below; if the version bumps, update here.
UCDP_GED_CANDIDATES = [
    "https://ucdp.uu.se/downloads/ged/ged251-csv.zip",
    "https://ucdp.uu.se/downloads/ged/ged241-csv.zip",
    "https://ucdp.uu.se/downloads/ged/ged231-csv.zip",
]

# Country FIPS / Gleditsch-Ward country codes used in UCDP-GED's `country_id` field
COUNTRY_CODES = {
    # UCDP uses Gleditsch & Ward (GW) country codes
    "Colombia": 100,
    "Sudan":    625,   # post-2011 (north) Sudan
    "South_Sudan": 626,  # included for completeness, may filter out
    "DRC":      490,   # Democratic Republic of Congo (Zaire)
    "Yemen":    678,   # UCDP v25.1 retains 678 (North Yemen historical code) for unified Yemen post-1990
}


def fetch_url(url, dest, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "IDP-Study/0.1"})
            with urllib.request.urlopen(req, timeout=300) as resp:
                with open(dest, "wb") as f:
                    f.write(resp.read())
            return True
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print(f"  attempt {attempt+1}/{retries} failed: {type(e).__name__}: {e}")
            time.sleep(5 * (attempt + 1))
    return False


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def update_manifest(entry):
    manifest = {}
    if MANIFEST.exists():
        try: manifest = json.loads(MANIFEST.read_text())
        except: manifest = {}
    manifest.setdefault("files", []).append(entry)
    manifest["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    MANIFEST.write_text(json.dumps(manifest, indent=2))


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== UCDP-GED fetch (4-country panel: Colombia, Sudan, DRC, Yemen) ===")

    # Try each candidate URL
    ged_zip = OUT_DIR / "ucdp-ged-latest.zip"
    if ged_zip.exists():
        print(f"[cache] {ged_zip} already present, skipping download")
    else:
        for url in UCDP_GED_CANDIDATES:
            print(f"  trying {url} ...")
            if fetch_url(url, ged_zip):
                print(f"  downloaded {ged_zip}")
                break
        if not ged_zip.exists():
            print(f"FAIL: no UCDP-GED URL accessible. Manual download required from "
                  f"https://ucdp.uu.se/downloads/", file=sys.stderr)
            sys.exit(1)

    # Record manifest entry
    update_manifest({
        "source": "UCDP-GED",
        "url": "https://ucdp.uu.se/downloads/",
        "filename": str(ged_zip.relative_to(ROOT)),
        "sha256": sha256(ged_zip),
        "size_bytes": ged_zip.stat().st_size,
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    })

    # Unzip + filter to study countries
    import zipfile
    with zipfile.ZipFile(ged_zip) as zf:
        ged_csvs = [n for n in zf.namelist() if n.endswith(".csv")]
        if not ged_csvs:
            print(f"FAIL: no CSV inside {ged_zip}", file=sys.stderr); sys.exit(1)
        main_csv = ged_csvs[0]
        print(f"  extracting {main_csv}")
        zf.extract(main_csv, OUT_DIR)

    raw_csv = OUT_DIR / main_csv
    print(f"  reading {raw_csv}")
    import pandas as pd
    df = pd.read_csv(raw_csv, low_memory=False)
    print(f"  total events: {len(df):,}")
    print(f"  columns: {list(df.columns)[:25]}")

    # Filter to study countries
    if "country_id" in df.columns:
        gw_col = "country_id"
    elif "gwnoa" in df.columns:
        gw_col = "gwnoa"
    elif "country" in df.columns:
        gw_col = "country"
    else:
        print(f"FAIL: cannot identify country column. Cols: {list(df.columns)}", file=sys.stderr); sys.exit(1)

    for country, code in COUNTRY_CODES.items():
        if gw_col == "country":  # text match
            sub = df[df[gw_col].astype(str).str.contains(country.replace("_", " "), case=False, na=False)]
        else:
            sub = df[pd.to_numeric(df[gw_col], errors="coerce") == code]
        out_path = OUT_DIR / f"ucdp-ged-{country.lower().replace(' ','_')}.csv"
        sub.to_csv(out_path, index=False)
        update_manifest({
            "source": f"UCDP-GED filtered: {country}",
            "filename": str(out_path.relative_to(ROOT)),
            "sha256": sha256(out_path),
            "size_bytes": out_path.stat().st_size,
            "row_count": len(sub),
            "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        # Year coverage check
        year_col = "year" if "year" in sub.columns else ("date_start" if "date_start" in sub.columns else None)
        if year_col:
            try:
                years = pd.to_datetime(sub[year_col], errors="coerce").dt.year if "date" in year_col else pd.to_numeric(sub[year_col], errors="coerce")
                y_min, y_max = int(years.min()) if years.notna().any() else None, int(years.max()) if years.notna().any() else None
            except: y_min, y_max = None, None
        else: y_min, y_max = None, None
        print(f"  {country}: {len(sub):,} events, year range {y_min}-{y_max}")

    print(f"\n=== UCDP fetch complete. {len(COUNTRY_CODES)} country files in {OUT_DIR} ===")


if __name__ == "__main__":
    main()
