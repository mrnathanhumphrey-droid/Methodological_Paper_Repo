"""Build Sahel country-year panel for BFA + MLI + BEN + NER, 1998-2024.

Joins:
- UCDP-GED: conflict events, fatalities, admin1 count
- IDMC IDU: new displacement figures, event count
- GDELT: event counts by quadclass + Goldstein mean
- EM-DAT: disaster count + total affected
- V-Dem: lib_democracy, civil_society, rule_of_law indices
- WB WDI: GDP per capita, unemployment, infant mortality, education spending
- HAPI DTM: IDP stock figures
- IPC food security (via HAPI): max phase per year

Output: D:/IDP/analysis/sahel_panel_2026_05_21.parquet
"""
import json
import pathlib
import time

import pandas as pd
import numpy as np

ROOT = pathlib.Path("D:/IDP")
DATA = ROOT / "data"
OUT = ROOT / "analysis"
OUT.mkdir(parents=True, exist_ok=True)

SAHEL_ISO3 = ["BFA", "MLI", "BEN", "NER"]
SAHEL_NAMES = {"BFA": "Burkina Faso", "MLI": "Mali", "BEN": "Benin", "NER": "Niger"}
YEARS = list(range(1998, 2025))

# Initialize panel skeleton
panel = pd.DataFrame([(iso, y) for iso in SAHEL_ISO3 for y in YEARS], columns=["iso3", "year"])

print(f"[{time.strftime('%H:%M:%S')}] === Building Sahel panel ===")

# === UCDP-GED ===
print("[1] UCDP-GED")
try:
    ged = pd.read_csv(DATA / "ucdp" / "GEDEvent_v25_1.csv",
                       usecols=["country", "year", "best", "adm_1"], low_memory=False)
    name_to_iso = {v: k for k, v in SAHEL_NAMES.items()}
    ged = ged[ged["country"].isin(SAHEL_NAMES.values())].copy()
    ged["iso3"] = ged["country"].map(name_to_iso)
    agg = ged.groupby(["iso3", "year"]).agg(
        ucdp_events=("best", "count"),
        ucdp_fatalities=("best", "sum"),
        ucdp_admin1_count=("adm_1", "nunique"),
    ).reset_index()
    panel = panel.merge(agg, on=["iso3", "year"], how="left")
    print(f"  added: {agg.shape[0]} country-year rows")
except Exception as e:
    print(f"  FAIL {type(e).__name__}: {e}")

# === IDMC IDU ===
print("[2] IDMC IDU per-country")
idu_rows = []
for iso3 in SAHEL_ISO3:
    p = DATA / "idmc_gidd" / "idu" / f"{iso3.lower()}_{iso3.lower()}.csv"
    if not p.exists():
        continue
    try:
        df = pd.read_csv(p, low_memory=False)
        date_col = next((c for c in df.columns if "displacement_start_date" in c.lower() or "displacement_date" in c.lower()), None)
        if date_col is None:
            date_col = next((c for c in df.columns if "date" in c.lower()), None)
        figure_col = next((c for c in df.columns if "figure" in c.lower()), None)
        if not (date_col and figure_col):
            print(f"  {iso3}: missing date/figure cols: {df.columns.tolist()[:10]}")
            continue
        df["year"] = pd.to_datetime(df[date_col], errors="coerce").dt.year
        df = df.dropna(subset=["year", figure_col])
        df["year"] = df["year"].astype(int)
        df[figure_col] = pd.to_numeric(df[figure_col], errors="coerce")
        df = df.dropna(subset=[figure_col])
        sub = df.groupby("year").agg(
            idu_new_disp_sum=(figure_col, "sum"),
            idu_event_count=(figure_col, "count"),
        ).reset_index()
        sub["iso3"] = iso3
        idu_rows.append(sub)
    except Exception as e:
        print(f"  {iso3}: FAIL {type(e).__name__}")
if idu_rows:
    idu_panel = pd.concat(idu_rows)
    panel = panel.merge(idu_panel, on=["iso3", "year"], how="left")
    print(f"  added: {idu_panel.shape[0]} country-year rows")

# === GDELT — per Sahel CSV ===
print("[3] GDELT per Sahel country")
gdelt_rows = []
for iso3 in SAHEL_ISO3:
    name = SAHEL_NAMES[iso3].lower().replace(" ", "_")
    p = DATA / "gdelt" / f"gdelt-{name}-2014_2024.csv"
    if not p.exists():
        continue
    try:
        # Pipe-separated since we wrote them that way
        df = pd.read_csv(p, sep="|", usecols=["year", "quadclass", "goldsteinscale"],
                          low_memory=False, on_bad_lines="skip")
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
        df["quadclass"] = pd.to_numeric(df["quadclass"], errors="coerce")
        df["goldsteinscale"] = pd.to_numeric(df["goldsteinscale"], errors="coerce")
        df = df.dropna(subset=["year"])
        df["year"] = df["year"].astype(int)
        agg = df.groupby("year").agg(
            gdelt_events=("year", "count"),
            gdelt_goldstein_mean=("goldsteinscale", "mean"),
        ).reset_index()
        # Quadclass counts
        qc = df.groupby(["year", "quadclass"]).size().unstack(fill_value=0)
        for q in [1, 2, 3, 4]:
            if q in qc.columns:
                agg[f"gdelt_qc{q}"] = qc[q].reindex(agg["year"]).values
            else:
                agg[f"gdelt_qc{q}"] = 0
        agg["iso3"] = iso3
        gdelt_rows.append(agg)
    except Exception as e:
        print(f"  {iso3}: FAIL {type(e).__name__}: {e}")
if gdelt_rows:
    gdelt_panel = pd.concat(gdelt_rows)
    panel = panel.merge(gdelt_panel, on=["iso3", "year"], how="left")
    print(f"  added: {gdelt_panel.shape[0]} country-year rows")

# === EM-DAT ===
print("[4] EM-DAT")
try:
    emdat = pd.read_excel(DATA / "emdat" / "public_emdat_incl_hist_2026-05-18.xlsx", header=0)
    iso_col = next((c for c in emdat.columns if "iso" in c.lower()), None)
    year_col = next((c for c in emdat.columns if c.lower() == "start year" or c.lower() == "year"), None)
    affected_col = next((c for c in emdat.columns if "total affected" in c.lower()), None)
    type_col = next((c for c in emdat.columns if "disaster type" in c.lower()), None)
    emdat_s = emdat[emdat[iso_col].isin(SAHEL_ISO3)].copy()
    agg = emdat_s.groupby([iso_col, year_col]).agg(
        emdat_disaster_count=(type_col, "count"),
        emdat_total_affected=(affected_col, "sum"),
    ).reset_index().rename(columns={iso_col: "iso3", year_col: "year"})
    agg["year"] = agg["year"].astype(int)
    panel = panel.merge(agg, on=["iso3", "year"], how="left")
    print(f"  added: {agg.shape[0]} country-year rows")
except Exception as e:
    print(f"  FAIL {type(e).__name__}: {e}")

# === V-Dem ===
print("[5] V-Dem")
try:
    vdem = pd.read_csv(DATA / "vdem" / "vdem_vdem.csv",
                       usecols=["country_text_id", "year", "v2x_libdem", "v2x_polyarchy",
                                "v2x_civlib", "v2x_corr", "v2x_rule"],
                       low_memory=False)
    vdem = vdem[vdem["country_text_id"].isin(SAHEL_ISO3)].copy()
    vdem = vdem.rename(columns={"country_text_id": "iso3",
                                  "v2x_libdem": "vdem_libdem",
                                  "v2x_polyarchy": "vdem_polyarchy",
                                  "v2x_civlib": "vdem_civlib",
                                  "v2x_corr": "vdem_corr",
                                  "v2x_rule": "vdem_rule"})
    panel = panel.merge(vdem, on=["iso3", "year"], how="left")
    print(f"  added: {vdem.shape[0]} country-year rows")
except Exception as e:
    print(f"  FAIL {type(e).__name__}: {e}")

# === WB WDI ===
print("[6] WB WDI")
try:
    wdi = pd.read_csv(DATA / "wb_wdi" / "extracted" / "WDICSV.csv", low_memory=False)
    wdi_priority = {
        "NY.GDP.PCAP.CD": "wdi_gdp_pcap",
        "SP.DYN.IMRT.IN": "wdi_infant_mort",
        "SE.XPD.TOTL.GD.ZS": "wdi_edu_spend_gdp",
        "SL.UEM.TOTL.ZS": "wdi_unemployment",
        "SP.POP.TOTL": "wdi_pop_total",
        "SI.POV.GINI": "wdi_gini",
        "EN.ATM.CO2E.PC": "wdi_co2_pc",
    }
    sub = wdi[wdi["Country Code"].isin(SAHEL_ISO3) & wdi["Indicator Code"].isin(wdi_priority)].copy()
    year_cols = [c for c in sub.columns if c.isdigit() and 1998 <= int(c) <= 2024]
    rows = []
    for _, r in sub.iterrows():
        for yc in year_cols:
            v = r[yc]
            if pd.notna(v):
                rows.append({
                    "iso3": r["Country Code"],
                    "year": int(yc),
                    "indicator": wdi_priority[r["Indicator Code"]],
                    "value": v,
                })
    if rows:
        wdi_long = pd.DataFrame(rows)
        wdi_wide = wdi_long.pivot_table(index=["iso3", "year"], columns="indicator", values="value").reset_index()
        panel = panel.merge(wdi_wide, on=["iso3", "year"], how="left")
        print(f"  added: {wdi_wide.shape[0]} country-year rows, {len(wdi_priority)} indicators")
except Exception as e:
    print(f"  FAIL {type(e).__name__}: {e}")

# Save panel
target = OUT / "sahel_panel_2026_05_21.parquet"
panel.to_parquet(target)
print(f"\n[{time.strftime('%H:%M:%S')}] === panel saved ===")
print(f"  {target}")
print(f"  shape: {panel.shape}")
print(f"  columns: {panel.columns.tolist()}")

# Quick coverage summary
print("\n=== coverage summary by country ===")
for iso3 in SAHEL_ISO3:
    sub = panel[panel["iso3"] == iso3]
    print(f"\n  {iso3} ({SAHEL_NAMES[iso3]})  rows: {len(sub)}")
    for col in panel.columns:
        if col in ("iso3", "year"):
            continue
        n_nonnull = sub[col].notna().sum()
        if n_nonnull > 0:
            print(f"    {col:30s}  n_years={n_nonnull:3d}")

# Tight conflict-displacement preview
print("\n=== conflict vs displacement preview (2018+) ===")
preview_cols = ["iso3", "year", "ucdp_events", "ucdp_fatalities", "idu_new_disp_sum",
                "gdelt_events", "emdat_disaster_count", "vdem_libdem", "wdi_gdp_pcap"]
preview_cols = [c for c in preview_cols if c in panel.columns]
preview = panel[panel["year"] >= 2018][preview_cols].sort_values(["iso3", "year"])
print(preview.to_string(index=False))
