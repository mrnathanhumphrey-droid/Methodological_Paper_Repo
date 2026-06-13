"""Pre-cond 3 — Historical polygon coverage.

Locked check (§7 of design doc):
  Each Stage-A polygon contains >= 5 admin-2 units to support
  within-polygon variance. Pure coverage count; no outcome inspection.

Pass: all 4 polygons clear.
Fail: aggregate polygon-internal admin-2s to a single binary indicator
      without within-polygon partial pooling; document downgrade.

Phase 0 status: requires both (1) digitized Stage-A polygon GeoJSON +
(2) GADM admin-2 polygons present. Emits STUB if either missing.
"""
import pathlib, sys, json, time, io
import warnings; warnings.filterwarnings("ignore")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
except Exception:
    pass

ROOT = pathlib.Path(r"D:/IDP")
HIST_DIR = ROOT / "historical_polygons"
GADM_DIR = ROOT / "data" / "gadm"
NOTES = ROOT / "notes"
REPORT = NOTES / "precond_3_report.md"

POLYGON_PATHS = {
    # Locked at redline Entry 002 (2026-05-17). Per PI confirmation, polygons
    # mark founding protracted-displacement geographies, not new-onset
    # displacement events.
    "colombia": (HIST_DIR / "colombia_la_violencia_1948_1958", GADM_DIR / "gadm41_colombia.gpkg"),
    "sudan":    (HIST_DIR / "sudan_fur_dar_pre1994",          GADM_DIR / "gadm41_sudan.gpkg"),
    "drc":      (HIST_DIR / "drc_kasai_1959_1965",            GADM_DIR / "gadm41_drc.gpkg"),
    "yemen":    (HIST_DIR / "yemen_six_wars_2004_2010",       GADM_DIR / "gadm41_yemen.gpkg"),
}
LOCKED_MIN_ADMIN2_PER_POLYGON = 5


def stub_result(country, reason):
    return {"country": country, "verdict": "PHASE0_STUB", "reason": reason, "n_admin2_in_polygon": None}


def check_country(country):
    poly_dir, gadm_path = POLYGON_PATHS[country]
    poly_files = list(poly_dir.glob("*.geojson")) + list(poly_dir.glob("*.shp")) + list(poly_dir.glob("*.gpkg"))
    if not poly_files:
        return stub_result(country, f"No digitized polygon in {poly_dir.relative_to(ROOT)} (only provenance.md present)")
    if not gadm_path.exists():
        return stub_result(country, f"GADM file missing: {gadm_path.relative_to(ROOT)}")
    try:
        import geopandas as gpd, pyogrio
    except ImportError:
        return stub_result(country, "geopandas/pyogrio not available")
    # Prefer the dissolved stage_a_polygon.geojson if present (built by build_admin_unit_polygons.py)
    canonical = poly_dir / "stage_a_polygon.geojson"
    poly_path = canonical if canonical.exists() else poly_files[0]
    poly = gpd.read_file(poly_path)
    layers = [row[0] for row in pyogrio.list_layers(str(gadm_path))]
    adm2_layer = next((l for l in layers if "_2" in l or "ADM_2" in l.upper()), layers[-1])
    adm2 = gpd.read_file(gadm_path, layer=adm2_layer)
    if poly.crs is None: poly.set_crs("EPSG:4326", inplace=True)
    if str(adm2.crs).lower() != "epsg:4326": adm2 = adm2.to_crs("EPSG:4326")
    if str(poly.crs).lower() != "epsg:4326": poly = poly.to_crs("EPSG:4326")
    poly_geom = poly.unary_union
    inside = adm2[adm2.intersects(poly_geom)]
    n = len(inside)
    verdict = "PASS" if n >= LOCKED_MIN_ADMIN2_PER_POLYGON else "FAIL"
    return {
        "country": country,
        "polygon_file": str(poly_files[0].relative_to(ROOT)),
        "n_admin2_in_polygon": int(n),
        "threshold": LOCKED_MIN_ADMIN2_PER_POLYGON,
        "verdict": verdict,
    }


def main():
    print(f"=== Pre-cond 3: historical polygon coverage ===")
    print(f"  Locked threshold: >= {LOCKED_MIN_ADMIN2_PER_POLYGON} admin-2 units per Stage-A polygon")
    results = [check_country(c) for c in POLYGON_PATHS.keys()]
    for r in results:
        print(f"  [{r['country']}] {r['verdict']}  n_in_polygon={r.get('n_admin2_in_polygon')}")

    overall = ("PASS" if all(r["verdict"] == "PASS" for r in results)
               else "PHASE0_STUB" if all(r["verdict"] == "PHASE0_STUB" for r in results)
               else "FAIL_OR_MIXED")

    md = []
    md.append("# Pre-cond 3 Report — Historical Polygon Coverage\n")
    md.append(f"**Run at:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    md.append(f"**Locked check:** Each Stage-A polygon contains >= {LOCKED_MIN_ADMIN2_PER_POLYGON} admin-2 units.\n")
    md.append(f"**Overall verdict:** **{overall}**\n")
    md.append("\n## Per-country results\n")
    md.append("| Country | Polygon file | N admin-2 inside | Verdict |")
    md.append("|---|---|---|---|")
    for r in results:
        md.append(f"| {r['country']} | {r.get('polygon_file','—')} | {r.get('n_admin2_in_polygon','—')} | {r['verdict']} |")
    md.append("\n## Failure handling (locked walk-back §7)\n")
    md.append("- FAIL: aggregate polygon-internal admin-2s to a single binary indicator without within-polygon partial pooling. Document downgrade.\n")
    md.append("- PHASE0_STUB: polygon digitization not yet complete. Phase 0+ pacing: 1922 CDO + pre-1994 Fur dar are 2-3 day each per locked budget.\n")
    REPORT.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\n=== Report: {REPORT} ===")
    (NOTES / "precond_3_results.json").write_text(json.dumps({"overall": overall, "results": results}, indent=2))


if __name__ == "__main__":
    main()
