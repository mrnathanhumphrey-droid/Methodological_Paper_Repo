"""DRC Kasai 1959-1965 atrocity-count first-pass — Phase 1 Item 2.

Per Phase 0 redline Entry 002-C (DRC source-list amendment): UCDP-GED +
EOSV both start at 1989, so Kasai 1959-1965 cannot be coded from event
databases. Manual academic-history coding from Young & Turner +
Lemarchand + Stearns + CRDA UCL Louvain is the locked alternative.

This Phase 1 first-pass uses the documented-territoire approach:
  - 12 territoires explicitly named in the literature as Kasai expulsion
    sites (Luba expulsion from Lulua-led west Kasai → return to South
    Kasai homeland 1959-1965)
  - Coded as 2 = HIGH (explicitly named in academic sources)
  - All other admin-2 inside Kasai dissolved polygon = 1 = MEDIUM
    (within province-level expulsion zone but not explicitly named)
  - All admin-2 outside polygon = 0 = NOT IN ZONE

The 0/1/2 coding feeds the Stan model's log1p(atrocity_count) covariate
under H_HISTORICAL_INTENSITY. True per-territoire event-count tallying
is deferred to the verification pass when academic source PDFs become
retrievable (Young & Turner Internet Archive is currently controlled-
digital-lending restricted; alternative path is local university library
or institutional inter-library loan).
"""
import pathlib, sys, json, io, time, hashlib
import warnings; warnings.filterwarnings("ignore")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
except Exception:
    pass
import geopandas as gpd

ROOT = pathlib.Path(r"D:/IDP")
GADM_DRC = ROOT / "data" / "gadm" / "gadm41_drc.gpkg"
POLY = ROOT / "historical_polygons" / "drc_kasai_1959_1965" / "stage_a_polygon.geojson"
OUT_CSV = ROOT / "data" / "atrocity_drc_kasai_1959_1965_first_pass.csv"
OUT_LOG = ROOT / "data" / "_atrocity_drc_kasai_build_log.json"
MANIFEST = ROOT / "manifest.json"

# 12 documented territoires from academic literature (Young & Turner +
# Lemarchand + Stearns + Wikipedia Invasion of South Kasai cross-cite).
# Coded HIGH (atrocity_count = 2).
DOCUMENTED_TERRITOIRES_HIGH = {
    "Luiza", "Demba", "Dimbelenge", "Mweka", "Tshikapa", "Luebo",
    "Ilebo", "Lusambo", "Lodja", "Lubefu", "Mwene-Ditu", "Kabinda",
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    print(f"=== DRC Kasai atrocity-count first-pass build ===")

    gdf = gpd.read_file(str(GADM_DRC), layer="ADM_ADM_2")
    poly = gpd.read_file(str(POLY))
    if poly.crs is None: poly.set_crs("EPSG:4326", inplace=True)
    if str(poly.crs).lower() != "epsg:4326": poly = poly.to_crs("EPSG:4326")
    if str(gdf.crs).lower() != "epsg:4326": gdf = gdf.to_crs("EPSG:4326")
    poly_geom = poly.geometry.union_all() if hasattr(poly.geometry, "union_all") else poly.unary_union

    in_polygon = gdf.intersects(poly_geom)
    is_doc = gdf["NAME_2"].isin(DOCUMENTED_TERRITOIRES_HIGH)

    gdf["in_kasai_polygon"] = in_polygon.astype(int)
    gdf["atrocity_count_first_pass"] = 0
    gdf.loc[in_polygon, "atrocity_count_first_pass"] = 1
    gdf.loc[is_doc, "atrocity_count_first_pass"] = 2
    gdf["atrocity_coding_source"] = "OUT_OF_POLYGON"
    gdf.loc[in_polygon, "atrocity_coding_source"] = "WITHIN_KASAI_PROVINCE_POLYGON"
    gdf.loc[is_doc, "atrocity_coding_source"] = "DOCUMENTED_TERRITOIRE_HIGH (Young+Turner / Lemarchand / Stearns / Wikipedia_cross_cite)"

    cols = ["GID_0", "GID_1", "GID_2", "NAME_1", "NAME_2",
            "in_kasai_polygon", "atrocity_count_first_pass", "atrocity_coding_source"]
    df_out = gdf[cols].copy()
    df_out.to_csv(OUT_CSV, index=False, encoding="utf-8")

    n_high = int((df_out["atrocity_count_first_pass"] == 2).sum())
    n_med = int((df_out["atrocity_count_first_pass"] == 1).sum())
    n_zero = int((df_out["atrocity_count_first_pass"] == 0).sum())

    print(f"  total admin-2: {len(df_out):,}")
    print(f"  HIGH (=2, documented territoire): {n_high}")
    print(f"  MEDIUM (=1, in polygon not explicitly documented): {n_med}")
    print(f"  ZERO (=0, out of polygon): {n_zero}")

    # Print the HIGH list for QA
    high = df_out[df_out["atrocity_count_first_pass"] == 2][["NAME_1", "NAME_2"]]
    print(f"\n  HIGH-coded territoires ({len(high)}):")
    for _, row in high.iterrows():
        print(f"    {row['NAME_1']:25s} / {row['NAME_2']}")

    log = {
        "build_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "method": "Phase 1 first-pass admin-2 coding (0/1/2) from documented-territoire list + Kasai dissolved polygon intersection",
        "documented_territoires_high": sorted(DOCUMENTED_TERRITOIRES_HIGH),
        "n_high": n_high,
        "n_medium": n_med,
        "n_zero": n_zero,
        "verification_status": "FIRST_PASS — true per-territoire event counts deferred pending Young & Turner / Lemarchand / Stearns PDF retrieval",
        "feeds": "Stan H_HISTORICAL_INTENSITY: log1p(atrocity_count_first_pass)",
        "sources": [
            "Young C. & Turner T., The Rise and Decline of the Zairian State (1985) — Kasai chapter",
            "Lemarchand R., Political Awakening in the Belgian Congo (1964)",
            "Stearns J.K., Dancing in the Glory of Monsters (2011) — ch. 1",
            "Wikipedia Invasion of South Kasai (2026-05-17 snapshot, multi-source-cross-cited)",
        ],
    }
    OUT_LOG.write_text(json.dumps(log, indent=2))
    print(f"\n  -> {OUT_CSV.relative_to(ROOT)}")
    print(f"  -> {OUT_LOG.relative_to(ROOT)}")

    # Manifest entry
    manifest = {}
    if MANIFEST.exists():
        try: manifest = json.loads(MANIFEST.read_text())
        except: manifest = {}
    manifest.setdefault("files", [])
    manifest["files"] = [m for m in manifest["files"]
                         if m.get("filename") != str(OUT_CSV.relative_to(ROOT))]
    manifest["files"].append({
        "source": "DRC Kasai 1959-1965 atrocity-count first-pass (admin-2 0/1/2 coding from documented territoire list)",
        "filename": str(OUT_CSV.relative_to(ROOT)),
        "sha256": sha256(OUT_CSV),
        "size_bytes": OUT_CSV.stat().st_size,
        "row_count": len(df_out),
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    })
    manifest["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    MANIFEST.write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
