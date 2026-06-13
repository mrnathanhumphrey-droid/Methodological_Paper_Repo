"""Fetch EOSV (Ethnic One-Sided Violence) dataset from UCDP.

EOSV is an extension of UCDP's One-Sided Violence dataset with ethnicity
codings. Published by Eck & Hultman; UCDP maintains.

**Locked constraint:** EOSV ends in 2013. For Sudan, the historical
atrocity-count window is 2003-2010 (cleanly within EOSV coverage). Post-2013
ethnic-targeting events fold into `current_conflict_intensity`, NOT into
atrocity-count. Documented in §3.2 of design doc.

EOSV download URL (UCDP): https://www.pcr.uu.se/research/ucdp/datasets/eosv/

Output: data/eosv/eosv-{version}.csv + manifest entry.
"""
import pathlib, sys, hashlib, json, urllib.request, urllib.error, time, io
import warnings; warnings.filterwarnings("ignore")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
except Exception:
    pass

ROOT = pathlib.Path(r"D:/IDP")
OUT_DIR = ROOT / "data" / "eosv"
MANIFEST = ROOT / "manifest.json"

EOSV_CANDIDATES = [
    "https://ucdp.uu.se/downloads/eosv/eosv-v15-1989-2013.zip",
    "https://ucdp.uu.se/downloads/eosv/eosv151.zip",
]


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


def write_fetch_instructions():
    stub = OUT_DIR / "FETCH_INSTRUCTIONS.md"
    stub.write_text("""# EOSV Manual Fetch Instructions

UCDP EOSV (Ethnic One-Sided Violence) dataset, Eck & Hultman variant.

**Time coverage:** 1989-2013. Per locked constraint: do NOT extend post-2013
into the EOSV atrocity-count covariate. Post-2013 ethnic-targeting events
fold into current_conflict_intensity instead.

## Manual download

1. Visit https://ucdp.uu.se/downloads/eosv/
2. Download the latest EOSV release (typically .zip or .xlsx).
3. Save as `data/eosv/eosv-1989-2013.xlsx` or `.csv`.
4. Re-run dependent scripts.

Alternative: UCDP One-Sided Violence dataset (annualized country-level)
at https://ucdp.uu.se/downloads/index.html#onesided. The georeferenced
event-level data is in UCDP-GED with `type_of_violence = 3` (one-sided).
The locked design doc uses UCDP-GED filtered by type_of_violence=3 as
the operational substitute for EOSV when geocoded events are needed; EOSV
proper is used for ethnic-target coding.
""")
    print(f"  scaffolded: {stub}")
    return stub


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== EOSV fetch ===")
    eosv_zip = OUT_DIR / "eosv-latest.zip"
    if eosv_zip.exists():
        print(f"  [cache] {eosv_zip.name} already present, skipping")
    else:
        for url in EOSV_CANDIDATES:
            print(f"  trying {url} ...")
            if fetch_url(url, eosv_zip):
                print(f"  downloaded {eosv_zip}")
                break
        if not eosv_zip.exists():
            print(f"  EOSV direct URL not accessible — writing fetch instructions.")
            write_fetch_instructions()
            return
    update_manifest({
        "source": "UCDP EOSV (Ethnic One-Sided Violence, 1989-2013)",
        "url": "https://ucdp.uu.se/downloads/eosv/",
        "filename": str(eosv_zip.relative_to(ROOT)),
        "sha256": sha256(eosv_zip),
        "size_bytes": eosv_zip.stat().st_size,
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    })

    # Try to unzip + report contents
    try:
        import zipfile
        with zipfile.ZipFile(eosv_zip) as zf:
            print(f"  EOSV zip contents: {zf.namelist()}")
            zf.extractall(OUT_DIR)
    except Exception as e:
        print(f"  WARN: {e}")
    print(f"\n=== EOSV fetch complete. Files in {OUT_DIR} ===")


if __name__ == "__main__":
    main()
