"""
Paper 9 Phase 1 - Parse EOIR FY2024 asylum decisions by nationality.
Source: justice.gov/eoir/media/1344846/dl?inline (PDF).
Outputs P9-origin asylum-decision counts: grants, denials, abandonment, other,
withdrawn, not_adjudicated. * = privacy-suppressed (count < 4).
"""
from __future__ import annotations
import re, sys
from pathlib import Path
import pdfplumber
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

PDF = Path("D:/IDP/data/paper9/eoir/raw/eoir_asylum_decisions_by_nationality.pdf")
OUT = Path("D:/IDP/data/paper9/eoir/eoir_fy2024_asylum_by_nationality.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

# Map EOIR nationality strings to canonical P9 names
EOIR_TO_P9 = {
    "AFGHANISTAN": "Afghanistan",
    "BURMA (MYANMAR)": "Myanmar",
    "CUBA": "Cuba",
    "DEMOCRATIC REPUBLIC OF CONGO": "DRC",
    "EL SALVADOR": "El Salvador",
    "ERITREA": "Eritrea",
    "GUATEMALA": "Guatemala",
    "HAITI": "Haiti",
    "HONDURAS": "Honduras",
    "IRAQ": "Iraq",
    "SOMALIA": "Somalia",
    "SUDAN": "Sudan",
    "SYRIA": "Syria",
    "UKRAINE": "Ukraine",
    "VENEZUELA": "Venezuela",
}


def parse_value(s: str) -> int:
    """Parse number cell; * means suppressed (<4), treat as 2 (midpoint of 0-3)."""
    s = s.strip().replace(",", "")
    if s == "*":
        return 2
    try:
        return int(s)
    except ValueError:
        return 0


def main():
    text = ""
    with pdfplumber.open(PDF) as pdf:
        for p in pdf.pages:
            text += (p.extract_text() or "") + "\n"

    # Each P9 country line: NAME grants denials abandon other withdrawn not_adjudicated
    # Some names span 2 lines (e.g., "DEMOCRATIC REPUBLIC OF CONGO" has the data on its
    # own line). Handle multi-line headers via continuation detection.
    rows = []
    lines = text.splitlines()
    for eoir_name, p9_name in EOIR_TO_P9.items():
        # Search for the line that ends with this name, or starts with it
        toks = eoir_name.split()
        first_token = toks[0]
        for i, line in enumerate(lines):
            line_s = line.strip()
            # Two patterns: (a) "NAME val val val val val val" all on one line,
            # (b) NAME continuation -- multi-line, with data on the line after.
            if line_s.upper().startswith(eoir_name):
                # Data immediately follows on same line
                remainder = line_s[len(eoir_name):].strip()
                vals = remainder.split()
                if len(vals) >= 6:
                    rows.append({
                        "origin": p9_name,
                        "grants": parse_value(vals[0]),
                        "denials": parse_value(vals[1]),
                        "abandonment": parse_value(vals[2]),
                        "other": parse_value(vals[3]),
                        "withdrawn": parse_value(vals[4]),
                        "not_adjudicated": parse_value(vals[5]),
                    })
                    break
            elif line_s.upper() == eoir_name and i+1 < len(lines):
                # Look at NEXT line for data
                next_line = lines[i+1].strip()
                vals = next_line.split()
                if len(vals) >= 6 and all(v == "*" or v.replace(",","").isdigit() for v in vals[:6]):
                    rows.append({
                        "origin": p9_name,
                        "grants": parse_value(vals[0]),
                        "denials": parse_value(vals[1]),
                        "abandonment": parse_value(vals[2]),
                        "other": parse_value(vals[3]),
                        "withdrawn": parse_value(vals[4]),
                        "not_adjudicated": parse_value(vals[5]),
                    })
                    break
            elif line_s.upper().endswith(eoir_name.split()[0]) and i+1 < len(lines):
                # split header: first part of country name ends line, rest on next
                pass

    # DRC: PDF splits "DEMOCRATIC" / data / "REPUBLIC OF CONGO" across 3 lines —
    # manual entry from verified PDF page-2 line: "DEMOCRATIC ... 95 59 20 139 * 4 ... REPUBLIC OF CONGO"
    if "DRC" not in {r["origin"] for r in rows}:
        rows.append({"origin":"DRC","grants":95,"denials":59,"abandonment":20,"other":139,"withdrawn":2,"not_adjudicated":4})

    df = pd.DataFrame(rows)
    df["total_decisions"] = df[["grants","denials","abandonment","other","withdrawn","not_adjudicated"]].sum(axis=1)
    df.to_csv(OUT, index=False)
    print(f"EOIR FY2024 asylum decisions, P9 origins:")
    print(df.to_string(index=False))
    print(f"\nSaved -> {OUT}")
    print(f"P9 origins covered: {len(df)} / 15")
    missing = set(EOIR_TO_P9.values()) - set(df["origin"])
    if missing:
        print(f"MISSING: {missing}")


if __name__ == "__main__":
    main()
