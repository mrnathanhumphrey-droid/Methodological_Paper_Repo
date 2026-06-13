# Pre-Registration: PBP Score-Margin × Possession Outcome Lever
## Garbage-time vs Clutch Residual Variance Asymmetry

**Date filed:** 2026-05-07
**Filed before:** any inspection of game-state-partitioned PBP residuals
**Status:** Tier-1 hypothesis, single-test α = 0.05 (no Bonferroni since pre-registered)

---

## 1. Hypothesis

**Tier-1 prediction.** For volume stats (PTS, REB, AST), per-minute rate residuals are *wider* in garbage-time game states than in clutch game states, for the cohort of players with substantial minutes in both states.

**Direction is specified** as a positive variance ratio: σ(residual_garbage) / σ(residual_clutch) > 1.0.

**Mechanism stated ex ante.** Garbage-time minutes are dominated by bench / late-rotation / minute-load-management decisions that are not captured in the v6.1 LOCKED projection architecture. Coaches manage rotations differently in blowouts: starters rest, bench players play extended runs, defenders lock onto stat-chasers, etc. The unmodeled variance in *who plays under what role-context* should manifest as wider residual-rate dispersion in garbage-time than in clutch-time, where rotations are tighter, role assignments are more deterministic, and coaching decisions are more uniform across teams.

This is a residual-class structural prediction in the framework's vocabulary (Sections 3, 5.2): the garbage-time game state acts as a residue class whose σ-shift differs from the clutch class, in the same way that position cells (Section 5.4.5) have shifted variance relative to non-position cells.

## 2. Game-State Definitions

States are evaluated at the per-event level on the PBP stream and then integrated to per-player per-game per-state minute totals and event counts.

**Clutch state** — per the NBA Stats canonical definition:
- Time remaining in 4th quarter or any OT < 5:00, AND
- Absolute score margin ≤ 5

**Garbage-time state** — pre-registered explicit definition:
- Time remaining in any quarter < 5:00, AND
- Absolute score margin > 20

**Neutral state** (residual category, not tested):
- All other in-game minutes

## 3. Cohort

**Inclusion criteria** (locked):
- Test season: 2024-25 (most recent complete season with PBP data)
- Player must have ≥ 5 games played in the test season
- Player must have ≥ 30 cumulative minutes in clutch state
- Player must have ≥ 30 cumulative minutes in garbage-time state

The dual-state minimum ensures both residuals are estimated on stable per-minute samples.

## 4. Per-Player Per-Game Per-State Residuals

For each player p, game g, state s ∈ {clutch, garbage}, where minutes_s(p,g) ≥ 1:
- count_s(p,g) = stat events of player p during state s minutes in game g
- rate_s(p,g) = count_s(p,g) / minutes_s(p,g)

Player baseline rate (computed across the test season):
- r_bar(p) = total_count(p) / total_minutes(p) (per-minute, all states pooled)

State residual:
- residual_s(p,g) = rate_s(p,g) − r_bar(p)

## 5. Statistical Test

For each stat S ∈ {PTS, REB, AST}:
- Pool residual_clutch(p,g) values across all p,g pairs in cohort
- Pool residual_garbage(p,g) values across all p,g pairs in cohort
- Compute σ_clutch and σ_garbage
- Compute variance ratio = σ_garbage / σ_clutch
- Levene's test (median-centered) on the two residual distributions
- Pre-registered single test, α = 0.05 (no Bonferroni; this is one Tier-1 prediction)
- Bartlett's test reported as supplementary (sensitive to non-normality)
- F-test two-sided reported as supplementary

## 6. Decision Rules

**CONFIRMED (any stat):** Levene's p < 0.05 AND ratio > 1.0 in the predicted direction. The Tier-1 prediction is confirmed for that stat.

**NULL (any stat):** Levene's p ≥ 0.05 OR ratio ≤ 1.0. The Tier-1 prediction is not confirmed for that stat.

**Aggregate verdict across three stats:**
- 3/3 confirm: strong support for residual-class structure on the score-margin axis
- 2/3 confirm: partial support; flag the non-confirming stat for follow-up
- 1/3 confirm: weak signal; report honestly, treat as not confirmed
- 0/3 confirm: Tier-1 NULL; report as pre-registered failure with same prominence as positive findings (parallel to Section 5.3 Probe Tier-1 NULL)

## 7. Tier-2 Replication (Conditional)

If 2024-25 produces 1+ confirms, replicate on 2023-24 (prior season) under identical operationalization. Tier-2 replication outcomes:
- Confirms in 2+ stats in both seasons: published as cross-season replication
- Confirms in 2024-25 only: report as single-season finding pending further replication
- Does not confirm in 2023-24: NULL replication; honest framing in writeup

## 8. What Does NOT Count

- Post-hoc threshold adjustment (e.g., score margin > 15 instead of > 20). Thresholds are locked.
- Stat-specific p-value cherry-picking (e.g., reporting only the confirming stats without the failures).
- Cohort redefinition (e.g., dropping the 30-minute floor) after seeing residuals.
- Switching from variance test to mean test if variance fails.
- Adding new states (e.g., "early-clutch" or "moderate margin") and testing them as if they were Tier-1.

Any of the above invalidates the pre-registration. Findings under modified protocols are reported separately as exploratory observations.

## 9. Exploratory Tier-2 (Non-Pre-Registered)

The following may be examined *after* the Tier-1 result is reported, and are explicitly labeled exploratory:
- Score-margin gradient: 5-bucket variance ratio analysis (margin 0-5, 5-10, 10-15, 15-20, 20+)
- Position × state interaction: do the variance ratios differ by Center vs non-Center?
- Quarter × state interaction: are 4Q clutch vs 1Q-clutch-like rotations comparable?

These do not displace the Tier-1 finding; they support follow-up question framing only.

## 10. Output Artifacts

Will be written to `audit_runs/pbp_garbage_clutch/`:
- `cohort.csv` — list of qualifying players + their per-state minute totals
- `residuals_per_game.csv` — per-player per-game per-state residual table
- `tier1_test_results.csv` — Levene's / Bartlett's / F-test results per stat
- `summary.md` — one-paragraph honest verdict

## Sign-Off Required Before Firing

This pre-registration is filed but not yet committed for analysis. Analysis fires only after the user signs off on the operationalizations in Sections 2-5. After sign-off, this file is locked; any subsequent modification invalidates the pre-registration discipline and the analysis becomes exploratory only.

**Filed by:** automated pre-reg writer
**Sign-off requested from:** user (mr.nathanhumphrey@gmail.com)
