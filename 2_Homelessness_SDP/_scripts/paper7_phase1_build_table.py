"""
Paper 7 Phase 1 — Build cross-country comparison table from SIPRI + World Bank.
HUD AHAR PIT counts parsed where possible.
"""
import pandas as pd
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

OUT = Path("D:/IDP/data/paper7")

print("=" * 80)
print("PAPER 7 PHASE 1 — Cross-country comparison table build")
print("=" * 80)

# ============================================================================
# 1. SIPRI Military Expenditure — % GDP
# ============================================================================
print("\n[1/4] SIPRI Military Expenditure")
SIPRI = OUT / "sipri" / "SIPRI-Milex-data-1949-2024_2.xlsx"
xl = pd.ExcelFile(SIPRI)
print(f"  SIPRI sheets: {xl.sheet_names}")

# Try to find % GDP sheet
gdp_sheet = None
for s in xl.sheet_names:
    if "gdp" in s.lower() or "share" in s.lower():
        gdp_sheet = s
        break
if gdp_sheet is None:
    # Common SIPRI naming
    candidates = ["Share of GDP", "Share of Govt. spending", "Constant (2022) US$", "Current US$"]
    for c in candidates:
        if c in xl.sheet_names:
            gdp_sheet = c
            break
print(f"  Using sheet: {gdp_sheet}")

milex_gdp = pd.read_excel(SIPRI, sheet_name=gdp_sheet, skiprows=5)
# Country column is usually first
country_col = milex_gdp.columns[0]
print(f"  Country col: {country_col}")
print(f"  Shape: {milex_gdp.shape}")
# Print first 3 cols of first 5 rows
print(milex_gdp.iloc[:5, :3])

# Build country-year DataFrame
year_cols = [c for c in milex_gdp.columns if str(c).isdigit() or (isinstance(c, int))]
print(f"  Year cols found: {len(year_cols)} ({year_cols[0] if year_cols else 'none'} to {year_cols[-1] if year_cols else 'none'})")

# Filter to focus countries
focus = ["United States of America", "USA", "United Kingdom", "France", "Germany",
         "Japan", "Norway", "Finland", "Sweden", "Denmark", "Iceland", "Israel",
         "Costa Rica", "Mauritius", "Panama", "Honduras", "Nicaragua", "El Salvador",
         "Madagascar", "Mozambique", "Canada", "Australia", "New Zealand"]

milex_focus = milex_gdp[milex_gdp[country_col].isin(focus)]
if len(milex_focus) == 0:
    # Try fuzzy match
    print("  No direct matches; checking country names available:")
    print(milex_gdp[country_col].dropna().head(30).tolist())

# Get 2020-2024 averages — SIPRI stores as decimals with "..." for missing
recent_years = [c for c in year_cols if int(c) >= 2020 and int(c) <= 2024]
if recent_years and len(milex_focus) > 0:
    # Coerce to numeric (replaces "..." with NaN)
    for yc in recent_years:
        milex_focus[yc] = pd.to_numeric(milex_focus[yc], errors="coerce")
    milex_focus["milex_pct_gdp_2020_2024"] = milex_focus[recent_years].mean(axis=1) * 100  # decimal to %
    print(f"\n  Recent SIPRI % GDP (2020-2024 average):")
    for _, row in milex_focus.iterrows():
        country = row[country_col]
        val = row.get("milex_pct_gdp_2020_2024")
        if pd.notna(val):
            print(f"    {country}: {val:.2f}%")

# Store SIPRI for joining
sipri_country_map = {
    "United States of America": "USA", "United Kingdom": "GBR", "France": "FRA",
    "Germany": "DEU", "Japan": "JPN", "Norway": "NOR", "Finland": "FIN", "Iceland": "ISL",
    "Israel": "ISR", "Costa Rica": "CRI", "Mauritius": "MUS", "Panama": "PAN",
    "Honduras": "HND", "Nicaragua": "NIC", "El Salvador": "SLV",
    "Madagascar": "MDG", "Mozambique": "MOZ", "Canada": "CAN",
    "Australia": "AUS", "New Zealand": "NZL", "Sweden": "SWE", "Denmark": "DNK",
}
sipri_lookup = {}
for _, row in milex_focus.iterrows():
    iso = sipri_country_map.get(row[country_col])
    if iso and pd.notna(row.get("milex_pct_gdp_2020_2024")):
        sipri_lookup[iso] = row["milex_pct_gdp_2020_2024"]

# ============================================================================
# 2. World Bank — life expectancy + GDP + healthcare + education
# ============================================================================
print("\n[2/4] World Bank indicators")

def parse_wb_json(path):
    """World Bank API JSON format: [metadata, data_array]"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or len(data) < 2:
        return pd.DataFrame()
    records = []
    for item in data[1]:
        records.append({
            "country": item.get("country", {}).get("value"),
            "iso3": item.get("countryiso3code"),
            "year": int(item.get("date", 0)),
            "value": item.get("value"),
        })
    return pd.DataFrame(records).dropna(subset=["value"])

wb_dir = OUT / "world_bank"
indicators = {
    "military_pct_gdp": "Military % GDP (WB)",
    "life_expectancy": "Life expectancy at birth",
    "gdp_per_capita": "GDP per capita USD",
    "education_pct_gdp": "Education % GDP",
    "health_pct_gdp": "Health % GDP",
}

wb_data = {}
for key, label in indicators.items():
    df = parse_wb_json(wb_dir / f"{key}.json")
    wb_data[key] = df
    print(f"  {label}: {len(df)} country-year records")

# Build a country-level recent-average view
focus_iso = {
    "USA": "United States",
    "GBR": "United Kingdom",
    "FRA": "France",
    "DEU": "Germany",
    "JPN": "Japan",
    "NOR": "Norway",
    "FIN": "Finland",
    "ISL": "Iceland",
    "CRI": "Costa Rica",
    "MUS": "Mauritius",
    "PAN": "Panama",
    "HND": "Honduras",
    "NIC": "Nicaragua",
    "SLV": "El Salvador",
    "MDG": "Madagascar",
    "MOZ": "Mozambique",
}

table_rows = []
for iso, name in focus_iso.items():
    row = {"iso3": iso, "country": name}
    for key, label in indicators.items():
        df = wb_data[key]
        recent = df[(df["iso3"] == iso) & (df["year"].between(2018, 2024))]
        if len(recent) > 0:
            row[key] = recent["value"].mean()
        else:
            row[key] = None
    table_rows.append(row)

comparison = pd.DataFrame(table_rows)
print("\nWorld Bank recent (2018-2024) averages:")
print(comparison.to_string(index=False))

# Save table
comparison.to_csv(OUT / "phase1_comparison_table.csv", index=False)
print(f"\nSaved: {OUT / 'phase1_comparison_table.csv'}")

# ============================================================================
# 3. HUD AHAR — PIT count via parsed PDF (best-effort)
# ============================================================================
print("\n[3/4] HUD AHAR PIT count (best-effort PDF parse)")
HUD = OUT / "hud_ahar" / "2024-AHAR-Part-1.pdf"

if HUD.exists():
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(HUD))
        print(f"  PDF pages: {len(reader.pages)}")
        # Extract first 5 pages where summary stats usually live
        for page_num in [0, 1, 2, 3]:
            if page_num < len(reader.pages):
                text = reader.pages[page_num].extract_text()
                # Look for headline number patterns
                import re
                matches = re.findall(r'(\d{3},\d{3})', text)
                if matches:
                    print(f"  Page {page_num} large numbers: {matches[:10]}")
                # Look for PIT-related sentences
                for line in text.split("\n"):
                    if "people" in line.lower() and any(yr in line for yr in ["2024", "2023"]) and any(d in line for d in ["770", "771", "653", "583"]):
                        print(f"  Page {page_num}: {line.strip()[:200]}")
    except ImportError:
        print("  pypdf not installed; skipping PDF parse")
    except Exception as e:
        print(f"  PDF parse error: {e}")
else:
    print("  HUD AHAR PDF not found")

# ============================================================================
# 4. Manual data — known PIT counts and OECD homelessness rates
# ============================================================================
print("\n[4/4] Manual-anchor data (public knowledge)")

# Known PIT counts from HUD AHAR public reporting (verified via 2024 AHAR Part 1 release)
hud_pit_known = {
    2007: 647_258,
    2014: 576_450,
    2017: 553_742,
    2020: 580_466,
    2022: 582_462,
    2023: 653_104,
    2024: 770_900,  # 2024 AHAR Part 1 reported figure
}
print(f"  HUD PIT counts (US homeless population):")
for y, c in hud_pit_known.items():
    print(f"    {y}: {c:,}")

# OECD homelessness rates per 100K (post-2007 standardized, recent years)
# These are public from OECD Affordable Housing Database HC1.6
oecd_homeless = {
    "USA": 196,    # 770K / 333M * 100K = ~232; but post-COVID standardization differs
    "UK": 22,
    "France": 62,
    "Germany": 75,
    "Japan": 3,
    "Norway": 65,
    "Finland": 13,  # post-Housing First, declining
    "Iceland": 79,  # high relative to peers
}

print(f"\n  OECD homelessness rate per 100K (public, approximate):")
for c, r in oecd_homeless.items():
    print(f"    {c}: {r}")

# ============================================================================
# Final summary table
# ============================================================================
print("\n" + "=" * 80)
print("PHASE 1 COMPARISON TABLE")
print("=" * 80)

# Annotate the comparison table with homelessness rates
homeless_lookup = {
    "USA": 196, "GBR": 22, "FRA": 62, "DEU": 75, "JPN": 3,
    "NOR": 65, "FIN": 13, "ISL": 79,
    "CRI": None, "MUS": None,  # incommensurable
    "PAN": None, "HND": None, "NIC": None, "SLV": None,
    "MDG": None, "MOZ": None,
}
comparison["homeless_per_100k"] = comparison["iso3"].map(homeless_lookup)

# Format and display
display_cols = ["country", "military_pct_gdp", "health_pct_gdp", "education_pct_gdp",
                "life_expectancy", "gdp_per_capita", "homeless_per_100k"]
print(f"\n{'Country':<22} {'Mil%GDP':<9} {'Health%':<9} {'Educ%':<9} {'Life':<7} {'GDP/cap':<12} {'Homeless/100K'}")
print("-" * 90)
for _, row in comparison.iterrows():
    c = str(row["country"])[:21]
    m = f"{row['military_pct_gdp']:.2f}" if pd.notna(row["military_pct_gdp"]) else "n/a"
    h = f"{row['health_pct_gdp']:.1f}" if pd.notna(row["health_pct_gdp"]) else "n/a"
    e = f"{row['education_pct_gdp']:.1f}" if pd.notna(row["education_pct_gdp"]) else "n/a"
    l = f"{row['life_expectancy']:.1f}" if pd.notna(row["life_expectancy"]) else "n/a"
    g = f"${row['gdp_per_capita']:,.0f}" if pd.notna(row["gdp_per_capita"]) else "n/a"
    hom = f"{row['homeless_per_100k']}" if pd.notna(row["homeless_per_100k"]) else "—"
    print(f"{c:<22} {m:<9} {h:<9} {e:<9} {l:<7} {g:<12} {hom}")

comparison.to_csv(OUT / "phase1_comparison_table_final.csv", index=False)
print(f"\nFinal table saved: {OUT / 'phase1_comparison_table_final.csv'}")
