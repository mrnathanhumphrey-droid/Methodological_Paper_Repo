"""Build admin-2 × year IDP panels from HDX HAPI v2 fetch.

HDX HAPI v2 already publishes the harmonized DTM at admin-2 resolution.
This script collapses round-level records into admin-2 × year using:
  - Annual IDP figure = max population value across all rounds whose
    reference_period_start falls within calendar year Y, per admin-2
  - Sub-aggregations also emitted: mean, median, n_rounds_in_year

(Max captures the peak displacement state in the year, which is the
canonical IDP year-figure convention used by UNHCR/IDMC. Mean is
included as a sensitivity column.)

Output per country: data/panels/idp_admin2_annual_<country>.csv
Output combined:    data/panels/idp_admin2_annual.csv

Joins to GADM admin-2 via admin2_code (HAPI) ↔ GID_2 (GADM 4.1).
Adds:
  - in_polygon  (Stage-A polygon intersection, binary)
  - atrocity_count_first_pass  (DRC only; from build_drc_atrocity_first_pass.py)
"""
import pathlib, sys, json, io, time, hashlib
import warnings; warnings.filterwarnings("ignore")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
except Exception:
    pass
import pandas as pd
import geopandas as gpd

ROOT = pathlib.Path(r"D:/IDP")
DTM_DIR = ROOT / "data" / "dtm"
GADM_DIR = ROOT / "data" / "gadm"
HIST_DIR = ROOT / "historical_polygons"
ATROCITY_DRC = ROOT / "data" / "atrocity_drc_kasai_1959_1965_first_pass.csv"
OUT_DIR = ROOT / "data" / "panels"
MANIFEST = ROOT / "manifest.json"

COUNTRIES = {
    "sudan":  {"hdx_csv": "sudan/hdx_idps_admin2_sudan.csv",  "gadm": "gadm41_sudan.gpkg",
               "polygon": "sudan_fur_dar_pre1994",  "iso3": "SDN"},
    "drc":    {"hdx_csv": "drc/hdx_idps_admin2_drc.csv",      "gadm": "gadm41_drc.gpkg",
               "polygon": "drc_kasai_1959_1965",   "iso3": "COD"},
    "yemen":  {"hdx_csv": "yemen/hdx_idps_admin2_yemen.csv",  "gadm": "gadm41_yemen.gpkg",
               "polygon": "yemen_six_wars_2004_2010", "iso3": "YEM"},
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_country_panel(country_slug, cfg):
    print(f"\n=== {country_slug} ===")
    csv_path = DTM_DIR / cfg["hdx_csv"]
    if not csv_path.exists():
        print(f"  ERROR: {csv_path} not found; skip")
        return None
    df = pd.read_csv(csv_path, encoding="utf-8")
    print(f"  raw rows: {len(df):,}")
    df["reference_period_start"] = pd.to_datetime(df["reference_period_start"], errors="coerce")
    df["year"] = df["reference_period_start"].dt.year.astype("Int64")
    df = df.dropna(subset=["year"])
    print(f"  with valid year: {len(df):,}  range {int(df['year'].min())}..{int(df['year'].max())}")

    # Aggregate to admin-2 × year
    agg = (df.groupby(["admin2_code", "admin2_name", "admin1_code", "admin1_name", "year"])
             .agg(idp_max=("population", "max"),
                  idp_mean=("population", "mean"),
                  idp_median=("population", "median"),
                  n_rounds_in_year=("reporting_round", "nunique"))
             .reset_index())
    agg["country"] = country_slug
    agg["iso3"] = cfg["iso3"]
    print(f"  admin2-year rows: {len(agg):,}")
    print(f"    unique admin-2: {agg['admin2_code'].nunique()}")
    print(f"    unique years: {sorted(agg['year'].unique().tolist())}")

    # Polygon intersection — annotate admin-2 codes that are inside Stage-A polygon
    poly_path = HIST_DIR / cfg["polygon"] / "stage_a_polygon.geojson"
    gadm_path = GADM_DIR / cfg["gadm"]
    if poly_path.exists() and gadm_path.exists():
        gdf = gpd.read_file(str(gadm_path), layer="ADM_ADM_2")
        poly = gpd.read_file(str(poly_path))
        if poly.crs is None: poly.set_crs("EPSG:4326", inplace=True)
        if str(poly.crs).lower() != "epsg:4326": poly = poly.to_crs("EPSG:4326")
        if str(gdf.crs).lower() != "epsg:4326": gdf = gdf.to_crs("EPSG:4326")
        poly_geom = poly.geometry.union_all() if hasattr(poly.geometry, "union_all") else poly.unary_union
        in_polygon_mask = gdf.intersects(poly_geom)
        gdf["in_polygon"] = in_polygon_mask.astype(int)

        # Join by name — GADM uses NAME_2; HDX HAPI uses admin2_name. May not match exactly.
        gadm_names = gdf[["NAME_2", "GID_2", "NAME_1", "in_polygon"]].copy()
        gadm_names["join_key"] = gadm_names["NAME_2"].astype(str).str.lower().str.strip()
        agg["join_key"] = agg["admin2_name"].astype(str).str.lower().str.strip()
        joined = agg.merge(gadm_names[["join_key", "GID_2", "in_polygon"]],
                           on="join_key", how="left")
        joined = joined.drop(columns=["join_key"])

        n_joined = joined["GID_2"].notna().sum()
        print(f"  GADM admin-2 name joined: {n_joined:,}/{len(joined):,}")
        n_in_poly = (joined["in_polygon"] == 1).sum()
        print(f"  in_polygon=1 rows: {n_in_poly:,}")
        agg = joined
    else:
        print(f"  skip polygon join (missing files)")
        agg["GID_2"] = None
        agg["in_polygon"] = 0

    # DRC atrocity-count merge
    if country_slug == "drc" and ATROCITY_DRC.exists():
        atroc = pd.read_csv(ATROCITY_DRC, encoding="utf-8")
        atroc_lookup = atroc[["NAME_2", "atrocity_count_first_pass"]].copy()
        atroc_lookup["join_key"] = atroc_lookup["NAME_2"].astype(str).str.lower().str.strip()
        agg["join_key"] = agg["admin2_name"].astype(str).str.lower().str.strip()
        agg = agg.merge(atroc_lookup[["join_key", "atrocity_count_first_pass"]],
                        on="join_key", how="left").drop(columns=["join_key"])
        agg["atrocity_count_first_pass"] = agg["atrocity_count_first_pass"].fillna(0).astype(int)
        n_high = (agg["atrocity_count_first_pass"] == 2).sum()
        print(f"  DRC atrocity merge: {n_high} HIGH-coded admin-2-year rows")
    else:
        agg["atrocity_count_first_pass"] = 0

    return agg


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== Building admin-2 × year IDP panels from HDX HAPI v2 ===")

    panels = []
    for country_slug, cfg in COUNTRIES.items():
        p = build_country_panel(country_slug, cfg)
        if p is None: continue
        out_path = OUT_DIR / f"idp_admin2_annual_{country_slug}.csv"
        p.to_csv(out_path, index=False, encoding="utf-8")
        print(f"    -> {out_path.relative_to(ROOT)}")
        panels.append(p)

    if panels:
        combined = pd.concat(panels, ignore_index=True)
        out_combined = OUT_DIR / "idp_admin2_annual.csv"
        combined.to_csv(out_combined, index=False, encoding="utf-8")
        print(f"\n=== combined panel: {out_combined.relative_to(ROOT)} ===")
        print(f"  total admin-2-year rows: {len(combined):,}")
        for c in ["sudan", "drc", "yemen"]:
            sub = combined[combined["country"] == c]
            print(f"    {c}: {len(sub):,} rows; "
                  f"{sub['admin2_code'].nunique()} admin-2; "
                  f"{(sub['in_polygon']==1).sum()} in-polygon rows")

        # Manifest entry
        manifest = {}
        if MANIFEST.exists():
            try: manifest = json.loads(MANIFEST.read_text())
            except: manifest = {}
        manifest.setdefault("files", [])
        manifest["files"] = [m for m in manifest["files"]
                             if m.get("filename") != str(out_combined.relative_to(ROOT))]
        manifest["files"].append({
            "source": "Combined admin-2 × year IDP panel from HDX HAPI v2 (Phase 1 first-pass; Colombia gap)",
            "filename": str(out_combined.relative_to(ROOT)),
            "sha256": sha256(out_combined),
            "size_bytes": out_combined.stat().st_size,
            "row_count": len(combined),
            "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        manifest["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        MANIFEST.write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
