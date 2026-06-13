# Pre-Registration — v6.1 LOCKED Re-Scoring under Adjudicated Position Bucketing

## Sloan Test 2: MAE Delta on the 46 Forward → Center Flip Cohort + 230-Player Adjudication Cohort

**Date filed:** 2026-06-02
**Filed before:** any inspection of per-player or aggregate MAE on the adjudicated re-scored projections. The metadata-bucketed v6.1 LOCKED MAE numbers (`paper_draft/production_application/v6_1_postmortem_session2_locked.md` Table 1: locked PTS MAE 1.8203 / AST MAE 0.6428) are visible and locked. The adjudicated-bucket-derived per-player projections have not been computed.
**Status:** Sloan-grade Tier-1 pre-registration. Single document covering one Tier-1 hypothesis (MAE_metadata > MAE_adjudicated on the 46 F→C flip cohort, four observables PTS / REB / AST / BLK), one secondary hypothesis (MAE delta on the full 230-player adjudication cohort), one structural validation (per-player named-table comparison for 8 priority players), and one power gate.
**Sloan paper:** *Partial pooling of residual classes: theory, application to basketball projections, and measurable noise-floor reduction* (working title), draft state at `paper_draft/section_5_empirical_validation.md`. This pre-registration extends §5.4 (NBA position-vs-career-stage asymmetry) and §6 (practical implications / front-office decision relevance, currently a stub) with the MAE-delta arm.
**Cross-paper anchors (inputs, all read-only):**
- NBA v1.2 adjudication artifact: SHA256 `eb615269f09159e0d0ceaf071812b84750578d81a9a53b01dff5a1ac2ac9dcbd` (locked under commit `1bfdb4c`).
- Sloan adjudicated Test 1: pre-reg commit `e52505f`, results commit `3919406`.
- Sloan cross-league adjudicated Test 1: pre-reg commit `28e3dc7`, analysis commit `4a4a595`.

---

## 1. Why this exists

Sloan adjudicated Test 1 (`e52505f`, results `3919406`) established that the metadata Center mis-bucketing of 46 modern NBA bigs (Davis, Antetokounmpo, Love, Plumlee, Porziņģis, Olynyk, Powell, Gibson + 38 others) was driving the cross-league §5.4.1 REB × Center walk-back: under adjudicated bucketing, all 3 NBA cells flipped from WALK-BACK UPHELD to WALK-BACK FALSIFIED at p < 1e-5. The cross-league extension (`4a4a595`) showed the same falsification at WNBA + NCAA M + NCAA W, for a 10/10 walk-back falsification across all four leagues.

That work was a VARIANCE-RATIO TEST on residuals computed under the existing v6.1 LOCKED predictions. The §5 guard #8 prohibited any v6.1 re-fit. The locked argument was: *under the metadata bucket, the v6.1 LOCKED model treats AD/Giannis/etc. as Forward, and the Center × REB variance signature gets diluted into the non-Center pool*. The variance ratio test caught this dilution. But the test did NOT directly demonstrate that the v6.1 LOCKED predictions themselves are systematically biased for these 46 players. It demonstrated that the residual VARIANCE structure was inconsistent with the metadata partition.

This pre-registration extends the analysis to the predictions themselves. Specifically: v6.1 LOCKED conditions on position in three places, identified by source-code grep `2026-06-02`:

1. **Additive offset:** `apply_v6_1_locked_offsets_2025_26.py:6` — `VALIDATED_OFFSETS["PTS"]["position"]["Center"] = -0.587`. Every Center player's PTS prediction is shifted by -0.587 relative to the Stan posterior mean.
2. **Variance multipliers:** `apply_v6_1_locked_offsets_2025_26.py:11-13`:
   - `("REB", "position", "Guard"): 0.723` (tightens REB variance for Guards)
   - `("AST", "position", "Forward"): 0.819` (tightens AST variance for Forwards)
   - `("BLK", "position", "Guard"): 0.662` (tightens BLK variance for Guards)
   - These affect the SD of the predictive distribution, which matters for log-likelihood and uncertainty intervals but NOT for the point MAE. They are reported as supplementary.
3. **Stan hierarchical level:** `hierarchical_aging_quadratic_v4.stan:30, 56, 84, 95-96, 123, 148-157` — `mu_position[player_position[p]]` is the per-position mean rate, `beta_age_pos / peak_age_pos / gamma_pos` are position-specific aging-curve parameters. The Stan posterior's predicted mean for player `p` depends on `player_position[p]`. Changing `player_position[p]` from Forward to Center for the 46 flip players moves their predicted means to draw from `mu_position[Center]` + Center-specific aging instead of `mu_position[Forward]` + Forward-specific aging.

**Re-scoring is NOT a re-fit.** The Stan posterior chains stay at their existing snapshot. The `VALIDATED_OFFSETS` and `VARIANCE_MULTIPLIERS` stay at their existing values. The only thing that changes is the categorical input `player_position[p]` for the 46 flip players, which selects WHICH locked posterior column / WHICH locked offset row applies. This is the exact same re-scoring operation the Sloan adjudicated Test 1 variance ratio used to define Center vs non-Center group membership — just now extended from "which group's variance does this player contribute to" to "which group's mean prediction applies to this player."

The pre-reg-e52505f §5 guard #8 ("the model does not condition on position") was based on the assumption that v6.1's position dependence was confined to the variance multipliers (which only affect variance, not the point MAE the cross-league paper §5.4 reports). The source-code grep shows position is ALSO in the Stan posterior's hierarchical level and the PTS additive offset. The pre-reg e52505f stands as written (its variance-ratio test was correct under the residual-from-existing-predictions framing), but this is a new analysis testing a different question: do the predictions themselves improve under adjudicated bucketing?

The decision-theoretic / front-office relevance: if v6.1 LOCKED is producing systematically biased projections for 46 NBA bigs (because it conditions on the wrong position bucket), then any front office using v6.1 for trade valuation, lineup construction, or contract evaluation is operating with biased estimates on those players. The MAE delta is the size of that bias.

## 2. Locked operationalizations

### 2.1 Substrate scope

- **Test seasons:** 2024-25 + 2025-26 NBA regular season. Two seasons, matching the Stan-vet cohort and full-ship cohort respectively (the cohort framework from cross-league paper §5.4 / Sloan e52505f §2.1). The 2023-24 season is NOT in scope because it pre-dates v6.1 LOCKED's training window (v6.1 was fit on 2019-20 through 2023-24); 24-25 is the first holdout season for v6.1.
- **Cohort A — Flip cohort (load-bearing):** the 46 NBA players whose v1.2 adjudication flipped from metadata-Forward to adjudicated-Center. Identified by `metadata_bucket_v1 == "Forward" AND adjudicated_bucket == "Center"` in `position_adjudication_v12.json`. Filtered per season to players who qualified for v6.1 LOCKED's published cohort (top-200 Stan vet pool for 24-25; full ship n=567 for 25-26).
- **Cohort B — Full adjudication cohort (secondary):** the full 230 adjudicated players from v1.2, regardless of flip direction. Reported as a no-cherry-pick comparison.
- **Cohort C — Non-flip adjudication cohort (sanity check):** the 184 adjudicated players whose metadata and adjudicated buckets agree. MAE delta on Cohort C should be approximately zero (no position change means no re-scoring delta). Used as a calibration check that the re-scoring pipeline is correct.
- **Observables (locked):** PTS, REB, AST, BLK — four per-game stats. PTS load-bearing because the additive offset directly conditions on it; REB load-bearing because the Stan posterior `mu_position[Center]` differs from `mu_position[Forward]` most strongly there; AST and BLK reported for completeness and to prevent selective reporting.

### 2.2 v6.1 LOCKED re-scoring procedure

The re-scoring uses the existing v6.1 LOCKED parameters verbatim — no re-fit. Source-of-truth:

- **Stan posterior:** the chains and posterior draws produced by the Stan fit logged at v6.1 lock event (2026-05-05). For the 46 flip players, re-extract per-game predicted means using `player_position = Center` instead of the metadata's `Forward`. All other Stan inputs (player random effect `mu_player`, age, season, hierarchical hyperparameters) are unchanged. The re-extraction uses the same posterior draws and the same predict function; only the categorical position column changes.
- **Additive offsets (`apply_v6_1_locked_offsets_2025_26.py`):** the existing `VALIDATED_OFFSETS` dict is applied post-Stan. For the 46 flip players, the dict's lookup key changes from `("PTS", "position", "Forward")` (which has no entry → no offset applied) to `("PTS", "position", "Center")` (which has `-0.587` → applied). Same dict, different lookup keys for the 46 flip players.
- **Variance multipliers (`VARIANCE_MULTIPLIERS`):** same dict, different lookup. For BLK and AST, the multipliers change per flip player (e.g., `("AST", "position", "Forward"): 0.819` no longer applies; `("AST", "position", "Center")` has no entry → multiplier 1.0). Reported as supplementary; not load-bearing for the point MAE.

The re-scored projection for player p, game g, stat S is:
```
mu_adjudicated(p, g, S) =
    Stan_posterior_mean(p, g, S | player_position[p] = adjudicated_bucket[p])
    + VALIDATED_OFFSETS.get((S, "position", adjudicated_bucket[p]), 0.0)
    + (other non-position offsets, identical to metadata version)
```

The variance side `sigma_adjudicated(p, g, S)` uses `VARIANCE_MULTIPLIERS.get((S, "position", adjudicated_bucket[p]), 1.0)`. Reported as supplementary.

For the 184 Cohort C players whose adjudicated bucket equals the metadata bucket, `mu_adjudicated == mu_metadata` by construction (no flip means no re-scoring change). This is the calibration check.

### 2.3 Per-player MAE

For each (player p, season s, stat S):
- `actuals(p, s, S)` = per-game observed value for stat S in season s, restricted to the player's GP ≥ 10 cohort qualifying games.
- `MAE_metadata(p, s, S)` = mean( | actual(p, g, S) - mu_metadata(p, g, S) | ) over qualifying games g in season s.
- `MAE_adjudicated(p, s, S)` = mean( | actual(p, g, S) - mu_adjudicated(p, g, S) | ) over the same games.
- `Delta_MAE(p, s, S) = MAE_metadata(p, s, S) - MAE_adjudicated(p, s, S)`. Positive = adjudicated improves.

### 2.4 Aggregate MAE per cohort

For each (cohort, season, stat) cell:
- `MAE_cohort(cohort, s, S, arm) = mean( MAE(p, s, S, arm) | p in cohort, p qualifying in season s )`.
- `Delta_cohort(cohort, s, S) = MAE_cohort(metadata) - MAE_cohort(adjudicated)`. Positive = adjudicated improves.
- **Bootstrap 95% CI on Delta_cohort: B = 1,000 resamples**, cluster on player (resample players with replacement, compute Delta on each bootstrap cohort). Seed = `20260602` (one day later than e52505f / 28e3dc7 to identify provenance).
- **Paired Wilcoxon signed-rank test** on per-player `MAE_metadata(p) - MAE_adjudicated(p)`, restricted to qualifying players in the cohort. Two-sided p-value reported.

### 2.5 Power gate (pre-committed)

For each cohort × season cell:
```
n_qualifying_players ≥ 8
```

Below 8 qualifying players (e.g., if Stan vet 24-25 cohort intersects Flip cohort thinly), the cell is POWER-LIMITED INCONCLUSIVE.

For 25-26 full ship, Flip cohort should have approximately 30-35 qualifying players (the 46 flip players minus the few who didn't play 24-25 / 25-26 with GP ≥ 10).

## 3. Tier-1 Hypothesis

### 3.1 H1 — Flip cohort REB MAE delta

The load-bearing claim. v6.1 LOCKED with metadata bucketing assigns the 46 flip players to Forward, which under the Stan hierarchical level draws their predicted REB mean from `mu_position[Forward]` (lower than `mu_position[Center]`). Their actuals are high (they ARE on-court Centers), so residuals are positive on average → MAE is inflated by the position-bucket-induced mean bias. Re-scoring with adjudicated Center bucket draws from `mu_position[Center]` → predicted REB mean is higher → residuals shrink → MAE drops.

**Per-cell decision rule:**

| Condition | Disposition |
|---|---|
| `Delta_cohort(REB, season) > 0` AND CI95 lower bound > 0 AND Wilcoxon p < 0.05 | **MAE-PERSISTS** — adjudicated re-scoring reduces REB MAE, statistically significant. |
| `Delta_cohort(REB, season) > 0` AND CI95 lower bound ≤ 0 | **DIRECTIONAL** — point estimate positive but CI brackets zero. |
| `Delta_cohort(REB, season) < 0` AND CI95 upper bound < 0 AND Wilcoxon p < 0.05 | **REGRESSES** — adjudicated re-scoring increases MAE. Surprising; would suggest the metadata bucket was actually closer to a useful prediction for these players' REB. Walk-back of the §5.4.1 falsification interpretation. |
| `Delta_cohort(REB, season)` CI brackets zero | **NULL** — re-scoring does not measurably improve REB MAE despite the §5.4.1 walk-back falsification. The variance signature was real but the mean-prediction shift is too small to detect at this cohort scale. |
| Power-limited per §2.5 | **INCONCLUSIVE**. |

**Pre-committed magnitude thresholds:**
- `Delta_cohort(REB, season) ≥ 0.15 REB/game`: "large MAE reduction" — directly Sloan-talk-worthy.
- `Delta_cohort(REB, season) ∈ [0.05, 0.15)`: "small-to-medium MAE reduction" — reportable but less load-bearing.
- `Delta_cohort(REB, season) ∈ (0, 0.05)`: "marginal" — direction correct but small.
- `Delta_cohort(REB, season) ≤ 0`: not improving.

**Aggregate H1 verdict (across 2 seasons):**
- 2/2 MAE-PERSISTS + ≥ 0.15 magnitude in both → **HEADLINE.** The 46-player flip cohort REB MAE under adjudicated bucketing is materially smaller; v6.1 LOCKED produces measurably biased REB projections for these players under metadata bucketing.
- 2/2 MAE-PERSISTS + ≥ 0.05 in both → strong supporting finding.
- 1/2 MAE-PERSISTS → mixed, paper reports both cells.
- 0/2 MAE-PERSISTS or any REGRESSES → §5.4.1 walk-back falsification stands as a variance result without a mean-prediction-improvement claim. Paper framing reverts to "variance signature is real, point prediction unchanged."

### 3.2 H2 — Flip cohort PTS / AST / BLK MAE delta

Same decision rule as H1, applied to PTS / AST / BLK.

PTS has a direct -0.587 additive offset under Center that under Forward bucketing doesn't apply. If the 46 flip players' actual PTS averages closer to the (Stan_Forward - 0.587) Center prediction than the unshifted Stan_Forward prediction, MAE drops.

AST and BLK shift through the Stan `mu_position` term only (no additive offset). Effect size is expected smaller than REB.

All cells reported regardless of disposition.

### 3.3 H3 — Cohort B (full 230 adjudication cohort) MAE delta

Same decision rule as H1 / H2, applied to the full 230-player cohort.

Pre-committed: H3 deltas should be SMALLER than H1 / H2 deltas, because the 184 non-flip players contribute zero delta by §2.2 construction. Specifically, H3 deltas should be approximately `(46/230) × H1 deltas + noise`.

If H3 deltas are NOT approximately `(46/230) × H1`, the re-scoring pipeline has a bug: either Cohort C (non-flip) is producing non-zero deltas, or H1 deltas are not internally consistent with H3 aggregation.

### 3.4 H4 — Cohort C (184 non-flip adjudication cohort) MAE delta — pipeline integrity check

Per §2.2 construction, `Delta_cohort(Cohort C, season, S) ≡ 0` exactly. Reporting non-zero delta in Cohort C is a pipeline bug that invalidates H1 / H2 / H3. Detection rule: any |Cohort C delta| > 1e-6 in any cell triggers a pipeline bug investigation and the analysis does NOT proceed to disposition reporting until the bug is fixed.

## 4. Named-player projection comparison tables

A per-player tabular report covering the 8 priority players from the Sloan paper §5.4.1 narrative:

| Player | Metadata bucket | Adjudicated bucket | Stat | 25-26 mu_metadata | 25-26 mu_adjudicated | Delta (predicted) | 25-26 actual mean | MAE_metadata | MAE_adjudicated |
|---|---|---|---|---|---|---|---|---|---|
| Anthony Davis | Forward | Center | REB | (to fill) | (to fill) | (to fill) | (to fill) | (to fill) | (to fill) |
| ... etc for Giannis, Love, Plumlee, Porziņģis, Olynyk, Powell, Gibson × {PTS, REB, AST, BLK} × {24-25, 25-26 where they have ≥ 10 GP} |

All 8 × 4 stats × 2 seasons = 64 reportable cells (minus cells where the player doesn't qualify). Reported regardless of magnitude; selective reporting forbidden per §5 guard #5.

## 5. Discipline guards

1. **Threshold adjustment after firing.** The magnitude thresholds [0.05, 0.15] for REB, the Wilcoxon p < 0.05 cutoff, the power gate n ≥ 8, and the per-cell decision rules are locked. Adjusting any after compute is a violation.
2. **Classifier redefinition.** The 46 flip cohort is read verbatim from `position_adjudication_v12.json` (artifact SHA256 `eb615269...`). Re-running the v1.2 adjudication, re-judging any verdict, or modifying the override map is a violation across both papers and this sub-pre-reg.
3. **v6.1 LOCKED re-fit forbidden.** No Stan re-sampling, no offset re-validation, no variance multiplier re-tuning. The re-scoring uses the existing posterior draws + existing dict values verbatim.
4. **Cohort cap adjustment.** The Stan-vet 200 cap for 24-25 and full ship n=567 for 25-26 match the cross-league paper protocol. Removing the cap to fish for more qualifying flip players is a violation.
5. **Selective reporting.** All cells reported: 4 stats × 2 seasons × 3 cohorts (A=46 flip, B=230 full, C=184 non-flip) = 24 reportable cells. Cohort C is the pipeline integrity check (expected zero by construction); reporting only Cohort A would mask any bug in C.
6. **Magnitude threshold definition.** The 0.15 / 0.05 REB/game thresholds are derived a priori: 0.15 is approximately 10% of an NBA Center's typical 1.5-2 REB/game intra-game residual SD; 0.05 is approximately 3% of same. These thresholds are pre-committed; not re-tunable after seeing the data.
7. **No adding observables.** PTS / REB / AST / BLK are locked. Adding STL or TOV after seeing patterns requires a new pre-reg.
8. **Fleet independence.** No subagents needed for this work (re-scoring is deterministic given v6.1 LOCKED + adjudication artifact). The fleet-independence guard is preserved for cross-paper consistency but not load-bearing here.
9. **Pipeline integrity gate.** §3.4 H4 enforces zero delta on Cohort C before §3.1-§3.3 dispositions are reported. Bypassing this gate is a violation.
10. **Pre-reg-e52505f compatibility.** This sub-pre-reg does NOT modify, retract, or amend `e52505f`. The variance-ratio result stands at its committed values (NBA Test 1 BLK 3/3 PERSISTS, REB 3/3 WALK-BACK FALSIFIED). H1 of this sub-pre-reg tests a different question (point prediction MAE) on the same cohort.

## 6. Output artifacts

All under `D:/NBA Projections/RMD_SRC_PIPELINE/results/sloan_mae_delta/`:

- `per_player_projections_metadata.parquet` — re-scored predictions under metadata bucket for the 230 adjudicated players across 24-25 + 25-26 + 4 stats.
- `per_player_projections_adjudicated.parquet` — same shape, adjudicated bucket.
- `per_player_mae_table.parquet` — per (player, season, stat, arm) MAE.
- `cohort_aggregate_mae.parquet` — per (cohort, season, stat) MAE + Delta + bootstrap CI + Wilcoxon p.
- `dispositions.json` — per-cell disposition per §3 decision rules.
- `named_player_tables.md` — the §4 Sloan-talk comparison table.
- `SLOAN_MAE_DELTA_RESULTS.md` — umbrella report with aggregate verdict and front-office framing for §6 of the cross-league paper.
- `pipeline_integrity_check.md` — Cohort C zero-delta verification (must show |delta| < 1e-6 in all 8 cells).

## 7. Timing and commitment

- **Lock event:** git commit of this file to NBAProjections `main`, commit SHA recorded in `RMD_SRC_PIPELINE/SHA_LOCK.txt` under a `## Sloan MAE delta Test 2 v1.0` section.
- **Re-scoring fires:** once, after sign-off. Single batch, deterministic. The Stan posterior re-extraction uses the existing posterior draw matrices; the offsets + multipliers use the existing dicts.
- **Analysis fires:** once, immediately after re-scoring artifacts written.
- **No re-runs.** Methodological flaws → new pre-reg (v1.1), not re-fire.
- **No v6.1 re-fits.**
- **Final report:** `SLOAN_MAE_DELTA_RESULTS.md` produced after analysis. Headline disposition feeds the paper §6 front-office decision relevance subsection.

## 8. Sign-off

- **Filed by:** Claude Code (claude-opus-4-7[1m])
- **Sign-off requested from:** mr.nathanhumphrey@gmail.com
- **Repo:** https://github.com/mrnathanhumphrey-droid/NBAProjections
- **Cross-paper anchor SHAs (input):**
  - NBA v1.2 adjudication artifact + commit: `1bfdb4c` + SHA256 `eb615269...`.
  - Sloan adjudicated Test 1 pre-reg + results: `e52505f` + `3919406`.
  - Sloan cross-league adjudicated Test 1: `28e3dc7` + `4a4a595`.
  - v6.1 LOCKED apply_offsets script: `scripts/apply_v6_1_locked_offsets_2025_26.py` at HEAD `1e2080b` (this session's most recent commit).
  - v6.1 LOCKED Stan model: `models/skill/stan/hierarchical_aging_quadratic_v4.stan` at HEAD `1e2080b`.
- **Lock event:** rename this file (already drafted under the `_LOCKED.md` suffix; lock event is the git commit of this exact path). Append commit-SHA to `SHA_LOCK.txt` under a `## Sloan MAE delta Test 2 v1.0` section.

---

**End of draft v1.0.**
