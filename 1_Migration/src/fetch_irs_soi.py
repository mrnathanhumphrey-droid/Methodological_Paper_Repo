"""
Pull IRS SOI county-to-county migration CSVs for the year-pairs covering
PRE_REG v1.0 §2.3 window (2012-2023 annual time bins).

Idempotent: skips files already present with non-zero size. Writes a
SHA256 + byte-count manifest per file for the data provenance record.

Output: D:\\Migration\\data\\raw\\irs_soi\\
Manifest: D:\\Migration\\data\\raw\\irs_soi\\MANIFEST.tsv
Log:     D:\\Migration\\logs\\fetch_irs_soi_{ts}.log
"""
from __future__ import annotations
import hashlib
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Year-pair codes for tax filing years YYYY1-YYYY2, where time bin t = YYYY2
# Covers PRE_REG v1.0 §2.3 window: 2012 ... 2023 (T = 12)
YEAR_PAIRS = [
    "1112", "1213", "1314", "1415", "1516", "1617",
    "1718", "1819", "1920", "2021", "2122", "2223",
]
BASE = "https://www.irs.gov/pub/irs-soi"
OUT_DIR = Path(r"D:\Migration\data\raw\irs_soi")
LOG_DIR = Path(r"D:\Migration\logs")
MANIFEST = OUT_DIR / "MANIFEST.tsv"
UA = "Mozilla/5.0 (research download; contact: mr.nathanhumphrey@gmail.com)"


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, dest: Path, log) -> tuple[str, int, str]:
    """Returns (status, bytes, sha256). Status in {'downloaded','skipped','failed'}."""
    if dest.exists() and dest.stat().st_size > 0:
        size = dest.stat().st_size
        digest = sha256_of(dest)
        log.write(f"SKIP\t{url}\t{size}\t{digest}\n")
        return "skipped", size, digest
    req = Request(url, headers={"User-Agent": UA})
    attempts = 3
    for i in range(1, attempts + 1):
        try:
            with urlopen(req, timeout=60) as resp:
                data = resp.read()
            dest.write_bytes(data)
            size = len(data)
            digest = sha256_of(dest)
            log.write(f"OK\t{url}\t{size}\t{digest}\n")
            return "downloaded", size, digest
        except (URLError, HTTPError) as e:
            log.write(f"RETRY{i}\t{url}\t{e}\n")
            time.sleep(2 * i)
    log.write(f"FAIL\t{url}\n")
    return "failed", 0, ""


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"fetch_irs_soi_{ts}.log"

    rows = []
    with log_path.open("w") as log:
        log.write(f"# fetch_irs_soi run {ts}\n")
        for yp in YEAR_PAIRS:
            for kind in ("countyinflow", "countyoutflow"):
                fname = f"{kind}{yp}.csv"
                url = f"{BASE}/{fname}"
                dest = OUT_DIR / fname
                status, size, digest = fetch(url, dest, log)
                rows.append((fname, yp, kind, status, size, digest))
                print(f"{status:11s} {fname:24s} {size:>10d} bytes  {digest[:12]}")

    header = "filename\tyear_pair\tkind\tstatus\tbytes\tsha256\n"
    with MANIFEST.open("w") as m:
        m.write(header)
        for r in rows:
            m.write("\t".join(str(x) for x in r) + "\n")

    n_ok = sum(1 for _, _, _, s, _, _ in rows if s in ("downloaded", "skipped"))
    n_fail = sum(1 for _, _, _, s, _, _ in rows if s == "failed")
    total_bytes = sum(b for _, _, _, _, b, _ in rows)
    print(f"\n{n_ok}/{len(rows)} files in place, {n_fail} failed, {total_bytes/1e6:.1f} MB total")
    print(f"Manifest: {MANIFEST}")
    print(f"Log:      {log_path}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
