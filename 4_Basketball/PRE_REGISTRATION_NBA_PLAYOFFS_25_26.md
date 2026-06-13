# Pre-Registration — NBA 25-26 Playoff Regime Extension

## Cross-Regime Test of Partial Pooling of Residual Classes at Playoff Scale

**Date filed:** 2026-05-10
**Filed before:** any inspection of 2025-26 NBA playoff per-game residuals (v6.1-conditional or cohort-mean), any cell-level statistic on playoff data, any PBP score-margin × possession partition on playoff games.
**Status:** Pre-registered methodology test — five Tier-1 hypotheses locked together as a single document. Effect-size primary at playoff scale; p-values secondary. No re-fits, no new offsets, no model tuning to playoff data.

---

## 1. Why this exists

The Sloan-conference-grade methodology paper (PAPER_STATE.md, 2026-05-08) has established cross-league cross-method replication of partial pooling of residual classes on regular-season data: 11/11 BLK × Center, 11/11 PTS × Center directional, REB × Center retracted under Stan robustness, AST × deep-vet null replicated cross-season + cross-league, and two pre-registered Tier-1 NULLs (Probe B contextual + PBP score-margin × possession cross-season).

This pre-registration extends that finding set into the **NBA playoff regime** — a within-sport regime shift where:

- Cohort sizes compress to single digits / teens per cell (vs n_in 21–224 in regular season)
- Rotations tighten from 9–10 to 7–8 deep, changing role-stability covariates
- Opponent quality is bracket-filtered and systematically higher
- Within-series coaching adjustments violate within-season stationarity assumptions
- Higher-stakes variance dynamics may activate or suppress structure differently than regular-season league-wide play

The framework's regular-season finding set either persists across this regime shift, weakens, partially regime-shifts, or falsifies. **All four outcomes are publishable.** The discipline of this pre-registration is that the test design is locked before any 2025-26 playoff data is touched for analysis — even though some playoff games have already been played as of 2026-05-10, the agent (Claude) committing this document has not inspected playoff residuals at any cell level.

This document cannot be amended after sign-off without invalidating the pre-registration discipline. Any additional tests run on playoff data after sign-off are exploratory and labeled as such.

## 2. Locked operationalizations

### 2.1 Playoff data scope

- **Season:** 2025-26 NBA playoffs only.
- **Inclusion:** all completed playoff games at analysis time. The analysis runs **once**, in a single batch, after the second round (Conference Semifinals) completes — approximately late May 2026, expected ~60–80 playoff games.
- **No rolling re-analysis.** Multiple-look discipline: one fit per prediction; if more playoff data accumulates after the analysis run, the additional games do not trigger re-analysis. They are reserved for any future pre-registered cycle.

### 2.2 Position classifier

Inclusive Test 1 protocol, exact match to Section 2.5 of the paper:

- **Center:** position string in {`C`, `C-F`, `F-C`}
- **Non-Center:** all other position labels in the playoff cohort (Guards, Forwards, Wings)
- Hyphenated boundary positions (`C-F`, `F-C`) classify as Center under the inclusive classifier, matching every Test 1 cell in the cross-league paper.

### 2.3 Years-pro buckets

- **Mid-season** (used in PTS × Center calibration cells): `years_pro` ∈ {6, 7, 8, 9, 10, 11, 12}
- **Deep-vet primary:** `years_pro ≥ 13`. Exact match to NBA cross-season Test 1 cell definition.
- **Deep-vet fallback:** `years_pro ≥ 10`, used **only** if the 13+ cell has n_in < 10 at analysis time. Aligns with WNBA surgical 10+ definition. **If the fallback triggers, both 13+ and 10+ results are reported; the 13+ result is primary, the 10+ result is supplementary.**

### 2.4 Player inclusion criteria

For Predictions 1–4 (per-game stat residuals):

- Player must appear in ≥ 3 playoff games at analysis time
- Player must average ≥ 10 minutes per playoff game (excludes garbage-time-only appearances and DNPs)
- Player's position string is non-empty and parseable under §2.2

For Prediction 5 (PBP score-margin × possession):

- Player must appear in ≥ 3 playoff games at analysis time
- Player must accumulate ≥ 15 cumulative minutes in clutch state across playoff games
- Player must accumulate ≥ 15 cumulative minutes in garbage-time state across playoff games

The 15-minute floors are scaled from the regular-season pre-reg's 30-minute floors at the ratio of typical playoff cumulative minutes to regular-season cumulative minutes (~50%). Scaling rationale is the data-physics difference between regimes; the floors are pre-registered before any inspection of playoff PBP. **If a stat's cohort fails the 15-minute floor for fewer than 8 qualifying players, the cell is reported as non-testable rather than null.**

### 2.5 Residual computation — dual baseline (Predictions 1–4)

Per the human-confirmed protocol, residuals are computed under **two baselines** for every cell, and both are reported:

**Baseline A — v6.1 LOCKED conditional re-score.**
For each playoff game (player p, game g, opponent o, minutes m_pg), the v6.1 LOCKED posterior is *re-scored* (not re-fit) conditional on the actual playoff minutes m_pg and opponent context o, producing a per-game expected stat E_v61(p, g). The residual is:

```
residual_v61(p, g, S) = actual_S(p, g) − E_v61(p, g, S)
```

**Critical constraint.** "Conditional re-scoring" means evaluating the locked v6.1 posterior with playoff covariates substituted into the existing model structure. **No re-fitting, no new offsets, no parameter updates from playoff actuals, no reshuffling of player-level random effects.** The v6.1 model's parameters are frozen at the 2026-05-05 final-lock snapshot. Per-game expectation conditional on opponent and minutes is a forward-pass computation using existing posterior samples; it does not constitute model tuning to playoff data.

**Baseline B — within-cohort mean.**
For each cell c (e.g., Center / non-Center) and each stat S, the cohort-mean baseline is:

```
r_bar_c(S) = mean_{(p,g) ∈ cell c, playoff games} actual_S(p, g) / minutes(p, g)
residual_cohort(p, g, S) = actual_S(p, g) / minutes(p, g) − r_bar_c(S)
```

Both baselines are computed independently. **A finding is robust only if the disposition (PERSISTS / WEAKENS / REGIME-SHIFT / FALSIFIED) agrees across both baselines.** Disagreement between baselines is itself a methodological finding — it indicates that the apparent coupling is sensitive to whether residuals are taken against a regular-season-trained model (potential regime-mismatch confound) or against playoff-internal cohort structure.

### 2.6 PBP residuals (Prediction 5)

Per-state per-player per-game rate residuals, mirroring the regular-season PBP pre-reg (`audit_runs/pbp_garbage_clutch_pre_reg/PRE_REGISTRATION.md`):

For state s ∈ {clutch, garbage} and game g:

```
rate_s(p, g, S) = count_S(p, g, s) / minutes_s(p, g)        [if minutes_s(p, g) ≥ 1]
r_bar(p, S)     = total_S_playoffs(p) / total_minutes_playoffs(p)
residual_s(p, g, S) = rate_s(p, g, S) − r_bar(p, S)
```

**Game-state definitions** (locked, identical to regular-season pre-reg):

- **Clutch:** time remaining < 5:00 in 4Q or any OT, AND |score margin| ≤ 5
- **Garbage:** time remaining < 5:00 in any quarter, AND |score margin| > 20
- **Neutral:** all other in-game minutes (not tested)

---

## 3. The five Tier-1 hypotheses

Each hypothesis specifies (a) prediction direction, (b) effect-size expectation derived from regular-season findings, (c) decision rule producing one of {PERSISTS, WEAKENS, REGIME-SHIFT, FALSIFIED}.

### Prediction 1 — BLK × Center coupling persistence

**H1.** The variance ratio of Center σ vs non-Center σ on per-game BLK residuals in the 25-26 NBA playoffs falls within the regular-season cross-league range **[1.26, 2.03]**.

**Mechanism stated ex ante.** BLK is the cleanest residual-class structural cell in the paper: 11/11 leagues × methods couple, magnitude consistent across two orders of magnitude in cohort size (n_in 21 → 224). The mechanism is structural — Centers carry shot-blocking variance that is not absorbed into position-mean structure under hierarchical pooling, and the residual-class variance shift is invariant to cohort size. If the framework's prediction is regime-stable, playoff-scale BLK × Center should remain in the same magnitude band even at compressed cohort sizes.

**Statistical test.**

- Compute σ_Center and σ_non-Center on BLK residuals (Baseline A, then Baseline B).
- Variance ratio = σ_Center / σ_non-Center.
- Bootstrap 95% CI on the ratio, B = 1000.
- Levene's test (median-centered) reported but not load-bearing at this n.
- Permutation null B = 1000 (relabel Center / non-Center, recompute ratio): report p_perm.

**Decision rule.**

| Condition | Disposition |
|---|---|
| Bootstrap CI overlaps [1.26, 2.03] | **PERSISTS** |
| CI overlaps coupling region (>1.0) but is fully below 1.26 | **WEAKENS** |
| CI brackets 1.0 (no clear coupling direction) | **REGIME-SHIFT** (toward null) |
| CI is fully below 1.0 (Center variance tighter than non-Center) | **FALSIFIED** (inversion) |
| CI is fully above 2.03 | **PERSISTS — INTENSIFIES** (sub-disposition reported) |

Both baselines must agree on disposition for the headline finding. Disagreement is reported as **BASELINE-SENSITIVE** with both dispositions noted.

### Prediction 2 — AST × deep-vet null persistence

**H2.** AST × deep-vet (pro-context, 13+ years) remains process-only in the 25-26 NBA playoffs. Variance ratio σ_13+ / σ_non-13+ overlaps 1.0; no significant coupling under Levene's test.

**Mechanism stated ex ante.** The regular-season finding is that pro-league career-stage axis is process-only at the AST cell, replicated 6/6 across NBA cross-season Test 1 + WNBA surgical 3-classifier matrix, with CF refinement confirming process-only at full Fourier resolution (0/4 higher moments significant, 0/201 CF grid points significant). The mechanism is that pro-league role-stability covariates do not shift career-stage residual variance because rotation patterns and offensive scheme demands are cross-class uniform in pro contexts. Playoff regime compresses rotations but does not change the underlying class structure — if the regular-season null is real, it should hold at playoff scale.

**Statistical test.**

- Compute σ_13+ and σ_non-13+ on AST residuals (both baselines).
- Variance ratio + bootstrap 95% CI (B = 1000).
- Levene's test + permutation null (B = 1000).
- If the 13+ cell has n_in < 10, the 10+ fallback fires; both 13+ and 10+ results are reported.
- CF refinement on the deep-vet residual distribution (per Section 2.5 of paper) **only** if n_in ≥ 30 in the deep-vet cell. Otherwise CF refinement is reported as not-performed (insufficient resolution).

**Decision rule.**

| Condition | Disposition |
|---|---|
| Variance ratio CI overlaps 1.0 AND Levene's p ≥ 0.05 AND p_perm ≥ 0.05 | **PERSISTS** (null replicates) |
| Variance ratio CI overlaps 1.0 BUT Levene's p < 0.05 | **WEAKENS** (Levene's signal but ratio inconclusive) |
| Variance ratio CI excludes 1.0 (coupling appears) AND Levene's p < 0.05 | **REGIME-SHIFT / FALSIFIED** (playoff regime activates coupling that was null in regular season) |

Note: a "weakened null" is conceptually different from a weakened positive — it means the null is no longer cleanly defended at playoff scale. **Both baselines must agree.**

### Prediction 3 — PTS × Center directional persistence

**H3.** Variance ratio σ_Center / σ_non-Center on per-game PTS residuals shows ratio < 1.0 (Center σ tighter than non-Center σ) in the 25-26 NBA playoffs.

**Mechanism stated ex ante.** The regular-season finding is 11/11 cells directional (ratio < 1.0), reaching formal Levene's significance only at NCAA cohort sizes (n_in > 200). NBA / WNBA cohorts (n_in 21–71) are too small to detect the small effect at p < 0.05. Playoff cohorts are smaller still. The directional pattern is the load-bearing claim; formal significance is not expected at playoff scale.

**Mechanism — why Center PTS is tighter.** Centers' point-scoring is concentrated in lower-variance shot zones (rim, post-ups) compared to non-Centers' broader shot distribution (3pt, midrange, drives, transition). The framework predicts that this structural variance compression at the residual-class level survives partial pooling because the mean component is absorbed into `mu_position[Center]`, leaving the residual class to carry the variance asymmetry. Playoff regime preserves shot-zone concentration patterns — Centers continue to score primarily at the rim — so the directional prediction should persist.

**Statistical test.**

- Compute σ_Center and σ_non-Center on PTS residuals (both baselines).
- Variance ratio + bootstrap 95% CI.
- Levene's test reported but not load-bearing.
- Permutation null B = 1000.
- **Headline metric:** count of cells (across all sub-cohort × baseline combinations) with ratio < 1.0 vs cells with ratio ≥ 1.0.

**Decision rule.**

| Condition | Disposition |
|---|---|
| Ratio < 1.0 in majority (≥ 60%) of testable cells × baselines | **PERSISTS** |
| Ratio < 1.0 in 50–60% of cells (consistent direction but weak) | **WEAKENS** |
| Ratio < 1.0 in 40–50% of cells | **REGIME-SHIFT** (no direction) |
| Ratio < 1.0 in < 40% of cells (ratio > 1.0 majority) | **FALSIFIED** (inversion) |

### Prediction 4 — REB × Center surgical/Stan walk-back persistence

**H4.** In the 25-26 playoff data, surgical-method REB × Center may show apparent coupling (σ_Center > σ_non-Center, ratio > 1.0). Stan robustness (re-scoring against v6.1 LOCKED, which absorbs position-mean structure into `mu_position[Center]`) dissolves the coupling. **Surgical and Stan disagree directionally; this is the regular-season pattern.**

**Mechanism stated ex ante.** The regular-season finding is 4/4 leagues couple under surgical (career-mean baseline picks up position-level mean structure that masquerades as residual-class coupling), 0/7 testable cells couple under Stan robustness (hierarchical pooling correctly absorbs position mean into `mu_position[Center]`, leaving residual variance asymmetry vanishes). The walk-back claim is that surgical REB × Center is a position-mean structural finding mis-classified as residual-class structure; Stan correctly classifies it. If playoff regime preserves the mechanistic distinction (position mean in surgical, hierarchical absorption in Stan), the same pattern should hold.

**Statistical test.**

- Compute REB residuals under both baselines.
- Variance ratio + bootstrap 95% CI under each.
- Permutation null B = 1000 under each.

**Decision rule.**

| Condition | Disposition |
|---|---|
| Baseline B (cohort-mean ≈ surgical) shows ratio > 1.0 with CI excluding 1.0; Baseline A (v6.1) shows ratio CI overlaps 1.0 | **PERSISTS** (walk-back replicates: surgical couples, Stan dissolves) |
| Both baselines show ratio > 1.0 with CIs excluding 1.0 | **REGIME-SHIFT** (Stan now shows playoff coupling that didn't exist in regular season) |
| Both baselines show ratio CI overlapping 1.0 | **WEAKENS** (surgical coupling weaker, Stan still null) |
| Baseline A excludes 1.0 above; Baseline B overlaps 1.0 | **FALSIFIED — UNEXPECTED** (Stan shows coupling that surgical does not — implausible inversion of mechanism) |

### Prediction 5 — PBP score-margin × possession in playoff regime

**H5.** Variance ratio σ_garbage / σ_clutch on per-game per-state rate residuals for PTS / REB / AST in the 25-26 NBA playoffs. Regular-season cross-season aggregate was NULL (1/3 single-season → 0/3 replication → cross-season null). **The playoff regime is the regime-shift candidate — the hypothesis under test is whether playoffs activate residue-class structure on the score-margin axis that regular season suppresses.**

**Mechanism stated ex ante.** Regular-season garbage time is dominated by bench / late-rotation / minute-load-management decisions that should produce wider residual variance than clutch (where rotations are tighter). The regular-season test failed: cross-season aggregate σ_garbage / σ_clutch did not reliably exceed 1.0. The playoff regime has structurally different garbage-time vs clutch dynamics: less garbage time per game (closer games, fewer blowouts), more clutch possessions per game, higher-stakes coaching variability. If the regular-season NULL was a power problem (signal too small to detect at season aggregate), playoff regime may concentrate the signal. If the regular-season NULL was a structural absence, playoffs should also be NULL.

**Statistical test.**

- For each stat S ∈ {PTS, REB, AST}:
  - Compute σ_clutch and σ_garbage on per-state per-player per-game rate residuals.
  - Variance ratio σ_garbage / σ_clutch + bootstrap 95% CI (B = 1000).
  - Levene's test (median-centered).
  - Bartlett's test reported as supplementary.
  - Permutation null B = 1000 (relabel state-tags within player, recompute ratio).
- Three stats, three independent variance ratios.

**Decision rule (per stat).**

| Condition | Disposition |
|---|---|
| Variance ratio CI overlaps 1.0 AND Levene's p ≥ 0.05 | **PERSISTS** (NULL holds in playoffs) |
| Variance ratio CI excludes 1.0 above AND Levene's p < 0.05 (ratio > 1.0 with significance) | **REGIME-SHIFT** (playoffs activate structure that regular season suppressed — publishable regime-dependent finding) |
| Variance ratio CI excludes 1.0 below (clutch wider than garbage, ratio < 1.0) | **FALSIFIED** (inversion) |

**Aggregate verdict for H5:**
- 0/3 stats regime-shift → **PERSISTS** (null holds across regimes)
- 1/3 → **PARTIAL REGIME-SHIFT** (single-stat regime activation, flag for replication on 26-27 playoffs)
- 2/3 or 3/3 → **REGIME-SHIFT** (publishable as regime-dependent activation of residue-class structure on the score-margin axis)

---

## 4. Falsification cascade

After initial coupling tests for any prediction that produces a non-null disposition (PERSISTS / WEAKENS / REGIME-SHIFT — i.e., any case where coupling is observed), the cascade fires per cell:

### 4.1 Permutation null (always run)

For each cell with apparent coupling, permute class labels (Center / non-Center, 13+ / non-13+, garbage / clutch) within player to preserve player-level structure, recompute variance ratio, repeat B = 1000 times. Report p_perm = fraction of permuted ratios as extreme as observed.

**Threshold.** If p_perm ≥ 0.05, the cell's apparent coupling does not exceed chance at this cohort size. The cell is downgraded to **AMBIGUOUS** in the cell-level report and does not contribute to the headline disposition.

### 4.2 Series-of-games dependency check

NBA playoff games are clustered into series (4–7 games per series, same opponent, same player rotation). Within-series residuals may be correlated due to matchup effects, coaching adjustments across games in a series, and shared health/rest state. If the effective sample size at the series level is much smaller than at the game level, game-level statistics overstate certainty.

**Test.** For each cell, compute intraclass correlation (ICC) of residuals within series (player × series as the cluster). If ICC > 0.3 (moderate clustering threshold, pre-registered), repeat the variance ratio computation at the series-as-observation level (each player × series produces one residual = mean of within-series residuals). Report both game-level and series-level variance ratios + CIs.

**Threshold.** If series-level CI overlaps 1.0 while game-level CI excludes 1.0, the cell is **DEPENDENCY-AMBIGUOUS** and downgraded.

### 4.3 Opponent-quality confound

Playoff matchups are bracket-filtered: better teams advance, so later-round games involve higher-quality opponents on average. If apparent coupling correlates with opponent quality across cells (not within), the coupling may be driven by opponent quality rather than residue-class structure.

**Test.** For each cell, compute mean opponent defensive rating quartile (from prior-season DvP) and mean opponent record quartile. Across cells, regress observed variance ratio on mean opponent quality. If R² > 0.4 (pre-registered threshold), opponent quality is a viable confound and cells must be reported with opponent quality as a stratification covariate.

### 4.4 Sample-size partialing

Apparent coupling can be a small-sample artifact: with n_in single digits, bootstrap variance estimation is unstable.

**Test.** For each cell, simulate 1000 bootstrap resamples at the same n_in but with class labels randomized (preserves cohort size, removes class structure). Compute the 95th percentile variance ratio under random-label simulation at this cohort size. If observed variance ratio is below the 95th-percentile null at this n_in, the apparent coupling is consistent with small-sample chance.

**Threshold.** Any cell where observed ratio is below the n_in-matched 95th-percentile null is downgraded to **SMALL-SAMPLE-AMBIGUOUS**.

### 4.5 Cascade-survival summary

A cell's disposition is **load-bearing** for the headline only if it survives:
- p_perm < 0.05 (not chance at cohort size)
- Series-level CI agrees directionally with game-level CI
- Cell does not require opponent-quality stratification to defend the finding
- Observed ratio exceeds the n_in-matched 95th-percentile null

Cells that fail one or more cascade checks are reported with explicit downgrade labels and do not contribute to the headline PERSISTS / WEAKENS / REGIME-SHIFT / FALSIFIED disposition.

---

## 5. Aggregate verdict framework

After per-prediction dispositions are determined, the aggregate verdict is reported with all five outcomes in a single table, regardless of how many "succeed":

| Prediction | Disposition | Baseline A (v6.1) | Baseline B (cohort) | Cascade survival |
|---|---|---|---|---|
| H1: BLK × Center | … | … | … | … |
| H2: AST × deep-vet null | … | … | … | … |
| H3: PTS × Center directional | … | … | … | … |
| H4: REB × Center walk-back | … | … | … | … |
| H5: PBP score-margin × possession | … | … | … | … |

**Publishable framings, written ex ante:**

- **5/5 PERSISTS** — "Cross-regime replication: framework's regular-season findings hold at playoff scale within NBA. Strongest available cross-regime support."
- **4/5 PERSISTS, 1 WEAKENS** — "Cross-regime replication with documented playoff-regime regularization at [stat]."
- **3+ PERSISTS, others split** — "Partial cross-regime replication; regime-dependent attenuation at [stats]."
- **Predominantly REGIME-SHIFT or FALSIFIED** — "Framework's regular-season findings do not replicate at NBA playoff scale; cross-regime regularization is regime-dependent. Honest negative finding integrated into Sloan paper as documented regime sensitivity."
- **H5 REGIME-SHIFT alone** — "Regular-season-NULL PBP lever activates in playoff regime: publishable regime-dependent residue-class activation on the score-margin axis." Reported separately as a regime-shift positive even if H1–H4 persist.

All five disposition outcomes are reported with equal prominence. There is no version of this report that omits any prediction.

---

## 6. What does NOT count

The following are explicit pre-registration violations. If any occurs, the analysis becomes exploratory only and the affected predictions are flagged as not pre-registration-defended:

- **Threshold adjustment after analysis.** The 15-minute PBP floor, the 10-minute average-minutes floor, the 3-game inclusion floor, and the 13+ years-pro primary cutoff are locked. Adjusting them after seeing data invalidates the affected prediction.
- **Stat-specific p-value cherry-picking.** All five predictions are reported regardless of how each lands. Reporting only the confirms is a violation.
- **Cohort redefinition.** The Test 1 inclusive position classifier and the deep-vet years-pro buckets are locked. Switching to a different position classifier (e.g., excluding hyphenated `C-F` from Center) after seeing residuals is a violation.
- **Switching from variance test to mean test.** The framework predicts variance asymmetry, not mean shift. If variance ratio fails, switching to a mean test of the residuals is a violation.
- **Adding new predictions post-hoc.** If during analysis a new pattern is observed (e.g., variance ratio on STL × Guard, or AST × Center coupling), it is documented as **exploratory observation worth pre-registering for a future round** but does NOT enter the headline disposition for this pre-registration. The five locked predictions are the test set.
- **Re-analysis on additional playoff data accumulated after the analysis run.** This is a single-batch pre-reg. If the analysis runs after second-round completion and additional playoff games occur after that point, those games are not used to update this pre-registration's findings.
- **Re-fitting v6.1.** The model is production-locked at the 2026-05-05 final-lock snapshot. Conditional re-scoring on playoff opponents and minutes uses existing posterior parameters; any tuning of player random effects, position effects, or any v6.1 hyperparameters using playoff actuals is a violation.
- **Model-tuning narratives.** If the analysis finds dispositions inconsistent with the regular-season findings, the response is to report the finding honestly, not to identify a "missing covariate" or "playoff-specific adjustment" that would close the gap.

---

## 7. Output artifacts

All outputs written to `runs/run_nba_playoffs_25_26/`:

- `cohort.csv` — qualifying players × per-prediction inclusion flags + per-state minute totals
- `residuals_v61.csv` — per-player per-game per-stat residuals under Baseline A (v6.1 conditional re-score)
- `residuals_cohort.csv` — same under Baseline B (within-cohort mean baseline)
- `pbp_state_residuals.csv` — per-player per-game per-state per-stat rate residuals
- `cell_results_h1.csv` … `cell_results_h5.csv` — per-cell variance ratios, bootstrap CIs, Levene's p, permutation p, ICC, opponent-quality covariate, n_in
- `cascade_summary.csv` — per-cell cascade survival flags
- `aggregate_verdict.md` — the five-row table from §5 with prose disposition per prediction
- `PLAYOFF_VALIDATION_RESULTS.md` — the umbrella report (companion deliverable to this pre-reg)

Companion `.docx` of `PLAYOFF_VALIDATION_RESULTS.md` produced via `scripts/md_to_docx.py` per the paper-state workflow.

---

## 8. Timing and commitment

- **Pre-registration committed:** 2026-05-10, before any inspection of 2025-26 NBA playoff residuals at any cell level.
- **Analysis fires:** once, after Conference Semifinals (second round) completes — expected late May 2026, ~60–80 playoff games available.
- **Single batch.** No rolling re-analysis. Multiple-look discipline is preserved by running the analysis exactly once.
- **No re-fits.** v6.1 is conditionally re-scored, never re-fit. No new offsets, no new variance tightenings, no model architecture changes triggered by playoff observations.
- **Final report:** `PLAYOFF_VALIDATION_RESULTS.md` produced after analysis. Headline dispositions match the §5 framework.

This pre-registration's discipline is invariant to whether the framework persists to playoff regime. Both PERSISTS and FALSIFIED outcomes are publishable. The result is the result.

---

## 9. Sign-off

Pre-registered before any 25-26 NBA playoff residual inspection. Located at the repo root alongside [PAPER_STATE.md](file:///D:/NBA%20Projections/PAPER_STATE.md), parallel to existing pre-registrations at `audit_runs/pbp_garbage_clutch_pre_reg/PRE_REGISTRATION.md` and `audit_runs/probe_b_2627_pre_registration/PRE_REGISTRATION_2627_forward_probe.md`.

- **Filed by:** Claude Code (claude-opus-4-7[1m])
- **Sign-off requested from:** mr.nathanhumphrey@gmail.com
- **Repo:** https://github.com/mrnathanhumphrey-droid/NBAProjections — to be committed and pushed only after sign-off
- **Companion paper section:** future Section 5.x of the methodology paper, integrated after analysis completes
