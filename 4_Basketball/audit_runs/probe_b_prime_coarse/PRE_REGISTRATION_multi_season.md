# Pre-registration — Probe B multi-season replication prediction

**Date written:** 2026-05-05
**Status when written:** Multi-season Stan chain (24-25 + 23-24, PTS/REB/AST) was kicked off ~30 min ago. ETA ~6-9h. Residuals from those backtests do not yet exist. This file is dated and committed before any multi-season residual analysis is run.

## Why this exists

Probe B (648 configs) returned 0/15 hits at p<0.05; Probe B′ (72 configs) returned 2/24 nominal hits, neither surviving Bonferroni. Both nominal hits in B′ share a coherent contextual theme:

- `top_record_tier + early_season + home`
- (rookie_Guard / PTS, p=0.044, outlier `top_top_early_home`)
- (vet_Center / REB, p=0.028, outlier `mid_top_early_home`)

This shared theme is structurally interpretable: facing currently-elite opponents in October-November at home is the cell where (a) opponent quality is highest, (b) opponent effort is highest (no tanking, full motivation early in season), and (c) venue effects favor the home team. It is the joint-context configuration where mismatch from baseline-rate projections would be most expected on first principles.

Two-of-twenty-four nominal hits is well within the false-positive rate at α=0.05 (1.2 expected). The shared theme is suggestive but absolutely could be drift inside the multiple-comparison noise. Without pre-registration, a multi-season replication that re-flagged this theme would look like cherry-picking; a multi-season replication that did NOT flag it would not be recorded as a miss.

This document fixes the prediction in advance.

## The prediction

**Hypothesis:** If contextual residue-class structure beyond v6.3-A exists and is detectable at multi-season pooled resolution, the configuration cluster anchored on `top_record_tier + early_season + home` has the highest prior probability of beating strict gates (Bonferroni-corrected α and k* ∈ [4,16]).

**Specifically:**
- The OUTLIER cluster in Probe B/B′-style hierarchical agglomerative clustering on multi-season-pooled v6.3-A residuals will, with prior probability higher than chance, contain configurations sharing the `top_record_tier + early_season + home` theme.
- The strongest such hits are most likely to appear in **Guard cohorts (rookie or vet)** for **PTS**, and in **Center cohorts (vet)** for **REB** — the same combinations that B′ flagged at single-season resolution.

**Other configurations are tested without prior expectation.** Hits anywhere else in config space are treated as exploratory and require their own correction.

## Test protocol (locked here, run when multi-season residuals land)

When the 24-25 and 23-24 Stan backtests complete and residuals are available:

1. **Pool residuals** across 23-24, 24-25, and 25-26 (3 seasons). Apply v6.3-A-style per-player conjugate update on each season's residuals using prior-season K_prior; project to test season; compute residuals = actual − projection.

2. **Re-tag residuals** with the same Probe B′ 72-config space: `opp_class (4) × record_tier (3) × season_phase (3) × home_away (2)`. Same axis derivations: 24-25 final D-rating quartile for `opp_class` (per season's prior season), rolling current win pct for `record_tier`, calendar phase + last-20 for `season_phase`, `is_home` from box scores.

3. **Run cohort × stat clustering** on the pooled-residuals: same hierarchical agglomerative + average linkage, same combined distance (z-norm d_moment + d_phi)/2, same k ∈ {2, 4, 6, 8, 10, 16, 32, 50}, same 500-rep bootstrap.

4. **Two-tier reporting:**
   - **Tier 1 — pre-registered:** test whether the outlier cluster at k*=2 (or any sub-cluster at k*∈[4,16]) is dominated by configurations sharing `top_record + early + home`. Count: how many of the cluster's configs share that theme? Compute conditional probability vs random theme-membership. Report at α=0.05 (single test, no Bonferroni — pre-registered).
   - **Tier 2 — exploratory:** every other cell × cohort × stat × config that beats Bonferroni-corrected α=0.05/n_cells. Reported separately.

5. **Decision rules:**
   - **CONFIRMED:** Tier-1 prediction beats α=0.05 AND at least one Tier-1 test beats k* ∈ [4,16] gate. Multi-season pooling enabled detection of the prediction. Sloan paper §6 lifts from "null at one season" to "detectable at three pooled seasons; structural finding."
   - **DETECTED-BUT-WRONG-LOCATION:** Bonferroni-survived hits exist BUT outside Tier-1's predicted theme. Sloan paper §6 reports "different residue-class structure exists than the one we pre-registered" — itself a finding.
   - **NULL:** No hits beat Bonferroni at multi-season either. Pre-registered prediction did NOT pan out. Sloan paper §6 reports "single-season null replicates at multi-season; contextual residue-class structure not detectable in NBA box-score-only axes at the resolution tested." This is the negative-as-finding outcome.

## What counts as a "hit on the predicted theme"

Define a config string sharing the theme = matches all three of:
- `record_tier == "top"` (current-season top-tier opponent, rolling)
- `season_phase == "early"` (calendar pre-2026-02-14 AND team_game_n ≤ 62 — for the test season)
- `home_away == "home"`

Across all 4 levels of `opp_class` (top/high/mid/bottom), this defines exactly **4 of 72 configurations** that match the theme. Random expected fraction in any cluster = 4/72 = 5.6%.

A hit on the theme = a cluster (size n_cluster ≥ 2 to count) where ≥ 50% of its configs match the theme. Random probability of this happening in any single cluster (under uniform random cluster assignment) ≤ 4!/(72·71·70·...) for small clusters, which is << α=0.05 for clusters of size 2-4.

## Caveats

- Multi-season Stan run uses 200 players × 400/400 warmup/sampling per stat × 3 stats × 2 seasons. If posterior diagnostics (Rhat, ESS, divergences) are bad, that's documented and the analysis is run anyway — but flagged.
- 25-26 residuals are already available; 24-25 and 23-24 residuals require Stan completion. Estimated chain finish: ~late evening 2026-05-05 to early morning 2026-05-06.
- The cohort-widening hybrid v3 priors used for sophs/rookies in 25-26 don't apply cleanly to 23-24 / 24-25 (those cohorts had different rookie classes). Multi-season pool will be: vets (deep prior) + sophs (within-season prior + 24-25 H2 lever scaled to test season) only. Rookies excluded from multi-season pooling for clean comparison.
- Test-1 stats only (PTS/REB/AST). The 9 non-Test-1 stats are not in scope for this multi-season run, per the methodologically-sound A-vs-B scope decision: per-cohort γ on those 9 stats is engineering shrinkage not framework validation, so they don't gate paper claims.

---

## Pre-registered decision tree: Test 1 cross-season replication

Test 1 (mean-variance coupling) on 25-26 single season: PTS×Center, REB×Center, BLK×Center coupled at p<0.001; AST×13+ NOT coupled (variance ratio 1.05, p=0.64). The paper's load-bearing §2.5 finding.

Multi-season Stan replication will give us 23-24 and 24-25 residuals on the same cells. Outcomes locked here BEFORE data arrives:

### A. Full replication (the dream)
**Definition:** 3 of 4 cells confirm at p<0.05 in BOTH 23-24 and 24-25, same sign, magnitudes within ~30% of 25-26's values.

**Sloan paper response:** §5 lifts from "single-season blind validation" to "three-season cross-season replication." §2.5 gains a multi-season table. Test 1 is locked as a real structural finding. No walk-back needed; framework's headline is intact.

### B. Two-of-three replication (signal w/ year-to-year noise)
**Definition:** Same cells confirm in BOTH prior seasons but with different magnitudes (some >30% drift), or one cell drops to non-significance in one season but holds in the other.

**Sloan paper response:** §2.5 reports cell-by-cell stability table. Headline claim survives but is qualified: "Test 1 coupling is detectable across three seasons in 2-3 of 4 testable cells; cell stability varies by year, consistent with league-composition-driven year-to-year noise on a real underlying coupling." Publishable as-is, no walk-back, but framing softens.

### C. Same-direction-but-weaker (RTM on a real smaller effect)
**Definition:** Signs replicate across all 4 cells but magnitudes attenuate substantially (e.g., variance ratios in 23-24/24-25 land between 1.0 and 25-26's value, never matching). 25-26 was the high-water-mark season; prior seasons show the effect's smaller true value.

**Sloan paper response:** §2.5 reports the attenuation transparently. Headline becomes "Test 1 coupling exists but is smaller than 25-26 alone suggested; the mean of three seasons is the honest effect size." This is regression-to-mean on a real signal — the kind of correction that strengthens the paper by showing the team is calibrated, not weakens it. The framing is "the residue-class theorem operates; magnitudes are season-modulated."

### D. Sign-inconsistent or null in prior seasons (FAILURE mode)
**Definition:** Centers do NOT show variance compression in 23-24 OR 24-25 in the predicted direction. Variance ratios are at-or-near 1.0 (consistent with no coupling) or run the wrong sign.

**Sloan paper response:** Major walk-back. §2.5 cannot anchor on Test 1; the structural claim was 25-26-specific. Two paths:
   - **Walk back to honest exploratory framing**: "Test 1 was performed on 25-26 as the discovery season; cross-season replication did not confirm. We report the discovery and the failed replication." This is uncomfortable but it's what reviewers respect.
   - **Withdraw the structural-coupling claim from §2.5** and reframe the paper around v6.3-A's in-season-info finding (Probe A) + the engineering ablations (§6). The paper still ships, but the residue-class theory takes a backseat.

The decision between those two paths in scenario D depends on whether 24-25 OR 23-24 (single-season prior) shows ANY coupling — partial replication in one season but not the other = scenario B-ish; null in both = forced walk-back.

### What we are NOT pre-registering

- Effect sizes for cells that DID show structure in 25-26 (Centers × PTS/REB/BLK). We accept whatever multi-season values come back.
- The AST × 13+ "no coupling" finding — that's the asymmetry in Test 1; if AST × 13+ does NOT couple in any of 23-24/24-25, that REINFORCES the asymmetry, doesn't break it. We're predicting it stays uncoupled.
- New cells that weren't in 25-26 Test 1 (e.g., REB × Forward, AST × 4-7). Those are exploratory in multi-season and reported separately.

---

## Signature

Pre-registered before multi-season residuals exist.
- Local time: 2026-05-05 ~9:25am (multi-season Stan kicked off ~9:23am)
- Stan chain task ID: `bwc5be1x0`
- Probe B / B′ artifacts at: `audit_runs/probe_b_contextual_a_final/`, `audit_runs/probe_b_prime_coarse/`
- Stan run output expected at: `audit_runs/v4lite_PTS_2024-25/`, `audit_runs/v4lite_REB_2024-25/`, `audit_runs/v4lite_AST_2024-25/`, then 23-24 equivalents
