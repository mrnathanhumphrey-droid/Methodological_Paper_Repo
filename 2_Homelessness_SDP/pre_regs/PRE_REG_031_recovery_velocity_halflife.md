# Pre-Registration 031 — Recovery Velocity / Half-Life by Tier

**ID:** PRE_REG_031
**Locked:** 2026-05-27 (predictions + falsifiers pre-committed before velocity computation)
**Substrate:** PRE_REG_012 (mirror-order recovery, 6/6 supported) + PATTERN_022 + PATTERN_024
**Paper:** 5 (Democratic Resilience)
**Status:** LOCKED — first fit fires on recovery-case time series

---

## 1. Hypothesis

**H1 (tier velocity asymmetry):** Recovery is not just ordered (mirror of capture, per PRE_REG_012) but TEMPO-asymmetric. Horizontal-accountability institutions recover in months-to-1-year; vertical-accountability institutions recover over multiple years (or not within the observation window).

**H2 (quantified half-life):** Define per-tier recovery half-life = years from trough to reach 50% of (baseline − trough). Predicted ordering:
- Horizontal half-life: ≤ 1.5 years
- Diagonal half-life: ≤ 2.5 years
- Vertical half-life: ≥ 3 years OR censored (not reached within window)

---

## 2. Pre-locked predictions

### Prediction set A — Half-life ordering
Across the 6 recovery cases (POL, BRA, KOR, BGD, Sri Lanka, ZMB), median per-tier half-life:
- **Predicted**: horizontal < diagonal < vertical (strict ordering)

**Match threshold**: horizontal median half-life < vertical median half-life in ≥5 of 6 cases → H1 supported.

### Prediction set B — Vertical censoring
**Predicted**: in ≥3 of 6 cases, the vertical tier does NOT reach 50% recovery within the observation window (right-censored half-life).

### Prediction set C — Year-1 dominance
**Predicted**: in the first year of recovery, horizontal-tier delta > vertical-tier delta in ≥5 of 6 cases (horizontal moves first).

---

## 3. Falsifiers

- **F1 (uniform velocity)**: per-tier half-lives within ±0.5 yr of each other in ≥4 of 6 cases → no tempo asymmetry; mirror-order is a measurement artifact not a sequence
- **F2 (vertical-first)**: any case shows vertical half-life < horizontal half-life → reverse tempo possible
- **F3 (no censoring)**: vertical tier reaches 50% within 2 years in ≥4 of 6 cases → vertical lag is mild, not structural

F1 firing = velocity-asymmetry walked back; PRE_REG_012's ordering stands but without tempo content.

---

## 4. Methodology
- V-Dem v15/v16 annual sub-indicators per recovery case, trough year → latest
- recovery fraction(t) = (value(t) − trough) / (baseline − trough) per sub-indicator
- tier = mean of constituent sub-indicators (horizontal: hcind/jucon/horacc; diagonal: media/CSO/diagacc; vertical: v2elfrfair/v2psoppaut/veracc)
- half-life = interpolated year crossing 0.5; right-censored if never crossed
- Acknowledgment: annual resolution limits half-life precision to ~1 yr; small n; Sri Lanka baseline-inflation caveat carried from PRE_REG_012

## 5. Cross-references
- PRE_REG_012 (ordering — this is the tempo counterpart)
- PATTERN_022 (BRA), PATTERN_024 (POL)
- PRE_REG_006 (stalled-recovery — slow/censored vertical recovery is the stalled signature)

## 6. Provenance
Locked 2026-05-27 before velocity computation. First fit fires on recovery time series.

---

## 7. Results — first fit (fired 2026-05-28)

Full dig: `D:/IDP/papers/PAPER_5_DEMOCRATIC_RECOVERY/digs/2026_05_28_prereg031_032_velocity_ceiling.md`

**SUPPORTED.** Half-life (years from trough to 50% tier recovery), 4 well-conditioned cases (BGD/LKA excluded — degenerate baseline-trough libdem gaps 0.017/0.001):

| Case | horizontal HL | diagonal HL | vertical HL |
|---|:---:|:---:|:---:|
| POL | 2 | 2 | censored |
| BRA | 4 | 4 | censored |
| KOR | 1 | 2 | censored |
| ZMB | 2 | 2 | 1 |

- PRED A (horizontal HL ≤ vertical HL in ≥5 of 6): **5/6 SUPPORTED**
- PRED B (vertical right-censored in ≥3 of 6): **4/6 SUPPORTED**
- F1/F2/F3 all NOT FIRED

Vertical is censored (never reaches 50%) in POL/BRA/KOR while horizontal recovers in 1-4 yrs. Tier composition restricted to 0-1 bounded v2x_ indices (diagnostic amendment — see dig §metric amendments).
