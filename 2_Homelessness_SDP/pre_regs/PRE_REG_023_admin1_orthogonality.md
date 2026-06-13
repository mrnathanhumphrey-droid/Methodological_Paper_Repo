# Pre-Registration 023 — Channel-Orthogonality at Admin-1 Sub-National Level

**ID:** PRE_REG_023
**Locked:** 2026-05-27
**Substrate:** PRE_REG_004 (country-level orthogonality 92% confirmed) + PATTERN_001 family + Paper 6 methodology
**Status:** LOCKED — predictions and falsifiers pre-committed; first fit deferred pending admin-1 panel construction

---

## 1. Hypothesis

**H1 (sub-national channel-orthogonality):** Channel-orthogonality holds at admin-1 sub-national level. That is, within most country-year-admin1 cells, ≤1 displacement channel (conflict / flood / storm / EQ / drought) accounts for >50% of displacement.

**Predicted orthogonality rate**: ≥ 70% at admin-1 level (lower than country-level 92% because admin-1 has lower N and more zero-cells; some cells will be 50-50 mixed).

**H2 (mechanism):** Even within multi-channel countries (e.g., MOZ Type B + Regime 3 storm; HTI Type B + Regime 6 EQ), channels operate in DIFFERENT admin-1 zones. Conflict in NK/Ituri (COD); storms in coastal Cabo Delgado (MOZ); EQ in Petite-Goâve (HTI). Geographic specialization within country.

**H3 (test of methodology portability):** Residue-class Stan model (PRE_REG_022) applied at admin-1 level should also outperform admin-1 baseline. If true, methodology is **scale-portable** from country to admin-1.

---

## 2. Pre-locked predictions

### Prediction set A — Admin-1 orthogonality rate
≥ 70% of admin-1-year cells with displacement data show single-channel dominance (>50% of cell total).

### Prediction set B — Within-country geographic specialization
For multi-channel confirmed countries, computed channel-by-admin-1 share. Predicted:
- COD: conflict concentrated in NK+Ituri (≥80% conflict-IDP); flood/storm in other provinces
- MOZ: conflict in Cabo Delgado (≥70% conflict-IDP); storms in coastal provinces
- HTI: EQ in Sud + Grand-Anse; storms in NW; gang-violence in West (Port-au-Prince)
- ETH: conflict in Tigray + Amhara; floods in Somali + Oromia (different provinces)
- BFA: conflict in Sahel + Est; floods in Centre regions

≥ 4 of 5 countries match predicted geographic specialization.

### Prediction set C — Methodology scale-portability
Fit residue-class model and baseline at admin-1 level. **Predicted**: residue-class outperforms baseline by ΔLOO ≥ 3 (smaller effect than country-level due to higher noise but still positive).

---

## 3. Falsifiers

- **F1 (orthogonality fails sub-national)**: < 50% of admin-1-year cells show single-channel dominance → orthogonality is country-level artifact, doesn't transfer
- **F2 (geographic specialization absent)**: < 3 of 5 countries match predicted within-country pattern → channels mix at admin-1 level within country
- **F3 (methodology doesn't scale)**: residue-class fails to outperform baseline at admin-1 → methodology is country-level-only

F1 firing = sub-national orthogonality claim walked back; methodology stays country-level only.

---

## 4. Methodology

### Data acquisition required
- UCDP-GED v25 admin-1 (already in hand)
- GIDD admin-1 displacement data (IDMC IDU operational data may be needed; admin-1 may not be standard in GIDD aggregates)
- ACLED admin-1 (alternative source if needed)

### Test sequence
1. Pull admin-1 panels for 5+ confirmed multi-channel countries (COD, MOZ, HTI, ETH, BFA)
2. Compute admin-1 channel decomposition
3. Apply orthogonality test
4. Apply residue-class Stan model at admin-1 (Paper 6 methodology portable)
5. LOO-CV comparison

## 5. Cross-references
- PRE_REG_004 (country-level orthogonality anchor)
- PRE_REG_022 (Paper 6 country-level Stan fit)
- PATTERN_001 family
- Papers 2 + 4 typology assignments (for residue-class)

## 6. Provenance
Locked 2026-05-27 in parallel with PRE_REG_022 Stan fit. First fit deferred pending admin-1 panel construction.
