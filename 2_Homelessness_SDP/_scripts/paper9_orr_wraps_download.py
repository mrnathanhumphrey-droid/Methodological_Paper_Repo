"""
Paper 9 Phase 1 - Pull ORR / WRAPS refugee arrivals by state x nationality x FY.

Sources: Refugee Processing Center (rpc.state.gov), official Department of State
Worldwide Refugee Admissions Processing System (WRAPS) reports.

FY2018-FY2020: Excel (.xls/.xlsx) - machine readable directly.
FY2021-FY2025 + FY2026-partial: PDF - needs table extraction (pdfplumber).
"""
from __future__ import annotations
import os, sys, time, urllib.request
from pathlib import Path
from urllib.parse import quote

sys.stdout.reconfigure(encoding="utf-8")

OUT_DIR = Path("D:/IDP/data/paper9/orr_wraps/raw")
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE = "https://www.rpc.state.gov"

# (fiscal_year, url_path, local_filename) - locked from archive listing 2026-05-30
FILES = [
    ("FY2018",
     "/documents/Archives/FY 2018 Arrivals by State and Nationality.xls",
     "fy2018_arrivals_by_state_nationality.xls"),
    ("FY2019",
     "/documents/Archives/FY 2019 Arrivals by State and Nationality.xlsx",
     "fy2019_arrivals_by_state_nationality.xlsx"),
    ("FY2020",
     "/documents/Archives/FY 2020 Arrivals by State and Nationality.xlsx",
     "fy2020_arrivals_by_state_nationality.xlsx"),
    ("FY2021",
     "/documents/FY 2021 Arrivals by State and Nationality as of 30 Sep 2021.pdf",
     "fy2021_arrivals_by_state_nationality.pdf"),
    ("FY2022",
     "/documents/FY 2022 Arrivals by State and Nationality as of 30 Sep 2022.pdf",
     "fy2022_arrivals_by_state_nationality.pdf"),
    ("FY2023",
     "/documents/FY 2023 Refugee Arrivals by State and Nationality as of 30 Sep 2023.pdf",
     "fy2023_arrivals_by_state_nationality.pdf"),
    ("FY2024",
     "/documents/FY 2024 Arrivals by State and Nationality as of 30 Oct 2024_updated.pdf",
     "fy2024_arrivals_by_state_nationality.pdf"),
    ("FY2025",
     "/documents/FY 2025 Arrivals by State and Nationality as of 30 Sep 2025.pdf",
     "fy2025_arrivals_by_state_nationality.pdf"),
    ("FY2026_partial",
     "/documents/Refugee Arrivals by State and Nationality as of April 30, 2026.pdf",
     "fy2026_partial_arrivals_by_state_nationality.pdf"),
]


def download(path: str, dest: Path):
    # quote() the path-component to URL-encode spaces and commas, but keep slashes
    url = BASE + quote(path, safe="/,")
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 IDP-Paper9-Research (academic, mr.nathanhumphrey@gmail.com)",
            "Accept": "*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    dest.write_bytes(data)
    return len(data)


def main():
    print(f"Downloading {len(FILES)} RPC/WRAPS reports to {OUT_DIR}")
    total = 0
    for fy, path, fname in FILES:
        dest = OUT_DIR / fname
        if dest.exists() and dest.stat().st_size > 1000:
            print(f"  {fy}: SKIP ({dest.stat().st_size/1e3:.1f} KB exists)")
            continue
        try:
            n = download(path, dest)
            total += n
            print(f"  {fy}: {n/1e3:.1f} KB -> {fname}")
        except Exception as e:
            print(f"  {fy}: FAIL {type(e).__name__} {str(e)[:120]}")
        time.sleep(0.5)  # be polite
    print(f"\nTotal downloaded: {total/1e6:.2f} MB")


if __name__ == "__main__":
    main()
