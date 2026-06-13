"""
Paper 2 Phase 3 — fire P2-H (regime stability 1980-2007 vs 2008-2024) + P2-F (USA 2024 decomposition)
+ partial PRE_REG_015 fit (USA storm-mega-year count from EM-DAT historical).
Pre-regs locked 2026-05-25: PRE_REG_014, PRE_REG_015.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding="utf-8")

GIDD = Path("D:/IDP/data/idmc_gidd/IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx")
EMDAT = Path("D:/IDP/data/emdat/public_emdat_incl_hist_2026-05-18.xlsx")

print("=" * 80)
print("PAPER 2 PHASE 3 — Stability test (PRE_REG_014) + USA decomposition (P2-F) + partial PRE_REG_015")
print("=" * 80)

print("\n[1/3] Loading EM-DAT historical...")
e = pd.read_excel(EMDAT)
print(f"  EM-DAT total rows: {len(e)}")
print(f"  Year range: {e['Start Year'].min()} - {e['Start Year'].max()}")

# Map disaster types to hazard classes
emdat_to_hazard = {
    "Earthquake": "Earthquake",
    "Flood": "Flood",
    "Storm": "Storm",
    "Drought": "Drought",
    "Mass movement (wet)": "Mass Movement",
    "Mass movement (dry)": "Mass Movement",
    "Volcanic activity": "Volcanic activity",
    "Wildfire": "Wildfire",
    "Extreme temperature": "Extreme Temperature",
}
e["hazard"] = e["Disaster Type"].map(emdat_to_hazard).fillna("Other")
# Use Total Affected as displacement proxy for historical data
e["affected"] = pd.to_numeric(e["Total Affected"], errors="coerce")
e = e.dropna(subset=["affected", "ISO", "Start Year"])
e = e[e["affected"] > 0]

# Split into 1980-2007 and 2008-2024 windows
e_old = e[e["Start Year"].between(1980, 2007)].copy()
e_new = e[e["Start Year"].between(2008, 2024)].copy()
print(f"  1980-2007 events: {len(e_old)}")
print(f"  2008-2024 events: {len(e_new)}")

# ============================================================================
# P2-H — Regime stability test (PRE_REG_014)
# ============================================================================
print("\n" + "=" * 80)
print("P2-H — Regime stability (1980-2007 vs 2008-2024)")
print("=" * 80)

def classify_emdat(window_df, iso, threshold=100_000):
    rows = window_df[window_df["ISO"] == iso]
    if len(rows) == 0:
        return ("MISSING", 0, {})
    total = rows["affected"].sum()
    if total < threshold:
        return ("DATA-SPARSE", total, {})
    haz = rows.groupby("hazard")["affected"].sum()
    flood = haz.get("Flood", 0)
    storm = haz.get("Storm", 0)
    eq = haz.get("Earthquake", 0)
    drought = haz.get("Drought", 0)
    fire = haz.get("Wildfire", 0)
    flood_pct = 100 * flood / total
    storm_pct = 100 * storm / total
    eq_pct = 100 * eq / total
    drought_pct = 100 * drought / total
    fire_pct = 100 * fire / total

    # Per-year flood max/median
    flood_yrs = rows[rows["hazard"] == "Flood"].groupby("Start Year")["affected"].sum()
    flood_mm = (flood_yrs.max() / flood_yrs.median()) if len(flood_yrs) > 1 and flood_yrs.median() > 0 else 0
    flood_mega = int((flood_yrs >= 1_000_000).sum())

    details = {
        "total": total, "flood_pct": flood_pct, "storm_pct": storm_pct, "eq_pct": eq_pct,
        "drought_pct": drought_pct, "fire_pct": fire_pct, "flood_max_median": flood_mm,
        "flood_mega": flood_mega,
    }

    # Apply rules (EM-DAT-adjusted: affected ≠ IDP, but share-by-hazard comparable)
    if flood_mm > 30 and flood_mega >= 2 and storm_pct < 10:
        return ("1 (Bimodal-mega-flood)", total, details)
    if eq_pct >= 60:
        return ("6 (Earthquake-dominant)", total, details)
    if storm_pct >= 70:
        storm_yrs = rows[rows["hazard"] == "Storm"].groupby("Start Year")["affected"].sum()
        storm_mm = (storm_yrs.max() / storm_yrs.median()) if len(storm_yrs) > 1 and storm_yrs.median() > 0 else 0
        if storm_mm >= 10:
            return ("3a (Bimodal-mega-storm)", total, details)
        else:
            return ("3 (Storm-dominant)", total, details)
    if drought_pct >= 50:
        return ("5 (Drought-dominant — sub-channel)", total, details)
    if fire_pct >= 50:
        return ("7 (Wildfire-dominant — candidate)", total, details)
    if max(flood_pct, storm_pct, eq_pct) < 70:
        if flood_pct >= 50:
            return ("4a (Flood-leaning mixed)", total, details)
        elif storm_pct >= 50:
            return ("4b (Storm-leaning mixed)", total, details)
        else:
            return ("4c (Balanced mixed)", total, details)
    return ("UNCLASSIFIED", total, details)


# Pull the regime members from PATTERN_019 and Phase 2 expansion
confirmed_members = {
    "PAK": "1", "THA": "1", "IND": "2",
    "PHL": "3b", "USA": "3a", "CUB": "3a", "DOM": "3a", "FJI": "3a", "VUT": "3a", "PRI": "3a",
    "VNM": "3", "MOZ": "3",
    "BGD": "4b", "BRA": "4a", "MEX": "4c", "IDN": "4a", "JPN": "4b", "PER": "4a", "CHN": "4c",
    "MMR": "4b", "AFG": "4a", "IRN": "4a", "GRC": "4c (or 7)",
    "HTI": "6", "NPL": "6", "TUR": "6", "CHL": "6", "ECU": "6", "ITA": "6",
}

print(f"\n{'ISO':<5} {'2008-2024 (GIDD-based)':<28} {'1980-2007 (EM-DAT-based)':<32} {'Stability'}")
print("-" * 90)

results_stability = []
for iso, current in confirmed_members.items():
    old_regime, old_total, old_det = classify_emdat(e_old, iso)
    # Simple stability check: same regime DIGIT
    if old_regime in ("MISSING", "DATA-SPARSE"):
        stability = old_regime
    else:
        old_digit = old_regime.split(" ")[0].rstrip("ab")[0]
        cur_digit = current[0]
        stability = "STABLE" if old_digit == cur_digit else f"SHIFT ({old_digit} -> {cur_digit})"
    results_stability.append({"iso": iso, "current": current, "old": old_regime, "stability": stability,
                              "old_total": old_total})
    print(f"{iso:<5} {current:<28} {old_regime:<32} {stability}")

# Falsifier check
stable = sum(1 for r in results_stability if r["stability"] == "STABLE")
shifted = sum(1 for r in results_stability if "SHIFT" in r["stability"])
data_ok = sum(1 for r in results_stability if r["stability"] in ("STABLE",) or "SHIFT" in r["stability"])
sparse = sum(1 for r in results_stability if r["stability"] in ("DATA-SPARSE", "MISSING"))
print(f"\nStability summary: {stable}/{data_ok} stable (data-valid); {shifted} shifted; {sparse} data-sparse")
print(f"F1 (>= 5 shift): {'FIRED' if shifted >= 5 else 'NOT FIRED'}")

# Specific predictions
print("\n--- HTI/NPL/TUR R6-arrival prediction ---")
for iso in ["HTI", "NPL", "TUR"]:
    r = [x for x in results_stability if x["iso"] == iso][0]
    print(f"  {iso}: current = {r['current']}, 1980-2007 = {r['old']}")
all_r6_late = all(
    (r["old"] in ("MISSING", "DATA-SPARSE")) or "6" not in r["old"]
    for r in results_stability if r["iso"] in ("HTI", "NPL", "TUR")
)
print(f"F3 (ALL R6 fail in 1980-2007): {'FIRED — R6 is event-arrival-driven' if all_r6_late else 'NOT FIRED — at least one R6 was pre-2007'}")

# F2 + F4
flood_shifted = sum(1 for r in results_stability if r["iso"] in ("PAK","IND","THA") and "SHIFT" in r["stability"])
print(f"\nF2 (major flood countries shift): {flood_shifted} of 3 → {'FIRED' if flood_shifted >= 2 else 'NOT FIRED'}")

usa_r = [x for x in results_stability if x["iso"] == "USA"][0]
print(f"F4 (USA shifts from R3): USA 1980-2007 = {usa_r['old']} → {'FIRED' if '3' not in usa_r['old'] and usa_r['stability'] not in ('DATA-SPARSE','MISSING') else 'NOT FIRED'}")

# ============================================================================
# P2-F — USA 2024 mega-storm decomposition
# ============================================================================
print("\n" + "=" * 80)
print("P2-F — USA 2024 mega-storm decomposition")
print("=" * 80)

g = pd.read_excel(GIDD)
g["idp"] = pd.to_numeric(g["Disaster Internal Displacements"], errors="coerce")
usa_2024 = g[(g["ISO3"] == "USA") & (g["Year"] == 2024)].copy()
print(f"\nUSA 2024 events in GIDD: {len(usa_2024)}")

usa_2024_sorted = usa_2024.sort_values("idp", ascending=False)
print(f"\nTop 10 events by displacement:")
print(f"{'Event Name':<55} {'Hazard':<20} {'IDP':>12}")
for _, r in usa_2024_sorted.head(10).iterrows():
    event = str(r.get("Event Name", "n/a"))[:54]
    haz = str(r.get("Hazard Sub Type", r.get("Hazard Type", "n/a")))[:19]
    idp = r.get("idp", 0)
    print(f"{event:<55} {haz:<20} {idp:>12,.0f}")

# Hazard breakdown for USA 2024
print(f"\nUSA 2024 hazard breakdown:")
breakdown_2024 = usa_2024.groupby("Hazard Type")["idp"].sum().sort_values(ascending=False)
total_2024 = breakdown_2024.sum()
for haz, idp in breakdown_2024.items():
    pct = 100 * idp / total_2024 if total_2024 > 0 else 0
    print(f"  {haz:<25} {idp:>12,.0f}  ({pct:5.1f}%)")
print(f"  {'TOTAL':<25} {total_2024:>12,.0f}")

# Compare to USA 2008-2023 baseline
usa_baseline = g[(g["ISO3"] == "USA") & (g["Year"].between(2008, 2023))]
usa_baseline_storm_yr = usa_baseline[usa_baseline["Hazard Type"] == "Storm"].groupby("Year")["idp"].sum()
print(f"\nUSA storm-IDP per year, 2008-2023 baseline:")
for yr, idp in usa_baseline_storm_yr.items():
    print(f"  {yr}: {idp:>12,.0f}")
print(f"\nUSA 2024 storm-IDP: {usa_2024[usa_2024['Hazard Type']=='Storm']['idp'].sum():,.0f}")

# 2024 ratio to baseline median
baseline_median = usa_baseline_storm_yr.median()
baseline_max = usa_baseline_storm_yr.max()
usa_2024_storm = usa_2024[usa_2024['Hazard Type']=='Storm']['idp'].sum()
print(f"\n  Baseline 2008-2023 storm-IDP median: {baseline_median:,.0f}")
print(f"  Baseline 2008-2023 storm-IDP max:    {baseline_max:,.0f}")
print(f"  2024 / median ratio:                 {usa_2024_storm / baseline_median:.1f}x")
print(f"  2024 / max ratio:                    {usa_2024_storm / baseline_max:.1f}x")

# ============================================================================
# PRE_REG_015 partial fit — USA storm-mega-year count 1980-2007 vs 2008-2024
# ============================================================================
print("\n" + "=" * 80)
print("PRE_REG_015 partial fit — USA storm-mega-year count from EM-DAT historical")
print("=" * 80)

# USA storm events from EM-DAT
usa_storms_em = e[(e["ISO"] == "USA") & (e["hazard"] == "Storm")]
usa_storm_yr_em = usa_storms_em.groupby("Start Year")["affected"].sum()
print(f"\nUSA storm-events in EM-DAT 1980-2024: {len(usa_storms_em)}")

mega_old = int((usa_storm_yr_em.loc[1980:2007] >= 1_000_000).sum())
mega_new = int((usa_storm_yr_em.loc[2008:2024] >= 1_000_000).sum())
total_old_yrs = 2007 - 1980 + 1
total_new_yrs = 2024 - 2008 + 1

print(f"\nUSA storm-mega-years (≥1M affected per year):")
print(f"  1980-2007 ({total_old_yrs}y window): {mega_old} years (frequency {100*mega_old/total_old_yrs:.1f}%)")
print(f"  2008-2024 ({total_new_yrs}y window): {mega_new} years (frequency {100*mega_new/total_new_yrs:.1f}%)")
print(f"\nPrediction (PRE_REG_015 H3): 1980-2007 mega-years should be <= 3 (freq <= 11%)")
print(f"Result: {mega_old} mega-years -> {'CONSISTENT' if mega_old <= 3 else 'PREDICTION EXCEEDED (need to refine)'}")

# Display year-by-year for context
print(f"\nYear-by-year USA storm-affected (EM-DAT, sorted by year):")
for yr in sorted(usa_storm_yr_em.index):
    val = usa_storm_yr_em[yr]
    flag = " ← mega" if val >= 1_000_000 else ""
    print(f"  {yr}: {val:>12,.0f}{flag}")

# F1 check
print(f"\nF1 (1980-2007 mega-years > 5): {'FIRED' if mega_old > 5 else 'NOT FIRED'}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\nP2-H Regime stability:")
print(f"  Stable: {stable}/{data_ok} data-valid countries")
print(f"  Shifted: {shifted}")
print(f"  Data-sparse: {sparse}")
print(f"  F1 (>= 5 shift): {'FIRED' if shifted >= 5 else 'NOT FIRED'}")
print(f"  F3 (R6 all event-driven): {'FIRED' if all_r6_late else 'NOT FIRED'}")

print(f"\nP2-F USA 2024 decomposition:")
print(f"  Total USA 2024 IDP: {total_2024:,.0f}")
print(f"  Storm share: {100*usa_2024_storm/total_2024:.1f}%")
print(f"  2024 storm vs 2008-2023 median: {usa_2024_storm/baseline_median:.1f}x")

print(f"\nPRE_REG_015 partial fit (USA storm-mega-year count):")
print(f"  1980-2007: {mega_old} mega-years (predicted <= 3)")
print(f"  2008-2024: {mega_new} mega-years")
print(f"  Trend: {'INTENSIFYING' if mega_new > mega_old else 'STABLE OR DECREASING'}")
