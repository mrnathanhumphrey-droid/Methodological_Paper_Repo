"""Sanity check on precond_2 FAIL: re-test GDELT↔UCDP-GED agreement at
admin-2 × MONTH resolution instead of admin-2 × year.

Annual aggregation can wash out spatial signal when events are temporally
bursty (Darfur intercommunal cycles, Yemen-war pulses). If monthly
correlation rises substantially above the annual figure, the
year-aggregation was the constraint, not source disagreement.

If monthly stays low, source disagreement is confirmed and the locked
walk-back applies as written.

Read-only diagnostic; does NOT modify any locked state.
"""
import pathlib, sys, io, json, time
import warnings; warnings.filterwarnings("ignore")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
except Exception:
    pass
import pandas as pd
import geopandas as gpd

ROOT = pathlib.Path(r"D:/IDP")
UCDP_DIR = ROOT / "data" / "ucdp"
GDELT_DIR = ROOT / "data" / "gdelt"
GADM_DIR = ROOT / "data" / "gadm"
NOTES = ROOT / "notes"

COUNTRIES = ["colombia", "sudan", "drc", "yemen"]


def check_country_monthly(country):
    ucdp_path = UCDP_DIR / f"ucdp-ged-{country}.csv"
    gdelt_path = GDELT_DIR / f"gdelt-{country}-2014_2024.csv"
    gadm_path = GADM_DIR / f"gadm41_{country}.gpkg"
    if not (ucdp_path.exists() and gdelt_path.exists() and gadm_path.exists()):
        return {"country": country, "verdict": "MISSING"}

    print(f"\n=== {country} ===", flush=True)
    ucdp = pd.read_csv(ucdp_path, low_memory=False)
    gdelt = pd.read_csv(gdelt_path, low_memory=False, sep="\t")

    # UCDP date: prefer date_start (YYYY-MM-DD). Fall back to year + 06-15 midpoint.
    ucdp["_date"] = pd.to_datetime(ucdp["date_start"], errors="coerce")
    mask = ucdp["_date"].isna()
    if mask.any():
        ucdp.loc[mask, "_date"] = pd.to_datetime(
            ucdp.loc[mask, "year"].astype(str) + "-06-15", errors="coerce")
    ucdp["_year"] = ucdp["_date"].dt.year
    ucdp["_month"] = ucdp["_date"].dt.month
    ucdp = ucdp[(ucdp["_year"] >= 2014) & (ucdp["_year"] <= 2024)]

    # GDELT: sqldate is YYYYMMDD int
    sql = gdelt["sqldate"].astype(str)
    gdelt["_year"] = pd.to_numeric(sql.str[:4], errors="coerce")
    gdelt["_month"] = pd.to_numeric(sql.str[4:6], errors="coerce")
    gdelt = gdelt[(gdelt["_year"] >= 2014) & (gdelt["_year"] <= 2024)]

    print(f"  ucdp rows 2014-2024: {len(ucdp):,}", flush=True)
    print(f"  gdelt rows 2014-2024: {len(gdelt):,}", flush=True)

    adm2 = gpd.read_file(gadm_path, layer="ADM_ADM_2")
    if str(adm2.crs).lower() != "epsg:4326": adm2 = adm2.to_crs("EPSG:4326")

    u_g = gpd.GeoDataFrame(ucdp, geometry=gpd.points_from_xy(ucdp["longitude"], ucdp["latitude"]),
                           crs="EPSG:4326")
    g_g = gpd.GeoDataFrame(gdelt, geometry=gpd.points_from_xy(gdelt["actiongeo_long"], gdelt["actiongeo_lat"]),
                           crs="EPSG:4326")
    print(f"  sjoin...", flush=True)
    u_join = gpd.sjoin(u_g, adm2[["GID_2", "geometry"]], how="left", predicate="within")
    g_join = gpd.sjoin(g_g, adm2[["GID_2", "geometry"]], how="left", predicate="within")

    out = {"country": country}
    # Annual: admin-2 × year
    u_y = u_join.dropna(subset=["GID_2"]).groupby(["GID_2", "_year"]).size().rename("ucdp")
    g_y = g_join.dropna(subset=["GID_2"]).groupby(["GID_2", "_year"]).size().rename("gdelt")
    p_y = pd.concat([u_y, g_y], axis=1).fillna(0).reset_index()
    rho_y = p_y["ucdp"].corr(p_y["gdelt"], method="spearman")
    out["spearman_annual"] = float(rho_y)
    out["n_cells_annual"] = int(len(p_y))

    # Monthly: admin-2 × year × month
    u_m = u_join.dropna(subset=["GID_2"]).groupby(["GID_2", "_year", "_month"]).size().rename("ucdp")
    g_m = g_join.dropna(subset=["GID_2"]).groupby(["GID_2", "_year", "_month"]).size().rename("gdelt")
    p_m = pd.concat([u_m, g_m], axis=1).fillna(0).reset_index()
    rho_m = p_m["ucdp"].corr(p_m["gdelt"], method="spearman")
    out["spearman_monthly"] = float(rho_m)
    out["n_cells_monthly"] = int(len(p_m))

    # Admin-2 only (collapse over time)
    u_a = u_join.dropna(subset=["GID_2"]).groupby(["GID_2"]).size().rename("ucdp")
    g_a = g_join.dropna(subset=["GID_2"]).groupby(["GID_2"]).size().rename("gdelt")
    p_a = pd.concat([u_a, g_a], axis=1).fillna(0).reset_index()
    rho_a = p_a["ucdp"].corr(p_a["gdelt"], method="spearman")
    out["spearman_admin2_only"] = float(rho_a)
    out["n_cells_admin2_only"] = int(len(p_a))

    # Country-year (collapse over space)
    u_cy = u_join.dropna(subset=["GID_2"]).groupby(["_year"]).size().rename("ucdp")
    g_cy = g_join.dropna(subset=["GID_2"]).groupby(["_year"]).size().rename("gdelt")
    p_cy = pd.concat([u_cy, g_cy], axis=1).fillna(0).reset_index()
    rho_cy = p_cy["ucdp"].corr(p_cy["gdelt"], method="spearman")
    out["spearman_country_year"] = float(rho_cy)
    out["n_cells_country_year"] = int(len(p_cy))

    print(f"  annual:        spearman={rho_y:.3f}  cells={len(p_y)}", flush=True)
    print(f"  monthly:       spearman={rho_m:.3f}  cells={len(p_m)}", flush=True)
    print(f"  admin-2 only:  spearman={rho_a:.3f}  cells={len(p_a)}", flush=True)
    print(f"  country-year:  spearman={rho_cy:.3f}  cells={len(p_cy)}", flush=True)
    return out


def main():
    print(f"=== Sanity check on precond_2: monthly + cross-aggregation ===")
    print(f"  Locked annual threshold (>=0.6) FAILED on all 4. Testing alternative aggregations.")
    results = [check_country_monthly(c) for c in COUNTRIES]
    out_path = NOTES / "precond_2_sanity_aggregation.json"
    out_path.write_text(json.dumps({"results": results,
                                     "ran_at": time.strftime("%Y-%m-%d %H:%M:%S")},
                                    indent=2))
    print(f"\n=== summary table ===")
    print(f"  {'country':10s}  {'annual':>8s}  {'monthly':>8s}  {'adm2-only':>10s}  {'cty-year':>9s}")
    for r in results:
        if "spearman_annual" not in r: continue
        print(f"  {r['country']:10s}  {r['spearman_annual']:>8.3f}  {r['spearman_monthly']:>8.3f}  "
              f"{r['spearman_admin2_only']:>10.3f}  {r['spearman_country_year']:>9.3f}")
    print(f"\n  -> {out_path}")


if __name__ == "__main__":
    main()
