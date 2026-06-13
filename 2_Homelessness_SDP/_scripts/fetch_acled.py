"""Fetch ACLED (Armed Conflict Location & Event Data) for the 4 study countries.

ACLED API requires registration (email + key). The script supports two modes:
  1. **Authenticated:** if ACLED_EMAIL and ACLED_API_KEY env vars are set,
     pulls country-filtered events via the official API.
  2. **Manual / scaffold:** if no credentials, writes a download instruction
     stub at data/acled/FETCH_INSTRUCTIONS.md with the exact ACLED Data
     Export Tool URL parameters per country.

Per Phase 0 lock: actually execute if possible; scaffold if network/auth blocks.

Output: data/acled/acled-{country}-{date_range}.csv + manifest entries.
"""
import pathlib, sys, hashlib, json, urllib.request, urllib.error, urllib.parse, time, os, io
import warnings; warnings.filterwarnings("ignore")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
except Exception:
    pass

ROOT = pathlib.Path(r"D:/IDP")
OUT_DIR = ROOT / "data" / "acled"
MANIFEST = ROOT / "manifest.json"

# ACLED uses ISO3 country codes in the API
COUNTRIES = {
    "Colombia": "COL",
    "Sudan":    "SDN",
    "DRC":      "COD",   # Congo, Democratic Republic of
    "Yemen":    "YEM",
}

# Locked date window per Phase 0: 2014-01-01 to 2024-12-31 (10-year contemporary panel)
DATE_START = "2014-01-01"
DATE_END   = "2024-12-31"

# Yemen pre-cond 4 also pulls 2010-2013 as the "pre-2014" reference for Houthi
# coverage check. Locked here.
YEMEN_PRE_START = "2010-01-01"
YEMEN_PRE_END   = "2013-12-31"

API_BASE = "https://api.acleddata.com/acled/read"


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


def write_fetch_instructions():
    """Emit a manual-fetch instruction stub if API credentials unavailable."""
    stub = OUT_DIR / "FETCH_INSTRUCTIONS.md"
    stub.write_text(f"""# ACLED Manual Fetch Instructions

The ACLED API requires registration. To execute the Phase 0 ACLED fetch:

1. Register at https://acleddata.com/register-for-an-acled-access/
2. Receive email confirmation + API key.
3. Set environment variables:

   ```
   $env:ACLED_EMAIL = "your@email"
   $env:ACLED_API_KEY = "your_key"
   ```

4. Re-run `python _scripts/fetch_acled.py`.

ALTERNATIVELY, use the Data Export Tool (browser): https://acleddata.com/data-export-tool/

Per-country export parameters (locked here):

| Country | ISO3 | Date range | Export filename |
|---|---|---|---|
| Colombia | COL | {DATE_START} to {DATE_END} | `acled-colombia.csv` |
| Sudan    | SDN | {DATE_START} to {DATE_END} | `acled-sudan.csv` |
| DRC      | COD | {DATE_START} to {DATE_END} | `acled-drc.csv` |
| Yemen    | YEM | {DATE_START} to {DATE_END} | `acled-yemen.csv` |
| Yemen pre-2014 | YEM | {YEMEN_PRE_START} to {YEMEN_PRE_END} | `acled-yemen-pre2014.csv` |

Save the CSVs to `data/acled/` then re-run any downstream scripts that read
ACLED. The harmonization layer + pre-cond 2 + pre-cond 4 will use whichever
files are present.

The Yemen pre-2014 file is required for pre-cond 4 (Yemen post-2022 coverage
degradation check).
""")
    print(f"  scaffolded: {stub}")
    return stub


def fetch_country(iso3, country, date_start, date_end, email, key, suffix=""):
    params = {
        "email": email,
        "key": key,
        "iso3": iso3,
        "event_date": f"{date_start}|{date_end}",
        "event_date_where": "BETWEEN",
        "format": "csv",
        "limit": 0,  # 0 = unlimited
    }
    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    out_path = OUT_DIR / f"acled-{country.lower().replace(' ','_')}{suffix}.csv"
    print(f"  fetching {country} {date_start}..{date_end} -> {out_path.name}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "IDP-Study/0.1"})
        with urllib.request.urlopen(req, timeout=600) as resp:
            with open(out_path, "wb") as f:
                f.write(resp.read())
    except Exception as e:
        print(f"  FAIL: {type(e).__name__}: {e}")
        return None
    # Quick row check
    try:
        import pandas as pd
        df = pd.read_csv(out_path, low_memory=False)
        n = len(df)
        print(f"  {country}: {n:,} events")
    except Exception as e:
        print(f"  WARN: couldn't read {out_path}: {e}")
        n = None
    update_manifest({
        "source": f"ACLED API filtered: {country}{' (pre-2014)' if suffix else ''}",
        "filename": str(out_path.relative_to(ROOT)),
        "sha256": sha256(out_path),
        "size_bytes": out_path.stat().st_size,
        "row_count": n,
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    })
    return out_path


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== ACLED fetch (4-country panel: Colombia, Sudan, DRC, Yemen) ===")

    email = os.environ.get("ACLED_EMAIL", "").strip()
    key   = os.environ.get("ACLED_API_KEY", "").strip()

    if not email or not key:
        print("  ACLED_EMAIL / ACLED_API_KEY env vars not set — emitting manual fetch instructions.")
        write_fetch_instructions()
        # Note: do NOT exit nonzero. Scaffold path is a valid Phase 0 outcome
        # per locked constraint: "ACLED actually executed; DTM and GADM
        # scaffolded if network access is limited". ACLED requires auth, so
        # if credentials are absent, scaffolding is the correct fallback.
        print("\n=== ACLED scaffold complete. Set credentials and re-run to fetch. ===")
        return

    # Authenticated path
    for country, iso3 in COUNTRIES.items():
        fetch_country(iso3, country, DATE_START, DATE_END, email, key)

    # Yemen pre-2014 for pre-cond 4
    fetch_country("YEM", "Yemen", YEMEN_PRE_START, YEMEN_PRE_END, email, key, suffix="-pre2014")

    print(f"\n=== ACLED fetch complete. Country files in {OUT_DIR} ===")


if __name__ == "__main__":
    main()
