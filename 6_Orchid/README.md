# Phenotype_Research

Data corpus for the first biological-substrate addition to the methodology corpus extension. Per `DIAGNOSTIC_LAYER_RESEARCH_DESIGN.md`: testing whether the partial-pooling-on-residual-classes-with-structural-priors methodology generalizes to plant trait variation along environmental gradients (precipitation, soil, elevation, latitude) — the cleanest "no decision-making" biological substrate, as a prerequisite for the full 2×2 diagnostic-layer comparison.

This folder is the data side. Analysis goes in `D:\corpus_extension\` (the corpus extension workspace) once probes start firing.

## Status (2026-05-12)

**~1.7 GB pulled.** Most public data is on disk; TRY and BIEN require user-side registration steps (instructions below).

| Tier | Status |
|---|---|
| Climate (WorldClim 2.1) | ✅ 7 zips: bioclim @ 2.5m/5m/10m, monthly tavg/tmin/tmax/prec @ 10m |
| Soil (SoilGrids 2.0) | ✅ 60 GeoTIFFs: 10 properties × 6 depths @ 5km |
| Elevation (WorldClim DEM) | ✅ 5m + 10m elev rasters |
| Ecoregions (Dinerstein 2017 / Olson successor) | ✅ Ecoregions2017.zip, 149 MB |
| Vegetation plots (sPlotOpen) | ✅ 105 MB — 95,104 plots, 42,677 species, environmentally-balanced |
| Plant occurrences (GBIF API sample) | ✅ 6 JSON pulls (kingdom + 4 families) |
| Trait aggregator (Open Traits Network) | ✅ OTN species/traits/family summary, 17 MB |
| TRY plant trait database | ⚠️ requires free user registration — see [scripts/FETCH_PENDING.md](scripts/FETCH_PENDING.md) |
| BIEN database | ⚠️ R package only (no public REST/HTTP) — see [scripts/FETCH_PENDING.md](scripts/FETCH_PENDING.md) |
| AusTraits | ⚠️ build infra pulled; data file needs Zenodo version-specific URL — see [scripts/FETCH_PENDING.md](scripts/FETCH_PENDING.md) |

## Layout

```
D:\Phenotype_Research\
├── README.md                  — this file
├── DATA_INVENTORY.md          — per-file description + provenance
├── data/
│   ├── climate/               — WorldClim 2.1 bioclim, temp, precip (988 MB)
│   ├── elevation/             — WorldClim 2.1 elevation DEM (6 MB)
│   ├── soil/                  — SoilGrids 2.0 5km, 10 properties × 6 depths (469 MB)
│   ├── ecoregions/            — Dinerstein 2017 ecoregions / biomes (149 MB)
│   ├── occurrences/           — GBIF API samples + sPlotOpen 105 MB
│   └── traits/                — OTN summary + AusTraits build (22 MB so far)
├── notes/                     — pre-reg drafts, methodology notes (empty; for user)
├── scripts/
│   └── FETCH_PENDING.md       — instructions for TRY, BIEN, AusTraits manual fetches
└── pdfs/                      — relevant lit (empty; user can drop papers here)
```

## Next steps for the user

1. **TRY registration:** free user account at https://www.try-db.org/ → submit a Public Data Request → download. Instructions in [scripts/FETCH_PENDING.md](scripts/FETCH_PENDING.md).
2. **BIEN install:** R + `install.packages("BIEN")` → fetch script in [scripts/FETCH_PENDING.md](scripts/FETCH_PENDING.md).
3. **AusTraits data file:** check https://zenodo.org/communities/austraits-data for current versioned Zenodo DOI; the github master.zip we have is just the build infrastructure.

Once 1–3 are in place, the first plant-phenotype probe can be pre-registered in `D:\corpus_extension\notes\`.

## Provenance

Per the methodology corpus discipline ([C:\Users\Nate\OneDrive\Documents\methodology\METHODOLOGY_NOTES.md](C:\Users\Nate\OneDrive\Documents\methodology\METHODOLOGY_NOTES.md), locked 2026-05-12 as the "Paper 6" snapshot), every dataset has a citation + source URL in `DATA_INVENTORY.md`. All sources are public and most are CC-BY licensed; the few that require registration (TRY, BIEN) have free user accounts.
