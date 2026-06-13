"""
Paper 4 Phase 1 — fire P4-C: apply conflict-type classifier to full IDP corpus.
Pre-reg: PRE_REG_018 locked 2026-05-27.
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
print("PAPER 4 PHASE 1 — Conflict-type classifier (PRE_REG_018 locked 2026-05-27)")
print("=" * 80)

# Load UCDP-GED
print("\n[1/4] Loading UCDP-GED v25...")
u = pd.read_csv(UCDP, usecols=[
    "country", "country_id", "year", "type_of_violence",
    "best", "adm_1", "side_a", "side_b", "conflict_name"
])
u = u[u["year"].between(2020, 2024)]
print(f"  UCDP-GED 2020-2024 events: {len(u)}")

# Manual country name to ISO3 mapping (faster than pycountry fuzzy for our corpus)
# Cover countries present in cluster panels + anchors
COUNTRY_TO_ISO = {}
for c in u["country"].dropna().unique():
    try:
        co = pycountry.countries.search_fuzzy(c)[0]
        COUNTRY_TO_ISO[c] = co.alpha_3
    except Exception:
        COUNTRY_TO_ISO[c] = None

# Manual overrides for common mismatches
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
print(f"  Unique ISO3 mapped: {u['iso3'].nunique()}")
missing = u[u["iso3"].isna()]["country"].unique()
if len(missing) > 0:
    print(f"  Missing ISO3 for: {missing}")

# ============================================================================
# Aggregate per country
# ============================================================================
agg_violence = u.groupby(["iso3", "type_of_violence"])["best"].sum().unstack(fill_value=0)
agg_violence.columns = ["state_based", "non_state", "one_sided"]
agg_violence["total_fat"] = agg_violence.sum(axis=1)

# Filter: 500+ fatalities total threshold
agg_violence = agg_violence[agg_violence["total_fat"] >= 500]
print(f"\n  Countries with >= 500 acute fatalities: {len(agg_violence)}")

# Compute shares
agg_violence["state_share"] = agg_violence["state_based"] / agg_violence["total_fat"]
agg_violence["strife_share"] = agg_violence["non_state"] / agg_violence["total_fat"]
agg_violence["one_sided_share"] = agg_violence["one_sided"] / agg_violence["total_fat"]

# Admin-1 top-3 share per country
print("\n[2/4] Computing admin-1 dominance...")
adm1_dom = {}
for iso in agg_violence.index:
    rows = u[u["iso3"] == iso]
    by_adm = rows.groupby("adm_1")["best"].sum().sort_values(ascending=False)
    if len(by_adm) > 0:
        top3 = by_adm.head(3).sum()
        adm1_dom[iso] = top3 / by_adm.sum() if by_adm.sum() > 0 else 0
    else:
        adm1_dom[iso] = 0
agg_violence["admin1_top3_share"] = agg_violence.index.map(adm1_dom)

# Top-actor share (for one-sided)
print("[2.5/4] Computing top-actor dominance for one-sided violence...")
top_actor = {}
for iso in agg_violence.index:
    rows = u[(u["iso3"] == iso) & (u["type_of_violence"] == 3)]
    if len(rows) > 0:
        by_actor = rows.groupby("side_a")["best"].sum().sort_values(ascending=False)
        if by_actor.sum() > 0:
            top_actor[iso] = by_actor.iloc[0] / by_actor.sum()
        else:
            top_actor[iso] = 0
    else:
        top_actor[iso] = 0
agg_violence["top_actor_share"] = agg_violence.index.map(top_actor)

# ============================================================================
# Join with GIDD conflict-displacement
# ============================================================================
print("\n[3/4] Loading GIDD conflict-displacement...")
g = pd.read_excel(GIDD_CONF)
g = g.rename(columns={c: c.strip() for c in g.columns})
# Find ISO3 col + year + conflict idp col
print(f"  GIDD conflict cols: {[c for c in g.columns if 'isp' in c.lower() or 'iso' in c.lower() or 'ear' in c.lower() or 'event' in c.lower() or 'conflict' in c.lower()][:10]}")

# Identify ISO + year + IDP cols
iso_col = next((c for c in g.columns if "iso3" in c.lower().replace(" ", "")), None)
if not iso_col:
    iso_col = next((c for c in g.columns if "iso" in c.lower()), None)
year_col = next((c for c in g.columns if "year" in c.lower()), None)
idp_col = next((c for c in g.columns if "displacement" in c.lower() and "raw" not in c.lower()), None)
print(f"  Using cols: ISO={iso_col}, year={year_col}, IDP={idp_col}")

g[idp_col] = pd.to_numeric(g[idp_col], errors="coerce")
g_idp = g[g[year_col].between(2020, 2024)].groupby(iso_col)[idp_col].sum().to_dict()
agg_violence["conflict_idp"] = agg_violence.index.map(g_idp).fillna(0)
agg_violence["disp_per_fat"] = (agg_violence["conflict_idp"] / agg_violence["total_fat"]).clip(upper=5000)

print(f"\n  Joined records: {(agg_violence['conflict_idp'] > 0).sum()} countries with IDP > 0")

# ============================================================================
# Apply classifier (PRE_REG_018 rules)
# ============================================================================
print("\n[4/4] Applying classifier rules...")

def classify(row):
    s = row["state_share"]
    st = row["strife_share"]
    o = row["one_sided_share"]
    dpf = row["disp_per_fat"]
    adm = row["admin1_top3_share"]
    actor = row["top_actor_share"]

    # Type A
    if s >= 0.70 and st <= 0.10 and dpf <= 150 and adm >= 0.60:
        return "A formal-army"
    # Type B
    if o >= 0.40 and dpf >= 250 and adm >= 0.60 and actor >= 0.30:
        return "B predator-militia"
    # Type C
    if st >= 0.30 and adm < 0.60:
        return "C irregular insurgency"
    if 0.20 <= s <= 0.60 and 0.20 <= o <= 0.60 and adm < 0.60:
        return "C irregular insurgency"
    # Borderline cases
    if s >= 0.70 and adm < 0.60:
        return "A-diffuse (boundary)"
    if o >= 0.40 and dpf >= 250 and adm < 0.60:
        return "B-diffuse (boundary)"
    if st >= 0.30:
        return "C-concentrated (boundary)"
    return "D-or-UNCLASSIFIED"

agg_violence["type"] = agg_violence.apply(classify, axis=1)

# Sort by total fatalities
agg_violence = agg_violence.sort_values("total_fat", ascending=False)

# ============================================================================
# Display results
# ============================================================================
print("\n" + "=" * 80)
print("P4-C — Full corpus classification results")
print("=" * 80)
print(f"\n{'ISO':<5} {'Total fat':<10} {'State %':<8} {'Strife %':<9} {'1-sided %':<10} {'D/F':<8} {'Adm1 top3':<10} {'Actor':<8} {'IDP':<13} {'Type'}")
for iso, r in agg_violence.iterrows():
    print(f"{iso:<5} {r['total_fat']:<10,.0f} {100*r['state_share']:<8.1f} {100*r['strife_share']:<9.1f} {100*r['one_sided_share']:<10.1f} {r['disp_per_fat']:<8.0f} {100*r['admin1_top3_share']:<10.1f} {100*r['top_actor_share']:<8.1f} {r['conflict_idp']:<13,.0f} {r['type']}")

# Type counts
print("\n" + "=" * 80)
print("TYPE COUNTS")
print("=" * 80)
type_counts = agg_violence["type"].value_counts()
for t, c in type_counts.items():
    print(f"  {t}: {c}")

# Anchor case check (PRE_REG_018 Prediction set A)
print("\n" + "=" * 80)
print("ANCHOR CASE CHECK (PRE_REG_018 Prediction set A)")
print("=" * 80)
anchors = {
    "ETH": "A formal-army",
    "UKR": "A formal-army",
    "COD": "B predator-militia",
    "MLI": "C irregular insurgency",
    "BFA": "C irregular insurgency",
    "NER": "C irregular insurgency",
    "SOM": "C irregular insurgency",
    "SSD": "C-or-D1",  # ambiguous prediction
    "HTI": "B-or-D2",  # ambiguous prediction
}
print(f"\n{'ISO':<5} {'Actual':<28} {'Predicted':<22} {'Match'}")
matches = 0
data_valid = 0
for iso, pred in anchors.items():
    if iso in agg_violence.index:
        actual = agg_violence.loc[iso, "type"]
        if "-or-" in pred:
            options = pred.split("-or-")
            match = "YES" if any(opt in actual for opt in options) else "NO"
        else:
            match = "YES" if pred in actual else "NO"
        data_valid += 1
        if match == "YES":
            matches += 1
    else:
        actual = "INSUFFICIENT (<500 fat)"
        match = "DATA"
    print(f"{iso:<5} {actual:<28} {pred:<22} {match}")
print(f"\nAnchor matches: {matches}/{data_valid}")
print(f"F1 (>= 2 anchors fail): {'FIRED' if (data_valid - matches) >= 2 else 'NOT FIRED'}")

# Unclassified count
unclass = (agg_violence["type"].str.contains("UNCLASSIFIED")).sum()
print(f"\nUnclassified country-periods: {unclass}")
print(f"F2 (>= 5 unclassified): {'FIRED' if unclass >= 5 else 'NOT FIRED'}")

# Save results
agg_violence.to_parquet("D:/IDP/analysis/paper4_phase1_classifier_2026_05_27.parquet")
print(f"\nResults saved: D:/IDP/analysis/paper4_phase1_classifier_2026_05_27.parquet ({len(agg_violence)} country-periods)")
