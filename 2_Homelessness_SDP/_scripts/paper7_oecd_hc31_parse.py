"""
Paper 7 — OECD HC3.1 Homeless Population PDF parse.
Reconciles measurement methodology (PRE_REG_027 third triple-outlier condition).
"""
from __future__ import annotations
import json
import re
from pathlib import Path

import pdfplumber  # noqa: F401

PDF = Path(r"D:/IDP/data/paper7/oecd_housing/HC3-1-Homeless-population.pdf")
OUT_JSON = Path(r"D:/IDP/analysis/paper7_oecd_hc31_2026_05_27.json")
OUT_DIG = Path(
    r"D:/IDP/papers/PAPER_7_SDP_FRAMEWORK/digs/2026_05_27_oecd_hc31_parse.md"
)


def extract_text(pdf_path: Path) -> str:
    chunks: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            chunks.append(txt)
    return "\n\n--- PAGE BREAK ---\n\n".join(chunks)


def extract_tables(pdf_path: Path):
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            for tbl in page.extract_tables():
                tables.append({"page": i + 1, "rows": tbl})
    return tables


def main() -> None:
    raw = extract_text(PDF)
    tables = extract_tables(PDF)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(
            {
                "n_pages": raw.count("--- PAGE BREAK ---") + 1,
                "n_tables": len(tables),
                "text_first_3000": raw[:3000],
                "text_last_3000": raw[-3000:],
                "tables": tables,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    print(f"[hc31] pages={raw.count('--- PAGE BREAK ---') + 1} tables={len(tables)}")
    # Look for OECD country names + numeric homelessness rows
    countries = [
        "Australia", "Austria", "Belgium", "Canada", "Chile", "Colombia",
        "Costa Rica", "Czechia", "Denmark", "Estonia", "Finland", "France",
        "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Israel",
        "Italy", "Japan", "Korea", "Latvia", "Lithuania", "Luxembourg",
        "Mexico", "Netherlands", "New Zealand", "Norway", "Poland",
        "Portugal", "Slovak", "Slovenia", "Spain", "Sweden", "Switzerland",
        "Türkiye", "Turkey", "United Kingdom", "United States",
    ]
    summary: dict[str, list[str]] = {}
    for c in countries:
        # Capture each line containing the country name (the PDF lays out
        # country data row-by-row).
        hits = []
        for line in raw.splitlines():
            if c in line:
                hits.append(line.strip())
        if hits:
            summary[c] = hits[:5]  # cap
    OUT_JSON_S = OUT_JSON.with_suffix(".country_lines.json")
    OUT_JSON_S.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[hc31] countries with hits: {len(summary)}; wrote {OUT_JSON_S}")
    print("[hc31] DONE")


if __name__ == "__main__":
    main()
