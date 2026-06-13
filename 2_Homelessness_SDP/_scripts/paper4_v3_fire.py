"""
Paper 4 v3 — re-fire PRE_REG_018 v3 (5-type with sub-types + narrowed E + short-A).
Pre-reg locked 2026-05-27.
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
print("PAPER 4 v3 RE-FIRE — PRE_REG_018 v3 (refined classifier)")
print("=" * 80)

# Load
u = pd.read_csv(UCDP, usecols=[
    "country", "country_id", "year", "type_of_violence",
    "best", "adm_1", "side_a", "side_b"
])
u = u[u["year"].between(2020, 2024)]

COUNTRY_TO_ISO = {}
for c in u["country"].dropna().unique():
    try:
        co = pycountry.countries.search_fuzzy(c)[0]
        COUNTRY_TO_ISO[c] = co.alpha_3
    except Exception:
        COUNTRY_TO_ISO[c] = None
for k, v in {"DR Congo (Zaire)":"COD","Yemen (North Yemen)":"YEM","Russia (Soviet Union)":"RUS",
             "Cambodia (Kampuchea)":"KHM","Iran":"IRN","Vietnam (North Vietnam)":"VNM",
             "Madagascar (Malagasy)":"MDG","Myanmar (Burma)":"MMR","Macedonia, FYR":"MKD",
             "Bolivia":"BOL","Ivory Coast":"CIV","Türkiye":"TUR","Turkey":"TUR"}.items():
    COUNTRY_TO_ISO[k] = v
u["iso3"] = u["country"].map(COUNTRY_TO_ISO)

# Aggregate
agg = u.groupby(["iso3", "type_of_violence"])["best"].sum().unstack(fill_value=0)
agg.columns = ["state_based", "non_state", "one_sided"]
agg["total_fat"] = agg.sum(axis=1)
agg = agg[agg["total_fat"] >= 500]
agg["state_share"] = agg["state_based"] / agg["total_fat"]
agg["strife_share"] = agg["non_state"] / agg["total_fat"]
agg["one_sided_share"] = agg["one_sided"] / agg["total_fat"]

# Admin-1
adm1_dom = {}
for iso in agg.index:
    rows = u[u["iso3"] == iso]
    by_adm = rows.groupby("adm_1")["best"].sum().sort_values(ascending=False)
    adm1_dom[iso] = (by_adm.head(3).sum() / by_adm.sum()) if by_adm.sum() > 0 else 0
agg["admin1_top3_share"] = agg.index.map(adm1_dom)

# Top actor
top_actor = {}
for iso in agg.index:
    rows = u[(u["iso3"] == iso) & (u["type_of_violence"] == 3)]
    if len(rows) > 0:
        by_actor = rows.groupby("side_a")["best"].sum().sort_values(ascending=False)
        top_actor[iso] = (by_actor.iloc[0] / by_actor.sum()) if by_actor.sum() > 0 else 0
    else:
        top_actor[iso] = 0
agg["top_actor_share"] = agg.index.map(top_actor)

# GIDD
g = pd.read_excel(GIDD_CONF)
g.columns = [c.strip() for c in g.columns]
idp_col = "Conflict Stock Displacement"
g[idp_col] = pd.to_numeric(g[idp_col], errors="coerce")
g_idp = g[g["Year"].between(2020, 2024)].groupby("ISO3")[idp_col].sum().to_dict()
agg["conflict_idp"] = agg.index.map(g_idp).fillna(0)
agg["disp_per_fat"] = (agg["conflict_idp"] / agg["total_fat"]).clip(upper=5000)

def classify_v3(row):
    s = row["state_share"]; st = row["strife_share"]; o = row["one_sided_share"]
    dpf = row["disp_per_fat"]; adm = row["admin1_top3_share"]; actor = row["top_actor_share"]
    idp = row["conflict_idp"]; total = row["total_fat"]

    # Type A
    # A-strict
    if (s >= 0.70 and st <= 0.10 and dpf <= 150
        and (adm >= 0.60 or total >= 100_000)):
        return "A formal-army"
    # A-short
    if s >= 0.85 and st == 0 and dpf <= 200 and total >= 1_000:
        return "A formal-army (short-duration)"

    # Type B
    if o >= 0.40 and dpf >= 250 and adm >= 0.60 and actor >= 0.30:
        return "B predator-militia"

    # Type D
    if st >= 0.80 and dpf <= 100 and s <= 0.10:
        return "D criminal-violence"

    # Type E — NARROWED with organized opposition requirement
    if (s >= 0.55 and dpf >= 300 and idp >= 500_000
        and (st + o) >= 0.20):
        return "E civil-war-mass-displacement"

    # Type C — with sub-typing
    if st >= 0.20 and adm <= 0.85:
        if dpf <= 400:
            return "C1 low-DPF irregular"
        else:
            return "C2 high-DPF irregular"
    if 0.20 <= s <= 0.70 and o >= 0.15 and adm <= 0.85:
        return "C-mixed irregular"

    return "UNCLASSIFIED"

agg["type_v3"] = agg.apply(classify_v3, axis=1)
agg = agg.sort_values("total_fat", ascending=False)

print(f"\n{'ISO':<5} {'Total':<8} {'State%':<7} {'Strife%':<8} {'1-side%':<8} {'D/F':<7} {'Adm1%':<7} {'IDP':<11} {'v2 → v3'}")
v2 = pd.read_parquet("D:/IDP/analysis/paper4_phase2_classifier_v2_2026_05_27.parquet")
v2_types = v2["type_v2"].to_dict()

for iso, r in agg.iterrows():
    v2t = v2_types.get(iso, "?").split(" ")[0]
    v3t = r["type_v3"].split(" ")[0]
    arrow = "→" if v2t != v3t else "="
    print(f"{iso:<5} {r['total_fat']:<8,.0f} {100*r['state_share']:<7.1f} {100*r['strife_share']:<8.1f} {100*r['one_sided_share']:<8.1f} {r['disp_per_fat']:<7.0f} {100*r['admin1_top3_share']:<7.1f} {r['conflict_idp']:<11,.0f} {v2t} {arrow} {v3t}: {r['type_v3']}")

# Type counts v3
print("\n=== Type counts v3 ===")
type_counts = agg["type_v3"].value_counts()
for t, c in type_counts.items():
    print(f"  {t}: {c}")

# Anchor check
anchors_v3 = {
    "ETH": "A", "UKR": "A", "RUS": "A", "ISR": "A", "PAK": "A", "EGY": "A",
    "COD": "B", "MOZ": "B", "HTI": "B",
    "MEX": "D", "BRA": "D", "ECU": "D",
    "MLI": "C", "BFA": "C", "SOM": "C",  # v3 should route these to C
    "SYR": "E", "YEM": "E", "AFG": "E",
}
matches = 0; data_valid = 0
print("\n=== Anchor check v3 ===")
print(f"{'ISO':<5} {'Predicted':<10} {'Actual':<32} {'Match'}")
for iso, pred in anchors_v3.items():
    if iso in agg.index:
        actual = agg.loc[iso, "type_v3"]
        match = "YES" if actual.startswith(pred) else "NO"
        data_valid += 1
        if match == "YES":
            matches += 1
    else:
        actual = "INSUFFICIENT"
        match = "DATA"
    print(f"{iso:<5} {pred:<10} {actual:<32} {match}")
print(f"\nAnchor matches v3: {matches}/{data_valid}")
print(f"H1 (>= 17 of 18): {'SUPPORTED' if matches >= 17 else 'NOT MET'}")
print(f"F1 v3 (<17): {'FIRED' if matches < 17 else 'NOT FIRED'}")

# F2: BFA/SOM still E?
bfa_v3 = agg.loc["BFA", "type_v3"] if "BFA" in agg.index else "?"
som_v3 = agg.loc["SOM", "type_v3"] if "SOM" in agg.index else "?"
print(f"\nF2 (BFA/SOM still E): BFA={bfa_v3}, SOM={som_v3}")
print(f"  Status: {'FIRED' if 'E' in bfa_v3 or 'E' in som_v3 else 'NOT FIRED'}")

# F3: AZE 2020 in v3 — would need historical decomp; check 2020-2024 acute
aze_v3 = agg.loc["AZE", "type_v3"] if "AZE" in agg.index else "?"
print(f"F3 (AZE 2020-2024 acute classification): AZE={aze_v3}")

# F4: C sub-typing
c1_count = (agg["type_v3"].str.startswith("C1")).sum()
c2_count = (agg["type_v3"].str.startswith("C2")).sum()
print(f"F4 (C sub-typing): C1={c1_count}, C2={c2_count}")
print(f"  Status: {'FIRED' if c1_count == 0 or c2_count == 0 else 'NOT FIRED'}")

# F5: over-correction
unclass = (agg["type_v3"] == "UNCLASSIFIED").sum()
print(f"\nF5 (>=5 unclassified): {unclass}")
print(f"  Status: {'FIRED' if unclass >= 5 else 'NOT FIRED'}")

# Save
agg.to_parquet("D:/IDP/analysis/paper4_v3_classifier_2026_05_27.parquet")
print("\nResults saved.")
