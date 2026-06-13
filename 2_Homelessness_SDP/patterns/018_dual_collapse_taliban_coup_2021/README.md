# Pattern 018 — Twin 2021 libdem collapses: AFG (Taliban) + MMR (military coup)

- **ID:** PATTERN_018
- **Status:** candidate-hypothesis
- **Type:** mechanism (trigger-typology)
- **Discovered:** 2026-05-25 via South Asia cluster build
- **Severity / interest:** medium-high (extends [[PATTERN_011]]/[[PATTERN_013]] trigger typology)

## One line
AFG (Taliban takeover Aug 2021) and MMR (military coup Feb 2021) both collapsed libdem from mid-range to near-floor in the same year via **different trigger mechanisms**, both classifiable as forms of authoritarian-takeover-from-outside-the-existing-system.

## Numbers

| Country | 2020 libdem | 2024 libdem | Δ | Trigger | Trigger type |
|---|---|---|---|---|---|
| AFG | 0.167 | 0.014 | **−0.153** | Taliban takeover Aug 2021 | armed-faction conquest |
| MMR | 0.252 | 0.015 | **−0.237** | Tatmadaw coup Feb 2021 | military coup |

Both end at ~0.014-0.015 (floor). Sahel-style trajectory but different geography.

For comparison, the Sahel coup-collapse cases (PATTERN_002):
- BFA 0.485 → 0.126 (military coups 2022, 2023)
- MLI 0.307 → 0.141 (military coups 2020, 2021)
- NER 0.405 → 0.182 (military coup 2023)

Same shape, ~similar magnitudes.

## Why it stands out
- **Cross-region replication**: PATTERN_011's range-then-trigger model now has cases in Sahel (3), LatAm (HTI, SLV), Central Africa (CAF), and South Asia (AFG, MMR). 9 collapse cases across 4 continents.
- **Trigger-typology expanding**: We now have at least 4 trigger types in the corpus that all produce libdem-collapse:
  1. **Military coup** (Sahel, MMR)
  2. **Armed-faction conquest** (AFG, CAF as Wagner/Touadéra coalition)
  3. **Civilian-authoritarian consolidation** (SLV, [[PATTERN_013]] Bukelization)
  4. **State-fragility-by-civil-war** (SYR-style, already-floor-locked)
- **Confirms PAK control**: PAK same 2018 range as MMR but no trigger event → no collapse. The trigger is the active ingredient given range.

## Open questions
- Do the trigger types produce the **same displacement-mechanism** downstream, or different? AFG saw massive emigration; MMR saw internal displacement to ethnic regions; SLV had no major displacement; Sahel coups produced mixed displacement.
- Is the "armed-faction conquest" path (AFG, CAF) a distinct category from "military coup" (Sahel, MMR)? Both involve military force but the relationship to the existing state differs.
- Does the trigger-typology predict downstream displacement-displacement-magnitude? Hypothesis: armed-faction conquest > military coup > civilian-authoritarian consolidation, for short-term IDP flows.

## Related
- [[PATTERN_011]] range-conditioning — this pattern adds cases and trigger-typology
- [[PATTERN_013]] Bukelization — alternative civilian-authoritarian trigger
- [[PATTERN_002]] Sahel coup-collapse — original observation, now part of a larger family

## Data sources
- `D:/IDP/analysis/south_asia_stratified_panel_2026_05_21.parquet`
- V-Dem v15
- Known historical triggers (Taliban Aug 2021; Tatmadaw Feb 2021)
