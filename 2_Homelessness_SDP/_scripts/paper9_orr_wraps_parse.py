"""
Paper 9 Phase 1 - Parse WRAPS refugee arrivals reports into long-format
(state x nationality x FY x count).

Excel files (FY2018-2020): hierarchical state-then-nationality layout, forward-fill state.
PDF files (FY2021-2026): line-based; "STATE Total" rows then nationality rows; last number on each line = FY grand total.

Output: D:/IDP/data/paper9/orr_wraps/wraps_arrivals_by_state_nationality_FY_long.csv
"""
from __future__ import annotations
import re, sys
from pathlib import Path
import pandas as pd
import pdfplumber

sys.stdout.reconfigure(encoding="utf-8")

RAW = Path("D:/IDP/data/paper9/orr_wraps/raw")
OUT = Path("D:/IDP/data/paper9/orr_wraps")

# State name normalization
STATES = {
    "Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut","Delaware",
    "District of Columbia","Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa",
    "Kansas","Kentucky","Louisiana","Maine","Maryland","Massachusetts","Michigan","Minnesota",
    "Mississippi","Missouri","Montana","Nebraska","Nevada","New Hampshire","New Jersey",
    "New Mexico","New York","North Carolina","North Dakota","Ohio","Oklahoma","Oregon",
    "Pennsylvania","Rhode Island","South Carolina","South Dakota","Tennessee","Texas",
    "Utah","Vermont","Virginia","Washington","West Virginia","Wisconsin","Wyoming",
    "Puerto Rico","Guam","US Virgin Islands","American Samoa","Northern Mariana Islands",
}

# Nationality name normalization (PDF truncations + variants -> canonical)
NAT_CANON = {
    "Dem. Rep. Congo": "DRC",
    "Dem. Rep. Con..": "DRC",
    "Democratic Republic of Congo": "DRC",
    "Congo, Democratic Republic": "DRC",
    "Republic of Sou..": "South Sudan",
    "Republic of South Sudan": "South Sudan",
    "Central African..": "Central African Republic",
    "Burma": "Myanmar",  # treat Burma == Myanmar
    "United Arab Emir..": "United Arab Emirates",
    "Russian Federa..": "Russia",
}

# Map any nationality string to canonical via prefix-match for truncations
def norm_nat(n: str) -> str:
    n = n.strip().rstrip(".").strip()
    if not n:
        return n
    if n in NAT_CANON:
        return NAT_CANON[n]
    # try prefix-match resolution
    for trunc, canon in NAT_CANON.items():
        if trunc.endswith(".") and n.startswith(trunc.rstrip(".")):
            return canon
    return n


# -----------------------------------------------------------------------------
# Excel parser (FY2018-2020)
# -----------------------------------------------------------------------------

def parse_excel(fp: Path, fy: str) -> pd.DataFrame:
    df = pd.read_excel(fp, sheet_name=0, header=None, engine="xlrd" if fp.suffix == ".xls" else "openpyxl")
    # find the data start: row containing "Placement State" or "Affiliate State"
    start = None
    for i in range(len(df)):
        if df.iloc[i, 0] and isinstance(df.iloc[i, 0], str) and any(
            k in df.iloc[i, 0] for k in ("Placement State", "Affiliate State", "State Name")
        ):
            start = i + 1
            break
    if start is None:
        # fallback: find first row where col 0 is a state name
        for i in range(len(df)):
            v = df.iloc[i, 0]
            if isinstance(v, str) and v.strip() in STATES:
                start = i
                break
    if start is None:
        raise ValueError(f"Could not locate data start in {fp.name}")

    rows = []
    cur_state = None
    for i in range(start, len(df)):
        v0 = df.iloc[i, 0]
        v1 = df.iloc[i, 1]
        v2 = df.iloc[i, 2]
        # State-total row: col0=state, col1=NaN, col2=number
        if isinstance(v0, str) and v0.strip() in STATES:
            cur_state = v0.strip()
            continue
        # Nationality row: col0=NaN, col1=nationality, col2=number
        if cur_state and isinstance(v1, str) and v1.strip() and pd.notna(v2):
            try:
                n = int(v2)
                rows.append((fy, cur_state, norm_nat(v1.strip()), n))
            except (ValueError, TypeError):
                pass
        # Stop at "Total" or footer
        if isinstance(v0, str) and v0.strip().lower() == "total":
            break

    return pd.DataFrame(rows, columns=["fy", "state", "nationality", "arrivals"])


# -----------------------------------------------------------------------------
# PDF parser (FY2021-2026)
# -----------------------------------------------------------------------------

# Pre-build "STATE Total" prefix lookup
STATE_TOTAL_PREFIXES = {f"{s} Total": s for s in STATES}

# Token regex: a number is digits with optional commas
NUM_RE = re.compile(r"^[0-9][0-9,]*$")
# Lines we definitely skip
SKIP_TOKENS = (
    "Refugee Arrivals", "Affiliate State", "Grand Total",
    "Department of State", "Bureau of", "Office of",
    "Placement State", "Data as of", "Single FY", "By Department",
    "Data provided", "Doe et a", "settlement in",
    "Fiscal Year ", "All Nationalities",
    "through September", "through April", "through October", "through March",
    "through November", "through December", "through January", "through February",
    "through May", "through June", "through July", "through August",
    "October 1,", "Actual Destin", "Actual Destination",
)


def label_is_plausible_nationality(label: str) -> bool:
    """A nationality label must be all alphabetic words (no embedded digits / years)."""
    if not label:
        return False
    if not any(ch.isalpha() for ch in label[:3]):
        return False
    # Reject anything with digits embedded (date fragments, etc.)
    if any(ch.isdigit() for ch in label):
        return False
    return True


def split_label_and_last_number(line: str):
    """Return (label, last_number_int) or (None, None). Last token must be a number."""
    toks = line.split()
    if not toks:
        return None, None
    if not NUM_RE.match(toks[-1]):
        return None, None
    last_num = int(toks[-1].replace(",", ""))
    # Walk backwards to find where the label ends (first non-number token from the right)
    end_label_idx = len(toks) - 1
    while end_label_idx > 0 and NUM_RE.match(toks[end_label_idx - 1]):
        end_label_idx -= 1
    label = " ".join(toks[:end_label_idx])
    return label.strip(), last_num


def parse_pdf(fp: Path, fy: str) -> pd.DataFrame:
    """Layout A: "STATE Total" rows then nationality rows (FY2021-2023)."""
    rows = []
    cur_state = None
    with pdfplumber.open(fp) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            for line in txt.splitlines():
                line = line.strip()
                if not line:
                    continue
                if any(s in line for s in SKIP_TOKENS):
                    continue
                label, count = split_label_and_last_number(line)
                if label is None:
                    continue
                # STATE Total row
                if label in STATE_TOTAL_PREFIXES:
                    cur_state = STATE_TOTAL_PREFIXES[label]
                    continue
                if label.endswith(" Total"):
                    cand = label[:-len(" Total")].strip()
                    if cand in STATES:
                        cur_state = cand
                        continue
                # Nationality row
                if cur_state and label and any(ch.isalpha() for ch in label):
                    nat = norm_nat(label)
                    if nat and any(ch.isalpha() for ch in nat[:3]):
                        rows.append((fy, cur_state, nat, count))
    return pd.DataFrame(rows, columns=["fy", "state", "nationality", "arrivals"])


def parse_pdf_inline_state(fp: Path, fy: str) -> pd.DataFrame:
    """Layout B: state name as first token on each state-block's first row;
    subsequent rows in same block are nationality-only. No "STATE Total" anchor.
    Used by FY2025+ format.
    """
    rows = []
    cur_state = None
    with pdfplumber.open(fp) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            for line in txt.splitlines():
                line = line.strip()
                if not line:
                    continue
                if any(s in line for s in SKIP_TOKENS):
                    continue
                label, count = split_label_and_last_number(line)
                if label is None:
                    continue
                # Check if this line starts with a state name (possibly multi-word)
                state_match = None
                for s in STATES:
                    if label.startswith(s + " ") or label == s:
                        state_match = s
                        break
                if state_match:
                    cur_state = state_match
                    # The rest of the label after the state is the nationality
                    nat_part = label[len(state_match):].strip()
                    if nat_part:
                        nat = norm_nat(nat_part)
                        if label_is_plausible_nationality(nat):
                            rows.append((fy, cur_state, nat, count))
                    continue
                # No state prefix → nationality-only row under current state
                if cur_state and label:
                    nat = norm_nat(label)
                    if label_is_plausible_nationality(nat):
                        rows.append((fy, cur_state, nat, count))
    return pd.DataFrame(rows, columns=["fy", "state", "nationality", "arrivals"])


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

# (fy, filename, layout): layout = "excel" | "pdf_state_total" | "pdf_inline_state"
FILES = [
    ("FY2018", "fy2018_arrivals_by_state_nationality.xls", "excel"),
    ("FY2019", "fy2019_arrivals_by_state_nationality.xlsx", "excel"),
    ("FY2020", "fy2020_arrivals_by_state_nationality.xlsx", "excel"),
    ("FY2021", "fy2021_arrivals_by_state_nationality.pdf", "pdf_state_total"),
    ("FY2022", "fy2022_arrivals_by_state_nationality.pdf", "pdf_state_total"),  # partial — pages 2-19 rasterized
    ("FY2023", "fy2023_arrivals_by_state_nationality.pdf", "pdf_state_total"),
    ("FY2024", "fy2024_arrivals_by_state_nationality.pdf", "pdf_state_total"),  # full file cid-encoded — skip
    ("FY2025", "fy2025_arrivals_by_state_nationality.pdf", "pdf_inline_state"),
    ("FY2026_partial", "fy2026_partial_arrivals_by_state_nationality.pdf", "pdf_state_total"),  # partial period Oct-Apr
]


def main():
    frames = []
    for fy, fname, layout in FILES:
        fp = RAW / fname
        if not fp.exists():
            print(f"  {fy}: MISSING {fname}")
            continue
        try:
            if layout == "excel":
                d = parse_excel(fp, fy)
            elif layout == "pdf_inline_state":
                d = parse_pdf_inline_state(fp, fy)
            else:
                d = parse_pdf(fp, fy)
        except Exception as e:
            print(f"  {fy}: PARSE-FAIL {type(e).__name__} {str(e)[:200]}")
            continue
        n_states = d["state"].nunique()
        n_nats = d["nationality"].nunique()
        n_rows = len(d)
        total = d["arrivals"].sum()
        print(f"  {fy}: {n_rows:>4} rows, {n_states} states, {n_nats} nationalities, {total:>6} total arrivals")
        frames.append(d)

    if not frames:
        print("No data parsed."); return

    full = pd.concat(frames, ignore_index=True)
    out = OUT / "wraps_arrivals_by_state_nationality_FY_long.csv"
    full.to_csv(out, index=False)
    print(f"\nSaved {len(full):,} rows -> {out}")

    # Summary: arrivals by FY
    print("\n=== Total arrivals by FY ===")
    print(full.groupby("fy")["arrivals"].sum().to_string())

    # P9 origin coverage
    P9 = ["Ukraine","Venezuela","Cuba","Honduras","El Salvador","Guatemala","Haiti",
          "Afghanistan","Syria","Iraq","Myanmar","DRC","Eritrea","Somalia","Sudan"]
    p9 = full[full["nationality"].isin(P9)]
    print(f"\n=== P9-origin arrivals by FY (15 origins; refugee track only) ===")
    pivot = p9.pivot_table(index="nationality", columns="fy", values="arrivals", aggfunc="sum", fill_value=0)
    print(pivot.to_string())


if __name__ == "__main__":
    main()
