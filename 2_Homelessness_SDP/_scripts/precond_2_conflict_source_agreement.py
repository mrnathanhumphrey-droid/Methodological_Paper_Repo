"""Pre-cond 2 — Conflict-source agreement (GDELT vs UCDP-GED).

**REDLINE Entry 001 (notes/pre_reg_redline.md):** ACLED replaced by GDELT
because non-institutional PI cannot access ACLED. Threshold (Spearman
>= 0.6) and aggregation (admin-2 x year) UNCHANGED from v1.

Locked check (§7 of design doc, as redlined v1 -> v2):
  GDELT and UCDP-GED event counts per admin-2 x year correlate >= 0.6
  across the panel (Spearman). Cross-source validity check.

Pass: all countries clear.
Fail: reframe shock indicator as source-specific; rerun §5 Axis 1 as
      primary instead of robustness.

Phase 0 status: runs against fetched UCDP + GDELT data spatial-joined to
GADM admin-2 polygons. In Phase 0 smoke test, GDELT covers Dec 2024 only;
Phase 1 expands to full 2014-2024.
"""
import pathlib, sys, json, time, io
import warnings; warnings.filterwarnings("ignore")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
except Exception:
    pass
import numpy as np
import pandas as pd

ROOT = pathlib.Path(r"D:/IDP")
UCDP_DIR = ROOT / "data" / "ucdp"
GDELT_DIR = ROOT / "data" / "gdelt"   # was ACLED_DIR; redlined per Entry 001
GADM_DIR = ROOT / "data" / "gadm"
NOTES = ROOT / "notes"
REPORT = NOTES / "precond_2_report.md"

COUNTRIES = ["colombia", "sudan", "drc", "yemen"]
LOCKED_CORR_THRESHOLD = 0.6


def stub_result(country, reason):
    return {
        "country": country,
        "verdict": "PHASE0_STUB",
        "reason": reason,
        "spearman_correlation": None,
    }


def check_country(country):
    ucdp_path = UCDP_DIR / f"ucdp-ged-{country}.csv"
    # Phase 1 full panel; fall back to Phase 0 smoke if not present
    gdelt_phase1 = GDELT_DIR / f"gdelt-{country}-2014_2024.csv"
    gdelt_phase0 = GDELT_DIR / f"gdelt-{country}.csv"
    gdelt_path = gdelt_phase1 if gdelt_phase1.exists() else gdelt_phase0
    gadm_path = GADM_DIR / f"gadm41_{country}.gpkg"
    missing = []
    for p, name in [(ucdp_path, "UCDP"), (gdelt_path, "GDELT"), (gadm_path, "GADM")]:
        if not p.exists(): missing.append(name)
    if missing:
        return stub_result(country, f"Missing data: {missing}")

    try:
        import geopandas as gpd
        import pyogrio
    except ImportError:
        return stub_result(country, "geopandas/pyogrio not available")

    # Load admin-2 polygons
    try:
        layers = [row[0] for row in pyogrio.list_layers(str(gadm_path))]
        adm2_layer = next((l for l in layers if "_2" in l or "ADM_2" in l.upper()), layers[-1])
        adm2 = gpd.read_file(gadm_path, layer=adm2_layer)
    except Exception as e:
        return stub_result(country, f"GADM read failed: {e}")

    if "GID_2" in adm2.columns:
        adm2_id_col = "GID_2"
    elif "ID_2" in adm2.columns:
        adm2_id_col = "ID_2"
    else:
        adm2_id_col = adm2.columns[0]

    # Load + filter event tables to year + admin-2 join
    try:
        ucdp = pd.read_csv(ucdp_path, low_memory=False)
        gdelt = pd.read_csv(gdelt_path, low_memory=False, sep="\t")
    except Exception as e:
        return stub_result(country, f"event table read failed: {e}")

    def to_year(df, col_candidates):
        for c in col_candidates:
            if c in df.columns:
                # Try numeric first; pd.to_datetime treats int 2014 as nanoseconds
                # since epoch -> 1970-01-01, which silently kills the year filter.
                numeric = pd.to_numeric(df[c], errors="coerce")
                if numeric.notna().sum() > 0 and numeric.min() >= 1900 and numeric.max() <= 2100:
                    return numeric.astype("Int64")
                # Date-string column (e.g. UCDP date_start="2014-03-15"): parse as datetime
                try:
                    dt = pd.to_datetime(df[c], errors="coerce")
                    if dt.notna().sum() > 0:
                        return dt.dt.year
                except Exception:
                    pass
                # GDELT sqldate is YYYYMMDD integer; take first 4 chars
                try:
                    s = df[c].astype(str).str[:4]
                    return pd.to_numeric(s, errors="coerce")
                except Exception:
                    pass
        return None

    ucdp_year = to_year(ucdp, ["year","date_start","Year"])
    gdelt_year = to_year(gdelt, ["year","Year","sqldate"])  # GDELT 1.0 has 'year' + 'sqldate'
    if gdelt_year is None and "sqldate" in gdelt.columns:
        gdelt_year = pd.to_numeric(gdelt["sqldate"].astype(str).str[:4], errors="coerce")
    if ucdp_year is None or gdelt_year is None:
        return stub_result(country, "year column not identified in events")
    ucdp = ucdp.assign(_year=ucdp_year)
    gdelt = gdelt.assign(_year=gdelt_year)

    # Filter to panel years 2014-2024
    ucdp = ucdp[(ucdp["_year"] >= 2014) & (ucdp["_year"] <= 2024)]
    gdelt = gdelt[(gdelt["_year"] >= 2014) & (gdelt["_year"] <= 2024)]

    # Spatial join each event table to admin-2
    def make_gdf(df, lat_cols, lon_cols):
        for lat, lon in zip(lat_cols, lon_cols):
            if lat in df.columns and lon in df.columns:
                return gpd.GeoDataFrame(df.copy(),
                    geometry=gpd.points_from_xy(df[lon], df[lat]), crs="EPSG:4326")
        return None
    u_g = make_gdf(ucdp, ["latitude","lat"], ["longitude","lon"])
    g_g = make_gdf(gdelt, ["actiongeo_lat","ActionGeo_Lat","lat"],
                          ["actiongeo_long","ActionGeo_Long","lon"])
    if u_g is None or g_g is None:
        return stub_result(country, "lat/lon columns not identified")
    if adm2.crs is None or str(adm2.crs).lower() != "epsg:4326":
        adm2 = adm2.to_crs("EPSG:4326")
    u_join = gpd.sjoin(u_g, adm2[[adm2_id_col,"geometry"]], how="left", predicate="within")
    g_join = gpd.sjoin(g_g, adm2[[adm2_id_col,"geometry"]], how="left", predicate="within")

    # Per-admin2 × year counts
    u_count = (u_join.dropna(subset=[adm2_id_col])
                     .groupby([adm2_id_col,"_year"]).size().rename("ucdp_events"))
    g_count = (g_join.dropna(subset=[adm2_id_col])
                     .groupby([adm2_id_col,"_year"]).size().rename("gdelt_events"))
    panel = pd.concat([u_count, g_count], axis=1).fillna(0).reset_index()
    if len(panel) < 30:
        return stub_result(country, f"only {len(panel)} cells — too few for correlation")

    rho = panel["ucdp_events"].corr(panel["gdelt_events"], method="spearman")
    verdict = "PASS" if rho >= LOCKED_CORR_THRESHOLD else "FAIL"
    return {
        "country": country,
        "verdict": verdict,
        "spearman_correlation": float(rho),
        "n_admin2_year_cells": int(len(panel)),
        "threshold": LOCKED_CORR_THRESHOLD,
    }


def main():
    print(f"=== Pre-cond 2: GDELT vs UCDP source agreement (per redline Entry 001) ===")
    print(f"  Locked threshold: Spearman corr >= {LOCKED_CORR_THRESHOLD}")
    results = [check_country(c) for c in COUNTRIES]
    for r in results:
        print(f"  [{r['country']}] {r['verdict']}  corr={r.get('spearman_correlation')}")

    overall = ("PASS" if all(r["verdict"] == "PASS" for r in results)
               else "PHASE0_STUB" if all(r["verdict"] == "PHASE0_STUB" for r in results)
               else "FAIL_OR_MIXED")

    md = []
    md.append("# Pre-cond 2 Report — Conflict-Source Agreement (GDELT vs UCDP-GED)\n")
    md.append(f"**Redline:** Entry 001 — ACLED replaced by GDELT (notes/pre_reg_redline.md). Threshold unchanged.\n")
    md.append(f"**Run at:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    md.append(f"**Locked check:** Spearman corr >= {LOCKED_CORR_THRESHOLD} between GDELT and UCDP-GED event counts per admin-2 x year.\n")
    md.append(f"**Overall verdict:** **{overall}**\n")
    md.append("\n## Per-country results\n")
    md.append("| Country | Spearman corr | N cells | Verdict |")
    md.append("|---|---|---|---|")
    for r in results:
        corr = r.get('spearman_correlation')
        corr_s = f"{corr:.3f}" if corr is not None else "—"
        md.append(f"| {r['country']} | {corr_s} | {r.get('n_admin2_year_cells','—')} | {r['verdict']} |")
    md.append("\n## Failure handling (locked walk-back §7)\n")
    md.append("- FAIL: reframe shock indicator as source-specific; promote §5 Axis 1 to primary.\n")
    md.append("- PHASE0_STUB: Phase 2 re-runs after data fetched.\n")
    REPORT.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\n=== Report: {REPORT} ===")
    (NOTES / "precond_2_results.json").write_text(json.dumps({"overall": overall, "results": results}, indent=2))


if __name__ == "__main__":
    main()
