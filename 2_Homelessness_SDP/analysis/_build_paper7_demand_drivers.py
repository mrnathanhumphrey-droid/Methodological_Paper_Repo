"""
MECHANICAL data-engineering build for Paper 7 CoC-level rent-demand drivers.
NO regressions. NO hand-coded values. Only data downloaded/read from disk.

Outputs:
  D:/IDP/analysis/paper7_demand_drivers_coc.csv
  D:/IDP/analysis/paper7_demand_drivers_coverage.json

Sources actually used:
  1. Employment + wage: BLS QCEW annual_by_area zips (2012, 2023), local copies in
     D:/IDP/data/paper7/demand_drivers/qcew_{year}_annual_by_area.zip
     -> County, Total Covered (agglvl_code==70, own_code==0):
        annual_avg_emplvl (employment), annual_avg_wkly_wage (avg weekly wage)
  2. In-migration: IRS SOI county inflow (local D:/Migration/data/raw/irs_soi),
     latest file countyinflow2223.csv, "Total Migration-US and Foreign" row
     (y1_statefips==96, y1_countyfips==000); n2 = in-migrant exemptions (persons).
  3. Population: Census ACS5 B01003 county total population, 2012 and 2024 (saved JSON).

Crosswalk: D:/IDP/data/paper7/coc_crosswalk/county_coc_match.csv (latin-1),
  county_fips, coc_number, pct_cnty_pop_coc.  County series allocated to CoC by
  pct_cnty_pop_coc/100 (population share of the county that falls in the CoC).
CoC population denominator: coc_population.csv.
"""
import json, zipfile, io, os
import pandas as pd
import numpy as np

DD   = r"D:/IDP/data/paper7/demand_drivers"
XW   = r"D:/IDP/data/paper7/coc_crosswalk/county_coc_match.csv"
POPF = r"D:/IDP/data/paper7/coc_crosswalk/coc_population.csv"
IRS  = r"D:/Migration/data/raw/irs_soi/countyinflow2223.csv"
OUT_CSV = r"D:/IDP/analysis/paper7_demand_drivers_coc.csv"
OUT_JSON= r"D:/IDP/analysis/paper7_demand_drivers_coverage.json"

coverage = {"sources": {}, "drivers_n_cocs": {}, "notes": []}

# ---------- crosswalk ----------
xw = pd.read_csv(XW, encoding="latin-1", dtype={"county_fips": str})
xw["county_fips"] = xw["county_fips"].str.strip().str.zfill(5)
xw["w"] = pd.to_numeric(xw["pct_cnty_pop_coc"], errors="coerce") / 100.0
xw = xw[["county_fips", "coc_number", "w"]].dropna()
coverage["sources"]["crosswalk"] = {"status": "ok", "rows": int(len(xw)),
                                    "n_coc": int(xw["coc_number"].nunique()),
                                    "n_county": int(xw["county_fips"].nunique())}

cocpop = pd.read_csv(POPF, encoding="latin-1")
cocpop = cocpop[["coc_number", "total_population"]].copy()
cocpop["total_population"] = pd.to_numeric(cocpop["total_population"], errors="coerce")

# ---------- helpers ----------
def agg_count_to_coc(county_df, value_col):
    """Allocate a county COUNT to CoCs by population share, then sum per CoC."""
    m = xw.merge(county_df, on="county_fips", how="inner")
    m["alloc"] = m[value_col] * m["w"]
    return m.groupby("coc_number")["alloc"].sum().rename(value_col)

def agg_rate_to_coc(county_df, value_col, weight_col):
    """Weighted mean of a county RATE to CoC, weight = weight_col * pop-share."""
    m = xw.merge(county_df, on="county_fips", how="inner")
    m["wt"] = m[weight_col] * m["w"]
    m = m.dropna(subset=[value_col, "wt"])
    m = m[m["wt"] > 0]
    g = m.groupby("coc_number").apply(
        lambda d: np.average(d[value_col], weights=d["wt"]), include_groups=False)
    return g.rename(value_col)

# ---------- 1. QCEW employment + wage (2012, 2023) ----------
def load_qcew(year):
    zpath = os.path.join(DD, f"qcew_{year}_annual_by_area.zip")
    z = zipfile.ZipFile(zpath)
    rows = []
    for n in z.namelist():
        if not n.lower().endswith(".csv"):
            continue
        # county members carry 5-digit fips in the name; skip statewide/national/MSA
        with z.open(n) as f:
            df = pd.read_csv(io.TextIOWrapper(f, "latin-1"),
                             dtype={"area_fips": str, "industry_code": str})
        sub = df[(df["agglvl_code"] == 70) & (df["own_code"] == 0)]
        if len(sub) == 0:
            continue
        for _, r in sub.iterrows():
            fips = str(r["area_fips"]).strip().zfill(5)
            if not fips.isdigit():
                continue
            rows.append((fips, r["annual_avg_emplvl"], r["annual_avg_wkly_wage"]))
    out = pd.DataFrame(rows, columns=["county_fips", f"emp_{year}", f"wkly_wage_{year}"])
    out[f"emp_{year}"] = pd.to_numeric(out[f"emp_{year}"], errors="coerce")
    out[f"wkly_wage_{year}"] = pd.to_numeric(out[f"wkly_wage_{year}"], errors="coerce")
    # county-total-covered should be unique per fips; keep last if dup
    out = out.dropna(subset=["county_fips"]).drop_duplicates("county_fips", keep="last")
    return out

qcew_ok = True
try:
    q12 = load_qcew(2012)
    q23 = load_qcew(2023)
    coverage["sources"]["qcew_2012"] = {"status": "ok", "n_county": int(len(q12))}
    coverage["sources"]["qcew_2023"] = {"status": "ok", "n_county": int(len(q23))}
except Exception as e:
    qcew_ok = False
    coverage["sources"]["qcew"] = {"status": "FAILED", "error": repr(e)[:200]}

emp_growth = None
wage_coc = None
if qcew_ok:
    # employment growth: aggregate counts both years, then pct change
    e12 = agg_count_to_coc(q12.rename(columns={"emp_2012": "v"})[["county_fips", "v"]], "v").rename("emp_2012")
    e23 = agg_count_to_coc(q23.rename(columns={"emp_2023": "v"})[["county_fips", "v"]], "v").rename("emp_2023")
    emp = pd.concat([e12, e23], axis=1)
    emp["employment_growth_12_23"] = (emp["emp_2023"] - emp["emp_2012"]) / emp["emp_2012"]
    emp_growth = emp[["emp_2012", "emp_2023", "employment_growth_12_23"]].reset_index()

    # avg weekly wage 2023: employment-weighted county mean to CoC
    wdf = q23.rename(columns={"wkly_wage_2023": "v", "emp_2023": "ew"})[["county_fips", "v", "ew"]]
    w23 = agg_rate_to_coc(wdf, "v", "ew").rename("avg_weekly_wage_2023")
    # wage 2012 too, for change
    wdf12 = q12.rename(columns={"wkly_wage_2012": "v", "emp_2012": "ew"})[["county_fips", "v", "ew"]]
    w12 = agg_rate_to_coc(wdf12, "v", "ew").rename("avg_weekly_wage_2012")
    wage_coc = pd.concat([w12, w23], axis=1).reset_index()

# ---------- 2. IRS in-migration (2022-23) ----------
mig_coc = None
try:
    mig = pd.read_csv(IRS, dtype=str, encoding="latin-1")
    for c in ["y2_statefips", "y2_countyfips", "y1_statefips", "y1_countyfips"]:
        mig[c] = mig[c].str.strip()
    tot = mig[(mig["y1_statefips"] == "96") & (mig["y1_countyfips"] == "000")].copy()
    tot["county_fips"] = tot["y2_statefips"].str.zfill(2) + tot["y2_countyfips"].str.zfill(3)
    tot["inmig_n2"] = pd.to_numeric(tot["n2"], errors="coerce")
    tot = tot[tot["county_fips"].str.isdigit()][["county_fips", "inmig_n2"]]
    inmig = agg_count_to_coc(tot.rename(columns={"inmig_n2": "v"}), "v").rename("inmig_persons")
    mig_df = inmig.reset_index().merge(cocpop, on="coc_number", how="left")
    mig_df["in_migration_rate"] = mig_df["inmig_persons"] / mig_df["total_population"]
    mig_coc = mig_df[["coc_number", "inmig_persons", "in_migration_rate"]]
    coverage["sources"]["irs_inflow_2223"] = {"status": "ok",
                                              "file": os.path.basename(IRS),
                                              "n_dest_county": int(len(tot)),
                                              "note": "n2 = in-migrant exemptions (persons), Total Migration US+Foreign row"}
except Exception as e:
    coverage["sources"]["irs_inflow_2223"] = {"status": "FAILED", "error": repr(e)[:200]}

# ---------- 3. Census ACS population (2012, 2024) ----------
def load_acs(year):
    with open(os.path.join(DD, f"acs5_{year}_B01003_county.json")) as f:
        data = json.load(f)
    df = pd.DataFrame(data[1:], columns=data[0])
    df["county_fips"] = df["state"].str.zfill(2) + df["county"].str.zfill(3)
    df[f"pop_{year}"] = pd.to_numeric(df["B01003_001E"], errors="coerce")
    return df[["county_fips", f"pop_{year}"]]

pop_coc = None
try:
    p12 = load_acs(2012)
    p24 = load_acs(2024)
    coverage["sources"]["acs_2012"] = {"status": "ok", "n_county": int(len(p12))}
    coverage["sources"]["acs_2024"] = {"status": "ok", "n_county": int(len(p24))}
    pc12 = agg_count_to_coc(p12.rename(columns={"pop_2012": "v"}), "v").rename("pop_2012")
    pc24 = agg_count_to_coc(p24.rename(columns={"pop_2024": "v"}), "v").rename("pop_2024")
    pop = pd.concat([pc12, pc24], axis=1)
    pop["population_growth_12_24"] = (pop["pop_2024"] - pop["pop_2012"]) / pop["pop_2012"]
    pop_coc = pop[["pop_2012", "pop_2024", "population_growth_12_24"]].reset_index()
except Exception as e:
    coverage["sources"]["acs"] = {"status": "FAILED", "error": repr(e)[:200]}

# ---------- assemble ----------
base = cocpop[["coc_number"]].copy()
for piece in [emp_growth, wage_coc, mig_coc, pop_coc]:
    if piece is not None:
        base = base.merge(piece, on="coc_number", how="left")

base = base.sort_values("coc_number").reset_index(drop=True)

# ---------- Connecticut FIPS-transition correction ----------
# ACS switched CT from 8 county FIPS (09001-09015) to 9 planning-region FIPS
# (09110-09190) circa 2022.  The CoC<->county crosswalk uses the OLD codes, so
# the 2024 ACS population join is incomparable for CT -> spurious pop drops.
# Null CT pop_2024 / population_growth so the parent does not regress on garbage.
ct_mask = base["coc_number"].astype(str).str.startswith("CT")
if "population_growth_12_24" in base.columns:
    n_ct = int(ct_mask.sum())
    base.loc[ct_mask, ["pop_2024", "population_growth_12_24"]] = np.nan
    coverage.setdefault("notes", [])
    coverage["data_corrections"] = {
        "connecticut_pop_2024_nulled": {
            "n_coc": n_ct,
            "reason": "ACS5 2024 reports CT as 9 planning-region FIPS (09110-09190) "
                      "vs 8 county FIPS (09001-09015) in 2012 and in the crosswalk; "
                      "2024 population join incomparable. pop_2024 and "
                      "population_growth_12_24 set to NaN for CT CoCs."
        }
    }

base.to_csv(OUT_CSV, index=False)

# coverage counts (non-null per driver)
def nn(col):
    return int(base[col].notna().sum()) if col in base.columns else 0
coverage["drivers_n_cocs"] = {
    "employment_growth_12_23": nn("employment_growth_12_23"),
    "avg_weekly_wage_2023": nn("avg_weekly_wage_2023"),
    "avg_weekly_wage_2012": nn("avg_weekly_wage_2012"),
    "in_migration_rate": nn("in_migration_rate"),
    "population_growth_12_24": nn("population_growth_12_24"),
}
coverage["total_cocs_in_output"] = int(len(base))
coverage["columns"] = list(base.columns)
coverage["notes"] = [
    "BLS LAUS direct download blocked (HTTP 403, Akamai bot protection) on all paths/UAs; "
    "employment growth sourced from BLS QCEW annual_avg_emplvl (County Total Covered) instead.",
    "Wage metric = QCEW annual_avg_wkly_wage (County Total Covered), employment-weighted to CoC. "
    "High-wage-industry share NOT built (supersector rows absent at own_code 0; disclosure-suppressed at private level).",
    "Employment growth window is 2012->2023 (latest QCEW annual available), not 2024.",
    "Population growth window is ACS5 2012->2024.",
    "In-migration from IRS SOI countyinflow2223 (tax year 2022->2023), single latest year.",
    "County counts allocated to CoCs by pct_cnty_pop_coc; wage allocated as employment-weighted mean.",
]
with open(OUT_JSON, "w") as f:
    json.dump(coverage, f, indent=2)

print("OUTPUT ROWS:", len(base))
print(coverage["drivers_n_cocs"])
for c in ["NY-600", "CA-600", "IL-510"]:
    row = base[base["coc_number"] == c]
    if len(row):
        print(c, row.to_dict("records")[0])
    else:
        print(c, "NOT FOUND")
print("WROTE", OUT_CSV)
print("WROTE", OUT_JSON)
