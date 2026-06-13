# Pre-Registration 032 — Gentrification Dynamics + What Drives Rent Demand

**ID:** PRE_REG_032
**Locked:** 2026-05-28
**Substrate:** PRE_REG_031 (metro mediation CONFIRMED: rent is the displacement funnel; demand dominates supply ~3×; income shows suppression = gentrification signature)
**Status:** LOCKED — design + thresholds pre-committed BEFORE building the CoC time-panel / demand-driver data and BEFORE any coefficient inspection.

---

## 0. Why this pre-reg exists

PRE_REG_031 found, cross-sectionally at metro level, that income/demand → rent → homelessness is the dominant pathway, with an income-**suppression** signature (income inflates rent → homelessness, but is directly protective at fixed rent). **That is the statistical fingerprint of gentrification: higher-income demand bids up rent and displaces incumbents even as average income rises.** But cross-section ≠ a test of the dynamic process. This pre-reg does two things:

1. **Confirm the dynamic** (gentrification is within-place, over-time): does *rising* rent/income within a CoC drive *rising* homelessness?
2. **Find the next answer — what drives rent demand?** Decompose the demand side: which upstream forces (job growth, in-migration, high-wage industry, population growth) drive the rent that drives displacement?

Honest stance: correlational; ordering (demand-driver → rent/income → homelessness) locked by timescale; "gentrification" used as the mechanism label for the income-suppression displacement pattern, not a neighborhood-level claim (HUD homelessness is CoC-level only — the block-by-block displacement core of gentrification is not measurable here; flagged).

---

## 1. Hypotheses

**H1 (dynamic gentrification — within-place displacement):** Within CoCs over time (CoC fixed effects + year FE, and long-difference 2012→2024), rising rent and rising income are associated with rising homelessness. The cross-sectional 031 pattern persists *within places over time*, not just across them.

**H2 (demand drivers — WHAT DRIVES RENT DEMAND, the new frontier):** A demand-driver block — employment/job growth, in-migration rate, high-wage-industry share, population growth — predicts rent (and the income/demand pressure). Identify which driver dominates.

**H3 (gentrification-specific signature):** CoCs where rent rises *faster than local incomes* (rent-to-income worsening — newcomers outbidding incumbents) show larger homelessness increases than CoCs where rent and income rise together.

---

## 2. Pre-locked thresholds

| Hypothesis | SUPPORTED | FALSIFIED |
|---|---|---|
| **H1** dynamic | within-CoC FE: Δrent or Δincome coef on homelessness p<0.05 correct sign; AND long-difference concurs | **F1**: within-CoC coefs n.s. → cross-section was a between-place confound, no dynamic displacement |
| **H2** demand drivers | demand block predicts rent (panel R²≥0.30 within); ≥1 driver p<0.05 correct sign | **F2**: no driver significant → rent demand exogenous/unexplained by these |
| **H3** rent-outpaces-income | the rent>income-growth group shows larger Δhomelessness (p<0.05) | n.s. → no incumbent-outbidding signature |

Panel inference: CoC + year fixed effects, SE clustered by CoC. Long-difference as the clean cross-confound check.

---

## 3. Data

**CoC time-panel (2012–2024):**
- Homelessness: HUD PIT by CoC (have, all years).
- Rent + income: ACS county→CoC aggregated per year (1-yr for large CoCs; 5-yr endpoints for long-difference). Mediator/treatment time series.

**Demand-driver block (the new pull):**
- **Employment / job growth:** BLS LAUS county employment (or QCEW) → CoC.
- **Wage / high-wage industry:** BLS QCEW average weekly wage + industry mix (info/tech/finance share) → CoC.
- **In-migration:** IRS SOI county-to-county migration inflows (available locally at D:/Migration) → CoC; and/or ACS migration.
- **Population growth:** Census B01003 Δ → CoC.

**Outcome:** homeless_per_10k (CoC); robustness unsheltered_per_10k.

---

## 4. Pre-conditions
1. CoC time-panel: ≥120 CoCs with ≥6 years of rent+income+homelessness.
2. Demand drivers: ≥120 CoCs with employment + in-migration + population coverage; flag any block unobtainable (e.g., if QCEW industry too granular, use employment+wage only).
3. Long-difference endpoints (2012, 2024) both present for ≥120 CoCs.
Failures redlined.

## 5. Robustness (ROBUST n/4)
1. FE panel vs long-difference (2012→2024)
2. Outcome homeless_per_10k vs unsheltered_per_10k
3. Demand drivers with vs without the COVID years (2020–2021)
4. Drop top-5 metros — dynamic not megacity-driven

## 6. Causal / selection guards
- Correlational; ordering by timescale (demand drivers → rent/income medium-run → homelessness fast).
- Reverse causality: homelessness could deter in-migration (minor); FE + lagged drivers mitigate; flagged.
- ACS overlapping 5-yr windows attenuate first-differences → prefer 1-yr for panel changes, 5-yr only for long-difference endpoints; noted.
- Gentrification is sub-CoC (neighborhood); CoC-level can only test the metro dynamic, NOT block displacement. Locked limitation.

## 7. Cross-references
PRE_REG_031 (metro mediation; income suppression), PRE_REG_029/030, P7-P migrant bridge (external displacement) — gentrification is the INTERNAL/domestic displacement engine, conceptual parallel to IDP economic-force displacement.

## 8. Provenance
Locked 2026-05-28 before CoC time-panel + demand-driver data built and before coefficient inspection. 031 cross-section seen; dynamic within-place + demand-driver decomposition NOT yet fit. First fit after §4 pre-conditions.
