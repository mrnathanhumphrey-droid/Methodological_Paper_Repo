# P1-I — V-Dem Subnational Data Acquisition (2026-05-25)

**Thread**: P1-I (V-Dem sub-national data for federal-friction test)
**Status after**: closed-data-identified (acquisition queued; not blocking Paper 1)
**Method**: Web search for V-Dem subnational datasets

## Data source identified — ISED

**Index of Subnational Electoral Democracy (ISED)**
- Authors: Imke Harbers et al.
- Coverage: US states, Canadian provinces, Indian states, 9 Latin American countries (likely ARG, BRA, COL, MEX, VEN, PER, BOL, CHL, ECU)
- Time span: ~40 years (~1985-present)
- Type: subnational electoral-democracy index (parallel to V-Dem's libdem but at sub-national level)
- Citation: Harbers et al. 2023, *Democratization*, "Measuring and assessing subnational electoral democracy: a new dataset for the Americas and India"
- URL (paper): https://www.tandfonline.com/doi/full/10.1080/13510347.2023.2183195

V-Dem itself does NOT have a subnational dataset; ISED is the closest existing scholarly equivalent.

## Why this matters for federal-friction (P1-B)

P1-B established federal-friction slow-burn at COUNTRY level. ISED would enable:
- **State-by-state variation within IND**: do Modi-affiliated BJP states show faster libdem decline than non-BJP states?
- **State-by-state variation within USA**: do GOP-controlled states show faster libdem decline than Democratic states? Especially 2024-2025 breakout period.
- **BRA states**: do Bolsonaro-aligned states show different sub-indicator trajectories than opposition states?
- **MEX states**: Morena vs PAN vs PRI-controlled states

If federal-friction is real, BJP-state libdem should decline faster than non-BJP-state libdem; GOP-state faster than non-GOP-state.

## Why P1-I is closed-data-identified (not closed-supported)

The full sub-national analysis requires:
1. Downloading ISED dataset (likely available via Harvard Dataverse or replication package — needs follow-up)
2. Cleaning + harmonizing with V-Dem country-level data
3. Computing state-by-state libdem trajectories
4. Cross-tabulating with party-control data (which is non-trivial — would need ANES/CSES, US state-government records, IND ECI data, etc.)
5. Statistical testing for federal-friction sub-national effect

This is a 1-2 week project, not a session-scale thread pull. The country-level federal-friction confirmation (P1-B) is sufficient for Paper 1's main argument. Sub-national analysis becomes a robustness check / extension.

**Decision**: Close P1-I as data-identified. Acquisition + analysis added to threads register as a follow-up task for Paper 1 robustness work or as a separate Paper 1b / 2 contribution.

## Implications for Paper 1

The Paper 1 federal-friction claim (PATTERN_013 + P1-B) can be written using:
- Country-level V-Dem libdem rates (sufficient evidence)
- Country-level judicial-constraints sub-indicator (IND 17-year hold, then erosion)
- Qualitative case discussion (USA SCOTUS 6-3 capture; Modi era acceleration; MEX Morena reforms)

Sub-national analysis is a **robustness check / methodology extension** — desirable but not load-bearing.

## Implication for the substrate

The substrate now has a clearly identified data acquisition task that's beyond session-scale:
- Add **O-O — ISED dataset acquisition + sub-national federal-friction analysis** to the threads register

This is a Paper 1 extension / Paper 1b candidate rather than a critical-path closure.

## Closure of P1-I

P1-I is closed-data-identified. ISED is the right data source for the federal-friction sub-national test. Acquisition is non-trivial (out of session scope). Paper 1 can proceed without it; sub-national analysis becomes follow-up work.

## Cross-references
- [[PATTERN_013]] — country-level evidence sufficient
- [[PATTERN_026]] — USA state-level data would refine the federal-friction breakout finding
- [[PRE_REG_008]] — durability prediction could be tested at state level too
- Harbers et al. 2023 *Democratization* — ISED publication

## Sources
- [Harbers et al. 2023 — Measuring subnational electoral democracy (Democratization)](https://www.tandfonline.com/doi/full/10.1080/13510347.2023.2183195)
- V-Dem main website: https://www.v-dem.net/data/
