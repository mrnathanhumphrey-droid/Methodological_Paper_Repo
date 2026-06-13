"""Build a stratified country-year panel for any regional cluster.

Usage: python build_regional_panel.py <cluster_name> <ISO3_1> <ISO3_2> ...

Same stratification logic as build_sahel_stratified.py: GIDD + UCDP type-of-
violence + GIDD Disasters hazard + HAPI food security + V-Dem + WB WDI.

Period bins are global (1998-2013 / 2014-2019 / 2020-2024) so panels can be
compared across regions.
"""
import json
import pathlib
import sys
import time
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np

if len(sys.argv) < 3:
    print("Usage: python build_regional_panel.py <cluster_name> <ISO3_1> <ISO3_2> ...")
    sys.exit(1)

CLUSTER = sys.argv[1]
ISO3_LIST = sys.argv[2:]

ROOT = pathlib.Path("D:/IDP")
DATA = ROOT / "data"
OUT = ROOT / "analysis"
OUT.mkdir(parents=True, exist_ok=True)
YEARS = list(range(1998, 2025))


def assign_period(y):
    if y <= 2013: return "pre_crisis_1998_2013"
    if y <= 2019: return "early_2014_2019"
    return "acute_2020_2024"


print(f"[{time.strftime('%H:%M:%S')}] === Building {CLUSTER} panel for {ISO3_LIST} ===")

panel = pd.DataFrame([(iso, y) for iso in ISO3_LIST for y in YEARS], columns=["iso3", "year"])
panel["period"] = panel["year"].apply(assign_period)
panel["cluster"] = CLUSTER

# === GIDD displacement ===
print("[1] GIDD displacement")
gidd = pd.read_excel(DATA / "idmc_gidd" / "IDMC_GIDD_Conflict_Violence_Disasters.xlsx",
                      sheet_name="1_Displacement_data")
gidd = gidd[gidd["ISO3"].isin(ISO3_LIST)].copy()
gidd = gidd.rename(columns={
    "ISO3": "iso3", "Year": "year",
    "Conflict Internal Displacements": "gidd_conflict_idp_new",
    "Conflict Stock Displacement": "gidd_conflict_idp_stock",
    "Disaster Internal Displacements": "gidd_disaster_idp_new",
    "Disaster Stock Displacement": "gidd_disaster_idp_stock",
})[["iso3", "year", "gidd_conflict_idp_new", "gidd_conflict_idp_stock",
    "gidd_disaster_idp_new", "gidd_disaster_idp_stock"]]
panel = panel.merge(gidd, on=["iso3", "year"], how="left")
print(f"  GIDD: {gidd.shape[0]} country-year rows")

# === GIDD Disasters hazard ===
print("[2] GIDD Disasters hazard")
gdis = pd.read_excel(DATA / "idmc_gidd" / "IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx",
                      sheet_name="1_Disaster_Displacement_data")
gdis = gdis[gdis["ISO3"].isin(ISO3_LIST)].copy()
gdis_agg = gdis.groupby(["ISO3", "Year", "Hazard Type"])["Disaster Internal Displacements"].sum().unstack(fill_value=0)
gdis_agg.columns = [f"disaster_{c.lower().replace(' ', '_').replace('/', '_')}" for c in gdis_agg.columns]
gdis_agg = gdis_agg.reset_index().rename(columns={"ISO3": "iso3", "Year": "year"})
panel = panel.merge(gdis_agg, on=["iso3", "year"], how="left")
print(f"  Disasters: {gdis_agg.shape[0]} rows x {gdis_agg.shape[1]-2} hazard cols")

# === UCDP-GED stratification ===
print("[3] UCDP-GED")
ged = pd.read_csv(DATA / "ucdp" / "GEDEvent_v25_1.csv", low_memory=False)
import pycountry
name_to_iso = {c.name: c.alpha_3 for c in pycountry.countries}
# UCDP-GED uses some non-canonical names; explicit overrides
UCDP_NAME_OVERRIDES = {
    "Syria": "SYR",
    "Yemen": "YEM",
    "Yemen (North Yemen)": "YEM",
    "DR Congo (Zaire)": "COD",
    "Myanmar (Burma)": "MMR",
    "Cambodia (Kampuchea)": "KHM",
    "Russia (Soviet Union)": "RUS",
    "Madagascar (Malagasy)": "MDG",
    "Iran": "IRN",
    "Vietnam (North Vietnam)": "VNM",
    "South Korea": "KOR",
    "North Korea": "PRK",
    "Bolivia": "BOL",
    "Tanzania": "TZA",
    "Moldova": "MDA",
    "Laos": "LAO",
    "Venezuela": "VEN",
    "Brunei": "BRN",
}
name_to_iso.update(UCDP_NAME_OVERRIDES)
ged["iso3"] = ged["country"].map(name_to_iso)
ged = ged[ged["iso3"].isin(ISO3_LIST)].copy()

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

ged["any_state_involved"] = ged["side_a"].fillna("").str.contains("Government", case=False) | \
                              ged["side_b"].fillna("").str.contains("Government", case=False)
state_agg = ged.groupby(["iso3", "year", "any_state_involved"])["best"].sum().unstack(fill_value=0)
if True in state_agg.columns:
    state_agg = state_agg.rename(columns={True: "fatal_state_involved", False: "fatal_only_non_state"})
    state_agg = state_agg.reset_index()
    for col in ["fatal_state_involved", "fatal_only_non_state"]:
        if col in state_agg.columns:
            panel = panel.merge(state_agg[["iso3", "year", col]], on=["iso3", "year"], how="left")
print(f"  UCDP-GED events for cluster: {len(ged)}")

# === HAPI food security ===
print("[4] HAPI food security")
try:
    fs = json.load(open(DATA / "hdx_hapi" / "food_security" / "page_0.json"))
    rows = []
    for r in fs.get("data", []):
        iso3 = r.get("location_code", "")
        if iso3 not in ISO3_LIST: continue
        y = (r.get("reference_period_start", "") or "")[:4]
        if not y.isdigit(): continue
        rows.append({"iso3": iso3, "year": int(y),
                     "ipc_phase": r.get("ipc_phase", ""),
                     "pop_in_phase": r.get("population_in_phase", 0) or 0})
    if rows:
        fs_df = pd.DataFrame(rows)
        fs_agg = fs_df.groupby(["iso3", "year"]).agg(
            ipc_max_phase=("ipc_phase", lambda s: pd.to_numeric(s, errors="coerce").max()),
            pop_in_crisis_plus=("pop_in_phase", "sum"),
        ).reset_index()
        panel = panel.merge(fs_agg, on=["iso3", "year"], how="left")
        print(f"  HAPI food: {fs_agg.shape[0]} rows")
except Exception as e:
    print(f"  FAIL {type(e).__name__}")

# === V-Dem + WDI ===
print("[5] V-Dem + WDI")
vdem = pd.read_csv(DATA / "vdem" / "vdem_vdem.csv",
                    usecols=["country_text_id", "year", "v2x_libdem", "v2x_polyarchy", "v2x_civlib", "v2x_corr"],
                    low_memory=False)
vdem = vdem[vdem["country_text_id"].isin(ISO3_LIST)].rename(columns={
    "country_text_id": "iso3", "v2x_libdem": "vdem_libdem",
    "v2x_polyarchy": "vdem_polyarchy", "v2x_civlib": "vdem_civlib", "v2x_corr": "vdem_corr",
})
panel = panel.merge(vdem, on=["iso3", "year"], how="left")

wdi = pd.read_csv(DATA / "wb_wdi" / "extracted" / "WDICSV.csv", low_memory=False)
wdi_indicators = {"NY.GDP.PCAP.CD": "wdi_gdp_pcap", "SP.DYN.IMRT.IN": "wdi_infant_mort",
                   "SP.POP.TOTL": "wdi_pop_total", "SI.POV.GINI": "wdi_gini"}
sub = wdi[wdi["Country Code"].isin(ISO3_LIST) & wdi["Indicator Code"].isin(wdi_indicators)].copy()
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

target = OUT / f"{CLUSTER}_stratified_panel_2026_05_21.parquet"
panel.to_parquet(target)
print(f"\n[{time.strftime('%H:%M:%S')}] panel saved: {target}")
print(f"  shape: {panel.shape}")

# === First look summary ===
print(f"\n=== {CLUSTER} period x country x cause ===")
agg = panel.groupby(["period", "iso3"]).agg(
    conflict_disp=("gidd_conflict_idp_new", "sum"),
    disaster_disp=("gidd_disaster_idp_new", "sum"),
    war_fatal=("ucdp_war_state_based_fatal", "sum"),
    strife_fatal=("ucdp_strife_non_state_fatal", "sum"),
    one_sided_fatal=("ucdp_one_sided_civilians_fatal", "sum"),
).reset_index()
for col in ["conflict_disp", "disaster_disp", "war_fatal", "strife_fatal", "one_sided_fatal"]:
    agg[col] = agg[col].fillna(0).astype("Int64")
print(agg.to_string(index=False))

print(f"\n=== {CLUSTER} V-Dem libdem trajectory ===")
lib = panel.pivot_table(index="iso3", columns="year", values="vdem_libdem", aggfunc="first")
for y in [2018, 2020, 2024]:
    if y in lib.columns:
        for iso in ISO3_LIST:
            if iso in lib.index:
                v = lib.loc[iso, y]
                print(f"  {iso} {y}: {v:.3f}" if pd.notna(v) else f"  {iso} {y}: NaN")

# === Hazard breakdown acute ===
print(f"\n=== {CLUSTER} disaster hazard types (acute 2020-2024) ===")
acute = panel[panel["period"] == "acute_2020_2024"]
haz_cols = [c for c in acute.columns if c.startswith("disaster_")]
if haz_cols:
    haz = acute.groupby("iso3")[haz_cols].sum().T
    haz = haz.loc[haz.sum(axis=1) > 0].astype("Int64")
    print(haz.to_string())

print(f"\n[{time.strftime('%H:%M:%S')}] complete")
