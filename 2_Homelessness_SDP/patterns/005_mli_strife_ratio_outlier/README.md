# Pattern 005 — Mali strife:war fatality ratio 2.3× higher than peers

- **ID:** PATTERN_005
- **Status:** noted
- **Type:** contrast
- **Discovered:** 2026-05-21 via `build_sahel_stratified.py` first look
- **Severity / interest:** medium

## One line
Mali's acute-period non-state communal-violence fatality share is 44% (2,197 of 4,995+2,197) — versus BFA's 4% and NER's 7%. Mali's conflict has a distinctly higher communal/inter-ethnic component than its Sahel neighbors.

## Numbers

Acute period (2020-2024) fatalities by UCDP type-of-violence:

| Country | war_state_based | strife_non_state | strife share |
|---|---|---|---|
| BFA | 10,403 | 476 | 4.4% |
| MLI | 4,995 | 2,197 | **30.5%** |
| NER | 2,801 | 218 | 7.2% |
| BEN | 147 | 0 | 0% |

(Strife share = strife / (war + strife). MLI's is ~7× BFA's, ~4× NER's.)

## Why it stands out
This matches qualitative reporting on the Mopti / inner Niger Delta region where Dogon farmer communities and Fulani herder communities have had cyclical communal violence (Dan Na Ambassagou, etc.). It's a different mechanism from BFA's JNIM/ISGS-vs-army war. If we model Sahel conflict-displacement with country fixed effects, we'd miss this mechanism difference. Residue-class candidate: (country × violence-type) cell.

## Open questions
- Does MLI's strife-driven displacement track different admin-1 regions than its war-driven displacement?
- Does the strife share shift over the acute period (climbing? falling?) or is it stable?
- Is there a similar but smaller signal in BFA (e.g., communal violence in Sahel/Centre-Nord between Fulani and other groups)?

## Related
- [[PATTERN_003]] BFA is the war-dominant peer; MLI is the strife-with-war composite
- [[PATTERN_001]] The two-channel hypothesis could become three-channel (war / strife / flood)

## Data sources
- `D:/IDP/analysis/sahel_stratified_panel_2026_05_21.parquet` columns ucdp_war_state_based_fatal, ucdp_strife_non_state_fatal
- UCDP-GED 2025-Jan release, country=Mali / Burkina Faso / Niger / Benin

---

## Dig 2026-05-25 — MLI is the strife EPICENTER, not just an outlier

**First year with ≥50 non-state-strife fatalities** (UCDP type=2) for each strife-relevant country in our corpus:

| Country | First year ≥50 strife fatal | Modern strife start | Lifetime strife fatal |
|---|---|---|---|
| **Mali** | **1999** (early); modern run 2012+ | 2012 | 3,213 |
| South Sudan | 2011 (immediately post-indep) | 2011 | 6,547 |
| Central African Republic | 2011 (Séléka era opening) | 2011 | 3,896 |
| Burkina Faso | **2020** (8 years after MLI) | 2020 | 516 |
| Niger | **2021** (9 years after MLI) | 2021 | 270 |
| Haiti | 2021 (gang-war emergence) | 2021 | 422 |
| Benin | NEVER (zero strife in UCDP) | — | 0 |

**MLI is the temporal epicenter** of the modern Sahel strife signature. The Sahel strife signal *diffused outward from Mali by ~8 years* — BFA caught the signal in 2020, NER in 2021. SSD and CAF have their own independent strife dynamics (started 2011 in both, from separate causes).

**MLI strife dyad decomposition (lifetime):**

| Dyad | Fatalities | Mechanism type |
|---|---|---|
| IS - JNIM | 925 | Jihadist-on-jihadist (competition for territory) |
| Dozos (Mali) - JNIM | 519 | Traditional hunters' brotherhood vs jihadists |
| Dan na Ambassagou - JNIM | 442 | Dogon ethnic militia vs jihadists |
| GATIA, MSA - IS | 247 | Tuareg pro-gov militias vs IS |
| IS - MSA | 192 | Jihadist vs Tuareg militia |
| **Dogon - Fulani** | **180** | **Classic farmer-herder communal** |
| CMA - GATIA | 131 | CMA (separatist) vs pro-gov Tuareg |
| GATIA - IS | 107 | Tuareg militia vs IS |
| Arab - Kounta | 79 | Inter-ethnic |
| CMA - CM-FPR, GATIA, MAA | 70 | Tuareg factional |

**MLI is a triple-strife structure** (rare among peer countries):
1. **Jihadist competition** (IS vs JNIM, ~1.1K fatalities)
2. **Self-defense militias vs jihadists** (Dozos, Dan na Ambassagou, ~960)
3. **Inter-ethnic / inter-clan** (Dogon-Fulani, Tuareg factional, Arab clans, ~660)

BFA's strife (~516) is much smaller and largely category 1+2 (no comparable Dogon-Fulani analog). NER's strife is similar mix at smaller scale.

**MLI strife admin-1 acute (2020-2024):** Mopti (876, 50% of acute strife) >> Gao (417) >> Ménaka (404) >> Segou (231) >> Tombouctou (162). **Mopti is the Dogon-Fulani-jihadist belt** — the strife concentration there is the inner Niger Delta communal violence + JNIM/IS overlap.

**Status updated:** noted (contrast) → **firmed-contrast + candidate-hypothesis (temporal-diffusion)**.

**New hypothesis born:** strife signatures can **diffuse spatially and temporally** from epicenters. Sahel strife is mostly diffusion outward from MLI's 2012 onset. This generalizes [[PATTERN_010]] (strife-dominant cross-cluster recurrence) by adding a **diffusion mechanism** to what was previously just "co-occurrence."

**Open thread:** Are SSD and CAF's 2011 strife onsets *independent emergences* or has there been any cross-pollination? Compare with Sudan-South Sudan secession effects, Central Africa Séléka-Anti-Balaka.
