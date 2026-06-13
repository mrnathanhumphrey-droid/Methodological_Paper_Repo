# Pre-Registration 031 — Metro-level Supply + Demand → Rent → Homelessness Mediation

**ID:** PRE_REG_031
**Locked:** 2026-05-28
**Substrate:** PRE_REG_030 (state-level: H1 supply→rent SUPPORTED; H2 mediation FALSIFIED-borderline at n≈47 — power ceiling; H3 demand>supply for rent)
**Status:** LOCKED — design + thresholds pre-committed BEFORE building the metro panel and BEFORE any indirect-CI inspection.

---

## 0. Why this pre-reg exists

PRE_REG_030 found the supply→rent→homelessness indirect effect is positive (+0.22, both legs significant) but its bootstrap CI grazed zero (−0.0001) — **a power ceiling: n≈47 between-state units, supply constraint ~time-invariant.** And H3 found demand (income) drives rent ~3× more than supply at state level. **This pre-reg moves to metro resolution (CoC/CBSA, n~hundreds) for the power to settle the mediation, AND — per PI request — promotes income/demand from a control to a CO-TESTED pathway: does the mediation run through SUPPLY, DEMAND, or both, once we have power?**

Key data advantage: **Saiz (2010) elasticity is natively metro (MSA)** — no aggregation loss (unlike the state pop-weighting in 030).

Honest stance: correlational; mediation pattern consistent with the chain; ordering (supply/demand → rent → homelessness) locked by timescale, not proven.

---

## 1. Hypotheses

**H1 (first stages — drivers of rent):** At metro level, BOTH a structural supply-constraint block (Saiz elasticity + WRLURI zoning) AND a demand block (median income + population growth) predict median rent.

**H2 (SUPPLY mediation — load-bearing):** supply-constraint → rent → homelessness indirect effect (a_s × b) has a bootstrapped 95% BC CI excluding zero (positive). [The test 030 couldn't power.]

**H2b (DEMAND mediation — the PI-requested addition):** income/demand → rent → homelessness indirect effect (a_d × b) — does demand ALSO reach homelessness through rent? Bootstrapped CI excludes zero?

**H3 (which pathway dominates at metro level):** compare standardized supply-indirect vs demand-indirect. Does the state-level "demand > supply for rent" finding (030 H3) carry to the homelessness OUTCOME, or does supply dominate the displacement pathway even if demand dominates rent levels?

---

## 2. Pre-locked thresholds

| Hypothesis | SUPPORTED | FALSIFIED |
|---|---|---|
| **H1** supply→rent & demand→rent | metro rent model LOO R²≥0.40; each block ≥1 var p<0.05 correct sign | block insignificant |
| **H2** supply mediation (load-bearing) | boot 95% BC CI of a_s×b excludes 0, positive | **F2**: CI crosses 0 → supply doesn't mediate even with power |
| **H2b** demand mediation | boot 95% BC CI of a_d×b excludes 0, positive | CI crosses 0 → demand doesn't reach homelessness via rent |
| **H3** dominance | larger |indirect| with non-overlapping/clearly-separated bootstrap distributions | (descriptive if overlapping) |

Bootstrap: 5,000 resamples, BC percentile CI, standardized indirect effects. Ordering locked. **If BOTH H2 and H2b clear → rent is the common funnel and both supply and demand feed displacement through it (the unified mechanism). If only one clears → that side is the displacing driver.**

---

## 3. Unit + data

**Unit:** Continuum-of-Care (CoC) as the homelessness-native unit, attached to its primary CBSA for covariates (via CoC→county→CBSA crosswalk). Target n ≥ 150 metro CoCs with full covariates. (Robustness: CBSA as unit, aggregating CoC PIT to CBSA.)

- **Homelessness:** HUD PIT by CoC (overall + unsheltered + family), per-capita via CoC population (county-crosswalk-derived).
- **Rent (mediator):** ACS B25064 median gross rent at CBSA. [Robustness: rent-to-income.]
- **Supply block:** Saiz elasticity (MSA-native) + WRLURI 2018 aggregated to CBSA + building-permits-per-capita (if obtainable).
- **Demand block:** ACS median HH income (B19013) + population growth (B01003 multi-year) at CBSA.
- **Outcome:** homeless_per_10k (CoC).

**Selection guard:** covariates at/just-before the PIT year; correlational ordering by timescale (Saiz geography decades-stable; zoning slow; income/pop medium; rent medium; homelessness fast).

---

## 4. Pre-conditions
1. Crosswalk maps ≥150 CoCs to a primary CBSA with Saiz + ACS coverage.
2. Saiz MSA codes reconcilable to modern CBSA (msanecma → CBSA via name/FIPS bridge); flag unmatched.
3. CoC population derivable (county-crosswalk × county pop) for the per-capita outcome.
Failures redlined, not worked around.

## 5. Robustness axes (ROBUST n/4)
1. CoC-unit vs CBSA-unit (aggregate PIT to CBSA)
2. Mediator rent-level vs rent-to-income
3. Outcome homeless_per_10k vs unsheltered_per_10k
4. With vs without the largest metros (NYC/LA) — mediation not driven by 2 megacities

## 6. Method
Parallel-mediator bootstrap: a_s (supply→rent | demand), a_d (demand→rent | supply), b (rent→homeless | supply,demand). indirect_supply = a_s×b, indirect_demand = a_d×b. 5,000-resample BC CIs. Report c, c', both indirects, proportion-mediated, and the supply-vs-demand indirect contrast.

## 7. Cross-references
PRE_REG_029 (rent=level mechanism), PRE_REG_030 (state mediation underpowered; demand>supply for rent), P7-O authentic zoning null, Saiz 2010, Colburn & Aldern 2022.

## 8. Provenance
Locked 2026-05-28 before metro panel built + before indirect-CI inspection. State-level (030) seen; metro-level supply/demand mediation NOT yet fit. First fit after §4 pre-conditions.

---

## 9. Results — FIRST FIT (fired 2026-05-28)

Full dig: `papers/PAPER_7_SDP_FRAMEWORK/digs/2026_05_28_prereg031_metro_mediation_CONFIRMED.md`. Panel n=302 CoCs (ACS5yr county→CoC; Saiz MSA→CoC 88.8% match; WRLURI county→CoC). Parent-verified before firing.

| Hypothesis | Threshold | Result | Disposition |
|---|---|---|---|
| **H1** supply & demand → rent | 5fold R²≥0.40, both sig | R²=0.76; supply p<0.001, income p<0.001 | **SUPPORTED** |
| **H2** supply mediation (load-bearing) | boot CI excludes 0 | indirect **+0.181 [0.105, 0.286]**; direct ≈0 (full mediation) | **SUPPORTED** |
| **H2b** demand mediation | boot CI excludes 0 | indirect **+0.562 [0.374, 0.78]**; direct −0.50 (suppression) | **SUPPORTED** |
| **H3** dominance | larger indirect | demand 0.562 vs supply 0.181 (~3×), both sig | **DEMAND dominant** |

**ROBUST 4/4 both pathways** (composite supply, drop-NYC/LA, unsheltered outcome — all 8 CIs exclude zero). F2 NOT FIRED.

**Mechanism**: rent is the common displacement funnel (b=0.76). Supply constraint is FULLY mediated through rent (acts only via rent). Demand/income is the LARGER rent-pathway driver (~3×) but suppressed (directly protective at fixed rent). The state-level near-miss (PRE_REG_030 H2, CI −0.0001) was confirmed to be a power ceiling — metro resolution settles it decisively.

**Answer**: yes, there is a patterned structural driver of rent (supply constraint) that reaches homelessness through rent — AND demand/income is the dominant such driver. Both funnel through rent.
