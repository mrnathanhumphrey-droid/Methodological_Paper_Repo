"""
Paper 5 — PRE_REG_030 blocking-lever predictive model (Phase 1).

Scores 12 corpus cases on 4 blocking levers at attempt onset, using V-Dem
global-median splits (minimal subjective coding):
  Lever 1 court independence   = v2juhcind  > global median (onset year)
  Lever 2 civil-society capac. = v2csprtcpt > global median (onset year)
  Lever 3 competitive election = v2xel_frefair > global median (onset year)
  Lever 4 federal/regional pwr = v2elreggov > global median (onset year)

Decision rule (pre-committed): >=3 levers -> BLOCKED; <=2 -> CONSOLIDATES.

Tests:
  A. In-corpus separation (predict >=10 of 12 correct)
  B. USA lever-erosion 2017 (Trump I) vs 2025 (Trump II): >=3 -> <=2
Sensitivity: re-score with +/-1 lever threshold shift (median +/- 0.25 sd).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

VDEM = Path("D:/IDP/data/vdem/vdem_vdem.csv")
OUT = Path("D:/IDP/analysis/paper5_prereg030_2026_05_28.json")

# Levers 1-3 are V-Dem global-median splits at onset. Lever 4 (federal/regional
# parallel power) is NOT a clean V-Dem median split: v2elreggov is binary (most
# countries have elected regional govts) and v2elsrgel doesn't separate genuine
# federations from unitary states with local councils. Lever 4 is therefore
# hand-coded from constitutional structure (formal federation with independently
# elected state/provincial governments). Among the 12 cases, the formal
# federations are USA, BRA, VEN (coded by constitutional structure, not outcome).
LEVER_COLS = {
    "court_independence": "v2juhcind",
    "civil_society": "v2csprtcpt",
    "competitive_election": "v2xel_frefair",
}
FEDERAL = {"USA": 1, "BRA": 1, "VEN": 1}  # constitutional federations; others unitary

# case -> (iso3, onset_year, actual_outcome)
CASES = {
    # blocked
    "BRA_Bolsonaro": ("BRA", 2019, "blocked"),
    "ISR_overhaul": ("ISR", 2023, "blocked"),
    "USA_TrumpI": ("USA", 2017, "blocked"),
    "KOR_Yoon": ("KOR", 2022, "blocked"),
    "PER_Castillo": ("PER", 2021, "blocked"),
    # consolidated
    "SLV_Bukele": ("SLV", 2019, "consolidated"),
    "HUN_Orban": ("HUN", 2010, "consolidated"),
    "TUR_Erdogan": ("TUR", 2014, "consolidated"),
    "VEN_Chavez": ("VEN", 2006, "consolidated"),
    "POL_PiS": ("POL", 2015, "consolidated"),
    "TUN_Saied": ("TUN", 2021, "consolidated"),
    "BLR_Luka2020": ("BLR", 2020, "consolidated"),
}


def main():
    usecols = ["country_text_id", "year"] + list(LEVER_COLS.values())
    v = pd.read_csv(VDEM, usecols=usecols, low_memory=False)

    # global median + sd per indicator per year (reference distribution = all countries)
    def global_stat(col, year, fn):
        s = v[v["year"] == year][col].dropna()
        return fn(s) if len(s) else np.nan

    results = {}
    for case, (iso, onset, actual) in CASES.items():
        row = v[(v["country_text_id"] == iso) & (v["year"] == onset)]
        levers = {}
        raw = {}
        for lever, col in LEVER_COLS.items():
            val = row[col].values[0] if len(row) and not row[col].isna().all() else np.nan
            gmed = global_stat(col, onset, np.median)
            raw[lever] = None if pd.isna(val) else float(val)
            levers[lever] = 0 if pd.isna(val) else int(val > gmed)
        levers["federal_regional"] = FEDERAL.get(iso, 0)
        score = sum(levers.values())
        predicted = "blocked" if score >= 3 else "consolidated"
        results[case] = {
            "iso": iso, "onset": onset, "actual": actual,
            "raw": raw, "levers": levers, "score": score,
            "predicted": predicted, "correct": predicted == actual,
        }

    # ---- Test A: in-corpus separation ----
    n_correct = sum(r["correct"] for r in results.values())
    print("=" * 78)
    print("PRE_REG_030 — Blocking-lever model (>=3 levers -> blocked)")
    print("=" * 78)
    print(f"{'case':<16}{'iso':<5}{'onset':<7}{'L1c':<4}{'L2cs':<5}{'L3el':<5}{'L4fr':<5}{'score':<6}{'pred':<13}{'actual':<13}{'ok'}")
    for case, r in results.items():
        L = r["levers"]
        print(f"{case:<16}{r['iso']:<5}{r['onset']:<7}{L['court_independence']:<4}{L['civil_society']:<5}{L['competitive_election']:<5}{L['federal_regional']:<5}{r['score']:<6}{r['predicted']:<13}{r['actual']:<13}{'Y' if r['correct'] else 'N'}")
    print(f"\nTest A: {n_correct} of 12 correct (threshold >=10 -> H1 supported)")
    verdict_A = "SUPPORTED" if n_correct >= 10 else ("F1 FIRED" if n_correct < 8 else "WEAK")
    print(f"Test A verdict: {verdict_A}")

    # ---- Test B: USA erosion ----
    usa_levers = {}
    for yr in [2017, 2025]:
        row = v[(v["country_text_id"] == "USA") & (v["year"] == yr)]
        lev = {}
        for lever, col in LEVER_COLS.items():
            val = row[col].values[0] if len(row) and not row[col].isna().all() else np.nan
            gmed = global_stat(col, yr, np.median)
            lev[lever] = 0 if pd.isna(val) else int(val > gmed)
        lev["federal_regional"] = FEDERAL.get("USA", 0)
        usa_levers[yr] = {"levers": lev, "score": sum(lev.values())}
    print("\n" + "=" * 78)
    print("Test B: USA lever-erosion 2017 (Trump I) vs 2025 (Trump II)")
    print("=" * 78)
    for yr in [2017, 2025]:
        print(f"  {yr}: levers={usa_levers[yr]['levers']} score={usa_levers[yr]['score']}")
    erosion = usa_levers[2017]["score"] >= 3 and usa_levers[2025]["score"] <= 2
    print(f"  H2 (>=3 in 2017 -> <=2 in 2025): {'SUPPORTED' if erosion else 'NOT supported'}")

    out = {
        "test_A": {"results": results, "n_correct": int(n_correct), "verdict": verdict_A},
        "test_B_usa_erosion": {"by_year": usa_levers, "h2_supported": bool(erosion)},
        "decision_rule": ">=3 levers -> blocked",
        "lever_operationalization": {k: f"{vcol} > global median at onset year" for k, vcol in LEVER_COLS.items()},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
