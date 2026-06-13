"""Fetch IOM DTM (Displacement Tracking Matrix) data — SCAFFOLD.

Per Phase 0 locked constraint:
  "DTM and GADM scaffolded if network access is limited"
  "Do not build Stage B fetch scripts beyond stubs that document the
   intended source. Stage B fetch happens in Phase 2."

DTM is country-by-country with significant per-country variation:
  - DTM Colombia: minimal IOM presence; primary IDP data is Unidad de
    Víctimas (registro único)
  - DTM Sudan: IOM DTM Sudan publishes Round-by-Round mobility tracking
    matrices; URL https://dtm.iom.int/sudan
  - DTM DRC: IOM DTM DRC publishes monthly displacement reports per
    province; URL https://dtm.iom.int/democratic-republic-congo
  - DTM Yemen: IOM DTM Yemen publishes Master List + Area Assessments;
    URL https://dtm.iom.int/yemen

The DTM Data Portal (https://dtm.iom.int/data-and-analysis/dtm-api) is the
API endpoint but requires per-country API access. Many DTM products are
distributed as Excel files per round, NOT as a clean longitudinal panel.

Phase 0 scaffold output: data/dtm/FETCH_INSTRUCTIONS.md with per-country
download checklist + schema-drift warning. Phase 2 executes the actual
downloads + builds the panel via build_longitudinal_panel.py.

Per locked constraint: "DTM schema drift is real. Different rounds have
different columns. The harmonization layer must be defensive."
"""
import pathlib, sys, time
ROOT = pathlib.Path(r"D:/IDP")
OUT_DIR = ROOT / "data" / "dtm"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stub = OUT_DIR / "FETCH_INSTRUCTIONS.md"
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    stub.write_text("""# IOM DTM (Displacement Tracking Matrix) Fetch Instructions

**Phase 0 status:** SCAFFOLDED (not yet executed). Phase 2 will execute
country-by-country with the defensive harmonization layer in
`build_longitudinal_panel.py`.

**Critical constraint (Phase 0 lock):** DTM schema drift is real. Different
rounds have different columns. The harmonization layer must be defensive:
log every column rename, every type coercion, every missing-value fill.
Output `data/dtm/_harmonization_log.json` per country.

## Per-country data sources

### Colombia
DTM presence is minimal. Primary IDP data:
- **Unidad para las Víctimas (RUV)** — Registro Único de Víctimas. Census
  of victims of armed conflict including IDPs. URL:
  https://www.unidadvictimas.gov.co/es/registro-unico-de-victimas-ruv/37394
- Provides annual displacement statistics per municipio.
- Alternative: **JIPS-Colombia** (Joint IDP Profiling Service) reports.

### Sudan
DTM Sudan: https://dtm.iom.int/sudan
- Round-by-Round mobility tracking matrices. ~quarterly cadence.
- Published as Excel files. Per-round columns vary.
- Typical columns (some optional per round): admin1 / admin2 / state /
  locality / idp_individuals / arrival_period / location_type.
- **Schema drift to expect:** column renames between rounds (e.g.
  "Locality" -> "Admin 2 Name"); presence of `ssid` / `assessment_round`
  fields varies; population denominators absent in some rounds.

### DRC
DTM DRC: https://dtm.iom.int/democratic-republic-congo
- Monthly provincial reports. PDF + Excel + Tableau.
- Per-territoire (admin-2 equivalent) IDP counts.
- **Schema drift to expect:** PDF tables OCR'd inconsistently across
  reports; CSV exports only available from 2018 forward; pre-2018 data
  is PDF-extract.

### Yemen
DTM Yemen: https://dtm.iom.int/yemen
- Master List + Area Assessments + Mobility Tracking.
- Per-mudiriyah (admin-2) IDP counts + flow.
- **Schema drift to expect:** governorate-level vs district-level
  resolution varies by round; the "Master List" granularity is district;
  Area Assessments are governorate.

## Fetch sequence (Phase 2 execution)

For each country:
  1. Visit DTM country page; download all available round files.
  2. Save raw round files to `data/dtm/<country>/round_NN_raw.xlsx`.
  3. Run `_scripts/build_longitudinal_panel.py <country>` to harmonize.
  4. Inspect `data/dtm/<country>/_harmonization_log.json` for drift warnings.
  5. Output: `data/dtm/<country>/panel_admin2_annual.csv`.

## Pre-cond 1 dependency

Pre-cond 1 (country sample availability) requires that each of the 4
countries has >= 5 years of DTM data with >= 50 admin-2 units per year.
If a country fails pre-cond 1, drop it from primary panel per locked
walk-back protocol (§7).

## Pre-cond 4 dependency (Yemen)

Pre-cond 4 requires Yemen ACLED post-2022 coverage in Houthi-controlled
governorates to be >= 30% of pre-2022 level. If fail, drop Yemen post-2022
from Stage B; keep Stage A historical polygon analysis only. Document;
do not fight it.

## Scaffold last updated

""" + ts + "\n")
    print(f"=== DTM scaffold written: {stub} ===")
    print(f"  Phase 2 executes country-by-country with build_longitudinal_panel.py harmonization.")


if __name__ == "__main__":
    main()
