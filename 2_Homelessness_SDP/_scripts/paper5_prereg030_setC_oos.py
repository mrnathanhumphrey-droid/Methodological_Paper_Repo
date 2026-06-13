"""
Paper 5 — PRE_REG_030 Prediction set C (out-of-sample lever scoring).

Scores current democracies NOT in the original 12-case corpus on the 4 blocking
levers at a recent year (2024 = latest stable V-Dem), using the SAME locked
operationalization as Test A:
  L1 court        = v2juhcind   > global median (2024)
  L2 civil-soc    = v2csprtcpt  > global median (2024)
  L3 competitive  = v2xel_frefair > global median (2024)
  L4 federal      = constitutional federation (hand-coded)

Decision rule (locked): >=3 levers -> PROTECTED; <=2 -> AT-RISK.

This is a forward-looking classification, falsifiable as these countries'
trajectories unfold. No outcomes assigned (they haven't happened yet).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

VDEM = Path("D:/IDP/data/vdem/vdem_vdem.csv")
OUT = Path("D:/IDP/analysis/paper5_prereg030_setC_2026_05_28.json")
SCORE_YEAR = 2024

LEVER_COLS = {
    "court_independence": "v2juhcind",
    "civil_society": "v2csprtcpt",
    "competitive_election": "v2xel_frefair",
}
FEDERAL = {"IND", "MEX", "ARG", "DEU", "USA", "BRA", "AUS", "CAN", "CHE", "NGA"}

# Current democracies / at-risk cases of policy interest (not in original 12).
# note = brief contemporary backsliding-watch context (for the writeup only).
CASES = {
    "IND": "Modi/BJP — widely flagged backsliding",
    "MEX": "Morena 2024 supermajority + judicial reform",
    "GEO": "Georgian Dream — foreign-agent law, EU accession frozen",
    "IDN": "Prabowo 2024",
    "PHL": "Marcos/Duterte",
    "ZAF": "ANC decline, GNU 2024",
    "ITA": "Meloni",
    "ARG": "Milei",
    "DEU": "control (stable)",
    "FRA": "control (semi-presidential)",
    "GRC": "control",
    "ESP": "control",
}


def main():
    usecols = ["country_text_id", "year"] + list(LEVER_COLS.values())
    v = pd.read_csv(VDEM, usecols=usecols, low_memory=False)

    def gmed(col, year):
        s = v[v["year"] == year][col].dropna()
        return float(np.median(s)) if len(s) else np.nan

    medians = {col: gmed(col, SCORE_YEAR) for col in LEVER_COLS.values()}

    results = {}
    for iso, note in CASES.items():
        row = v[(v["country_text_id"] == iso) & (v["year"] == SCORE_YEAR)]
        levers, raw = {}, {}
        for lever, col in LEVER_COLS.items():
            val = row[col].values[0] if len(row) and not row[col].isna().all() else np.nan
            raw[lever] = None if pd.isna(val) else float(val)
            levers[lever] = 0 if pd.isna(val) else int(val > medians[col])
        levers["federal_regional"] = int(iso in FEDERAL)
        score = sum(levers.values())
        results[iso] = {
            "note": note, "raw": raw, "levers": levers, "score": score,
            "classification": "protected" if score >= 3 else "at-risk",
        }

    print("=" * 88)
    print(f"PRE_REG_030 Set C — out-of-sample lever scoring at {SCORE_YEAR} (>=3 protected, <=2 at-risk)")
    print("=" * 88)
    print(f"global medians {SCORE_YEAR}: " + ", ".join(f"{k.split('_')[0]}={v:.2f}" for k, v in
          {"court": medians['v2juhcind'], "civsoc": medians['v2csprtcpt'], "elect": medians['v2xel_frefair']}.items()))
    print(f"\n{'iso':<5}{'L1c':<4}{'L2cs':<5}{'L3el':<5}{'L4fr':<5}{'score':<6}{'class':<11}note")
    for iso, r in results.items():
        L = r["levers"]
        print(f"{iso:<5}{L['court_independence']:<4}{L['civil_society']:<5}{L['competitive_election']:<5}{L['federal_regional']:<5}{r['score']:<6}{r['classification']:<11}{r['note']}")

    at_risk = [iso for iso, r in results.items() if r["classification"] == "at-risk"]
    protected = [iso for iso, r in results.items() if r["classification"] == "protected"]
    print(f"\nAT-RISK (<=2 levers): {at_risk}")
    print(f"PROTECTED (>=3 levers): {protected}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "score_year": SCORE_YEAR, "global_medians": medians,
        "results": results, "at_risk": at_risk, "protected": protected,
    }, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
