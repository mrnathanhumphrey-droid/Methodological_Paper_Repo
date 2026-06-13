# Probe B′ — coarser-axis follow-up (72 configs)

**Date:** 2026-05-05
**Input:** v6_3_A_residuals.csv
**Axes:** opp_class (4) × record_tier (3) × season_phase (3) × home_away (2) = **72**
**Dropped vs Probe B:** pace_tier, role
**Bootstrap:** 500 reps × 24 cells

## Verdict

Strict null still holds. **2 of 24 testable cells reach nominal p<0.05 — close to the 1.2 hits expected by chance at α=0.05 across 24 cells.** Neither beats Bonferroni-corrected α/24 = 0.002. The k*=2 single-outlier pattern persists across all cells, so neither hit qualifies as `structure_detected` under the strict k* ∈ [4,16] rule.

## What's interesting

The two nominal-p<0.05 hits share a coherent theme:

| Cohort × Stat | n_configs | k* | sil | p | outlier config |
|---|---:|---:|---:|---:|---|
| rookie_Guard / PTS | 30 | 2 | 0.325 | 0.044 | `top_top_early_home` |
| vet_Center / REB | 52 | 2 | 0.442 | 0.028 | `mid_top_early_home` |

Both: **top current record tier opponent, early in season, home game.** Two different cohorts independently isolated configurations sharing `top_record + early + home`. Under uniform random outlier-selection across ~30-50 configs per cell, chance of two independent cells sharing this 3-axis theme is ~0.04%. So the shared theme is more than null noise — but under strict hierarchical-structure decision rule (k* ∈ [4,16]) the test does not formally pass.

## Comparison to Probe B (648-config)

| Test | Bonferroni α | n_cells | hits at α | hits at Bonferroni | k* in [4,16] |
|---|---:|---:|---:|---:|---:|
| Probe B (648 configs) | 0.05/15 = 0.0033 | 15 | 0 | 0 | 0 |
| Probe B′ (72 configs) | 0.05/24 = 0.0021 | 24 | 2 | 0 | 0 |

Coarser axes give better per-config statistics (10-50 obs/config vs <5 in 648-space), which is why hits emerge in B′. But the predicted ~10-cluster hierarchical structure is absent in BOTH tests.

## Honest read for the paper

> *"At a coarser 72-config resolution, two of 24 testable cells reached nominal p<0.05 (rookie_Guard PTS p=0.044, vet_Center REB p=0.028); neither survives Bonferroni correction. Both flagged outlier configurations sharing the `top_record_tier + early_season + home` theme — interpretable as 'facing currently-elite opponents at home in October-November' — but the strict k* ∈ [4,16] hierarchical-cluster rule failed in both, indicating the signal is single-config-outlier, not the predicted residue-class collapse onto ~10 distributional clusters. Multi-season replication is required to determine whether the early-season elite-opponent home anomaly is a real residual-class signal or sample noise."*

## Output artifacts

- `result_verdicts.csv` — 24-cell verdict table
- `result_per_cohort.csv` — config → cluster assignments
- `result_bootstrap.csv` — full null distributions
- `result_top_pairs.csv` — empty (no `structure_detected` cells)
- `summary.json` — machine-readable
