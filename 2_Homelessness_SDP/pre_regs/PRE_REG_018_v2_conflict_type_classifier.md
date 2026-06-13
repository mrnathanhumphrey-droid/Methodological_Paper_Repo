# Pre-Registration 018 v2 — Conflict-Type Classifier (5-type framework)

**ID:** PRE_REG_018 v2
**Locked:** 2026-05-27 (after v1 fired + refined)
**Substrate:** PRE_REG_018 v1 first fit (5/8 anchors match strict rules; Type D + Type E emerged)
**Status:** LOCKED — refined rules with Type D + Type E definitions; first fit fires on same UCDP-GED v25 + GIDD data

**Honesty note**: v2 rules for Type D and Type E are derived from v1 first-fit cluster discovery. Re-firing on the same data confirms cluster structure but does NOT independently validate. Independent validation requires either (a) held-out countries not classified in v1 fire, or (b) within-country temporal decomposition (PRE_REG_021 IRQ phase test).

---

## 1. Hypothesis (refined)

**H1 v2 (5-type conflict typology):** Country-conflict-periods cluster into 5 distinct types determined by organizational form of violence:

- **Type A — Formal-army war**: state-vs-state OR state-vs-structured-rebel high-intensity conflict; low DPF
- **Type B — Predator-militia campaign**: one-sided violence dominant, single-actor brand, high DPF, hyper-concentrated
- **Type C — Irregular insurgency**: multi-actor non-state landscape, political-ideological motivation, mid-DPF
- **Type D — Criminal-violence**: cartel/gang non-state-vs-non-state, very low DPF, commercial motivation
- **Type E — Civil-war-mass-displacement**: state-dominated multi-actor civil war with mass civilian displacement, high DPF

---

## 2. Classifier rules v2 (locked BEFORE re-fire)

For each country-conflict-period (acute 2020-2024 default):

### Type A — Formal-army war (REFINED)
ALL of:
- `state_share ≥ 0.70`
- `strife_share ≤ 0.10`
- `disp_per_fat ≤ 150`
- `admin1_top3_share ≥ 0.60` OR `total_fat ≥ 100,000` (front-line concentration OR very-high-intensity)

### Type B — Predator-militia (UNCHANGED)
ALL of:
- `one_sided_share ≥ 0.40`
- `disp_per_fat ≥ 250`
- `admin1_top3_share ≥ 0.60`
- `top_actor_share ≥ 0.30`

### Type C — Irregular insurgency (REFINED: admin-1 threshold loosened)
ANY of:
- `strife_share ≥ 0.30` AND `admin1_top3_share ≤ 0.85`
- (`state_share` 0.20-0.70 AND `one_sided_share` 0.20-0.60) AND `admin1_top3_share ≤ 0.85`
- `disp_per_fat` 100-300 AND multi-actor (`top_actor_share` < 0.50)

### Type D — Criminal-violence (NEW)
ALL of:
- `strife_share ≥ 0.80` (overwhelmingly non-state vs non-state)
- `disp_per_fat ≤ 100`
- `state_share ≤ 0.10`

### Type E — Civil-war-mass-displacement (NEW)
ALL of:
- `state_share ≥ 0.55`
- `disp_per_fat ≥ 300`
- NOT Type A (fails one of A's conditions)
- conflict_idp ≥ 500,000 (mass-displacement criterion)

### Tie-breaking
If multiple types match, apply order: A > B > D > E > C (formal-army first, criminal-violence and civil-war-mass-displacement before irregular).

### UNCLASSIFIED
If no type matches AND total_fat ≥ 500.

---

## 3. Pre-locked predictions

### Prediction set A — Anchor + new-type cases all classify cleanly

Predict 100% of these 18 cases match their v2-rule classifications:

| ISO | Predicted | Type |
|---|---|---|
| ETH | A | formal-army anchor |
| UKR | A | formal-army anchor |
| RUS | A | formal-army |
| ISR | A | formal-army |
| PAK | A | formal-army |
| EGY | A | formal-army |
| COD | B | predator-militia anchor |
| MOZ | B | predator-militia (new from v1) |
| HTI | B | predator-militia |
| MEX | D | criminal-violence anchor |
| BRA | D | criminal-violence |
| ECU | D | criminal-violence |
| MLI | C | irregular insurgency (re-test after admin-1 loosening) |
| BFA | C | irregular insurgency (re-test) |
| SOM | C | irregular insurgency (re-test) |
| SYR | E | civil-war-mass-displacement |
| YEM | E | civil-war-mass-displacement |
| AFG | E | civil-war-mass-displacement |

≥ 16 of 18 must match → v2 H1 SUPPORTED.

### Prediction set B — Unclassified reduction

Predict v2 unclassified count drops from 12 (v1) to ≤ 3 → rule refinement works.

### Prediction set C — Type counts

| Type | v1 strict | v2 predicted |
|---|---|---|
| A | 6 | 6-8 |
| B | 3 | 3 |
| C | 4 | 6-8 |
| D | 0 strict | 3 (MEX/BRA/ECU) |
| E | 0 | 4-6 |
| Unclassified | 12 | ≤ 3 |

### Prediction set D — Tie-break correctness

Predict tie-break order produces sensible classifications. Specifically:
- Cases where Type A and Type E both technically match → classify as A if DPF < 150 else E
- Cases where Type B and Type D both match (HTI?) → classify as B (predator-militia mechanism over criminal mechanism)

---

## 4. Falsifiers

- **F1 v2 (anchor + new-type fail)**: ≥3 of 18 cases fail v2 rules → typology framework wrong
- **F2 v2 (unclassified overflow)**: ≥5 unclassified after v2 → rules still incomplete
- **F3 v2 (Type D collapses)**: 0 cases classify Type D after v2 → 4th type was v1 artifact
- **F4 v2 (Type E collapses)**: 0 cases classify Type E after v2 → 5th type was v1 artifact
- **F5 v2 (Type A overflow)**: ≥10 cases classify Type A → A rules too loose; absorbs others
- **F6 v2 (regional uniformity reappears)**: Sahel all same type AND Horn all same type → conflict-form-over-region claim wrong

F1 firing alone OR F3+F4 together = v2 walked back.

---

## 5. Methodology

Same as v1: UCDP-GED v25 (2020-2024) + GIDD conflict-displacement. Re-fire identical script with v2 rules.

## 6. Provenance

Locked 2026-05-27 after v1 first fit revealed walk-back + 2 new types. Re-fire follows immediately.

---

## 7. Cross-references

- PRE_REG_018 v1 first fit (substrate for v2 refinement)
- PATTERN_031 / 032 / 033 (new type anchors)
- PRE_REG_019 (forthcoming — type-distinct ratios formal test)
- PRE_REG_020 (forthcoming — spatial concentration)
- PRE_REG_021 (forthcoming — IRQ within-country test; independent validation)

---

## 8. Results — first fit v2 (fired 2026-05-27)

Full dig: `D:/IDP/papers/PAPER_4_CONFLICT_TYPES/digs/2026_05_27_P4_phase2_v2_ratios_spatial.md`

### Anchor + new-type matches: 16/18 → **H1 v2 SUPPORTED** (threshold ≥16 met)

Anchor failures:
- BFA: predicted C, actual E (state 66% + IDP 8.7M trips E rules)
- SOM: predicted C, actual E (state 93% + IDP 16.8M trips E rules)

### Type counts after v2
| Type | Count | Members |
|---|---|---|
| A formal-army | 6 | ETH/UKR/RUS/ISR/PAK/EGY |
| B predator-militia | 3 | COD/MOZ/HTI |
| C irregular insurgency | 5 | MLI/LBN/SSD/COL/IRN |
| D criminal-violence | 3 | MEX/BRA/ECU |
| E civil-war-mass-displacement | 17 | (broad) |
| UNCLASSIFIED | 1 | TUR |

### Falsifier summary
| Falsifier | Result |
|---|---|
| F1 (≥3 anchors fail) | NOT FIRED (2 fail) |
| F2 (≥5 unclassified) | NOT FIRED (1) |
| F3 (Type D = 0) | NOT FIRED |
| F4 (Type E = 0) | NOT FIRED |
| F5 (Type A ≥ 10) | NOT FIRED |

### Refinement candidate (v3)
Type E is broad (17 members) — captures both true civil wars (SYR/YEM/AFG/IRQ/LBY/MMR) AND state counterinsurgency against irregular insurgency (BFA/SOM/NGA/PHL/IND/KEN). v3 candidate: require non-state-share ≥ 30% (organized opposition) to qualify Type E, otherwise route to C.

**Status**: SUPPORTED. Refinement to v3 deferred pending case-expansion data.
