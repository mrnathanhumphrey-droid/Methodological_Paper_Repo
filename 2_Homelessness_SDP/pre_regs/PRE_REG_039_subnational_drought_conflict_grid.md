# Pre-Registration 039 — Sub-National Drought→Conflict Co-Location & Co-Occurrence (Paper 8 mechanism frontier, Phase 2)

**ID:** PRE_REG_039
**Locked:** 2026-05-29 (predictions + falsifiers committed before any grid join is computed)
**Substrate:** PRE_REG_038 (Phase 1 — SOM displacement co-locates; cross-country test underpowered by IDU single-channel coverage) + PRE_REG_033 (coupling census, signed axis) + PRE_REG_036/037 (ENSO ruled out)
**Paper:** 8 (Compound-Crisis Coupling)
**Status:** LOCKED — fires on a GEE SPEI grid pull + UCDP-GED binning

---

## 0. Why this test exists (the Phase 1 fix)

PRE_REG_038 found the Horn coupling case (SOM) co-locates its conflict- and drought-DISPLACEMENT at district scale, while non-coupling controls (PHL/NGA) spatially separate — F1 (aggregation artifact) did NOT fire. **But it was coverage-limited:** IDU disaster-displacement is single-channel-sparse in most countries, so only 4 countries had both channels, the cross-country tracking test (Set C) could not fire, and COD (a positive case) had only 38 disaster events. ETH and BRA are absent from IDU entirely.

**Phase 2 fixes coverage by replacing the sparse disaster-DISPLACEMENT channel with a dense drought-HAZARD channel:** SPEI (via GEE, every 0.5° cell, every year) paired with UCDP-GED geocoded conflict (every country, 1990-2023). This (a) makes the drought channel dense everywhere → enables the full cross-country test, (b) unlocks ETH/BRA, and (c) enables a confound-robust **spatio-temporal within-cell** test (does conflict spike in a cell's drought years?) that controls for time-invariant cell features (population, baseline conflict-proneness).

Note: this tests **hazard co-location** (conflict-events × drought-severity), upstream of Phase 1's displacement co-location. The two are complementary: Phase 1 = do the displacement channels share geography; Phase 2 = do the underlying hazards.

---

## 1. Hypotheses

**H1 (spatial co-location, completes Phase 1):** In coupling cases, conflict intensity and drought frequency co-locate across sub-national cells (positive spatial correlation); across countries, the spatial co-location coefficient tracks the PRE_REG_033 national coupling sign.

**H2 (spatio-temporal, confound-robust):** Within cells, conflict is elevated in that cell's drought years vs its non-drought years (cell fixed-effects) — and this local drought→conflict elevation is stronger in coupling cases than non-coupling controls.

---

## 2. Pre-locked metrics + predictions

**Grid:** 0.5° cells. **Window:** 1990–2023 (UCDP-GED × SPEI overlap).
**Drought channel:** SPEI_12 December per cell per year (GEE `CSIC/SPEI/2_10`, sampled at cell centers). Cell-year "drought" = SPEI_12 ≤ −1.0. Cell "drought frequency" = count of drought years / years.
**Conflict channel:** UCDP-GED events binned to 0.5° cells; cell(-year) conflict = sum of `best` (best fatality estimate); analysis on log1p.
**National coupling coefficient:** PRE_REG_033 per-country conflict-vs-disaster coupling (recompute pooled from GIDD where needed), for Set B tracking.

**Country set (pre-committed):** coupling cases ETH, SOM, BRA, COD, BGD, MEX, UKR, TUR + non-coupling/control conflict countries PHL, NGA, MLI, NER, SDN, SYR, AFG, IRQ, COL, CMR, MMR, MOZ (≥18 for the cross-country test).

### Set A — coupling cases co-locate (spatial)
- **Predicted:** ETH, SOM, BRA each show spatial Spearman ρ(cell conflict, cell drought-frequency) > **+0.2**.

### Set B — cross-country tracking (the test Phase 1 couldn't power)
- **Predicted:** across the country set (n ≥ 15), per-country spatial ρ correlates POSITIVELY with the PRE_REG_033 national coupling coefficient (Spearman across countries, positive, p < 0.10).

### Set C — spatio-temporal within-cell (confound-robust)
- **Predicted:** in coupling cases, mean conflict in a cell's drought-years exceeds its non-drought-years (pooled within-cell difference > 0, sign-test/Wilcoxon across cells significant); the effect is larger in coupling cases than in non-coupling controls (PHL/NGA ≈ 0).

### Set D — orthogonal control
- **Predicted:** PHL and NGA spatial ρ ≤ 0 (conflict and drought in different cells) — mirroring Phase 1.

---

## 3. Falsifiers (pre-committed)

- **F1 (no sub-national co-location even with dense data):** ETH/SOM/BRA spatial ρ ≈ 0 (≤ +0.1) → drought and conflict do NOT share sub-national geography → Phase 1's SOM result was displacement-specific / does not generalize to the hazards. Re-interprets the mechanism.
- **F2 (universal, not coupling-specific):** the drought→conflict spatial co-location and within-cell elevation are similar in coupling and non-coupling countries → drought-conflict co-location is universal, doesn't explain why only some couple.
- **F3 (sign doesn't track):** cross-country spatial ρ does NOT correlate with the PRE_REG_033 coupling coefficient → sub-national co-location is not the mechanism behind the national coupling sign.
- **F4 (confound):** spatial co-location (H1) holds but the within-cell spatio-temporal elevation (H2) is absent → the spatial correlation is a static co-incidence (both hit the same vulnerable zones), NOT a dynamic local drought→conflict process.

F1 firing re-interprets the mechanism; F4 firing distinguishes static co-vulnerability from dynamic triggering.

---

## 4. Methodology
- GEE: stack annual Dec SPEI_12 (1990-2023) as bands; `sampleRegions`/`reduceRegions` at 0.5° cell centers over each country → cell × year SPEI table. Mask land sentinel (|SPEI|<10).
- UCDP-GED v25/v26 (on disk): keep events 1990-2023 with lat/lon; bin to 0.5° cells; sum `best` per cell(-year).
- Join on cell (rounded lat/lon to 0.5°) within country.
- H1: per country, Spearman across cells (total conflict vs drought-frequency).
- H2: per cell with ≥3 drought-years and ≥3 non-drought-years, compare mean conflict; pooled Wilcoxon across cells; coupling vs control contrast.
- Set B: Spearman of per-country ρ vs PRE_REG_033 coupling coefficient.
- Sensitivity: 0.25° and 1° grid; SPEI threshold −0.8/−1.5; lag 0/1 for H2.

## 5. Acknowledgments at lock time
- Hazard co-location ≠ displacement coupling (tests the upstream structure; complements Phase 1).
- Spatial H1 is population/exposure-confoundable (both hit populated agricultural zones) — that is exactly why H2 (within-cell fixed-effects) is the confound-robust arbiter (F4 guards against static co-incidence).
- UCDP-GED counts fatalities, not displacement; conflict-intensity proxy.
- SPEI cell-center sampling approximates cell mean; 0.5° sensitivity reported.
- Coupling ≠ causation; "drought year elevates conflict" is associational at annual resolution.
- ETH/BRA now testable (UCDP-GED + SPEI) though absent from IDU.

## 6. Cross-references
- PRE_REG_038 (Phase 1 — this completes its underpowered cross-country test); PRE_REG_033 (coupling coefficients, Set B); PRE_REG_036/037 (ENSO ruled out); PRE_REG_034 Set B (national contemporaneity — H2 is its sub-national version).
- [[reference-google-earth-engine-access]]; data `data/ucdp/GEDEvent_v26_0_4.csv`, GIDD xlsx.

## 7. Provenance
Locked 2026-05-29 before any SPEI×UCDP grid join. Grid (0.5°), metrics, country set, predictions, and falsifiers committed first.

---

## 8. Results — first fit (fired 2026-05-29, GEE SPEI × UCDP-GED v25.1, 20 countries)

Full dig: `papers/PAPER_8_COMPOUND_CRISIS/digs/2026_05_29_prereg039_drought_conflict_grid.md`

**F1 + F3 fired; Set C reversed. The hazard-level test REJECTS same-place drought-conflict co-occurrence and reframes Phase 1.**

- **Set A (F1)**: coupling cases show NO spatial hazard co-location — ETH −0.07, **SOM −0.24 (p=0.002, inverse)**, BRA +0.09, COD +0.005. Conflict cells are not more drought-prone. Conflict clusters in populated/contested zones; drought-frequency is a climatological property of often-sparse peripheries.
- **Set B (F3)**: cross-country spatial co-location does NOT track national coupling (Spearman −0.15, p=0.52, n=20).
- **Set C (REVERSED)**: within-cell drought→conflict is NEGATIVE in coupling cases (ETH/SOM/COD frac-positive 0.17-0.27, Wilcoxon p≈0 — conflict *lower* in drought years). The only POSITIVE drought→conflict cases are **SYR/AFG/IRQ** (protracted-war/"Syria drought" cases) — which are NOT the displacement-coupling countries. Predicted coupling-positive / control-zero; observed the opposite.
- **Set D**: PHL/NGA ≤0 (trivially, since nearly all are ~0/neg) — control no longer discriminates (unlike Phase 1).

### Net + reframe
Phase 1 found displacement channels co-locate (SOM +0.30); Phase 2 shows the underlying HAZARDS do not (SOM −0.24) and drought does not locally trigger conflict in coupling cases. **Compound-crisis coupling is NOT co-located hazards and NOT locally drought-triggered conflict.** Triangulated triple-negative (ENSO-null 036/037 + hazard-co-location-null + within-cell-trigger-null) → the coupling is a **displacement-system property: shared receiving destinations + national-temporal overlap of two spatially-distinct, separately-driven hazards.** Side-finding: the classic local drought→conflict signal appears only in SYR/AFG/IRQ (not the coupling cases). **Phase 3 (candidate): IDU origin-vs-destination decomposition** to test the shared-destination hypothesis directly. NOTE: use `GEDEvent_v25_1.csv` (full history); v26_0_4 is 2026-candidate only.
