"""Pre-cond 1 — Country sample availability.

Locked check (§7 of design doc):
  Each of the 4 countries has >= 5 years of DTM data with >= 50 admin-2
  units present per year. Counts only.

Pass: all 4 countries clear.
Fail: drop the failing country from primary panel; rerun with 3 countries
      or pivot to Stage-B-only for the failing country.

Phase 0 status: this script runs against DTM panel files (output of
build_longitudinal_panel.py Phase 2). In Phase 0, if no panel files
present, the script emits a STUB status indicating the check has not
been runnable yet. The script is written and locked at Phase 0 so the
check rule is auditable.
"""
import pathlib, sys, json, time, io
import warnings; warnings.filterwarnings("ignore")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
except Exception:
    pass
import numpy as np
import pandas as pd

ROOT = pathlib.Path(r"D:/IDP")
DTM_DIR = ROOT / "data" / "dtm"
NOTES = ROOT / "notes"
REPORT = NOTES / "precond_1_report.md"

COUNTRIES = ["colombia", "sudan", "drc", "yemen"]
LOCKED_MIN_YEARS = 5
LOCKED_MIN_ADMIN2_PER_YEAR = 50


def check_country(country):
    panel_path = DTM_DIR / country / "panel_admin2_annual.csv"
    if not panel_path.exists():
        return {
            "country": country,
            "panel_present": False,
            "n_years_meeting_threshold": None,
            "verdict": "PHASE0_STUB",
            "note": f"Panel file {panel_path.relative_to(ROOT)} not yet built; Phase 2 will produce it.",
        }
    df = pd.read_csv(panel_path)
    # Locked count rule
    by_year = df.groupby("year")["admin2"].nunique()
    qualifying_years = (by_year >= LOCKED_MIN_ADMIN2_PER_YEAR).sum()
    pass_ = qualifying_years >= LOCKED_MIN_YEARS
    return {
        "country": country,
        "panel_present": True,
        "n_years_total": int(by_year.count()),
        "n_years_meeting_threshold": int(qualifying_years),
        "min_admin2_threshold": LOCKED_MIN_ADMIN2_PER_YEAR,
        "min_years_threshold": LOCKED_MIN_YEARS,
        "verdict": "PASS" if pass_ else "FAIL",
        "admin2_per_year": {int(y): int(n) for y, n in by_year.items()},
    }


def main():
    print(f"=== Pre-cond 1: country sample availability ===")
    print(f"  Locked thresholds: >= {LOCKED_MIN_YEARS} years with >= {LOCKED_MIN_ADMIN2_PER_YEAR} admin-2 units/year")
    results = []
    for c in COUNTRIES:
        r = check_country(c)
        results.append(r)
        print(f"  [{c}] verdict: {r['verdict']}  panel_present={r.get('panel_present')}  qualifying_years={r.get('n_years_meeting_threshold')}")

    all_pass = all(r["verdict"] == "PASS" for r in results)
    all_stub = all(r["verdict"] == "PHASE0_STUB" for r in results)
    overall = "PASS" if all_pass else ("PHASE0_STUB" if all_stub else "FAIL_OR_MIXED")

    # Write report
    md = []
    md.append("# Pre-cond 1 Report — Country Sample Availability\n")
    md.append(f"**Run at:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    md.append(f"**Locked check:** Each country has >= {LOCKED_MIN_YEARS} years of DTM data with >= {LOCKED_MIN_ADMIN2_PER_YEAR} admin-2 units present per year.\n")
    md.append(f"**Overall verdict:** **{overall}**\n")
    md.append("\n## Per-country results\n")
    md.append("| Country | Panel present | Years meeting threshold | Verdict |")
    md.append("|---|---|---|---|")
    for r in results:
        md.append(f"| {r['country']} | {r.get('panel_present')} | {r.get('n_years_meeting_threshold')} | {r['verdict']} |")
    md.append("\n## Failure handling (locked walk-back §7)\n")
    md.append("- Any country FAIL: drop from primary panel; rerun with remaining 3 countries OR pivot to Stage-B-only for the failing country.\n")
    md.append("- PHASE0_STUB results indicate Phase 0 lock-time scaffold; Phase 2 re-runs after DTM panels build.\n")
    REPORT.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\n=== Report: {REPORT} ===")

    # Write JSON for downstream
    NOTES.mkdir(parents=True, exist_ok=True)
    (NOTES / "precond_1_results.json").write_text(json.dumps({
        "overall_verdict": overall,
        "results": results,
        "ran_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }, indent=2))


if __name__ == "__main__":
    main()
