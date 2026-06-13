# Pattern 007 — Drought displacement is invisible in GIDD Disasters for Sahel; only flood is logged

- **ID:** PATTERN_007
- **Status:** noted
- **Type:** data-quality-flag
- **Discovered:** 2026-05-21 via `build_sahel_stratified.py` first look
- **Severity / interest:** medium

## One line
The GIDD Disasters file logs 100% of Sahel disaster-displacement as `flood` hazard type. Zero drought-displacement is captured, despite the Sahel being one of the world's most drought-prone regions and drought being a documented displacement driver.

## Numbers

Disaster-displacement by hazard type, Sahel acute period 2020-2024 (GIDD Disasters):

| iso3 | disaster_flood | disaster_drought | other |
|---|---|---|---|
| BFA | 51,000 | 0 | 0 |
| MLI | 68,810 | 0 | 0 |
| NER | 1,916,500 | 0 | 0 |
| BEN | 27,620 | 0 | 0 |

## Why it stands out
Drought is rarely a single discrete displacement *event* — it's a slow-onset stressor that displaces people over months/years through livestock loss, harvest failure, food insecurity, and eventual migration. IDMC's "displacement event" methodology requires identifiable events with attributable trigger and displacement count; that excludes slow-onset drought displacement almost by construction. This is not a bug in our pipeline — it's a methodological limitation of the source. For Sahel analysis, drought displacement has to come from a different channel: IPC food-insecurity phase + FEWS NET food-security shapefile coverage + climate driver overlays (SPEI drought index, CHIRPS rainfall anomalies).

## Open questions
- What does HAPI food_security (IPC phase 3+) show for Sahel — does the population-in-crisis figure capture drought-affected populations that GIDD misses?
- Does SPEI-12 drought intensity for Sahel correlate with later-year IPC phase escalation?
- Can we proxy "drought-displacement" via population_in_crisis * average crisis-to-displacement ratio from comparator regions?

## Related
- [[PATTERN_001]] The two-channel hypothesis becomes three-channel if drought is added as a distinct mechanism
- [[PATTERN_004]] NER 2024 flood story would shift if drought was also visible

## Data sources
- `D:/IDP/data/idmc_gidd/IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx`
- Will need: HAPI food_security pagination, FEWS NET Sahel shapefiles (already have), SPEI extract
