"""Fetch GDELT 2.0 conflict events filtered to the 4 study countries.

REPLACES fetch_acled.py per pre_reg_redline.md Entry 001 (2026-05-17).

GDELT 1.0 publishes daily event files at:
  http://data.gdeltproject.org/events/{YYYYMMDD}.export.CSV.zip

Each daily file is tab-separated, no header, 57 columns per GDELT 1.0
documentation. Key columns (0-indexed):
   0  GLOBALEVENTID
   1  SQLDATE       (YYYYMMDD)
   3  Year
  26  EventCode     (CAMEO; 19=Fight, 20=Use unconventional mass violence)
  27  EventBaseCode
  28  EventRootCode (1-letter; 1=Make public statement, 2=Appeal, ..., 19=Fight, 20=Mass violence)
  29  QuadClass     (1=Verbal Coop, 2=Material Coop, 3=Verbal Conflict, 4=Material Conflict)
  30  GoldsteinScale
  31  NumMentions
  32  NumSources
  33  NumArticles
  34  AvgTone
  51  ActionGeo_CountryCode (FIPS 10-4 country code)
  52  ActionGeo_ADM1Code
  53  ActionGeo_ADM2Code
  54  ActionGeo_Lat
  55  ActionGeo_Long
  56  ActionGeo_FeatureID
  57  DATEADDED

Country FIPS codes:
  Colombia = CO
  Sudan    = SU (combined N/S Sudan pre-2011 split; some files may have OD for South Sudan)
  DRC      = CG (Congo, Democratic Republic of)
  Yemen    = YM

Phase 0 execution: smoke-test single-month fetch (December 2024) to
prove the pipeline works. Phase 1 expands to full 2014-2024 panel.

The 1-month smoke test is enough to demonstrate the pipeline end-to-end
+ unblock the pre-cond 2 + 4 redline path. Full 11-year panel is
budgeted for Phase 1.

Per redline Entry 001:
  - GDELT replaces ACLED for cross-source validation
  - Spearman >= 0.6 threshold UNCHANGED
  - admin-2 x year aggregation UNCHANGED
  - Yemen Houthi-area pre-cond 4 UNCHANGED (just uses GDELT country=YM
    instead of ACLED country=YEM)
"""
import pathlib, sys, hashlib, json, urllib.request, urllib.error, time, io, zipfile, csv
import warnings; warnings.filterwarnings("ignore")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
except Exception:
    pass
import pandas as pd

ROOT = pathlib.Path(r"D:/IDP")
OUT_DIR = ROOT / "data" / "gdelt"
MANIFEST = ROOT / "manifest.json"

COUNTRY_FIPS = {
    "Colombia": "CO",
    "Sudan":    "SU",
    "DRC":      "CG",
    "Yemen":    "YM",
}

# Phase 0 smoke test: fetch December 2024 (31 days). Phase 1 expands.
SMOKE_DATE_START = "20241201"
SMOKE_DATE_END   = "20241231"

# Phase 1 full panel (commented out for Phase 0):
# DATE_START = "20140101"
# DATE_END   = "20241231"

GDELT_URL = "http://data.gdeltproject.org/events/{date}.export.CSV.zip"

# GDELT 1.0 column count (no header). ActionGeo_CountryCode at index 51.
GDELT_COL_COUNTRY = 51
GDELT_COL_LAT = 54
GDELT_COL_LON = 55
GDELT_COL_EVENT_ROOT = 28


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


def daterange(start, end):
    """Yield YYYYMMDD strings between start and end inclusive."""
    from datetime import datetime, timedelta
    d0 = datetime.strptime(start, "%Y%m%d")
    d1 = datetime.strptime(end, "%Y%m%d")
    cur = d0
    while cur <= d1:
        yield cur.strftime("%Y%m%d")
        cur += timedelta(days=1)


def fetch_day(date_str, country_buffers):
    """Fetch one daily GDELT file, filter to our 4 countries, append to per-country buffers.

    country_buffers: dict mapping FIPS -> list of row strings (tab-separated)
    Returns: dict mapping FIPS -> rows-appended-this-day
    """
    url = GDELT_URL.format(date=date_str)
    appended = {fips: 0 for fips in country_buffers}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "IDP-Study/0.1"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"  [{date_str}] 404 (file not available; some early-2014 dates have gaps)")
            return appended
        else:
            print(f"  [{date_str}] HTTP {e.code}: skip")
            return appended
    except Exception as e:
        print(f"  [{date_str}] FAIL: {type(e).__name__}: {e}")
        return appended

    # Parse the zipped CSV
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            csv_name = [n for n in zf.namelist() if n.endswith(".CSV") or n.endswith(".csv")][0]
            with zf.open(csv_name) as f:
                for line in f:
                    cols = line.decode("utf-8", errors="replace").rstrip("\n").split("\t")
                    if len(cols) <= GDELT_COL_COUNTRY: continue
                    cc = cols[GDELT_COL_COUNTRY]
                    if cc in country_buffers:
                        country_buffers[cc].append(cols)
                        appended[cc] += 1
    except Exception as e:
        print(f"  [{date_str}] parse FAIL: {type(e).__name__}: {e}")
    return appended


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== GDELT 2.0 fetch (4-country panel; Phase 0 smoke test {SMOKE_DATE_START}..{SMOKE_DATE_END}) ===")

    fips_to_country = {v: k for k, v in COUNTRY_FIPS.items()}
    country_buffers = {fips: [] for fips in fips_to_country}

    dates = list(daterange(SMOKE_DATE_START, SMOKE_DATE_END))
    print(f"  fetching {len(dates)} daily files ...")
    totals = {fips: 0 for fips in fips_to_country}
    for i, d in enumerate(dates, 1):
        appended = fetch_day(d, country_buffers)
        for f, n in appended.items(): totals[f] += n
        if i % 5 == 0 or i == len(dates):
            print(f"  [{i}/{len(dates)}] {d}: cumulative " +
                  ", ".join(f"{fips_to_country[f]}={totals[f]:,}" for f in totals))

    # Write per-country CSVs
    print(f"\n=== writing per-country CSVs ===")
    for fips, rows in country_buffers.items():
        country = fips_to_country[fips]
        out_path = OUT_DIR / f"gdelt-{country.lower()}.csv"
        # GDELT 1.0 has 57 columns; produce CSV with named headers for the columns we'll actually use downstream
        header_min = [
            "globaleventid", "sqldate", "monthyear", "year", "fractiondate",
            "actor1code", "actor1name", "actor1countrycode", "actor1knowngroupcode",
            "actor1ethniccode", "actor1religion1code", "actor1religion2code",
            "actor1type1code", "actor1type2code", "actor1type3code",
            "actor2code", "actor2name", "actor2countrycode", "actor2knowngroupcode",
            "actor2ethniccode", "actor2religion1code", "actor2religion2code",
            "actor2type1code", "actor2type2code", "actor2type3code",
            "isrootevent", "eventcode", "eventbasecode", "eventrootcode",
            "quadclass", "goldsteinscale", "nummentions", "numsources", "numarticles", "avgtone",
            "actor1geo_type", "actor1geo_fullname", "actor1geo_countrycode",
            "actor1geo_adm1code", "actor1geo_adm2code", "actor1geo_lat", "actor1geo_long", "actor1geo_featureid",
            "actor2geo_type", "actor2geo_fullname", "actor2geo_countrycode",
            "actor2geo_adm1code", "actor2geo_adm2code", "actor2geo_lat", "actor2geo_long", "actor2geo_featureid",
            "actiongeo_type", "actiongeo_fullname", "actiongeo_countrycode",
            "actiongeo_adm1code", "actiongeo_adm2code", "actiongeo_lat", "actiongeo_long", "actiongeo_featureid",
            "dateadded", "sourceurl",
        ]
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            f.write("\t".join(header_min) + "\n")
            for row in rows:
                f.write("\t".join(row) + "\n")
        n = len(rows)
        print(f"  {country}: {n:,} events -> {out_path.name}")
        if n > 0:
            update_manifest({
                "source": f"GDELT 1.0 filtered: {country} (Phase 0 smoke test {SMOKE_DATE_START}..{SMOKE_DATE_END})",
                "filename": str(out_path.relative_to(ROOT)),
                "sha256": sha256(out_path),
                "size_bytes": out_path.stat().st_size,
                "row_count": n,
                "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "fips_country_code": fips,
            })

    print(f"\n=== GDELT Phase 0 smoke test complete. Files in {OUT_DIR} ===")
    print(f"  Phase 1 will expand to full 2014-2024 panel.")


if __name__ == "__main__":
    main()
