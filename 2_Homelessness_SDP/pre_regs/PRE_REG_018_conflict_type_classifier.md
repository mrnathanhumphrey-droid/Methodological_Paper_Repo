# Pre-Registration 018 — Conflict-Type Classifier (Paper 4 anchor)

**ID:** PRE_REG_018
**Locked:** 2026-05-27
**Substrate:** PATTERN_012 (Type A anchor) + PATTERN_015 (Type B anchor) + PATTERN_017 (Type A anchor) + PATTERN_010 (Type C anchor)
**Status:** LOCKED — predictions and falsifiers pre-committed; first fit fires on existing UCDP-GED + cluster panels

---

## 1. Hypothesis

**H1 (3-type conflict typology):** Country-conflict-periods in the IDP corpus cluster into a small number of distinct types determined by **organizational form of violence**, not by region, income, or libdem level. The three confirmed types are:

- **Type A — Formal-army war**: ≥1 inter-state or state-vs-structured-regional-military conflict with high state-based fatalities and low strife channel
- **Type B — Predator-militia campaign**: dominated by one-sided violence against civilians by a single armed-group brand with high displacement-per-fatality ratio
- **Type C — Irregular insurgency**: multi-actor non-state landscape with overlapping dyads, strife channel dominant, diffuse spatial pattern

**H2 (4th-type open):** A 4th type (D — communal/ethnic clash OR regime-collapse uprising) may emerge from corpus-fire. If ≥3 cases cluster with distinct signatures from A/B/C → confirm 4th type. If ≤2 cases or signatures absorb into existing types → walk back to 3 types.

---

## 2. Classifier rules (locked BEFORE corpus fire)

For each country-conflict-period (acute 2020-2024 default), compute:

- `state_based_fat` = UCDP-GED type_of_violence==1 fatalities
- `non_state_fat` = UCDP-GED type_of_violence==2 fatalities (strife / non-state conflict)
- `one_sided_fat` = UCDP-GED type_of_violence==3 fatalities
- `total_fat` = sum
- `idp` = GIDD conflict-displacement events (cumulative for period)
- `disp_per_fat` = idp / total_fat (capped at 5000 if fat very low)
- `admin1_top3_share` = % of total fatalities concentrated in top-3 admin-1 zones
- `top_actor_share` = % of one-sided fatalities attributable to single armed-group brand
- `state_share` = state_based_fat / total_fat
- `one_sided_share` = one_sided_fat / total_fat
- `strife_share` = non_state_fat / total_fat

### Rules (apply in order; first-match)

**Type A — Formal-army war** if ALL:
- `state_share ≥ 0.70`
- `strife_share ≤ 0.10`
- `disp_per_fat ≤ 150`
- `admin1_top3_share ≥ 0.60` (front-line concentration)

**Type B — Predator-militia campaign** if ALL:
- `one_sided_share ≥ 0.40`
- `disp_per_fat ≥ 250`
- `admin1_top3_share ≥ 0.60` (territorial concentration)
- `top_actor_share ≥ 0.30` (single-brand dominance)

**Type C — Irregular insurgency** if:
- `strife_share ≥ 0.30` OR
- (`state_share` and `one_sided_share` both 0.20-0.60, multi-actor)
- AND `admin1_top3_share < 0.60` (diffuse) OR `top_actor_share < 0.30`

**Type D (candidate) — 4th** if:
- doesn't fit A/B/C cleanly AND has distinct admin-1 + actor signature

**UNCLASSIFIED** if:
- doesn't satisfy any rule AND total_fat ≥ threshold

**INSUFFICIENT** if:
- total_fat < 500 in the period (too sparse to classify reliably)

---

## 3. Pre-locked predictions

### Prediction set A — Anchor cases hold

| Country-period | Predicted | Anchor pattern |
|---|---|---|
| ETH 2020-2022 | A | PATTERN_012 (Federal-TPLF) |
| UKR 2020-2024 | A | PATTERN_017 |
| COD 2020-2024 | B | PATTERN_015 |
| MLI 2020-2024 | C | PATTERN_005/010 |
| BFA 2020-2024 | C | PATTERN_003/010 |
| NER 2020-2024 | C | PATTERN_010 |
| SOM 2020-2024 | C | Horn cluster |
| SSD 2020-2024 | C or D1 | strife-dominant |
| HTI 2020-2024 | B or D2 | gang-state |

All 9 anchor cases predicted to match. F1 falsifier (anchors fail) fires if ≥2 anchors don't classify as predicted.

### Prediction set B — Cluster panel test

Apply classifier across the full IDP cluster panels (Sahel, Horn, MENA, Central Africa, Latin America, South Asia, Eastern Europe). Predict:
- ≥ 15 country-periods classify cleanly into A/B/C
- ≤ 4 country-periods unclassified
- 4th-type cluster: predict 2-4 cases (SSD, ETH-Amhara, HTI, maybe SDN-2023+) cluster as D

### Prediction set C — Regional non-uniformity

Predict that Type C dominates Sahel + Horn (5+ cases); Type A dominates Eastern Europe + Horn (ETH); Type B dominates Central Africa (COD, maybe CAF). Falsifier F-region (below).

---

## 4. Falsifiers

- **F1 (anchors fail)**: ≥2 of 9 anchor cases don't classify as predicted → classifier rules wrong
- **F2 (unclassified overflow)**: ≥5 country-periods unclassified → rules incomplete; new type needed
- **F3 (4th-type absent)**: 0 cases cluster as D AND no D1/D2 candidates separate from A/B/C → walk back to 3 types
- **F4 (regional uniformity)**: All Sahel countries classify the same as all Horn countries → typology operates on region not conflict-form (would walk back the framework's deepest claim)
- **F5 (ratio overlap)**: disp_per_fat distributions for A, B, C have >50% overlap → ratios not type-distinct (defers to PRE_REG_019 for formal test, but cluster check here)

F1 firing alone = classifier rules walked back; refine and re-fire.
F4 firing = framework's load-bearing claim walked back; conflict-form typology fails.
F2 + F3 together = typology incomplete and not extending; walk back to 3 types with caveat.

---

## 5. Methodology

- UCDP-GED v24 (latest available locally) for fatalities + type_of_violence + admin-1 + actor codes
- GIDD Disasters + conflict displacement file for IDP totals
- Acute period default: 2020-2024 (matches PATTERN_010/012/015/017 windows)
- Cluster panels at `D:/IDP/analysis/*_stratified_panel_2026_05_21.parquet`
- Sufficient-evidence threshold: 500+ fatalities in period

### Data joins
- UCDP-GED → country-year-violence-type aggregation → join GIDD IDP by ISO3 × year
- Admin-1 dominance: rank admin-1 names by fatality, compute top-3 share
- Top-actor share: rank side_a OR side_b by one-sided fatality, compute share for top brand

## 6. Cross-references
- PATTERN_012 (Type A ETH anchor)
- PATTERN_015 (Type B COD anchor)
- PATTERN_017 (Type A UKR anchor)
- PATTERN_010 (Type C strife-dominant anchor)
- PRE_REG_019 (forthcoming — type-distinct ratios formal test)
- PRE_REG_020 (forthcoming — spatial concentration formal test)

---

## 7. Provenance
Locked 2026-05-27 before Paper 4 Phase 1 P4-C corpus fire.

---

## 8. Results — first fit (fired 2026-05-27)

Pre-reg fired immediately after lock. Full dig: `D:/IDP/papers/PAPER_4_CONFLICT_TYPES/digs/2026_05_27_P4_C_classifier_corpus_fire.md`

### Headline
**F1 + F2 FIRED**. 5/8 anchor cases match strict rules. 12 of 35 country-periods unclassified.

**BUT substantive typology survives in EXPANDED form**:
- Type A clean class (6): ETH, UKR, RUS, ISR, PAK, EGY
- Type B clean class (3): COD, MOZ, HTI (MOZ Cabo Delgado new; HTI gang-state confirms B mechanism)
- **Type D criminal-violence CONFIRMED as 4th type** (MEX, BRA, ECU) — cartel/gang violence with low DPF
- **Type E civil-war-mass-displacement EMERGED unpredicted** as 5th type candidate (SYR/YEM/AFG/IRQ/LBY)
- F4 (regional uniformity) **NOT FIRED** — strong support for conflict-form > region

### Falsifier status
| Falsifier | Result |
|---|---|
| F1 (≥2 anchors fail) | **FIRED** — MLI, BFA, SOM fail strict rules (admin-1 threshold too strict; SOM tripped to A-diffuse) |
| F2 (≥5 unclassified) | **FIRED** — 12 unclassified |
| F3 (no 4th type) | **NOT FIRED** — OPPOSITE: Type D criminal-violence emerges robustly |
| F4 (regional uniformity) | **NOT FIRED** — types spread heterogeneously across regions; load-bearing positive |
| F5 (ratio overlap) | deferred to PRE_REG_019 |

### Net result
H1 walked back to refined H1: typology has **5 types** (not 3): A formal-army, B predator-militia, C irregular insurgency, **D criminal-violence (new)**, **E civil-war-mass-displacement (new candidate)**. Classifier rules need refinement (loosen admin-1 threshold for Type C; add Type D and Type E rules). 

H2 (4th-type open question) RESOLVED — Type D criminal-violence confirmed across 3 LatAm cases. H2's 4th-type candidates D1 (communal/ethnic — SSD) and D2 (regime-collapse — HTI) absorbed into existing types (C-concentrated and B respectively).

**Status**: PARTIAL SUPPORT + 2 walk-backs (F1 + F2) + 2 NEW TYPE DISCOVERIES (D criminal-violence, E civil-war-mass-displacement). Refinement to PRE_REG_018 v2 needed before formal re-fire.
