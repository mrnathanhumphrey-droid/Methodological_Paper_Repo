"""Sanity check: filter GDELT to QuadClass=4 (Material Conflict) — the
subset closest to UCDP-GED's fatal-armed-event definition. Re-test
Spearman at the same aggregations.

GDELT QuadClass codes:
  1 = Verbal Cooperation
  2 = Material Cooperation
  3 = Verbal Conflict
  4 = Material Conflict   <-- fatal/armed events, closest to UCDP

If QuadClass=4 lifts the correlation to >=0.6 at any aggregation, the
locked threshold was salvageable by a definitional subset. If not, the
walk-back stands as documented.

Read-only diagnostic.
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


def check_country(country):
    ucdp_path = UCDP_DIR / f"ucdp-ged-{country}.csv"
    gdelt_path = GDELT_DIR / f"gdelt-{country}-2014_2024.csv"
    gadm_path = GADM_DIR / f"gadm41_{country}.gpkg"
    print(f"\n=== {country} ===", flush=True)
    ucdp = pd.read_csv(ucdp_path, low_memory=False)
    gdelt = pd.read_csv(gdelt_path, low_memory=False, sep="\t")
    n_gdelt_all = len(gdelt)
    gdelt = gdelt[gdelt["quadclass"] == 4]
    print(f"  gdelt: {n_gdelt_all:,} total -> {len(gdelt):,} QuadClass=4", flush=True)

    ucdp["_date"] = pd.to_datetime(ucdp["date_start"], errors="coerce")
    mask = ucdp["_date"].isna()
    if mask.any():
        ucdp.loc[mask, "_date"] = pd.to_datetime(
            ucdp.loc[mask, "year"].astype(str) + "-06-15", errors="coerce")
    ucdp["_year"] = ucdp["_date"].dt.year
    ucdp["_month"] = ucdp["_date"].dt.month
    ucdp = ucdp[(ucdp["_year"] >= 2014) & (ucdp["_year"] <= 2024)]

    sql = gdelt["sqldate"].astype(str)
    gdelt["_year"] = pd.to_numeric(sql.str[:4], errors="coerce")
    gdelt["_month"] = pd.to_numeric(sql.str[4:6], errors="coerce")
    gdelt = gdelt[(gdelt["_year"] >= 2014) & (gdelt["_year"] <= 2024)]

    print(f"  ucdp rows 2014-2024: {len(ucdp):,}", flush=True)
    print(f"  gdelt rows 2014-2024 QuadClass=4: {len(gdelt):,}", flush=True)
    print(f"  volume ratio gdelt/ucdp: {len(gdelt)/max(len(ucdp),1):.1f}x", flush=True)

    adm2 = gpd.read_file(gadm_path, layer="ADM_ADM_2")
    if str(adm2.crs).lower() != "epsg:4326": adm2 = adm2.to_crs("EPSG:4326")
    u_g = gpd.GeoDataFrame(ucdp, geometry=gpd.points_from_xy(ucdp["longitude"], ucdp["latitude"]),
                           crs="EPSG:4326")
    g_g = gpd.GeoDataFrame(gdelt, geometry=gpd.points_from_xy(gdelt["actiongeo_long"], gdelt["actiongeo_lat"]),
                           crs="EPSG:4326")
    u_join = gpd.sjoin(u_g, adm2[["GID_2", "geometry"]], how="left", predicate="within")
    g_join = gpd.sjoin(g_g, adm2[["GID_2", "geometry"]], how="left", predicate="within")

    out = {"country": country, "n_gdelt_qc4": len(gdelt), "n_ucdp": len(ucdp)}
    # Annual
    u_y = u_join.dropna(subset=["GID_2"]).groupby(["GID_2", "_year"]).size().rename("ucdp")
    g_y = g_join.dropna(subset=["GID_2"]).groupby(["GID_2", "_year"]).size().rename("gdelt")
    p_y = pd.concat([u_y, g_y], axis=1).fillna(0).reset_index()
    out["spearman_annual"] = float(p_y["ucdp"].corr(p_y["gdelt"], method="spearman"))
    out["n_cells_annual"] = len(p_y)

    # Monthly
    u_m = u_join.dropna(subset=["GID_2"]).groupby(["GID_2", "_year", "_month"]).size().rename("ucdp")
    g_m = g_join.dropna(subset=["GID_2"]).groupby(["GID_2", "_year", "_month"]).size().rename("gdelt")
    p_m = pd.concat([u_m, g_m], axis=1).fillna(0).reset_index()
    out["spearman_monthly"] = float(p_m["ucdp"].corr(p_m["gdelt"], method="spearman"))
    out["n_cells_monthly"] = len(p_m)

    # Admin-2 only
    u_a = u_join.dropna(subset=["GID_2"]).groupby(["GID_2"]).size().rename("ucdp")
    g_a = g_join.dropna(subset=["GID_2"]).groupby(["GID_2"]).size().rename("gdelt")
    p_a = pd.concat([u_a, g_a], axis=1).fillna(0).reset_index()
    out["spearman_admin2_only"] = float(p_a["ucdp"].corr(p_a["gdelt"], method="spearman"))
    out["n_cells_admin2_only"] = len(p_a)

    # Country-year
    u_cy = u_join.dropna(subset=["GID_2"]).groupby(["_year"]).size().rename("ucdp")
    g_cy = g_join.dropna(subset=["GID_2"]).groupby(["_year"]).size().rename("gdelt")
    p_cy = pd.concat([u_cy, g_cy], axis=1).fillna(0).reset_index()
    out["spearman_country_year"] = float(p_cy["ucdp"].corr(p_cy["gdelt"], method="spearman"))
    out["n_cells_country_year"] = len(p_cy)

    print(f"  annual:        spearman={out['spearman_annual']:.3f}  cells={out['n_cells_annual']}", flush=True)
    print(f"  monthly:       spearman={out['spearman_monthly']:.3f}  cells={out['n_cells_monthly']}", flush=True)
    print(f"  admin-2 only:  spearman={out['spearman_admin2_only']:.3f}  cells={out['n_cells_admin2_only']}", flush=True)
    print(f"  country-year:  spearman={out['spearman_country_year']:.3f}  cells={out['n_cells_country_year']}", flush=True)
    return out


def main():
    print(f"=== Sanity check: GDELT QuadClass=4 (Material Conflict) only ===")
    results = [check_country(c) for c in COUNTRIES]
    out_path = NOTES / "precond_2_sanity_quadclass4.json"
    out_path.write_text(json.dumps({"results": results,
                                     "ran_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                                     "note": "GDELT filtered to QuadClass=4 (Material Conflict) as the closest GDELT subset to UCDP-GED's fatal-armed-event definition"},
                                    indent=2))
    print(f"\n=== QuadClass=4 summary ===")
    print(f"  {'country':10s}  {'annual':>8s}  {'monthly':>8s}  {'adm2-only':>10s}  {'cty-year':>9s}  {'gdelt/ucdp ratio':>17s}")
    for r in results:
        ratio = r['n_gdelt_qc4'] / max(r['n_ucdp'], 1)
        print(f"  {r['country']:10s}  {r['spearman_annual']:>8.3f}  {r['spearman_monthly']:>8.3f}  "
              f"{r['spearman_admin2_only']:>10.3f}  {r['spearman_country_year']:>9.3f}  {ratio:>16.1f}x")
    print(f"\n  -> {out_path}")


if __name__ == "__main__":
    main()
