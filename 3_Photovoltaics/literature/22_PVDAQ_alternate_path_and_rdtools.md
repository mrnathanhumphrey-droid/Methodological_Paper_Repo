# 22 — PVDAQ Alternate-Path Pull + rdtools Install

**Status:** PARTIAL (alternate path WORKS; cell-architecture metadata absent at index level)
**Date:** 2026-05-27
**Closes blocker:** "DuraMAT Fleet Insights CSV NREL SSL blocked" (NEXT.md §5 #1) — alternate via OEDI PVDAQ public S3 IS LIVE.
**Surfaces new gap:** PVDAQ index CSV has no cell-architecture field; TOPCon cohort identification requires a deeper step than systems-index lookup.

---

## 1. OEDI PVDAQ — live alternate path

**Source:** Open Energy Data Initiative (OEDI) submission 4568
- URL: `https://data.openei.org/submissions/4568`
- DOI: `10.25984/1846021`
- License: **CC-BY 4.0**
- Lake size: 512.11 GB total (44.36 GB CSV + 17.21 GB parquet + 450.54 GB 2023 DOE Solar Data Prize + JSON metadata)
- Direct S3: `s3://oedi-data-lake/pvdaq/`
- Public viewer: `https://data.openei.org/s3_viewer`
- Documentation: `https://github.com/openEDI/documentation/blob/main/pvdaq.md`

**No SSL/auth blockers.** Direct HTTPS to S3 succeeded for systems-index CSV.

### Acquired this session
- **`PVDAQ_systems_20250729.csv`** (383 KB, 1862 rows × 26 columns)
  - Path: `D:/Renewables/Solar/data/raw/datasets/PVDAQ_systems_20250729.csv`
  - Gitignored per `D:/Renewables/.gitignore` Solar rules

### Systems-index schema (26 columns)

| Group | Columns |
|---|---|
| Identifiers | `system_id`, `system_public_name`, `site_location`, `timezone_or_utc_offset` |
| Geometry | `latitude`, `longitude`, `elevation_m`, `azimuth`, `tilt` |
| Sizing | `dc_capacity_kW` |
| **PVCZ assignment (Karin 2019)** | `pvcz_composite` (T:H integer), `pvcz_t_rack`, `pvcz_t_roof`, `pvcz_humidity`, `pvcz_wind` |
| Köppen-Geiger | `kg_climate` |
| Mounting | `tracking` (fixed/tracking), `type` (roof/ground/single-axis tracker/dual-axis tracker/carport/unknown) |
| Coverage | `first_timestamp`, `last_timestamp`, `years`, `number_records`, `dataset_size_mb` |
| QA | `available_sensor_channels`, `qa_status`, `qa_issue` |

**HUGE WIN:** Karin 2019 PVCZ zone assignments are **pre-computed for all 1862 systems**. No separate lookup needed; direct join.

---

## 2. PVDAQ cohort sizing (initial scan)

QA-passing systems with ≥0.5 yr coverage: **1564 / 1862 (84%)**
QA-passing with ≥2 yr: 1527
QA-passing with ≥5 yr: **1288** (longitudinal cohort feasible)

### PVCZ T-zone distribution (QA-pass, years ≥ 0.5)

| T-zone | Count | Note |
|---|---|---|
| T1 (≤14 °C) | 8 | sparse — high-latitude/cold sites |
| T2 (14-19 °C) | 50 | |
| T3 (19-24 °C) | 506 | dominant moderate |
| T4 (24-29 °C) | 761 | dominant warm |
| T5 (29-34 °C) | 217 | hot |
| T6 (34-39 °C) | 22 | sparse — very hot (likely AZ/NV/inland desert) |

**Coverage gap:** T1, T6+ extremely sparse. T7-T10 effectively zero in PVDAQ. **For hot-climate degradation findings beyond ~T5, PVDAQ insufficient** — would need additional cohorts (Sandia RTC outdoor arrays, partner installations in MENA/Australia/Sahel).

### PVCZ H-zone distribution

| H-zone | Count | Note |
|---|---|---|
| H1 (0.7-3.0 g/kg) | 47 | arid |
| H2 (3.0-4.1 g/kg) | 152 | semi-arid |
| H3 (4.1-5.9 g/kg) | **1291** | dominant temperate-moderate (82%) |
| H4 (5.9-10.5 g/kg) | 74 | subtropical |
| H5 (10.5-18.3 g/kg) | **0** | **no tropical-humidity coverage** |

**Coverage gap:** H5 (tropical) entirely absent from PVDAQ. Maritime + tropical-equatorial degradation not in this fleet.

### Composite PVCZ concentration

Top 2 zones cover **78% of QA-pass data:**
- T3:H3 (moderate-temperate / moderate-humidity): 481 systems
- T4:H3 (warm-temperate / moderate-humidity): 719 systems

**ℙ₀ partition implication for 19_PREREG_v1.0_TOPCon_UVID:** ~12 PVCZ cells have meaningful (≥20) PVDAQ presence. Per pre-reg §11 termination criterion `n_c ≥ 50 per leaf`, only ~4-6 PVCZ cells are individually viable; rest will need aggregation rules per §7 sub-decomposition.

Total available data volume (QA-pass + years ≥ 0.5): **~213 GB** parquet/CSV.

---

## 3. HONEST BLOCKER — cell architecture absent at systems-index level

**No `cell_technology` / `module_arch` / `cell_type` column in 1862-row PVDAQ systems CSV.**

The `type` column means MOUNTING (roof/ground/carport/tracker), NOT cell architecture. The `tracking` column is fixed-vs-tracking, also mounting.

### Cell-tech detection via `system_public_name` string search

| Pattern | Matches | Note |
|---|---|---|
| `CIGS` | 2 | thin-film NREL CIGS-11, CIGS-12 |
| `CIS` | 2 | older CIS NREL systems |
| `x-Si` | 4 | NREL x-Si -1, low-X x-Si, x-Si 6, x-Si 7 (generic c-Si reference systems) |
| `bifacial` | 1 | single bifacial system |
| **`TOPCon`** | **0** | **NONE** |
| `TPC` | 0 | |
| `HJT` / `SHJ` | 0 | |
| `n-type` | 0 | |
| `PERC` | 0 | |
| `Al-BSF` / `BSF` | 0 | |
| `tandem` | 0 | |

**TOPCon cohort identification through PVDAQ systems-index alone is NOT feasible.** Public names use site labels (e.g., "Residential - NOLA -31"), not module specs.

### Paths forward for TOPCon identification

1. **Pull JSON metadata per system_id from S3.** PVDAQ documentation references richer per-system metadata files in S3. Possible cell-tech encoding there.
2. **Cross-reference manufacturer + commission date.** TOPCon market-ramp is ~2022+ per ITRPV. Filter PVDAQ for `first_timestamp ≥ 2022` AND manufacturer/datasheet known → small post-2022 commissioning cohort. Operationally: probably <50 systems.
3. **Sandia RTC partnership** for purpose-installed TOPCon arrays. Industry-standard reference platform.
4. **DuraMAT direct** still preferred; alternate-host email path (`duramat-help@nrel.gov`) for non-NREL mirror.
5. **Manufacturer test-bench partnership.** TOPCon-specific outdoor arrays at JinkoSolar, LONGi, JA Solar, Trina under NDA terms.

**My read:** Path 1 (JSON metadata per system) is cheapest next step; if it doesn't contain cell-arch, Path 5 (manufacturer outreach) becomes load-bearing.

---

## 4. rdtools — cloned + ready

**Source:** `https://github.com/NREL/rdtools.git`
**Path:** `D:/Renewables/Solar/code/rdtools/`
**License:** MIT
**Maintainer:** NREL (`RdTools@nrel.gov`)

### Repo structure

```
code/rdtools/
├── CITATION.cff
├── CODE_OF_CONDUCT.md
├── LICENSE
├── MANIFEST.in
├── README.md
├── docs/
├── rdtools/        ← Python package
│   ├── __init__.py
│   ├── aggregation.py
│   ├── analysis_chains.py
│   ├── availability.py
│   ├── bootstrap.py
│   ├── clearsky_temperature.py
│   ├── data/
│   ├── degradation.py       ← YoY methodology (Deceglie 2018 + Jordan 2022)
│   ├── filtering.py
│   ├── models/
│   ├── normalization.py
│   ├── plotting.py
│   ├── soiling.py
│   ├── test/
│   └── utilities.py
├── requirements-min.txt
├── requirements.txt
├── setup.cfg
├── setup.py
└── versioneer.py
```

### Operational role in 19_PREREG_v1.0_TOPCon_UVID

Per pre-reg §14 Step 5 (moment-flow computation):
- `rdtools.normalization` — normalize raw kWh to per-Wp performance index
- `rdtools.filtering` — clearsky / poor-data filtering before trajectory build
- `rdtools.degradation` — YoY rate computation (per Deceglie 2018 + Jordan 2022 fleet methodology)
- `rdtools.aggregation` — monthly bin aggregation (matches pre-reg ≥24 monthly bin termination criterion)
- `rdtools.analysis_chains` — opinionated pipeline (Jordan 2022 SDA / TrendAnalysis)

**Install action deferred:** Cloning ≠ install. `pip install -e ./Solar/code/rdtools/` is the next step when first PVDAQ system data is pulled for trial run.

---

## 5. CLM-ledger entries to add

| ID | Claim | Status | Notes |
|---|---|---|---|
| CLM-058 | PVDAQ public lake @ s3://oedi-data-lake/pvdaq/ has 1862 systems with pre-computed Karin PVCZ zone assignments (composite, t_rack, t_roof, humidity, wind) | **VERIFIED** | PVDAQ_systems_20250729.csv schema |
| CLM-059 | PVDAQ QA-passing systems with ≥0.5 yr coverage: 1564/1862 (84%) | **VERIFIED** | Direct CSV computation |
| CLM-060 | PVDAQ QA-passing with ≥5 yr coverage: 1288 systems | **VERIFIED** | Same |
| CLM-061 | PVDAQ T-zone coverage T1=8, T2=50, T3=506, T4=761, T5=217, T6=22, T7+=0 | **VERIFIED** | T-zone distribution scan |
| CLM-062 | PVDAQ H-zone coverage H1=47, H2=152, H3=1291, H4=74, H5=0 | **VERIFIED** | H-zone distribution scan |
| CLM-063 | PVDAQ has no tropical-humidity (H5) coverage at all | **VERIFIED** | Same |
| CLM-064 | PVDAQ has no high-temperature (T7-T10) coverage at all | **VERIFIED** | Same |
| CLM-065 | PVDAQ systems-index CSV has no cell-architecture / module-arch field; only mounting (`type`/`tracking`) | **VERIFIED** | Schema inspection |
| CLM-066 | PVDAQ `system_public_name` string search finds zero TOPCon / HJT / SHJ / PERC / Al-BSF labeled systems | **VERIFIED** | Direct string search across all 1862 rows |
| CLM-067 | PVDAQ license is CC-BY 4.0 | **VERIFIED** | OEDI submission page |
| CLM-068 | rdtools package (NREL, MIT license) cloned to local Solar/code/; modules: aggregation, analysis_chains, availability, bootstrap, clearsky_temperature, degradation, filtering, normalization, plotting, soiling | **VERIFIED** | Direct clone + ls |

---

## 6. Update to NEXT.md §5 blockers

**DuraMAT blocker — RECLASSIFIED:**
- ~~"NREL SSL/TLS host issue" — primary path blocked~~
- → "PVDAQ alternate path LIVE @ OEDI S3; index CSV in hand. **TOPCon cohort identification still pending** — index lacks cell-architecture field."

**Karin 2019 zone thresholds blocker — CLOSED** (memo 20).

**T13-30:2025 SLIDES blocker — CLOSED** (memo 21).

**rdtools clone — DONE.**

**New blocker added:** Cell-architecture metadata for TOPCon cohort identification — requires Path 1 (S3 per-system JSON) or Path 5 (manufacturer outreach). See §3.

---

## 7. Storage

- `D:/Renewables/Solar/data/raw/datasets/PVDAQ_systems_20250729.csv` (gitignored)
- `D:/Renewables/Solar/code/rdtools/` (git submodule? — no, separate clone; .gitignored or tracked? — currently untracked; decide on commit)

---

**END MEMO 22**
