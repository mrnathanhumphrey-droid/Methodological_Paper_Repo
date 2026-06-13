"""
Paper 4 Phase 3 — fire PRE_REG_021 within-country phase decomposition (IRQ + ARM-AZE + NGA).
Pre-reg PRE_REG_021 locked 2026-05-27.
Apply PRE_REG_018 v2 classifier to historical phases per country.
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
print("PAPER 4 PHASE 3 — Within-country phase decomposition (PRE_REG_021)")
print("=" * 80)

# Load UCDP-GED full historical 1989-2024
print("\n[1/4] Loading UCDP-GED v25 1989-2024...")
u = pd.read_csv(UCDP, usecols=[
    "country", "country_id", "year", "type_of_violence",
    "best", "adm_1", "side_a", "side_b"
])
print(f"  Full UCDP-GED v25: {len(u)} events; years {u['year'].min()}-{u['year'].max()}")

# Country to ISO3
COUNTRY_TO_ISO = {}
for c in u["country"].dropna().unique():
    try:
        co = pycountry.countries.search_fuzzy(c)[0]
        COUNTRY_TO_ISO[c] = co.alpha_3
    except Exception:
        COUNTRY_TO_ISO[c] = None
overrides = {
    "DR Congo (Zaire)": "COD", "Yemen (North Yemen)": "YEM",
    "Russia (Soviet Union)": "RUS", "Cambodia (Kampuchea)": "KHM",
    "Iran": "IRN", "Vietnam (North Vietnam)": "VNM",
    "Madagascar (Malagasy)": "MDG", "Myanmar (Burma)": "MMR",
    "Macedonia, FYR": "MKD", "Bolivia": "BOL", "Ivory Coast": "CIV",
    "Türkiye": "TUR", "Turkey": "TUR",
}
for k, v in overrides.items():
    COUNTRY_TO_ISO[k] = v
u["iso3"] = u["country"].map(COUNTRY_TO_ISO)

# Load GIDD conflict displacement (historical coverage spotty for pre-2009)
print("[2/4] Loading GIDD conflict-displacement...")
g = pd.read_excel(GIDD_CONF)
g.columns = [c.strip() for c in g.columns]
idp_col = "Conflict Stock Displacement"
g[idp_col] = pd.to_numeric(g[idp_col], errors="coerce")

# Define phases per country
phases = {
    "IRQ": [
        ("2003 interstate", 2003, 2003),
        ("2004-2011 insurgency", 2004, 2011),
        ("2012-2017 ISIS war", 2012, 2017),
        ("2018-2024 post-ISIS", 2018, 2024),
    ],
    "AZE": [
        ("1992-1994 First Karabakh", 1992, 1994),
        ("2020 44-day war", 2020, 2020),
        ("2023 AZE offensive", 2023, 2023),
    ],
    "NGA": [
        ("2009-2014 BH insurgency", 2009, 2014),
        ("2015-2017 BH territorial", 2015, 2017),
        ("2018-2024 post-territorial", 2018, 2024),
    ],
}

def classify_v2(state_share, strife_share, one_sided_share, dpf, adm1_top3, top_actor, idp, total_fat):
    s = state_share; st = strife_share; o = one_sided_share
    if s >= 0.70 and st <= 0.10 and dpf <= 150 and (adm1_top3 >= 0.60 or total_fat >= 100_000):
        return "A formal-army"
    if o >= 0.40 and dpf >= 250 and adm1_top3 >= 0.60 and top_actor >= 0.30:
        return "B predator-militia"
    if st >= 0.80 and dpf <= 100 and s <= 0.10:
        return "D criminal-violence"
    if s >= 0.55 and dpf >= 300 and idp >= 500_000:
        return "E civil-war-mass-displacement"
    if st >= 0.30 and adm1_top3 <= 0.85:
        return "C irregular insurgency"
    if 0.20 <= s <= 0.70 and 0.20 <= o <= 0.60 and adm1_top3 <= 0.85:
        return "C irregular insurgency"
    if 100 <= dpf <= 300 and top_actor < 0.50:
        return "C irregular insurgency"
    return "UNCLASSIFIED"

def compute_phase_features(iso, y_start, y_end):
    rows = u[(u["iso3"] == iso) & (u["year"].between(y_start, y_end))]
    if len(rows) == 0:
        return None
    total = rows["best"].sum()
    state = rows[rows["type_of_violence"] == 1]["best"].sum()
    strife = rows[rows["type_of_violence"] == 2]["best"].sum()
    one_sided = rows[rows["type_of_violence"] == 3]["best"].sum()

    by_adm = rows.groupby("adm_1")["best"].sum().sort_values(ascending=False)
    adm1_top3 = (by_adm.head(3).sum() / by_adm.sum()) if by_adm.sum() > 0 else 0

    one_sided_rows = rows[rows["type_of_violence"] == 3]
    if len(one_sided_rows) > 0:
        by_actor = one_sided_rows.groupby("side_a")["best"].sum().sort_values(ascending=False)
        top_actor = (by_actor.iloc[0] / by_actor.sum()) if by_actor.sum() > 0 else 0
    else:
        top_actor = 0

    # GIDD IDP for the period
    g_period = g[(g["ISO3"] == iso) & (g["Year"].between(y_start, y_end))]
    idp = g_period[idp_col].sum() if len(g_period) > 0 else 0

    return {
        "total_fat": total,
        "state_share": state / total if total > 0 else 0,
        "strife_share": strife / total if total > 0 else 0,
        "one_sided_share": one_sided / total if total > 0 else 0,
        "admin1_top3_share": adm1_top3,
        "top_actor_share": top_actor,
        "conflict_idp": idp,
        "disp_per_fat": min(idp / total, 5000) if total > 0 else 0,
    }

print("\n[3/4] Computing phase classifications...")
print()

results = {}
predictions = {
    ("IRQ", "2003 interstate"): "A",
    ("IRQ", "2004-2011 insurgency"): "C or E",
    ("IRQ", "2012-2017 ISIS war"): "B or E",
    ("IRQ", "2018-2024 post-ISIS"): "E",
    ("AZE", "1992-1994 First Karabakh"): "A",
    ("AZE", "2020 44-day war"): "A",
    ("AZE", "2023 AZE offensive"): "A",
    ("NGA", "2009-2014 BH insurgency"): "C",
    ("NGA", "2015-2017 BH territorial"): "B",
    ("NGA", "2018-2024 post-territorial"): "C or E",
}

for iso, phase_list in phases.items():
    print(f"\n=== {iso} ===")
    print(f"{'Phase':<32} {'Total':<8} {'State%':<7} {'Strife%':<8} {'1-side%':<8} {'D/F':<6} {'Adm1%':<7} {'IDP':<11} {'Type':<35} {'Pred':<8} {'Match'}")
    results[iso] = []
    for phase_name, y_start, y_end in phase_list:
        feat = compute_phase_features(iso, y_start, y_end)
        if feat is None:
            print(f"{phase_name:<32} -- NO UCDP DATA --")
            results[iso].append({"phase": phase_name, "type": "NO DATA", "match": "DATA"})
            continue
        ftype = classify_v2(
            feat["state_share"], feat["strife_share"], feat["one_sided_share"],
            feat["disp_per_fat"], feat["admin1_top3_share"], feat["top_actor_share"],
            feat["conflict_idp"], feat["total_fat"]
        )
        pred = predictions[(iso, phase_name)]
        # Match if classified type starts with predicted letter
        if "or" in pred:
            options = [p.strip() for p in pred.split("or")]
            match = "YES" if any(ftype.startswith(opt) for opt in options) else "NO"
        else:
            match = "YES" if ftype.startswith(pred) else "NO"
        print(f"{phase_name:<32} {feat['total_fat']:<8,.0f} {100*feat['state_share']:<7.1f} {100*feat['strife_share']:<8.1f} {100*feat['one_sided_share']:<8.1f} {feat['disp_per_fat']:<6.0f} {100*feat['admin1_top3_share']:<7.1f} {feat['conflict_idp']:<11,.0f} {ftype:<35} {pred:<8} {match}")
        results[iso].append({"phase": phase_name, "type": ftype, "predicted": pred, "match": match, **feat})

# Falsifier check
print("\n" + "=" * 80)
print("FALSIFIER CHECK (PRE_REG_021)")
print("=" * 80)

# F1: IRQ same type all 4 phases?
irq_types = [r["type"] for r in results["IRQ"] if r["type"] != "NO DATA"]
irq_same = len(set(irq_types)) == 1
print(f"\nF1 (IRQ same type all phases): {'FIRED' if irq_same else 'NOT FIRED'} (types: {irq_types})")

# F2: ARM-AZE different types?
aze_types = [r["type"] for r in results["AZE"] if r["type"] != "NO DATA"]
aze_diff = len(set(aze_types)) > 1
print(f"F2 (ARM-AZE different types): {'FIRED' if aze_diff else 'NOT FIRED'} (types: {aze_types})")

# F3: NGA same type all phases?
nga_types = [r["type"] for r in results["NGA"] if r["type"] != "NO DATA"]
nga_same = len(set(nga_types)) == 1
print(f"F3 (NGA same type all phases): {'FIRED' if nga_same else 'NOT FIRED'} (types: {nga_types})")

# F4 LOAD-BEARING: all 3 countries stable across phases?
all_stable = irq_same and (not aze_diff) and nga_same
print(f"\nF4 LOAD-BEARING (all 3 stable across phases): {'FIRED — framework walked back' if all_stable else 'NOT FIRED — within-country type-shift confirmed'}")

# F5: IRQ 2003 not Type A?
irq_2003 = results["IRQ"][0]["type"] if results["IRQ"][0]["type"] != "NO DATA" else None
print(f"F5 (IRQ 2003 not Type A): {'FIRED' if irq_2003 and not irq_2003.startswith('A') else 'NOT FIRED'} (IRQ 2003 = {irq_2003})")

# Match summary
irq_match = sum(1 for r in results["IRQ"] if r["match"] == "YES")
aze_match = sum(1 for r in results["AZE"] if r["match"] == "YES")
nga_match = sum(1 for r in results["NGA"] if r["match"] == "YES")
print(f"\nMatch summary:")
print(f"  IRQ: {irq_match}/4 phases match prediction (threshold: >=3)")
print(f"  AZE: {aze_match}/3 phases match (threshold: >=2)")
print(f"  NGA: {nga_match}/3 phases match (threshold: >=2)")

# H1 load-bearing: at least one country shows shift
type_shifts = [
    ("IRQ", len(set(irq_types)) > 1),
    ("NGA", len(set(nga_types)) > 1),
]
shifts = [c for c, s in type_shifts if s]
print(f"\nH1 LOAD-BEARING: type-shifts visible in {shifts}")
print(f"  Status: {'SUPPORTED' if len(shifts) >= 1 else 'WALKED BACK'}")

# Save
import json
out = {iso: results[iso] for iso in results}
Path("D:/IDP/analysis/paper4_phase3_within_country_2026_05_27.json").write_text(
    json.dumps(out, indent=2, default=str), encoding="utf-8"
)
print(f"\nResults saved: D:/IDP/analysis/paper4_phase3_within_country_2026_05_27.json")
