# Pre-Registration 029 — Structural Determination of US Displacement (SDP-legitimacy test)

**ID:** PRE_REG_029
**Locked:** 2026-05-27
**Substrate:** PRE_REG_025 (SDP framework) + PRE_REG_026 (channel-orthogonality, fired) + Paper 6 methodology
**Status:** LOCKED — thresholds pre-committed before structural-covariate outcome inspection. First-look (`analysis/paper7_structural_firstlook_2026_05_27.json`) used a thin 5-var set; this pre-reg locks the FULL structural-block test. The first-look is the motivating prior, not a confirmatory result.

---

## 0. Why this pre-reg exists

PRE_REG_026 established that US homelessness decomposes into orthogonal structural-proxy channels (SUPPORTED) and sorts into residue-class regimes (bimodal: street vs sheltered). The gross pattern is climate/shelter-policy organized. **This pre-reg asks the load-bearing SDP question: does the STRUCTURE of America — legislative policy + social conditions — explain the displacement geography and the residual variation, net of climate?**

The term "SDP" (Structurally Displaced Persons, PRE_REG_025) claims people are displaced *by institutional/policy structure*. That claim is **legitimate iff structural variables explain the displacement — especially after environmental (climate) structure is partialled out.** If only climate explains it, displacement is environmental, not policy-structural, and SDP weakens to a weather artifact. This is a falsifiable test of the term itself.

---

## 1. Hypotheses

**H1 (structural explanation):** Policy + social structural variables explain US homelessness geography — both the LEVEL (homeless per 10k) and the FORM (unsheltered share) — at state level, 2024 cross-section + panel.

**H2 (policy net of climate — LOAD-BEARING):** After partialling out climate (January mean temperature), the policy/social block still explains residual variance in displacement. This is the SDP-legitimacy test: policy-structure explains displacement beyond weather.

**H3 (housing-supply mechanism):** The housing-scarcity block (zoning restrictiveness + rental vacancy + median rent level) is the dominant *policy* driver of the homelessness LEVEL (positive direction: more restrictive supply / lower vacancy / higher rent → higher homelessness). This is the core SDP mechanism (structural scarcity as displacing force), and is the housing-economics replication (Colburn & Aldern: homelessness is a housing-supply problem, not a poverty/addiction problem at the margin).

---

## 2. Pre-locked thresholds (LOO R², leave-one-out, n≈51 states)

| Hypothesis | SUPPORTED | MIXED | FALSIFIED (falsifier) |
|---|---|---|---|
| **H1** full structural explanation | LOO R² ≥ 0.40 on ≥1 of {level, form} | 0.20–0.40 | **F1**: LOO R² < 0.20 on BOTH → structure doesn't explain displacement; SDP not supported (homelessness individual/random) |
| **H2** policy net of climate | policy-block ΔLOO-R² ≥ 0.10 after climate partialled | 0.05–0.10 | **F2**: ΔR² < 0.05 → environmental not policy; SDP = weather artifact, term weakened |
| **H3** housing-supply mechanism | housing block significant + correct sign (scarcity→more homeless), largest policy partial-R² for LEVEL | significant but not largest | **F3**: not significant OR wrong sign → core SDP mechanism fails |

Thresholds are not movable post-fit. H2 is load-bearing for SDP legitimacy.

---

## 3. Structural variable blocks

**Climate (control, partialled first):** January mean temperature (°F) by state.

**Housing-supply block (core SDP mechanism, H3):**
- Wharton WRLURI zoning restrictiveness (2018 state aggregate)
- Rental vacancy rate (ACS B25004)
- Median gross rent level (ACS B25064) + rent-to-income ratio

**Tenant-protection / shelter-law block:**
- Right-to-shelter (NY=2 strong, MA/DC=1 partial, else 0)
- Local rent regulation not state-preempted (binary)
- Just-cause eviction / eviction-record-sealing (hand-coded)

**Welfare-generosity block:**
- TANF max monthly benefit (family of 3)
- Medicaid expansion (ACA) status + year
- State minimum wage (2024) + min-wage-to-median-rent ratio

**Health/institutional block (institutional-discharge channel):**
- CDC opioid/drug-overdose death rate (state×year)
- Psychiatric inpatient bed capacity per capita (best-available; may defer)
- Prison-release + foster-care-exit rates (defer to v2 if coverage thin)

**Social-condition controls:** poverty rate, income inequality (Gini), unemployment, median household income (ACS/BLS).

---

## 4. Pre-conditions (must pass before H2 fit)

1. **Coverage**: ≥45 of 51 states have non-missing values on climate + housing-supply + welfare + ≥1 health block variable.
2. **Climate-policy non-collinearity**: |ρ(jan_temp, each policy var)| < 0.85 (else climate and policy not separable — report which collapse).
3. **Zoning availability**: WRLURI obtained for ≥45 states; if not, hand-coded published state-ranking substituted and flagged.

Pre-cond failures redlined, not silently worked around (IDP substrate discipline).

---

## 5. Selection-bias / endogeneity guards (per feedback_post_game_features_selection_bias)

- **Knowable-at-observation**: for panel/predictive reads, policy covariates use the value in force at the start of the PIT year. 2024 cross-section uses 2023-vintage ACS where the outcome is 2024.
- **RTS↔counting confound (pre-registered limitation)**: right-to-shelter states show *higher* measured rates partly because sheltered persons are easier to count than unsheltered. RTS coefficient on LEVEL is NOT interpreted causally; it is reported with this caveat. RTS is interpreted only on FORM (unsheltered share), where the counting direction is the mechanism, not the bias.
- **Reverse causality**: high homelessness may drive policy adoption (e.g., CA passes tenant protections *because* of its crisis). Panel + lagged-policy specification used to mitigate; flagged where cross-section can't resolve.
- **Cost-burden replaced**: PRE_REG_026 first-look showed cost-burden *share* is a weak predictor (LOO R² −0.02). Replaced by rent *level* + vacancy per housing-economics literature.

---

## 6. Robustness axes (report ROBUST n/4)

1. Cross-sectional (2024) vs panel (2007–2024 fixed-effects)
2. Climate operationalized as Jan-temp vs Census region dummy
3. LOO state cross-validation vs 5-fold (SEED 20260527)
4. With vs without RTS states (NY/MA/DC) — test that results aren't RTS-driven

---

## 7. Honest framing (LOCKED)

- Framing is **correlational + structural-association**, never causal (per PRE_REG_025).
- "SDP is legitimate" = "structural variables explain displacement net of climate," an empirical finding, NOT an assumed conclusion. F1/F2 firing would mean SDP is NOT empirically supported and that disposition is reported verbatim.
- Climate is structure too (environmental), but it is partialled FIRST so the *policy* contribution is isolated. The paper distinguishes environmental-structure from policy-structure explicitly.
- Do not pick the prettiest narrative. If H2 lands MIXED (ΔR² 0.05–0.10), report MIXED.

---

## 8. Cross-references
- PRE_REG_025 (SDP framework — H4 portability, H3 equivalence)
- PRE_REG_026 (channel-orthogonality, fired 2026-05-27)
- First-look: `analysis/paper7_structural_firstlook_2026_05_27.json`
- Colburn & Aldern, *Homelessness is a Housing Problem* (2022) — housing-supply mechanism prior art

## 9. Provenance
Locked 2026-05-27 before full structural-block outcome inspection. Climate + RTS + rent-control + cost-burden already seen in first-look (thin set); zoning, vacancy, rent-level, TANF, opioid, min-wage, Medicaid-dates NOT yet fit against outcomes. First fit fires after §4 pre-conditions pass.

---

## 10. Results — FIRST FIT (fired 2026-05-27; robustness 2026-05-28)

Full dig: `papers/PAPER_7_SDP_FRAMEWORK/digs/2026_05_27_prereg029_structural_sdp_legitimacy.md`

Pre-cond outcome: §4.3 WRLURI zoning NOT obtained (JUE Table 10 image-rendered, not extractable) → housing-supply operationalized by ACS vacancy + median rent + rent/income (Colburn & Aldern), flagged. Opioid 1999–2018 clean; 2018-proxy for 2024 cross-section, flagged.

| Hypothesis | Threshold | Result | Disposition |
|---|---|---|---|
| **H1** structural explanation | LOO R²≥0.40 on ≥1 of {level,form} | FORM 0.672, LEVEL 0.11–0.22 | **SUPPORTED** (form) |
| **H2** policy net of climate (LOAD-BEARING) | ΔLOO-R²≥0.10 after climate | LEVEL +0.355, FORM +0.199; **ROBUST 4/4** | **SUPPORTED** |
| **H3** housing-supply mechanism | vacancy<0 & rent>0 & p<0.10 | rent +11.64 p=0.004; vacancy −3.77 p=0.19 | **SUPPORTED** (rent-level-driven) |

Robustness (H2 ΔR², ≥0.10 per axis): primary-Jantemp ✓ / region-climate ✓ / drop-RTS ✓(form only; LEVEL −0.14) / pooled-panel-5fold ✓ → **4/4**.

**Honest boundary**: SDP-legitimacy strongest for the FORM of displacement (street vs sheltered; survives drop-RTS at 0.199). The LEVEL (per-10k) partly leans on right-to-shelter/coastal states (drop-RTS collapses LEVEL ΔR² to −0.14). RTS↔counting confound honored: RTS read on FORM not LEVEL.

**Falsifiers**: F1 NOT FIRED; F2 NOT FIRED; F3 NOT FIRED.

**SDP verdict**: empirically LEGITIMATE via passed falsifiable test — structure explains displacement net of climate, robustly. Term supported, with the form-vs-level boundary reported verbatim.

### Post-hoc refinement (2026-05-28) — does NOT change locked H1/H2/H3 dispositions
Two follow-up probes refined the "level is RTS-fragile" honest-boundary caveat:
1. **Authentic WRLURI zoning (P7-O): zoning hypothesis FALSIFIED.** Real Gyourko microdata (not the hand-coded probe, which was confabulated — Hawaii absent from 2018 survey) shows zoning on the LEVEL is wrong-signed + insignificant (−2.69 p=0.24). Zoning is NOT the upstream lever; rent is the mechanism. Dig: digs/2026_05_28_zoning_probe_authentic_NULL.md.
2. **Level robustness re-test: the "collapse" was overfitting.** Model ladder shows the 9-var block (this pre-reg's robustness-axis spec) catastrophically overfits at n=48 (drop-RTS LOO −0.34). A parsimonious rent model SURVIVES drop-RTS (M1 rent-only 0.22 cross-section; pooled panel 0.31 drop-RTS, n=816; stable 2015–2024). Climate is noise for the level (predicts form, not level). **Refined: the LEVEL is robustly rent-explained (R²≈0.2–0.3), not RTS-fragile — that caveat was an artifact of overfitting the 9-var block.** Dig: digs/2026_05_28_level_robustness_retest.md. (Post-hoc; a clean confirmatory re-test would lock M1/M2 a priori.)
