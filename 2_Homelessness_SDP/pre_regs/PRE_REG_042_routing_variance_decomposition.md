# Pre-Registration 042 — Track-vs-Origin Variance Decomposition + Differential Outcome Prediction (Paper 9, Phase 1, load-bearing test)

**ID:** PRE_REG_042
**Locked:** 2026-05-30 (before any data acquisition or cross-walk construction)
**Substrate**: META_PIVOT_QUANTIFICATION_2026_05_30 (Paper 9 selected as the program's first ACTIVE CHANNEL paper) + PAPER_9_SCOPE.md (load-bearing claims 1+2)
**Paper:** 9 (Legal-Status Routing as Active CHANNEL)
**Status:** LOCKED — fires on next session after Phase 1 data acquisition + cross-walk

---

## 0. Why this test exists (the load-bearing test for Paper 9)

Paper 9 claims that the US receiving-state apparatus routes heterogeneous upstream displacement events into a small number of legal-status tracks, and that **outcomes for the displaced are dominated by track (not origin)** — but only for outcomes whose mechanism runs through legal authorization. PRE_REG_042 is the load-bearing test for both halves of that claim:

- **Existence (H1)**: legal-track explains substantial variance in work-authorization-dependent outcomes.
- **Differential mechanism (H2 — the sharpest test)**: track effects DOMINATE origin effects on work-authorization-dependent outcomes; **origin effects DOMINATE track effects on human-capital-dependent outcomes**. This differential prediction is what distinguishes the routing-as-mechanism claim from a trivial "track and origin both matter" claim — the channel has to operate *specifically* through legal authorization, not as a generic confounder.

H2 is the deeper test: if track and origin effects move *together* across all outcomes (no differential), then track is just a proxy for unobserved population characteristics. If they move *oppositely* by outcome type (track dominates auth-dep; origin dominates HC-dep), the routing channel has the right mechanistic shape.

---

## 1. Hypotheses

**H1 (track-effect exists, work-auth-dep outcomes)**: Across (state × origin × cohort) cells, legal-track distribution explains ≥ **15%** of the variance in each work-authorization-dependent outcome (labor-force participation rate, formal-employment rate, mean earnings, public-benefit takeup rate among eligible).

**H2 (differential mechanism — load-bearing)**: In a joint model with track-distribution and origin as predictors:
- For **work-authorization-dependent outcomes** (LFP, formal employment, earnings, benefit takeup): track explains *more variance than* origin.
- For **human-capital-dependent outcomes** (English-proficiency rate, mean educational attainment): origin explains *more variance than* track.

**H3 (rights-bundle ordering)**: Among the tracks identified, outcomes order monotonically with the rights-bundle: tracks with broader work-authorization + benefit-eligibility (Refugee, SIV) > tracks with intermediate rights (TPS, asylum-granted) > tracks with narrow rights (asylum-pending, parole-without-work-permit) > undocumented. This is a *predicted ordering*, not a categorical-only claim.

---

## 2. Pre-locked metrics + predictions

### Cell-aggregate analysis (PRIMARY)
- **Unit of analysis**: (state × origin × entry-cohort) cell. State = ACS state. Origin = country of birth, top ~15 origins by displacement-driven cohort size. Entry-cohort = year-of-entry binned (2018-2019, 2020-2021, 2022, 2023). Window: ACS 5-yr 2018-2023.
- **Track distribution per cell**: 7-dim probability vector across {Refugee, TPS, Asylum-pending, Asylum-granted, SIV, Parole-with-EAD, Undocumented} constructed from external admin data (ORR + USCIS TPS + EOIR + DOS SIV + CHNV/UFU reports + MPI undocumented).
- **Outcomes** (cell-aggregate rates / means among foreign-born from displacement origins):
  - **Work-auth-dependent**: LFP rate (16-64); formal-employment rate (employed for wages or self-employed in formal sector); mean wage/salary earnings (employed only); SNAP receipt rate (among eligible-by-track); Medicaid receipt rate (among eligible-by-track).
  - **Human-capital-dependent**: English-proficiency rate ("speaks English well/very well"); mean years of education (25+).
- **Variance decomposition**: linear mixed-effects model — outcome ~ track-distribution + origin + cohort + state + interactions; report partial-R² of track-distribution vs origin via Type-II SS decomposition + variance-partitioning.
- **Bar for H1**: track-distribution partial-R² ≥ **0.15** on at least 3 of 5 work-auth-dependent outcomes.
- **Bar for H2 (differential)**: track partial-R² > origin partial-R² on at least 3 of 5 work-auth outcomes AND origin partial-R² > track partial-R² on at least 1 of 2 human-capital outcomes. **The differential is the load-bearing pattern.**

### Probabilistic individual-level (ROBUSTNESS)
- Assign each ACS individual a probability-distribution over tracks conditional on (state × origin × entry-cohort) and individual covariates (citizenship status, year of arrival, age, education).
- Multiple-imputation analysis with M=10 imputations; pool variance decomposition.
- Report individual-level R² alongside cell-aggregate.

### Falsifiers (pre-committed)
- **F1 (track effect absent)**: track partial-R² < 0.05 on ALL work-auth-dependent outcomes → routing is not a meaningful channel; reframe needed.
- **F2 (no differential)**: track partial-R² > origin on ALL outcomes (auth-dep AND HC-dep) → track is just a population-quality proxy, not a mechanism through authorization specifically. Routing-as-mechanism claim NOT supported in its sharp form.
- **F3 (origin dominates)**: origin partial-R² > track on ALL outcomes → origin is the fundamental axis; routing is decorative. Reframe needed.
- **F4 (ordering wrong)**: rights-bundle ordering in H3 is reversed or null → tracks are not ordered by rights-bundle; channel framing is wrong.

F1 or F3 firing = the META_PIVOT_QUANTIFICATION prediction (CHANNEL-mode produces novel mechanism) is **falsified for Paper 9** — informative for the meta-framework.

---

## 3. Methodology

### Data acquisition (pre-locked sources)
- **ACS 5-yr 2018-2023** via Census API or IPUMS-USA: variables BPL (country of birth), YRIMMIG (year of immigration), CIT (citizenship status), STATEFIP, LABFORCE, EMPSTAT, CLASSWKR, INCWAGE/INCEARN, SPEAKENG, EDUCD, FOODSTMP, HCOVANY (Medicaid via subcomponents).
- **ORR refugee resettlement data**: state × origin × FY arrivals 2018-2023 (HHS ORR annual reports).
- **USCIS TPS Fact Sheets**: TPS designations + estimated populations by origin × period.
- **EOIR Statistics**: asylum filings, grants, denials by court (proxy for state) × origin × year.
- **DOS SIV reports**: Afghan + Iraqi SIV approvals by year.
- **CHNV / UFU parole reports**: USCIS quarterly dashboards.
- **MPI undocumented estimates**: state × origin estimates from MPI Data Hub.

### Cross-walk construction (pre-committed rules)
- For each (state × origin × entry-cohort) cell, compute the probability vector over the 7 tracks using the external admin sources.
- Where admin sources don't distinguish track at sub-national resolution (e.g., USCIS reports often national-only for TPS), allocate to states proportionally to the foreign-born population of that origin in each state (per ACS).
- Where multiple admin sources cover the same cell (e.g., ORR + USCIS), reconcile by mutual constraints; report any inconsistencies.
- **Sensitivity**: report results under (i) strict cross-walk, (ii) alternative cross-walks with weakest-link assumption.

### Outcomes restrictive to track-eligible populations
- Benefit takeup: SNAP and Medicaid eligibility differs by track. Restrict the takeup analysis to track-eligible cells (Refugees and asylees are eligible from arrival; TPS holders restricted; undocumented excluded except for emergency Medicaid). Make eligibility-by-track an explicit pre-committed mapping (locked here, not derived later).

### Origins covered (pre-locked)
Ukrainian, Venezuelan, Cuban, Honduran, Salvadoran, Guatemalan, Haitian, Afghan, Syrian, Iraqi, Burmese, Congolese (DRC), Eritrean, Somali, Sudanese. Other origins reported but not load-bearing.

---

## 4. Acknowledgments at lock time

- **Cross-walk introduces measurement error** — quantified in robustness section.
- **Selection into track is non-random** — Phase 1 reports associations; Phase 2 (PRE_REG_043/044) handles within-origin causal identification.
- **CPS-ASEC and SIPP** would give better employment-history detail than ACS; deferred to Phase 2 if needed (CPS sample size limits sub-state origin analysis).
- **English proficiency at arrival vs current** — ACS captures current; the differential test assumes some HC variation persists; consider entry-cohort filters.
- **Public benefits**: many state-level program rules complicate eligibility cross-walk. Report sensitivity to state-rule heterogeneity.
- **2025-2026 TPS terminations** may affect 2023+ cohorts mid-analysis; lock the data window at 2018-2023 ACS pre-termination.
- **Routing-as-mechanism ≠ routing-causes-outcomes**: this is an associational test. Phase 2 (within-origin) and Phase 4 (TPS termination natural experiment) add causal identification.

---

## 5. Cross-references

- META_PIVOT_QUANTIFICATION_2026_05_30 (Paper 9 selected as ACTIVE CHANNEL paper; this PRE_REG tests the framework's prediction)
- PAPER_9_SCOPE.md (load-bearing claims 1+2 are this PRE_REG)
- PAPER_9_LEGAL_STATUS_ROUTING/HUNT_PLAN.md (Phase 1 of 4)
- P7 (parallel agent) — coordinate on receiving-side scope to avoid overlap

---

## 6. Provenance

Locked 2026-05-30 before any data acquisition, cross-walk, or analysis. Predictions, falsifiers, data sources, cross-walk method, eligibility mappings, outcome definitions, partial-R² bars, and origins-covered all committed first.

---

## 7. Results — first fit
_(pending Phase 1 data acquisition + cross-walk construction; fires on next session)_
