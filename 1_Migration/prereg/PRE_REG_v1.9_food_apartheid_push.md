# Pre-Registration v1.9 — Food-Apartheid Migration Push (race-stratified gravity arm)

**Type:** New arc (third push axis). Additive; all prior arms (demographic, geographic, v1.7 taxonomy, v1.8 net-livability field) stand.
**Authored:** 2026-05-28
**Status:** LOCKED before fitting. Commit hash recorded at lock.

## Motivation

v1.8 Stage A falsified the net-livability field: no race-pooled economic gradient (ΔN, ΔINC, ΔRENT, Δμ) beats gravity on the MIGPUMA corridor cube — gravity (mass + distance) ate everything (`field_real_and_singular = false`). The food-apartheid hypothesis is a different claim and a popular one: that the structurally/racially produced denial of food access is itself a **migration push**, visible in flows. The key move vs Stage A: **food apartheid is racial structure, so if a push exists it lives in race-specific corridors and a race-pooled model washes it out.** This arm therefore stratifies flows by race and asks whether food-scarce/redlined **origins over-emit** — and crucially whether they over-emit *more for the racialized group than for White flows*.

Scope (locked by user): food scarcity is a push on **observable migration flows**, NOT a homelessness terminus. This dissolves the food↔homelessness reverse-causality/simultaneity confound — homelessness is not in this model. It extends the net-livability field arm; it is not the SDP funnel.

## Instruments (origin-fixed; durable structural measures preferred for a push role)

Per origin MIGPUMA (2010 vintage), population-weighted from component tracts:

- **FARA** — low-access share (USDA Food Access Research Atlas 2019, structural distance-to-supermarket). The *continuous* underlying low-access measure, NOT the LILA whitelist flag (which bakes in income → double-counts precarity into its own gate).
- **HOLC** — redline share (1930s grade D, and C+D, from Mapping Inequality via the 2010-tract crosswalk). Maximally exogenous: a 1930s grade cannot be reverse-caused by 2010s flows (90-yr gap = the temporal firewall).
- **mRFEI** — DEFERRED (not on disk; needs CDC 2011 tract pull). When pulled, enters as the *contemporary readout* of apartheid, not as an exogenous push driver (retail composition follows departures → endogenous to flow).

## Cube and windows

Same MIGPUMA gravity cube as v1.8 Stage A. Between-MIGPUMA corridors, train 2012–2017 / holdout 2018–2021, corridors with race-group flow ≥ 50. Flows re-derived race-tagged: RACE+HISPAN joined onto the locked event layer by (YEAR, SERIAL, PERNUM). Race groups (collapse): NH-White, NH-Black, Hispanic(any race), NH-Asian/PI, NH-AIAN, NH-Other/Multi. Race-specific masses = window-mean residence population by race per MIGPUMA.

## Models (Poisson GLM, log link, exposure offset = window years, origin-MIGPUMA-clustered SE), fit SEPARATELY per race group g

```
M0_g  (gravity):   log E[flow_od] = a + b·log(mass_o^g) + c·log(mass_d^g) + d·log(dist)
M1_FARA_g:         M0_g + β_F · FARA_lowaccess(origin)
M1_HOLC_g:         M0_g + β_H · redline_share(origin)        (HOLC-covered origins only)
```

β > 0 ⇔ food-scarce / redlined origins **over-emit** beyond size and distance = the push.

## Falsifiers (pre-registered decision rules)

- **FOODPUSH_F1 — signal.** β significant (p < 0.01, clustered) AND > 0 in the highest-power race group, in BOTH train and holdout. Fails → no food push in observed flows (gravity dominates, as Stage A predicts for the pooled case) → primary hypothesis FALSIFIED.
- **FOODPUSH_F2 — the apartheid signature (the one that matters).** β larger for the racialized group than for NH-White: require β_Black > β_White (and/or β_Hispanic > β_White), gap outside overlapping 95% CIs. **If β is statistically equal across race**, the push is generic place-decline, NOT food apartheid → downgrade to race-neutral (and likely just gravity noise). This is the falsifier that separates "apartheid pushes the group it was built against" from "poor places lose people."
- **FOODPUSH_F3 — held-out transfer.** Train coefficients predict holdout sign + significance for the highest-power group. GEO_F4 already showed dynamic structure does not transfer here, so this is a live risk. Caveat: 2020 race-recode affects the 2021 holdout year.
- **FOODPUSH_F4 — instrument coherence.** On HOLC-covered origins, FARA-push and HOLC-push agree in direction. Incoherence (cf. Probe C's negative HOLC×LILA coupling at D:/Food Deserts) → flag, do not average.

## Verdict logic

Food apartheid is a **real, racially-differential migration push** ⇔ FOODPUSH_F1 fires-correctly AND FOODPUSH_F2 fires-correctly (racial differential present) AND FOODPUSH_F3 does-not-fail. Any other pattern → report exactly which clause broke. Most-likely prior (from Stage A): F1 null in the pooled/aggregate sense; the entire live bet is the race-stratified F2.

## Known limitations (logged pre-fit)

- **HOLC covers only 1930s-graded cities** → HOLC arm restricted to graded urban origins, not national. Probe C (D:/Food Deserts) found HOLC×LILA negative/counter-intuitive — prior null to respect; redlining instruments not promised to behave.
- **FARA on disk is 2019 single-vintage** → used as a time-invariant origin trait for 2012–2021 (defensible *only because* the structural claim is that access geography is durable; it is an assumption, logged).
- **2020 race/Hispanic recode** (Census questionnaire change) → train (2012–17) clean; holdout (2018, 2019, 2021) includes the 2021 recode — caveat for F3 race transfer.
- **ACS post-move blindness** still removes the desperate tail (same wall as rent-desperation). This arm is scoped to *observable completed-move flows* — the claim is "visible flows follow the food-apartheid pattern," NOT "all food-pushed people are captured."
- Origin food term is origin-fixed → identified off cross-origin variation in over-emission, race-differenced.

## Next (not this pre-reg)

mRFEI contemporary-readout arm once the CDC 2011 tract file is pulled. Culture-war sorting as a competing explanation for the flow residual is being tested separately (user); if F2 nulls it is the natural alternative, and if F2 fires it is a confound to control.
