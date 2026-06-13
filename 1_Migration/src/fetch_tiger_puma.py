"""
Pull Census TIGER/Line PUMA shapefiles and PUMA equivalency files for
both vintages relevant to PRE_REG v1.0 §2.2 / §2.5:
  - 2010-vintage PUMAs (TIGER 2019): used by ACS 2012-2021
  - 2020-vintage PUMAs (TIGER 2023): used by ACS 2022-2023

Also pulls the 2010 PUMA Equivalency files (PUMSEQ10_{FIPS}.txt) and
the 2020 tract-to-PUMA crosswalk for IRS SOI ↔ IPUMS county-to-PUMA
linkage downstream.

Outputs to D:\\Migration\\data\\raw\\tiger\\
  puma_2010/       — state-level puma10 shapefile zips
  puma_2020/       — state-level puma20 shapefile zips
  equiv_2010/      — PUMSEQ10_{FIPS}.txt files
  equiv_2020/      — tract-to-PUMA 2020 crosswalk

Manifest: D:\\Migration\\data\\raw\\tiger\\MANIFEST.tsv
Log:      D:\\Migration\\logs\\fetch_tiger_{ts}.log
"""
from __future__ import annotations
import hashlib
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser

OUT_BASE = Path(r"D:\Migration\data\raw\tiger")
LOG_DIR = Path(r"D:\Migration\logs")
MANIFEST = OUT_BASE / "MANIFEST.tsv"
UA = "Mozilla/5.0 (research download; contact: mr.nathanhumphrey@gmail.com)"

DIRS = [
    ("https://www2.census.gov/geo/tiger/TIGER2019/PUMA/",
     OUT_BASE / "puma_2010", r"\.zip$"),
    ("https://www2.census.gov/geo/tiger/TIGER2023/PUMA/",
     OUT_BASE / "puma_2020", r"\.zip$"),
    ("https://www2.census.gov/geo/docs/reference/puma/",
     OUT_BASE / "equiv_2010", r"^PUMSEQ10_\d+\.txt$"),
    ("https://www2.census.gov/geo/docs/reference/puma2020/",
     OUT_BASE / "equiv_2020", r"_to_2020_PUMA\.txt$"),
]


class HrefCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for k, v in attrs:
                if k == "href":
                    self.hrefs.append(v)


def list_dir(url: str) -> list[str]:
    req = Request(url, headers={"User-Agent": UA})
    for i in range(1, 5):
        try:
            with urlopen(req, timeout=30) as r:
                html = r.read().decode("utf-8", errors="replace")
            p = HrefCollector()
            p.feed(html)
            return p.hrefs
        except (URLError, HTTPError) as e:
            wait = 5 * i
            print(f"  list_dir retry {i} after {wait}s: {e}")
            time.sleep(wait)
    raise RuntimeError(f"list_dir failed after retries: {url}")


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, dest: Path, log) -> tuple[str, int, str]:
    if dest.exists() and dest.stat().st_size > 0:
        size = dest.stat().st_size
        digest = sha256_of(dest)
        log.write(f"SKIP\t{url}\t{size}\t{digest}\n")
        return "skipped", size, digest
    req = Request(url, headers={"User-Agent": UA})
    for i in range(1, 5):
        try:
            with urlopen(req, timeout=120) as resp:
                data = resp.read()
            dest.write_bytes(data)
            size = len(data)
            digest = sha256_of(dest)
            log.write(f"OK\t{url}\t{size}\t{digest}\n")
            return "downloaded", size, digest
        except (URLError, HTTPError) as e:
            wait = 5 * i
            log.write(f"RETRY{i}\t{url}\t{e}\twait={wait}s\n")
            time.sleep(wait)
    log.write(f"FAIL\t{url}\n")
    return "failed", 0, ""


def main():
    import re
    OUT_BASE.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"fetch_tiger_{ts}.log"

    rows = []
    with log_path.open("w", encoding="utf-8") as log:
        log.write(f"# fetch_tiger run {ts}\n")
        for cat_idx, (src_url, dest_dir, pat) in enumerate(DIRS):
            dest_dir.mkdir(parents=True, exist_ok=True)
            if cat_idx > 0:
                time.sleep(10)  # cool-down between categories so Census doesn't 403
            try:
                hrefs = list_dir(src_url)
            except Exception as e:
                log.write(f"DIR_FAIL\t{src_url}\t{e}\n")
                print(f"DIR_FAIL {src_url}: {e}")
                continue
            files = [h for h in hrefs if re.search(pat, h)]
            print(f"\n[{dest_dir.name}] {len(files)} files from {src_url}")
            for fname in files:
                url = src_url.rstrip("/") + "/" + fname
                dest = dest_dir / fname.split("/")[-1]
                status, size, digest = fetch(url, dest, log)
                rows.append((str(dest.relative_to(OUT_BASE)), dest_dir.name,
                             status, size, digest))
                print(f"  {status:11s} {dest.name:<30s} {size:>10d} bytes")

    header = "filepath\tcategory\tstatus\tbytes\tsha256\n"
    with MANIFEST.open("w", encoding="utf-8") as m:
        m.write(header)
        for r in rows:
            m.write("\t".join(str(x) for x in r) + "\n")

    n_ok = sum(1 for _, _, s, _, _ in rows if s in ("downloaded", "skipped"))
    n_fail = sum(1 for _, _, s, _, _ in rows if s == "failed")
    total = sum(b for _, _, _, b, _ in rows)
    print(f"\n{n_ok}/{len(rows)} files in place, {n_fail} failed, {total/1e6:.1f} MB total")
    print(f"Manifest: {MANIFEST}")
    print(f"Log:      {log_path}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
