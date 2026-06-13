# Pre-Registration 018 v3 — Conflict-Type Classifier (Refined 5-type with sub-types)

**ID:** PRE_REG_018 v3
**Locked:** 2026-05-27 (after v2 fired + 5 refinement candidates surfaced)
**Substrate:** PRE_REG_018 v2 SUPPORTED (16/18 anchors) + PRE_REG_021 within-country test SUPPORTED + 5 refinement candidates from v2 + Phase 3 digs
**Status:** LOCKED — refined rules. First fit fires on same UCDP-GED v25 + GIDD data.

**Honesty note**: v3 refinements derived from v2 + Phase 3 first-fit. Re-firing confirms classifier shape; independent validation will come from forward data (2025-2027 UCDP releases) + held-out countries below the current 500-fat threshold.

---

## 1. Hypothesis (refined v3)

**H1 (5-type framework with refined boundaries):** With v3 rule refinements, the classifier achieves:
- ≥17 of 18 anchor + new-type matches (improvement from v2's 16/18)
- ≤2 unclassified (improvement from v2's 1, with TUR still likely unclassified due to IDP=0)
- Type E narrowed to TRUE civil-war (organized opposition required); state-counterinsurgency-against-irregular cases route to Type C

**H2 (Type C sub-typing):** Type C splits into C1 (low-DPF irregular: ≤300) and C2 (high-DPF irregular: >300) reflecting heterogeneity discovered in PRE_REG_019 H3 walk-back.

**H3 (Type A short-duration accommodation):** AZE Karabakh wars classify Type A under refined rule.

---

## 2. Classifier rules v3 (refined)

For each country-conflict-period (acute 2020-2024 default):

### Type A — Formal-army war (REFINED with short-duration sub-rule)
ANY of:
- **A-strict (long-duration high-intensity)**: `state_share ≥ 0.70` AND `strife_share ≤ 0.10` AND `disp_per_fat ≤ 150` AND (`admin1_top3_share ≥ 0.60` OR `total_fat ≥ 100,000`)
- **A-short (short-duration interstate)**: `state_share ≥ 0.85` AND `strife_share = 0` AND `disp_per_fat ≤ 200` AND `total_fat ≥ 1,000` (catches Karabakh-type mid-scale interstate wars)

### Type B — Predator-militia (UNCHANGED)
ALL: `one_sided_share ≥ 0.40` AND `disp_per_fat ≥ 250` AND `admin1_top3_share ≥ 0.60` AND `top_actor_share ≥ 0.30`

### Type C — Irregular insurgency (REFINED with sub-typing)
ANY of:
- **C1 (low-DPF irregular, mid-DPF)**: `strife_share ≥ 0.20` AND `admin1_top3_share ≤ 0.85` AND `disp_per_fat ≤ 400`
- **C2 (high-DPF irregular)**: `strife_share ≥ 0.20` AND `disp_per_fat > 400`
- **C-mixed (multi-actor)**: `0.20 ≤ state_share ≤ 0.70` AND `one_sided_share ≥ 0.15` AND `admin1_top3_share ≤ 0.85`

### Type D — Criminal-violence (UNCHANGED)
ALL: `strife_share ≥ 0.80` AND `disp_per_fat ≤ 100` AND `state_share ≤ 0.10`

### Type E — Civil-war-mass-displacement (NARROWED)
ALL of:
- `state_share ≥ 0.55`
- `disp_per_fat ≥ 300`
- `conflict_idp ≥ 500,000`
- **NEW**: `(strife_share + one_sided_share) ≥ 0.20` — requires organized non-state opposition (distinguishes true civil-war from pure state-counterinsurgency)

### Tie-breaking
Apply in order: A > B > D > E > C2 > C1 > C-mixed

### UNCLASSIFIED
If no rule matches AND `total_fat ≥ 500`.

---

## 3. Pre-locked predictions

### Prediction set A — Improved anchor matches
| ISO | v2 result | v3 predicted | Change |
|---|---|---|---|
| ETH | A | A | stable |
| UKR | A | A | stable |
| RUS | A | A | stable |
| ISR | A | A | stable |
| PAK | A | A | stable |
| EGY | A | A | stable |
| COD | B | B | stable |
| MOZ | B | B | stable |
| HTI | B | B | stable |
| MEX | D | D | stable |
| BRA | D | D | stable |
| ECU | D | D | stable |
| MLI | C | **C-mixed** | stable type |
| **BFA** | E | **C-mixed** | **FIX — state 66.3% + one-sided 30.7% = mixed; no organized opposition for E** |
| **SOM** | E | **C-mixed** | **FIX — state 93.5% + one-sided 2.7% + strife 3.8% = pure state counterinsurgency; non-state share only 6.5% < 20% E new threshold** |
| SYR | E | E (organized rebels) | stable |
| YEM | E | E (Houthi + others) | stable |
| AFG | E | E (Taliban + ISKP) | stable |

**Match prediction**: 18/18 anchors should match v3 → H1 SUPPORTED.

### Prediction set B — Type E narrowing impact
- BFA, SOM, PHL, IND, KEN should reclassify FROM E TO C (state counterinsurgency without organized rebel opposition)
- True civil wars (SYR, YEM, AFG, LBY, MMR, IRQ, CAF, AZE, NGA, SDN, CMR, TCD) stay E

**Predicted Type E count after v3**: 8-12 (down from v2's 17)
**Predicted Type C count after v3**: 9-13 (up from v2's 5)

### Prediction set C — AZE Karabakh fix
- AZE 2020 (44-day war): A-short under new rule (state 100%, strife 0%, DPF 96, fat 7,636) — passes all 4 criteria
- AZE 2023 offensive: borderline (state 100% but DPF 1489 fails ≤200) — likely still UNCLASSIFIED or boundary
- AZE 1992-1994: data-gap, expect UNCLASSIFIED

### Prediction set D — Type C sub-typing visible
- MLI (DPF 165): C1 ✓
- LBN (DPF 238): C1 ✓
- SSD (DPF 1930): C2 ✓ (high-DPF irregular)
- COL (DPF 5000+): C2 ✓
- IRN (DPF 0): boundary, possibly C1 via C-mixed rule

**Predicted C-sub split**: ~3 C1 + ~2 C2.

---

## 4. Falsifiers

- **F1 v3**: <17 of 18 anchor matches → v3 refinements ineffective
- **F2 v3 (E narrowing fails)**: BFA OR SOM still classifies E after v3 → narrowing rule wrong
- **F3 v3 (A-short fails)**: AZE 2020 still UNCLASSIFIED → short-duration A rule wrong
- **F4 v3 (C sub-typing collapses)**: Either C1 or C2 has 0 members → sub-typing not real
- **F5 v3 (over-correction)**: ≥5 unclassified after v3 → rules too restrictive

F1 OR (F2 AND F3) firing = v3 walked back.

---

## 5. Methodology
Same as v1/v2; re-fire identical script with v3 rules.

## 6. Provenance
Locked 2026-05-27 after v2 + Phase 3 surfaced 5 refinement candidates.

## 7. Cross-references
- PRE_REG_018 v1 + v2 (predecessors)
- PRE_REG_019 (DPF H3 walk-back → motivates C sub-typing)
- PRE_REG_020 (spatial signature, unchanged in v3)
- PRE_REG_021 (within-country test surfaced AZE failure mode → A-short rule)
- PATTERN_031/032/033 (anchors)

---

## 8. Results — first fit (fired 2026-05-27)

### v3 WALKED BACK. Anchor matches: 14/18 (DOWN from v2's 16/18).

**Falsifier status**:
| Falsifier | Result |
|---|---|
| F1 v3 (<17 anchors) | **FIRED** (14 < 17) |
| F2 v3 (BFA/SOM still E) | **FIRED** (BFA still E; SOM UNCLASSIFIED — not the predicted C) |
| F3 v3 (AZE 2020 still UNCLASS) | informational |
| F4 v3 (C sub-typing) | NOT FIRED (C1=1, C2=2) |
| F5 v3 (≥5 unclassified) | **FIRED** (9 unclassified — over-correction) |

### Root cause of v3 walk-back

The Type E narrowing rule `(strife_share + one_sided_share) ≥ 0.20` was **wrong-directional**. AFG (3% non-state), YEM (2.9%), IRQ (6.7%), LBY (4.9%), SOM (6.5%) all have organized opposition BUT their UCDP fatalities are dominated by state-side battle deaths. **Non-state-share-of-fatalities does NOT capture "presence of organized opposition"**.

True organized opposition in these cases (Taliban, Houthis, IS, LNA, Al-Shabaab) is reflected in dyad structure / side_b actors / UCDP conflict_type — NOT in the fatality-share allocation. The refinement targeted the wrong feature.

### A-short rule limitation
AZE 2020-2024 acute window aggregates 2020 + 2023 wars across 5 years → 8,262 cumulative fatalities, DPF 407. A-short threshold `dpf ≤ 200` failed. The rule needs **temporal phase decomposition** (PRE_REG_021 style) to capture short-duration interstate wars, not aggregate-window classification.

### v3 walked back; reverting to v2 as the SUPPORTED classifier

**v2 (16/18 anchor matches) remains the strong-supported framework** for Paper 4. v3 over-corrected.

### Honest finding logged
The pre-reg discipline caught the misguided refinement before publication. v3 is logged as an attempted refinement that walked back, not as classifier improvement. v2 is the locked Paper 4 classifier.

**Refinement candidates that remain OPEN for future work**:
1. **Better "organized opposition" feature** — UCDP conflict_type column or side_b actor presence (not fatality-share)
2. **Temporal phase decomposition built into classifier** — instead of aggregate 2020-2024, classify per phase (PRE_REG_021 framework)
3. **Type C sub-typing IS supported** (C1=1, C2=2 across MLI/SSD/COL) — keep this finding even though v3 overall walked back

**Status**: WALKED BACK. Use v2 as Paper 4's classifier. v3 informs future-work direction.
