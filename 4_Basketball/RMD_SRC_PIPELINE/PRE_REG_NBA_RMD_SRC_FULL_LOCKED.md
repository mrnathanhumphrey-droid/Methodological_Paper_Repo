# Pre-Registration — NBA Full-Pipeline RMD-SRC + Comparative vs Traditional Partial Pooling

**Substrate:** NBA per-game player statistics (regular season).
**Status:** LOCKED v1.0 — signed off by mr.nathanhumphrey@gmail.com 2026-06-01. The lock event is the git commit of this file to the `NBAProjections` repo's `main` branch. The commit-SHA recorded in `RMD_SRC_PIPELINE/SHA_LOCK.txt` is the load-bearing timestamp.
**Author:** Claude Code (claude-opus-4-7[1m]).
**Filed before:** any inspection of any cell-level (μ, σ²) trajectory, regime label, response coefficient, F1–F4 firing value, or comparative-arm metric on the 2019-20 through 2025-26 NBA per-game data. The pre-reg is committed before any compute under this protocol fires.
**Companion paper section:** Section 4.2 of the RMD-SRC methodology paper — promotion of the NBA substrate from backbone-only application to full-pipeline application.

---

## 1. Why this exists

The RMD-SRC methodology paper (Resolve Research, 2026) names NBA at §4.2 as a substrate applying the broader residue-class partial-pooling discipline **without** the full RMD-SRC pipeline. Specifically, the paper records that the NBA work applies Step 1 (residue partition) and Step 3 (response validation) with a substrate-specific falsifier suite operationalized at the variance-ratio level rather than at the regime-label level of Step 2 of RMD-SRC.

For NBA to be counted among the paper's full-pipeline substrates — and for the cross-substrate generality claim to carry the NBA substrate at the same depth as Migration (the load-bearing full-pipeline exemplar at §4.5) — the NBA substrate must run Steps 0 through 6 with the five-regime trajectory taxonomy and the F1–F4 falsifier suite at locked quantitative thresholds.

The comparative arm answers a reviewer's first question: does iterative RMD-SRC recover structure that traditional partial pooling (the same data, the same partition, no trajectory taxonomy, no iterative sub-partition) does not? On the NBA substrate, the traditional-pooling arm is operationalized as the existing v6.1 LOCKED model — the hierarchical Bayesian NB2 Stan posterior with partial pooling across `position × years_pro` classes. The comparative measures per-cell regime-label recovery on the same P0 partition.

This pre-registration locks the operational definitions before any compute fires and before any cell-level statistic the pre-reg is designed to test is inspected.

## 2. Locked operationalizations

### 2.1 Data scope

- **Seasons:** 2019-20 through 2025-26, inclusive. Seven seasons.
- **Games:** regular-season only. Playoffs and play-in games are excluded from this pre-registration's data scope. The existing `PRE_REGISTRATION_NBA_PLAYOFFS_25_26.md` (committed 2026-05-10) continues to govern the playoff regime test. This full-pipeline pre-registration does not overwrite or amend that document.
- **Source parquet:** `D:/NBA Projections/data/parquet/historical_box_scores.parquet` (no backup-vintage substitution; locked at HEAD at lock time).
- **Player inclusion:** the player must appear in ≥ 20 games in the season AND average ≥ 10 minutes per game in that season's regular-season appearances. A player can appear in some seasons and not others; the partition is computed per (player, season).

### 2.2 P0 partition (Step 0/1)

The locked partition is **`position × years-pro × role-cohort`**. The three axes:

**Position** (inclusive Test 1 classifier, matching the cross-league paper at §2.5):
- **Center:** position string in {`C`, `C-F`, `F-C`}
- **Forward:** position string in {`F`, `F-G`, `G-F`} that does not satisfy the Center rule
- **Guard:** position string in {`G`, `PG`, `SG`} or any other string not matching the above

**Years-pro** (years-pro buckets matching the v6.1 LOCKED model's classifier):
- **Rookie:** years_pro ∈ {0, 1}
- **Soph–Early:** years_pro ∈ {2, 3, 4, 5}
- **Mid:** years_pro ∈ {6, 7, 8, 9, 10, 11, 12}
- **Deep-vet:** years_pro ≥ 13

**Role-cohort** (locked to **usage-rate-tier classifier** on prior-season `USG%`; user-confirmed selection 2026-06-01):
- **High-usage:** USG% ≥ 25.0
- **Mid-usage:** USG% ∈ [15.0, 25.0)
- **Low-usage:** USG% < 15.0
- **Rookie handling:** for a player with no prior-season USG% (first NBA season), the role-cohort defaults to **Mid-usage** at season t and is re-classified on prior-season t–1 actuals from season t+1 onward. The default-Mid-usage assignment is locked.

The Cartesian product produces **3 × 4 × 3 = 36 candidate cells**. The locked sparse-cell collapse rule (matching the paper's Step 1 discipline) is:
- For each (position × years-pro × role-cohort) cell, count the number of qualifying player-seasons across the seven seasons.
- If the cell has fewer than 50 player-seasons total OR fewer than 5 player-seasons in any single season, the cell is merged with its nearest neighbor (preferring along role-cohort first, then years-pro, then position) under the deterministic agglomerative rule.
- Final K is determined by the data; the merge map is logged at `RMD_SRC_PIPELINE/results/P0_collapse_map.json` and is part of the partition's SHA-lockable surface.

**Known limitation (documented, not amended later):** the usage-tier classifier is offense-tilted. Defensive specialists with high BLK or STL rates but low USG% land in Low-usage cells; this means the Center × Low-usage cell will pool shot-blocking specialists with bench bigs whose role is different. This is acknowledged ex ante as a substrate-specific feature of the locked partition. It does NOT trigger a partition-redefinition pathway; it is part of the substrate ledger and is discussed in the report.

### 2.3 Observables

Four observables, one per RMD-SRC pipeline run:
- **PTS_per36** = (PTS × 36) / MIN
- **REB_per36** = (REB × 36) / MIN
- **AST_per36** = (AST × 36) / MIN
- **BLK_per36** = (BLK × 36) / MIN

Per-36 normalization absorbs the season-to-season MPG drift that would otherwise produce artifactual mean-slope signal in raw per-game totals.

The pipeline runs four times in parallel, once per observable. Bonferroni correction at α = 0.0125 (= 0.05 / 4) is applied to any statistical-significance claim that aggregates across observables; per-observable falsifier thresholds are NOT Bonferroni-adjusted (they are absolute, locked thresholds).

### 2.4 Time axis

The Step 2 trajectory's time axis is the **season axis**, indexed `s ∈ {2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26}`. Seven points. For each (cell, observable), μ_s and σ²_s are the PERWT-equivalent unweighted (cell-membership-weighted) sample mean and sample variance of the observable across all qualifying (player, game) records in cell × season.

### 2.5 Train / holdout split

- **Training window:** 2019-20 through 2023-24 (5 seasons).
- **Holdout window:** 2024-25 and 2025-26 (2 seasons).
- The Step 2 regime labels, Step 3 response coefficients, Step 4 decomposition, and the v6.1 LOCKED comparative posterior are all fit / re-scored against the training window only. The holdout window is reserved for F4 (regime-label transfer), Step 5 (cell-signature transfer), and the comparative arm's per-cell regime-label recovery test.

## 3. Step 2 — five-regime trajectory taxonomy

For each (cell, observable) pair in the training window:
1. Compute the trajectory `{μ_s, σ²_s}_{s=2019-20}^{2023-24}` (5 points).
2. OLS fit of `μ_s` on season-index `t_s ∈ {0, 1, 2, 3, 4}` → slope `μ̇`.
3. OLS fit of `σ²_s` on `t_s` → slope `σ̇²`.
4. Compute normalization scales:
   - `μ_bar` = mean of `μ_s` across training seasons
   - `σ²_bar` = mean of `σ²_s` across training seasons
5. Compute unitless rates:
   - `r_μ = μ̇ / |μ_bar|` if `|μ_bar| > 0.01` else `r_μ = μ̇` (absolute, in observable-units/season — flagged in output)
   - `r_σ² = σ̇² / |σ²_bar|` if `|σ²_bar| > 1e-6` else `r_σ² = σ̇²`

### 3.1 Locked thresholds

- Mean-slope threshold: `ε_μ = 0.02` per season (2% per-season normalized mean change)
- Variance-slope threshold: `ε_σ² = 0.05` per season (5% per-season normalized variance change)

### 3.2 Classifier (deterministic, paper-canon five-regime taxonomy)

```
if |r_μ| ≤ ε_μ  AND  |r_σ²| ≤ ε_σ²:    → Stationary
elif r_μ > +ε_μ  AND  r_σ² < -ε_σ²:     → Concentrating
elif r_μ > +ε_μ  AND  r_σ² > +ε_σ²:     → Diffusing
elif r_μ < -ε_μ  AND  r_σ² < -ε_σ²:     → Contracting
elif r_μ < -ε_μ  AND  r_σ² > +ε_σ²:     → Drifting
else (one slope inside threshold, one outside): → Edge
```

The Edge bucket is reported but is NOT one of the five canonical regimes; it captures cells that sit at the slope-threshold edge in one moment and is reported separately as a substrate-ledger row. Cells classified as Edge do not contribute to F2 / F4 headlines but are preserved in the substrate ledger with explicit downgrade labels.

## 4. Step 3 — response validation

For each (cell, observable):
1. **Single-mode check:** Hartigan dip test on the within-cell observable distribution pooled across training seasons. PASS if `p_dip ≥ 0.05`.
2. **Permutation-stability check:** permute the season-index assignment among the training seasons (5! = 120 permutations exhaustively); recompute regime label. PASS if the cell's regime label is the modal label in ≥ 60% of permutations.
3. **Held-out-subset check:** for the training window, hold out one season (leave-one-season-out, 5-fold); recompute regime. PASS if ≥ 3 of 5 LOSO folds return the same regime as the full-training-window label.

A cell is **response-validated (clean)** if all three checks PASS. A cell failing any check is flagged and does not contribute to substrate-level conclusions; it is reported with the failing check named.

## 5. Step 4 — decomposition

Applied only to cells that are response-validated and classified as one of {Concentrating, Diffusing, Contracting, Drifting} (i.e., have nontrivial regime signal). Order: 4a → 4b → 4c.

### 5.1 4a — categorical sub-partition

Two pre-registered candidate axes are tested independently per non-Stationary cell:

1. **`opp_DEF_RTG_tertile`** — prior-season opponent average defensive rating, tertile-binned at the league level. Cell-natural in the sense that defensive matchup is the most-load-bearing exogenous cell axis the residual-class framework has identified for NBA.
2. **`home_away`** — binary home / away indicator on the per-game record. Cell-natural in the sense that home-court is the most-stable single contextual axis in NBA box-score residuals.

**PASS criterion (per candidate axis):** child cells' mean cleanness (fraction of (sub-cell, observable) clean under Step 3) exceeds parent cell's cleanness by **≥ 0.10 absolute**.

**Resolution rule (deterministic):**
- If neither axis passes its ≥ 0.10 gate → 4a fails; proceed to 4b.
- If exactly one axis passes → that axis locks the 4a split.
- If both axes pass → the axis with the larger child-vs-parent cleanness improvement locks the split. Ties broken by alphabetical axis-name (`home_away` < `opp_DEF_RTG_tertile`, so `home_away` wins exact ties).

The 4a candidate set is exhausted at these two axes. Adding a third axis post-hoc (e.g., `back_to_back_flag`, `opp_PACE_tertile`) is a §11 violation; any third axis requires a new pre-reg.

### 5.2 4b — continuous sub-partition

If 4a fails, test continuous covariate `prior_season_per36_value_self` (the player's prior-season per-36 rate of the same observable, capturing player-level mean structure NOT in P0).

Method: fit OLS of within-cell training residuals on this continuous covariate (after position+years-pro residualization, against v6.1 LOCKED Baseline A). PASS criterion: residual R² ≥ 0.30 reduction post-covariate adjustment, AND the post-adjustment regime classification flips to Stationary.

### 5.3 4c — null

If both 4a and 4b fail: the cell is declared non-decomposable for the observable. Reported as Step 4c null.

All three outcomes (4a-success, 4b-success, 4c-null) are pre-committed as publishable. Mixed outcomes across the four observables for the same cell are preserved.

## 6. Step 5 — held-out transfer

The cell-level signature for transfer testing is a 4-tuple per (cell, observable):
- Regime label (categorical, one of {Stationary, Concentrating, Diffusing, Contracting, Drifting, Edge})
- σ_within (within-cell sample SD across cell-membership rows, training window)
- ρ_LOSO (LOSO mean correlation of within-cell rates across pooled cell-rows)
- β_role-cohort (response coefficient on role-cohort indicator from Step 3 OLS fit)

The full-cell signature across the K-cell partition is the matrix `S_train ∈ ℝ^{K × 4}` (regime label encoded as integer in column 1).

### 6.1 Transfer test

1. Re-fit Step 2 + Step 3 on the 2024-25 + 2025-26 holdout window only (with the same partition, the same observables, the same thresholds).
2. Produce `S_holdout ∈ ℝ^{K × 4}`.
3. Cell-level signature transfer = **mean Pearson r ≥ 0.80** across the four columns of `S_train` vs `S_holdout`, computed over the K cells.
4. PASS if mean r ≥ 0.80. The mean of column-wise Pearson r is the headline transfer score; per-column r values are reported.

## 7. Step 6 — mechanism inference (partition-level, confidence-tiered)

Mechanism claims are committed at three tiers:

**Prospective tier (strongest claim — committed now, before compute):**
- If the (Center × any-years-pro × any-role-cohort) cell × BLK_per36 observable classifies as Concentrating in the training window AND survives Step 5 transfer, the mechanism inference is: Centers carry a residual-class concentration mechanism on shot-blocking that tightens variance across the seven-season panel.

**Retrospective tier (named after decomposition, before validation):**
- Any mechanism named after Step 4 (e.g., "the BLK × Center concentration is absorbed by opp_DEF_RTG_tertile at 4a") is recorded as a retrospective candidate; reported as a candidate, not a load-bearing claim.

**Post-hoc tier (named after Step 5):**
- Any mechanism named after the held-out transfer test is reported only as forward-watch for the 2026-27 season.

## 8. F1–F4 falsifier suite (paper-canon thresholds locked)

### 8.1 F1 — substrate validity

Additive linear model: `Y_pg = α + β_pos × position + β_yp × years_pro_bucket + β_rc × role_cohort + β_s × season_dummy + ε_pg`, fit on the training window pooled across cells and observables. Compute `R² = 1 − SS_res / SS_tot`.

**Fires if R² ≥ 0.90** on any of the four observables. A firing is a correct refusal: a substrate where ≥ 90% of variance is absorbed by a simple additive model on partition variables does not need the framework.

### 8.2 F2 — decomposability

**Fires if fewer than 50% of (cell × observable) pairs terminate cleanly** in the training window, where "terminate cleanly" means:
- Classified as Stationary in Step 2, OR
- Classified as non-Stationary in Step 2 AND response-validated in Step 3 AND Step 4 produces a successful sub-partition (4a or 4b) — i.e., a clean decomposition with at least one of the children passing Step 3.

The headline F2 metric is `n_clean / (K × 4)`. F2 fires if `n_clean / (K × 4) < 0.50`.

### 8.3 F3 — lossy decomposition

For each cell where Step 4a or 4b succeeded, compute the within-cell variance explained by the sub-partition: `R²_sub = 1 − Var(within-sub-cell) / Var(within-parent-cell)`.

**Fires if R²_sub < 0.30** on any (cell, observable) sub-partition flagged as successful. Firing flags the sub-partition as visible-but-thin; not load-bearing.

### 8.4 F4 — regime non-transfer

Compute Cohen's κ between training-window regime labels (Step 2 on 2019-20 to 2023-24) and holdout-window regime labels (Step 2 re-fit on 2024-25 + 2025-26) per observable, across K cells.

**Fires if κ < 0.40** on any of the four observables. Firing localizes the failure of the framework's dynamic layer for that observable.

All four falsifier outcomes (per observable) are reported regardless of which fire, with the threshold, the observed value, and a bootstrap 95% CI (B = 1000 cell-resample) on the observed value.

## 9. Comparative arm — RMD-SRC vs Traditional Partial Pooling

### 9.1 Methods compared

**Method A — RMD-SRC full pipeline:** the protocol specified in Sections 2 through 8 above.

**Method B — Traditional partial pooling:** the existing v6.1 LOCKED hierarchical Bayesian NB2 Stan posterior with partial pooling across `position × years_pro` classes (production-locked at 2026-05-05), conditionally re-scored on the same training window and producing per-cell mean and variance estimates without trajectory taxonomy and without iterative sub-partition. v6.1 LOCKED uses the same data scope and the same per-36 normalization for the comparative.

### 9.2 Per-cell regime-label recovery metric

For each (cell, observable) pair on the training window:

- **Method A's verdict per cell:** one of the five regimes {Stationary, Concentrating, Diffusing, Contracting, Drifting} (Step 2 + Step 3 response-validated; cells flagged by Step 3 are excluded from the comparative). Call this `regime_A`.
- **Method B's verdict per cell:** Method B assigns no regime label (no trajectory machinery). For comparability, we synthesize Method B's implicit verdict as **"Stationary"** for every cell — Method B's posterior pools the cell's variance across seasons without distinguishing trajectory regime. This is the honest operational reading of "no trajectory machinery."

### 9.3 PASS / TIE / LOSE decision rule

Per (cell, observable):

- **PASS for RMD-SRC** if: `regime_A ∈ {Concentrating, Diffusing, Contracting, Drifting}` AND the cell is response-validated AND the cell-level held-out transfer test (the cell's 4-tuple signature in `S_train` vs `S_holdout`, per-cell Pearson r) achieves r ≥ 0.50. (The per-cell transfer threshold for the comparative is r ≥ 0.50, looser than Step 5's partition-level r ≥ 0.80 because per-cell transfer has fewer degrees of freedom; the looser threshold is locked here and not adjusted later.)
- **LOSE for RMD-SRC** if: `regime_A ∈ {Concentrating, Diffusing, Contracting, Drifting}` AND the cell-level held-out transfer test returns per-cell r < 0.50 AND the cell's regime label flips in the holdout window. Method A over-fit a regime label that did not transfer.
- **TIE** otherwise: `regime_A = Stationary` (both methods agree, no claim differential) OR the cell is flagged in Step 3 (no verdict to compare) OR `regime_A` is non-Stationary with per-cell transfer r < 0.50 AND no holdout-window regime flip (regime label persists across windows but per-cell transfer-r is below the headline PASS bar — neither method is meaningfully ahead).

### 9.4 Headline disposition

Headline = the (PASS, TIE, LOSE) count across all (cell × observable) pairs. Per-observable breakdown is reported. Substantive read:

- **PASS-dominant (PASS > LOSE by ≥ 2× across all observables):** RMD-SRC recovers structure traditional pooling misses on this substrate. The methodology paper's NBA section claims a substantive cross-substrate generality finding.
- **PASS ≈ LOSE:** RMD-SRC and traditional pooling are at parity on NBA. The framework's added machinery does not pay for itself on this substrate. Reported honestly.
- **LOSE-dominant:** RMD-SRC over-fits the substrate. The traditional-pooling baseline is the correct epistemic floor for NBA. Reported honestly.
- **Mixed:** PASS-dominant on some observables, LOSE-dominant on others. The per-observable mixed disposition is the substantive read.

All four dispositions are pre-committed as publishable.

## 10. Preservation of prior pre-registered work (NON-OVERWRITE clause)

This pre-registration does NOT overwrite or amend:
- The 2026-05-05 v6.1 LOCKED production model.
- The 2026-05-08 paper-state findings (BLK × Center 11/11, AST × deep-vet null, PTS × Center directional, REB × Center walk-back).
- The 2026-05-10 `PRE_REGISTRATION_NBA_PLAYOFFS_25_26.md` Tier-1 hypotheses H1–H5 on the 2025-26 playoffs.
- The REB × Center walk-back (Appendix D, Walk-back 1 of the methodology paper).
- The H4 pre-registered walk-back-validation discipline (the test of whether the retracted REB × Center finding stays retracted under new data).

This pre-registration is **additive**: it adds the full-pipeline RMD-SRC application on regular-season data to the substrate ledger. The playoff regime test (PRE_REGISTRATION_NBA_PLAYOFFS_25_26.md) remains the canonical document for the playoff arm of the NBA substrate.

## 11. What does NOT count (discipline guards)

Each item below is an explicit pre-registration violation. Any occurrence flags the affected disposition as exploratory only.

- **Threshold adjustment after firing:** `ε_μ = 0.02`, `ε_σ² = 0.05`, F1 ≥ 0.90, F2 < 0.50, F3 < 0.30, F4 κ < 0.40, Step 5 r ≥ 0.80, comparative per-cell r ≥ 0.50, and the 4a/4b decomposition gates (≥ 0.10 absolute cleanness improvement for 4a; ≥ 0.30 R² reduction for 4b) are locked. Adjusting any after compute invalidates the affected outcome.
- **Adding a third 4a sub-axis post-hoc:** the locked 4a candidate set is `opp_DEF_RTG_tertile` and `home_away`. If both fail their ≥ 0.10 cleanness improvement gate, the pipeline proceeds to 4b. Adding a third axis mid-stream (`back_to_back_flag`, `opp_PACE_tertile`, etc.) is a violation; a new candidate axis requires a new pre-reg.
- **Partition redefinition:** the `position × years-pro × role-cohort` partition with the locked sparse-cell collapse rule is fixed. Switching role-cohort to MPG-tier after observing BLK / Center awkwardness is a violation. The known limitation is documented in §2.2 and is not a violation pathway.
- **Observable substitution:** the four observables (PTS_per36, REB_per36, AST_per36, BLK_per36) are locked. Adding STL or TOV mid-stream because a new pattern surfaces is a violation; a fifth observable would require a new pre-reg.
- **Window adjustment:** the train (2019-20 to 2023-24) / holdout (2024-25 + 2025-26) split is locked. Sliding the split because the holdout dispositions look noisy is a violation.
- **Selective comparative reporting:** all four observables × all K cells contribute to the comparative-arm PASS/TIE/LOSE count. Reporting only the PASS-dominant observable or only the BLK cell is a violation.
- **Post-hoc mechanism promotion:** any mechanism named after Step 5 is reported as forward-watch tier only. Promoting a post-hoc mechanism to prospective tier requires a separate pre-reg for the next round.
- **Method B re-tuning:** the v6.1 LOCKED model used in the comparative is the production-locked posterior at the 2026-05-05 snapshot. Re-fitting v6.1 with new hyperparameters or new priors for the comparative is a violation; the comparison is against the deployed model.
- **Selective F1–F4 reporting:** all four falsifiers, on all four observables, are reported regardless of firing. Reporting only the falsifiers that did not fire is a violation.

## 12. Output artifacts

All outputs written under `D:/NBA Projections/RMD_SRC_PIPELINE/results/`:

- `P0_partition.parquet` — per (player, season) → cell_id mapping.
- `P0_collapse_map.json` — the sparse-cell merge log + final K.
- `moment_trajectories.parquet` — per (cell, observable, season): μ_s, σ²_s, n.
- `trajectory_classification.parquet` — per (cell, observable): r_μ, r_σ², regime label.
- `step3_validation.parquet` — per (cell, observable): dip_p, perm_pass_rate, LOSO_pass_count, clean flag.
- `step4_decomposition.parquet` — per (cell, observable): 4a / 4b / 4c outcome, sub-partition variable, R²_sub.
- `step5_transfer.parquet` — per (cell, observable): S_train row, S_holdout row, per-cell Pearson r.
- `F1_F4_summary.json` — per observable: F1/F2/F3/F4 observed values + bootstrap 95% CI + fires flag.
- `comparative_per_cell.parquet` — per (cell, observable): regime_A, regime_B (always Stationary), per-cell transfer r, PASS/TIE/LOSE.
- `comparative_headline.json` — aggregate PASS/TIE/LOSE counts per observable + overall.
- `mechanism_inference.md` — partition-level mechanism inferences with confidence tier per claim.
- `substrate_ledger.md` — every cell disposition + every falsifier outcome, mixed outcomes preserved.
- `RESULTS.md` — the umbrella report.

Every reported number in `RESULTS.md` cites the artifact and the row producing it. No prose-only figures.

## 13. Sign-off

- **Filed by:** Claude Code (claude-opus-4-7[1m])
- **Sign-off requested from:** mr.nathanhumphrey@gmail.com
- **Repo:** https://github.com/mrnathanhumphrey-droid/NBAProjections
- **Lock event:** rename this file to `PRE_REG_NBA_RMD_SRC_FULL_LOCKED.md`, git add, git commit. Record the commit-SHA in `RMD_SRC_PIPELINE/SHA_LOCK.txt`. The compute pipeline does not begin until SHA_LOCK.txt exists with a commit-SHA in it.

---

**End of draft v0.1.**
