"""
Scan D:\\Migration\\data\\raw\\ipums\\ and write MANIFEST.tsv with
SHA256, byte-count, and (when available) IPUMS extract metadata.

Standalone — safe to run after any IPUMS download, including ones from
prior sessions. Idempotent: rewrites MANIFEST.tsv from current disk state
each run, so deleting a file and re-running shrinks the manifest.

Per PRE_REG v1.0 §3.1 hashing discipline: this manifest is the integrity
record for IPUMS raw data, parallel to data/raw/irs_soi/MANIFEST.tsv.
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

IPUMS_DIR = Path(r"D:\Migration\data\raw\ipums")
MANIFEST = IPUMS_DIR / "MANIFEST.tsv"
STATE = IPUMS_DIR / "extract_state.json"  # written by submit script, optional


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def main():
    if not IPUMS_DIR.exists():
        print(f"ERROR: {IPUMS_DIR} does not exist; nothing to manifest")
        return 1

    files = sorted(p for p in IPUMS_DIR.iterdir()
                   if p.is_file() and p.name not in ("MANIFEST.tsv", "extract_state.json"))
    if not files:
        print(f"No files to manifest in {IPUMS_DIR}")
        return 0

    state = load_state()
    extract_id = state.get("extract_id", "")
    collection = state.get("collection", "usa")
    api_version = state.get("api_version", "")
    submitted_at = state.get("submitted_at", "")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows = []
    print(f"Hashing {len(files)} files...")
    for f in files:
        size = f.stat().st_size
        digest = sha256_of(f)
        rows.append((f.name, size, digest, extract_id, collection, api_version,
                     submitted_at, ts))
        print(f"  {f.name:<40s} {size:>12d}  {digest[:12]}...")

    header = ("filename\tbytes\tsha256\tipums_extract_id\tipums_collection\t"
              "ipums_api_version\tsubmitted_at\thashed_at\n")
    with MANIFEST.open("w", encoding="utf-8") as m:
        m.write(header)
        for r in rows:
            m.write("\t".join(str(x) for x in r) + "\n")

    total = sum(r[1] for r in rows)
    print(f"\n{len(rows)} files, {total/1e6:.1f} MB total")
    print(f"Manifest: {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
