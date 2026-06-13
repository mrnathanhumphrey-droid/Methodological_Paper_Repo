"""Fetch GDELT 1.0 conflict events — PHASE 1 full panel 2014-2024.

Expands fetch_gdelt.py (Phase 0 smoke) to the full 2014-01-01..2024-12-31
panel needed for cross-source agreement with UCDP-GED on admin-2 x year
aggregation.

Design for an 8-20 hour background run:
  - Per-day raw cache at data/gdelt/_raw/{YYYYMMDD}.export.CSV.zip
    (skipped if already on disk; survives interruption)
  - Per-country accumulator CSVs at data/gdelt/gdelt-{country}-2014_2024.csv
    are *appended* in 30-day blocks; safe to re-run
  - Per-day filter state at data/gdelt/_progress.json so we can resume
  - Manifest entry written ONCE at end with final SHA-256

Per redline Entry 001:
  - GDELT replaces ACLED for cross-source validation
  - Spearman >= 0.6 threshold UNCHANGED
  - admin-2 x year aggregation UNCHANGED
  - Yemen Houthi-area pre-cond 4 UNCHANGED (just uses GDELT country=YM
    instead of ACLED country=YEM)
"""
import pathlib, sys, hashlib, json, urllib.request, urllib.error, time, io, zipfile
import warnings; warnings.filterwarnings("ignore")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
except Exception:
    pass

ROOT = pathlib.Path(r"D:/IDP")
OUT_DIR = ROOT / "data" / "gdelt"
RAW_DIR = OUT_DIR / "_raw"
PROGRESS = OUT_DIR / "_progress.json"
MANIFEST = ROOT / "manifest.json"

COUNTRY_FIPS = {
    "Colombia": "CO",
    "Sudan":    "SU",
    "DRC":      "CG",
    "Yemen":    "YM",
}
FIPS_TO_COUNTRY = {v: k for k, v in COUNTRY_FIPS.items()}

# Phase 1 full panel
DATE_START = "20140101"
DATE_END   = "20241231"

GDELT_URL = "http://data.gdeltproject.org/events/{date}.export.CSV.zip"
GDELT_COL_COUNTRY = 51

# GDELT 1.0 has exactly 58 columns. ADM2Code does NOT exist in GDELT 1.0
# (it was added in GDELT 2.0). Original fetch added it by mistake; corrected
# here. Files written before 2026-05-18 had 61-col header over 58-col data
# (3-column drift). The fix_gdelt_phase1_headers.py one-shot rewrites
# headers in-place for those existing files.
HEADER_COLS = [
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
    "actor1geo_adm1code", "actor1geo_lat", "actor1geo_long", "actor1geo_featureid",
    "actor2geo_type", "actor2geo_fullname", "actor2geo_countrycode",
    "actor2geo_adm1code", "actor2geo_lat", "actor2geo_long", "actor2geo_featureid",
    "actiongeo_type", "actiongeo_fullname", "actiongeo_countrycode",
    "actiongeo_adm1code", "actiongeo_lat", "actiongeo_long", "actiongeo_featureid",
    "dateadded", "sourceurl",
]
assert len(HEADER_COLS) == 58, f"GDELT 1.0 has 58 columns; got {len(HEADER_COLS)}"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def daterange(start, end):
    from datetime import datetime, timedelta
    d0 = datetime.strptime(start, "%Y%m%d")
    d1 = datetime.strptime(end, "%Y%m%d")
    cur = d0
    while cur <= d1:
        yield cur.strftime("%Y%m%d")
        cur += timedelta(days=1)


def load_progress():
    if PROGRESS.exists():
        try: return json.loads(PROGRESS.read_text())
        except: return {}
    return {}


def save_progress(p):
    PROGRESS.write_text(json.dumps(p, indent=2))


def fetch_one_day(date_str):
    """Download GDELT day zip to cache (skip if present). Returns path or None on 404."""
    cache_path = RAW_DIR / f"{date_str}.export.CSV.zip"
    if cache_path.exists() and cache_path.stat().st_size > 0:
        return cache_path
    url = GDELT_URL.format(date=date_str)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "IDP-Study/1.0"})
        with urllib.request.urlopen(req, timeout=180) as resp:
            raw = resp.read()
        cache_path.write_bytes(raw)
        return cache_path
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except Exception:
        # Surface to caller; loop will retry next pass
        return False


def parse_day(zip_path):
    """Yield (fips, row_cols) for each event in target countries."""
    target_fips = set(FIPS_TO_COUNTRY.keys())
    try:
        with zipfile.ZipFile(zip_path) as zf:
            csv_name = [n for n in zf.namelist() if n.lower().endswith(".csv")][0]
            with zf.open(csv_name) as f:
                for line in f:
                    cols = line.decode("utf-8", errors="replace").rstrip("\n").split("\t")
                    if len(cols) <= GDELT_COL_COUNTRY: continue
                    cc = cols[GDELT_COL_COUNTRY]
                    if cc in target_fips:
                        yield cc, cols
    except (zipfile.BadZipFile, KeyError, IndexError):
        return


def append_country_buffer(fips, rows, file_handles):
    """Append rows for one country to its open per-country CSV."""
    if not rows: return
    f = file_handles[fips]
    for row in rows:
        f.write("\t".join(row) + "\n")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== GDELT 1.0 Phase 1 fetch (full panel {DATE_START}..{DATE_END}) ===")

    progress = load_progress()
    if "done_dates" not in progress:
        progress["done_dates"] = []
        progress["404_dates"] = []
        progress["started_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    done_set = set(progress["done_dates"])
    four_o_four_set = set(progress["404_dates"])

    # Open per-country output CSVs in append mode; write header only if empty
    country_paths = {fips: OUT_DIR / f"gdelt-{FIPS_TO_COUNTRY[fips].lower()}-2014_2024.csv"
                     for fips in FIPS_TO_COUNTRY}
    file_handles = {}
    for fips, p in country_paths.items():
        write_header = (not p.exists()) or (p.stat().st_size == 0)
        f = open(p, "a", encoding="utf-8", newline="")
        if write_header: f.write("\t".join(HEADER_COLS) + "\n")
        file_handles[fips] = f

    dates = list(daterange(DATE_START, DATE_END))
    n_total = len(dates)
    n_skip = len(done_set & set(dates)) + len(four_o_four_set & set(dates))
    print(f"  {n_total} target dates; {n_skip} already done; {n_total - n_skip} to fetch")

    totals = {fips: 0 for fips in FIPS_TO_COUNTRY}
    t0 = time.time()
    last_save = t0
    last_print = t0

    for i, d in enumerate(dates, 1):
        if d in done_set or d in four_o_four_set:
            continue
        zp = fetch_one_day(d)
        if zp is None:
            four_o_four_set.add(d)
            progress["404_dates"].append(d)
            continue
        if zp is False:
            # Transient failure — leave for next pass; do NOT mark done
            time.sleep(1.0)
            continue
        for fips, row in parse_day(zp):
            file_handles[fips].write("\t".join(row) + "\n")
            totals[fips] += 1
        done_set.add(d)
        progress["done_dates"].append(d)

        now = time.time()
        if now - last_save > 60:
            for f in file_handles.values(): f.flush()
            save_progress(progress)
            last_save = now
        if now - last_print > 30 or i == n_total:
            elapsed = now - t0
            n_done_this_run = (i - n_skip) if i >= n_skip else 0
            rate = n_done_this_run / max(elapsed, 1e-6)
            remain = (n_total - i) / max(rate, 1e-6) if rate > 0 else 0
            print(f"  [{i:5d}/{n_total}] {d} | events: " +
                  ", ".join(f"{FIPS_TO_COUNTRY[f]}={totals[f]:,}" for f in totals) +
                  f" | rate={rate:.2f}/s | ETA={remain/3600:.1f}h")
            last_print = now

    for f in file_handles.values(): f.close()
    save_progress(progress)

    print(f"\n=== writing final manifest entries ===")
    manifest = {}
    if MANIFEST.exists():
        try: manifest = json.loads(MANIFEST.read_text())
        except: manifest = {}
    for fips, p in country_paths.items():
        if not p.exists() or p.stat().st_size == 0: continue
        n_rows = sum(1 for _ in open(p, encoding="utf-8")) - 1
        country = FIPS_TO_COUNTRY[fips]
        # Drop any prior phase 1 entry for the same file before appending
        manifest.setdefault("files", [])
        manifest["files"] = [m for m in manifest["files"]
                             if m.get("filename") != str(p.relative_to(ROOT))]
        manifest["files"].append({
            "source": f"GDELT 1.0 filtered: {country} (Phase 1 full panel {DATE_START}..{DATE_END})",
            "filename": str(p.relative_to(ROOT)),
            "sha256": sha256(p),
            "size_bytes": p.stat().st_size,
            "row_count": n_rows,
            "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "fips_country_code": fips,
        })
        print(f"  {country}: {n_rows:,} events -> {p.name}")
    manifest["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    MANIFEST.write_text(json.dumps(manifest, indent=2))
    print(f"\n=== GDELT Phase 1 complete. Files in {OUT_DIR} ===")


if __name__ == "__main__":
    main()
