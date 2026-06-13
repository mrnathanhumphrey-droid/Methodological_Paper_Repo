"""Build longitudinal IDP panels from DTM data (defensive harmonization).

This is the riskiest piece in Phase 0 per locked constraint:

  "DTM schema drift is real. Different rounds have different columns. The
   harmonization layer must be defensive: log every column rename, every
   type coercion, every missing-value fill. Output a
   data/dtm/_harmonization_log.json per country."

This script reads raw DTM round files per country, applies country-specific
schema-drift rules, and produces a clean longitudinal panel at admin-2 ×
year resolution.

Per Phase 0 lock:
  - Phase 0 scaffold of harmonization rules + log structure
  - Phase 2 execution: actually run against fetched DTM files

The harmonization rule book is committed at Phase 0 so any deviation
between rule and execution is logged + auditable.

Usage:
  python build_longitudinal_panel.py {country}    # 'colombia', 'sudan', 'drc', 'yemen'
  python build_longitudinal_panel.py --all
  python build_longitudinal_panel.py --schema-only    # emit rule book without running
"""
import pathlib, sys, json, time, io, argparse
import warnings; warnings.filterwarnings("ignore")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
except Exception:
    pass
import numpy as np
import pandas as pd

ROOT = pathlib.Path(r"D:/IDP")
DTM_DIR = ROOT / "data" / "dtm"


# Per-country harmonization rule book. Phase 0 LOCKS this. Any change after
# Phase 0 must be logged in _harmonization_log.json with a `rule_change`
# entry pointing to the commit hash that introduces the change.
HARMONIZATION_RULES = {
    "colombia": {
        "primary_source": "Unidad para las Víctimas (RUV)",
        "admin_level": "Municipio",
        "join_column_candidates": ["municipio", "Municipio", "MPIO_CCNCT", "DIVIPOLA"],
        "outcome_column_candidates": ["desplazados", "DESPLAZADOS", "idps", "victimas_desplazadas"],
        "year_column_candidates": ["year", "anio", "vigencia"],
        "expected_schema_drift": [
            "RUV switched format around 2018 — pre-2018 files have different column names",
            "Multiple aggregation levels in same file (departmental + municipal); filter to admin-2 only",
        ],
        "notes": "Primary source is NOT IOM DTM (minimal Colombia presence). RUV is the canonical IDP registration.",
    },
    "sudan": {
        "primary_source": "IOM DTM Sudan Round-by-Round",
        "admin_level": "Locality (mahaliya)",
        "join_column_candidates": ["locality", "Locality", "Admin 2", "admin2", "Admin2_Name", "Admin 2 Name", "mahaliya"],
        "outcome_column_candidates": ["IDP Individuals", "idp_individuals", "Number of IDPs", "n_idps", "Total IDPs"],
        "year_column_candidates": ["year", "Year", "Round Date", "Assessment Date"],
        "expected_schema_drift": [
            "Round-by-Round column renames between rounds (typically Q1 vs Q3 format changes)",
            "Pre-2023 vs post-2023 (post-RSF-war) major schema change expected",
            "Some rounds report Households not Individuals; need conversion factor (HH × 5)",
            "South Sudan rounds may be in same file pre-2011 — filter Sudan-only",
        ],
        "notes": "Post-April-2023 RSF-SAF war: DTM coverage may be partial in RSF-controlled areas. Flag in panel.",
    },
    "drc": {
        "primary_source": "IOM DTM DRC monthly provincial reports",
        "admin_level": "Territoire",
        "join_column_candidates": ["territoire", "Territoire", "Admin 2", "admin2", "Territory", "Zone"],
        "outcome_column_candidates": ["pdi_total", "PDI Total", "idps", "Number of IDPs", "personnes_deplacees_internes"],
        "year_column_candidates": ["year", "Year", "annee", "date"],
        "expected_schema_drift": [
            "Pre-2018 reports are PDF-only; CSV exports only available 2018-forward",
            "Province-level rolls up territoire-level; need to disaggregate",
            "Eastern DRC (Nord-Kivu, Sud-Kivu, Ituri) reported more frequently than west",
            "M23 cycles (2022-present) create reporting bursts; flag round-frequency irregularity",
        ],
        "notes": "Use 2024 INS population estimates for denominators; 1984 census is 40yr stale. Flag uncertainty.",
    },
    "yemen": {
        "primary_source": "IOM DTM Yemen Master List + Area Assessments",
        "admin_level": "Mudīriyah (district)",
        "join_column_candidates": ["district", "District", "Admin 2", "admin2", "mudiriyah", "Mudiriyah"],
        "outcome_column_candidates": ["IDP Individuals", "idp_individuals", "Number of IDPs", "n_idps", "Total IDPs", "HH Number"],
        "year_column_candidates": ["year", "Year", "Round", "Assessment Year"],
        "expected_schema_drift": [
            "Governorate-level vs district-level resolution varies by round",
            "Post-2022 Houthi-controlled governorate coverage degraded (pre-cond 4)",
            "Master List vs Area Assessments are different products; Master List is district-granular",
            "Some rounds report HH only; convert HH × 6 (Yemen HH-size avg) or HH × locked factor",
        ],
        "notes": "Pre-cond 4 determines whether post-2022 Yemen data enters Stage B panel. Document, don't fight it.",
    },
}


def emit_schema_only():
    """Emit the harmonization rule book as schema_rulebook.json. Phase 0 deliverable."""
    out = DTM_DIR / "schema_rulebook.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "0.1.0-phase0",
        "locked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "rule_book": HARMONIZATION_RULES,
        "lock_note": (
            "This rule book is locked at Phase 0 initial commit. Any change "
            "during Phase 2 execution must be logged in the country's "
            "_harmonization_log.json under a `rule_change` entry pointing to "
            "the introducing commit hash. Substantive changes (e.g., a new "
            "outcome column candidate that materially changes a country's "
            "IDP estimate) trigger a pre_reg_redline.md v1->v2 entry."
        ),
    }
    out.write_text(json.dumps(payload, indent=2))
    print(f"=== harmonization rule book emitted: {out} ===")


def harmonize_country(country):
    """Phase 2 execution path. In Phase 0 this is a no-op stub if no raw files."""
    rules = HARMONIZATION_RULES.get(country)
    if rules is None:
        print(f"FAIL: no rule book for country '{country}'", file=sys.stderr)
        sys.exit(2)
    country_dir = DTM_DIR / country
    country_dir.mkdir(parents=True, exist_ok=True)
    log = {
        "country": country,
        "primary_source": rules["primary_source"],
        "phase": "phase0_scaffold",
        "rule_book_version": "0.1.0-phase0",
        "ran_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "raw_files_found": [],
        "column_renames": [],
        "type_coercions": [],
        "missing_fills": [],
        "rule_changes": [],
        "notes": [],
    }
    raw_files = sorted([p for p in country_dir.glob("*") if p.is_file() and p.suffix in (".xlsx", ".xls", ".csv")])
    log["raw_files_found"] = [p.name for p in raw_files]
    if not raw_files:
        log["notes"].append("Phase 0: no raw DTM files present. Phase 2 will fetch then re-run harmonization.")
        log_path = country_dir / "_harmonization_log.json"
        log_path.write_text(json.dumps(log, indent=2))
        print(f"  [{country}] Phase 0 stub log written: {log_path}")
        return

    # If raw files exist, attempt harmonization (Phase 2 path)
    # Implementation note: this block runs in Phase 2. Phase 0 should not have raw files.
    log["notes"].append(f"Phase 2 path: {len(raw_files)} raw files present. Running harmonization.")
    # TODO Phase 2: implement full harmonization with renames/coercions/fills logged.
    # For now (Phase 0), just record file inventory.
    log_path = country_dir / "_harmonization_log.json"
    log_path.write_text(json.dumps(log, indent=2))
    print(f"  [{country}] harmonization log written: {log_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("country", nargs="?", default=None, choices=[None, "colombia","sudan","drc","yemen","all"])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--schema-only", action="store_true")
    args = ap.parse_args()

    emit_schema_only()

    if args.schema_only:
        return

    if args.all or args.country == "all":
        for c in HARMONIZATION_RULES.keys():
            harmonize_country(c)
    elif args.country:
        harmonize_country(args.country)
    else:
        # Default Phase 0: run scaffold for all 4 countries
        for c in HARMONIZATION_RULES.keys():
            harmonize_country(c)


if __name__ == "__main__":
    main()
