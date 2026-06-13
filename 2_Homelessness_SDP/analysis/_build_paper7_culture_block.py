"""
MECHANICAL data-engineering build for Paper 7 CoC-level CULTURE / POLITICS /
SOCIAL-FABRIC block.  NO regressions.  NO hand-coded / recalled values.
Only data actually downloaded to D:/IDP/data/paper7/culture/ is used; any source
that could not be downloaded is left missing and flagged in the coverage JSON.

Outputs (new files only):
  D:/IDP/analysis/paper7_culture_block_coc.csv
  D:/IDP/analysis/paper7_culture_block_coverage.json

Sources actually used (each verified on disk before use):
  1. Partisan lean: MIT Election Lab "County Presidential Returns 2000-2020"
     (Harvard Dataverse mirror, datafile id 10778153, file countypres_2000-2020.tab).
     County two-party Democratic share = DEMOCRAT / (DEMOCRAT + REPUBLICAN)
     candidatevotes, for 2012 and 2020 (mode == 'TOTAL' only -> no double count).
  2. Family / social structure: Census ACS5 (pulled via CENSUS_API_KEY):
       - single-person HH share = B11001_008E (householder living alone) / B11001_001E
         (total households), years 2012 and 2024.
       - never-married share = (B12001_003E male never-married + B12001_012E female
         never-married) / B12001_001E (pop 15+), years 2012 and 2024.
  3. Social capital: Rupasingha-Goetz county Social Capital Index, Penn State NERCRD,
     social_capital_2014.xlsx, sheet '2014 social capital data', col sk2014 ->
     social_capital_index.  2014 is the latest vintage NERCRD publishes (single
     vintage, no 2012->recent change).
  4. Religiosity: ARDA US Religion Census (RCMS) 2010/2020 -> NOT obtained
     (thearda.com download.aspx serves a JS agreement-shell, no scriptable file);
     flagged missing.

County -> CoC aggregation: crosswalk county_coc_match.csv (latin-1), weight =
county_population (ACS5 B01003) * pct_cnty_pop_coc/100.
  - All metrics are SHARES / indices aggregated as population-weighted means.
  - The two-party Dem share is aggregated weighted by county MAJOR-PARTY VOTES *
    pop-share (so a CoC's lean reflects where votes actually are); single-person,
    never-married, and social-capital aggregated by county population * pop-share.
"""
import json, os
import pandas as pd
import numpy as np

CUL  = r"D:/IDP/data/paper7/culture"
DD   = r"D:/IDP/data/paper7/demand_drivers"
XW   = r"D:/IDP/data/paper7/coc_crosswalk/county_coc_match.csv"
OUT_CSV  = r"D:/IDP/analysis/paper7_culture_block_coc.csv"
OUT_JSON = r"D:/IDP/analysis/paper7_culture_block_coverage.json"

coverage = {"sources": {}, "n_cocs_per_variable": {}, "notes": []}

# ---------- crosswalk ----------
xw = pd.read_csv(XW, encoding="latin-1", dtype={"county_fips": str})
xw["county_fips"] = xw["county_fips"].str.strip().str.zfill(5)
xw["w"] = pd.to_numeric(xw["pct_cnty_pop_coc"], errors="coerce") / 100.0
xw = xw[["county_fips", "coc_number", "w"]].dropna()
all_cocs = sorted(xw["coc_number"].unique())
coverage["sources"]["crosswalk"] = {"status": "ok", "rows": int(len(xw)),
    "n_coc": int(len(all_cocs)), "n_county": int(xw["county_fips"].nunique())}

# ---------- county population (weights), ACS5 B01003 2012 & 2024 ----------
def load_b01003(year):
    with open(os.path.join(DD, f"acs5_{year}_B01003_county.json")) as f:
        d = json.load(f)
    df = pd.DataFrame(d[1:], columns=d[0])
    df["county_fips"] = df["state"].str.zfill(2) + df["county"].str.zfill(3)
    df[f"pop_{year}"] = pd.to_numeric(df["B01003_001E"], errors="coerce")
    return df[["county_fips", f"pop_{year}"]]

pop12 = load_b01003(2012)
pop24 = load_b01003(2024)
coverage["sources"]["county_population_b01003"] = {"status": "ok",
    "n_county_2012": int(pop12["pop_2012"].notna().sum()),
    "n_county_2024": int(pop24["pop_2024"].notna().sum())}

def wmean_to_coc(county_df, val_col, wt_col):
    """Pop(or vote)-share weighted mean of a county rate to CoC."""
    m = xw.merge(county_df, on="county_fips", how="inner")
    m["wt"] = m[wt_col] * m["w"]
    m = m.dropna(subset=[val_col, "wt"])
    m = m[m["wt"] > 0]
    if len(m) == 0:
        return pd.Series(dtype=float, name=val_col)
    g = m.groupby("coc_number").apply(
        lambda dd: np.average(dd[val_col], weights=dd["wt"]), include_groups=False)
    return g.rename(val_col)

pieces = []

# ====================================================================
# 1. PARTISAN LEAN  (MIT Election Lab county presidential returns)
# ====================================================================
try:
    cp = pd.read_csv(os.path.join(CUL, "countypres_2000-2020.tab"), sep="\t",
                     dtype={"county_fips": str})
    cp = cp[cp["year"].isin([2012, 2020])]
    cp["county_fips"] = (cp["county_fips"].astype(str).str.strip()
                         .str.replace(".0", "", regex=False))
    cp = cp[cp["county_fips"].str.isdigit()]
    cp["county_fips"] = cp["county_fips"].str.zfill(5)
    cp["party"] = cp["party"].astype(str).str.upper()
    cp["mode"] = cp["mode"].astype(str).str.upper()
    cp["candidatevotes"] = pd.to_numeric(cp["candidatevotes"], errors="coerce")
    cp = cp[cp["party"].isin(["DEMOCRAT", "REPUBLICAN"])]

    # Mode handling: most states+years carry a single mode=='TOTAL' row per
    # county/party.  TEN states in 2020 (AR,AZ,GA,IA,KY,MD,NC,OK,SC,VA) instead
    # report votes broken out by mode (ABSENTEE/EARLY VOTE/ELECTION DAY/
    # PROVISIONAL/...) with NO 'TOTAL' row.  For each (year,county,party): use
    # the 'TOTAL' row where present, otherwise SUM over the mode-level rows.
    # This recovers the same county totals without double counting.
    def county_party_votes(g):
        tot = g[g["mode"] == "TOTAL"]["candidatevotes"]
        return tot.sum() if len(tot) else g["candidatevotes"].sum()

    agg = (cp.groupby(["year", "county_fips", "party"])
             .apply(county_party_votes, include_groups=False)
             .rename("votes").reset_index())
    states_modeonly = (cp[~cp["state_po"].isin(
        cp[cp["mode"] == "TOTAL"]["state_po"].unique())]["state_po"].unique()
        if "state_po" in cp.columns else [])

    yr_county = {}
    for yr in (2012, 2020):
        piv = (agg[agg["year"] == yr]
               .pivot_table(index="county_fips", columns="party",
                            values="votes", aggfunc="sum"))
        piv = piv.rename(columns={"DEMOCRAT": "dem", "REPUBLICAN": "rep"})
        for c in ("dem", "rep"):
            if c not in piv.columns:
                piv[c] = np.nan
        piv["major"] = piv["dem"].fillna(0) + piv["rep"].fillna(0)
        piv[f"dem_share_{yr}"] = piv["dem"] / piv["major"]
        yr_county[yr] = piv[[f"dem_share_{yr}", "major"]].reset_index()

    s12 = wmean_to_coc(yr_county[2012].rename(columns={"major": "wt"}),
                       "dem_share_2012", "wt")
    s20 = wmean_to_coc(yr_county[2020].rename(columns={"major": "wt"}),
                       "dem_share_2020", "wt")
    dem = pd.concat([s12, s20], axis=1)
    dem["d_dem_share"] = dem["dem_share_2020"] - dem["dem_share_2012"]
    pieces.append(dem.reset_index())
    coverage["sources"]["mit_election_countypres"] = {"status": "ok",
        "file": "countypres_2000-2020.tab (Dataverse datafile id 10778153)",
        "n_county_2012": int(yr_county[2012]["dem_share_2012"].notna().sum()),
        "n_county_2020": int(yr_county[2020]["dem_share_2020"].notna().sum()),
        "metric": "two-party Dem share = DEM/(DEM+REP) candidatevotes",
        "mode_handling": "use mode=='TOTAL' where present else sum over modes; "
                         "10 states (AR,AZ,GA,IA,KY,MD,NC,OK,SC,VA) report 2020 by "
                         "mode with no TOTAL row -> summed.",
        "coc_weight": "county major-party votes * pop-share"}
except Exception as e:
    coverage["sources"]["mit_election_countypres"] = {"status": "FAILED",
                                                      "error": repr(e)[:300]}

# ====================================================================
# 2a. SINGLE-PERSON HOUSEHOLD SHARE  (ACS5 B11001, 2012 & 2024)
# ====================================================================
def load_hh(year):
    with open(os.path.join(CUL, f"acs5_{year}_hh_county.json")) as f:
        d = json.load(f)
    df = pd.DataFrame(d[1:], columns=d[0])
    df["county_fips"] = df["state"].str.zfill(2) + df["county"].str.zfill(3)
    df["tot_hh"] = pd.to_numeric(df["B11001_001E"], errors="coerce")
    df["alone"]  = pd.to_numeric(df["B11001_008E"], errors="coerce")
    df[f"sp_share_{year}"] = df["alone"] / df["tot_hh"]
    return df[["county_fips", f"sp_share_{year}"]]

try:
    h12 = load_hh(2012)
    h24 = load_hh(2024)
    sp12 = wmean_to_coc(h12.merge(pop12, on="county_fips", how="left")
                            .rename(columns={"pop_2012": "wt"}),
                        "sp_share_2012", "wt").rename("single_person_hh_share_2012")
    sp24 = wmean_to_coc(h24.merge(pop24, on="county_fips", how="left")
                            .rename(columns={"pop_2024": "wt"}),
                        "sp_share_2024", "wt").rename("single_person_hh_share_2024")
    sp = pd.concat([sp12, sp24], axis=1)
    sp["d_single_person"] = (sp["single_person_hh_share_2024"]
                             - sp["single_person_hh_share_2012"])
    pieces.append(sp.reset_index())
    coverage["sources"]["acs5_B11001_single_person_hh"] = {"status": "ok",
        "metric": "B11001_008E / B11001_001E (householder living alone / total HH)",
        "n_county_2012": int(h12["sp_share_2012"].notna().sum()),
        "n_county_2024": int(h24["sp_share_2024"].notna().sum())}
except Exception as e:
    coverage["sources"]["acs5_B11001_single_person_hh"] = {"status": "FAILED",
                                                           "error": repr(e)[:300]}

# ====================================================================
# 2b. NEVER-MARRIED SHARE  (ACS5 B12001, 2012 & 2024)
# ====================================================================
def load_marital(year, popdf, popcol):
    with open(os.path.join(CUL, f"acs5_{year}_marital_county.json")) as f:
        d = json.load(f)
    nm = pd.DataFrame(d[1:], columns=d[0])
    nm["county_fips"] = nm["state"].str.zfill(2) + nm["county"].str.zfill(3)
    nm["pop15"]   = pd.to_numeric(nm["B12001_001E"], errors="coerce")
    nm["m_never"] = pd.to_numeric(nm["B12001_003E"], errors="coerce")
    nm["f_never"] = pd.to_numeric(nm["B12001_012E"], errors="coerce")
    col = f"never_married_share_{year}"
    nm[col] = (nm["m_never"] + nm["f_never"]) / nm["pop15"]
    nm_w = nm.merge(popdf, on="county_fips", how="left").rename(columns={popcol: "wt"})
    return wmean_to_coc(nm_w, col, "wt"), int(nm[col].notna().sum())

try:
    nm12, ncty12 = load_marital(2012, pop12, "pop_2012")
    nm24, ncty24 = load_marital(2024, pop24, "pop_2024")
    nm = pd.concat([nm12, nm24], axis=1)
    nm["d_never_married"] = (nm["never_married_share_2024"]
                             - nm["never_married_share_2012"])
    pieces.append(nm.reset_index())
    coverage["sources"]["acs5_B12001_never_married"] = {"status": "ok",
        "metric": "(B12001_003E + B12001_012E) / B12001_001E (never-married / pop15+)",
        "n_county_2012": ncty12, "n_county_2024": ncty24}
except Exception as e:
    coverage["sources"]["acs5_B12001_never_married"] = {"status": "FAILED",
                                                        "error": repr(e)[:300]}

# ====================================================================
# 3. SOCIAL CAPITAL INDEX  (Rupasingha-Goetz / NERCRD, 2014 county sheet)
# ====================================================================
try:
    sc = pd.read_excel(os.path.join(CUL, "social_capital_2014.xlsx"),
                       sheet_name="2014 social capital data", engine="openpyxl")
    sc = sc[sc["FIPS"].astype(str).str.upper() != "FIPS"]
    sc["FIPS"] = pd.to_numeric(sc["FIPS"], errors="coerce")
    sc = sc.dropna(subset=["FIPS"])
    sc["county_fips"] = sc["FIPS"].apply(lambda v: str(int(v)).zfill(5))
    sc["social_capital_index"] = pd.to_numeric(sc["sk2014"], errors="coerce")
    scp = (sc.merge(pop24, on="county_fips", how="left")
             .merge(pop12, on="county_fips", how="left"))
    scp["wt"] = scp["pop_2024"].fillna(scp["pop_2012"])
    sci = wmean_to_coc(scp, "social_capital_index", "wt")
    pieces.append(sci.reset_index())
    coverage["sources"]["social_capital_index_nercrd"] = {"status": "ok",
        "file": "social_capital_2014.xlsx (sheet '2014 social capital data', col sk2014)",
        "source": "Rupasingha-Goetz county Social Capital Index (2014), Penn State "
                  "NERCRD (nercrd.psu.edu social-capital-variables-spreadsheet)",
        "n_county_sk2014": int(sc["social_capital_index"].notna().sum()),
        "note": "2014 is the most recent vintage NERCRD publishes -> single vintage; "
                "no 2012->recent change for social capital."}
except Exception as e:
    coverage["sources"]["social_capital_index_nercrd"] = {"status": "FAILED",
                                                          "error": repr(e)[:300]}

# ====================================================================
# 4. RELIGIOSITY (ARDA US Religion Census) -- NOT OBTAINED
# ====================================================================
coverage["sources"]["arda_religion_census_rcms"] = {"status": "FAILED_MISSING",
    "reason": "thearda.com download.aspx serves a JavaScript agreement-shell page "
              "(no input/viewstate/submit fields; method=post returns the same HTML, "
              "data-archive?fid=... 500 without session / JS-only with session). The "
              "RCMSCY10/RCMSCY20 .DTA/.SAV/.ASC files are delivered only after a "
              "client-side agreement interaction a scripted HTTP client cannot "
              "complete. relig_adherence_2010/2020 left missing.",
    "attempted": ["GET download.aspx?file=RCMSCY10.DTA / RCMSCY20.DTA",
                  "POST same with session cookies + browser UA",
                  "data-archive?fid=RCMSCY10 / RCMSCY20"]}

# ====================================================================
# assemble
# ====================================================================
base = pd.DataFrame({"coc_number": all_cocs})
for p in pieces:
    base = base.merge(p, on="coc_number", how="left")

# Connecticut: 2024 ACS uses 9 planning-region FIPS vs 8 county FIPS in crosswalk;
# null 2024-vintage ACS values for CT to avoid incomparable joins.
ct = base["coc_number"].astype(str).str.startswith("CT")
n_ct = int(ct.sum())
for col in ["single_person_hh_share_2024", "d_single_person",
            "never_married_share_2024", "d_never_married"]:
    if col in base.columns:
        base.loc[ct, col] = np.nan
coverage["data_corrections"] = {"connecticut_2024_acs_nulled": {
    "n_coc": n_ct,
    "reason": "ACS5 2024 reports CT as 9 planning-region FIPS (09110-09190) vs 8 "
              "county FIPS (09001-09015) in 2012 and in the county->CoC crosswalk; "
              "2024 ACS join incomparable -> single_person/never_married 2024 values "
              "and their changes set NaN for CT CoCs (2012 values retained)."}}

order = ["coc_number", "dem_share_2012", "dem_share_2020", "d_dem_share",
         "single_person_hh_share_2012", "single_person_hh_share_2024", "d_single_person",
         "never_married_share_2012", "never_married_share_2024", "d_never_married",
         "social_capital_index"]
cols = [c for c in order if c in base.columns] + \
       [c for c in base.columns if c not in order]
base = base[cols].sort_values("coc_number").reset_index(drop=True)
base.to_csv(OUT_CSV, index=False)

def nn(c):
    return int(base[c].notna().sum()) if c in base.columns else 0
for c in base.columns:
    if c != "coc_number":
        coverage["n_cocs_per_variable"][c] = nn(c)
coverage["total_cocs_in_output"] = int(len(base))
coverage["columns"] = list(base.columns)
coverage["notes"] = [
    "NO regressions; all values aggregated from downloaded county series only.",
    "Partisan lean: MIT Election Lab county presidential 2012 & 2020 two-party Dem share.",
    "single-person HH share and never-married share both available 2012 & 2024 (+change).",
    "social_capital_index = NERCRD Rupasingha-Goetz 2014 county index (sk2014); single "
    "vintage (no change) -- 2014 is the latest NERCRD publishes.",
    "Religiosity (ARDA RCMS 2010/2020) NOT obtained -- JS-gated download; flagged missing.",
    "County rates aggregated to CoC by pop-weighted mean (Dem share by major-party "
    "votes * pop-share).",
]
with open(OUT_JSON, "w") as f:
    json.dump(coverage, f, indent=2)

# ---- console report ----
print("ROWS:", len(base))
print("NN per var:", coverage["n_cocs_per_variable"])
for c in ["NY-600", "CA-600", "IL-510", "TX-700", "MS-501"]:
    row = base[base["coc_number"] == c]
    if len(row):
        print(c, {k: (round(v, 4) if isinstance(v, float) and pd.notna(v) else v)
                  for k, v in row.iloc[0].to_dict().items()})
    else:
        print(c, "NOT FOUND")
print("WROTE", OUT_CSV)
print("WROTE", OUT_JSON)
