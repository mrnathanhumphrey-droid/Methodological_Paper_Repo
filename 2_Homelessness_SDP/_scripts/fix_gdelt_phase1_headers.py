"""One-shot: rewrite first line of each Phase 1 GDELT CSV with correct
58-column GDELT 1.0 header. Original fetch wrote a 61-col header over
58-col data (3 ADM2Code columns inserted in error per GDELT 2.0 schema
which doesn't apply to GDELT 1.0).

Streams the file to avoid loading the full 644MB into memory.
"""
import pathlib, sys, io, shutil, hashlib, json, time
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
except Exception:
    pass

ROOT = pathlib.Path(r"D:/IDP")
GDELT_DIR = ROOT / "data" / "gdelt"
MANIFEST = ROOT / "manifest.json"

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
assert len(HEADER_COLS) == 58

NEW_HEADER = "\t".join(HEADER_COLS) + "\n"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def fix(path):
    print(f"  {path.name}: streaming rewrite ...")
    tmp = path.with_suffix(".csv.tmp")
    with open(path, "rb") as fin, open(tmp, "wb") as fout:
        # Drop original (wrong) header
        fin.readline()
        # Write new (correct) header
        fout.write(NEW_HEADER.encode("utf-8"))
        # Stream rest of file in 4MB chunks
        while True:
            buf = fin.read(4 * 1024 * 1024)
            if not buf: break
            fout.write(buf)
    shutil.move(str(tmp), str(path))
    size = path.stat().st_size
    # Count lines for manifest
    n_lines = 0
    with open(path, "rb") as f:
        for _ in f: n_lines += 1
    print(f"    rewrote OK: {size:,} bytes, {n_lines:,} lines")
    return n_lines, size


def main():
    print(f"=== Fixing GDELT Phase 1 CSV headers (61-col -> 58-col) ===")
    countries = ["colombia", "sudan", "drc", "yemen"]
    manifest = {}
    if MANIFEST.exists():
        try: manifest = json.loads(MANIFEST.read_text())
        except: manifest = {}
    for c in countries:
        p = GDELT_DIR / f"gdelt-{c}-2014_2024.csv"
        if not p.exists():
            print(f"  {p.name}: not found; skip")
            continue
        n_rows, size = fix(p)
        # Update manifest sha256 + row count
        for entry in manifest.get("files", []):
            if entry.get("filename", "").endswith(p.name):
                entry["sha256"] = sha256(p)
                entry["size_bytes"] = size
                entry["row_count"] = n_rows - 1  # excluding header
                entry["fetched_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                entry["note"] = "Header repaired 2026-05-18 (61-col -> 58-col GDELT 1.0)"
                break
    manifest["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    MANIFEST.write_text(json.dumps(manifest, indent=2))
    print(f"\n  manifest SHA-256s + row counts updated")


if __name__ == "__main__":
    main()
