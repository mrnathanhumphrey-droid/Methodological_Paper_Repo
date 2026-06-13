# IDP Substrate — Session State (pre-compact)

**Date:** 2026-05-25
**Posture:** broad-data → thread-following phase; 5 cluster panels built, 15 patterns logged, no pre-reg drafted yet.

## Where we are in the arc

The IDP work pivoted on 2026-05-21 from a paused narrow framing (substrate 9 v1, conflict→displacement causal with UCDP-GED agreement gate that failed at precond_2) to a broad exploratory data pull with thread-following + late pre-reg discipline. The pivot was driven by: "im tired of being stuck by shit data. we're going broad and preregging and following threads."

## Methodology framing

- IDP work is its own thing now, not formally substrate 9 of Paper 6 corpus
- The residue-class framework is *applied* throughout, mentioned in methodology section, but the IDP studies stand alone
- Same posture as Women's Health corpus

## Data backbone on disk (`D:/IDP/data/`)

~50+ GB total across 30+ sources. Inventory by source family:

**Displacement:**
- IDMC GIDD master (annual country-year conflict + disaster) — `idmc_gidd/IDMC_GIDD_*.xlsx`
- IDMC IDU rolling (recent events ~6 mo window, 24+ countries on disk) — `idmc_gidd/idu/*.csv`
- UNHCR Refugee Data Finder — `unhcr_rdf/population_1990_2024.csv`
- IOM DTM via HAPI (8 countries paginated: original 4 + Sahel 4) — `dtm/{iso3}/page_*.json`
- HAPI baseline_population, food_security, refugees — `hdx_hapi/*/page_0.json`

**Conflict:**
- UCDP-GED v25.1 (1989+, global event-level, 385K events) — `ucdp/GEDEvent_v25_1.csv`
- GDELT 1.0 daily 2014-2024 (4012 zips raw + per-country filtered for 4+4 Sahel countries) — `gdelt/_raw/*.zip` + `gdelt/gdelt-*-2014_2024.csv`
- ICEWS historic 1995-2023 (49 files, 1.7 GB) — `icews/files/`
- POLECAT post-2023 (7 files, 1.2 GB) — `polecat/files/`
- COW MID dyadic v4.03 — `cow/`

**Governance:**
- V-Dem v15 full (1789-2024, 202 countries, 4618 vars; CSV converted from .RData) — `vdem/vdem_vdem.csv`
- Polity 5 (1800-2018, 194 countries) — `polity5/p5v2018.xls`

**Disaster:**
- EM-DAT (1900+, full XLSX) — `emdat/public_emdat_incl_hist_2026-05-18.xlsx`
- GIDD Disasters (event-level with hazard type) — `idmc_gidd/IDMC_GIDD_Disasters_*.xlsx`
- NASA EONET — `eonet/`

**Food security:**
- HAPI food_security (paginated; 10K rows cap hit, need to expand)
- IPC FEWS NET shapefiles + geojson (46 countries) — `ipc_fewsnet/`

**Climate:**
- ERA5 monthly 1998-2024 global (5 variables, 2.4 GB extracted) — `era5/data_stream-moda_stepType-*.nc`
- CHIRPS v2 global monthly NetCDF (128 MB) — `chirps/chirps-v2.0.monthly.nc`
- SPEI 1/3/6/12/24-month NetCDFs (67 MB) — `spei/SPEI_*.nc`

**Economic:**
- World Bank WDI bulk (1500 indicators, 217 countries, 1960+, 196 MB CSV) — `wb_wdi/extracted/WDICSV.csv`
- UNDP HDR statistical annex — `undp_hdr/`

**Health:**
- WHO GHO indicator list + 25 priority indicators (mortality, immunization, nutrition) — `who_gho/indicators/*.json`

**Geographic baseline:**
- GADM admin polygons (from v1) — `gadm/`
- Natural Earth admin 0+1 via GitHub mirror — `natural_earth/`

## Cluster panels built (`D:/IDP/analysis/`)

5 clusters, 19 countries, country-year stratified panels:

| Cluster | Countries | Panel file |
|---|---|---|
| Sahel | BFA, MLI, BEN, NER | `sahel_stratified_panel_2026_05_21.parquet` |
| Horn of Africa | SOM, SDN, SSD, ETH, ERI | `horn_of_africa_stratified_panel_2026_05_21.parquet` |
| Middle East | SYR, YEM, IRQ, LBN | `middle_east_stratified_panel_2026_05_21.parquet` (v2 after UCDP name fix) |
| Latin America | COL, HTI, SLV | `latin_america_stratified_panel_2026_05_21.parquet` |
| Central Africa | COD, CAF, CMR | `central_africa_stratified_panel_2026_05_21.parquet` |

Plus cell-availability matrix (long + source-count): `cell_availability_*_2026_05_21.parquet`.

## Pattern catalog (`D:/IDP/patterns/`)

15 patterns logged. INDEX tiered by interest. The four Tier A patterns are the methodology-paper seeds:

- **PATTERN_001** (candidate-hypothesis, revised): Displacement-channel orthogonality — conflict / flood / drought (3-channel after Horn data added drought)
- **PATTERN_010** (candidate-hypothesis): Strife-dominant pattern recurs across 4 clusters / 4 continents (MLI, SSD, HTI, CAF)
- **PATTERN_011** (candidate-hypothesis, sharpened): V-Dem libdem range-conditioning, not cluster-conditioning. CAF inside Central Africa collapsed while COD+CMR stayed flat — the conditioning is range-based, not geographic
- **PATTERN_013** (candidate-hypothesis): Bukelization — libdem collapse without coup, civilian-authoritarian path (SLV mirrors Sahel outcome via different mechanism)

Tier B (single-cluster mechanism): 002 (Sahel libdem-coup, now downstream of 011), 009 (earthquake as 4th channel)
Tier C (anomalies): 003 (BFA scale), 004 (NER flood >war), 012 (Tigray largest single-period war), 015 (DRC ~30M cumulative IDP corpus)
Tier D (contrasts): 005 (MLI strife outlier — generalized via 010), 006 (BEN periphery spillover)
Tier E (data-quality): 007 (Sahel drought invisible — Sahel-specific via 008), 008 (drought captured globally), 014 (UCDP+ISO3 name bugs — firmed via fix)

Pattern catalog conventions in `patterns/README.md`. Status taxonomy: noted / digging / null / candidate-hypothesis / firmed / walked-back / discarded.

## Scripts (`D:/IDP/_scripts/`)

- `build_regional_panel.py` — parameterized cluster panel builder (used for all 5 clusters)
- `build_sahel_stratified.py` — original Sahel-specific (kept for reference)
- `cell_availability_sweep.py` — produces the (country, year, source) matrix
- `expand_data_pulls.py` — WB WDI extract + V-Dem RData→CSV + WHO GHO + IDMC IDU expansion
- `patch_sahel.py` — HAPI DTM + IDMC IDU + GDELT refilter for BFA/MLI/BEN/NER
- `fetch_era5_monthly.py` — CDS API ERA5 monthly request
- `fetch_icews_polecat_files.py` — Dataverse bulk fetcher
- Plus v1 scripts: `fetch_gdelt_phase1.py`, `fetch_ucdp.py`, `fetch_dtm_hdx.py`, etc.

## Next steps (queued, do AFTER compact)

1. **Stratify South Asia** (AFG, PAK, MMR) — adds 3 more cases for PATTERN_011's range-conditioning test (AFG = post-Taliban collapse acute; MMR = post-2021-coup mid-range collapse; PAK = stable mid-range comparator)
2. **Stratify Eastern Europe** — UKR alone, the pure interstate-war case; tests whether the corpus framework even applies to a different conflict TYPE
3. Then likely: deep-dive on one of the Tier A patterns, or write a draft pre-reg for the 3-channel hypothesis (PATTERN_001 + 008)

## Blockers / queued

- ERA5 done; full 2.4 GB on disk
- ICEWS+POLECAT done; full historic + successor on disk
- ReliefWeb appname approval still pending (~2 days from 2026-05-21 submission)
- HAPI pagination still capped at 10K per endpoint — fix queued
- UNHCR RDF CSV had UTF-8 encoding issue in the sweep — fix queued
- UNDP HDR XLSX parsing didn't find ISO3 — fix queued (low priority)
- FEWS NET broad fetch landed 46 country files; not yet joined into panels

## Calibration / posture

- Broad-data → late-pre-reg discipline (NOT pre-reg-first). Threads have to emerge before we commit to a hypothesis.
- Don't oversell findings. The framework's contribution is honesty: walk back when the data doesn't support a claim. Bird-song substrate (substrate 7) walk-back is the precedent.
- The work intent: "be in a position to try" to help displaced people. Mechanism is methodology paper → field practitioners (IDMC, UNHCR Stats & Demographics, ACAPS) read it → if patterns hold, they cite/extend.
- No professional-embarrassment stance. If we find nothing, that's also a result.
