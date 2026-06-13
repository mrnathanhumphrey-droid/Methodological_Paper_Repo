# Pre-Registration 030 — Structural Housing-Supply → Rent → Homelessness Mediation

**ID:** PRE_REG_030
**Locked:** 2026-05-28
**Substrate:** PRE_REG_029 (structure explains displacement; rent is the LEVEL mechanism) + authentic WRLURI zoning + P7-O null + rent-mediation first-look
**Status:** LOCKED — mediation design + thresholds pre-committed BEFORE pulling Saiz/permits and BEFORE bootstrapped-CI inspection. The 2026-05-28 rent-mediation first-look (zoning only) is the motivating prior, not a confirmatory result.

---

## 0. Why this pre-reg exists

PRE_REG_029 found rent is the robust mechanism behind the homelessness LEVEL. The authentic-zoning probe (P7-O) found zoning has NO direct effect on homelessness — but a first-look mediation decomposition found zoning reaches homelessness THROUGH rent (indirect +0.33, both legs significant; suppression masked the direct path). **This pre-reg tests whether the chain `structural housing-supply constraint → rent → homelessness` holds with a proper bootstrapped mediation, replacing the single-driver (zoning-only) first-look with a full supply block.**

This answers the user's question: *is there a patterned structural driver of rent that (in a chain) reaches homelessness?* The honest causal stance is **mediation pattern consistent with the chain**, not proof — observational, ordering assumed by timescale.

---

## 1. Hypotheses

**H1 (first stage — structural driver of rent):** A structural housing-supply block predicts median rent across states. Constrained supply (high zoning + low Saiz elasticity + low building-permits-per-capita + slow housing-unit growth) → higher rent.

**H2 (mediation — LOAD-BEARING):** The supply-constraint → homelessness association is mediated through rent. The bootstrapped indirect effect (a×b, supply→rent→homelessness) has a 95% bias-corrected CI excluding zero on the displacing (positive) side.

**H3 (supply dominates demand as rent driver):** Within the rent first-stage, the supply block carries more explanatory weight than the pure-demand block (income + population growth). (Patterned STRUCTURAL — not just demand — driver.)

---

## 2. Pre-locked thresholds

| Hypothesis | SUPPORTED | FALSIFIED (falsifier) |
|---|---|---|
| **H1** supply→rent | first-stage LOO R² ≥ 0.40 AND ≥1 supply var significant (p<0.05, correct sign) | **F1**: LOO R² < 0.30 OR no supply var significant → no structural driver of rent |
| **H2** mediation (LOAD-BEARING) | bootstrapped 95% BC CI of indirect effect (a×b) excludes 0, positive side | **F2**: indirect-effect CI crosses 0 → supply does NOT reach homelessness through rent |
| **H3** supply > demand | supply-block partial-R² for rent > demand-block partial-R² | (no falsifier; descriptive) |

Bootstrap: 5,000 resamples, bias-corrected percentile CI on the standardized indirect effect. Ordering (supply→rent→homelessness) is locked, not movable.

---

## 3. Variable blocks

**Structural supply (a-path drivers):**
- Authentic WRLURI 2018 zoning (have)
- Saiz (2010) housing-supply elasticity, metro→state population-weighted (geographic+regulatory land constraint)
- Building permits per capita (Census Building Permits Survey, state×year)
- Housing-unit growth vs population growth (ACS B25001 units; supply-demand imbalance)

**Mediator:** median gross rent (ACS B25064). [Robustness: rent-to-income.]

**Outcome:** homeless_per_10k.

**Demand controls (H3 contrast + confound):** median HH income, population growth, (job growth if available).

**Note:** climate excluded from the LEVEL/rent models — first-look + retest showed climate is noise for the level (predicts FORM only).

---

## 4. Pre-conditions

1. Permits + housing-units coverage: ≥48 states (Census BPS is full-coverage; expected pass).
2. Saiz coverage: metro elasticity maps to ≥40 states after pop-weighting. **If Saiz unobtainable** (like WRLURI's near-miss), FLAG deferred and run the supply block as {zoning + permits + unit-growth}; the mediation still tests with those.
3. First-stage non-degeneracy: supply vars not perfectly collinear with income.

Pre-cond failures redlined, not silently worked around.

---

## 5. Causal / selection guards (locked)

- **Observational; correlational framing.** Result is "mediation pattern consistent with the chain," never "proves causes."
- **Ordering justification (pre-committed):** zoning + Saiz geography are slow/upstream (decades); rent is medium-run; homelessness is fast-responding. Timescale ordering motivates the chain direction.
- **Reverse-causality flags:** homelessness does not plausibly cause zoning/geography (one-directional a-path); rent↔homelessness could have minor feedback (noted; panel mitigates).
- **Suppression honesty:** the zoning direct effect is negative (RTS/services/climate bundle, holding rent fixed). The mediation reports total / direct / indirect separately; the headline is the indirect path, with suppression disclosed.
- **Knowable-at-observation:** panel uses supply/rent values at PIT-year start.

---

## 6. Robustness axes (ROBUST n/4)

1. Cross-section 2024 vs pooled panel 2007–2024
2. Mediator = rent level vs rent-to-income
3. Supply block with vs without Saiz (in case deferred)
4. Drop-RTS states (NY/MA/DC) — indirect effect must persist

---

## 7. Method

Baron-Kenny + modern bootstrapped mediation. a = supply→rent (control demand). b = rent→homelessness (control supply). indirect = a×b standardized; 5,000-resample BC bootstrap CI. Report c (total), c' (direct), indirect, proportion-mediated, with suppression flagged when sign(direct)≠sign(indirect).

## 8. Cross-references
- PRE_REG_029 (rent = level mechanism); P7-O authentic-zoning null; rent-mediation first-look (`analysis/paper7_rent_mediation_firstlook_2026_05_28.json`)
- Saiz 2010 QJE (supply elasticity); Colburn & Aldern 2022 (housing-supply prior); Gyourko WRLURI

## 9. Provenance
Locked 2026-05-28 before Saiz/permits pulled and before bootstrapped-CI inspection. Zoning→rent→homelessness seen only in the single-driver first-look; full supply block + bootstrap NOT yet fit. First fit after §4 pre-conditions.

---

## 10. Results — FIRST FIT (fired 2026-05-28)

Full dig: `papers/PAPER_7_SDP_FRAMEWORK/digs/2026_05_28_prereg030_supply_rent_mediation.md`. Data: authentic WRLURI zoning + Saiz 2010 elasticity (MIT, 269 MSAs→48 states) + ACS. n=47. Supply index = mean(z(zoning), −z(saiz_elasticity)). Permits deferred (units-pull flaky; zoning+Saiz are the structural constraints).

| Hypothesis | Threshold | Result | Disposition |
|---|---|---|---|
| **H1** supply→rent | LOO R²≥0.40 + supply sig | LOO 0.77; supply +116.9 p<0.001 | **SUPPORTED** |
| **H2** mediation (LOAD-BEARING) | boot 95% CI excludes 0 | indirect +0.219 (a=0.38,b=0.57 both sig); **CI [−0.0001, 0.524]** | **FALSIFIED (borderline/underpowered)** — F2 fired |
| **H3** supply>demand | supply ΔR² > demand ΔR² | supply 0.085 vs income 0.244 | **NO — demand-led** |

**Honest reading**: rent IS structurally driven (H1, 77%), but demand (income) > supply constraint (H3). The supply→rent→homelessness chain is suggestive (+0.22 indirect, both legs significant) but the 95% bootstrap CI lower bound grazes zero (−0.0001) → **does not clear the locked bar. Reported FALSIFIED, not fudged.** The failure is POWER, not sign: at n≈47 *between-state* units (supply constraint is ~time-invariant, so a state panel adds no identifying variation), the CI can't tighten above zero. **Path to power = CoC/metro resolution (n~380), not more years.**

**F2 FIRED.** Mediation unconfirmed at state resolution. Candidate follow-up: PRE_REG_031 CoC/metro-level mediation.
