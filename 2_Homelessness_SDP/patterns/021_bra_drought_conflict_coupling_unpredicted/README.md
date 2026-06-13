# Pattern 021 — Brazil shows unpredicted conflict-drought coupling (ρ=0.697)

- **ID:** PATTERN_021
- **Status:** noted (unpredicted exception to PATTERN_001)
- **Type:** anomaly + mechanism candidate
- **Discovered:** 2026-05-25 via PRE_REG_004 holdout fit
- **Severity / interest:** medium — interesting exception, needs investigation

## One line
Brazil's annual conflict-displacement and drought-displacement are strongly correlated (Spearman ρ = **0.697**) across 2008-2024. This violates [[PATTERN_001]]'s 3-channel orthogonality hypothesis and was NOT pre-specified as an exception in PRE_REG_004 (which expected SOM/SDN/Horn as the only conf-drought coupling cases).

## Numbers (BRA 2008-2024)
- Spearman ρ(conf_IDP, flood_IDP) = 0.415
- Spearman ρ(conf_IDP, drought_IDP) = **0.697** (predicted: ≤0.3 ortho; actual: well above)
- Spearman ρ(flood_IDP, drought_IDP) = 0.386

Brazil drought-displacement appears to spike in the same years as conflict-displacement. Need year-by-year inspection to determine mechanism.

## Why it stands out
- **Unpredicted exception** — we pre-registered SOM/SDN as the only expected conflict-drought couplings (famine-conflict feedback in Horn). BRA was expected to fit Regime 2 (steady-flood) with low coupling.
- **Brazil is not a famine country** in the standard sense — strong conf-drought coupling is unexpected from a middle-income agricultural giant
- **Possible mechanisms:**
  - (a) Amazon drought 2010, 2015-16, 2023-24 → indigenous community displacement + secondary land-rights conflict displacement (logging, mining, evictions during drought-weakened agriculture)
  - (b) Northeast drought (sertão) → rural-to-urban migration → favela conflict displacement (statistical artifact via reverse causation)
  - (c) Coding artifact in GIDD — some drought events may be coded as conflict-displacement when the proximate cause is post-drought land conflict
  - (d) ENSO teleconnection coupling — La Niña years drive both Amazon drought AND political tensions

## Implications for PRE_REG_004
- This is a falsifier F2 candidate (conf-drought coupling outside the Horn). Combined with the other potential F2 (would need ≥2 outside-Horn countries), this hasn't yet fired F2 alone — but it's a YELLOW flag.
- **NOT a F1 (general orthogonality) violation** because PRE_REG_004's H1 still holds in ~92% of countries; BRA is one exception.
- Refinement: H3 should add "Amazon drought → indigenous/extractive-frontier conflict" as a 4th specified exception alongside Horn famine-conflict.

## Open questions
- Year-by-year inspection: which years drive the correlation? (likely 2010, 2015-16, 2023-24)
- Admin-1 decomposition: is the coupling concentrated in Amazon states (Amazonas, Pará, Roraima)?
- Compare with neighboring drought-prone Amazonia countries (PER, BOL, COL) — does Amazon drought drive conf-drought coupling in PER/BOL too?
- Look at GIDD source documentation — is BRA's "drought" classification potentially capturing what should be land-conflict displacement?

## Related
- [[PATTERN_001]] 3-channel orthogonality — this is the first significant unpredicted violation
- [[PRE_REG_004]] 3-channel orthogonality pre-reg — this result is a yellow-flag refinement
- [[PATTERN_008]] drought-channel real globally — BRA confirms drought channel exists; just unexpectedly coupled here

## Data sources
- `D:/IDP/analysis/prereg_holdout_stratified_panel_2026_05_21.parquet` rows iso3=BRA
- GIDD displacement + GIDD Disasters drought hazard
- Spearman correlation 2008-2024
