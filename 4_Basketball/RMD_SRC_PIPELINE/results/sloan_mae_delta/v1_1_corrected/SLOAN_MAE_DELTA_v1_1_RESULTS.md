# Sloan MAE Delta Test 2 — v1.1 CORRECTED Results

**v1.1 amendment commit:** `d59f12b` (`AMENDMENT_v1.1_BUG_CORRECTION_LOCKED.md`)
**Original v1.0 pre-reg commit:** `49fd54b`
**Original v1.0 results commit (PRESERVED for transparency):** `189b61c`
**Adjudication artifact SHA256:** `eb615269f09159e0d0ceaf071812b84750578d81a9a53b01dff5a1ac2ac9dcbd`

---

## ★ Headline disposition under v1.1 (corrected formula)

**The v1.0 MAE-delta headline ("+5.5% REB improvement on the 46 flip cohort, p=0.008") is RETRACTED.** It was driven by a sign error and a phantom linear term in the Stan position-conditional aging-curve formula (full bug write-up in `AMENDMENT_v1.1_BUG_CORRECTION_LOCKED.md` §1).

Under the corrected formula, the predict-time effect of switching position from metadata-Forward to adjudicated-Center is essentially zero for REB on the 46 flip cohort:

| Cohort | Stat | n | MAE_metadata | MAE_adjudicated | Delta | CI95 | Wilcoxon p | Disposition |
|---|---|---|---|---|---|---|---|---|
| A_flip | PTS | 8 | 4.953 | 5.161 | -0.208 (-4.2%) | [-0.396, +0.015] | 0.195 | **NULL / DIRECTIONAL** |
| A_flip | REB | 8 | 3.165 | 3.167 | **-0.0024 (-0.1%)** | [-0.0034, -0.0016] | 0.008 | **NULL** (delta below 0.05 threshold) |
| A_flip | AST | 8 | 1.298 | 1.298 | 0 | [0, 0] | 1.000 | NULL (no offset) |
| A_flip | BLK | 8 | 0.288 | 0.288 | -0.0001 | [-0.003, +0.002] | 0.844 | NULL |
| B_all_230 | PTS | 46 | 4.474 | 4.533 | -0.059 (-1.3%) | [-0.161, +0.017] | 0.570 | NULL |
| B_all_230 | REB | 46 | 1.708 | 1.708 | -0.0003 | [-0.003, +0.003] | 0.049 | NULL |
| B_all_230 | AST | 46 | 1.001 | 1.001 | 0 | [0, 0] | 1.000 | NULL |
| B_all_230 | BLK | 46 | 0.204 | 0.204 | 0 | [-0.0007, +0.0006] | 0.959 | NULL |
| C_non_flip | (all 4 stats) | 30 | (matches metadata) | (matches metadata) | 0 | [0, 0] | 1.000 | PASS |

Aggregate H1 verdict under v1.1: **0/2 MAE-PERSISTS, 2/2 NULL.** The MAE delta hypothesis is not supported under the corrected formula.

**The Wilcoxon p=0.008 for REB A_flip is statistically significant but the magnitude is -0.0024 REB/game — five hundredths of one rebound, well below the pre-committed 0.05 small-magnitude threshold.** The statistical significance is on the wrong side (delta is slightly negative, meaning adjudicated very-slightly REGRESSES MAE) and the magnitude is small enough to be a numerical artifact of the Stan posterior point estimates used for parameter values. Disposition: **NULL.**

---

## Pipeline integrity (H4)

**PASS in all 4 cells.** Cohort C max |delta_mu| = 0.00e+00. The bug did NOT affect Cohort C because non-flip players have `metadata_bucket == adjudicated_bucket`, so the factor is `exp(0) = 1.0` regardless of formula error. The integrity check was a necessary-not-sufficient check; it caught zero non-flip drift but missed the buggy flip-player formula because v1.0 had no oracle for the FLIP-player delta.

---

## Per-named-player projections (v1.1 — Sloan-talk version)

For the 8 priority players from cross-league paper §5.4.1, 25-26 projections under metadata-Forward vs adjudicated-Center:

| Player | Stat | Stan factor | mu_metadata | mu_adjudicated | actual | MAE_meta | MAE_adj | Δ |
|---|---|---|---|---|---|---|---|---|
| Anthony Davis | PTS | 1.038 | 23.27 | **23.57** | 23.44 | 0.177 | 0.129 | **+0.048** |
| Anthony Davis | REB | 1.000 | 11.47 | 11.46 | 12.73 | 1.262 | 1.267 | -0.005 |
| Anthony Davis | AST | 1.000 | 3.55 | 3.55 | 3.23 | 0.323 | 0.323 | 0 |
| Anthony Davis | BLK | 1.004 | 1.99 | 2.00 | 1.90 | 0.086 | 0.095 | -0.009 |
| Giannis Antetokounmpo | PTS | 1.022 | 28.44 | **28.49** | 34.41 | 5.963 | 5.919 | **+0.044** |
| Giannis Antetokounmpo | REB | 1.000 | 11.59 | 11.59 | 12.20 | 0.603 | 0.606 | -0.003 |
| Giannis Antetokounmpo | AST | 1.000 | 6.42 | 6.42 | 6.79 | 0.369 | 0.369 | 0 |
| Giannis Antetokounmpo | BLK | 1.002 | 1.07 | 1.07 | 0.83 | 0.236 | 0.238 | -0.003 |
| Kristaps Porziņģis | PTS | 1.011 | 19.06 | 18.68 | 24.92 | 5.857 | 6.244 | -0.387 |
| Kristaps Porziņģis | REB | 1.000 | 6.79 | 6.79 | 7.81 | 1.014 | 1.015 | -0.001 |
| Kristaps Porziņģis | AST | 1.000 | 2.22 | 2.22 | 3.79 | 1.563 | 1.563 | 0 |
| Kristaps Porziņģis | BLK | 1.001 | 1.52 | 1.52 | 1.78 | 0.260 | 0.259 | +0.002 |
| Kevin Love | PTS | 1.196 | 5.00 | 5.40 | 14.64 | 9.634 | 9.240 | +0.394 |
| Kevin Love | REB | 0.999 | 3.59 | 3.58 | 12.69 | 9.102 | 9.106 | -0.004 |
| Kevin Love | AST | 1.000 | 1.12 | 1.12 | 3.95 | 2.839 | 2.839 | 0 |
| Kevin Love | BLK | 1.023 | 0.13 | 0.13 | 0.53 | 0.403 | 0.401 | +0.003 |

Among the 4 priority players with actuals:
- AD PTS: small improvement (0.048)
- Giannis PTS: small improvement (0.044)
- Porziņģis PTS: small regression (-0.387) — `Stan factor 1.011` × base PTS 19.06 = 19.27, minus -0.587 Center additive = 18.68 < 23.27 metadata, but actual is 24.92, so the Center additive offset moves AWAY from actual
- Love PTS: small improvement (0.394) — Love's actual PTS in 25-26 was 14.64 (he barely played), so the Center additive offset moves prediction TOWARD actual

The Sloan-talk version cannot make a per-named-player claim of "X% MAE reduction." The per-player deltas are small, mixed direction, and dominated by the PTS Center additive's calibration on heterogeneous Center subcohorts.

---

## What v1.1 confirms and what it rules out

### Confirmed: §5.4 walk-back falsification is a VARIANCE-ratio result, not a mean-prediction result

The cross-league paper §5.4.1 walk-back falsification (10/10 cells across NBA + WNBA + NCAA M + NCAA W, committed `4a4a595`) tested whether residual VARIANCE for Center vs non-Center is consistent with the metadata partition. It is not — the variance signature is real, big-bias, and reproduces across 4 leagues.

The MAE delta test in this sub-pre-reg tested a different question: do v6.1 LOCKED's point predictions improve under adjudicated bucketing? Under the corrected formula: **NO, they don't materially.** v6.1 LOCKED's point predictions are largely position-invariant at production time because the Stan model's fitted `age_tilt_player[p]` random effect absorbs position information at fit time. Switching position at predict time only shifts the quadratic-only aging-curve component, which is small relative to the player random effect.

These two findings (variance signature is real / point predictions are position-invariant) are CONSISTENT and methodologically interesting:
- **The variance signature lives in `mu_position[k] + sigma_position` interaction**, which determines how variance gets pooled across Center vs non-Center groups. Adjudicated bucketing changes which group's variance pool each player contributes to.
- **The point predictions live in `mu_player[p]` + age curve**, which is largely fixed per-player. Switching position barely shifts mu_player[p]'s posterior at predict time (it was fit under the original prior).

### Ruled out: front-office point-prediction-bias claim

v1.0's headline was "metadata mis-bucketing produces measurably biased point projections on 46 modern bigs." Under v1.1, this claim is FALSIFIED. v6.1 LOCKED's point projections for the 46 flip players are not measurably biased by metadata-Forward bucketing — they're driven by the fitted player random effect, which absorbed the position information at fit time.

### Still on the table: variance-band miscalibration

v6.1 LOCKED's variance multipliers tighten σ for (REB, Guard), (AST, Forward), (BLK, Guard). For the 46 F→C flip players under metadata-Forward bucketing, AST σ is tightened by × 0.819 (the Forward AST multiplier). Under adjudicated-Center bucketing, no AST tightening applies, so σ is wider.

If actual AST variance for the 46 modern bigs is wider than v6.1 LOCKED's metadata-bucketed σ allows, the confidence intervals are too narrow for these players. This is a testable claim but requires a NEW sub-pre-reg (different test statistic, different decision rule, different cohort intersection).

**This is the open Sloan paper §6 direction** — a more nuanced front-office claim: "variance bands, not point predictions, are systematically miscalibrated for the 46 modern bigs under v6.1 LOCKED metadata bucketing." A v1.2 sub-pre-reg could test this via z-score residual sd, log-likelihood scoring, or interval coverage.

---

## v1.0 results retraction (per amendment §5 guard #4)

The following claims from v1.0 results commit `189b61c` and any derived talk-version material are RETRACTED:

- "REB MAE 3.165 → 2.990 = +0.175 REB/game (+5.5%) on the 46-flip cohort"
- "Anthony Davis REB MAE: 1.26 → 0.91 (-28%)"
- "Giannis REB MAE: 0.60 → 0.34 (-43%)"
- "Porziņģis REB MAE: 1.01 → 0.91 (-10%)"
- "PTS MAE 4.953 → 5.970 = -1.018 (-20.5%) REGRESSES"
- "v6.1 LOCKED's PTS Center additive offset of -0.587 is mis-calibrated for the 46 adjudicated-Center stretch-bigs"

The retraction is recorded here, in the v1.1 results doc, and is referenced from `SHA_LOCK.txt`. The v1.0 results files at `results/sloan_mae_delta/` are preserved at commit-189b61c content as a record of the buggy fire. The Sloan paper main text uses ONLY v1.1 numbers.

The retraction is itself a worked example of pre-registration discipline: the bug was caught by user-driven verification after the buggy commit was pushed, and the discipline of preserving v1.0 + correcting under v1.1 + publishing both prevents either silent edit or selective reporting.

---

## Sloan paper revision targets (v1.1)

- **§5.4 cross-league walk-back falsification:** stands. Variance-ratio result is 10/10 across 4 leagues, unchanged by v1.1.
- **§6 front-office decision relevance:** rewrite to drop the point-prediction MAE claim. Replace with:
  1. The cross-league variance signature finding (substrate result).
  2. The methodology paper's worked example: how a Stan aging-curve sign error produced a false-positive headline at v1.0, and how SHA-chained discipline + user verification + amendment caught and corrected it without retroactive history rewrite.
  3. The open direction: variance-band miscalibration for the 46 modern bigs (next sub-pre-reg).
- **§6.2 (proposed new subsection):** v1.0 → v1.1 amendment trajectory as a Sloan-relevant example of pre-registration discipline in practice. The discrepancy between v1.0 and v1.1 is itself a methodology paper contribution — concrete evidence that "fix-in-place + silent edit" would have produced a false-positive published result, and that SHA-chained discipline + amendment protocol prevents this failure mode.

---

## Discipline compliance (v1.1)

Per amendment §5 guards:
1. Magnitude thresholds 0.05 / 0.15 REB/game UNCHANGED from v1.0. ✓
2. v1.2 adjudication artifact unchanged (SHA256 `eb615269...`). ✓
3. v6.1 LOCKED parameters unchanged. No Stan re-sample, no offset re-validation. ✓
4. No retroactive narrative reshaping. v1.0 results preserved in-place; v1.1 published in `v1_1_corrected/` subfolder. ✓
5. Both v1.0 and v1.1 fired-arm numbers published. v1.0 retracted-with-correction; v1.1 authoritative. ✓
6. The v1.1 amendment was filed BEFORE the v1.1 fire. Bug discovered via verification, formula corrected, amendment locked at commit `d59f12b`, then re-scoring executed. ✓
7. v1.0 commit `189b61c` not amended in git history (no `git rebase`, no `--amend`, no force-push). Its content stays at fired-with-bug record. ✓

---

## Companion figure status

`paper_draft/figures/forward_misbucket_scatter.png` (committed `49fd54b`) is UNCHANGED by v1.1. The scatter figure is independent of the Stan aging-curve formula — it plots metadata-Forward vs adjudicated-Center cohort by (height, REB/36) using game-log actuals, not v6.1 predictions. The visual is still valid for the cross-league §5.4 narrative. The figure's caption should be revised to align with v1.1's framing (variance signature, not point-prediction improvement).

---

**End of v1.1 results.**
