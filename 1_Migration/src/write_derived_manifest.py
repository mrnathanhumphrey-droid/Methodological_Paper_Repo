"""
Scan D:\\Migration\\data\\derived\\ and write MANIFEST.tsv with
SHA256 + byte-count for each derived artifact (parquet + json sidecars).

Per PRE_REG v1.0 §3.1 hashing discipline: extends the raw-data hashing
record to the derived layer. Note: P0_partition.parquet is *also* anchored
by prereg/P0_hash.txt (the pre-registration freeze). This MANIFEST is the
working integrity record for ALL derived artifacts and should be regenerated
each time a derived parquet is rebuilt.

If P0_partition.parquet's sha256 here ever diverges from prereg/P0_hash.txt,
the latter is the canonical pre-reg anchor and the discrepancy is a finding.

Idempotent: rewrites MANIFEST.tsv from current disk state each run.
"""
from __future__ import annotations
import hashlib
import sys
from datetime import datetime
from pathlib import Path

DERIVED_DIR = Path(r"D:\Migration\data\derived")
MANIFEST = DERIVED_DIR / "MANIFEST.tsv"
P0_HASH_FILE = Path(r"D:\Migration\prereg\P0_hash.txt")


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_p0_anchor() -> str | None:
    """Return the sha256 from the most recent ---block--- in P0_hash.txt, or None."""
    if not P0_HASH_FILE.exists():
        return None
    last = None
    for line in P0_HASH_FILE.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("sha256:"):
            last = s.split(":", 1)[1].strip()
    return last


def main():
    if not DERIVED_DIR.exists():
        print(f"ERROR: {DERIVED_DIR} does not exist; nothing to manifest")
        return 1

    files = sorted(p for p in DERIVED_DIR.iterdir()
                   if p.is_file() and p.name != "MANIFEST.tsv")
    if not files:
        print(f"No files to manifest in {DERIVED_DIR}")
        return 0

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    p0_anchor = read_p0_anchor()

    rows = []
    print(f"Hashing {len(files)} files...")
    p0_status = "n/a"
    for f in files:
        size = f.stat().st_size
        digest = sha256_of(f)
        kind = f.suffix.lstrip(".") or "file"
        anchor_match = ""
        if f.name == "P0_partition.parquet":
            if p0_anchor is None:
                anchor_match = "no_anchor"
                p0_status = "no anchor in prereg/P0_hash.txt"
            elif digest == p0_anchor:
                anchor_match = "matches_prereg"
                p0_status = f"MATCH (prereg sha256 {p0_anchor[:12]}...)"
            else:
                anchor_match = "MISMATCH_PREREG"
                p0_status = (f"MISMATCH: derived sha256 {digest[:12]}... vs "
                             f"prereg anchor {p0_anchor[:12]}... -- INVESTIGATE")
        rows.append((f.name, kind, size, digest, anchor_match, ts))
        print(f"  {f.name:<42s} {kind:<8s} {size:>12d}  {digest[:12]}...  {anchor_match}")

    header = "filename\tkind\tbytes\tsha256\tprereg_anchor_check\thashed_at\n"
    with MANIFEST.open("w", encoding="utf-8") as m:
        m.write(header)
        for r in rows:
            m.write("\t".join(str(x) for x in r) + "\n")

    total = sum(r[2] for r in rows)
    print(f"\n{len(rows)} files, {total/1e6:.1f} MB total")
    print(f"P0_partition.parquet vs prereg/P0_hash.txt: {p0_status}")
    print(f"Manifest: {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
