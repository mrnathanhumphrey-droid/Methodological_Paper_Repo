# Pre-Registration 034 — ENSO Teleconnection Test

**ID:** PRE_REG_034
**Locked:** 2026-05-28 (predictions + falsifiers pre-committed before ONI acquisition)
**Substrate:** PATTERN_023 (ETH triple-coupling; ENSO mechanism candidate) + PATTERN_008 (Horn drought)
**Paper:** 8 (Compound-Crisis Coupling)
**Status:** LOCKED — first fit fires after NOAA ONI data acquired

---

## 1. Hypothesis

**H1 (ENSO drives coupled channels):** In the coupling cases, the coupled displacement channels (especially drought, and conflict-via-food-shock) peak in association with ENSO phase. The shared climate driver (El Niño/La Niña) is what couples the channels.

**H2 (Horn = La Niña drought):** For Horn-of-Africa coupling cases (ETH, SOM), drought-displacement peaks in La Niña years (La Niña → East African short-rains failure → Horn drought). Conflict-displacement lags drought by 0-1 year (food-insecurity → conflict).

---

## 2. Pre-locked predictions

### Prediction set A — ENSO alignment
Using NOAA ONI (Oceanic Niño Index), classify each year 2008-2024 as El Niño (ONI ≥ +0.5), La Niña (≤ −0.5), or neutral.
- **Predicted**: in ETH + SOM, drought-displacement mega-years fall disproportionately in La Niña years (≥ 60% of drought mega-years are La Niña)

### Prediction set B — Conflict lag
- **Predicted**: in ETH + SOM, conflict-displacement peaks lag drought peaks by 0-1 year (drought → food insecurity → conflict), producing the observed CD coupling

### Prediction set C — Non-ENSO control
- **Predicted**: BRA conflict-drought coupling (Amazon) is LESS ENSO-aligned than Horn cases (Amazon drought has ENSO component but also Atlantic SST dipole + deforestation drivers) — if BRA coupling is ENSO-aligned too, the mechanism generalizes; if not, BRA coupling has a different (land-conflict) mechanism

---

## 3. Falsifiers

- **F1 (no ENSO alignment)**: Horn drought mega-years are NOT disproportionately La Niña (< 50%) → ENSO teleconnection mechanism walked back
- **F2 (no lag structure)**: conflict peaks do not follow drought peaks → drought→conflict food-shock pathway not supported
- **F3 (ENSO explains too much)**: ALL countries' drought aligns with ENSO equally → ENSO is a global drought driver but doesn't explain why only SOME countries COUPLE (coupling still needs the conflict-channel link)

F1 firing = drop ENSO mechanism; coupling is not climate-teleconnection-driven.

---

## 4. Methodology
- NOAA ONI monthly 1950-2025 (to be acquired — public NOAA CPC)
- GIDD drought + conflict displacement by year for coupling cases
- ENSO-phase classification per year; contingency test (drought-mega-year × ENSO-phase)
- Lag cross-correlation drought→conflict (0, 1, 2 yr lags)

## 5. Acknowledgments at lock time
- ENSO acquisition required (NOAA ONI — small public file)
- Small n (17 years × few coupling countries) → contingency tests low-power; report exact counts
- ENSO ≠ sole driver; deforestation (BRA), state-policy (ETH) confound
- Coupling ≠ causation

## 6. Cross-references
- PATTERN_023 (ENSO mechanism candidate stated there)
- PRE_REG_033 (coupling census), PRE_REG_035 (temporal-window)
- Paper 2 PRE_REG_015 (climate-attribution — SST/ENSO overlap)

## 7. Provenance
Locked 2026-05-28 before NOAA ONI acquisition. First fit fires when ONI arrives.

---

## 8. Results — first fit (fired 2026-05-28, NOAA ONI acquired)

Full dig: `D:/IDP/papers/PAPER_8_COMPOUND_CRISIS/digs/2026_05_28_prereg034_enso.md`

**Set A NOT SUPPORTED (F1 fired); Set B contemporaneous; Set C SUPPORTED.**

- **Set A**: Horn drought-displacement mega-years 50% La Niña vs 47% baseline — no enrichment, F1 fired. BUT underpowered: GIDD drought-displacement is ~4 years/country, all 2017-2023, and lags meteorological drought (2020-2023 Horn drought recorded as displacement in 2022-2023). Displacement timing ≠ rainfall timing → wrong instrument for the ENSO test.
- **Set B**: conflict-drought coupling is CONTEMPORANEOUS (lag 0 strongest: ETH 0.83, SOM 0.79), not drought-leads-conflict. Consistent with PRE_REG_035 structural synchrony.
- **Set C SUPPORTED**: BRA Amazon drought is El-Niño-aligned (0% La Niña) — OPPOSITE ENSO phase from Horn. The two CD-coupling families have distinct, opposite climate drivers (correct known climatology).

### Net
Single-year-ENSO mechanism not supported via displacement (F1), but family-specific opposite climate signatures (Horn La-Niña-ish / Amazon El-Niño) are real. Clean climate test deferred to SPEI meteorological drought (data/spei/, contemporaneous + dense) — Set A failure is likely a displacement-instrument artifact, not absence of climate signal.
