"""
Paper 9 Phase 1 - parse the FY2024 OCR text + merge into WRAPS long-format.

Reuses the line-based STATE-Total layout parser (same as FY2021-2023 layout).
Appends FY2024 rows to the WRAPS canonical CSV.
"""
from __future__ import annotations
import re, sys
from pathlib import Path
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

OCR_TXT = Path("D:/IDP/data/paper9/orr_wraps/raw/fy2024_ocr_text.txt")
WRAPS_CSV = Path("D:/IDP/data/paper9/orr_wraps/wraps_arrivals_by_state_nationality_FY_long.csv")

STATES = {
    "Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut","Delaware",
    "District of Columbia","Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa",
    "Kansas","Kentucky","Louisiana","Maine","Maryland","Massachusetts","Michigan","Minnesota",
    "Mississippi","Missouri","Montana","Nebraska","Nevada","New Hampshire","New Jersey",
    "New Mexico","New York","North Carolina","North Dakota","Ohio","Oklahoma","Oregon",
    "Pennsylvania","Rhode Island","South Carolina","South Dakota","Tennessee","Texas",
    "Utah","Vermont","Virginia","Washington","West Virginia","Wisconsin","Wyoming",
    "Puerto Rico","Guam",
}
STATE_TOTAL_PREFIXES = {f"{s} Total": s for s in STATES}

NAT_CANON = {
    "Dem. Rep. Congo": "DRC", "Dem. Rep. Con..": "DRC",
    "Democratic Republic of Congo": "DRC", "Congo, Democratic Republic": "DRC",
    "Republic of South Sudan": "South Sudan", "Republic of Sou..": "South Sudan",
    "Central African Republic": "Central African Republic", "Central African..": "Central African Republic",
    "Burma": "Myanmar",
    "United Arab Emirates": "United Arab Emirates", "United Arab Emir..": "United Arab Emirates",
    "Russian Federa..": "Russia",
}

NUM_RE = re.compile(r"^[0-9][0-9,]*$")
SKIP_TOKENS = (
    "Refugee Arrivals", "Affiliate State", "Grand Total",
    "Department of State", "Bureau of", "Office of",
    "Placement State", "Data as of", "Single FY", "By Department",
    "Data provided", "Doe et a", "settlement in",
    "Fiscal Year ", "All Nationalities",
    "through September", "October 1,", "Actual Destin", "Actual Destination",
    "=== PAGE",
)


def norm_nat(n: str) -> str:
    n = n.strip().rstrip(".").strip()
    if not n: return n
    if n in NAT_CANON: return NAT_CANON[n]
    return n


def label_is_plausible_nationality(label: str) -> bool:
    if not label: return False
    if not any(ch.isalpha() for ch in label[:3]): return False
    if any(ch.isdigit() for ch in label): return False
    return True


def split_label_and_last_number(line: str):
    toks = line.split()
    if not toks: return None, None
    if not NUM_RE.match(toks[-1]): return None, None
    last_num = int(toks[-1].replace(",", ""))
    end_label_idx = len(toks) - 1
    while end_label_idx > 0 and NUM_RE.match(toks[end_label_idx - 1]):
        end_label_idx -= 1
    return " ".join(toks[:end_label_idx]).strip(), last_num


def parse_ocr(text: str, fy: str) -> pd.DataFrame:
    rows = []
    cur_state = None
    for line in text.splitlines():
        line = line.strip()
        if not line: continue
        if any(s in line for s in SKIP_TOKENS): continue
        label, count = split_label_and_last_number(line)
        if label is None: continue
        if label in STATE_TOTAL_PREFIXES:
            cur_state = STATE_TOTAL_PREFIXES[label]
            continue
        if label.endswith(" Total"):
            cand = label[:-len(" Total")].strip()
            if cand in STATES:
                cur_state = cand
                continue
        if cur_state and label and any(ch.isalpha() for ch in label):
            nat = norm_nat(label)
            if label_is_plausible_nationality(nat):
                rows.append((fy, cur_state, nat, count))
    return pd.DataFrame(rows, columns=["fy","state","nationality","arrivals"])


def main():
    text = OCR_TXT.read_text(encoding="utf-8")
    fy24 = parse_ocr(text, "FY2024")
    print(f"FY2024 parsed: {len(fy24)} rows, {fy24['state'].nunique()} states, "
          f"{fy24['nationality'].nunique()} nationalities, {fy24['arrivals'].sum()} total")

    # Compare with published grand total ~100,034
    print(f"  vs published grand total ~100,034 (diff {fy24['arrivals'].sum() - 100034:+d})")

    # P9-origin pivot
    P9 = ["Ukraine","Venezuela","Cuba","Honduras","El Salvador","Guatemala","Haiti",
          "Afghanistan","Syria","Iraq","Myanmar","DRC","Eritrea","Somalia","Sudan"]
    p9_rows = fy24[fy24["nationality"].isin(P9)]
    print(f"\nP9-origin FY2024 totals:")
    print(p9_rows.groupby("nationality")["arrivals"].sum().sort_values(ascending=False).to_string())

    # Merge into WRAPS canonical
    wraps = pd.read_csv(WRAPS_CSV)
    # Drop any pre-existing FY2024 rows (parser had 0 anyway)
    wraps_no24 = wraps[wraps["fy"] != "FY2024"]
    merged = pd.concat([wraps_no24, fy24], ignore_index=True)
    merged.to_csv(WRAPS_CSV, index=False)
    print(f"\nMerged FY2024 OCR rows. WRAPS CSV now {len(merged):,} rows.")
    print("\nFY-level totals after merge:")
    print(merged.groupby("fy")["arrivals"].sum().to_string())


if __name__ == "__main__":
    main()
