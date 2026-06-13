"""Sahel stratified panel + first-look summary.

Stratifications:
- Country: BFA, MLI, BEN, NER
- Period: pre-Sahel-crisis (1998-2013), early (2014-2019), acute (2020-2024)
- Cause:
  * Conflict-displacement total (GIDD)
  * War (UCDP type_of_violence=1, state-based armed conflict)
  * Strife (UCDP type_of_violence=2, non-state communal violence)
  * One-sided violence on civilians (UCDP type_of_violence=3)
  * Intrastate vs Interstate (UCDP conflict_type)
  * Government as side_a vs Rebel groups
  * Disaster-displacement by hazard (GIDD Disasters: flood, drought, storm, etc.)
  * Food insecurity phase (HAPI food-security, IPC phase 3+/4/5)
"""
import json
import pathlib
import time
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np

ROOT = pathlib.Path("D:/IDP")
DATA = ROOT / "data"
OUT = ROOT / "analysis"
OUT.mkdir(parents=True, exist_ok=True)

SAHEL_ISO3 = ["BFA", "MLI", "BEN", "NER"]
SAHEL_NAMES = {"BFA": "Burkina Faso", "MLI": "Mali", "BEN": "Benin", "NER": "Niger"}
YEARS = list(range(1998, 2025))

def assign_period(y):
    if y <= 2013: return "pre_crisis_1998_2013"
    if y <= 2019: return "early_sahel_2014_2019"
    return "acute_sahel_2020_2024"

print(f"[{time.strftime('%H:%M:%S')}] === Sahel stratified panel ===")

panel = pd.DataFrame([(iso, y) for iso in SAHEL_ISO3 for y in YEARS], columns=["iso3", "year"])
panel["period"] = panel["year"].apply(assign_period)

# === GIDD displacement (annual conflict + disaster) ===
print("[1] GIDD annual displacement")
gidd = pd.read_excel(DATA / "idmc_gidd" / "IDMC_GIDD_Conflict_Violence_Disasters.xlsx",
                      sheet_name="1_Displacement_data")
gidd = gidd[gidd["ISO3"].isin(SAHEL_ISO3)].copy()
gidd = gidd.rename(columns={
    "ISO3": "iso3", "Year": "year",
    "Conflict Internal Displacements": "gidd_conflict_idp_new",
    "Conflict Stock Displacement": "gidd_conflict_idp_stock",
    "Disaster Internal Displacements": "gidd_disaster_idp_new",
    "Disaster Stock Displacement": "gidd_disaster_idp_stock",
})[["iso3", "year", "gidd_conflict_idp_new", "gidd_conflict_idp_stock",
    "gidd_disaster_idp_new", "gidd_disaster_idp_stock"]]
panel = panel.merge(gidd, on=["iso3", "year"], how="left")
print(f"  GIDD: {gidd.shape[0]} country-year rows for Sahel")

# === GIDD Disasters — hazard-type breakdown ===
print("[2] GIDD Disasters (hazard-type)")
gdis = pd.read_excel(DATA / "idmc_gidd" / "IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx",
                      sheet_name="1_Disaster_Displacement_data")
gdis = gdis[gdis["ISO3"].isin(SAHEL_ISO3)].copy()
gdis_agg = gdis.groupby(["ISO3", "Year", "Hazard Type"])["Disaster Internal Displacements"].sum().unstack(fill_value=0)
gdis_agg.columns = [f"disaster_{c.lower().replace(' ', '_').replace('/', '_')}" for c in gdis_agg.columns]
gdis_agg = gdis_agg.reset_index().rename(columns={"ISO3": "iso3", "Year": "year"})
panel = panel.merge(gdis_agg, on=["iso3", "year"], how="left")
print(f"  GIDD Disasters: {gdis_agg.shape[0]} rows × {gdis_agg.shape[1]-2} hazard cols")

# === UCDP-GED — conflict stratification ===
print("[3] UCDP-GED stratification")
ged = pd.read_csv(DATA / "ucdp" / "GEDEvent_v25_1.csv", low_memory=False)
name_to_iso = {v: k for k, v in SAHEL_NAMES.items()}
ged = ged[ged["country"].isin(SAHEL_NAMES.values())].copy()
ged["iso3"] = ged["country"].map(name_to_iso)

# Type-of-violence breakdown: 1=state-based (war), 2=non-state (strife), 3=one-sided
tov_map = {1: "war_state_based", 2: "strife_non_state", 3: "one_sided_civilians"}
ged["violence_type"] = ged["type_of_violence"].map(tov_map)
tov_pivot = ged.groupby(["iso3", "year", "violence_type"]).agg(
    fatalities=("best", "sum"), events=("best", "count")
).reset_index()
for vt in tov_map.values():
    sub = tov_pivot[tov_pivot["violence_type"] == vt]
    panel = panel.merge(
        sub[["iso3", "year", "fatalities", "events"]].rename(
            columns={"fatalities": f"ucdp_{vt}_fatal", "events": f"ucdp_{vt}_events"}
        ),
        on=["iso3", "year"], how="left",
    )

# Government vs rebels (side_a often contains "Government of X")
ged["actor_is_govt"] = ged["side_a"].fillna("").str.contains("Government", case=False)
actor_agg = ged.groupby(["iso3", "year", "actor_is_govt"])["best"].sum().unstack(fill_value=0)
if True in actor_agg.columns:
    actor_agg = actor_agg.rename(columns={True: "fatal_govt_involved", False: "fatal_non_govt"})
    actor_agg = actor_agg.reset_index()
    for col in ["fatal_govt_involved", "fatal_non_govt"]:
        if col in actor_agg.columns:
            panel = panel.merge(actor_agg[["iso3", "year", col]], on=["iso3", "year"], how="left")

# Intrastate vs interstate (conflict_dset_id 1=intrastate (civil), 2+=interstate)
# Actually UCDP-GED uses 'type_of_violence' (1=state-based) combined with side info
# Simpler: count fatalities by whether involved a state vs only non-state actors
ged["any_state_involved"] = ged["side_a"].fillna("").str.contains("Government", case=False) | \
                              ged["side_b"].fillna("").str.contains("Government", case=False)
state_agg = ged.groupby(["iso3", "year", "any_state_involved"])["best"].sum().unstack(fill_value=0)
if True in state_agg.columns:
    state_agg = state_agg.rename(columns={True: "fatal_state_involved", False: "fatal_only_non_state"})
    state_agg = state_agg.reset_index()
    for col in ["fatal_state_involved", "fatal_only_non_state"]:
        if col in state_agg.columns:
            panel = panel.merge(state_agg[["iso3", "year", col]], on=["iso3", "year"], how="left")

print(f"  UCDP-GED Sahel events: {len(ged)} -> stratified into "
      f"{len([c for c in panel.columns if c.startswith('ucdp_') or c.startswith('fatal_')])} columns")

# === HAPI food security (IPC phase) ===
print("[4] HAPI food security (IPC phase)")
try:
    fs = json.load(open(DATA / "hdx_hapi" / "food_security" / "page_0.json"))
    fs_data = fs.get("data", [])
    rows = []
    for r in fs_data:
        iso3 = r.get("location_code", "")
        if iso3 not in SAHEL_ISO3:
            continue
        y = (r.get("reference_period_start", "") or "")[:4]
        if not y.isdigit():
            continue
        rows.append({
            "iso3": iso3, "year": int(y),
            "ipc_phase": r.get("ipc_phase", ""),
            "pop_in_phase": r.get("population_in_phase", 0) or 0,
        })
    if rows:
        fs_df = pd.DataFrame(rows)
        # Max phase reached + population in Crisis+ (3+) per year
        fs_agg = fs_df.groupby(["iso3", "year"]).agg(
            ipc_max_phase=("ipc_phase", lambda s: pd.to_numeric(s, errors="coerce").max()),
            pop_in_crisis_plus=("pop_in_phase", "sum"),
        ).reset_index()
        panel = panel.merge(fs_agg, on=["iso3", "year"], how="left")
        print(f"  HAPI food: {fs_agg.shape[0]} Sahel rows")
    else:
        print(f"  HAPI food: no Sahel rows")
except Exception as e:
    print(f"  FAIL {type(e).__name__}: {e}")

# === V-Dem + WB WDI (already worked, just re-merge select) ===
print("[5] V-Dem + WDI")
vdem = pd.read_csv(DATA / "vdem" / "vdem_vdem.csv",
                    usecols=["country_text_id", "year", "v2x_libdem", "v2x_polyarchy",
                             "v2x_civlib", "v2x_corr"], low_memory=False)
vdem = vdem[vdem["country_text_id"].isin(SAHEL_ISO3)].rename(columns={
    "country_text_id": "iso3", "v2x_libdem": "vdem_libdem",
    "v2x_polyarchy": "vdem_polyarchy", "v2x_civlib": "vdem_civlib", "v2x_corr": "vdem_corr",
})
panel = panel.merge(vdem, on=["iso3", "year"], how="left")

wdi = pd.read_csv(DATA / "wb_wdi" / "extracted" / "WDICSV.csv", low_memory=False)
wdi_indicators = {"NY.GDP.PCAP.CD": "wdi_gdp_pcap", "SP.DYN.IMRT.IN": "wdi_infant_mort",
                   "SP.POP.TOTL": "wdi_pop_total", "SI.POV.GINI": "wdi_gini"}
sub = wdi[wdi["Country Code"].isin(SAHEL_ISO3) & wdi["Indicator Code"].isin(wdi_indicators)].copy()
year_cols = [c for c in sub.columns if c.isdigit() and 1998 <= int(c) <= 2024]
rows = []
for _, r in sub.iterrows():
    for yc in year_cols:
        v = r[yc]
        if pd.notna(v):
            rows.append({"iso3": r["Country Code"], "year": int(yc),
                         "indicator": wdi_indicators[r["Indicator Code"]], "value": v})
if rows:
    wdi_long = pd.DataFrame(rows)
    wdi_wide = wdi_long.pivot_table(index=["iso3", "year"], columns="indicator", values="value").reset_index()
    panel = panel.merge(wdi_wide, on=["iso3", "year"], how="left")

# Save panel
target = OUT / "sahel_stratified_panel_2026_05_21.parquet"
panel.to_parquet(target)
print(f"\n[{time.strftime('%H:%M:%S')}] === panel saved ===")
print(f"  {target}")
print(f"  shape: {panel.shape}")

# === FIRST LOOK: period × country × cause displacement ===
print("\n" + "="*70)
print("FIRST LOOK — period × country × displacement cause")
print("="*70)

cause_summary = panel.groupby(["period", "iso3"]).agg(
    conflict_displaced_total=("gidd_conflict_idp_new", "sum"),
    disaster_displaced_total=("gidd_disaster_idp_new", "sum"),
    war_fatalities=("ucdp_war_state_based_fatal", "sum"),
    strife_fatalities=("ucdp_strife_non_state_fatal", "sum"),
    one_sided_fatalities=("ucdp_one_sided_civilians_fatal", "sum"),
    pop_food_crisis=("pop_in_crisis_plus", "sum"),
).reset_index()
cause_summary["conflict_displaced_total"] = cause_summary["conflict_displaced_total"].astype("Int64")
cause_summary["disaster_displaced_total"] = cause_summary["disaster_displaced_total"].astype("Int64")
cause_summary["war_fatalities"] = cause_summary["war_fatalities"].fillna(0).astype("Int64")
cause_summary["strife_fatalities"] = cause_summary["strife_fatalities"].fillna(0).astype("Int64")
cause_summary["one_sided_fatalities"] = cause_summary["one_sided_fatalities"].fillna(0).astype("Int64")
cause_summary["pop_food_crisis"] = cause_summary["pop_food_crisis"].fillna(0).astype("Int64")

print("\nDISPLACEMENT TOTALS by period × country (GIDD)")
print("Conflict = wars + civil violence; Disaster = natural hazards")
print()
print(cause_summary[["period", "iso3", "conflict_displaced_total", "disaster_displaced_total"]].to_string(index=False))

print("\nFATALITIES by period × country × violence type (UCDP-GED)")
print("war_state_based = governments vs organized groups (incl. JNIM, ISGS)")
print("strife_non_state = inter-communal / non-state violence")
print("one_sided_civilians = government or non-state attacks on civilians")
print()
print(cause_summary[["period", "iso3", "war_fatalities", "strife_fatalities", "one_sided_fatalities"]].to_string(index=False))

# === Hazard-type disaster breakdown ===
print("\n" + "="*70)
print("DISASTER displacement by hazard type (GIDD Disasters), acute period 2020-2024")
print("="*70)
acute = panel[panel["period"] == "acute_sahel_2020_2024"]
hazard_cols = [c for c in acute.columns if c.startswith("disaster_")]
if hazard_cols:
    haz_summary = acute.groupby("iso3")[hazard_cols].sum().T.astype("Int64")
    haz_summary = haz_summary.loc[haz_summary.sum(axis=1) > 0]
    print(haz_summary.to_string())

# === Year-by-year acute period for the load-bearing columns ===
print("\n" + "="*70)
print("ACUTE PERIOD year × country (2020-2024)")
print("="*70)
acute_cols = ["iso3", "year", "gidd_conflict_idp_new", "gidd_disaster_idp_new",
              "ucdp_war_state_based_fatal", "ucdp_strife_non_state_fatal",
              "ucdp_one_sided_civilians_fatal", "vdem_libdem"]
acute_view = panel[panel["period"] == "acute_sahel_2020_2024"][acute_cols].sort_values(["iso3", "year"])
print(acute_view.to_string(index=False))

print(f"\n[{time.strftime('%H:%M:%S')}] complete")
