# Forward-validation spec: v6 retargeted to 22-23

## Why

The Collatz protocol delivered a LOO-validated -1.48% composite MAE improvement
on the 23-24 ship cohort using parsimonious top-1-class-per-stat offsets. LOO
is honest *within* a season, but the offsets are derived from 23-24 residuals
themselves. The truly independent test is:

> Derive offsets from 22-23 residuals. Apply to 23-24 projections. Measure delta.

If the 23-24 lift survives (composite -1.0% to -1.5%, even with shrinkage),
the protocol generalizes across seasons and the v6.1 spec is ship-ready.

If the lift collapses (composite ~ 0% or worse), the per-class effects are
season-specific noise we'd been fitting in-sample, and the result was a false
positive — bullet dodged.

## What to fire (gate: explicit "fire it" required)

### Step 1: Build v6 22-23 ship CSV

This requires a chain of pandas wrappers + the upstream v4-lite NB2 PTS Stan fit.
Outputs:
  `audit_runs/unified_ship_v6_2022-23/per_player_projections_2022-23.csv`

The chain:
  v4-lite NB2 fit (Stan) -> v3 -> v4 -> v5 -> v6
With these constants swapped:
  TARGET_YEAR  = 2022     (was 2023)
  PRIOR_SEASON = "2021-22" (was "2022-23")

Each script in `scratch/_ship_v3_*.py`, `_ship_v4_*.py`, `_ship_v5_*.py`,
`_ship_v6_*.py` needs:
  - SAVE_DIR retargeted to `audit_runs/unified_ship_<v>_2022-23/`
  - Input CSV path retargeted to the prior step's 2022-23 output
  - The Stan PTS fit retargeted to `season=2021-22` for prior, `season=2022-23` for actuals

Estimated runtime: v4-lite NB2 fit is the long step (~30-90 min). Pandas wrappers
are seconds.

**THIS IS A FIT. NOT TO BE FIRED WITHOUT EXPLICIT CONFIRMATION.**

### Step 2: Run forward_validation.py

Once `unified_ship_v6_2022-23/per_player_projections_2022-23.csv` exists, the
application script (`scripts/forward_validation.py`) runs in seconds:

  1. Loads 22-23 ship CSV + 22-23 actuals (from box scores)
  2. Computes per-stat residuals for the 22-23 cohort
  3. Attaches class features (position, age_bucket, offseason_traded,
     years_pro_bucket, draft_pick_tier, career_mpg_tier, chronic_bucket)
     **as of the 22-23 season** (not 23-24)
  4. Runs noise-floor SNR test per (stat, class)
  5. Picks top-1 class per stat at SNR>=1.5 (Collatz parsimony rule)
  6. Computes class mean residuals (not LOO — these become "external" offsets
     when applied to 23-24)
  7. Loads 23-24 ship CSV
  8. Attaches 23-24 class features for each player
  9. Looks up offset by class value, applies to projection
  10. Compares MAE on 23-24 actuals: baseline vs offset-corrected
  11. Reports per-stat deltas + composite

  Critical: features for 23-24 cohort use the 22-23-derived OFFSET TABLE
  but classify each player by their 23-24 class membership. (E.g., a player
  who was age 28 in 22-23 and 29 in 23-24 still gets bucketed correctly per
  their 23-24 age.)

### Step 3: Decision

| 23-24 composite delta | Read |
|---|---|
| < -1.0% | Strong forward generalization. Ship v6.1 with offset table. |
| -0.3% to -1.0% | Moderate — offsets shrink across seasons but persist. Ship with shrinkage factor 0.5-0.7. |
| -0.3% to +0.3% | Wash — offsets are season-specific. Don't ship. |
| > +0.3% | Anti-correlation — offsets actively hurt forward. Reject. |

Each (stat, class) offset can also be inspected individually:
- Did `offseason_traded x PTS` (SNR 3.92 in 23-24) replicate in 22-23?
- Did `position x BLK` replicate?
- Did `years_pro x TOV` replicate?

A ship-spec is the SUBSET of (stat, class) combos that replicate across both seasons.

## Files involved

  scripts/forward_validation.py        - to be written, consumer
  audit_runs/unified_ship_v6/per_player_projections_2023-24.csv - 23-24 ship (exists)
  audit_runs/unified_ship_v6_2022-23/per_player_projections_2022-23.csv - 22-23 ship (TO BUILD)

## Architectural priors retained

1. Per-stat residuals (not MPG residuals) — see direction-of-effect diagnostic
   confirming cascade compensation across all 8 stats with player-level
   Pearson r ranging -0.39 to -0.75.
2. Top-1 class per stat at SNR>=1.5 — multicollinearity from summing correlated
   classes destroyed -1.34% into +7.30% in the 8-class expansion test.
3. LOO is sufficient within-season honesty; cross-season is the real proof.
