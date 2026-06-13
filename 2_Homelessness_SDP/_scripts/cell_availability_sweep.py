"""Cell-availability sweep — build country-year coverage matrix across all sources.

For each tabular source, extract (country_iso3, year) pairs that have data.
Cross-reference, count sources per (country, year), identify dense threads.
"""
import json
import pathlib
import time
from collections import defaultdict

import pandas as pd

ROOT = pathlib.Path("D:/IDP/data")
OUT = pathlib.Path("D:/IDP/analysis")
OUT.mkdir(parents=True, exist_ok=True)

# country_iso3 -> year -> set of sources
matrix = defaultdict(lambda: defaultdict(set))


def add(iso3, year, source):
    if iso3 and year:
        matrix[iso3.upper()][int(year)].add(source)


print(f"[{time.strftime('%H:%M:%S')}] starting sweep")

# === 1. UCDP-GED (event-level) ===
print("[1] UCDP-GED")
try:
    df = pd.read_csv(ROOT / "ucdp" / "GEDEvent_v25_1.csv", usecols=["country", "year"], low_memory=False)
    # UCDP uses country names; map to iso3 via a small inline dict (basic; will leave non-matches)
    from pycountry import countries
    name_to_iso = {c.name: c.alpha_3 for c in countries}
    df["iso3"] = df["country"].map(name_to_iso).fillna(df["country"].str.upper().str[:3])
    for iso3, year in df[["iso3", "year"]].drop_duplicates().itertuples(index=False):
        add(iso3, year, "ucdp_ged")
    print(f"  {len(df):,} events, {df[['iso3','year']].drop_duplicates().shape[0]:,} country-years")
except Exception as e:
    print(f"  FAIL {type(e).__name__}: {e}")

# === 2. UNHCR RDF (already country-year) ===
print("[2] UNHCR RDF")
try:
    df = pd.read_csv(ROOT / "unhcr_rdf" / "population_1990_2024.csv", low_memory=False)
    # Columns typically include coo_iso (country of origin) + coa_iso (country of asylum) + year
    yearcol = next((c for c in df.columns if "year" in c.lower()), None)
    isocols = [c for c in df.columns if "iso" in c.lower()]
    if yearcol and isocols:
        for col in isocols[:2]:
            sub = df[[col, yearcol]].dropna().drop_duplicates()
            for iso3, year in sub.itertuples(index=False):
                add(str(iso3), year, "unhcr_rdf")
        print(f"  {len(df):,} rows; cols {df.columns.tolist()[:8]}")
    else:
        print(f"  could not find year+iso columns: {df.columns.tolist()[:10]}")
except Exception as e:
    print(f"  FAIL {type(e).__name__}: {e}")

# === 3. WB WDI ===
print("[3] WB WDI")
try:
    wdi = pd.read_csv(ROOT / "wb_wdi" / "extracted" / "WDICSV.csv", low_memory=False)
    # Columns: Country Name, Country Code, Indicator Name, Indicator Code, 1960, 1961, ..., 2024
    year_cols = [c for c in wdi.columns if c.isdigit()]
    for iso3 in wdi["Country Code"].dropna().unique():
        sub = wdi[wdi["Country Code"] == iso3]
        for year in year_cols:
            if sub[year].notna().any():
                add(iso3, year, "wb_wdi")
    print(f"  {len(wdi):,} rows × {len(year_cols)} year-cols; {wdi['Country Code'].nunique()} countries")
except Exception as e:
    print(f"  FAIL {type(e).__name__}: {e}")

# === 4. V-Dem ===
print("[4] V-Dem")
try:
    df = pd.read_csv(ROOT / "vdem" / "vdem_vdem.csv", usecols=["country_text_id", "year"], low_memory=False)
    for iso3, year in df.drop_duplicates().itertuples(index=False):
        add(str(iso3), year, "vdem")
    print(f"  {len(df):,} country-years; {df['country_text_id'].nunique()} countries")
except Exception as e:
    print(f"  FAIL {type(e).__name__}: {e}")

# === 5. Polity 5 ===
print("[5] Polity 5")
try:
    df = pd.read_excel(ROOT / "polity5" / "p5v2018.xls")
    iso = None
    for c in df.columns:
        if c.lower() in ("scode", "ccode", "stateabb", "country_code"):
            iso = c; break
    yearcol = next((c for c in df.columns if c.lower() == "year"), None)
    if iso and yearcol:
        for code, year in df[[iso, yearcol]].dropna().drop_duplicates().itertuples(index=False):
            add(str(code), year, "polity5")
        print(f"  {len(df):,} rows; iso_col={iso} year_col={yearcol}; {df[iso].nunique()} entities")
    else:
        print(f"  could not find cols; have {df.columns.tolist()[:10]}")
except Exception as e:
    print(f"  FAIL {type(e).__name__}: {e}")

# === 6. EM-DAT ===
print("[6] EM-DAT")
try:
    df = pd.read_excel(ROOT / "emdat" / "public_emdat_incl_hist_2026-05-18.xlsx", header=0)
    iso_col = next((c for c in df.columns if "iso" in c.lower()), None)
    year_col = next((c for c in df.columns if c.lower() == "start year" or c.lower() == "year"), None)
    if iso_col and year_col:
        for iso3, year in df[[iso_col, year_col]].dropna().drop_duplicates().itertuples(index=False):
            add(str(iso3), year, "emdat")
        print(f"  {len(df):,} events; iso={iso_col} year={year_col}")
    else:
        print(f"  cols: {df.columns.tolist()[:15]}")
except Exception as e:
    print(f"  FAIL {type(e).__name__}: {e}")

# === 7. HAPI 3 endpoints (JSON) ===
print("[7] HAPI 3 endpoints")
for ep_name, ep_path in [
    ("hapi_baseline_pop", "hdx_hapi/baseline_population/page_0.json"),
    ("hapi_food_security", "hdx_hapi/food_security/page_0.json"),
    ("hapi_refugees", "hdx_hapi/refugees/page_0.json"),
]:
    p = ROOT / ep_path
    if not p.exists(): continue
    try:
        j = json.load(open(p))
        data = j.get("data", [])
        cnt = 0
        for row in data:
            iso3 = row.get("location_code") or row.get("origin_location_code") or ""
            yr = row.get("reference_period_start", "")[:4] or row.get("year", "")
            if iso3 and yr.isdigit():
                add(iso3, yr, ep_name)
                cnt += 1
        print(f"  {ep_name}: {len(data)} rows, {cnt} added")
    except Exception as e:
        print(f"  {ep_name}: FAIL {type(e).__name__}")

# === 8. IDMC IDU per-country CSVs ===
print("[8] IDMC IDU per-country")
idu_dir = ROOT / "idmc_gidd" / "idu"
if idu_dir.exists():
    for f in idu_dir.glob("*.csv"):
        iso3 = f.stem.split("_")[0][:3].upper()
        try:
            df = pd.read_csv(f, low_memory=False)
            year_col = next((c for c in df.columns if "year" in c.lower() or "date" in c.lower()), None)
            if year_col:
                years = pd.to_datetime(df[year_col], errors="coerce").dt.year.dropna().unique()
                if len(years) == 0:
                    years = pd.to_numeric(df[year_col], errors="coerce").dropna().astype(int).unique()
                for y in years:
                    if 1900 < y < 2030:
                        add(iso3, y, "idmc_idu")
        except Exception:
            pass
    print(f"  scanned {len(list(idu_dir.glob('*.csv')))} country CSVs")

# === 9. WHO GHO indicators ===
print("[9] WHO GHO")
who_dir = ROOT / "who_gho" / "indicators"
if who_dir.exists():
    for f in who_dir.glob("*.json"):
        try:
            j = json.load(open(f))
            for row in j.get("value", []):
                iso3 = row.get("SpatialDim", "")
                year = row.get("TimeDim", 0)
                if iso3 and year and isinstance(year, int) and 1900 < year < 2030 and len(iso3) == 3:
                    add(iso3, year, "who_gho")
        except Exception:
            pass
    print(f"  scanned {len(list(who_dir.glob('*.json')))} indicator JSONs")

# === 10. UNDP HDR annex ===
print("[10] UNDP HDR")
try:
    df = pd.read_excel(ROOT / "undp_hdr" / "HDR23-24_Annex_HDI.xlsx", header=None)
    # XLSX with various tables; just note country coverage; year defaults to 2022 (latest HDR cycle)
    iso_candidates = df.iloc[:, 1].astype(str).str.strip()
    # Loose match: ISO-3 is 3 uppercase letters
    iso_set = set([v for v in iso_candidates if len(v) == 3 and v.isupper() and v.isalpha()])
    for iso3 in iso_set:
        for y in range(1990, 2024):
            add(iso3, y, "undp_hdr")
    print(f"  ~{len(iso_set)} countries (HDR 1990-2023 backfilled coverage)")
except Exception as e:
    print(f"  FAIL {type(e).__name__}: {e}")

# === Summary ===
print(f"\n[{time.strftime('%H:%M:%S')}] building summary")

# Long-form: country, year, source, has_data
rows = []
for iso3, years in matrix.items():
    for year, sources in years.items():
        for src in sources:
            rows.append({"iso3": iso3, "year": year, "source": src})
long_df = pd.DataFrame(rows)
long_df.to_parquet(OUT / "cell_availability_matrix_2026_05_21.parquet")
print(f"  long-form: {len(long_df):,} (iso3, year, source) tuples")

# Wide: country x year -> source count
src_count = long_df.groupby(["iso3", "year"])["source"].nunique().reset_index(name="n_sources")
src_count.to_parquet(OUT / "cell_availability_source_count_2026_05_21.parquet")
print(f"  source-count matrix: {src_count.shape[0]:,} (iso3, year) cells")

# Top dense cells
top_cells = src_count.sort_values("n_sources", ascending=False).head(30)
print("\n=== TOP 30 (iso3, year) cells by source count ===")
print(top_cells.to_string(index=False))

# Source × country count
src_country = long_df.groupby("source")["iso3"].nunique().reset_index(name="n_countries").sort_values("n_countries", ascending=False)
print("\n=== Source × n_countries ===")
print(src_country.to_string(index=False))

# Source × year count
src_year = long_df.groupby("source")["year"].nunique().reset_index(name="n_years").sort_values("n_years", ascending=False)
print("\n=== Source × n_years ===")
print(src_year.to_string(index=False))

# Mid-2010s+ density (year >= 2010)
recent = long_df[long_df["year"] >= 2010]
recent_density = recent.groupby("iso3")["source"].nunique().reset_index(name="n_sources_2010plus").sort_values("n_sources_2010plus", ascending=False).head(30)
print("\n=== TOP 30 countries by sources-2010+ ===")
print(recent_density.to_string(index=False))

print(f"\n[{time.strftime('%H:%M:%S')}] complete")
print(f"  parquet outputs at {OUT}/")
