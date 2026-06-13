# Probe B — contextual residue-class structure on v6.3-A residuals

**Date:** 2026-05-05
**Input:** `v6_3_A_residuals.csv` (15,376 player-games, post-Probe-A residuals)
**Stats tested:** PTS, REB, AST
**Cohorts:** 9 (position_class × cohort_class)
**Bootstrap:** 500 reps per cohort × stat = 13,500 total

---

## Verdict

**Probe B's strict hypothesis is NOT supported.** 0 of 15 testable cohort × stat cells beat the bootstrap null at p<0.05. Best p-value across the entire test grid is 0.176 (soph_Guard/REB). Best silhouette is 0.438 (vet_Guard/REB) — but inspection reveals it's driven by a single outlier configuration, not a genuine bimodal split.

**Read this as load-bearing.** v6.3-A absorbed everything box-score-only contextual axes can recover at one season's resolution. The residual structure that *would* support contextual residue-class theory at the strict level is not detectable in this data. This is exactly the strict-significance test framing Nate set up: in-season info absorbs most, and Probe B asks if context can absorb MORE on top — at p<0.05, the answer is no.

The negative is informative for the Sloan paper. It separates "in-season information channel works" (which v6.3-A confirmed) from "additional contextual residue-class structure exists at strict significance" (which Probe B does not confirm at this data resolution).

---

## Methodology summary

### Contextual configuration axes (648-dim space)
| Axis | Levels | How derived |
|---|---|---|
| opp_class | top/high/mid/bottom (4) | 24-25 final defensive rating quartile (pts allowed per 100 poss) |
| record_tier | top/mid/bottom (3) | opponent's win pct as of game date (24-25 final if <30 GP, else current) |
| pace_tier | fast/medium/slow (3) | combined-team possessions per game, global tercile across 25-26 |
| home_away | home/away (2) | `is_home` from box scores |
| role | starter/sixth/spot (3) | prior-10-games avg minutes (≥28 / 18-28 / <18) |
| season_phase | early/post_AS/last20 (3) | calendar (pre 2026-02-14) / post-AS pre last 20 / final 20 |

Total: 4 × 3 × 3 × 2 × 3 × 3 = **648 configurations**.

### Per-cohort × stat clustering test
1. Aggregate per-config: residual mean, var, skew, kurt + empirical CF on t ∈ [-3,3] step 0.1
2. Drop configs with <10 obs
3. Combined distance: z-normalized (d_moment + d_phi)/2, average linkage
4. Cut at k ∈ {2, 4, 6, 8, 10, 16, 32, 50}; pick k* = argmax silhouette
5. Bootstrap null: 500 reps with permuted config tags
6. Decision rule per spec: structure_detected iff k* ∈ [4, 16] AND p < 0.05

---

## Per-cohort verdict table

| Cohort | Stat | n_obs | n_configs (of 648) | k* | silhouette | p-value | verdict |
|---|---|---:|---:|---:|---:|---:|---|
| rookie_Center | PTS/REB/AST | 215 | **0** | — | — | — | insufficient_configs |
| rookie_Forward | PTS/REB/AST | 772 | **0** | — | — | — | insufficient_configs |
| rookie_Guard | PTS/REB/AST | 611 | **0** | — | — | — | insufficient_configs |
| soph_Center | PTS/REB/AST | 489 | **0** | — | — | — | insufficient_configs |
| soph_Forward | PTS | 2,207 | 46 | 2 | 0.247 | 0.588 | no_structure |
| soph_Forward | REB | 2,207 | 46 | 2 | 0.186 | 0.946 | no_structure |
| soph_Forward | AST | 2,207 | 46 | 2 | 0.244 | 0.862 | no_structure |
| soph_Guard | PTS | 2,568 | 65 | 2 | 0.223 | 0.786 | no_structure |
| **soph_Guard** | **REB** | 2,568 | 65 | 2 | 0.364 | **0.176** | no_structure (best p) |
| soph_Guard | AST | 2,568 | 65 | 2 | 0.255 | 0.890 | no_structure |
| vet_Center | PTS | 1,499 | 9 | 2 | 0.166 | 0.676 | no_structure |
| vet_Center | REB | 1,499 | 9 | 2 | 0.233 | 0.272 | no_structure |
| vet_Center | AST | 1,499 | 9 | 2 | 0.272 | 0.356 | no_structure |
| vet_Forward | PTS | 3,007 | 101 | 2 | 0.325 | 0.460 | no_structure |
| vet_Forward | REB | 3,007 | 101 | 2 | 0.366 | 0.516 | no_structure |
| vet_Forward | AST | 3,007 | 101 | 2 | 0.214 | 0.970 | no_structure |
| vet_Guard | PTS | 4,008 | 144 | 2 | 0.278 | 0.614 | no_structure |
| **vet_Guard** | **REB** | 4,008 | 144 | 2 | **0.438** | 0.234 | no_structure (best silhouette) |
| vet_Guard | AST | 4,008 | 144 | 2 | 0.240 | 0.962 | no_structure |

**Summary:** 0/15 testable cells reach p<0.05; 0/15 reach p<0.10; 1/15 (soph_Guard/REB) reaches p<0.20.

---

## Why the silhouettes are non-trivial yet still null

Every testable cell picks k*=2 — a binary outlier-vs-rest split — never the predicted k* ∈ [4, 16] hierarchical structure. Inspection of the highest-silhouette cells confirms this is not bimodal context structure but single-outlier-config dominance:

| Cell | sil | Cluster sizes | Outlier config(s) |
|---|---:|---|---|
| vet_Guard/REB | 0.438 | 143 / 1 | `mid_bottom_fast_away_sixth_last20` |
| vet_Forward/REB | 0.366 | 99 / 2 | `high_top_slow_away_starter_last20`, `top_mid_fast_home_starter_early` |
| soph_Guard/REB | 0.364 | 63 / 2 | `high_top_slow_home_sixth_early`, `top_top_slow_away_starter_early` |
| vet_Forward/PTS | 0.325 | 99 / 2 | `high_mid_medium_away_starter_last20`, `high_top_slow_home_starter_early` |
| vet_Guard/PTS | 0.278 | 143 / 1 | `top_top_fast_home_starter_last20` |

The outlier configs across cells share **no coherent contextual theme** (no consistent tanking signature, no role-stability pattern, no season-phase concentration). Different outliers per cell. The bootstrap null reproduces these single-outlier silhouettes via random permutation at p > 0.20.

---

## Tanking-detection check

The earlier (pre-fix) buggy run flagged 3 cells (rookie_Guard/REB, soph_Guard/REB, vet_Guard/PTS) where cluster 2 corresponded to "top opponent class + bottom current record tier" — the literal tanking signature. **That signal vanishes in the corrected run** because the buggy run had collapsed 4 of 6 axes; the fix restored the full 648-dim space and the tanking-detection cluster is no longer the dominant separator.

This means: even if there is a tanking-driven residual signature, it's not the strongest contextual axis when all six axes can compete. Either tanking-driven structure is below the noise floor, or it's confounded with axes that don't load on the tanking dimension.

---

## What's load-bearing for the paper

Add to §6 of the Sloan paper (or §8 if structured as multi-probe results):

> *"In a strict permutation test against bootstrap null at p<0.05, contextual residue-class structure beyond v6.3-A's per-player in-season update is not detectable in single-season 25-26 data across nine cohorts × three stats (27 cells, 0 reaches p<0.05; best p=0.176). The 648-dim contextual configuration space (opp_class × current_record_tier × pace × home/away × role × season_phase) is too sparsely populated at one season for a strict structural test — only 4 of 9 cohorts reach n_configs ≥ 20 at the 10-observation gate. The negative is consistent with two interpretations:
> (a) v6.3-A's per-player Gamma-Poisson update absorbs the box-score-only contextual signal recoverable at this resolution;
> (b) genuine residue-class structure may exist but requires multi-season pooling (≥3 seasons projected to lift retained-config count to ~150-300 per cohort) for the bootstrap null to be beatable.
> We do not interpret this negative as falsifying the residue-class theorem itself — only its detectability in single-season NBA data with box-score-only contextual axes. The follow-up multi-season backtest (currently the next gate) will provide the data to resolve (a) vs (b)."*

---

## What the test failed to test

Five cohorts × stats = 12 of 27 cells couldn't run because n_configs_retained = 0:
- **All 3 rookie cohorts (215-772 obs)**: too few obs for any 6-axis combination to hit 10
- **soph_Center (489 obs)**: same

For the underpowered cells, "no_structure" is unfalsifiable. The right interpretation is: **insufficient data** for the test rather than evidence of absence. Multi-season would partially resolve.

---

## Caveats / honest framing

1. **One season only.** Multi-season replication is the obvious next step. With 3-5 seasons pooled, each cohort would have ~3-5x the obs and 50-100% more configs at the gate. Repeat Probe B then.

2. **648 configs may be the wrong granularity.** A coarser axis set — say opp_class × record_tier × season_phase × home_away (72 configs) — could expose structure that 648 obscures by over-fragmenting. This is a follow-up.

3. **Box-score-only restriction.** Probe B used purely derivable axes per the original task spec. Other contextual axes (lineup-level pace, opponent-specific defensive matchups, rest days, recent injury history) might carry contextual residue-class signal that this test is blind to.

4. **k*=2 always.** Hierarchical agglomerative with average linkage tends to maximize silhouette at k=2 when data has one or two outlier points and a uniform rest — exactly what we see. A different validity metric (gap statistic, Calinski-Harabasz with elbow) might pick a higher k*. Sensitivity analysis is a follow-up.

5. **The bug-fix story.** First run had a `game_id` type-mismatch (int after CSV roundtrip vs string in parquet) that silently failed 4 of 6 axis lookups, collapsing 648 → effectively 12 configs. That run produced 3 ambiguous "p<0.05" hits all pointing at "top defensive opp + bottom current record" — a tanking signature. **That finding does not survive the fix.** When all 6 axes are properly populated, the tanking signature is no longer the dominant cluster split. Documented for transparency.

---

## Output artifacts

- `result_contextual_a_final.md` — this document
- `result_contextual_a_final_verdicts.csv` — per-cell verdict + p-value table
- `result_contextual_a_final_per_cohort.csv` — config → cluster assignments per cohort
- `result_contextual_a_final_bootstrap.csv` — full null distribution (15 cells × 500 reps × ~8 k-values)
- `result_contextual_a_final_top_pairs.csv` — empty (0 cells reached structure_detected verdict)
- `summary.json` — machine-readable summary

## Implications for next steps

1. **Multi-season backtest is the right gate.** It was already next on the queue; Probe B's null result reinforces the urgency. With 3+ seasons, retained configs will rise to a level where the strict bootstrap null becomes a fair test rather than a sparsity-limited one.

2. **Coarser-axis follow-up Probe B'.** Run a 72-config (opp_class × record_tier × season_phase × home_away) test on the same residuals before multi-season is available. Cheaper data — faster signal.

3. **The Sloan paper's contextual claims must be honest.** Probe A's 14-18% MAE reduction is the headline. Probe B's null at strict significance is reported transparently. The framework's predictive value lies in the cohort-uncertainty scaling (rookie > soph > vet) confirmed by Probe A, not in unverified contextual residue-class clusters.
