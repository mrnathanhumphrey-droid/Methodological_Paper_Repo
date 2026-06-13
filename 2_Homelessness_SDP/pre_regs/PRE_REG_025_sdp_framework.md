# Pre-Registration 025 — SDP Framework + IDP-Equivalence as Empirical Question

**ID:** PRE_REG_025
**Locked:** 2026-05-27
**Substrate:** Papers 2 + 4 + 6 methodology + US homelessness data (to be pulled)
**Status:** LOCKED — definitional pre-reg; subsequent empirical pre-regs (026/027/028) will lock specific tests

---

## 1. Hypothesis

**H1 (definitional / framework introduction):** "Structurally Displaced Persons (SDP)" is introduced as a parallel analytical concept to "Internally Displaced Persons (IDP)" for populations forced into displacement by institutional / policy mechanisms. SDP is coined **out of respect for IDP's protection-framework integrity**, not as an expansion of IDP.

**H2 (force operationalization):** SDP-producing force = **state revealed-preference for one allocation pattern over alternatives**, operating where:
- (a) institutional / policy-produced (not natural law)
- (b) counterfactual existence (alternative allocations demonstrably possible)
- (c) sustained allocation pattern across administrations (revealed preference, not single decision)

**H3 (SDP-IDP equivalence — the core empirical question):** Whether SDP and IDP describe **the same mechanism, overlapping mechanisms, or distinct mechanisms** is treated as an empirical question. The same analytical methodology (channel-orthogonality + residue-class — Papers 2/4/6) is applied to both. Substantive equivalence is tested, not assumed.

**H4 (methodology portability):** The channel-orthogonality + residue-class framework, developed for IDP analysis, transfers to SDP analysis. If H4 holds, the methodology has domain-portable explanatory power.

---

## 2. Pre-locked operationalizations

### "Voluntary" reallocation
**Voluntary = not externally imposed by occupying power, treaty constraint, or military defeat.**

- Captures: Costa Rica 1948, Mauritius 1968, peace dividend 1990s, Finland Housing First 2008+
- Excludes: Japan post-1947, Panama 1990, Germany pre-1955

### "Force" for SDP
State revealed-preference operating through institutional / policy mechanism with all three:
1. Institutionally-produced (policy choice, not natural)
2. Counterfactual existence (alternative allocations exist as demonstrated by peer countries)
3. Sustained allocation pattern (multiple administrations / decades — not single-decision)

### What this pre-reg does NOT claim
- US homelessness IS IDP (this is the empirical question — not assumed)
- Pro-war funding CAUSES homelessness (causation explicitly dropped)
- Single-administration responsibility (framework is structural, not partisan)
- "Inflation = force" without the three-criterion test (slippery-slope mitigation)

---

## 3. Pre-locked predictions (to be tested in subsequent pre-regs 026/027/028)

### Prediction set A — Channel-orthogonality holds for SDP (operationalized in PRE_REG_026)
US state-year homelessness decomposes into orthogonal channels (eviction / unaffordability / institutional-discharge / domestic-violence / disaster-displacement-not-recovered). ≥ 70% of state-years show ≤1 channel dominant (>50%). Parallel to PRE_REG_004 IDP 92% orthogonality.

### Prediction set B — Cross-country spending pattern + SDP correlation (PRE_REG_027)
Among OECD high-income peer countries, military-spending-share is **negatively** correlated with homelessness reduction; public-housing-spend-share is **positively** correlated with homelessness reduction. Pearson r |≥ 0.3| in either direction.

### Prediction set C — US is structural outlier on multiple dimensions
US is in the top quartile of military-spending-share AND bottom quartile of public-housing-spending-share AND top quartile of homelessness rate among OECD peers. (Triple-position outlier prediction.)

### Prediction set D — Case study reallocation matches predicted directions
- Costa Rica 1948: post-reallocation outcomes (life expectancy + education + democracy continuity) exceed Latin American peers. **Predicted ≥ 5 percentage points or 5 years on key metrics.**
- Mauritius 1968: post-reallocation GDP per capita and life expectancy exceed African peers within same income range.
- Peace dividend countries: cross-country variation in 1990s allocation choices correlates with post-2007 homelessness rate variation.
- Finland Housing First: post-2008 homelessness rate declines (sustained) — predicted ≥ 30% decline by 2024 from 2008 baseline.

### Prediction set E — SDP residue-class structure exists
US states cluster into 2-5 "homelessness regimes" based on dominant channel signatures (parallel to Paper 2 disaster regimes; Paper 4 conflict types).

### Prediction set F — Methodology portability (H4)
LOO-CV or WAIC of residue-class-aware SDP model outperforms no-typology baseline model (parallel to Paper 6 IDP test). **Predicted ΔLOO ≥ 5.**

---

## 4. Falsifiers

- **F1 (channel-orthogonality fails)**: US SDP < 50% of state-years show single-channel dominance → orthogonality doesn't transfer; methodology partially walked back for SDP
- **F2 (cross-country pattern absent)**: no correlation (|r| < 0.1) between spending allocation and homelessness rate among OECD peers → revealed-preference claim weakens substantially
- **F3 (US not outlier)**: US falls within OECD peer interquartile range on military / housing / homelessness metrics → "US structural outlier" claim walked back
- **F4 (case studies don't match)**: ≥2 of 4 case studies (Costa Rica, Mauritius, peace dividend, Finland) show outcomes opposite predicted direction → reallocation narrative walked back
- **F5 (residue-class structure absent)**: US states don't cluster meaningfully (1 cluster only, or random clustering) → SDP residue-class claim walked back
- **F6 (methodology doesn't transfer)**: residue-class-aware SDP model does NOT outperform baseline → Paper 6 methodology-portability claim walks back for SDP domain

F1 + F6 firing together = methodology doesn't transfer to SDP → walk back H4. SDP framework remains as descriptive coining; analytical machinery doesn't apply.

F3 + F4 firing together = US-outlier + case-study narratives both walk back → H2 (force = revealed-preference) substantially weakens. SDP framework retained as definitional; substantive content reframes.

H3 (equivalence-as-question) **doesn't have a falsifier** — it's a research question, not a hypothesis. Whatever the empirical answer, H3 is "answered" not "falsified."

---

## 5. Methodology

### Data acquisition required
- HUD Annual Homeless Assessment Report (PIT counts) 2007-2024
- Eviction Lab Princeton (eviction filings + judgments) 2000-2024
- ACS housing cost-burdened share
- SIPRI Military Expenditure Database 1949-2024
- OECD Social Expenditure Database (SOCX) 1980-2024
- OECD Affordable Housing Database (post-2007 standardized homelessness)
- World Bank development indicators (education + healthcare + life expectancy)
- Finland: ARA + Finnish Government Housing First reports

### Test sequence
1. Phase 1: data acquisition + cross-country comparison table
2. Phase 2: case study writeups (Costa Rica, Mauritius, peace dividend, Finland)
3. Phase 3: channel-orthogonality (PRE_REG_026) + spending-outcome correlation (PRE_REG_027)
4. Phase 4: residue-class clustering + methodology portability test

---

## 6. Risk acknowledgments (locked at pre-reg time)

- Causation cannot be established with this framework; explicitly dropped
- Latin American homelessness data not directly comparable to OECD; Costa Rica case uses non-homelessness outcomes
- Maastricht 1992 confounder named in peace dividend case
- "Voluntary" operationalized strictly to exclude coerced reallocations (Japan, etc.)
- Political claim (war-vs-welfare framing) is separable from empirical framework; presented in implications section, not framework definition

---

## 7. Cross-references
- Papers 2 + 4 + 6 (methodology source)
- PRE_REG_004 (IDP channel-orthogonality reference)
- PRE_REG_022 (forthcoming — Paper 6 Stan residue-class IDP test)
- PRE_REG_026 (forthcoming — SDP channel-orthogonality)
- PRE_REG_027 (forthcoming — spending-outcome correlation)
- PRE_REG_028 (forthcoming — Finland Housing First case study)

## 8. Provenance
Locked 2026-05-27 as framework-definitional pre-reg. Subsequent empirical pre-regs will operationalize specific tests.
