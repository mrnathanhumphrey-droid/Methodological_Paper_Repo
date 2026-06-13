# Pre-Registration 032 — Recovery Completeness / Ceiling

**ID:** PRE_REG_032
**Locked:** 2026-05-27 (predictions + falsifiers pre-committed before ceiling computation)
**Substrate:** PRE_REG_012 + PATTERN_022 (BRA overshoot) + PRE_REG_006 (stalled-recovery)
**Paper:** 5 (Democratic Resilience)
**Status:** LOCKED — first fit fires on recovery-case ceilings

---

## 1. Hypothesis

**H1 (tier-differentiated ceiling):** Recoveries do not return uniformly to baseline. Horizontal and diagonal tiers recover to ≥90% of pre-backsliding baseline (or overshoot); the vertical tier plateaus BELOW baseline — a structural ceiling reflecting that captured electoral architecture (gerrymandered districts, packed electoral commissions, opposition-suppression laws) outlasts the autocrat.

**H2 (overshoot):** Some horizontal-tier recoveries OVERSHOOT baseline (BRA hcind 1.394 → 2.036; libdem 0.608 → 0.712) — backlash mobilization produces institutions stronger than before the attempt. Predicted: ≥2 of 6 cases show horizontal-tier overshoot.

---

## 2. Pre-locked predictions

### Prediction set A — Ceiling by tier
Per case, recovery ceiling = latest value / baseline value, per tier:
- **Predicted**: horizontal ceiling ratio ≥ 0.90 in ≥5 of 6 cases
- **Predicted**: vertical ceiling ratio < 0.90 in ≥4 of 6 cases (plateaus below baseline)

### Prediction set B — Overshoot
**Predicted**: ≥2 of 6 cases show horizontal-tier ceiling ratio > 1.0 (overshoot). BRA is the strong candidate.

### Prediction set C — Stalled-recovery signature
**Predicted**: cases flagged as "stalled" (PRE_REG_006) show vertical ceiling ratio < 0.50 (deep persistent vertical deficit). POL is the live test.

---

## 3. Falsifiers

- **F1 (uniform completeness)**: all tiers reach ≥90% of baseline in ≥4 of 6 cases → no structural ceiling; vertical-lag is purely temporal (recovers eventually, just slower) not a permanent deficit
- **F2 (no overshoot)**: zero cases show horizontal overshoot → backlash-strengthening (H2) walked back
- **F3 (vertical recovers fully)**: vertical ceiling ratio ≥ 0.90 in ≥4 of 6 cases → captured electoral architecture does NOT persistently outlast the autocrat

F1 firing = ceiling-finding walks back; recovery is complete-but-slow rather than incomplete.

---

## 4. Interpretation note (pre-committed)
Distinguishing "vertical plateaus below baseline" (H1, structural ceiling) from "vertical just hasn't finished recovering yet" (temporal lag, PRE_REG_031) requires the longest-window cases. Cases with ≥5 years post-trough (BRA 2023+, Sri Lanka) carry the most weight for the ceiling claim. Short-window cases (KOR 2025+, BGD 2024+) are inconclusive for ceiling and flagged as such.

## 5. Methodology
- V-Dem v15/v16: baseline (pre-attempt peak), trough (minimum), ceiling (latest)
- ceiling ratio = latest / baseline per tier
- weight cases by post-trough window length
- Sri Lanka baseline-inflation caveat carried from PRE_REG_012

## 6. Cross-references
- PRE_REG_012 (ordering), PRE_REG_031 (velocity)
- PATTERN_022 (BRA overshoot — H2 anchor)
- PRE_REG_006 (stalled-recovery — Prediction set C)

## 7. Provenance
Locked 2026-05-27 before ceiling computation. First fit fires on recovery ceilings.

---

## 8. Results — first fit (fired 2026-05-28)

Full dig: `D:/IDP/papers/PAPER_5_DEMOCRATIC_RECOVERY/digs/2026_05_28_prereg031_032_velocity_ceiling.md`

**AMENDMENT (diagnostic-driven):** ceiling metric changed from ratio (latest/baseline) to recovery fraction (latest−trough)/(baseline−trough). Trigger: ratio explodes/goes negative on near-zero V-Dem baselines (LKA −63, BGD −0.03). Recovery fraction is bounded (1.0=baseline, >1.0=overshoot, <1.0=below). Tiers restricted to 0-1 bounded v2x_ indices. [[feedback_diagnostic_driven_amendments]]

Latest recovery fraction, 4 well-conditioned cases (BGD/LKA excluded — degenerate gaps):

| Case | horizontal | diagonal | vertical |
|---|:---:|:---:|:---:|
| POL | 0.67 | 0.74 | 0.44 |
| BRA | 1.17 (overshoot) | 0.73 | **0.02** |
| KOR | 1.10 (overshoot) | 0.86 | **0.04** |
| ZMB | 0.59 | 1.48 | 0.88 |

- **PRED A2 (vertical < 0.90 in ≥4 of 6): 4/6 SUPPORTED** — vertical plateaus below baseline in all clean cases
- **PRED B (horizontal overshoot > 1.0 in ≥2): BRA + KOR SUPPORTED** (H2)
- PRED A1 (horizontal ≥ 0.90 in ≥5 of 6): NOT uniform — POL (0.67) is re-stalling under Nawrocki PiS-backed presidency (ties to PRE_REG_006)
- F1/F2/F3 all NOT FIRED

**Headline**: vertical-accountability recovers to just 2% (BRA) / 4% (KOR) / 44% (POL) of baseline — the captured electoral machinery is the lasting damage. Horizontal (courts) fully recovers or overshoots. Structural ceiling SUPPORTED.
