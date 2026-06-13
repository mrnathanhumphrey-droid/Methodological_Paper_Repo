"""
Paper 4 Phase 2 — re-fire PRE_REG_018 v2 (5-type classifier with refined rules) +
test PRE_REG_019 (type-distinct DPF ratios) + PRE_REG_020 (type-distinct spatial).
Pre-regs locked 2026-05-27.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import pycountry

sys.stdout.reconfigure(encoding="utf-8")

UCDP = Path("D:/IDP/data/ucdp/GEDEvent_v25_1.csv")
GIDD_CONF = Path("D:/IDP/data/idmc_gidd/IDMC_GIDD_Conflict_Violence_Disasters.xlsx")

print("=" * 80)
print("PAPER 4 PHASE 2 — Re-fire v2 classifier + PRE_REG_019 + PRE_REG_020")
print("=" * 80)

# Load and aggregate (same as Phase 1)
print("\n[1/5] Loading UCDP-GED v25...")
u = pd.read_csv(UCDP, usecols=[
    "country", "country_id", "year", "type_of_violence",
    "best", "adm_1", "side_a", "side_b"
])
u = u[u["year"].between(2020, 2024)]

# Country to ISO3
COUNTRY_TO_ISO = {}
for c in u["country"].dropna().unique():
    try:
        co = pycountry.countries.search_fuzzy(c)[0]
        COUNTRY_TO_ISO[c] = co.alpha_3
    except Exception:
        COUNTRY_TO_ISO[c] = None
overrides = {
    "DR Congo (Zaire)": "COD",
    "Yemen (North Yemen)": "YEM",
    "Russia (Soviet Union)": "RUS",
    "Cambodia (Kampuchea)": "KHM",
    "Iran": "IRN",
    "Vietnam (North Vietnam)": "VNM",
    "Madagascar (Malagasy)": "MDG",
    "Myanmar (Burma)": "MMR",
    "Macedonia, FYR": "MKD",
    "Bolivia": "BOL",
    "Ivory Coast": "CIV",
    "Türkiye": "TUR",
    "Turkey": "TUR",
}
for k, v in overrides.items():
    COUNTRY_TO_ISO[k] = v
u["iso3"] = u["country"].map(COUNTRY_TO_ISO)

# Aggregate per country
agg = u.groupby(["iso3", "type_of_violence"])["best"].sum().unstack(fill_value=0)
agg.columns = ["state_based", "non_state", "one_sided"]
agg["total_fat"] = agg.sum(axis=1)
agg = agg[agg["total_fat"] >= 500]
agg["state_share"] = agg["state_based"] / agg["total_fat"]
agg["strife_share"] = agg["non_state"] / agg["total_fat"]
agg["one_sided_share"] = agg["one_sided"] / agg["total_fat"]

# Admin-1 dominance
adm1_dom = {}
for iso in agg.index:
    rows = u[u["iso3"] == iso]
    by_adm = rows.groupby("adm_1")["best"].sum().sort_values(ascending=False)
    if len(by_adm) > 0 and by_adm.sum() > 0:
        adm1_dom[iso] = by_adm.head(3).sum() / by_adm.sum()
    else:
        adm1_dom[iso] = 0
agg["admin1_top3_share"] = agg.index.map(adm1_dom)

# Top-actor share
top_actor = {}
for iso in agg.index:
    rows = u[(u["iso3"] == iso) & (u["type_of_violence"] == 3)]
    if len(rows) > 0:
        by_actor = rows.groupby("side_a")["best"].sum().sort_values(ascending=False)
        if by_actor.sum() > 0:
            top_actor[iso] = by_actor.iloc[0] / by_actor.sum()
        else:
            top_actor[iso] = 0
    else:
        top_actor[iso] = 0
agg["top_actor_share"] = agg.index.map(top_actor)

# Join GIDD
print("[2/5] Joining GIDD...")
g = pd.read_excel(GIDD_CONF)
g.columns = [c.strip() for c in g.columns]
idp_col = "Conflict Stock Displacement"
g[idp_col] = pd.to_numeric(g[idp_col], errors="coerce")
g_idp = g[g["Year"].between(2020, 2024)].groupby("ISO3")[idp_col].sum().to_dict()
agg["conflict_idp"] = agg.index.map(g_idp).fillna(0)
agg["disp_per_fat"] = (agg["conflict_idp"] / agg["total_fat"]).clip(upper=5000)

# ============================================================================
# PRE_REG_018 v2 classifier
# ============================================================================
print("\n[3/5] Applying v2 classifier rules...")

def classify_v2(row):
    s = row["state_share"]
    st = row["strife_share"]
    o = row["one_sided_share"]
    dpf = row["disp_per_fat"]
    adm = row["admin1_top3_share"]
    actor = row["top_actor_share"]
    idp = row["conflict_idp"]
    total = row["total_fat"]

    # Apply with tie-break order: A > B > D > E > C

    # Type A — formal-army (refined)
    if (s >= 0.70 and st <= 0.10 and dpf <= 150
        and (adm >= 0.60 or total >= 100_000)):
        return "A formal-army"

    # Type B — predator-militia
    if (o >= 0.40 and dpf >= 250 and adm >= 0.60 and actor >= 0.30):
        return "B predator-militia"

    # Type D — criminal-violence (NEW)
    if (st >= 0.80 and dpf <= 100 and s <= 0.10):
        return "D criminal-violence"

    # Type E — civil-war-mass-displacement (NEW)
    if (s >= 0.55 and dpf >= 300 and idp >= 500_000):
        return "E civil-war-mass-displacement"

    # Type C — irregular insurgency (refined: admin-1 loosened)
    if (st >= 0.30 and adm <= 0.85):
        return "C irregular insurgency"
    if (0.20 <= s <= 0.70 and 0.20 <= o <= 0.60 and adm <= 0.85):
        return "C irregular insurgency"
    if (100 <= dpf <= 300 and actor < 0.50):
        return "C irregular insurgency"

    return "UNCLASSIFIED"

agg["type_v2"] = agg.apply(classify_v2, axis=1)
agg = agg.sort_values("total_fat", ascending=False)

# Display
print(f"\n{'ISO':<5} {'Total':<10} {'State%':<7} {'Strife%':<8} {'1-side%':<8} {'D/F':<7} {'Adm1%':<7} {'Actor%':<7} {'IDP':<11} {'Type v2'}")
for iso, r in agg.iterrows():
    print(f"{iso:<5} {r['total_fat']:<10,.0f} {100*r['state_share']:<7.1f} {100*r['strife_share']:<8.1f} {100*r['one_sided_share']:<8.1f} {r['disp_per_fat']:<7.0f} {100*r['admin1_top3_share']:<7.1f} {100*r['top_actor_share']:<7.1f} {r['conflict_idp']:<11,.0f} {r['type_v2']}")

# Type counts
print("\n=== Type counts ===")
type_counts = agg["type_v2"].value_counts()
for t, c in type_counts.items():
    print(f"  {t}: {c}")

# Anchor check (PRE_REG_018 v2 Prediction set A)
print("\n=== Anchor + new-type cases check ===")
anchors_v2 = {
    "ETH": "A", "UKR": "A", "RUS": "A", "ISR": "A", "PAK": "A", "EGY": "A",
    "COD": "B", "MOZ": "B", "HTI": "B",
    "MEX": "D", "BRA": "D", "ECU": "D",
    "MLI": "C", "BFA": "C", "SOM": "C",
    "SYR": "E", "YEM": "E", "AFG": "E",
}
matches = 0
data_valid = 0
print(f"{'ISO':<5} {'Predicted':<6} {'Actual':<35} {'Match'}")
for iso, pred in anchors_v2.items():
    if iso in agg.index:
        actual = agg.loc[iso, "type_v2"]
        match = "YES" if actual.startswith(pred) else "NO"
        data_valid += 1
        if match == "YES":
            matches += 1
    else:
        actual = "INSUFFICIENT (<500 fat)"
        match = "DATA"
    print(f"{iso:<5} {pred:<6} {actual:<35} {match}")
print(f"\nAnchor + new-type matches: {matches}/{data_valid}")
print(f"PRE_REG_018 v2 H1 (>= 16 of 18 match): {'SUPPORTED' if matches >= 16 else 'NOT MET'}")
print(f"F1 v2 (>= 3 fail): {'FIRED' if (data_valid - matches) >= 3 else 'NOT FIRED'}")

unclass = (agg["type_v2"] == "UNCLASSIFIED").sum()
print(f"\nUnclassified: {unclass}")
print(f"F2 v2 (>= 5 unclassified): {'FIRED' if unclass >= 5 else 'NOT FIRED'}")

# F3 / F4 / F5
type_d_count = (agg["type_v2"] == "D criminal-violence").sum()
type_e_count = (agg["type_v2"] == "E civil-war-mass-displacement").sum()
type_a_count = (agg["type_v2"] == "A formal-army").sum()
print(f"F3 (Type D = 0): {'FIRED' if type_d_count == 0 else 'NOT FIRED'} ({type_d_count} Type D)")
print(f"F4 (Type E = 0): {'FIRED' if type_e_count == 0 else 'NOT FIRED'} ({type_e_count} Type E)")
print(f"F5 (Type A >= 10): {'FIRED' if type_a_count >= 10 else 'NOT FIRED'} ({type_a_count} Type A)")

# ============================================================================
# PRE_REG_019 — type-distinct DPF ratios
# ============================================================================
print("\n" + "=" * 80)
print("PRE_REG_019 — Type-distinct DPF ratios")
print("=" * 80)

dpf_bands = {
    "A formal-army": (30, 80),
    "B predator-militia": (250, 1500),
    "C irregular insurgency": (100, 300),
    "D criminal-violence": (0, 100),
    "E civil-war-mass-displacement": (300, 2500),
}

dpf_results = {}
print(f"\n{'Type':<35} {'N':<5} {'Median':<10} {'P25':<10} {'P75':<10} {'IQR':<10} {'Predicted band':<20} {'Match'}")
for t in ["A formal-army", "B predator-militia", "C irregular insurgency",
          "D criminal-violence", "E civil-war-mass-displacement"]:
    rows = agg[agg["type_v2"] == t]
    if len(rows) == 0:
        print(f"{t:<35} 0     -          -          -          -          -                    DATA")
        continue
    med = rows["disp_per_fat"].median()
    p25 = rows["disp_per_fat"].quantile(0.25)
    p75 = rows["disp_per_fat"].quantile(0.75)
    iqr = p75 - p25
    band = dpf_bands[t]
    match = "YES" if band[0] <= med <= band[1] else "NO"
    dpf_results[t] = {"median": med, "iqr": iqr, "p25": p25, "p75": p75, "match": match, "n": len(rows)}
    print(f"{t:<35} {len(rows):<5} {med:<10.0f} {p25:<10.0f} {p75:<10.0f} {iqr:<10.0f} {f'{band[0]}-{band[1]}':<20} {match}")

# Rank ordering test
medians = {t: dpf_results[t]["median"] for t in dpf_results}
sorted_by_med = sorted(medians.items(), key=lambda x: x[1])
print(f"\nRank ordering by median DPF (low to high): {' < '.join([t.split()[0] for t, _ in sorted_by_med])}")
print(f"Predicted order: D ~= A < C < B < E")

# Check key pairs
pairs_to_check = [
    ("D criminal-violence", "C irregular insurgency"),
    ("A formal-army", "C irregular insurgency"),
    ("C irregular insurgency", "B predator-militia"),
    ("C irregular insurgency", "E civil-war-mass-displacement"),
]
correct_pairs = 0
for lo, hi in pairs_to_check:
    if lo in medians and hi in medians:
        if medians[lo] < medians[hi]:
            correct_pairs += 1
            print(f"  {lo} < {hi}: ✓ ({medians[lo]:.0f} < {medians[hi]:.0f})")
        else:
            print(f"  {lo} < {hi}: ✗ ({medians[lo]:.0f} vs {medians[hi]:.0f})")
print(f"\nPairs correct: {correct_pairs}/{len(pairs_to_check)}")
print(f"H2 rank ordering (≥3 of 4 pairs): {'SUPPORTED' if correct_pairs >= 3 else 'WALKED BACK'}")

# Within-type IQR vs inter-type spread
matches_h1 = sum(1 for t in dpf_results if dpf_results[t]["match"] == "YES")
print(f"\nH1 medians in bands: {matches_h1}/5 matches")
print(f"H1 (>= 4 of 5 bands match): {'SUPPORTED' if matches_h1 >= 4 else 'WALKED BACK'}")

inter_spread = max(medians.values()) - min(medians.values())
print(f"\nInter-type median spread: {inter_spread:.0f}")
max_iqr = max(dpf_results[t]["iqr"] for t in dpf_results)
print(f"Max within-type IQR: {max_iqr:.0f}")
print(f"H3 (within IQR < between spread for ALL types): ", end="")
all_smaller = all(dpf_results[t]["iqr"] < inter_spread for t in dpf_results)
print("SUPPORTED" if all_smaller else "WALKED BACK")

# ============================================================================
# PRE_REG_020 — spatial concentration
# ============================================================================
print("\n" + "=" * 80)
print("PRE_REG_020 — Type-distinct spatial concentration")
print("=" * 80)

spatial_bands = {
    "A formal-army": (0.85, 1.0),
    "B predator-militia": (0.85, 1.0),
    "C irregular insurgency": (0.50, 0.85),
    "D criminal-violence": (0.40, 0.80),
    "E civil-war-mass-displacement": (0.0, 1.0),  # variable
}

spatial_results = {}
print(f"\n{'Type':<35} {'N':<5} {'Median Adm1%':<14} {'P25':<8} {'P75':<8} {'Predicted band':<18} {'Match'}")
for t in ["A formal-army", "B predator-militia", "C irregular insurgency",
          "D criminal-violence", "E civil-war-mass-displacement"]:
    rows = agg[agg["type_v2"] == t]
    if len(rows) == 0:
        print(f"{t:<35} 0     -              -        -        -                  DATA")
        continue
    med = rows["admin1_top3_share"].median()
    p25 = rows["admin1_top3_share"].quantile(0.25)
    p75 = rows["admin1_top3_share"].quantile(0.75)
    band = spatial_bands[t]
    match = "YES" if band[0] <= med <= band[1] else "NO"
    spatial_results[t] = {"median": med, "match": match, "n": len(rows)}
    print(f"{t:<35} {len(rows):<5} {100*med:<14.1f} {100*p25:<8.1f} {100*p75:<8.1f} {f'{int(band[0]*100)}-{int(band[1]*100)}%':<18} {match}")

matches_spatial = sum(1 for t in spatial_results if spatial_results[t]["match"] == "YES")
print(f"\nH1 spatial bands matches: {matches_spatial}/5")
print(f"H1 (>= 3 of 5 bands): {'SUPPORTED' if matches_spatial >= 3 else 'WALKED BACK'}")

# F2: A and B both >= 70%?
spatial_medians = {t: spatial_results[t]["median"] for t in spatial_results}
if "A formal-army" in spatial_medians and "B predator-militia" in spatial_medians:
    a_med = spatial_medians["A formal-army"]
    b_med = spatial_medians["B predator-militia"]
    print(f"\nF2 (A or B median < 70%): A={100*a_med:.1f}%, B={100*b_med:.1f}%")
    f2 = "FIRED" if a_med < 0.70 or b_med < 0.70 else "NOT FIRED"
    print(f"  Status: {f2}")

# F3: Type C lowest?
if "C irregular insurgency" in spatial_medians:
    c_med = spatial_medians["C irregular insurgency"]
    is_lowest = all(c_med <= spatial_medians[t] for t in spatial_medians)
    print(f"\nF3 (Type C not lowest): C={100*c_med:.1f}%; lowest: {'YES' if is_lowest else 'NO'}")

# Save
agg.to_parquet("D:/IDP/analysis/paper4_phase2_classifier_v2_2026_05_27.parquet")
print(f"\nResults saved: D:/IDP/analysis/paper4_phase2_classifier_v2_2026_05_27.parquet")
