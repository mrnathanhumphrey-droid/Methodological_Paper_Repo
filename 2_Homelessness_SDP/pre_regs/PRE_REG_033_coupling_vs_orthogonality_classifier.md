# Pre-Registration 033 — Coupling-vs-Orthogonality Classifier

**ID:** PRE_REG_033
**Locked:** 2026-05-28 (predictions + falsifiers pre-committed before census)
**Substrate:** PATTERN_023 (ETH triple) + PATTERN_021 (BRA CD) + PRE_REG_004 (orthogonality 92%)
**Paper:** 8 (Compound-Crisis Coupling)
**Status:** LOCKED — first fit fires on full-corpus channel-correlation census

---

## 1. Hypothesis

**H1 (coupling is rare + distinct):** Across the corpus, channel coupling (≥1 channel-pair Spearman |ρ| > 0.5 at country-year level) is rare — present in ≤ 15% of countries with sufficient data. The majority are orthogonal, consistent with PRE_REG_004's 92%.

**H2 (coupling is not random — it has a correlate):** Coupling-status correlates with at least one of:
- state fragility (low Polity/libdem) — state can't buffer any channel
- a synchronized-shock-window feature (multiple channels with mega-years in the same 2-3yr window)

**H3 (triple-coupling is uniquely ETH):** Only ETH shows all three of CF/CD/FD > 0.5. Other coupling cases are single-pair (mostly conflict-drought).

---

## 2. Pre-locked predictions

### Prediction set A — Coupling census
Compute CF, CD, FD (and CS conflict-storm where applicable) Spearman ρ for every corpus country with ≥10 country-years of multi-channel data.
- **Predicted**: ≤ 15% of countries have any pair > 0.5
- **Predicted coupling set** (pre-committed): ETH, SOM, BRA, SDN are the principal coupling cases; possibly +1-2 not-yet-tested (e.g., AFG, COD if drought-data allows)

### Prediction set B — Coupling correlate
- **Predicted**: coupling countries have lower mean Polity2/libdem than orthogonal countries (state-fragility association), OR higher synchronized-shock-window overlap
- Test: compare coupling vs orthogonal groups on (a) mean libdem, (b) count of channels with a mega-year in the modal 3-yr window

### Prediction set C — Triple-coupling uniqueness
- **Predicted**: ETH is the only country with all 3 of CF/CD/FD > 0.5

---

## 3. Falsifiers

- **F1 (coupling not rare)**: > 25% of countries show ≥1 pair > 0.5 → coupling is common, orthogonality (PRE_REG_004) overstated
- **F2 (no correlate)**: coupling vs orthogonal groups differ on NEITHER fragility NOR shock-window (both tests null) → coupling is idiosyncratic; Paper 8 walks back to "documented exceptions, no regime"
- **F3 (triple not unique)**: ≥2 countries show all-3-pairs coupling → ETH not uniquely extreme

F2 firing = Paper 8's central "compound-crisis regime" claim walks back.

---

## 4. Methodology
- GIDD conflict/flood/drought/storm channels, country-year, 2008-2024
- Spearman ρ all-pairs per country (≥10 country-years required)
- Coupling threshold |ρ| > 0.5 (matches PATTERN_023/021 reporting)
- Group comparison: coupling vs orthogonal on Polity2/libdem (Mann-Whitney) + shock-window overlap
- Multiple-comparison caveat: with ~50 countries × 3 pairs, some |ρ|>0.5 by chance; report with n-years + bootstrap CI

## 5. Acknowledgments at lock time
- Drought-data sparsity limits FD testing to a subset
- Small coupling-set (4-6 cases) → Prediction set B group comparison is low-power
- Coupling ≠ causation

## 6. Cross-references
- PATTERN_023, PATTERN_021, PRE_REG_004
- PRE_REG_034 (ENSO mechanism), PRE_REG_035 (temporal-window)

## 7. Provenance
Locked 2026-05-28 before census. First fit fires on full-corpus channel-correlation computation.

---

## 8. Results — first fit (fired 2026-05-28)

Full dig: `D:/IDP/papers/PAPER_8_COMPOUND_CRISIS/digs/2026_05_28_prereg033_coupling_census.md`

**All 3 prediction sets SUPPORTED.** 101 countries with ≥10 country-years.

- **Set A**: 8 couple = **8%** (predicted ≤15%) → SUPPORTED. Coupling set: ETH, SOM, BRA, COD, UKR, TUR, BGD, MEX. Predicted ETH/SOM/BRA found; SDN not testable (drought-data sparsity).
- **Set C**: ETH only triple-coupler → SUPPORTED.
- **Set B**: discriminating correlate is **shock-window overlap (2.50 vs 1.59, p=0.001)**, NOT state fragility (libdem 0.258 vs 0.377, p=0.125 n.s.). Favors synchronized-shock mechanism over state-collapse.

F1/F2/F3 all NOT FIRED.

### Unanticipated: two coupling families
- **CD (conflict-drought)**: ETH 0.83 / SOM 0.79 / BRA 0.69 — famine-conflict + Amazon (→ PRE_REG_034 ENSO)
- **CF (conflict-flood)**: COD +0.64 / BGD +0.57 / MEX +0.52 positive; **UKR −0.62 / TUR −0.61 NEGATIVE** = "displacement substitution" (war eclipses the disaster-displacement signal). Reframes coupling as a SIGNED axis (amplification ↔ substitution).
