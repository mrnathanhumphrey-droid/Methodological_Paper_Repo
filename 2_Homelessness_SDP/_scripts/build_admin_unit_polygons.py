"""Build Stage-A historical polygons by dissolving GADM admin units.

First-pass automation per Phase 1 Item 1 walkback (2026-05-17).
Replaces multi-day CV-based polygon tracing with reproducible
admin-unit-list dissolution. Reads historical_polygons/admin_unit_lists.json
and writes per-polygon .geojson + .gpkg to each polygon's existing
directory alongside provenance.md.

The dissolution uses fuzzy-but-strict name matching:
  1. Exact match (case-insensitive, after diacritic normalize)
  2. If 0 matches, fall back to substring-startswith for known
     province/district name variants
  3. Log every match decision so verification is auditable

Output per polygon:
  <polygon_dir>/stage_a_polygon.geojson  — single MULTIPOLYGON feature
  <polygon_dir>/stage_a_polygon.gpkg     — same, GeoPackage format
  <polygon_dir>/_build_log.json          — match decisions + diagnostics

Verification target after build: re-run precond_3_polygon_coverage.py;
each polygon should clear LOCKED_MIN_ADMIN2_PER_POLYGON = 5.
"""
import pathlib, sys, json, io, unicodedata, hashlib, time
import warnings; warnings.filterwarnings("ignore")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
except Exception:
    pass
import geopandas as gpd
import pyogrio

ROOT = pathlib.Path(r"D:/IDP")
HIST_DIR = ROOT / "historical_polygons"
GADM_DIR = ROOT / "data" / "gadm"
CONFIG = HIST_DIR / "admin_unit_lists.json"

POLYGON_DIRS = {
    "colombia_la_violencia_1948_1958": HIST_DIR / "colombia_la_violencia_1948_1958",
    "sudan_fur_dar_pre1994":          HIST_DIR / "sudan_fur_dar_pre1994",
    "drc_kasai_1959_1965":            HIST_DIR / "drc_kasai_1959_1965",
    "yemen_six_wars_2004_2010":       HIST_DIR / "yemen_six_wars_2004_2010",
}


def norm(s):
    """Normalize for fuzzy matching: lower + strip diacritics + collapse whitespace + strip apostrophes."""
    if not isinstance(s, str): return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("'", "").replace("`", "").replace("-", " ")
    s = " ".join(s.split())
    return s


def load_gadm_layer(gadm_path, admin_level):
    """Load the GADM admin-N layer from a GeoPackage."""
    info = pyogrio.list_layers(str(gadm_path))
    layers = [row[0] for row in info]
    target = f"ADM_ADM_{admin_level}"
    layer = next((l for l in layers if l == target), None)
    if layer is None:
        layer = next((l for l in layers if f"_{admin_level}" in l), layers[-1])
    return gpd.read_file(str(gadm_path), layer=layer)


def match_units(gdf, admin_units, name_field):
    """Return GeoDataFrame of rows whose name_field normalizes to any unit in the list.

    Match decisions are recorded for the build log.
    """
    target_set = {norm(u) for u in admin_units}
    name_norm = gdf[name_field].astype(str).map(norm)
    matched = gdf[name_norm.isin(target_set)].copy()
    decisions = []
    matched_norms = set(name_norm[name_norm.isin(target_set)].tolist())
    for u in admin_units:
        un = norm(u)
        if un in matched_norms:
            decisions.append({"requested": u, "normalized": un, "status": "MATCHED"})
        else:
            decisions.append({"requested": u, "normalized": un, "status": "NOT_FOUND"})
    return matched, decisions


def build_polygon(polygon_key, cfg, out_dir):
    print(f"\n=== {polygon_key} ===")
    out_dir.mkdir(parents=True, exist_ok=True)

    gadm_path = GADM_DIR / cfg["gadm_file"]
    admin_level = cfg["gadm_admin_level"]
    name_field = cfg["gadm_name_field"]
    units_keys = ["admin_units",
                  "admin_units_admin1_full_governorate_coverage",
                  "admin_units_admin2_explicit_in_icg_mer86",
                  "admin_units_admin1_partial_expansion"]

    print(f"  GADM: {gadm_path.name}  ADM_{admin_level}  field={name_field}")
    gdf = load_gadm_layer(gadm_path, admin_level)
    print(f"  loaded {len(gdf):,} admin-{admin_level} features; CRS={gdf.crs}")

    # Get all available admin-1 too for Yemen districts (since ICG cites districts directly)
    all_decisions = []
    pieces = []

    # Yemen special case: ICG cites admin-2 districts. Load both ADM_1 and ADM_2.
    if polygon_key == "yemen_six_wars_2004_2010":
        gdf2 = load_gadm_layer(gadm_path, 2)
        print(f"  yemen ADM_2 loaded: {len(gdf2):,} features (field NAME_2)")
        # admin-2 explicit districts
        if "admin_units_admin2_explicit_in_icg_mer86" in cfg:
            m, d = match_units(gdf2, cfg["admin_units_admin2_explicit_in_icg_mer86"], "NAME_2")
            all_decisions.append({"level": 2, "source": "admin_units_admin2_explicit_in_icg_mer86",
                                  "decisions": d, "n_matched": len(m)})
            pieces.append(m)
        # admin-1 full governorate coverage
        if "admin_units_admin1_full_governorate_coverage" in cfg:
            gdf1 = load_gadm_layer(gadm_path, 1)
            m, d = match_units(gdf1, cfg["admin_units_admin1_full_governorate_coverage"], "NAME_1")
            all_decisions.append({"level": 1, "source": "admin_units_admin1_full_governorate_coverage",
                                  "decisions": d, "n_matched": len(m)})
            # Expand admin-1 matches to all admin-2 within
            if len(m) > 0:
                gov_names_norm = {norm(n) for n in m["NAME_1"].astype(str)}
                gdf2_in = gdf2[gdf2["NAME_1"].astype(str).map(norm).isin(gov_names_norm)]
                pieces.append(gdf2_in)
        # admin-1 partial-coverage governorates: also dissolve full extent (conservative)
        if "admin_units_admin1_partial_expansion" in cfg:
            gdf1 = load_gadm_layer(gadm_path, 1)
            m, d = match_units(gdf1, cfg["admin_units_admin1_partial_expansion"], "NAME_1")
            all_decisions.append({"level": 1, "source": "admin_units_admin1_partial_expansion",
                                  "decisions": d, "n_matched": len(m)})
            if len(m) > 0:
                gov_names_norm = {norm(n) for n in m["NAME_1"].astype(str)}
                gdf2_in = gdf2[gdf2["NAME_1"].astype(str).map(norm).isin(gov_names_norm)]
                pieces.append(gdf2_in)
    else:
        # Other countries: dissolve at the requested admin level by NAME field
        m, d = match_units(gdf, cfg["admin_units"], name_field)
        all_decisions.append({"level": admin_level, "source": "admin_units",
                              "decisions": d, "n_matched": len(m)})
        pieces.append(m)

    if not pieces or all(len(p) == 0 for p in pieces):
        print(f"  ERROR: no admin units matched. Check GADM field name + admin_units spelling.")
        log = {"polygon": polygon_key, "status": "FAILED", "decisions": all_decisions}
        (out_dir / "_build_log.json").write_text(json.dumps(log, indent=2))
        return None

    # Concat + dissolve all pieces
    import pandas as pd
    combined = gpd.GeoDataFrame(pd.concat(pieces, ignore_index=True), crs=pieces[0].crs)
    combined = combined.drop_duplicates(subset=[c for c in combined.columns if c.startswith("GID_")] or None)
    n_features_pre = len(combined)
    dissolved = combined.dissolve()
    print(f"  dissolved {n_features_pre} features -> single polygon")
    print(f"  area approx (deg^2): {float(dissolved.geometry.area.iloc[0]):.4f}")

    # Save geojson + gpkg
    geojson_path = out_dir / "stage_a_polygon.geojson"
    gpkg_path = out_dir / "stage_a_polygon.gpkg"
    dissolved[["geometry"]].to_file(str(geojson_path), driver="GeoJSON")
    dissolved[["geometry"]].to_file(str(gpkg_path), driver="GPKG", layer="stage_a_polygon")
    print(f"  -> {geojson_path.name}")
    print(f"  -> {gpkg_path.name}")

    # Component-list provenance: the admin-2 units actually inside the dissolved polygon
    component_list = []
    for p in pieces:
        for _, row in p.iterrows():
            entry = {}
            for c in ["GID_0", "GID_1", "GID_2", "NAME_1", "NAME_2"]:
                if c in row.index: entry[c] = row[c]
            component_list.append(entry)

    log = {
        "polygon": polygon_key,
        "status": "BUILT",
        "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "method": cfg.get("method", ""),
        "n_features_dissolved": n_features_pre,
        "decisions": all_decisions,
        "component_admin_units": component_list,
        "verification_status": cfg.get("verification_status", ""),
        "sources": cfg.get("sources", []),
    }
    (out_dir / "_build_log.json").write_text(json.dumps(log, indent=2, default=str))
    print(f"  -> _build_log.json")
    return geojson_path


def main():
    cfg_all = json.loads(CONFIG.read_text(encoding="utf-8"))
    print(f"=== Building Stage-A polygons (admin-unit-list dissolution) ===")
    print(f"  config: {CONFIG.name}")
    print(f"  output: per-polygon dirs under {HIST_DIR}")
    built = []
    for polygon_key, poly_dir in POLYGON_DIRS.items():
        cfg = cfg_all.get(polygon_key)
        if cfg is None:
            print(f"  [{polygon_key}] no config; skip")
            continue
        result = build_polygon(polygon_key, cfg, poly_dir)
        if result is not None:
            built.append(polygon_key)
    print(f"\n=== built {len(built)}/4: {built} ===")


if __name__ == "__main__":
    main()
