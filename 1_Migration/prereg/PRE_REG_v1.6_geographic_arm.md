# Pre-Registration v1.6 — Geographic Arm ("America as Mini-Countries")

**Type:** New analysis arm (additive). Does NOT amend or replace the demographic arm (v1.0–v1.5); that result stands.
**Authored:** 2026-05-28
**Status:** LOCKED v1.6-final, 2026-05-28 ("lock v1.6 + fire"). Full 4-cube, RMD-SRC moment-flow primary + all layers, between & within, divisions + states, power-gated. GEO_F1–F4 accepted as drafted. State-level 4-cube moments flow/gravity-only (data-density boundary). Demographic-arm Step-4 round-2 remains separately open.

## Motivation (diagnostic-driven, not result-driven)

The demographic arm found distance and density **decomposition-resistant** under a demographic ℙ₀ (Step-4 round 1: 0/47 clean on distance and density; 4a/4b/4c all failed across 38 species). The diagnosis: that structure is **geographic**, not demographic — migration distance follows a gravity law (origin/destination masses, distance), and the short/long bimodality is **within-mini-country vs between-mini-country**, which cuts across every demographic cell. No demographic slice can isolate it.

This arm re-partitions on geography ("America is mini-countries") to test whether the gravity dimension resolves when sliced and pooled on its natural axis. The demographic arm's findings (RMD-SRC captures the *sorting* dimension via opp_deficit: 48 boson / 41 fermion; decomposition-resistant on geography) are preserved and reported regardless of this arm's outcome.

## Scope: two resolutions, run separately

- **Divisions** — 9 Census divisions (the "mini-countries"), healthy cell sizes.
- **States** — 51 (50 + DC), the literal political analog, finer but sparser.
Each resolution is a separate, parallel analysis. State FIPS → division is a fixed Census mapping; no new data (every event already carries origin/destination state).

## The cube and cross matrices

**Cross matrix** = origin→destination flow matrix `T[i,j]` = PERWT-weighted migrant flow from unit i to unit j. **Diagonal = within** (intra-unit moves); **off-diagonal = between** (the long-distance gravity tail).

**Cube = full 4-cube `T[origin, dest, species, year]` at BOTH resolutions** (LOCKED per user: "full 4 cube, all of it"), built for **flows** (PERWT-weighted counts; counts tolerate sparsity and zeros are meaningful).
- **Divisions:** 9×9×38×10 = 30,780 cells (~32 events/cell avg).
- **States:** 51×51×38×10 = 988,380 cells (~1 event/cell avg).

**Hard estimability boundary (honest limit, not a design preference):** moment-flow (RMD-SRC Steps 1–3) needs n≥50 per cell. So:
- **Flows + gravity baseline:** computed on the full 4-cube at BOTH resolutions (valid everywhere).
- **Corridor moment-flow (mean/var of log_distance, log_dest_density, opp_deficit):** computed only in cells meeting n≥50 — a workable dense subset at **divisions**; at **states** the 4-cube is ~1 event/cell so moments are estimable in only a handful of dense corridors. State-level demographic structure is therefore carried by the **within-state runs** (below), and state-level between-structure by the 2D O-D flow matrix + gravity. This is reported as a resolution-dependent coverage map, not silently dropped cells.

**Companion moment cubes:** per cell meeting the n≥50 floor, store mean & variance of the three observables.

## Decomposition — primary RMD-SRC, all layers (LOCKED per user: "2 RMD SRC … ALL OF IT")

Primary method = **RMD-SRC moment-flow per corridor**; the other layers retained as supporting/exploratory (= "all of it").

1. **Gravity baseline (supporting, drives GEO_F1).** Poisson (log-linear) fit `flow_ij ~ log(mass_i) + log(mass_j) + log(dist_ij)`, per resolution, on the full 4-cube collapsed to O-D. mass = unit resident weight; dist = centroid great-circle. Record pseudo-R² + distance exponent γ.
2. **Residual cube.** observed − gravity-expected flow, per cell — structure beyond gravity.
3. **CP/PARAFAC tensor decomposition (exploratory)** of the residual species-cube at division resolution — the Anandkumar-2014 leg. Latent corridor/sorting factors + loadings.
4. **PRIMARY — RMD-SRC moment-flow per corridor.** Treat each O-D corridor cell (meeting n≥50) as an RMD-SRC cell; run Steps 1–3, i.e. the v1.0 pipeline with ℙ₀ = corridors. The within/between split (diagonal vs off-diagonal) and the divisions/states resolutions all flow through this.

   **Corridor observable (LOCKED, option A, operationalized):** the demographic observables (distance/density/opp_deficit) are corridor-CONSTANTS → degenerate at the corridor level. The corridor observable is instead the **gravity-residual flow, decomposed by species** to yield a within-cell distribution:
   - Per year t, refit gravity on between-unit flows → expected E_ij(t).
   - Species-expected E_ij,s(t) = E_ij(t) · p_s(t), p_s(t) = national share of species s among movers in year t.
   - Species residual r_ij,s(t) = log((O_ij,s(t)+ε)/(E_ij,s(t)+ε)).
   - **μ_ij(t) = mean_s r** (corridor over/under-performs gravity); **σ²_ij(t) = var_s r** (species-selectivity of the corridor).
   - Step-2 regimes on (μ,σ²): Stationary / Concentrating (species converging) / Diffusing (species diverging) / Fragmenting. Gradient-tracking N/A (no ∇g defined for corridors).
   - Between-corridors only (off-diagonal); diagonal/within flows go to the within-runs (Stage 3). Power-gated: corridor needs full training-window coverage and ≥10 species/yr with positive flow.

## Within: per-mini-country runs (pooling option c)

For each mini-country (each of 9 divisions; each of 51 states), run the **demographic** RMD-SRC pipeline (Steps 0–3) *separately on that unit's residents/events*, then compare leaf classifications **across** mini-countries. Tests whether the demographic sorting structure (boson/fermion) is homogeneous across the country or itself geographically heterogeneous ("mini-countries with different physics").

## Geographic-arm falsifiers

- **GEO_F1 (just gravity):** if the gravity baseline alone explains ≥ 80% of flow variance (pseudo-R²), the geographic structure is "just gravity" — no residual decomposition needed. Report and stop (the geographic analog of the classical disposition).
- **GEO_F2 (corridor decomposition-resistant):** if the residual tensor decomposition yields no stable, interpretable factors (reconstruction below a pre-registered floor, or factors not replicable across a split), the gravity dimension resists structured decomposition.
- **GEO_F3 (within-vs-between inconsistency):** if the within-mini-country demographic runs and the between-mini-country corridor structure imply contradictory mechanisms on ≥ 30% of units.
- **GEO_F4 (predictive transfer):** corridor factors / leaf classifications fit on training 2013–2017 should predict 2018–2021 holdout (κ ≥ 0.4 + accuracy sanity, mirroring the demographic F4).

## Minimum cell sizes

Flows (counts): no floor (zeros are meaningful). Corridor **moments**: n ≥ 50 events/cell (matches §2.8). Cells below the moment floor are flagged, used for flows/gravity only.

## Governing principle (user, 2026-05-28): "all of it that has the statistical strength"

Build the full comprehensive apparatus, but **gate every estimate on statistical power**: a cell/factor/fit is computed and reported only where it meets its pre-registered floor (moments n≥50; tensor factors must replicate; gravity fit always valid on counts). Cells below floor are shown on a coverage map, never silently filled. No estimate is produced where the data can't support it.

## Locked design (user-confirmed 2026-05-28)

1. Cube — **full 4-cube** `origin × dest × species × year`, both resolutions; flows everywhere, moments where n≥50 (coverage map reported; state 4-cube is flow/gravity-only).
2. Decomposition — **RMD-SRC moment-flow primary** + gravity baseline + CP tensor (all layers).
3. **Both** between (cube) **and** within (per-mini-country demographic runs).
4. Resolutions — **divisions (9) and states (51)**, separately.

## Remaining sign-off

- GEO_F1–F4 thresholds (80% gravity pseudo-R²; tensor factor stability; 30% within-vs-between inconsistency; κ≥0.4 holdout) — accept as drafted or adjust.
- The one honest limit: state-level 4-cube moment-flow is not estimable (~1 event/cell); acknowledged, handled via within-state runs + 2D O-D/gravity. OK?

Reply "lock v1.6 + fire" to build the geographic arm. The demographic arm's Step-4 round-2 (to formally close F2) remains separately open.
