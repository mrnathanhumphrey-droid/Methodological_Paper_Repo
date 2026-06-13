# FETCH_PENDING — registration / manual-step data sources

Three plant-trait sources require user action that I can't automate. Instructions below.

---

## 1. TRY plant trait database — free registration

**What you get:** ~12M trait records across ~280K species, ~2,800 traits. The definitive single source for plant traits. CC-BY but requires citation of contributing datasets.

**Steps:**

1. Go to https://www.try-db.org/TryWeb/Home.php
2. Click "Login / Register" → "Register" — free account, takes ~2 minutes
3. After login, go to the "Request Data" tab
4. Choose either:
   - **Public Data Request** — pre-curated public-domain TRY data. ~5,500 datasets, ~12M records. No data-owner approval needed; auto-approved within a few hours.
   - **Custom Data Request** — pick specific traits / species / datasets; some require data-owner approval (days to weeks).
5. Recommended first request: all public traits for the species in `sPlotOpen` (~42K species). The TRY UI accepts a species list upload.
6. Receive zip via email link. Save to `D:\Phenotype_Research\data\traits\TRY_<version>_PublicData_<date>.zip`.

**Citation when used:** TRY paper (Kattge et al. 2020 *Global Change Biology* 26:119–188) plus individual dataset DOIs as listed in the zip's `TRY_…_DataPackage.docx`.

---

## 2. BIEN — R package access

**What you get:** ~915K trait observations across 28 traits and ~93K species, plus ~81M occurrence records, plus range maps, plus stem inventories. Botanical Information and Ecology Network (NCEAS, Maitner et al. 2018).

**Why no curl pull:** BIEN runs a public PostgreSQL backend at NCEAS, accessed only via the R package `BIEN` (functions `BIEN_occurrence_…`, `BIEN_trait_…`, `BIEN_ranges_…`). No REST API.

**Steps:**

1. Install R (if not already): https://cran.r-project.org/
2. From an R console:
   ```r
   install.packages(c("BIEN", "dplyr"))
   library(BIEN)
   ```
3. Pull all trait data for a chosen scope. Example — all leaf-area observations:
   ```r
   traits <- BIEN_trait_trait("leaf area")
   write.csv(traits, "D:/Phenotype_Research/data/traits/BIEN_leaf_area.csv")
   ```
4. Or pull everything for a species list:
   ```r
   sp <- read.csv("D:/Phenotype_Research/data/occurrences/species_list.csv")$species
   traits <- BIEN_trait_species(sp, all.taxonomy = TRUE)
   write.csv(traits, "D:/Phenotype_Research/data/traits/BIEN_traits_byspecies.csv")
   ```

Available trait names (28 total): `BIEN_trait_list()` in R.

**Citation:** Maitner et al. 2018 *Methods in Ecology and Evolution* 9:373–379.

---

## 3. AusTraits — Zenodo versioned release

**What you get:** ~500 traits, ~30K Australian plant taxa. Falster et al. 2021 *Scientific Data* 8:254. Fully open, CC-BY 4.0.

**Why I couldn't auto-fetch:** the canonical concept DOI (10.5281/zenodo.3568417) needs to resolve to a specific version DOI; that resolution wasn't straightforward via curl.

**Steps (one-liner):**

1. Go to https://zenodo.org/doi/10.5281/zenodo.3568417 — this resolves to the latest version's page.
2. Download the `austraits-<version>.zip` (or use the API URL shown on that page).
3. Save to `D:\Phenotype_Research\data\traits\austraits_<version>.zip`.

Alternative — via R:
```r
install.packages("austraits")  # or remotes::install_github("traitecoevo/austraits")
library(austraits)
au <- load_austraits(version = "latest", path = "D:/Phenotype_Research/data/traits/austraits_cache/")
```

---

## Quick GBIF bulk download (if needed beyond the 6 API samples)

The API gives 300-record peeks. For the **full** GBIF plant kingdom (or any taxon subset), use the Download API:

1. Free account at https://www.gbif.org/user/profile
2. From the GBIF web UI, build a query (e.g., "Kingdom = Plantae, has coordinate = true, no geospatial issue"). Click "Download."
3. Wait minutes to hours. Receive email when ready. ~500 MB to tens of GB.
4. Save the DwC-A zip to `D:\Phenotype_Research\data\occurrences\gbif_<query>_<date>.zip`. Each download has a DOI for citation.

Alternative — Python with `pygbif`:
```python
import pygbif
res = pygbif.occurrences.download(
    queries=["taxonKey = 6", "hasCoordinate = true"],
    user="username", pwd="password", email="email"
)
# wait, then pygbif.occurrences.download_get(res, path="D:/Phenotype_Research/data/occurrences/")
```
