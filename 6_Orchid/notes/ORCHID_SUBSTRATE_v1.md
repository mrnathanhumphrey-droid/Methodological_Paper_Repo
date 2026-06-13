# Gymnadenia odoratissima decomposition substrate — v1 build

**Built:** 2026-06-01. All data products live under `D:/Phenotype_Research/`.

## Why this dataset

Three orchid candidates were vetted (see prompt 2026-06-01). Only *Gymnadenia
odoratissima* has per-individual raw data + environmental crossing in a single
public deposit:

- *Prosthechea karwinskii* (PMC11280756): supplementary is summary-stats PDF
  only; coordinates withheld for species protection. Not usable as primary.
- *Drakaea concolor* (Dryad 92961): deposit is pollinator counts + wasp
  morphology + microsats. No orchid floral measurements.
- ***Gymnadenia odoratissima*** (Dryad dj40r, Schiestl et al. PLOS ONE 2016):
  1028+ per-plant rows, lowland vs mountain regions, morphology + 22 scent
  compounds + color + reproductive success + herbivory + pollinator landscape.

## 8 populations (S1 Table of pone.0147975)

| code | name        | region   | lat (DD)  | lon (DD) | alt paper (m) | elev WC 5m (m) |
|------|-------------|----------|-----------|----------|---------------|----------------|
| D    | Doettingen  | lowland  | 47.5750   | 8.2736   | 500           | 462            |
| R    | Remigen     | lowland  | 47.5292   | 8.1625   | 600           | 477            |
| L    | Linn        | lowland  | 47.4764   | 8.1167   | 500           | 509            |
| RW   | Rossweid    | lowland  | 47.3125   | 8.5111   | 650           | 564            |
| S    | Schatzalp   | mountain | 46.8056   | 9.8250   | 1800          | 2060           |
| M    | Muenstertal | mountain | 46.6306   | 10.3181  | 1800          | 2320           |
| A    | Albulapass  | mountain | 46.5819   | 9.8139   | 2250          | 2546 *         |
| C    | Corviglia   | mountain | 46.5056   | 9.8319   | 2200          | 2546 *         |

*A and C share one 5m WorldClim elev pixel (4 km apart on Bernina ridge). The
paper-reported altitudes differentiate them (50 m). 2.5m BIO does separate them.

## Raw data on disk

```
data/orchids/gymnadenia/raw/
  doi_10_5061_dryad_dj40r__v20170119.zip
  Data__SelectionAnalysis.xlsx              (1028 plants x 72 cols)
  Data__FloralTraitDifferences.xlsx         (1162 plants x 59 cols)
  Data__ReproductiveSuccessDifferences.xlsx (1118 plants x 10 cols)
  Data__HerbivoryDifferences.xlsx           (1259 plants x 6  cols)
  Data__PollinatorLimitation.xlsx           (909 plants x 8 cols, +supplementation arm)
  Data__PhenotypicSelectionGradients.xlsx   (71 rows: pop x trait beta)
  Data__PollinatorFamiliesPerH.xlsx         (40 rows: pop x date x family counts)
  Data__NoPollinators_PollinatorFamilyRichness.xlsx
  pone.0147975.s001 ... s007.pdf            (PLOS supplements; S1_TABLE_population_locations.pdf has the coords)

data/orchids/drakaea/raw/                   (vetted but not used as primary)
data/orchids/prosthechea/raw/               (vetted; summary-only)
pdfs/prosthechea/                           (main article + XML)
```

## Phenotype columns in SelectionAnalysis (the core table)

- IDs / strata: `PlantID, Year, Region, Population`
- Morphology (3): `PlantHeight_cm, InflorescenceLength_cm, NrFlowers`
- Floral scent (22 cols, ng/L headspace): `Z3Hexen1Ol, Styrene, Heptanal,
  alphaPinene, Benzaldehyde, Sabinene, betaPinene, 6Methyl5Hepten2One,
  Z3HexenylAcetate, HexylAcetate, Limonene, BenzylAlcohol, Phenylacetaldehyde,
  PhenylethylAlcohol, BenzylAcetate, 1Phenyl12Propanedione, Phenylethylacetate,
  1Phenyl23Butanedione, Eugenol, MethylEugenol, GeranylAcetone, Benzylbenzoate`
- Color: `ColourCode`
- Fitness: `NrFruits, RelfRS`
- Z-standardized versions of all of the above
- 7 PCs from a published rotation, in both raw (`PC1-7`) and Z-scaled (`PC1A-7A`) forms

`FloralTraitDifferences` adds `TotalScentAmount_ngPerL` and LN-transformed columns.

## Environmental covariates

`data/orchids/gymnadenia/derived/gymnadenia_pop_env_v2.csv` — 8 rows x 138 cols:

- Coords + altitudes: `lat_dd, lon_dd, altitude_paper_m, elev_wc5m`
- Ecoregion (Dinerstein 2017): `ECO_NAME, BIOME_NAME, REALM, NNH_NAME`
  - Lowlands 4/4: Western European broadleaf forests | Temperate Broadleaf & Mixed Forests
  - Mountains 4/4: Alps conifer and mixed forests | Temperate Conifer Forests
- WorldClim 2.1 BIO 1-19 @ 2.5m (~4.5 km cell). All 8 pops in unique pixels.
- WorldClim 2.1 monthly tavg/tmin/tmax/prec @ 10m (48 cols).
- SoilGrids 2.0: 10 props (bdod, cec, cfvo, clay, nitrogen, ocd, phh2o, sand,
  silt, soc) x 6 depths (0-5, 5-15, 15-30, 30-60, 60-100, 100-200 cm) = 60 cols
  in IGH 5km. CRS reprojected; 8/8 pops in unique pixels.

### Climate gap headline numbers (2.5m BIO)

| code | region   | bio_1 °C | bio_6 °C (Tmin coldest mo) | bio_12 mm |
|------|----------|----------|----------------------------|-----------|
| D    | lowland  |   9.33   |   -2.68                    | 1093      |
| R    | lowland  |   8.63   |   -3.21                    | 1257      |
| L    | lowland  |   8.70   |   -3.21                    | 1272      |
| RW   | lowland  |   8.95   |   -2.74                    | 1193      |
| S    | mountain |   0.75   |  -10.36                    | 1334      |
| M    | mountain |  -0.63   |  -11.97                    |  776      |
| A    | mountain |  -1.16   |  -12.55                    | 1114      |
| C    | mountain |  -2.44   |  -13.79                    | 1110      |

Clean 7-12 °C T-gap and clean Tmin gap. M (Münstertal) is the rain-shadow site.

### Soil 0-5cm headline (lowland vs mountain)

- pH x10: lowland 62-65 (6.2-6.5), mountain 53-60 (5.3-6.0) — lowland less
  acidic. *Paper notes orchid grows on calcareous soil; SoilGrids 5km
  smooths this so does not catch outcrop-scale calcareousness.*
- Sand %: lowland 16-28, mountain 38-52
- Clay %: lowland 33-43, mountain 17-22
- Rossweid (RW) is nodata for 5 of 6 SoilGrids 0-5cm properties (phh2o, clay,
  sand, silt, cec). Deeper layers OK. 42/664 cells overall missing (6.3 %).

## Per-plant analysis substrates (env joined back)

`data/orchids/gymnadenia/derived/`:

| file                              | n plants | n cols |
|-----------------------------------|----------|--------|
| plants_selection_with_env.csv     | 1028     | 207    |
| plants_floraltrait_with_env.csv   | 1162     | 194    |
| plants_reproductive_with_env.csv  | 1118     | 145    |
| plants_herbivory_with_env.csv     | 1259     | 141    |
| plants_pollim_with_env.csv        |  909     | 143    |

All joins: 0 unmatched.

## sPlotOpen neighborhood (community context)

`data/orchids/gymnadenia/derived/`:

- `splot_neighborhood_50km.csv` — 2823 (pop, plot) pairs within 50 km of each
  Gymnadenia population. RW has most neighbors (753), C has fewest (145).
- `splot_species_neighborhood_50km.csv` — 5252 (pop, species) rows with
  n_plots, mean_rel_cover, sum_rel_cover.

Top species per pop neighborhood show a clean ecological gradient:

- **Lowland (D, L, R):** Fagus sylvatica > Fraxinus excelsior > Acer
  pseudoplatanus > Hedera helix — classic European temperate broadleaf forest.
- **RW (lowland, higher elev 650 m):** Fagus + Picea abies + Abies alba —
  mixed forest, shifted toward submontane.
- **Mountain (S, A, C):** Picea abies > Vaccinium myrtillus > V. vitis-idaea
  + Homogyne alpina — subalpine spruce-Vaccinium.
- **M (Münstertal, inner Alps):** Vaccinium + Larix decidua + Pinus cembra —
  upper subalpine larch-cembran pine, classic Central Alps inner-valley.

## Scripts

```
scripts/orchids/
  01_overlay_gymnadenia_env.py        v1 (10m BIO, no monthly, no ecoregion)
  02_overlay_gymnadenia_env_v2.py     v2 (2.5m BIO + 5m elev + monthly + soil + ecoregion)
  03_join_per_plant.py                joins env into 5 per-plant tables
  04_splotopen_neighborhood.py        50-km plot + species neighborhoods
```

## Known issues / decisions

- Albulapass + Corviglia: 5m elev pixel collision (4 km apart, both 2546 m
  in WC). Use paper-reported altitudes (2250, 2200) when elev matters; 2.5m
  BIO does separate them on climate (bio_1 -1.16 vs -2.44 °C).
- SoilGrids 5km coarseness: regional smoothing washes out outcrop-scale
  calcareousness. If soil pH/Ca becomes a load-bearing covariate, swap in
  a Swiss-specific source (Swisstopo / Agroscope soil maps).
- Rossweid 0-5cm soil cells nodata for 5 of 6 properties. Use deeper layers
  or impute neighbor.
- Sampling was 2010-2011 for most floral measurements (S1 table). Phenotype
  is a 2-year snapshot, not a multi-year average. Year is a covariate.

## What's next (deferred — not built yet)

- Within-region trait variance decomposition (between-pop vs within-pop x year)
- Lowland-mountain phenotype contrasts conditional on env covariates
- Whether scent composition orthogonalizes from morphology under env
  conditioning (the substrate this whole arc was set up to test)
- Sister-clade ladder: would require pulling congeneric *Gymnadenia*
  morphometrics (G. conopsea, G. rhellicani, etc.) from a separate source.
