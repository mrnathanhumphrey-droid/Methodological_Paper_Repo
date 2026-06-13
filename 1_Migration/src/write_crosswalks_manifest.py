"""
Scan D:\\Migration\\data\\raw\\crosswalks\\ and write MANIFEST.tsv with
SHA256 + byte-count for each crosswalk file.

Per PRE_REG v1.0 §3.1 hashing discipline: this manifest is the integrity
record for crosswalk inputs, parallel to data/raw/{ipums,irs_soi,tiger}/MANIFEST.tsv.

Idempotent: rewrites MANIFEST.tsv from current disk state each run.
"""
from __future__ import annotations
import hashlib
import sys
from datetime import datetime
from pathlib import Path

XWALK_DIR = Path(r"D:\Migration\data\raw\crosswalks")
MANIFEST = XWALK_DIR / "MANIFEST.tsv"


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if not XWALK_DIR.exists():
        print(f"ERROR: {XWALK_DIR} does not exist; nothing to manifest")
        return 1

    files = sorted(p for p in XWALK_DIR.iterdir()
                   if p.is_file() and p.name != "MANIFEST.tsv")
    if not files:
        print(f"No files to manifest in {XWALK_DIR}")
        return 0

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows = []
    print(f"Hashing {len(files)} files...")
    for f in files:
        size = f.stat().st_size
        digest = sha256_of(f)
        rows.append((f.name, size, digest, ts))
        print(f"  {f.name:<50s} {size:>12d}  {digest[:12]}...")

    header = "filename\tbytes\tsha256\thashed_at\n"
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
