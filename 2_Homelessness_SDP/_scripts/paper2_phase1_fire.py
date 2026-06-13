"""
Paper 2 Phase 1 — fire P2-A (within-regime sub-typing) + P2-I (displacement-per-affected ratios).
Pre-regs: PRE_REG_013 + PRE_REG_016 locked 2026-05-25.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Force UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")

GIDD = Path("D:/IDP/data/idmc_gidd/IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx")
EMDAT = Path("D:/IDP/data/emdat/public_emdat_incl_hist_2026-05-18.xlsx")

print("=" * 80)
print("PAPER 2 PHASE 1 — P2-A sub-typing + P2-I ratios")
print("Pre-regs: PRE_REG_013 + PRE_REG_016 locked 2026-05-25")
print("=" * 80)

# Load GIDD
print("\n[1/4] Loading GIDD Disasters...")
g = pd.read_excel(GIDD)
print(f"  GIDD shape: {g.shape}")
g["idp"] = pd.to_numeric(g["Disaster Internal Displacements"], errors="coerce")
g = g[g["Year"].between(2008, 2024)]
print(f"  After 2008-2024 filter: {g.shape}")

# ============================================================================
# P2-A — Within-regime sub-typing
# ============================================================================
print("\n" + "=" * 80)
print("P2-A — Within-regime sub-typing (PRE_REG_013)")
print("=" * 80)

# Aggregate to country x year x hazard
agg = g.groupby(["ISO3", "Year", "Hazard Type"])["idp"].sum().reset_index()

# Country totals by hazard
country_haz = agg.groupby(["ISO3", "Hazard Type"])["idp"].sum().unstack(fill_value=0)
country_total = country_haz.sum(axis=1)

# ---- Regime 4 sub-typing ----
print("\n[A1] Regime 4 (mixed flood-storm) sub-typing")
print("-" * 60)
regime_4 = ["BGD", "BRA", "MEX", "IDN", "JPN", "PER"]
predictions_4 = {
    "BRA": "4a flood-leaning",
    "IDN": "4a flood-leaning",
    "PER": "4a flood-leaning",
    "BGD": "4b storm-leaning",
    "JPN": "4b storm-leaning",
    "MEX": "4c balanced",
}

print(f"{'ISO':<5} {'Flood %':<10} {'Storm %':<10} {'EQ %':<10} {'Actual':<22} {'Predicted':<22} {'Match'}")
results_4 = []
for iso in regime_4:
    if iso not in country_haz.index:
        print(f"{iso} - no data")
        continue
    total = country_total[iso]
    flood_pct = 100 * country_haz.loc[iso, "Flood"] / total if "Flood" in country_haz.columns else 0
    storm_pct = 100 * country_haz.loc[iso, "Storm"] / total if "Storm" in country_haz.columns else 0
    eq_pct = 100 * country_haz.loc[iso, "Earthquake"] / total if "Earthquake" in country_haz.columns else 0

    if flood_pct >= 50 and storm_pct < 50:
        actual = "4a flood-leaning"
    elif storm_pct >= 50 and flood_pct < 50:
        actual = "4b storm-leaning"
    else:
        actual = "4c balanced"

    pred = predictions_4[iso]
    match = "YES" if actual == pred else "NO"
    results_4.append({"iso": iso, "actual": actual, "predicted": pred, "match": match,
                      "flood": flood_pct, "storm": storm_pct, "eq": eq_pct})
    print(f"{iso:<5} {flood_pct:<10.1f} {storm_pct:<10.1f} {eq_pct:<10.1f} {actual:<22} {pred:<22} {match}")

match_count_4 = sum(1 for r in results_4 if r["match"] == "YES")
print(f"\nRegime 4 sub-typing matches: {match_count_4}/{len(results_4)}")
print(f"PRE_REG_013 H3-4 threshold: >= 5 of 6 -> {'SUPPORTED' if match_count_4 >= 5 else 'NOT MET'}")

# ---- Regime 6 sub-typing ----
print("\n[A2] Regime 6 (EQ-dominant) sub-typing — single-event share")
print("-" * 60)
regime_6 = ["HTI", "NPL", "TUR", "CHL", "ECU", "ITA"]
predictions_6 = {
    "HTI": "6a single-quake-driven",
    "NPL": "6a single-quake-driven",
    "TUR": "6a single-quake-driven",
    "CHL": "6b multi-quake-distributed",
    "ECU": "6b multi-quake-distributed",
    "ITA": "6b multi-quake-distributed",
}

print(f"{'ISO':<5} {'EQ total':<12} {'Max event':<12} {'Max share %':<14} {'Actual':<28} {'Predicted':<28} {'Match'}")
results_6 = []
eq_only = g[g["Hazard Type"] == "Earthquake"].copy()

for iso in regime_6:
    rows = eq_only[eq_only["ISO3"] == iso]
    if len(rows) == 0:
        print(f"{iso} - no EQ data")
        continue
    eq_total = rows["idp"].sum()
    max_event = rows["idp"].max() if len(rows) > 0 else 0
    max_share = 100 * max_event / eq_total if eq_total > 0 else 0
    actual = "6a single-quake-driven" if max_share >= 50 else "6b multi-quake-distributed"
    pred = predictions_6[iso]
    match = "YES" if actual == pred else "NO"
    results_6.append({"iso": iso, "actual": actual, "predicted": pred, "match": match,
                      "eq_total": eq_total, "max_event": max_event, "max_share": max_share})
    print(f"{iso:<5} {eq_total:<12.0f} {max_event:<12.0f} {max_share:<14.1f} {actual:<28} {pred:<28} {match}")

match_count_6 = sum(1 for r in results_6 if r["match"] == "YES")
print(f"\nRegime 6 sub-typing matches: {match_count_6}/{len(results_6)}")
print(f"PRE_REG_013 H3-6 threshold: >= 5 of 6 -> {'SUPPORTED' if match_count_6 >= 5 else 'NOT MET'}")

# ---- Regime 3 extension: DOM/FJI/VUT/BGD year-by-year storm ----
print("\n[A3] Regime 3 extension — DOM/FJI/VUT/BGD bimodal vs perpetual")
print("-" * 60)
regime_3_test = ["DOM", "FJI", "VUT", "BGD"]
predictions_3 = {
    "DOM": "3a bimodal-mega-storm",
    "FJI": "3a bimodal-mega-storm",
    "VUT": "3a-leaning",
    "BGD": "3b-adjacent (perpetual)",
}

storm_only = g[g["Hazard Type"] == "Storm"].copy()
storm_yr = storm_only.groupby(["ISO3", "Year"])["idp"].sum().reset_index()

print(f"{'ISO':<5} {'Years>1M':<10} {'Total yrs':<10} {'Max/median':<12} {'Median':<12} {'Max':<12} {'Actual':<28} {'Predicted'}")
results_3 = []
for iso in regime_3_test:
    rows = storm_yr[storm_yr["ISO3"] == iso]
    if len(rows) == 0:
        print(f"{iso} - no storm data")
        continue
    vals = rows["idp"].values
    median = np.median(vals) if len(vals) > 0 else 0
    mx = vals.max() if len(vals) > 0 else 0
    mega_years = int((rows["idp"] > 1_000_000).sum())
    total_yrs = len(rows)
    ratio = mx / median if median > 0 else float("inf")

    if ratio >= 10 and mega_years <= total_yrs / 3:
        actual = "3a bimodal-mega-storm"
    elif ratio < 5 and mega_years >= 0.8 * total_yrs:
        actual = "3b perpetual-mega-storm"
    elif ratio >= 5:
        actual = "3a-leaning"
    else:
        actual = "3b-adjacent"

    pred = predictions_3[iso]
    match_strict = "YES" if actual == pred else "PARTIAL" if actual.split("-")[0] == pred.split("-")[0] else "NO"
    results_3.append({"iso": iso, "actual": actual, "predicted": pred, "match": match_strict,
                      "ratio": ratio, "mega_years": mega_years, "total_yrs": total_yrs})
    print(f"{iso:<5} {mega_years:<10} {total_yrs:<10} {ratio:<12.2f} {median:<12.0f} {mx:<12.0f} {actual:<28} {pred}")

partial_or_match_3 = sum(1 for r in results_3 if r["match"] in ("YES", "PARTIAL"))
print(f"\nRegime 3 extension matches (incl partial): {partial_or_match_3}/{len(results_3)}")

# ============================================================================
# P2-I — Displacement-per-affected ratios
# ============================================================================
print("\n" + "=" * 80)
print("P2-I — Displacement-per-affected ratios (PRE_REG_016)")
print("=" * 80)

print("\n[2/4] Loading EM-DAT...")
e = pd.read_excel(EMDAT)
print(f"  EM-DAT shape: {e.shape}")

# Filter EM-DAT to 2008-2024 disasters
e = e[e["Start Year"].between(2008, 2024)]
e["total_affected"] = pd.to_numeric(e["Total Affected"], errors="coerce")
e = e.dropna(subset=["total_affected", "ISO", "Start Year", "Disaster Type"])
e = e[e["total_affected"] > 0]
print(f"  After filter: {e.shape}")

# Map EM-DAT disaster types to GIDD hazard types
emdat_to_hazard = {
    "Earthquake": "Earthquake",
    "Flood": "Flood",
    "Storm": "Storm",
    "Drought": "Drought",
    "Mass movement (wet)": "Mass Movement",
    "Mass movement (dry)": "Mass Movement",
    "Volcanic activity": "Volcanic activity",
    "Wildfire": "Wildfire",
}
e["hazard"] = e["Disaster Type"].map(emdat_to_hazard)
e = e.dropna(subset=["hazard"])

# Country-year-hazard EM-DAT affected aggregates
emdat_agg = e.groupby(["ISO", "Start Year", "hazard"])["total_affected"].sum().reset_index()
emdat_agg.columns = ["ISO3", "Year", "Hazard Type", "affected"]

# Join with GIDD
joined = agg.merge(emdat_agg, on=["ISO3", "Year", "Hazard Type"], how="inner")
joined = joined[(joined["idp"] > 0) & (joined["affected"] > 0)]
joined["ratio"] = joined["idp"] / joined["affected"]
joined = joined[joined["ratio"] <= 2.0]  # cap at 2.0 to handle minor data mismatches; reject >2 as data error
print(f"  Joined records: {len(joined)}")
print(f"  Ratio range: {joined['ratio'].min():.4f} to {joined['ratio'].max():.4f}")

# ---- A: Hazard-type medians ----
print("\n[B1] Hazard-type median ratios")
print("-" * 60)
print(f"{'Hazard':<20} {'N':<8} {'Median %':<12} {'P25 %':<10} {'P75 %':<10}")
hazards = ["Earthquake", "Flood", "Storm", "Drought"]
hazard_medians = {}
for h in hazards:
    rows = joined[joined["Hazard Type"] == h]
    if len(rows) >= 5:
        med = 100 * rows["ratio"].median()
        p25 = 100 * rows["ratio"].quantile(0.25)
        p75 = 100 * rows["ratio"].quantile(0.75)
        hazard_medians[h] = med
        print(f"{h:<20} {len(rows):<8} {med:<12.2f} {p25:<10.2f} {p75:<10.2f}")
    else:
        print(f"{h:<20} {len(rows):<8} INSUFFICIENT (need n >= 5)")

# Falsifier F1
print(f"\nF1 (EQ median >= 20%): EQ median = {hazard_medians.get('Earthquake', 0):.1f}% -> {'NOT FIRED' if hazard_medians.get('Earthquake', 0) >= 20 else 'FIRED'}")
# Falsifier F2
if "Storm" in hazard_medians and "Flood" in hazard_medians:
    diff = abs(hazard_medians["Storm"] - hazard_medians["Flood"])
    print(f"F2 (|Storm - Flood| > 15pp): diff = {diff:.1f}pp -> {'FIRED' if diff > 15 else 'NOT FIRED'}")

# ---- B: Regime-by-regime ratios ----
print("\n[B2] Regime-by-regime median ratios")
print("-" * 60)

REGIME_MAP = {
    "PAK": "1",
    "IND": "2",
    "PHL": "3b", "VNM": "3", "MOZ": "3", "DOM": "3", "CUB": "3a", "USA": "3a", "FJI": "3", "VUT": "3",
    "BGD": "4", "BRA": "4", "MEX": "4", "IDN": "4", "JPN": "4", "PER": "4",
    "HTI": "6", "NPL": "6", "CHL": "6", "ECU": "6", "TUR": "6", "ITA": "6",
}
joined["regime"] = joined["ISO3"].map(REGIME_MAP)

print(f"{'Regime':<10} {'N':<8} {'Median %':<12} {'P25 %':<10} {'P75 %':<10} {'Countries'}")
regime_results = {}
for regime in ["1", "2", "3", "3a", "3b", "4", "6"]:
    rows = joined[joined["regime"] == regime]
    if len(rows) >= 3:
        med = 100 * rows["ratio"].median()
        p25 = 100 * rows["ratio"].quantile(0.25)
        p75 = 100 * rows["ratio"].quantile(0.75)
        countries = sorted(rows["ISO3"].unique().tolist())
        regime_results[regime] = med
        print(f"{regime:<10} {len(rows):<8} {med:<12.2f} {p25:<10.2f} {p75:<10.2f} {countries}")

# Falsifier F4
if len(regime_results) >= 3:
    spread = max(regime_results.values()) - min(regime_results.values())
    print(f"\nF4 (regimes within 10pp): max-min spread = {spread:.1f}pp -> {'FIRED' if spread < 10 else 'NOT FIRED'}")

# ---- C: State-capacity moderation ----
print("\n[B3] State-capacity moderation contrasts")
print("-" * 60)

def country_median(iso, hazard=None):
    rows = joined[joined["ISO3"] == iso]
    if hazard:
        rows = rows[rows["Hazard Type"] == hazard]
    return (100 * rows["ratio"].median(), len(rows)) if len(rows) >= 2 else (None, len(rows))

contrasts = [
    ("USA", "PHL", "Storm", "Regime 3 storm contrast (high vs mid capacity)"),
    ("ITA", "NPL", "Earthquake", "Regime 6 EQ contrast (high vs low capacity)"),
    ("JPN", "HTI", "Earthquake", "Mixed EQ contrast (high vs low capacity)"),
]

contrast_results = []
for high, low, haz, label in contrasts:
    h_med, h_n = country_median(high, haz)
    l_med, l_n = country_median(low, haz)
    print(f"\n  {label}")
    print(f"    {high} {haz} ratio: {h_med if h_med is None else f'{h_med:.1f}%'} (n={h_n})")
    print(f"    {low} {haz} ratio: {l_med if l_med is None else f'{l_med:.1f}%'} (n={l_n})")
    if h_med is not None and l_med is not None:
        diff = l_med - h_med
        direction = "PREDICTED" if h_med < l_med else "OPPOSITE"
        threshold = 10 if "EQ" not in label or "Mixed" not in label else 15
        meets = abs(diff) >= threshold and h_med < l_med
        print(f"    diff: {diff:+.1f}pp, direction: {direction}, meets >= {threshold}pp: {'YES' if meets else 'NO'}")
        contrast_results.append({"high": high, "low": low, "diff": diff, "meets": meets, "direction": direction})

meets_count = sum(1 for r in contrast_results if r["meets"])
print(f"\nState-capacity contrasts meeting prediction: {meets_count}/{len(contrast_results)}")
print(f"PRE_REG_016 F3 threshold: H2 walked back if < 2 of 3 -> {'WALKED BACK' if meets_count < 2 else 'NOT WALKED BACK'}")

# ============================================================================
# Save results
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\nPRE_REG_013 (within-regime sub-typing):")
print(f"  Regime 4 matches: {match_count_4}/{len(results_4)} -> {'SUPPORTED' if match_count_4 >= 5 else 'NOT MET'}")
print(f"  Regime 6 matches: {match_count_6}/{len(results_6)} -> {'SUPPORTED' if match_count_6 >= 5 else 'NOT MET'}")
print(f"  Regime 3 extension: {partial_or_match_3}/{len(results_3)} matches (incl partial)")

print(f"\nPRE_REG_016 (displacement-per-affected ratios):")
print(f"  Hazard medians: {hazard_medians}")
print(f"  Regime medians: {regime_results}")
print(f"  State-capacity contrasts: {meets_count}/{len(contrast_results)}")

# Save to parquet for digs
joined.to_parquet("D:/IDP/analysis/paper2_phase1_joined_2026_05_25.parquet")
print(f"\nJoined data saved: D:/IDP/analysis/paper2_phase1_joined_2026_05_25.parquet ({len(joined)} rows)")
