# Pre-Registration — Adjudicated-Position Test 1 Re-Validation

## Inclusivity Correction on the NBA Center Cells of the Cross-League Variance-Asymmetry Test

**Date filed:** 2026-06-01
**Filed before:** any inspection of variance ratio, Levene's p, bootstrap CI, or any per-cell statistic on residuals computed under adjudicated position bucketing. The metadata-bucketed Test 1 results (cross-league paper §5.5, §5.6.1, §5.7.3) are visible and locked at their existing reported values; the adjudicated-bucket-derived per-cell statistics have not been computed at any cell level.
**Status:** Sloan-grade Tier-1 pre-registration. Single document covering three Tier-1 hypotheses (BLK × Center, PTS × Center, REB × Center walk-back validation) plus one power-gating falsifier. Locks via git commit to the NBAProjections repository. Single-test α = 0.05 per cell, per the existing cross-league paper protocol (no Bonferroni since each cell is pre-registered).
**Sloan paper:** *Partial pooling of residual classes: theory, application to basketball projections, and measurable noise-floor reduction* (working title), draft state at `paper_draft/section_5_empirical_validation.md`. This pre-registration extends §5.5–§5.7.3 with an adjudicated NBA arm reported alongside the existing metadata arm.
**RMD-SRC paper cross-reference:** the adjudicated position bucketing is the v1.2 artifact at `RMD_SRC_PIPELINE/results/position_adjudication_v12.json` (content SHA256 `eb615269f09159e0d0ceaf071812b84750578d81a9a53b01dff5a1ac2ac9dcbd`, locked under amendment-v1.2 commit `1bfdb4c0dfa2b3754f67e9c2f91b2ab26fa01866`). The artifact's load-bearing audit pointer is shared between the two papers.

---

## 1. Why this exists

The cross-league paper claims partial pooling of residual classes generalizes across sport and method via three position-driven cell findings. BLK × Center couples in 11 of 11 testable cells across 4 leagues × 2 methods with variance ratios in the band [1.26, 2.03]. PTS × Center is directional (ratio < 1.0) in 11 of 11 cells with formal significance at NCAA cohort scale only. REB × Center is retracted under Stan robustness: 4 of 4 leagues couple under surgical projection method, but 0 of 7 testable cells couple under hierarchical NB2 Stan posterior. The walk-back is published equal-prominence to the confirmations per the paper's discipline.

Two methodological constraints govern the NBA contribution to these claims:

1. **The Stan vet cohort is capped at the top 200 players by minutes.** Under this cap, n_in for NBA Center cells is 21 in 23-24 and 24-25, expanding to 71 only at the 25-26 full-ship cohort. The 24-25 BLK × Center result at ratio 1.24 with Levene's p = 0.11 is reported in §5.4.2 as same-directional but underpowered. NBA contributes three cells (23-24, 24-25, 25-26) of the 11/11 BLK × Center result; two cells reach formal significance and one is underpowered.

2. **The inclusive Test 1 classifier operates on raw `player_metadata_enriched.position` strings.** Independent diagnostic work under the RMD-SRC v1.2 amendment (committed 2026-06-01 at `1bfdb4c`) established that 46 of 230 multi-eligible NBA players in the 2019-26 qualifying union are systematically mis-bucketed as Forward by the metadata while their on-court archetype is Center. Named examples: Anthony Davis, Giannis Antetokounmpo, Kevin Love, Mason Plumlee, Kristaps Porziņģis, Kelly Olynyk, Dwight Powell, Taj Gibson. The mis-classification pattern is a 42.6%-override-rate finding from a 230-agent independent-adjudication fleet (Sonnet, structured-output schema enforced) operating on a locked prompt template. The adjudicated Center bucket includes the metadata Center bucket as a strict superset plus 46 Forward-tagged players whose on-court archetype is Center.

The cross-league paper's NBA Center population for Test 1 therefore systematically under-counts modern bigs at a methodological scale. This pre-registration applies the v1.2-locked adjudicated bucketing to the existing NBA Test 1 protocol and pre-commits a four-pre-registered-disposition cascade per observable on whether the cross-league finding is robust to the inclusivity correction, attenuates, falsifies, or inverts.

The discipline of this pre-registration is that the test design is locked before any adjudicated-bucket-derived statistic is inspected. The 230-verdict adjudication artifact at SHA256 `eb615269...` is read-only input; the per-cell variance ratios on residuals computed under that bucketing have not been touched at the cell level.

## 2. Locked operationalizations

### 2.1 Substrate scope

- **Seasons:** 2023-24, 2024-25, 2025-26 NBA regular season. Three seasons, matching the existing NBA cross-season Test 1 design in cross-league paper §5.5 (Table 5.5).
- **Source:** `D:/NBA Projections/data/parquet/historical_box_scores.parquet`, restricted to regular-season rows for the three seasons.
- **Cohort selection (per-season, exactly matching existing protocol):**
  - **23-24 cell:** Stan vet pool at 200-player cap (per §5.4 v6.1 cohort definition).
  - **24-25 cell:** Stan vet pool at 200-player cap.
  - **25-26 cell:** Full ship (n=567 players, all v6.1 LOCKED-projected qualifying players).
- **Observable space:** three per-game stats, BLK, PTS, REB (exactly matching existing Test 1 protocol; not per-36, per existing).

### 2.2 Residual baseline

Residuals are computed under the **v6.1 LOCKED model** (production-locked at 2026-05-05, snapshot at `RMD_SRC_PIPELINE/PRE_REG_NBA_RMD_SRC_FULL_LOCKED.md` cross-reference and existing audit at `paper_draft/production_application/v6_1_postmortem_session2_locked.md`). No re-fit. No new offsets. No model tuning to adjudicated positions. The model parameters are frozen at the existing snapshot; only the player → position bucket assignment that determines Center vs non-Center for the variance comparison changes.

Per-game residual:
```
residual_S(p, g, season) = actual_S(p, g) − E_v61(p, g, S)
```
where `E_v61(p, g, S)` is the v6.1 LOCKED posterior's predicted mean for player p on game g for stat S, conditional on the player's existing v6.1 covariates.

This is exactly the residual definition from the cross-league paper §5.5. The variance ratio test operates on these residuals grouped by Center vs non-Center.

### 2.3 Position classifier — locked

**Metadata bucket (control, matching existing §5.5):**
- **Center:** `position` string in {`Center`, `Center-Forward`, `Forward-Center`} per the inclusive Test 1 classifier from cross-league paper §2.5.
- **Non-Center:** all other position strings.

**Adjudicated bucket (load-bearing, NEW):**
- For each player in the v1.2 adjudication scope (n=230): the bucket is the agent's verdict from `position_adjudication_v12.json`. Center if `adjudicated_bucket == "Center"`; non-Center otherwise.
- For each player NOT in the v1.2 adjudication scope (n=562 within the union; expanded to the full 23-26 NBA cohort): the bucket is the metadata bucket per the inclusive Test 1 classifier above.
- The adjudication artifact is read-only; the agent verdicts are not re-run, re-judged, or modified.

The 46 metadata-Forward → adjudicated-Center players (AD, Giannis, Love, Plumlee, Porziņģis, Olynyk, Powell, Gibson + 38 others per the v1.2 flip matrix) move from non-Center to Center under the adjudicated bucket. The 2 metadata-Forward → adjudicated-Guard players (Luka Dončić, Tyrese Martin) move from non-Center to non-Center (Forward → Guard within the non-Center side, no Center cell impact). The 50 metadata-Guard → adjudicated-Forward players (Batum, DeRozan, Simmons, Brown, Hart, Brooks + 44 others) move within non-Center as well.

**Net effect on Center cohort:** the adjudicated Center bucket equals the metadata Center bucket + 46 NEW Center entrants. No metadata Center players are removed under adjudication (0 Center → other flips in the v1.2 verdicts).

### 2.4 Test statistic — Levene's variance ratio (load-bearing)

For each (season, observable) cell, under each bucketing arm (metadata, adjudicated):
- `σ_Center` = sample SD of residuals across qualifying (Center player, game) records in the cohort.
- `σ_non-Center` = sample SD of residuals across qualifying (non-Center player, game) records.
- **Variance ratio = σ_Center / σ_non-Center.**
- **Bootstrap 95% CI on the ratio: B = 1,000 resamples** (cluster on player to preserve player-level variance structure, per existing Test 1 protocol).
- **Levene's test (median-centered) on residual^2.** Load-bearing for the per-cell decision.
- p_F (two-sided F-test) and p_Bartlett reported as supplementary but not load-bearing.

### 2.5 Power gate (pre-committed)

For each (season, observable) cell, the **adjudicated cohort must materially expand the Center population** for the cell to be a valid test of the inclusivity correction. The locked power gate:

```
n_in_adjudicated / n_in_metadata ≥ 1.30
```

If `n_in_adj / n_in_meta < 1.30` in any cell, that cell is **POWER-LIMITED** and is reported with the power flag and no disposition is assigned. The disposition for that cell is "inconclusive — adjudication did not materially expand cohort."

For the 23-24 and 24-25 Stan vet cells, the Stan 200-player cap still applies; the adjudicated cohort cannot exceed 200 players per season (the cap is preserved). The lift comes from the inclusivity correction within the 200-player pool — specifically, the 46 adjudicated-Center players among the top 200 by minutes.

For the 25-26 full ship, no cap applies. The full 46 adjudicated-Center additions enter the cohort.

## 3. Tier-1 Hypotheses

Each hypothesis is tested independently per season cell and aggregated to a three-cell verdict. Per cell, four exhaustive dispositions are pre-committed.

### 3.1 H1 — BLK × Center under adjudicated bucketing

The existing claim: σ_Center / σ_non-Center > 1.0 in NBA at variance ratios within [1.26, 2.03] (the cross-league 11/11 band). Three NBA cells in the existing paper: 23-24 ratio 1.98 (p=0.002, n_in=21), 24-25 ratio 1.24 (p=0.11, n_in=21), 25-26 full ship ratio 1.71 (p=4.7e-8, n_in=71).

**Per-cell decision rule under adjudicated bucketing:**

| Condition | Disposition |
|---|---|
| Bootstrap CI on adjudicated ratio overlaps [1.26, 2.03] AND p_levene < 0.05 | **PERSISTS** — adjudication confirms the cross-league BLK × Center coupling under inclusivity correction. |
| CI overlaps [1.26, 2.03] AND p_levene ≥ 0.05 (CI width > metadata CI width) | **PERSISTS-DIRECTIONAL** — magnitude band preserved but the larger cohort widens the CI such that formal significance is not reached. Reported as same-finding-at-wider-CI. |
| CI fully below 1.26 but lower bound > 1.0 AND p_levene < 0.05 | **ATTENUATES** — adjudication reduces magnitude but preserves direction. The paper's claimed magnitude band [1.26, 2.03] needs revision; the directional claim survives. Walk-back of magnitude band; coupling claim preserved. |
| CI brackets 1.0 (lower bound < 1.0 < upper bound) | **REGIME-NULL** — adjudication kills the BLK × Center coupling at NBA scale. The 11/11 claim becomes 8/11 (NBA cells 0/3) under inclusivity correction. Walk-back of NBA contribution; cross-league claim revised. |
| CI fully below 1.0 (ratio inverted, Center σ < non-Center σ on BLK) | **INVERTED** — the original finding was a metadata-bucketing artifact. Walk-back of cross-league claim is required at the NBA contribution layer; cross-league claim becomes ambiguous pending WNBA/NCAA re-validation under different inclusivity scrutiny. |
| Power-limited per §2.5 | **INCONCLUSIVE** (no disposition; cell reported with power flag). |

**Aggregate H1 verdict (across 3 NBA cells):**
- 3 of 3 PERSISTS or PERSISTS-DIRECTIONAL → headline: "BLK × Center NBA under adjudication: cross-league finding robust to inclusivity correction. 11/11 reaffirmed."
- 2 of 3 PERSISTS, 1 ATTENUATES → headline: "BLK × Center NBA under adjudication: coupling persists with magnitude attenuation in one cell. Cross-league magnitude band may need NBA-specific revision."
- 1 of 3 PERSISTS → headline: "BLK × Center NBA under adjudication: weak partial replication. Cross-league 11/11 claim has fragile NBA contribution."
- 0 of 3 PERSISTS → headline: "BLK × Center NBA under adjudication: cross-league finding's NBA contribution falsified or attenuated. Walk-back required."

### 3.2 H2 — PTS × Center under adjudicated bucketing

The existing claim: σ_Center / σ_non-Center < 1.0 in NBA (Center variance tighter on PTS). Three NBA cells: 23-24 ratio 0.94, 24-25 ratio 0.83, 25-26 ratio 0.85 (per cross-league paper Table 5.5; none reach formal significance at NBA cohort scale, all same-directional).

**Per-cell decision rule:**

| Condition | Disposition |
|---|---|
| CI overlaps existing range [0.76, 1.02] AND ratio < 1.0 | **DIRECTIONAL-PERSISTS** — adjudication preserves the cross-league directional finding under inclusivity correction. |
| CI overlaps 1.0 (no clear direction) | **NULL** — adjudication eliminates the PTS × Center directional signal. The 11/11 directional claim becomes 8/11 under inclusivity correction. |
| CI fully > 1.0 (Center σ > non-Center σ on PTS) | **INVERTED** — falsifies the cross-league directional finding's NBA contribution. Walk-back required. |
| Power-limited per §2.5 | **INCONCLUSIVE**. |

**Aggregate H2 verdict (across 3 NBA cells):**
- 3 of 3 DIRECTIONAL-PERSISTS → headline preserved.
- 2 of 3 → headline preserved with one-cell walk-back.
- 1 of 3 → headline weakened; directional claim becomes 1-of-3 NBA + cross-league.
- 0 of 3 → directional claim NBA-falsified.

### 3.3 H3 — REB × Center walk-back validation under adjudicated bucketing

The existing finding: surgical method shows σ_Center > σ_non-Center on REB residuals 4/4 leagues; Stan robustness produces 0/7 testable cells coupling (WNBA Stan 0/3, NCAA M Stan 0/2, NCAA W Stan 0/2). The walk-back framing is that surgical coupling reflects position-mean structure that Stan correctly absorbs into `mu_position[Center]`, leaving the residual class with no remaining variance asymmetry.

**Mechanism stated ex ante.** The walk-back assumes that the cross-league surgical/Stan disagreement is method-driven (Stan absorbs the position mean correctly). An alternative reading: the disagreement is a power problem hidden by metadata Center mis-bucketing — the 46 metadata-Forward-but-adjudicated-Center modern bigs (AD, Giannis, Love, Plumlee, etc.) carry REB profiles that would resurrect coupling at the larger Center population. The walk-back validation under adjudicated positions tests this alternative directly. If adjudicated Stan REB × Center couples, the original walk-back was a power problem; if it remains null, the walk-back is robust to the inclusivity correction.

**Per-cell decision rule under adjudicated Stan REB residuals:**

| Condition | Disposition |
|---|---|
| CI overlaps 1.0 AND p_levene > 0.05 | **WALK-BACK UPHELD** — adjudicated Stan REB × Center remains null. The walk-back claim is robust to inclusivity correction; the original finding (surgical couples, Stan absorbs into position mean) holds under the larger Center cohort. |
| CI fully > 1.0 AND p_levene < 0.05 (re-coupling materializes) | **WALK-BACK FALSIFIED** — adjudication resurrects REB × Center coupling that metadata-bucketed Stan suppressed. The original walk-back was a power problem hidden by metadata mis-bucketing; the cross-league REB × Center retraction needs revision (NBA cell: was retracted, now couples under adjudicated bucket; cross-league 0/7 becomes 0/6 + 1 NBA re-coupled). |
| CI fully < 1.0 (inverted from existing direction) | **WALK-BACK FALSIFIED — INVERTED** — Stan ratio inverts; either the walk-back logic was wrong or the adjudicated cohort introduces a structural reversal. Either reading is publishable. |
| Power-limited per §2.5 | **INCONCLUSIVE**. |

**Aggregate H3 verdict:**
- 3 of 3 WALK-BACK UPHELD → the walk-back is robust under inclusivity correction. The cross-league §5.4.1 retraction stands. **The walk-back is itself validated by a pre-registered test of an alternative reading.**
- ≥ 1 of 3 WALK-BACK FALSIFIED → the walk-back is overturned at the NBA contribution layer. The cross-league §5.4.1 retraction needs re-opening; the surgical/Stan disagreement was a power problem, not a mechanism difference. Major paper revision.

H3 is methodologically the highest-stakes hypothesis — it is a pre-registered test of a walk-back's robustness, which is itself a methodology paper contribution (Migration §3.4 / paper §3.4 walk-back-without-rescue discipline).

### 3.4 H4 (power-gate sanity, not a finding) — Adjudication n_in lift

For each cell, the power gate per §2.5: `n_in_adj / n_in_meta ≥ 1.30`. Report the actual lift per cell. If any cell fails the gate, that cell is INCONCLUSIVE in its observable's aggregate verdict.

**Reporting commitment:** all 9 cells (3 seasons × 3 observables) are reported with their (n_in_meta, n_in_adj, lift ratio, power-gate disposition) regardless of which fail or pass.

## 4. Aggregate report framework

After per-cell, per-hypothesis dispositions are determined, the aggregate verdict is reported as a 3 × 3 table (3 hypotheses × 3 cells) with one of {PERSISTS / DIRECTIONAL-PERSISTS / PERSISTS-DIRECTIONAL / ATTENUATES / REGIME-NULL / INVERTED / WALK-BACK UPHELD / WALK-BACK FALSIFIED / WALK-BACK FALSIFIED-INVERTED / INCONCLUSIVE} per cell.

**Published narratives, pre-committed:**

| H1 BLK | H2 PTS | H3 REB walk-back | Cross-league paper revision |
|---|---|---|---|
| 3/3 PERSISTS | 3/3 DIRECTIONAL | 3/3 UPHELD | **Strongest outcome.** Adjudicated NBA arm strengthens the cross-league paper. §5.4–§5.4.2 add an "adjudicated NBA cells" section showing 3/3 PERSISTS at substantially larger n_in. Walk-back validated by independent test of the alternative reading. |
| 3/3 PERSISTS | 3/3 DIRECTIONAL | ≥1 FALSIFIED | Walk-back overturned. §5.4.1 REB retraction is itself walked back: surgical/Stan disagreement was a power problem hidden by metadata mis-bucketing. REB × Center re-couples cross-league under adjudication. Major paper revision required. |
| 2/3 PERSISTS, 1 ATTENUATES | mixed | 3/3 UPHELD | Magnitude band needs NBA-specific revision; walk-back robust. Paper §5.4.2 BLK NBA contribution reframed. |
| 0/3 PERSISTS (3/3 REGIME-NULL or INVERTED) | mixed | 3/3 UPHELD | NBA contribution to 11/11 BLK × Center cross-league claim falsified. Cross-league claim becomes 8/11; paper §5.4 substantially revised. Walk-back robust. |

All combinations are publishable. The four sample combinations above are illustrative, not exhaustive.

## 5. Discipline guards

Each item is an explicit pre-registration violation. Any occurrence flags the affected disposition as exploratory only and triggers a published methodology footnote.

1. **Threshold adjustment after firing.** The existing-range bands [1.26, 2.03] for BLK and [0.76, 1.02] for PTS, the power-gate ratio of 1.30, and the per-cell decision-rule conditions are locked. Adjusting any after compute invalidates the affected disposition.
2. **Classifier redefinition.** The adjudicated bucket is read verbatim from `position_adjudication_v12.json` (SHA256 `eb615269f09159e0d0ceaf071812b84750578d81a9a53b01dff5a1ac2ac9dcbd`). Re-running the v1.2 adjudication, re-judging any verdict, or modifying the override map after seeing residuals is a §11 violation across both papers.
3. **Cohort cap adjustment.** The Stan 200-player cap for 23-24 and 24-25 and the full ship for 25-26 are matched to the existing cross-league paper protocol. Removing the cap mid-run to expand n_in is a violation.
4. **Statistical-test substitution.** Levene's variance ratio is the load-bearing test. Substituting an alternative test (e.g., switching to Bartlett or F-test) after seeing Levene's outcome is a violation.
5. **Selective reporting.** All 9 cells (3 seasons × 3 observables) and both bucketing arms (metadata, adjudicated) are reported regardless of disposition. Reporting only the adjudicated cells that confirm the cross-league finding is a violation.
6. **Walk-back rescue.** If H3 returns WALK-BACK FALSIFIED, the response is to revise the cross-league §5.4.1 retraction honestly, not to find a methodology footnote that "rescues" the walk-back. The cross-league paper's §3 discipline of preserving walk-backs equal-prominence applies to walk-backs OF walk-backs as well.
7. **Adding observables.** The three observables (BLK, PTS, REB) are locked. Adding STL × Center or AST × Center after seeing patterns is a violation; new observables require a new pre-reg.
8. **Re-fitting v6.1.** The model is production-locked at the 2026-05-05 snapshot. Conditional re-scoring on adjudicated positions IS NOT performed because the model does not condition on position (residuals are computed against the existing v6.1 LOCKED predictions). Any v6.1 re-fit triggered by this analysis is a violation.

## 6. Output artifacts

All outputs under `D:/NBA Projections/RMD_SRC_PIPELINE/results/sloan_adjudicated/`:

- `n_in_lift_table.parquet` — per (season, observable): n_in_metadata, n_in_adjudicated, lift_ratio, power_gate_pass.
- `variance_ratios_metadata.parquet` — per (season, observable): σ_Center, σ_non-Center, ratio, bootstrap 95% CI, Levene's p, p_F, p_Bartlett. METADATA bucket (replicates existing §5.5).
- `variance_ratios_adjudicated.parquet` — same fields, ADJUDICATED bucket (load-bearing new).
- `dispositions.json` — per (season, observable, arm): disposition per §3 decision rule.
- `aggregate_verdict.md` — the 3 × 3 disposition table plus the headline narrative chosen from §4.
- `SLOAN_ADJUDICATED_RESULTS.md` — the umbrella report. Companion `.docx` produced via `scripts/md_to_docx.py` per existing paper-state workflow.

Every reported number cites the artifact and the row producing it. No prose-only figures.

## 7. Timing and commitment

- **Pre-registration committed:** the lock event is a git commit of `SLOAN_PRE_REG_TEST_1_ADJUDICATED_v1.0_LOCKED.md` to the NBAProjections `main` branch, with the commit SHA recorded in `RMD_SRC_PIPELINE/SHA_LOCK.txt` under a `## Sloan adjudicated Test 1 re-validation` section.
- **Analysis fires:** once, after sign-off. Single batch.
- **No re-runs.** If a methodological flaw in the test design is discovered after firing, the response is a new pre-reg (v1.1) with the corrected design, not re-running v1.0.
- **No re-fits of v6.1.**
- **Final report:** `SLOAN_ADJUDICATED_RESULTS.md` produced after analysis. Headline disposition matches the §4 framework. The cross-league paper §5.4–§5.4.2 are updated to integrate the adjudicated arm.

This pre-registration's discipline is invariant to whether the cross-league finding strengthens, attenuates, or falsifies under adjudication. All four outcome classes are publishable. The result is the result.

## 8. Sign-off

- **Filed by:** Claude Code (claude-opus-4-7[1m])
- **Sign-off requested from:** mr.nathanhumphrey@gmail.com
- **Repo:** https://github.com/mrnathanhumphrey-droid/NBAProjections
- **Cross-paper anchor SHAs (input):**
  - Cross-league paper paper-state: `paper_draft/PAPER_STATE_snapshot.md` at the repo HEAD at sign-off time.
  - RMD-SRC v1.2 amendment + adjudication artifact: `1bfdb4c` (amendment) + `eb615269f09159e0d0ceaf071812b84750578d81a9a53b01dff5a1ac2ac9dcbd` (artifact SHA256).
- **Lock event:** rename this file to `SLOAN_PRE_REG_TEST_1_ADJUDICATED_v1.0_LOCKED.md`; git add; git commit; append commit-SHA to `SHA_LOCK.txt` under a `## Sloan adjudicated Test 1 re-validation` section.
- **Subsequent steps:**
  1. Build `RMD_SRC_PIPELINE/src/sloan_adjudicated_test_1.py` (computes per-cell variance ratios under both buckets, applies decision rules, produces artifacts).
  2. Run on the 3-season NBA cohort × 3 observables × 2 buckets = 18 per-cell computations.
  3. Write `SLOAN_ADJUDICATED_RESULTS.md` with the 3 × 3 disposition table.
  4. Integrate into `paper_draft/section_5_empirical_validation.md` as §5.4-adjudicated, alongside existing §5.4.1–§5.4.2.

---

**End of draft v1.0.**
