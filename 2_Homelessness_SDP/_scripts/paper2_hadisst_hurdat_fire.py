"""
Paper 2 — HadISST + HURDAT2 + USA storm-IDP correlation (PRE_REG_015 full fit).

Parses HadISST 1.1 gridded SST format:
- Each year has 12 monthly grids (180 rows × 360 cols).
- Values are SST × 100 (so -180 = -1.80°C, -1000 = land/missing).
- Grid is 1° latitude (89.5N to -89.5N) × 1° longitude (-179.5 to 179.5).

Atlantic Main Development Region (MDR):
- Latitude: 10°N to 20°N → rows ~70 to ~80 (0-indexed)
- Longitude: 20°W to 80°W → cols ~100 to ~160

Compute Aug-Oct mean MDR SST per year, then correlate with USA storm-IDP
from existing P2 corpus.

HURDAT2 ACE:
- Parse atlantic 1851-2025; compute season ACE = sum(v² × 1e-4) over 6-hourly
  observations with max sustained wind ≥ 34 kt.
"""
from __future__ import annotations
import gzip
import io
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

HADISST_DIR = Path(r"D:/IDP/data/hadisst")
HURDAT2_FILE = Path(r"D:/IDP/data/hurdat2/hurdat2-atlantic-1851-2025.txt")
USA_STORM_IDP = Path(
    r"D:/IDP/analysis/paper2_phase1_joined_2026_05_25.parquet"
)
OUT_JSON = Path(
    r"D:/IDP/analysis/paper2_hadisst_hurdat_2026_05_27.json"
)


# MDR rows: latitude 10N to 20N → rows from northern edge
# HadISST row 0 = 89.5N, row 179 = -89.5N
# row r → latitude = 89.5 - r → 10 ≤ 89.5 - r ≤ 20 → 69.5 ≤ r ≤ 79.5
MDR_ROWS = (70, 80)  # half-open
# MDR cols: lon -80 to -20 (west Atlantic to mid-Atlantic basin)
# col c → lon = c - 179.5 → -80 ≤ c - 179.5 ≤ -20 → 99.5 ≤ c ≤ 159.5
MDR_COLS = (100, 160)


def parse_hadisst_file(path: Path):
    """Yield (year, month, 180x360 ndarray) for each monthly grid.

    HadISST 1.1 text header format observed:
        "     1     1  1991   180 rows    360 columns"
    The triple is `month  XX  year` where XX appears to be a count/index;
    we anchor on `180 rows  360 columns` and extract the last 4-digit number
    before it as the year and the first int as the month.
    """
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="latin-1") as f:
        text = f.read()
    header_re = re.compile(r"180\s*rows\s+360\s*columns")
    headers = []
    for m in header_re.finditer(text):
        # Look back from match start to start-of-line for the prefix
        line_start = text.rfind("\n", 0, m.start()) + 1
        prefix = text[line_start:m.start()]
        nums = re.findall(r"\d+", prefix)
        if not nums:
            continue
        ints = [int(n) for n in nums]
        # HadISST text-format prefix: "<series_index> <month> <year>"
        year_candidates = [n for n in ints if 1850 <= n <= 2030]
        if not year_candidates:
            continue
        year = year_candidates[-1]
        # Month is the integer immediately preceding the year in the prefix
        try:
            year_idx = ints.index(year)
            month = ints[year_idx - 1] if year_idx > 0 else 1
        except ValueError:
            month = 1
        if not (1 <= month <= 12):
            month = 1
        # Block start is the next line after the header
        block_pos = text.find("\n", m.end()) + 1
        headers.append((block_pos, m.start(), month, year))
    num_re = re.compile(r"-?\d+")
    for i, (block_pos, header_start, month, year) in enumerate(headers):
        if i + 1 < len(headers):
            next_header_match_start = headers[i + 1][1]
            end = text.rfind("\n", 0, next_header_match_start) + 1
        else:
            end = len(text)
        block = text[block_pos:end]
        nums = num_re.findall(block)
        if len(nums) < 180 * 360:
            continue
        arr = np.array(nums[: 180 * 360], dtype=np.int32).reshape(180, 360)
        yield year, month, arr


def mdr_sst(arr: np.ndarray) -> float:
    block = arr[MDR_ROWS[0]:MDR_ROWS[1], MDR_COLS[0]:MDR_COLS[1]].astype(float)
    # missing/land = -1000; remove
    mask = block > -999
    if mask.sum() == 0:
        return float("nan")
    # SST is stored × 100 (so -180 = -1.80°C)
    return float(block[mask].mean() / 100.0)


def parse_hurdat2_ace(path: Path) -> dict[int, float]:
    """Compute Atlantic seasonal ACE 1851-2025 from HURDAT2.

    HURDAT2 row format (CSV):
      YYYYMMDD, HHMM, RecordID, Status, Lat, Lon, MaxWind, MinPressure, ...
    Storm header lines look like: AL011851,            UNNAMED,     14,
    """
    ace: dict[int, float] = {}
    if not path.exists():
        print(f"[hurdat] file not found: {path}")
        return ace
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            if parts[0].startswith("AL") and len(parts) <= 5:
                continue  # storm header
            if len(parts) < 8:
                continue
            date = parts[0]
            time = parts[1]
            try:
                year = int(date[:4])
                max_wind = int(parts[6])
            except ValueError:
                continue
            # ACE: only synoptic observations (00, 06, 12, 18 UTC), tropical
            # or subtropical status; we approximate via wind ≥ 34 kt and
            # synoptic time. Status field is parts[3].
            if time not in {"0000", "0600", "1200", "1800"}:
                continue
            status = parts[3]
            if status not in {"TS", "HU", "SS", "TY"}:
                continue
            if max_wind < 34:
                continue
            ace[year] = ace.get(year, 0.0) + (max_wind**2) * 1e-4
    return ace


def main() -> None:
    print("[hadisst] parsing files ...")
    # Build year × month × mdr_sst table
    records = []
    files = sorted(HADISST_DIR.glob("HadISST1_SST_*.txt.gz"))
    for fp in files:
        n = 0
        for year, month, arr in parse_hadisst_file(fp):
            sst = mdr_sst(arr)
            records.append({"year": year, "month": month, "mdr_sst_c": sst})
            n += 1
        print(f"[hadisst] {fp.name}: parsed {n} month grids")
    sst = pd.DataFrame(records)
    if sst.empty:
        print("[hadisst] no months parsed -- aborting")
        return
    print(f"[hadisst] total months: {len(sst)} | year range {sst['year'].min()}-{sst['year'].max()}")
    sst.to_csv(
        r"D:/IDP/analysis/paper2_mdr_sst_monthly_2026_05_27.csv", index=False
    )

    # Aug-Oct mean per year
    aug_oct = (
        sst[sst["month"].between(8, 10)]
        .groupby("year", as_index=False)["mdr_sst_c"]
        .mean()
        .rename(columns={"mdr_sst_c": "mdr_sst_aug_oct"})
    )
    print(f"[hadisst] Aug-Oct annual: {len(aug_oct)} years")

    # HURDAT2 ACE
    print(f"[hurdat] parsing {HURDAT2_FILE.name} ...")
    ace_map = parse_hurdat2_ace(HURDAT2_FILE)
    print(f"[hurdat] ACE years: {len(ace_map)} | sample 2017 = {ace_map.get(2017)}")
    ace_df = pd.DataFrame(
        [{"year": y, "ace": v} for y, v in sorted(ace_map.items())]
    )
    ace_df.to_csv(
        r"D:/IDP/analysis/paper2_hurdat_ace_2026_05_27.csv", index=False
    )

    # Join with USA storm-IDP from existing P2 corpus
    correlations: dict[str, dict] = {}
    if USA_STORM_IDP.exists():
        panel = pd.read_parquet(USA_STORM_IDP)
        print(f"[panel] cols = {list(panel.columns)}")
        # Try to extract USA storm rows
        usa_mask = (
            panel.get("iso3", pd.Series(dtype=str)).astype(str).str.upper() == "USA"
        )
        if usa_mask.any():
            usa = panel[usa_mask].copy()
            # Try to find storm-IDP column
            storm_cols = [
                c
                for c in usa.columns
                if ("storm" in c.lower() or "cyclone" in c.lower())
                and ("idp" in c.lower() or "disp" in c.lower() or "affected" in c.lower())
            ]
            year_col = next(
                (c for c in usa.columns if c.lower() in {"year", "yr"}), None
            )
            print(f"[panel] USA rows = {len(usa)} | year_col={year_col} | storm_cols={storm_cols}")
            if year_col and storm_cols:
                for sc in storm_cols:
                    yearly = (
                        usa[[year_col, sc]]
                        .apply(pd.to_numeric, errors="coerce")
                        .dropna()
                        .groupby(year_col, as_index=False)[sc]
                        .sum()
                    )
                    yearly = yearly.rename(columns={year_col: "year", sc: "usa_storm_metric"})
                    merged = yearly.merge(aug_oct, on="year", how="inner").merge(
                        ace_df, on="year", how="inner"
                    )
                    if len(merged) >= 5:
                        r_sst = float(
                            np.corrcoef(
                                merged["usa_storm_metric"], merged["mdr_sst_aug_oct"]
                            )[0, 1]
                        )
                        r_ace = float(
                            np.corrcoef(merged["usa_storm_metric"], merged["ace"])[0, 1]
                        )
                        correlations[sc] = {
                            "r_storm_vs_sst": r_sst,
                            "r_storm_vs_ace": r_ace,
                            "n_years": int(len(merged)),
                        }
                        print(f"[corr] {sc}: r(SST)={r_sst:+.3f} r(ACE)={r_ace:+.3f} n={len(merged)}")
    else:
        print(f"[panel] {USA_STORM_IDP} not found — skipping correlation")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(
            {
                "hadisst_years": (
                    [int(sst["year"].min()), int(sst["year"].max())]
                    if len(sst)
                    else []
                ),
                "n_months_parsed": int(len(sst)),
                "aug_oct_2024_mdr_sst": (
                    float(aug_oct.set_index("year").loc[2024, "mdr_sst_aug_oct"])
                    if 2024 in aug_oct["year"].values
                    else None
                ),
                "aug_oct_2003_mdr_sst": (
                    float(aug_oct.set_index("year").loc[2003, "mdr_sst_aug_oct"])
                    if 2003 in aug_oct["year"].values
                    else None
                ),
                "ace_2017": ace_map.get(2017),
                "ace_2024": ace_map.get(2024),
                "correlations": correlations,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    print(f"[done] wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
