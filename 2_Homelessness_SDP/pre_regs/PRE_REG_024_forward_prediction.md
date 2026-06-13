# Pre-Registration 024 — Forward-Prediction: Residue-Class Outperforms Baseline on Held-Out Future Data

**ID:** PRE_REG_024
**Locked:** 2026-05-27
**Substrate:** PRE_REG_022 (residue-class Stan model) + Papers 2 + 4 typology assignments
**Status:** LOCKED — predictions pre-committed; first fit fires when 2025-2027 data arrives (GIDD + UCDP-GED annual releases)

---

## 1. Hypothesis

**H1 (forward-prediction methodology portability):** A residue-class Stan model trained on 2008-2024 country-year-channel data outperforms a no-typology baseline model on held-out 2025-2027 data.

**Metric**: ΔLOO-CV (or held-out predictive log-likelihood) on 2025-2027 observations using 2008-2024-trained models.

**Predicted**: residue-class outperforms baseline by ≥ 3 elpd units on held-out data (smaller than in-sample improvement but still positive).

**H2 (specific forward cases):**

### USA storm-IDP 2025-2027
- Residue-class (USA = Regime 3a) should anticipate continued storm-displacement intensification (predicted ≥ 2M storm-IDP per year average 2025-2027, given Regime 3a intensification trajectory from PRE_REG_015)
- Baseline (no typology) should under-predict, treating USA 2024 (10.24M) as outlier-not-trend

### TGO conflict 2025-2027 (cross-link to Paper 3)
- If PRE_REG_001 (TGO emergence) confirms, residue-class with TGO as new Type C member predicts conflict-IDP trajectory
- Baseline predicts based on TGO's historical zero-conflict pattern → under-predicts

### POL libdem 2025-2027 (cross-link to Paper 1)
- POL libdem trajectory (Tusk + Nawrocki) tracked via V-Dem v17 release ~March 2027
- This is a Paper 1 forward-watch (PRE_REG_006), not directly Paper 6, but adds to multi-paper validation

---

## 2. Pre-locked predictions

### Prediction set A — Held-out elpd improvement
Train both models on 2008-2024 data; evaluate elpd on 2025-2027 observations.
**Predicted**: ΔLOO_held-out (residue-class - baseline) ≥ 3.

### Prediction set B — USA 2025 storm-IDP
Residue-class predicts mean USA 2025 storm-IDP ≥ 1M with credible interval [200K, 5M]. Baseline predicts based on 2008-2023 median (~450K) without intensification term.

### Prediction set C — TGO 2025 conflict-IDP
If TGO crosses PRE_REG_001 strife threshold in 2025 (UCDP-GED v26): residue-class with TGO assigned Type C predicts 2025 conflict-IDP ≥ 50K. Baseline predicts ≤ 5K based on historical zero pattern.

### Prediction set D — Calibration check
75% credible intervals from residue-class model should cover 75% of held-out observations (±10pp). Mis-calibration ≥ 20pp → walks back calibration claim.

---

## 3. Falsifiers

- **F1 (no improvement on held-out)**: ΔLOO_held-out < 0 → residue-class doesn't generalize forward
- **F2 (USA prediction missed)**: residue-class under-predicts USA 2025-2027 storm-IDP by >5× → methodology fails on USA Regime 3a anchor
- **F3 (TGO prediction missed conditional)**: IF TGO crosses PRE_REG_001 threshold AND residue-class predicts <10K conflict-IDP for that year → methodology fails on conflict-channel forward
- **F4 (calibration breakdown)**: credible interval coverage <50% on held-out → posterior intervals not trustworthy

F1 firing = methodology portability claim walks back; doesn't generalize forward.
F4 firing = posterior intervals miscalibrated even if point predictions are OK.

---

## 4. Methodology

### Training data
- 2008-2024 country-year-hazard panel (PRE_REG_022 substrate)
- Papers 2 + 4 type assignments locked at training time

### Held-out data
- 2025: UCDP-GED v26 + GIDD 2025 release (~April 2026)
- 2026: UCDP-GED v27 + GIDD 2026 release (~April 2027)
- 2027: UCDP-GED v28 + GIDD 2027 release (~April 2028)

### Test procedure
1. Fit both models on 2008-2024 data
2. As each year of 2025-2027 data arrives, compute log-likelihood under both models
3. Cumulative held-out elpd comparison
4. Specific case checks (USA storm, TGO conflict, etc.)

### Decision rules
- Strong confirmation: ΔLOO_held-out ≥ 5 AND all specific cases correct
- Partial: ΔLOO_held-out ∈ [0, 5] OR specific cases mixed
- Walks back: ΔLOO_held-out < 0 OR F2/F3/F4 fires

## 5. Cross-references
- PRE_REG_022 (in-sample Stan fit)
- PRE_REG_023 (admin-1 portability)
- PRE_REG_001 (TGO forward-watch; Paper 3)
- PRE_REG_015 (USA climate-attribution; Paper 2)

## 6. Provenance
Locked 2026-05-27 before any 2025-2027 data observation. First fit fires when UCDP-GED v26 + GIDD 2025 arrive (~April 2026).
