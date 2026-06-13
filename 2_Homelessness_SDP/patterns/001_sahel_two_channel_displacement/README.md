# Pattern 001 — Sahel: conflict-displacement and flood-displacement run orthogonal

- **ID:** PATTERN_001
- **Status:** candidate-hypothesis
- **Type:** mechanism-candidate
- **Discovered:** 2026-05-21 via `build_sahel_stratified.py` first look
- **Severity / interest:** high

## One line
Conflict-displacement tracks state collapse (V-Dem libdem); flood-displacement does not — and Niger had nearly 1M flood-displaced in 1998-2013, before its political crisis.

## Numbers

| Country | Pre-crisis (1998-2013) | Acute (2020-2024) |
|---|---|---|
| | Conflict / Disaster (cum.) | Conflict / Disaster (cum.) |
| BFA | 0 / 199,800 | 2,728,000 / 50,400 |
| MLI | 350,000 / 59,300 | 995,000 / 68,700 |
| NER | 0 / 983,900 | 628,000 / 1,916,000 |
| BEN | 0 / 490,000 | 7,700 / 27,600 |

## Why it stands out
Three of four countries had measurable disaster-displacement *before* any conflict-displacement. Niger especially: ~1M flood-displaced 1998-2013 with zero conflict-displaced. In the acute period the two channels are still distinct: NER's 1.9M flood-displacement is its own crisis, not driven by JNIM/ISGS. BFA is the opposite — conflict dominates (98% of acute displacement). If the channels are truly orthogonal, an additive (country + year + governance) model will miss it; a residue-class (country × year × cause-channel) cell should add explanatory variance.

## Open questions
- Does the orthogonality hold at admin-1 (sub-national) level, or only country?
- Are there years where BOTH channels surge in the same country-year (coupling)?
- Does CHIRPS rainfall anomaly predict flood-displacement independent of governance?
- What's the timing — does flood-displacement happen in months without conflict events, or are they spatially separated within a country?

## Related
- [[PATTERN_004]] Niger 2024 flood-as-larger-than-war is the strongest single data point
- [[PATTERN_007]] Drought-displacement is invisible in GIDD; would change the picture if added

## Data sources
- `D:/IDP/analysis/sahel_stratified_panel_2026_05_21.parquet`
- `D:/IDP/data/idmc_gidd/IDMC_GIDD_Conflict_Violence_Disasters.xlsx` sheet `1_Displacement_data`
- `D:/IDP/data/idmc_gidd/IDMC_GIDD_Disasters_Internal_Displacement_Data.xlsx`
