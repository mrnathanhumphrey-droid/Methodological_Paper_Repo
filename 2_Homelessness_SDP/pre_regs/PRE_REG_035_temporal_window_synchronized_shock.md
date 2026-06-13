# Pre-Registration 035 — Temporal-Window / Synchronized-Shock Test

**ID:** PRE_REG_035
**Locked:** 2026-05-28 (predictions + falsifiers pre-committed before split/bootstrap)
**Substrate:** PATTERN_023 (ETH triple-coupling; "is it 2020-2024 alone?" open question) + PRE_REG_033
**Paper:** 8 (Compound-Crisis Coupling)
**Status:** LOCKED — first fit fires on split-window + bootstrap of coupling cases

---

## 1. Hypothesis

**H1 (coupling is window-transient, not structural):** ETH's triple-channel coupling is driven substantially by the synchronized-shock window 2020-2024 (Tigray war + Rift Valley flood + Horn drought hitting simultaneously). When the pre-2018 period is examined separately, the coupling is materially weaker. Coupling is a transient property of overlapping shock windows, not a permanent country trait.

**H2 (forecasting implication):** If H1 holds, coupling is predictable from shock-calendar OVERLAP (do multiple channels have mega-years in the same window?) rather than from country type. This makes compound-crisis episodes forecastable.

---

## 2. Pre-locked predictions

### Prediction set A — Split-window
For ETH (and SOM/BRA where ≥8 years each side), compute coupling ρ separately for an early window vs the synchronized-shock window:
- ETH: pre-2018 (2008-2017) vs 2018-2024
- **Predicted**: ETH CD coupling is substantially weaker pre-2018 (ρ drops by ≥ 0.25) and concentrates in 2018-2024

### Prediction set B — Bootstrap CI
Bootstrap (resample country-years with replacement, 2000 reps) the coupling ρ for ETH all-pairs:
- **Predicted**: the full-window ETH CD ρ (0.83) has a wide CI; dropping the 2020-2022 triple-peak years collapses ρ below 0.5 (leave-window-out test)

### Prediction set C — Shock-overlap predictor
Define shock-overlap = number of channels with a mega-year in a country's modal 3-year window. 
- **Predicted**: coupling ρ correlates positively with shock-overlap across the coupling-set + a sample of orthogonal countries

---

## 3. Falsifiers

- **F1 (coupling is structural)**: ETH coupling ρ is similar pre-2018 vs 2018-2024 (Δρ < 0.15) → coupling is a persistent country trait, NOT window-transient; H1 walked back
- **F2 (leave-window-out doesn't collapse it)**: dropping 2020-2022 leaves ETH CD ρ > 0.6 → coupling not driven by the synchronized window
- **F3 (no shock-overlap relationship)**: coupling ρ uncorrelated with shock-overlap → the synchronized-shock mechanism doesn't generalize

F1 + F2 both firing = coupling is structural (country-trait), reorienting Paper 8 toward state-collapse or ENSO mechanisms rather than transient-window.

---

## 4. Methodology
- GIDD channel panels for coupling cases, 2008-2024
- Split-window Spearman ρ (early vs synchronized-shock window)
- Bootstrap + leave-window-out (drop 2020-2022) ρ recomputation
- Shock-overlap feature: count channels with mega-year (>country-specific threshold) in modal 3-yr window
- Acknowledgment: ETH has only 17 country-years; split halves give ~8-10 each → wide CIs; report honestly

## 5. Acknowledgments at lock time
- Small n per window (8-10 years) → low power; bootstrap CIs will be wide
- This test discriminates window-transient vs structural; it does NOT prove a mechanism (ENSO test PRE_REG_034 is the climate-driver test)
- Coupling ≠ causation

## 6. Cross-references
- PATTERN_023 (the "is it 2020-2024 alone?" open question this answers)
- PRE_REG_033 (coupling census), PRE_REG_034 (ENSO)

## 7. Provenance
Locked 2026-05-28 before split/bootstrap. First fit fires on coupling-case time series (data already in hand).

---

## 8. Results — first fit (fired 2026-05-28)

Full dig: `D:/IDP/papers/PAPER_8_COMPOUND_CRISIS/digs/2026_05_28_prereg035_temporal_window.md`

**H1 (window-transient) WALKED BACK. F1 + F2 FIRED.** Set C SUPPORTED.

### Set B (decisive) — leave-window-out
Dropping ETH 2020-2022 triple-peak years: CD ρ **0.83 → 0.83 (unchanged)**; bootstrap 90% CI (0.67, 0.90). CF 0.69→0.64, FD 0.58→0.54. Coupling is STRUCTURAL, not driven by the synchronized-shock window. Predicted collapse <0.5 did NOT happen.

### Set A — inconclusive (data coverage)
ETH drought-displacement sparse pre-2017 → CD/FD "early" window n/a. Split-window can't cleanly test CD; leave-window-out (Set B) is the reliable probe.

### Set C — SUPPORTED
Shock-overlap vs max|ρ| across 49 countries: Spearman ρ=+0.40, p=0.004.

### Reconciliation + redirect
Set B (structural within-ETH) + Set C (shock-overlap predicts cross-country) reconcile as CHRONIC recurrent multi-hazard synchrony (not a one-time window). Mechanism redirected to recurrent climate-teleconnection → **PRE_REG_034 (ENSO) is now the decisive test**. Fragility already tested weak (PRE_REG_033 p=0.125). Honest walk-back; pre-committed F1/F2 pointed the paper at the right next question.
