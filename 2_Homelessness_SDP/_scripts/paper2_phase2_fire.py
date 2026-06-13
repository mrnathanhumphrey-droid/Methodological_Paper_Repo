"""
Paper 2 Phase 2 — fire P2-B (Regime 6 expansion) + P2-C (Caribbean) + P2-D (South Pacific) + P2-G (Regime 2).
Pre-reg: PRE_REG_017 locked 2026-05-25.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding="utf-8")

GIDD = Path("D:/IDP/data/idmc_gidd/IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx")

print("=" * 80)
print("PAPER 2 PHASE 2 — Regime expansion (PRE_REG_017 locked 2026-05-25)")
print("=" * 80)

g = pd.read_excel(GIDD)
g["idp"] = pd.to_numeric(g["Disaster Internal Displacements"], errors="coerce")
g = g[g["Year"].between(2008, 2024)]
print(f"GIDD rows 2008-2024: {len(g)}")

# Aggregate country x hazard
ch = g.groupby(["ISO3", "Hazard Type"])["idp"].sum().unstack(fill_value=0)
ct = ch.sum(axis=1)

# Classification function — PRE_REG_003 H1 rules
def classify(iso):
    if iso not in ch.index:
        return ("MISSING", 0, {})
    total = ct[iso]
    if total < 100_000:
        return ("DATA-SPARSE", total, {})
    flood = ch.loc[iso, "Flood"] if "Flood" in ch.columns else 0
    storm = ch.loc[iso, "Storm"] if "Storm" in ch.columns else 0
    eq    = ch.loc[iso, "Earthquake"] if "Earthquake" in ch.columns else 0
    drought = ch.loc[iso, "Drought"] if "Drought" in ch.columns else 0
    other = total - (flood + storm + eq + drought)

    flood_pct = 100 * flood / total
    storm_pct = 100 * storm / total
    eq_pct = 100 * eq / total
    drought_pct = 100 * drought / total

    # Flood max/median for Regime 1 detection
    flood_yrs = g[(g["ISO3"]==iso) & (g["Hazard Type"]=="Flood")].groupby("Year")["idp"].sum()
    flood_mm = (flood_yrs.max() / flood_yrs.median()) if len(flood_yrs) > 1 and flood_yrs.median() > 0 else 0
    flood_mega = int((flood_yrs >= 1_000_000).sum())

    # Storm year stats for 3a/3b classification
    storm_yrs = g[(g["ISO3"]==iso) & (g["Hazard Type"]=="Storm")].groupby("Year")["idp"].sum()
    storm_mm = (storm_yrs.max() / storm_yrs.median()) if len(storm_yrs) > 1 and storm_yrs.median() > 0 else 0
    storm_mega = int((storm_yrs >= 1_000_000).sum())
    storm_yrs_count = len(storm_yrs)

    details = {
        "total": total, "flood_pct": flood_pct, "storm_pct": storm_pct,
        "eq_pct": eq_pct, "drought_pct": drought_pct,
        "flood_max_median": flood_mm, "flood_mega": flood_mega,
        "storm_max_median": storm_mm, "storm_mega": storm_mega, "storm_yrs": storm_yrs_count,
    }

    # Apply rules
    # Regime 1: flood max/median > 30x AND flood_mega >= 2 AND storm < 10%
    if flood_mm > 30 and flood_mega >= 2 and storm_pct < 10:
        return ("1 (Bimodal-mega-flood)", total, details)
    # Regime 6: EQ > 60%
    if eq_pct >= 60:
        return ("6 (Earthquake-dominant)", total, details)
    # Regime 3: storm > 70%
    if storm_pct >= 70:
        # Sub-classify 3a vs 3b
        if storm_mm >= 10 and storm_mega <= storm_yrs_count / 3:
            return ("3a (Bimodal-mega-storm)", total, details)
        elif storm_mm < 5 and storm_mega >= 0.8 * storm_yrs_count:
            return ("3b (Perpetual-mega-storm)", total, details)
        elif storm_mm >= 5:
            return ("3a-leaning", total, details)
        else:
            return ("3 (Storm-dominant)", total, details)
    # Regime 2: flood max/median < 5x AND >= 40% of yrs > 1M flood AND flood > 50%
    flood_yrs_count = len(flood_yrs) if len(flood_yrs) > 0 else 0
    if flood_mm < 5 and flood_yrs_count > 0 and flood_mega / flood_yrs_count >= 0.4 and flood_pct >= 50:
        return ("2 (Steady-high-flood)", total, details)
    # Regime 4: mixed (none > 70% but at least 2 hazards meaningful)
    if max(flood_pct, storm_pct, eq_pct) < 70:
        if flood_pct >= 50:
            return ("4a (Flood-leaning mixed)", total, details)
        elif storm_pct >= 50:
            return ("4b (Storm-leaning mixed)", total, details)
        else:
            return ("4c (Balanced mixed)", total, details)
    # Catch-all
    return ("UNCLASSIFIED", total, details)


# Phase 2 candidate lists (with predictions)
panels = {
    "P2-C Caribbean": {
        "JAM": "3", "PRI": "3", "BHS": "3", "TTO": "3", "BRB": "3", "GRD": "3", "LCA": "3",
    },
    "P2-D South Pacific small states": {
        "KIR": "3", "TUV": "3", "WSM": "3", "TON": "3", "NRU": "3", "PLW": "3", "COK": "3",
    },
    "P2-B Regime 6 expansion": {
        "IRN": "6", "GRC": "6", "NZL": "6 or 4", "AFG": "4",
    },
    "P2-G Regime 2 replication": {
        "CHN": "2 or 4", "MMR": "4", "ARG": "4 or 2", "KHM": "2", "THA": "4",
    },
}

results = {}
for panel_name, predictions in panels.items():
    print(f"\n{'=' * 80}")
    print(f"{panel_name}")
    print("=" * 80)
    print(f"{'ISO':<5} {'Total IDP':<14} {'Flood%':<8} {'Storm%':<8} {'EQ%':<8} {'Drought%':<10} {'Actual':<28} {'Predicted':<18} {'Match'}")
    panel_results = []
    for iso, pred in predictions.items():
        regime, total, det = classify(iso)
        if regime in ("MISSING", "DATA-SPARSE"):
            print(f"{iso:<5} {total:<14.0f} {'-':<8} {'-':<8} {'-':<8} {'-':<10} {regime:<28} {pred:<18} -")
            panel_results.append({"iso": iso, "regime": regime, "predicted": pred, "match": "DATA"})
            continue
        # Match logic: extract the leading digit/letter of regime
        actual_main = regime.split(" ")[0].rstrip("ab")[0] if regime[0].isdigit() else regime[0]
        pred_main = pred.split(" ")[0]
        if "or" in pred:
            options = [x.strip() for x in pred.split("or")]
            match = "YES" if any(actual_main == opt[0] for opt in options) else "NO"
        else:
            match = "YES" if actual_main == pred_main[0] else "NO"
        print(f"{iso:<5} {total:<14.0f} {det['flood_pct']:<8.1f} {det['storm_pct']:<8.1f} {det['eq_pct']:<8.1f} {det['drought_pct']:<10.1f} {regime:<28} {pred:<18} {match}")
        panel_results.append({"iso": iso, "regime": regime, "predicted": pred, "match": match, **det})
    results[panel_name] = panel_results
    matched = sum(1 for r in panel_results if r["match"] == "YES")
    data_ok = sum(1 for r in panel_results if r["match"] != "DATA")
    print(f"\nPanel matches: {matched}/{data_ok} (data-valid countries)")

# Summary against falsifiers
print("\n" + "=" * 80)
print("FALSIFIER CHECK (PRE_REG_017)")
print("=" * 80)

# F1: Caribbean failure (>=3 of 7 fit no regime)
carib_unclass = sum(1 for r in results["P2-C Caribbean"] if r["match"] == "DATA" or "UNCLASS" in r["regime"])
carib_data_valid = sum(1 for r in results["P2-C Caribbean"] if r["match"] != "DATA")
carib_matched = sum(1 for r in results["P2-C Caribbean"] if r["match"] == "YES")
print(f"\nF1 (>=3 of 7 Caribbean fit no regime): {carib_unclass} unclassified")
print(f"   Caribbean R3-predicted matches: {carib_matched}/{carib_data_valid} data-valid")
print(f"   Status: {'FIRED' if carib_unclass >= 3 else 'NOT FIRED'}")

# F2: South Pacific data-sparse + non-R3
sp_data_valid = sum(1 for r in results["P2-D South Pacific small states"] if r["match"] != "DATA")
sp_matched = sum(1 for r in results["P2-D South Pacific small states"] if r["match"] == "YES")
sp_non_r3 = sum(1 for r in results["P2-D South Pacific small states"]
                if r["match"] != "DATA" and not r["regime"].startswith("3"))
print(f"\nF2 (>=3 of 7 South Pacific not R3): {sp_non_r3} non-R3 (excluding data-sparse)")
print(f"   South Pacific R3-predicted matches: {sp_matched}/{sp_data_valid} data-valid")
print(f"   Status: {'FIRED' if sp_non_r3 >= 3 else 'NOT FIRED'}")

# F3: Regime 6 0 of 4 confirmed
r6_confirmed = sum(1 for r in results["P2-B Regime 6 expansion"]
                   if r["regime"].startswith("6"))
print(f"\nF3 (0 of 4 Regime 6 confirmed): {r6_confirmed} new R6 confirmed")
print(f"   Status: {'FIRED' if r6_confirmed == 0 else 'NOT FIRED'}")

# F4: Unclassified countries
unclassified = []
for panel, rs in results.items():
    for r in rs:
        if "UNCLASS" in r["regime"]:
            unclassified.append((panel, r["iso"], r["regime"]))
print(f"\nF4 (new regime needed): {len(unclassified)} unclassified countries")
for u in unclassified:
    print(f"   {u}")
print(f"   Status: {'FIRED' if len(unclassified) >= 1 else 'NOT FIRED'}")

# F5: Regime 1 candidates
r1_candidates = []
for panel, rs in results.items():
    for r in rs:
        if r["regime"].startswith("1 ") or r["regime"] == "1":
            r1_candidates.append((panel, r["iso"]))
print(f"\nF5 (>=2 Regime 1 candidates): {len(r1_candidates)} R1 candidates")
print(f"   Status: {'FIRED' if len(r1_candidates) >= 2 else 'NOT FIRED'}")

# ==== Updated typology member count ====
print("\n" + "=" * 80)
print("UPDATED TYPOLOGY MEMBER COUNT (post-Phase 2)")
print("=" * 80)

new_members = {"1": [], "2": [], "3": [], "3a": [], "3a-leaning": [], "3b": [], "4a": [], "4b": [], "4c": [], "6": []}
for panel, rs in results.items():
    for r in rs:
        rg = r["regime"]
        if rg.startswith("3a (Bimodal"):
            new_members["3a"].append(r["iso"])
        elif rg.startswith("3a-leaning"):
            new_members["3a-leaning"].append(r["iso"])
        elif rg.startswith("3b"):
            new_members["3b"].append(r["iso"])
        elif rg.startswith("3 (Storm"):
            new_members["3"].append(r["iso"])
        elif rg.startswith("6"):
            new_members["6"].append(r["iso"])
        elif rg.startswith("4a"):
            new_members["4a"].append(r["iso"])
        elif rg.startswith("4b"):
            new_members["4b"].append(r["iso"])
        elif rg.startswith("4c"):
            new_members["4c"].append(r["iso"])
        elif rg.startswith("2"):
            new_members["2"].append(r["iso"])
        elif rg.startswith("1"):
            new_members["1"].append(r["iso"])

for k, v in new_members.items():
    if v:
        print(f"  Regime {k}: +{len(v)} new — {v}")

# Save results
import json
out = {}
for panel, rs in results.items():
    out[panel] = []
    for r in rs:
        out[panel].append({k: (float(v) if isinstance(v, (np.floating, np.integer)) else v) for k, v in r.items()})

Path("D:/IDP/analysis/paper2_phase2_results_2026_05_25.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
print(f"\nResults saved: D:/IDP/analysis/paper2_phase2_results_2026_05_25.json")
