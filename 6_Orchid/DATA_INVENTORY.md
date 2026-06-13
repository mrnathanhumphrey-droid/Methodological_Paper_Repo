# DATA_INVENTORY — Phenotype_Research

Per-file provenance, citation, content summary, and re-fetch URL.

---

## Climate (`data/climate/`)

**WorldClim 2.1** — Fick & Hijmans 2017 *International Journal of Climatology* 37:4302–4315. Public, free, no registration. Re-fetch base URL: `https://geodata.ucdavis.edu/climate/worldclim/2_1/base/`

| File | Resolution | Variable | Source URL |
|---|---|---|---|
| `wc2.1_10m_bio.zip` | ~18.5 km | 19 bioclim vars (mean annual T, T seasonality, ann precip, etc.) | `…/wc2.1_10m_bio.zip` |
| `wc2.1_5m_bio.zip` | ~9.3 km | 19 bioclim vars | `…/wc2.1_5m_bio.zip` |
| `wc2.1_2.5m_bio.zip` | ~4.6 km | 19 bioclim vars | `…/wc2.1_2.5m_bio.zip` |
| `wc2.1_10m_tavg.zip` | ~18.5 km | 12 monthly mean temp | `…/wc2.1_10m_tavg.zip` |
| `wc2.1_10m_tmin.zip` | ~18.5 km | 12 monthly min temp | `…/wc2.1_10m_tmin.zip` |
| `wc2.1_10m_tmax.zip` | ~18.5 km | 12 monthly max temp | `…/wc2.1_10m_tmax.zip` |
| `wc2.1_10m_prec.zip` | ~18.5 km | 12 monthly precip | `…/wc2.1_10m_prec.zip` |

**Not pulled (manual if needed):** wc2.1_30s_bio.zip (~10 GB, 1 km resolution), monthly variables at 5m/2.5m, future climate projections.

---

## Elevation (`data/elevation/`)

**WorldClim 2.1 elevation** — derived from SRTM. Same Fick & Hijmans citation.

| File | Resolution | Source |
|---|---|---|
| `wc2.1_5m_elev.zip` | ~9.3 km | `…/wc2.1_5m_elev.zip` |
| `wc2.1_10m_elev.zip` | ~18.5 km | `…/wc2.1_10m_elev.zip` |

---

## Soil (`data/soil/`)

**SoilGrids 2.0** — Poggio et al. 2021 *SOIL* 7:217–240. ISRIC. CC-BY 4.0. 5 km aggregated mean from 250m base. 60 GeoTIFFs = 10 properties × 6 depths each.

| Property | Description | Depths |
|---|---|---|
| `bdod` | Bulk density (kg/dm³) | 0-5, 5-15, 15-30, 30-60, 60-100, 100-200 cm |
| `cec` | Cation exchange capacity (mmol(c)/kg) | same 6 depths |
| `cfvo` | Coarse fragments volume (%) | same 6 depths |
| `clay` | Clay content (g/kg) | same 6 depths |
| `nitrogen` | Total N (g/kg) | same 6 depths |
| `ocd` | Organic carbon density (g/dm³) | same 6 depths |
| `phh2o` | pH in water | same 6 depths |
| `sand` | Sand content (g/kg) | same 6 depths |
| `silt` | Silt content (g/kg) | same 6 depths |
| `soc` | Soil organic carbon (g/kg) | same 6 depths |

Filename pattern: `{prop}_{depth}_mean_5000.tif`. Source: `https://files.isric.org/soilgrids/latest/data_aggregated/5000m/{prop}/`.

**Not pulled:** water content layers (`wv0010`, `wv0033`, `wv1500`), `ocs` (organic carbon stock). Easy to add if needed.

---

## Ecoregions (`data/ecoregions/`)

| File | Description |
|---|---|
| `Ecoregions2017.zip` (149 MB) | Dinerstein et al. 2017 *BioScience* "An Ecoregion-Based Approach to Protecting Half the Terrestrial Realm" — successor to Olson 2001. 846 ecoregions × 14 biomes × 8 realms. Shapefile. Source: https://ecoregions.appspot.com/, CC-BY 4.0. |

**Olson 2001 original** — the WWF direct URL `assets.worldwildlife.org/publications/15/files/original/official_teow.zip` returns 403 to scrapers. If you specifically want Olson 2001 rather than Dinerstein 2017 (which is the recommended successor), grab it from a library terminal or use the R package `speciesgeocodeR::WwfLoad()`.

---

## Plant occurrences (`data/occurrences/`)

### sPlotOpen — vegetation plots

| File | Description |
|---|---|
| `sPlotOpen.zip` (105 MB) | Sabatini et al. 2021 *Global Ecology and Biogeography* 30:1740–1764. **95,104 plots, 42,677 vascular plant species, fully open-access.** Plot-level data include community-weighted means and variances of 18 plant functional traits from TRY. Three partially-overlapping environmentally-balanced datasets (~50k plots each), to be used as replicates in global analyses. Source: https://idata.idiv.de/ddm/Data/ShowData/3474. CC-BY 4.0. |

### GBIF API samples — for spot-checking + smoke testing

Six JSON pulls of 300 records each via the GBIF API. Hit `https://api.gbif.org/v1/occurrence/search?…` with the parameters below:

| File | Query | n records |
|---|---|---|
| `gbif_plantae_us_sample.json` | `taxonKey=6&country=US&hasCoordinate=true&hasGeospatialIssue=false` | 300 |
| `gbif_plantae_global_recent.json` | `taxonKey=6&year=2020,2024&hasCoordinate=true` | 300 |
| `gbif_asteraceae_sample.json` | `taxonKey=3065 (Asteraceae)&hasCoordinate=true` | 300 |
| `gbif_poaceae_sample.json` | `taxonKey=3073 (Poaceae)&hasCoordinate=true` | 300 |
| `gbif_fabaceae_sample.json` | `taxonKey=5386 (Fabaceae)&hasCoordinate=true` | 300 |
| `gbif_rosaceae_sample.json` | `taxonKey=5015 (Rosaceae)&hasCoordinate=true` | 300 |

For **full** GBIF downloads (millions of records per family) use the GBIF Download Predicate API; requires a free GBIF account and a download request (typical wait: minutes to hours; output: DwC-A or CSV).

---

## Trait aggregator (`data/traits/`)

| File | Description |
|---|---|
| `OTN_SpeciesTraitsCombinations_Family.zip` (17 MB) | Open Traits Network family-level species/trait summary table. Useful for "which traits exist for which families." Source: https://github.com/open-traits-network/otn-taxon-trait-summary. |
| `austraits.zip` (4.5 MB) | AusTraits build repo (master branch). Currently the **code**, not the trait CSV. To get the data file, fetch the latest versioned release from Zenodo — see `scripts/FETCH_PENDING.md`. |

**Major trait sources requiring registration / R install** — see `scripts/FETCH_PENDING.md`:
- **TRY** — 12M trait records, ~280K species. Free registration at try-db.org → public data request → bulk download.
- **BIEN** — ~915K trait observations, 28 traits, ~93K species. Public but R package only (`BIEN_trait_*` functions). PostgreSQL backend, no REST.
- **AusTraits data** — ~500 traits, 30K Australian taxa. Zenodo versioned release.

---

## Out of corpus (notes for future probes)

- **CHELSA v2.1** — higher-resolution climate alternative to WorldClim. Pull if WorldClim resolution proves insufficient.
- **GBIF full downloads** — vetted occurrence records at family/genus level, millions of rows. Free account at gbif.org.
- **iNaturalist DwC export** — community-science occurrences, can complement GBIF.
- **NEON** — US-only but high-quality plot data with site-level environmental measurements.

---

## Methodology corpus pointer

The methodology this corpus is being used to test is locked as the "Paper 6" snapshot at:

`C:\Users\Nate\OneDrive\Documents\methodology\` (see `CORPUS_LOCKED.md` there).

Analysis lands in `D:\corpus_extension\notes\` per the corpus extension protocol.
