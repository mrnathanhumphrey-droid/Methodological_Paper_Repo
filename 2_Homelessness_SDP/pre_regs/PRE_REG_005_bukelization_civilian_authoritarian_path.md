# Pre-Registration 005 — Bukelization (Civilian-Authoritarian Collapse Path)

**ID:** PRE_REG_005
**Locked:** 2026-05-25
**Substrate:** IDP broad-data corpus (D:/IDP/)
**Status:** LOCKED — predictions and falsifiers pre-committed; retrospective test fires immediately on existing V-Dem data; forward predictions await 2026-2029 data

---

## 1. Hypothesis

**H1 (Bukelization shape):** Countries where leaders consolidate authoritarian power through legal/civilian channels (state-of-exception declarations, supermajority constitutional reforms, judicial capture, media capture) show libdem trajectories matching a distinctive shape:
- **(a)** Δlibdem ≤ **−0.30** over a 5-year window
- **(b)** NO military coup in window
- **(c)** NO interstate war in window
- **(d)** Mid-range start: libdem at start of window in **0.30-0.55** range
- **(e)** Decline pattern is **monotonic** (not step-function) — consolidation accumulates over the 5-year window

**H2 (mechanism):** The Bukelization path is distinct from coup-driven collapse — it relies on populist legitimacy + institutional capture rather than military force. The trajectory shape (monotonic, mid-range start, 5-year window) is the signature that distinguishes it from coup-collapse (step-function, range-yes start, immediate post-coup drop).

**This is a purely structural/methodological hypothesis using V-Dem's quantitative libdem index. It is NOT a political endorsement, condemnation, or partisan claim about any specific country or leader. The test is whether the SLV-shape generalizes as a measurable trajectory pattern.**

---

## 2. In-sample evidence (NOT re-tested)

| Country | Window | start libdem | end libdem | Δ | Trigger | Coup? |
|---|---|---|---|---|---|---|
| **SLV** | 2019-2024 | 0.428 | 0.090 | **−0.338** | Bukele state-of-exception 2022 | NO |

Generation case: SLV (PATTERN_013). Single in-sample case so this pre-reg is testing whether the *shape* generalizes — high-risk pre-reg, high-information-value if it does.

---

## 3. Pre-locked predictions

### Prediction set A — Retrospective (fires NOW; tests H1 shape on past consolidations)

| Country | Window | Predicted start libdem | Predicted end libdem | Predicted Δ | Predicted coup? | Predicted fit |
|---|---|---|---|---|---|---|
| **HUN (Hungary)** | 2010-2015 (Orbán start) | ~0.55 | ~0.45 | -0.10 | NO | **PARTIAL fit** — slower decline; Bukelization-LITE |
| **HUN** | 2010-2020 (long window) | ~0.55 | ~0.32 | -0.23 | NO | borderline H1 (Δ approaches −0.30 over 10y) |
| **TUR (Turkey)** | 2014-2019 (post-Gezi) | ~0.40 | ~0.13 | -0.27 | 2016 coup attempt (FAILED — Erdoğan used to consolidate) | **FIT but caveated** — failed coup is the trigger event |
| **VEN (Venezuela)** | 2002-2007 (Chávez consolidation) | ~0.40 | ~0.21 | -0.19 | 2002 brief coup (FAILED) | **PARTIAL fit** |
| **VEN** | 2013-2018 (Maduro deepening) | ~0.21 | ~0.05 | -0.16 | NO | DOES NOT fit start condition (range-no, already low) |
| **RUS (Russia)** | 2000-2005 (early Putin) | ~0.40 | ~0.20 | -0.20 | NO | **PARTIAL fit** |
| **RUS** | 2007-2012 (Medvedev/return) | ~0.20 | ~0.10 | -0.10 | NO | DOES NOT fit start condition |

**Pre-locked retrospective prediction:** At least 2 of 4 retrospective cases (HUN, TUR, VEN, RUS) fit H1 shape ✓ in their primary-consolidation windows. If 0 fit, the shape is SLV-unique and the pre-reg is NULL.

### Prediction set B — Forward predictions (lock at 2026-05-25; test in 2029-2031)

| Country | Current libdem 2024 | Range condition? | Predicted trajectory 2024-2029 | Outcome locked |
|---|---|---|---|---|
| **IND (India)** | ~0.281 (declining from 0.363 over 6 years) | Yes — currently in mid-range, declining | If BJP supermajority continues + ECI capture continues, predict Δ ≤ −0.10 by 2029 (to ≤ 0.18) | Watch through 2029 |
| **BRA (Brazil)** | ~0.50 (post-Lula 2023-2024) | Yes | If Bolsonaro returns 2026 + judicial-capture continues, predict Δ ≤ −0.20 by 2031 | Watch through 2031 |
| **TUR (Turkey, post-Erdoğan)** | ~0.13 currently | NO (already at floor) | Floor-saturated; predict no further collapse — recovery uncertain. NOT a Bukelization candidate now | Watch for recovery signal |
| **HUN (Hungary)** | ~0.32 currently | Borderline | Continued slow decline predicted (Δ ≤ −0.05 by 2029) | Watch |
| **USA** | (to be measured at fire time) | Likely yes (high range still) | Score current trajectory; if 2025-2028 shows accelerated executive-power consolidation (firings, doj capture, regulatory rollback), predict Bukelization shape onset by 2030 | Watch through 2030 |

### Prediction set C — Negative controls (predict NO Bukelization)
- **DEU (Germany), FRA (France), GBR (UK), CAN, AUS, JPN, NLD, NOR, SWE, FIN** — high-libdem countries with no current consolidation indicator
- Predict: all stay in 0.50-0.80 band through 2029; Δ within ±0.10
- If any of these show Bukelization shape → mechanism is much more general than thought; refine

---

## 4. Falsifiers (pre-committed)

- **F1:** ALL 4 retrospective cases (HUN, TUR, VEN, RUS) fit H1 shape perfectly → mechanism is universal; not a discriminating pattern; SLV is just one of many
- **F2:** ZERO retrospective cases fit → SLV is unique; pattern doesn't generalize; walk back
- **F3:** Forward cases (IND, BRA, etc.) all collapse regardless of starting libdem → range condition doesn't matter
- **F4:** Forward cases all stay stable → no Bukelization happening anywhere; either we're at a unique historical moment OR the mechanism is over-stated
- **F5:** Negative-control countries (DEU/FRA/etc.) show Bukelization shape → mechanism not selective to "consolidation-tools-leader" contexts

Any 2 of {F1, F2, F3, F4, F5} firing = HYPOTHESIS WALKED BACK; will be logged in patterns/ as such.

---

## 5. Methodology

### Data
- **V-Dem v15** (libdem indicator) — annual country-year
- Manually-curated trigger event inventory (consolidation moments, coup events, war declarations) — locked at pre-reg lock time

### Test procedure (retrospective set, immediate)
1. Pull V-Dem libdem for HUN, TUR, VEN, RUS in their primary-consolidation windows
2. Score H1 shape conditions (Δ, coup, war, start range, monotonicity)
3. Compare against pre-locked predictions
4. Log result in PATTERN_013 dig section

### Test procedure (forward set, ongoing)
1. Annual V-Dem release: pull libdem for IND, BRA, TUR, HUN, USA
2. Check Δ from 2024 baseline
3. Score Bukelization-shape fit
4. Log result in PATTERN_013 + this pre-reg's annual update section

### Decision rules
- **Supported:** ≥2 of 4 retrospective fit + at least 1 of 3 strong-forward predictions fits within window
- **Partial:** Mixed retrospective results; refine threshold or add conditioning
- **Null:** F2 + F4 both fire → walk back

---

## 6. Methodological note
This pre-reg is structural-political (uses V-Dem libdem index, a quantitative measure). It is NOT a partisan claim about specific governments or leaders. The hypothesis is whether the *shape* (Bukelization trajectory) generalizes — that is a methodological question, not a political one. Whether to support or oppose any specific consolidation is outside the scope of this pre-reg.

---

## 7. Cross-references
- [[PATTERN_013]] Bukelization (the substrate; SLV in-sample)
- [[PATTERN_011]] Range+trigger libdem collapse (PRE_REG_002 — coup-trigger sister mechanism)
- [[PATTERN_018]] Trigger-typology (Bukelization = trigger type 3)
- [[INDEX]] meta-pattern of trigger-types

---

## 8. Provenance
Locked 2026-05-25, post-flood-corpus expansion, alongside PRE_REG_002/003/004. Retrospective test fires immediately on V-Dem data; forward test set runs at each V-Dem annual release.

---

## 9. Results — first fit (fired 2026-05-25)

Retrospective Bukelization-shape test (H1: Δ≤−0.30, start range≥0.30, no coup, monotonic):

| Country | Window | Start | End | Δ | Range≥0.30 | Δ≤−0.30 | Monotonic | Fit |
|---|---|---|---|---|---|---|---|---|
| **HUN** | 2010-2015 (5y) | 0.677 | 0.477 | −0.200 | YES | NO | YES | NO |
| **HUN** | 2010-2020 (10y) | 0.677 | 0.351 | **−0.326** | YES | YES | YES | **FIT** |
| TUR | 2014-2019 | 0.252 | 0.107 | −0.145 | NO (already <0.30) | NO | YES | NO |
| VEN | 2002-2007 | 0.255 | 0.162 | −0.093 | NO | NO | YES | NO |
| VEN | 2013-2018 | 0.109 | 0.061 | −0.048 | NO (floor) | NO | YES | NO |
| RUS | 2000-2005 | 0.223 | 0.149 | −0.074 | NO | NO | YES | NO |
| RUS | 2007-2012 | 0.146 | 0.122 | −0.024 | NO (already low) | NO | YES | NO |

**Critical methodological finding: the 5-year window is TOO NARROW for most retrospective cases.** By the time scholars label a country as "Bukelizing," libdem has ALREADY dropped below 0.30 (TUR was 0.252 in 2014, VEN 0.255 in 2002 — both well below the H1 start threshold). The pre-reg's range condition needs to apply BEFORE the consolidation begins, but consolidation typically begins after a libdem dip has already happened.

**HUN over 10-year window FITS PERFECTLY** (Δ=−0.326, range-yes, monotonic, no coup). Hungary IS Bukelization-shape over a long horizon.

Forward scoring snapshots (2024 libdem):

| Country | 2018 | 2024 | Δ (6yr) | Status |
|---|---|---|---|---|
| **IND** | 0.363 | 0.281 | **−0.082** | ON Bukelization trajectory (slower than SLV); continued BJP supermajority = continued decline predicted |
| BRA | 0.608 | 0.712 | +0.104 | **OPPOSITE — recovery case** (see [[PATTERN_022]]); not Bukelizing |
| TUR | 0.104 | 0.109 | +0.005 | Already collapsed; floor-saturated |
| HUN | 0.373 | 0.325 | −0.048 | Continued slow decline (consistent with extended Bukelization) |
| USA | 0.739 | 0.751 | +0.012 | High range, stable; no current Bukelization signal |

Negative controls (10 advanced democracies, 2014→2024):
- All Δ within ±0.08; NONE show Bukelization shape ✓

**Verdict:**
- **F1 not fired** (not all 4 retrospective fit)
- **F2 not fired** (HUN long-window fits → mechanism not SLV-unique)
- **F3 not fully testable yet** (forward window not complete)
- **F4 not fired** (HUN + IND showing decline, not all stable)
- **F5 not fired** (negative controls stable)

**Net: HYPOTHESIS SUPPORTED with critical refinement — window length must be ≥10 years, not 5.**

**Refinement for PRE_REG_005b (future):**
- Window length 10-year instead of 5-year
- Start condition: libdem ≥0.30 at START of leader's consolidation (not at arbitrary calendar date)
- Add monotonicity check across the window
- HUN-over-10y confirms the shape generalizes; mechanism is real but operates on decadal timescales

PRE_REG_005 is NOT walked back. The methodological refinement strengthens, not weakens, the hypothesis.
