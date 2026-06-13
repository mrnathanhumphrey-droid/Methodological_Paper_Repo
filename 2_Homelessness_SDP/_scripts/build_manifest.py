"""Build/refresh manifest.json with SHA-256 of every fetched raw data file.

Phase 0 chain-of-custody: every file under data/ that is a fetched raw
source (csv / gpkg / shp / xlsx / xls / zip / geojson) gets a SHA-256
recorded here for auditability, even though the file itself is
gitignored.
"""
import json, pathlib, hashlib, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "manifest.json"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    m = {
        "study": "Internal Displacement Cross-Country Study (substrate 9)",
        "phase": "Phase 0 — pre-reg lock + data fetch + pre-cond scaffold",
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "lock_commit": "set on initial git commit",
        "files": [],
    }
    fetched = []
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file(): continue
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        if "/.git/" in rel or rel.startswith(".git/") or "__pycache__" in rel: continue
        if not rel.startswith("data/"): continue
        if p.suffix.lower() not in (".csv",".gpkg",".shp",".xlsx",".xls",".zip",".geojson",".json"):
            continue
        try:
            fetched.append({
                "path": rel,
                "sha256": sha256(p),
                "size_bytes": p.stat().st_size,
                "kind": "raw_data_file (gitignored)",
            })
        except Exception as e:
            print(f"WARN: {rel}: {e}")
    m["files"] = fetched
    MANIFEST.write_text(json.dumps(m, indent=2))
    print(f"manifest files: {len(fetched)}")
    print(f"wrote {MANIFEST}")
    for f in fetched[:30]:
        print(f"  {f['path']:<60}  {f['size_bytes']:>12,} bytes  {f['sha256'][:16]}...")


if __name__ == "__main__":
    main()
