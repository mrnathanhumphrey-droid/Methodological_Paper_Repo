"""Tier C dig: 5 anomaly patterns, sub-period + actor + admin-1 decomposition.

Outputs everything to stdout (captured to dig_tier_c_2026_05_25.log) and
writes per-pattern dig notes as well.
"""
import json
import pathlib
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np

ROOT = pathlib.Path("D:/IDP")
DATA = ROOT / "data"

# Load once
print("[load] UCDP-GED")
ged = pd.read_csv(DATA / "ucdp" / "GEDEvent_v25_1.csv", low_memory=False)
print(f"  GED: {len(ged):,} events")

print("[load] GIDD displacement")
gidd_conf = pd.read_excel(DATA / "idmc_gidd" / "IDMC_GIDD_Conflict_Violence_Disasters.xlsx",
                          sheet_name="1_Displacement_data")
gidd_dis = pd.read_excel(DATA / "idmc_gidd" / "IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx",
                         sheet_name="1_Disaster_Displacement_data")

print("[load] EM-DAT")
emdat = pd.read_excel(DATA / "emdat" / "public_emdat_incl_hist_2026-05-18.xlsx",
                      sheet_name="EM-DAT Data", engine="openpyxl")
print(f"  EM-DAT: {len(emdat):,} rows; cols={list(emdat.columns)[:10]}...")


def dig_header(num, title):
    print()
    print("=" * 80)
    print(f"DIG {num}: {title}")
    print("=" * 80)


# ====================================================================
# DIG 003: BFA industrial-scale displacement
# ====================================================================
dig_header("003", "BFA — 22x fatality jump, actor decomposition, admin-1")

bfa_ged = ged[ged["country"] == "Burkina Faso"].copy()
print(f"BFA GED events: {len(bfa_ged):,}")

print("\nBFA annual fatality + event count:")
bfa_yr = bfa_ged.groupby("year").agg(events=("id", "count"), fatalities=("best", "sum")).reset_index()
bfa_yr["fatal_ratio_yoy"] = bfa_yr["fatalities"] / bfa_yr["fatalities"].shift(1)
print(bfa_yr.to_string(index=False))

print("\nBFA actor (side_a / side_b) totals 2014-2024:")
bfa_recent = bfa_ged[bfa_ged["year"] >= 2014]
print("\n  side_a (initiator) fatalities:")
print(bfa_recent.groupby("side_a")["best"].sum().sort_values(ascending=False).head(10).to_string())
print("\n  side_b (target) fatalities:")
print(bfa_recent.groupby("side_b")["best"].sum().sort_values(ascending=False).head(10).to_string())

print("\nBFA admin-1 acute (2020-2024) fatalities:")
bfa_acute = bfa_ged[(bfa_ged["year"] >= 2020) & (bfa_ged["year"] <= 2024)]
print(bfa_acute.groupby("adm_1")["best"].sum().sort_values(ascending=False).head(10).to_string())

print("\nBFA GIDD conflict-displacement by year:")
bfa_gidd = gidd_conf[gidd_conf["ISO3"] == "BFA"][["Year", "Conflict Internal Displacements"]].sort_values("Year")
print(bfa_gidd.to_string(index=False))


# ====================================================================
# DIG 004: NER 2024 flood >war
# ====================================================================
dig_header("004", "NER 2024 flood — singular event vs accumulation")

print("NER GIDD disaster-displacement by year (all hazards):")
ner_gidd_dis = gidd_dis[gidd_dis["ISO3"] == "NER"].groupby(["Year", "Hazard Type"])["Disaster Internal Displacements"].sum().unstack(fill_value=0)
print(ner_gidd_dis.to_string())

print("\nNER GIDD conflict-displacement by year:")
ner_gidd_conf = gidd_conf[gidd_conf["ISO3"] == "NER"][["Year", "Conflict Internal Displacements"]].sort_values("Year")
print(ner_gidd_conf.to_string(index=False))

print("\nNER EM-DAT 2024 events (all):")
emdat_cols = list(emdat.columns)
iso_col = [c for c in emdat_cols if "ISO" in c.upper()][0]
year_col = [c for c in emdat_cols if c.lower() == "start year"][0] if any(c.lower() == "start year" for c in emdat_cols) else "Start Year"
ner_em = emdat[(emdat[iso_col] == "NER") & (emdat[year_col] == 2024)]
keep = [c for c in ["Disaster Type", "Disaster Subtype", "Start Month", "End Month", "Location",
                    "Total Deaths", "No. Affected", "Total Affected", "No. Homeless"] if c in emdat.columns]
print(ner_em[keep].to_string(index=False) if len(ner_em) else "  (no NER 2024 events in EM-DAT)")


# ====================================================================
# DIG 012: Tigray war fatality cluster
# ====================================================================
dig_header("012", "Tigray — conflict_name filter, time profile, scale")

eth_ged = ged[ged["country"] == "Ethiopia"].copy()
print(f"ETH GED events: {len(eth_ged):,}")

print("\nETH unique conflict_name values (top 20 by fatality):")
print(eth_ged.groupby("conflict_name")["best"].sum().sort_values(ascending=False).head(20).to_string())

# Tigray filter
tigray_mask = eth_ged["conflict_name"].str.contains("Tigray", case=False, na=False)
tigray = eth_ged[tigray_mask]
print(f"\nTigray-named events: {len(tigray):,}, fatalities: {tigray['best'].sum():,}")
print("\nTigray annual + monthly profile:")
tigray["date_start"] = pd.to_datetime(tigray["date_start"], errors="coerce")
tigray["yr_mo"] = tigray["date_start"].dt.to_period("M")
print(tigray.groupby("yr_mo").agg(events=("id", "count"), fatalities=("best", "sum")).to_string())

print("\nETH GIDD conflict-displacement 2018-2024:")
eth_gidd = gidd_conf[(gidd_conf["ISO3"] == "ETH") & (gidd_conf["Year"] >= 2018)][["Year", "Conflict Internal Displacements"]]
print(eth_gidd.to_string(index=False))


# ====================================================================
# DIG 015: DRC 30M — one-sided actors, eastern provinces
# ====================================================================
dig_header("015", "DRC — one-sided actor decomposition, eastern provinces")

cod_ged = ged[ged["country"] == "DR Congo (Zaire)"].copy()
print(f"COD GED events: {len(cod_ged):,}")

cod_acute = cod_ged[(cod_ged["year"] >= 2020) & (cod_ged["year"] <= 2024)]
print(f"COD acute (2020-2024) events: {len(cod_acute):,}, total fatalities: {cod_acute['best'].sum():,}")

print("\nCOD acute type_of_violence breakdown:")
tov_map = {1: "state-based", 2: "non-state", 3: "one-sided"}
cod_acute["tov_label"] = cod_acute["type_of_violence"].map(tov_map)
print(cod_acute.groupby("tov_label")["best"].agg(["sum", "count"]).to_string())

print("\nCOD acute one-sided (type=3) actor decomposition (top 15):")
cod_os = cod_acute[cod_acute["type_of_violence"] == 3]
print(cod_os.groupby("side_a")["best"].sum().sort_values(ascending=False).head(15).to_string())

print("\nCOD acute admin-1 (top 10 by fatality):")
print(cod_acute.groupby("adm_1")["best"].sum().sort_values(ascending=False).head(10).to_string())


# ====================================================================
# DIG 016: PAK 2022 floods — monthly profile + ERA5 lookup queue
# ====================================================================
dig_header("016", "PAK 2022 floods — sub-event profile + EM-DAT confirm")

print("PAK GIDD disaster-displacement by year (all hazards):")
pak_gidd_dis = gidd_dis[gidd_dis["ISO3"] == "PAK"].groupby(["Year", "Hazard Type"])["Disaster Internal Displacements"].sum().unstack(fill_value=0)
print(pak_gidd_dis.to_string())

print("\nPAK EM-DAT 2022 flood events:")
pak_em = emdat[(emdat[iso_col] == "PAK") & (emdat[year_col] == 2022)]
if "Disaster Type" in pak_em.columns:
    pak_em = pak_em[pak_em["Disaster Type"].str.contains("Flood", case=False, na=False)]
keep = [c for c in ["Disaster Type", "Disaster Subtype", "Start Month", "End Month", "Location",
                    "Total Deaths", "No. Affected", "Total Affected", "No. Homeless"] if c in emdat.columns]
print(pak_em[keep].to_string(index=False) if len(pak_em) else "  (no PAK 2022 flood events in EM-DAT)")


print()
print("=" * 80)
print("TIER C DIG COMPLETE")
print("=" * 80)
