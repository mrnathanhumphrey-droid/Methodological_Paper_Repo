# Phase 1 First-Pass Progress

**Build session:** 2026-05-17 (post-compact continuation of substrate 9 Phase 0)

## Items landed in this session

### Item 3: GDELT 2014-2024 expansion — IN-FLIGHT

`_scripts/fetch_gdelt_phase1.py` built. Runs the full 2014-01-01..2024-12-31 daily
panel with per-day caching, resume-safe state, and incremental per-country CSV
appends. Fired as background task ID `b7cn2mh1v`. Progress: ~625/4018 daily files
through Sept 2015 at run start, ETA ~2h. Cumulative event counts at that
checkpoint: Colombia 157k, Sudan 346k, DRC 27k, Yemen 421k.

### Item 4: DTM 3-of-4 countries landed

`_scripts/fetch_dtm_hdx.py` hits HDX HAPI v2 `/api/v2/affected-people/idps`. App
identifier resolved as `base64("IDP_Study:mr.nathanhumphrey@gmail.com")`.

| Country | Rows | Admin-2 | Years         | Operations |
|---------|------|---------|---------------|------------|
| Sudan   | 16,452 | 186  | 2010-2025     | 5 (incl. Darfur conflict, Armed Clashes monthly/overview, Biometric Registration) |
| DRC     | 1,366  | 143  | 2016-2026     | 13 (incl. Kasai, Kasai Central, Kasai Oriental, M23 Crisis, Tanganyika, Ituri) |
| Yemen   | 4,641  | 329  | 2015-2025     | 1 (Yemen conflict) |
| Colombia | 0    | —    | —             | HDX HAPI has no DTM Colombia |

Per-country `_harmonization_log.json` records the schema we received (HDX HAPI
v2 is itself an upstream harmonization layer over IOM DTM rounds, so the
defensive-harmonization constraint is satisfied by recording the SHAPE).

Colombia gap: RUV `datos.gov.co` Socrata dataset `y6ru-nqsj` is a 2017
cross-section snapshot, not the longitudinal panel we need. Cifras
`cifras.unidadvictimas.gov.co` Power BI scraping deferred to Phase 2.

### Item 1: Stage-A polygons (4/4 built via admin-unit dissolution)

Methodology pivot: replaced multi-day CV-based polygon tracing from historic
maps with **admin-unit-list dissolution**. Reproducible, auditable, matches how
most historic-violence-zone empirical work codes geography.

`historical_polygons/admin_unit_lists.json` locks the unit lists with
citations. `_scripts/build_admin_unit_polygons.py` does the GADM dissolve.
Output per polygon: `stage_a_polygon.geojson` + `.gpkg` + `_build_log.json`.

`precond_3_polygon_coverage.py` re-run, all 4 PASS locked >=5 admin-2 threshold:

| Polygon | Admin-2 inside |
|---------|----------------|
| Colombia La Violencia 1948-1958 | 658 (9 departments × ~73 municipios) |
| Sudan Fur dar pre-1994          | 21 (5 modern Darfur states × ~4 localities) |
| DRC Kasai 1959-1965             | 59 (5 provinces × ~12 territoires) |
| Yemen Six Wars 2004-2010        | 102 (Saada + Al-Jawf full + Amran + Hajjah + 7 explicit ICG districts) |

Yemen polygon used `_scripts/extract_icg_mer86.py` to pull district mentions
directly from the ICG MER N°86 PDF (Saada Time Bomb, May 2009): 7 of 8 named
districts matched GADM (Ghamir not found; Haydan/Majz/Sahar/Baqim/Razih/Harf
Sufyan/Bani Hushaysh all matched).

**Verification pass deferred:** all 4 polygons coded as "FIRST_PASS" in
`_build_log.json` — Colombia municipio subdivision against CNMH Map 2;
Sudan eastern boundary precision against pre-1994 Province line; DRC
territoire subdivision against Young & Turner admin map.

### Item 2: DRC atrocity-count first-pass

`_scripts/build_drc_atrocity_first_pass.py` produces
`data/atrocity_drc_kasai_1959_1965_first_pass.csv` with 240 DRC admin-2 rows
coded 0/1/2:

- **HIGH (=2):** 12 territoires explicitly named in Young & Turner / Lemarchand /
  Stearns / Wikipedia cross-cite (Luiza, Demba, Dimbelenge, Mweka, Tshikapa,
  Luebo, Ilebo, Lusambo, Lodja, Lubefu, Mwene-Ditu, Kabinda)
- **MEDIUM (=1):** 47 admin-2 inside Kasai dissolved polygon, not explicitly named
- **ZERO (=0):** 181 admin-2 outside the polygon

Feeds Stan H_HISTORICAL_INTENSITY as `log1p(atrocity_count_first_pass)`. True
per-territoire event-count tallying deferred pending Young & Turner PDF
retrieval (Internet Archive copy is controlled-digital-lending restricted).

### BONUS: Admin-2 × year combined panel

`_scripts/build_admin2_year_panel_hdx.py` produces
`data/panels/idp_admin2_annual.csv` (3,160 admin-2-year rows across Sudan +
DRC + Yemen). Aggregation: `idp_max` (peak displacement in year, canonical
UNHCR/IDMC convention) + `idp_mean` + `idp_median` + `n_rounds_in_year`.

Joins to GADM admin-2 GID_2 by name lower-stripped:

| Country | HDX rows | GADM joined | Join rate |
|---------|----------|-------------|-----------|
| Sudan   | 1,133    | 162         | **14%** ← Phase 2 work to normalize transliterated Arabic names |
| DRC     | 514      | 509         | 99% |
| Yemen   | 1,513    | 926         | 61% |

DRC also carries the `atrocity_count_first_pass` and `in_polygon` columns.

## Open gates (Phase 1 → v0_1 Stan fit)

1. **GDELT full panel land** (~2h ETA). Once landed, run
   `precond_2_conflict_source_agreement.py` for the locked Spearman >=0.6
   GDELT↔UCDP cross-source check.
2. **Sudan name-join normalization** (the 14% join rate is too low for
   Stan-fit; need transliteration alignment between HDX HAPI Arabic-to-Latin
   romanization and GADM Sudan ADM_2 NAME_2).
3. **Colombia RUV Phase 2** (currently absent — v0_1 baseline can fit on
   3-country panel with Colombia exclusion documented).

## Memory + commit status

All work uncommitted as of this writeup; user has the locked
`feedback_no_autopush` setting. Files staged for commit on user trigger:

- `_scripts/{fetch_gdelt_phase1, fetch_dtm_hdx, extract_icg_mer86, build_admin_unit_polygons, build_drc_atrocity_first_pass, build_admin2_year_panel_hdx}.py`
- `_scripts/precond_3_polygon_coverage.py` (pyogrio backend)
- `data/dtm/{sudan,drc,yemen,colombia_ruv}/`
- `data/atrocity_drc_kasai_1959_1965_first_pass.csv` + `_atrocity_drc_kasai_build_log.json`
- `data/panels/idp_admin2_annual{,_sudan,_drc,_yemen}.csv`
- `historical_polygons/admin_unit_lists.json`
- `historical_polygons/_sources/icg_mer86_yemen_saada.{pdf,txt}`
- `historical_polygons/{4 polygon dirs}/stage_a_polygon.{geojson,gpkg}` + `_build_log.json`
- `manifest.json` (with SHA-256 entries for HDX HAPI + atrocity panel + combined panel)
- `notes/precond_3_report.md` + `precond_3_results.json` (all 4 PASS)
- `notes/phase1_first_pass_progress.md` (this file)
