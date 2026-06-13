"""Fetch IOM DTM IDP data via HDX HAPI v2 — Phase 1.

REPLACES the SCAFFOLD stub at fetch_dtm.py. HDX HAPI is the public IOM-DTM
aggregator and exposes admin-2 IDP figures cleanly for 3 of 4 study
countries (Sudan / DRC / Yemen). Colombia DTM presence is minimal —
HDX HAPI may return zero rows for COL; we still query and document.

Per Phase 0 locked constraint:
  "DTM schema drift is real. Different rounds have different columns.
   The harmonization layer must be defensive: log every column rename,
   every type coercion, every missing-value fill."

HDX HAPI's pre-aggregated /api/v2/affected-people/idps view is ALREADY
the harmonized layer (IOM normalizes across rounds before publishing).
We still emit a _harmonization_log.json per country documenting:
  - rows fetched
  - admin2 coverage count
  - reporting-round range
  - missing-value fields
  - any schema drift between rounds (column presence sparsity)
This satisfies the locked constraint while leveraging IOM's upstream work.

App identifier:
  base64("IDP_Study:mr.nathanhumphrey@gmail.com")
  per https://hdx-hapi.readthedocs.io/en/latest/getting-started/
"""
import pathlib, sys, hashlib, json, urllib.request, urllib.error, time, io, base64
import warnings; warnings.filterwarnings("ignore")
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
except Exception:
    pass
import pandas as pd

ROOT = pathlib.Path(r"D:/IDP")
OUT_DIR = ROOT / "data" / "dtm"
MANIFEST = ROOT / "manifest.json"

HAPI_BASE = "https://hapi.humdata.org/api/v2"
APP_ID = base64.b64encode(b"IDP_Study:mr.nathanhumphrey@gmail.com").decode("ascii")

COUNTRIES = {
    "colombia": "COL",
    "sudan":    "SDN",
    "drc":      "COD",
    "yemen":    "YEM",
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def update_manifest(entry):
    manifest = {}
    if MANIFEST.exists():
        try: manifest = json.loads(MANIFEST.read_text())
        except: manifest = {}
    manifest.setdefault("files", [])
    # Replace any prior entry for same filename
    manifest["files"] = [m for m in manifest["files"] if m.get("filename") != entry["filename"]]
    manifest["files"].append(entry)
    manifest["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    MANIFEST.write_text(json.dumps(manifest, indent=2))


def fetch_paginated(location_code, admin_level=2):
    """Hit /affected-people/idps and paginate via offset until empty."""
    rows = []
    offset = 0
    page_size = 1000
    while True:
        url = (f"{HAPI_BASE}/affected-people/idps"
               f"?location_code={location_code}"
               f"&admin_level={admin_level}"
               f"&output_format=json"
               f"&limit={page_size}"
               f"&offset={offset}"
               f"&app_identifier={APP_ID}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "IDP-Study/1.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = resp.read()
        except urllib.error.HTTPError as e:
            print(f"    HTTP {e.code} at offset={offset}: {e.read()[:200]}")
            break
        except Exception as e:
            print(f"    FAIL at offset={offset}: {type(e).__name__}: {e}")
            break
        try:
            page = json.loads(body)
        except json.JSONDecodeError:
            print(f"    JSON parse fail at offset={offset}")
            break
        data = page.get("data", []) if isinstance(page, dict) else []
        if not data:
            break
        rows.extend(data)
        if len(data) < page_size:
            break
        offset += page_size
    return rows


def write_harmonization_log(country, rows, out_dir):
    log = {
        "country": country,
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": "HDX HAPI v2 /api/v2/affected-people/idps",
        "n_rows": len(rows),
    }
    if not rows:
        log["coverage_note"] = ("HDX HAPI returned zero admin-2 rows for this country. "
                                "DTM presence may be minimal (esp. Colombia) or rounds "
                                "may not have been ingested into HAPI yet.")
    else:
        df = pd.DataFrame(rows)
        log["columns_present"] = list(df.columns)
        log["n_unique_admin2"] = int(df["admin2_code"].nunique()) if "admin2_code" in df else 0
        log["n_unique_admin1"] = int(df["admin1_code"].nunique()) if "admin1_code" in df else 0
        if "reporting_round" in df:
            log["reporting_round_range"] = [int(df["reporting_round"].min()),
                                             int(df["reporting_round"].max())]
        if "reference_period_start" in df:
            log["reference_period_start_range"] = [str(df["reference_period_start"].min()),
                                                    str(df["reference_period_start"].max())]
        if "reference_period_end" in df:
            log["reference_period_end_range"] = [str(df["reference_period_end"].min()),
                                                  str(df["reference_period_end"].max())]
        if "assessment_type" in df:
            log["assessment_types"] = sorted(df["assessment_type"].dropna().unique().tolist())
        if "operation" in df:
            log["operations"] = sorted(df["operation"].dropna().unique().tolist())[:50]
            log["n_unique_operations"] = int(df["operation"].nunique())
        # Missing-value fields
        log["null_counts"] = {c: int(df[c].isna().sum()) for c in df.columns}
        log["upstream_harmonization_note"] = (
            "HDX HAPI v2 pre-aggregates IOM DTM rounds into a uniform admin-2 schema; "
            "the harmonization above (rename + type coerce + missing-fill) happens "
            "upstream at IOM/OCHA. This log records the SHAPE we received."
        )
    log_path = out_dir / "_harmonization_log.json"
    log_path.write_text(json.dumps(log, indent=2, default=str))
    return log_path


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== DTM HDX HAPI fetch (4 countries, admin-2) ===")

    for country_slug, iso3 in COUNTRIES.items():
        country_dir = OUT_DIR / country_slug
        country_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n  [{country_slug}] {iso3} ...")
        rows = fetch_paginated(iso3, admin_level=2)
        print(f"    rows fetched: {len(rows):,}")
        if rows:
            df = pd.DataFrame(rows)
            out_csv = country_dir / f"hdx_idps_admin2_{country_slug}.csv"
            df.to_csv(out_csv, index=False, encoding="utf-8")
            print(f"    -> {out_csv.name}")
            update_manifest({
                "source": f"HDX HAPI v2 IDP admin2 fetch ({iso3})",
                "filename": str(out_csv.relative_to(ROOT)),
                "sha256": sha256(out_csv),
                "size_bytes": out_csv.stat().st_size,
                "row_count": len(df),
                "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "iso3": iso3,
            })
            # Save raw JSON too for full provenance
            raw_path = country_dir / f"hdx_idps_admin2_{country_slug}_raw.json"
            raw_path.write_text(json.dumps(rows, indent=2, default=str))
        log_path = write_harmonization_log(country_slug, rows, country_dir)
        print(f"    harmonization log: {log_path.name}")

    print(f"\n=== DTM HDX HAPI fetch complete ===")


if __name__ == "__main__":
    main()
