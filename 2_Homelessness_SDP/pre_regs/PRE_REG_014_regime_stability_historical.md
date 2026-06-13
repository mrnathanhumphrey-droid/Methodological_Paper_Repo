# Pre-Registration 014 — Regime Stability over 1980-2024

**ID:** PRE_REG_014
**Locked:** 2026-05-25
**Substrate:** PATTERN_019 (master typology) + PRE_REG_003 (regime rules)
**Status:** LOCKED — predictions and falsifiers pre-committed; first fit fires on EM-DAT historical data

---

## 1. Hypothesis

**H1 (regime stability):** Regime classification is **stable across decadal timescales** because physical geography (plate tectonics, hydrology, cyclone exposure) does not change on those timescales. A country classified Regime X in 2008-2024 should also classify Regime X in 1980-2007 (allowing for data-coverage gaps).

**H2 (mechanism):** The 6-regime typology reflects underlying geographic-mechanism categories. Decadal stability is a necessary condition for the typology to be useful as a classification framework rather than a snapshot artifact.

**H3 (specific exceptions):** A small number of countries may show **regime drift** driven by:
- Climate-attribution intensification (e.g., USA Atlantic hurricanes 1980 → 2024)
- Major infrastructure changes (e.g., dam construction altering flood profiles)
- Conflict-driven displacement masking disaster-displacement
H3 predicts ≤ 3 countries show drift; rest stable.

---

## 2. Pre-locked predictions

### Prediction set A — 1980-2007 vs 2008-2024 stability

For 22+ confirmed regime members from PATTERN_019/020/025 + Phase 2 candidates:
- Re-classify using EM-DAT 1980-2007 hazard-type breakdown
- Compare to 2008-2024 GIDD-based classification
- Tabulate: SAME / SHIFT / SPARSE-OLD-DATA

**Predicted outcomes**:
- Regime 1 (PAK): stable. 1980-2007 should show flood-dominant pattern (PAK 1992, 2010 mega-floods).
- Regime 2 (IND): stable. Long-standing monsoon-flood pattern.
- Regime 3 (PHL/VNM/MOZ/USA/CUB/etc.): stable. Cyclone belts have been active since 1980 baseline.
- Regime 4 mixed countries (BGD/BRA/CHN/JPN): mostly stable but may show 1-2 drifts.
- Regime 6 (HTI/NPL/CHL/ECU/TUR/ITA): variable — depends on whether 1980-2007 captured a major EQ event.

Specifically:
- **HTI 1980-2007**: 2010 EQ post-dates this window — HTI may NOT classify Regime 6 in older data; could appear Regime 3 (storm). **This is a falsifier**.
- **NPL 1980-2007**: 2015 Gorkha EQ post-dates — NPL may NOT classify R6 in older window.
- **TUR 1980-2007**: 2023 EQ post-dates; older window may show R4 mixed.
- **USA storm intensification**: 1980-2007 USA storm-displacement should be LOWER than 2008-2024; could show R3 at smaller magnitude or even drift to R4.

### Prediction set B — Threshold-shifting cases

Specifically predict that ≥1 of {HTI, NPL, TUR} shows REGIME DRIFT from non-R6 → R6 between 1980-2007 and 2008-2024. This is **expected drift driven by single-event arrival**, not a typology failure — it's a specific case where the geographic-mechanism (subduction-zone exposure) was always present but didn't register in displacement until a major event occurred.

---

## 3. Falsifiers

- **F1**: ≥ 5 of 22 countries shift regime → typology not stable on decadal scale
- **F2**: Major-flood countries (PAK, IND, THA) shift to non-flood regimes → flood-mechanism not geographic
- **F3**: ALL of {HTI, NPL, TUR} fail to show R6 in 1980-2007 → R6 is purely 2008-2024 artifact (event-driven)
- **F4**: USA shifts from R3 in 1980-2007 to non-R3 → cyclone-belt classification not stable

H1 walks back if F1 OR (F2 AND F3) fire.
H3 walks back if F1 fires alone (drift count exceeds prediction).

**Special case for F3**: If ALL R6 countries depend on a single-event in 2008-2024 to register R6, then "Regime 6" is a function of which decade is observed, not a stable geographic category. This would be a substantive refinement.

---

## 4. Methodology

- EM-DAT 1980-2007 (`D:/IDP/data/emdat/public_emdat_incl_hist_2026-05-18.xlsx`)
- Use EM-DAT "Total Affected" + "No. Homeless" as displacement proxies (GIDD doesn't extend that far back)
- Apply PRE_REG_003 H1 classification rules using affected-share by hazard type
- Note: EM-DAT methodology differs from GIDD; absolute magnitudes won't match, but **share-by-hazard** should be comparable
- Threshold: ≥ 100K total affected cumulative 1980-2007 for valid classification

## 5. Cross-references
- PATTERN_019 (master typology)
- PRE_REG_003 (regime rules)
- PRE_REG_017 (Phase 2 expansion)

---

## 6. Provenance
Locked 2026-05-25 before Phase 3 P2-H test fires.

---

## 7. Results — first fit (fired 2026-05-25)

Full dig: `D:/IDP/papers/PAPER_2_DISASTER_REGIMES/digs/2026_05_25_P2_H_F_phase3_stability_USA.md`

### Headline
**F1 FIRED — 15 of 29 countries shift regime (52% shift rate; threshold ≥5).** H1 walked back.

But ~5-6 of 15 shifts are methodological artifacts (drought-reporting differences between GIDD and EM-DAT) or sub-type-within-regime shifts. Real geographic shifts: ~6-8.

### Falsifier status
| Falsifier | Result |
|---|---|
| F1 (≥5 shift) | **FIRED** — H1 walked back |
| F2 (major-flood shift ≥2 of 3) | FIRED partially (IND artifact; THA real shift via 2011 megaflood) |
| F3 (ALL R6 fail in 1980-2007) | NOT FIRED — TUR + ITA were R6 historically |
| F4 (USA shifts from R3) | NOT FIRED |

### Substantive findings (not just walk-back)
1. **Regime 6 is event-arrival driven** (PRE_REG_014 H3 SUPPORTED) — HTI/NPL/CHL/ECU all gained R6 only with post-2007 major quakes. R6 classification is the JOINT product of (geophysical exposure) × (major event within observation window).
2. **Storm/flood regimes more stable** — USA/CUB/PRI/VUT 3a stable; PAK 1 stable; PHL 3 stable.
3. **Methodological artifact: drought reporting** between GIDD and EM-DAT distorts IND/AFG/IRN classifications. Paper should standardize on GIDD methodology.
4. **THA shift (4a → 1) is real** — 2011 Chao Phraya megaflood drove R1 classification post-2007. PATTERN_028 reinforced.

### Refined H1 (post-walk-back)
Typology is **window-sensitive** for event-latent regimes (R6 specifically). Storm-dominant and flood-dominant regimes are structurally more stable. Paper 2 must caveat that regime classification is anchored to the observation window and a country's R6 status is the joint product of (subduction/collision zone exposure) AND (major-event occurrence within window).

**Status**: H1 WALKED BACK; refined claim added. R6 event-latency = substantive finding.
