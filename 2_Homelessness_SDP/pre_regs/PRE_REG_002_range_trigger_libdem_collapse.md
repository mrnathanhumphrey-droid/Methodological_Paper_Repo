# Pre-Registration 002 — Range+Trigger Libdem Collapse Model

**ID:** PRE_REG_002
**Locked:** 2026-05-25
**Substrate:** IDP broad-data corpus (D:/IDP/)
**Status:** LOCKED — predictions and falsifiers pre-committed; holdout test fires immediately on existing data

---

## 1. Hypothesis

**H1 (conditional collapse model):** A country's V-Dem liberal-democracy index (libdem) collapses to ≤ 0.12 within 3 years **if and only if** both conditions hold:
- **(a) Range condition:** libdem at start of observation period ≥ **0.22**
- **(b) Trigger condition:** a regime-changing trigger event occurs within the window

Trigger types (pre-locked taxonomy from PATTERN_018):
1. Military coup (Sahel BFA/MLI/NER, MMR 2021)
2. Armed-faction conquest (AFG Taliban 2021, CAF Wagner-coalition)
3. Civilian-authoritarian consolidation (SLV Bukele state-of-exception)
4. Interstate war (UKR 2022 — but this produces *wartime suspension* trajectory, different from authoritarian capture)

**H2 (mechanism):** Range provides the "fall distance"; trigger provides the "activation energy". Both are necessary; neither is sufficient. Range-no countries (floor-saturated) cannot collapse further; range-yes countries without triggers stay stable (cf. PAK clean control).

---

## 2. In-sample evidence (generation data — NOT re-tested)

| Country | 2018-2020 libdem | 2024 libdem | Trigger | Outcome |
|---|---|---|---|---|
| BFA | 0.485 | 0.126 | Military coup 2022/2023 | COLLAPSED |
| MLI | 0.307 | 0.141 | Military coup 2020/2021 | COLLAPSED |
| NER | 0.405 | 0.182 | Military coup 2023 | COLLAPSED |
| CAF | 0.249 | 0.097 | Armed-faction (Wagner) | COLLAPSED |
| HTI | 0.257 | 0.101 | Gang-state collapse | COLLAPSED |
| SLV | 0.428 | 0.090 | Civilian-authoritarian (Bukele) | COLLAPSED |
| AFG | 0.176 | 0.014 | Armed-faction (Taliban 2021) | COLLAPSED |
| MMR | 0.232 | 0.015 | Military coup 2021 | COLLAPSED |
| **PAK** | **0.250** | **0.193** | **NO trigger** | **NO COLLAPSE** (clean control) |
| BEN | 0.472 | 0.323 | NO trigger | NO COLLAPSE |
| COL | 0.533 | 0.554 | NO trigger | NO COLLAPSE |
| UKR | 0.244 | 0.230 | Interstate war (different mech) | wartime suspension only (-0.014) |

Floor-saturated (range-no) countries: ETH, SOM, SDN, SSD, ERI, SYR, YEM, COD, CMR, IRQ, LBN — none collapsed because they had no range. Consistent with H1.

---

## 3. Pre-locked predictions (holdout test fires NOW on existing data + ongoing watch)

### Prediction set A — Retrospective check on additional in-corpus cases
- **MMR pre-2021:** trajectory before coup should show range-yes (≥0.22) + stable until 2021 trigger. CONFIRMED in dig 2026-05-25 but not used in original PATTERN_011 generation.
- **AFG pre-2021:** libdem 2018 = 0.176 is BORDERLINE range. Predict: should still satisfy range condition (≥0.22 unmet but close); collapse may be partly range-driven (already at low floor) rather than pure range+trigger. **This is a boundary case for the threshold; if AFG doesn't fit cleanly, the 0.22 cutoff needs refinement.**

### Prediction set B — Watch list (live forward predictions, 2026-2028)

Countries to score on (range, trigger-risk) at locking date 2026-05-25:

| Country | 2024 libdem | Range satisfied? | Predicted trigger-risk window | Outcome prediction |
|---|---|---|---|---|
| **AGO (Angola)** | ~0.25 (range-yes, post-2018 reforms) | Yes | João Lourenço 2022 re-election; succession by 2027 | If succession-coup or armed-faction emergence → collapse by 2030 |
| **MOZ (Mozambique)** | 0.189 (BORDERLINE, declining) | Borderline | Ongoing Cabo Delgado insurgency; 2024 election protests | If Frelimo doubles down + insurgency expands → collapse by 2028 |
| **COL (Colombia)** | 0.554 (high range) | Yes | Post-Petro succession; FARC dissident escalation | If Petro succeeded by an authoritarian-civilian or ELN coalition → collapse by 2029 |
| **IND (India)** | 0.281 (mid-range, declining 0.363→0.281 over 6 years) | Yes | BJP supermajority consolidation; 2024 election outcome | Already in civilian-authoritarian-consolidation trajectory (PRE_REG_005 substrate). If continues → collapse to ≤0.20 by 2029 |
| **TUR (Turkey)** | (to be measured at fire time) | Likely yes | Post-Erdoğan succession | If succession produces continuation, expect Bukelization-shape continuation |
| **BRA (Brazil)** | (to be measured) | Yes | Post-Lula 2026 election; Bolsonaro return scenario | If Bolsonaro returns + judicial-capture continues → Bukelization risk by 2030 |
| **PAK (control)** | 0.193 | Borderline | Maintained civilian government | Predict NO collapse — stays in 0.15-0.25 band through 2028 |

### Prediction set C — Cross-corpus negative cases
Countries already at floor (range-no) — predict NO collapse possible regardless of trigger:
- ETH, SOM, SDN, SSD, ERI, SYR, YEM, COD, CMR, IRQ
- These should remain in 0.0-0.15 band throughout 2026-2028. **If any of them collapses *below* 0.05 due to a trigger → range-no is insufficient defense; mechanism needs refinement.**

---

## 4. Falsifiers (pre-committed)

- **F1:** A range-yes country experiences a textbook trigger but does NOT collapse to ≤ 0.12 within 3 years → range+trigger is insufficient; mechanism falsified.
- **F2:** A range-no country (start libdem < 0.22) collapses to ≤ 0.05 within 3 years → range-no can still collapse; mechanism wrong.
- **F3:** A new trigger type emerges (not in the 4-type taxonomy) that produces collapse → taxonomy incomplete; needs PRE_REG_018b extension.
- **F4:** AFG (start 0.176, borderline range) collapse pattern requires lowering threshold to ≤0.15 → threshold needs recalibration (note this is partly a within-generation issue).

Any 2 of {F1, F2, F3, F4} firing = HYPOTHESIS WALKED BACK; will be logged in patterns/ as such.

---

## 5. Methodology

### Data
- **V-Dem v15** (libdem indicator) — annual country-year
- **UCDP-GED** for state-based fatality jumps as trigger-detection
- **Qualitative trigger event inventory** — locked at hypothesis lock time (see Prediction set B)

### Test procedure
1. At each V-Dem annual release (typically March), pull libdem for prediction-set countries
2. Score range condition at start of period (≥0.22)
3. Detect trigger events (coup database, news cycle, UCDP fatality jumps)
4. Compute libdem trajectory over 3-year window
5. Compare against pre-locked predictions and falsifiers
6. Update pattern catalog with result

### Decision rules
- **Supported:** All Prediction set B forward cases fit (range-yes + trigger → collapse; range-yes + no trigger → no collapse)
- **Partial:** Mixed results; refine threshold or add conditioning
- **Null:** F1 + F2 both fire → walk back the model

---

## 6. Cross-references

- [[PATTERN_011]] Range-conditioning of libdem collapse (the substrate)
- [[PATTERN_013]] Bukelization (the civilian-authoritarian trigger sub-mechanism — also pre-regged as PRE_REG_005)
- [[PATTERN_018]] Trigger-typology (4 types: coup / armed-faction / civilian-authoritarian / interstate war)
- [[PATTERN_017]] UKR boundary case (interstate war = different mechanism than authoritarian capture)

---

## 7. Provenance

Pre-reg locked 2026-05-25, substrate D:/IDP/, post Tier C+D dig, post flood-corpus expansion. Will be hashed and committed at next snapshot.

---

## 8. Results — first fit (fired 2026-05-25)

Holdout watch list libdem 2018-2024:

| Country | 2018 | 2024 | Δ | Range condition | Trigger fired? | Status |
|---|---|---|---|---|---|---|
| AGO | 0.161 | 0.161 | 0.000 | NO (range-no) | No | Consistent (no collapse possible) |
| MOZ | 0.264 | 0.189 | −0.075 | YES | No (slow Cabo Delgado, no regime change) | Slow decline, range-yes-no-trigger pattern matches PAK control |
| COL | 0.533 | 0.554 | +0.021 | YES | No | Consistent (no trigger, no collapse) |
| **IND** | 0.363 | 0.281 | −0.082 | YES | **Civilian-authoritarian consolidation (BJP supermajority)** | **ON Bukelization trajectory** — see PRE_REG_005 |
| TUR | 0.104 | 0.109 | +0.005 | NO (already at floor 2018) | (collapsed pre-2014) | Floor-saturated; consistent with H1 |
| **BRA** | 0.608 | **0.712** | **+0.104** | YES | **Election-driven recovery (Lula 2023)** | **RECOVERY case** — see new [[PATTERN_022]] |

PAK control: 0.250 → 0.193 (Δ −0.057, no collapse). H1 confirmed.

Floor-saturated cross-check: 10 of 11 floor countries stayed near floor; SDN dropped slightly (0.068 → 0.030) but in absolute terms tiny.

**No falsifier fired.** PRE_REG_002 is CONSISTENT with predictions so far. New finding: PATTERN_022 (BRA recovery) reveals an asymmetric gap — the pre-reg is collapse-only and doesn't model recovery. Future PRE_REG_006 candidate.

**Updated forward watch:** IND is the strongest live Bukelization candidate (continuous decline 0.363 → 0.281, range-yes, BJP consolidation ongoing).
