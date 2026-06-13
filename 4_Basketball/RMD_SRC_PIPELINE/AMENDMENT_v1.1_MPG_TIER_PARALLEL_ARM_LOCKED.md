# Amendment v1.1 — MPG-tier role-cohort parallel arm

**Type:** New analytical arm (additive). Does NOT amend or retract any operationalization, threshold, falsifier, or disposition in `PRE_REG_NBA_RMD_SRC_FULL_LOCKED.md` (v1.0, locked at commit `db0ed9a899c28691183cd5b640f460c10f3c2a75`). The usage-tier arm of the NBA full-pipeline RMD-SRC study stands as the canonical first-arm result; this amendment runs a second parallel arm on the same data with a different role-cohort operationalization and pre-commits a cross-arm comparison.

**Authored:** 2026-06-01.
**Status:** DRAFT v1.1 — pre-sign-off. Lock event is a git commit of this file (renamed to `AMENDMENT_v1.1_MPG_TIER_PARALLEL_ARM_LOCKED.md`) plus an update to `SHA_LOCK.txt` recording the amendment commit-SHA alongside the v1.0 SHA.
**Author:** Claude Code (claude-opus-4-7[1m]).
**Filed before:** any inspection of any MPG-tier-derived cell-level statistic. The usage-tier partition was inspected at the K-and-cell-counts level (substrate ledger row, Step 0/1 diagnostic) and at no observable level.

## 1. Why this exists

The user-recorded methodological motivation for this amendment, in the user's own language: **"we need to see the diagnostic because we found signals in both measures throughout the study."** Across NBA work to date (v6.1 LOCKED training, the cross-league replication paper, the playoff Tier-1 hypotheses, the cross-season variance findings) the role-cohort axis has been operationalized both as MPG-tier (in the v6.1 model class structure that the production system deploys against) and as usage-tier (in the variance-decomposition framing that this RMD-SRC pipeline locked at v1.0). Both measures have surfaced substantive structure in independent work. The full-pipeline run is the natural place to test which operationalization the RMD-SRC framework's machinery itself prefers, and where the two operationalizations diverge in regime classification.

The v1.0 usage-tier arm's Step 0/1 output (`results/P0_diagnostic.md`, derived from SHA `db0ed9a`) surfaced two structural findings that this amendment is partly designed to triangulate against:

1. No Center × High_usage cell survived the sparse-cell collapse in the usage-tier arm. Elite-Center high-usage substrate (Embiid, Jokić, Towns) pooled into `Center × Mid × Mid_usage`. The MPG-tier arm is expected to preserve a Center × High-MPG cell (≥28 MPG) because elite Centers are uniformly high-MPG starters even when their usage rate sits at 30 rather than 36.
2. No Center × Deep_vet cell survived. The MPG-tier arm may or may not preserve one; if it does, the BLK × Center × Deep_vet structural test that the cross-league paper named as a forward-watch substrate becomes testable at the partition level.

These two structural reads are framing context for the comparison, not threshold-tuning targets. The amendment locks before MPG-tier compute fires and is not adjusted after the MPG partition's K materializes.

## 2. Locked operationalizations (MPG-tier arm)

### 2.1 Data scope

Identical to v1.0 §2.1: 2019-20 through 2025-26 regular-season box scores from `D:/NBA Projections/data/parquet/historical_box_scores.parquet`, with the same player inclusion criteria (≥ 20 games and ≥ 10 MPG per season). The MPG-tier arm operates on the same qualifying player-season set as the usage-tier arm — exactly 2,798 player-seasons at the v1.0 SHA — so the arms are matched-cohort comparable.

### 2.2 MPG-tier role-cohort (the only operational difference vs v1.0)

Role-cohort is classified by **mean MPG in the same season** (not prior-season USG%). The locked thresholds:

- **Starter:** mean MPG ≥ 28.0
- **Rotation:** mean MPG ∈ [18.0, 28.0)
- **Bench:** mean MPG ∈ [10.0, 18.0)

(Bench's lower bound is the qualification floor; players with mean MPG < 10 are not in the qualifying set.)

**Same-season vs prior-season scoping rationale.** Usage-tier role-cohort uses *prior-season* USG% because USG% is a derived statistical-style covariate that aligns with the v6.1 model's "prior season covariate" structure and avoids endogeneity with the same-season trajectory. MPG-tier role-cohort uses *same-season* MPG because mean MPG is the same-season operational definition that "Starter / Rotation / Bench" labels carry in NBA usage and that the existing depth-chart and rotation analysis pipelines use in production. The two arms therefore differ on *two* axes: the source variable (USG% vs MPG) and the temporal scoping (prior-season vs same-season). This is the honest operationalization — both arms reflect how the respective measures are deployed in the wild — and the cross-arm comparison's substantive content includes both axes.

**Rookie handling.** No defaulting is required for MPG-tier because mean MPG is computed from the player's *own* current-season qualifying games. The first-season-NBA edge case the usage-tier arm had to default-to-Mid does not exist for MPG-tier.

### 2.3 Sparse-cell collapse (MPG-tier arm)

Identical rule and identical floors to v1.0 §2.2:
- Cell counts < 50 player-seasons across the 7-season panel OR < 5 in any single season → merge with nearest neighbor.
- Axis preference: role-cohort first (Starter↔Rotation, Rotation↔Bench), then years-pro, then position.
- Deterministic agglomerative merge with sparsest-first ordering, alphabetical cell-id tie-break.

The final K_mpg is determined by the data and recorded in `results/P0_collapse_map_mpg.json`.

### 2.4 Pipeline observables, time axis, train/holdout, decomposition gates

All identical to v1.0:
- Observables: PTS_per36, REB_per36, AST_per36, BLK_per36.
- Time axis: 7 seasons, 2019-20 → 2025-26.
- Train window: 2019-20 → 2023-24 (5 seasons). Holdout: 2024-25 + 2025-26 (2 seasons).
- Step 2 thresholds: `ε_μ = 0.02`, `ε_σ² = 0.05`.
- Step 4a axes: `opp_DEF_RTG_tertile` and `home_away` (two-axis, ≥ 0.10 cleanness gate, alphabetical tie-break).
- F1 ≥ 0.90, F2 < 0.50, F3 < 0.30, F4 κ < 0.40.
- Step 5: r ≥ 0.80 (partition-level signature transfer).
- Comparative arm vs v6.1 LOCKED: per-cell regime-label recovery, per-cell r ≥ 0.50.

### 2.5 Step 4a `opp_DEF_RTG_tertile` interaction with same-season scope

The Step 4a `opp_DEF_RTG_tertile` sub-partition uses prior-season opponent defensive rating, which is well-defined for either arm. The MPG-tier arm's same-season role-cohort scope is independent of the sub-partition axis; no interaction issues to flag.

## 3. Cross-arm comparison pre-commitment

This amendment pre-commits a single load-bearing cross-arm comparison reported as §4.6.x of the methodology paper section on NBA. The comparison runs after both arms complete Steps 0–6 + F1–F4 + comparative-arm runs in §9 of v1.0.

### 3.1 Regime-label cross-arm agreement matrix

For each observable (PTS_per36 / REB_per36 / AST_per36 / BLK_per36), build the per-(player, season) regime label under both arms:
- `regime_usg(player, season, obs)` from the usage-tier partition's cell-level regime label as classified in Step 2 of the usage-tier arm.
- `regime_mpg(player, season, obs)` from the MPG-tier partition's cell-level regime label.

For each observable, compute Cohen's κ between `regime_usg` and `regime_mpg` across the per-(player, season) records that qualify under both arms (matched-cohort intersection — expected to be the full 2,798 player-seasons since both arms share the qualifying set).

**Cross-arm agreement bands (locked, pre-fit):**
- **κ ≥ 0.60 — High agreement.** The two operationalizations classify cells into the same regime; the role-cohort axis is robust to how it is measured. Reported as substrate-level invariance.
- **κ ∈ [0.30, 0.60) — Partial agreement.** The two operationalizations agree on direction but classify some cells differently. The disagreements are localized in the cross-tab; the substantive read is "both measures are picking up signal, with measurement-level drift."
- **κ < 0.30 — Low agreement.** The two operationalizations classify cells differently. The substantive read is "role-cohort axis as a category is operationalization-dependent at the NBA level." This is a substrate-level finding about the role-cohort axis itself, reported with full prominence regardless of which arm's downstream F-falsifiers fire.

### 3.2 Per-cell PASS / TIE / LOSE differential

The §9 comparative arm of v1.0 returns a per-cell PASS / TIE / LOSE verdict for the usage-tier arm vs v6.1 LOCKED. The MPG-tier arm produces a parallel PASS / TIE / LOSE verdict vs the same v6.1 LOCKED.

**Cross-arm differential table (locked):**
For each observable, report a 3 × 3 table of (usage-tier verdict × MPG-tier verdict). Cell counts in the diagonal indicate cross-arm consistency at the verdict level. Off-diagonal entries — e.g., usage-tier PASSes a cell that MPG-tier LOSEs — indicate operationalization-dependent comparative outcomes against the v6.1 LOCKED baseline. The off-diagonal patterns are themselves substrate findings: a cell that one arm flags as RMD-SRC-recovers-structure and the other arm flags as RMD-SRC-overfits is the kind of finding the paper's discipline is designed to surface.

### 3.3 F1–F4 cross-arm firing pattern

For each falsifier (F1, F2, F3, F4) and each observable, report whether the usage-tier arm fires, whether the MPG-tier arm fires, and how the firings localize.

**Locked reporting commitment:** the 4 (falsifier) × 4 (observable) × 2 (arm) = 32 cells of the falsifier-firing matrix are all printed in `results/comparative_arm_F1_F4_matrix.json` regardless of how many fire. No selective reporting.

### 3.4 What does NOT count for the cross-arm comparison

- **Re-tuning either arm's role-cohort thresholds after observing the κ.** The locked threshold sets (25.0 / 15.0 for usage-tier; 28.0 / 18.0 for MPG-tier) are not adjustable mid-stream.
- **Adding a third role-cohort operationalization mid-stream** (e.g., usage-rate × MPG composite, starts-fraction, depth-chart-rank tertile). A third arm requires a new amendment with its own SHA.
- **Privileging one arm's verdict over the other in the headline.** Both arms produce equally-prominent reports. The headline framing is "we ran both; here is what the cross-arm comparison surfaced."
- **Re-running the usage-tier arm with the MPG-arm's same-season scoping** (or vice versa). The same-season-vs-prior-season scoping difference is *part of the comparison*, not a confound to be controlled away.

## 4. Discipline guards (v1.0 untouched)

This amendment is strictly additive. Specifically:

- **v1.0 SHA `db0ed9a` is preserved.** No file under SHA `db0ed9a` is modified. The usage-tier `P0_partition.parquet`, `P0_collapse_map.json`, and `P0_diagnostic.md` produced under v1.0 are preserved at their current content.
- **v1.0 pre-reg document is not edited.** `PRE_REG_NBA_RMD_SRC_FULL_LOCKED.md` is left exactly as committed. A reader of the v1.0 pre-reg sees a study that locks the usage-tier arm and reports its results; they then read this amendment to see what the second arm added.
- **v1.0 results stay reported.** When Steps 2–6 complete, both arms' results are reported. The usage-tier arm's results are not retroactively recharacterized as "partial" or "preliminary." They are reported as the first arm; the MPG-tier arm is reported as the second arm; the cross-arm comparison is reported as the third finding.
- **No falsifier rescue.** If F2 fires on usage-tier and not on MPG-tier (or vice versa), the firing remains in the v1.0 / v1.1 ledger as fired. The cross-arm difference is then a finding about operationalization sensitivity, not a rescue of the firing.

## 5. Outputs (parallel arm artifacts)

All outputs written under `D:/NBA Projections/RMD_SRC_PIPELINE/results/` with `_usg` and `_mpg` suffixes on every per-arm artifact:

- `P0_partition_usg.parquet` (renamed from existing `P0_partition.parquet` for clarity — content preserved, no row-level changes)
- `P0_partition_mpg.parquet` (new)
- `P0_collapse_map_usg.json` (renamed)
- `P0_collapse_map_mpg.json` (new)
- `P0_diagnostic_usg.md` (renamed)
- `P0_diagnostic_mpg.md` (new)
- (Subsequent steps: `moment_trajectories_{usg,mpg}.parquet`, `trajectory_classification_{usg,mpg}.parquet`, etc.)

**Cross-arm comparison artifacts:**
- `crossarm_regime_kappa.json` — per-observable κ + agreement-band disposition.
- `crossarm_PASS_TIE_LOSE_matrix.json` — per-observable 3×3 cross-tab of v1.0 vs v1.1 comparative-arm verdicts.
- `crossarm_F1_F4_matrix.json` — 4 × 4 × 2 falsifier-firing matrix.
- `CROSSARM_RESULTS.md` — umbrella cross-arm report.

The rename of `P0_partition.parquet → P0_partition_usg.parquet` (and the two companion files) is a content-preserving file-rename, locked as part of this amendment. The content's SHA256 (from the v1.0 `MANIFEST.txt`) is verified post-rename and re-recorded in `MANIFEST.txt` under the new filename.

## 6. Sign-off

- **Filed by:** Claude Code (claude-opus-4-7[1m])
- **Sign-off requested from:** mr.nathanhumphrey@gmail.com
- **Repo:** https://github.com/mrnathanhumphrey-droid/NBAProjections
- **Lock event:** rename this file to `AMENDMENT_v1.1_MPG_TIER_PARALLEL_ARM_LOCKED.md`; git add the renamed file; git commit; append the new commit-SHA to `RMD_SRC_PIPELINE/SHA_LOCK.txt` under a `## v1.1 amendment` section. Then re-run Step 0/1 with the MPG-tier flag; the script verifies the v1.1 SHA at startup before reading any data.

---

**End of draft v1.1.**
