"""Enumerate + fetch all ICEWS historic + POLECAT files from Harvard Dataverse."""
import json
import pathlib
import time
import urllib.request

BASE = "https://dataverse.harvard.edu/api/access/datafile"
TARGETS = [
    ("D:/IDP/data/icews/dataset_metadata.json", "D:/IDP/data/icews/files"),
    ("D:/IDP/data/polecat/dataset_metadata.json", "D:/IDP/data/polecat/files"),
]

for meta_path, out_dir in TARGETS:
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(meta_path) as f:
        meta = json.load(f)
    files = meta.get("data", {}).get("latestVersion", {}).get("files", [])
    print(f"[{time.strftime('%H:%M:%S')}] {meta_path}: {len(files)} files to fetch")
    for i, f in enumerate(files):
        df = f.get("dataFile", {})
        file_id = df.get("id")
        fname = df.get("filename", f"file_{file_id}")
        target = out / fname
        if target.exists() and target.stat().st_size > 0:
            continue
        url = f"{BASE}/{file_id}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "IDP-Study/1.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                target.write_bytes(resp.read())
            print(f"  [{i+1}/{len(files)}] {fname} ({target.stat().st_size:,} bytes)")
        except Exception as e:
            print(f"  [{i+1}/{len(files)}] FAILED {fname}: {e}")
        time.sleep(0.5)
print(f"[{time.strftime('%H:%M:%S')}] complete")
