# Amendment v1.1 — Bug correction to v1.0 Stan aging-curve delta formula

**Type:** Bug correction. Documents a computational error in v1.0's (`SLOAN_PRE_REG_TEST_2_MAE_DELTA_v1.0_LOCKED.md`, commit `49fd54b`; results commit `189b61c`) implementation of the Stan position-conditional aging-curve delta. Locks the corrected formula and re-fires under it. **v1.0 results are NOT retracted** — they remain published as the "fired-with-bug" record per pre-reg §5 guard #5 (selective reporting forbidden) and the discipline of preserving fired results regardless of outcome. v1.1 results are reported alongside v1.0 results as the "fired-with-corrected-formula" record. The user-facing Sloan paper integrates only v1.1's corrected numbers; the methodology appendix discloses both fires for transparency.

**Authored:** 2026-06-02 (same day as v1.0 lock and fire).
**Status:** DRAFT v1.1 — pre-sign-off. Lock event is a git commit of this file (renamed to `AMENDMENT_v1.1_BUG_CORRECTION_LOCKED.md`) plus an update to `SHA_LOCK.txt`. The re-scoring under corrected formula does not fire until this SHA exists.
**Author:** Claude Code (claude-opus-4-7[1m]).
**Filed before:** any inspection of per-cell MAE under the corrected formula. The metadata-bucket re-scored numbers are unchanged (the bug only affected the adjudicated-bucket Stan-level aging shift, which is zero for non-flip players). The adjudicated-bucket numbers under corrected formula have not been computed.

## 1. The bug

`sloan_mae_delta_rescore.py` v1.0 (committed 49fd54b) computed the Stan position-conditional aging shift via:

```python
def age_tilt(pos_idx, age, posterior):
    peak = posterior["peak_age_pos"][pos_idx]
    beta = posterior["beta_age_pos"][pos_idx]
    gamma = posterior["gamma_pos"][pos_idx]
    delta = age - peak
    return beta * delta + gamma * (delta ** 2)  # BUG
```

with `factor = exp(age_tilt(adj_idx, age) - age_tilt(meta_idx, age))` applied multiplicatively to `mu_metadata`.

Three errors versus the actual Stan model formula (`hierarchical_aging_quadratic_v4.stan:81-87, 119-127` + production projection at `models/skill/backtest.py:780-822`):

1. **Wrong sign on gamma.** The Stan formula is `-gamma_pos[k] * (age - peak_age_pos[k])^2` (negative quadratic, an aging penalty). The script used `+gamma * (age - peak)^2`.

2. **Wrong linear term entirely.** The Stan formula's linear term is `age_tilt_player[p] * (age - age_center)`, where `age_tilt_player[p]` is a FITTED per-player parameter that absorbs the position information at fit time. At predict time, switching position does NOT change `age_tilt_player[p]` — it's a posterior sample, not recomputed from `beta_age_pos[k']`. The script added a phantom `beta_age_pos[k] * (age - peak_age_pos[k])` term that is not in the predict equation.

3. **Wrong age reference.** The Stan formula's linear term uses `age - age_center` where `age_center = 27.0` per `models/skill/backtest.py:780`. The script used `age - peak_age_pos[k]` for the linear term, conflating the linear and quadratic references.

The net effect was inflating the multiplicative factor `exp(adj_aging - meta_aging)` by approximately 2-3× the true value. For Anthony Davis at age 32 on REB:
- v1.0 (buggy) factor: 1.0303 → 11.467 × 1.0303 = 11.815
- v1.1 (correct) factor: 0.9996 → 11.467 × 0.9996 = 11.462

The buggy factor produced the false-positive REB MAE delta of +0.175 (+5.5%) that v1.0's results commit (`189b61c`) reported as the headline finding.

## 2. The corrected formula

Per the Stan model and production projection code, the position-conditional shift at predict time is ONLY the quadratic position term:

```
factor_position_delta(meta_idx, adj_idx, age) =
    exp( -gamma_pos[adj_idx] * (age - peak_age_pos[adj_idx])^2
         + gamma_pos[meta_idx] * (age - peak_age_pos[meta_idx])^2 )
```

Multiplicatively applied to the v6 raw stat-per-game prediction (which is `exp(mu_player + linear_terms + quadratic_term_fitted_position + covariates)`):

```
mu_metadata = v6_raw[stat]_per_game + apply_offsets(metadata_bucket, stat)
mu_adjudicated_rate = v6_raw[stat]_per_game * factor_position_delta(metadata_idx, adjudicated_idx, age)
mu_adjudicated = mu_adjudicated_rate + apply_offsets(adjudicated_bucket, stat)
```

where `apply_offsets(bucket, stat)` is:
- For PTS: `-0.587` if bucket = Center, else `0`.
- For all other stats: `0` (no position-conditional apply_offsets-level additive).

The linear `age_tilt_player[p] * (age - age_center)` term does NOT enter the delta because it does not change between metadata and adjudicated buckets (it is a fitted per-player parameter).

The non-position covariates (pace_z, mates_usage_z, team_quality_z, gravity_z, young_on_tank, alpha_promotion, wowy_residual) do NOT enter the delta because they are not position-conditional.

## 3. Locked operationalizations

### 3.1 Scope (unchanged from v1.0)

- 25-26 full ship cohort (n=567), 24-25 Stan vet pool backtest cohort (n=131).
- 230 v1.2 adjudicated players (Cohort B), 46 F→C flip subset (Cohort A), 184 non-flip subset (Cohort C).
- Observables PTS / REB / AST / BLK.

### 3.2 Decision rules (unchanged from v1.0)

The same per-cell decision-rule cascade from v1.0 §3 applies verbatim. **Magnitude thresholds for REB MAE delta — 0.05 (small-medium) and 0.15 (large) REB/game — are unchanged.** The Wilcoxon paired test threshold p < 0.05 is unchanged. The CI95 cluster-bootstrap with B = 1,000 and seed 20260602 is unchanged.

### 3.3 Re-fire mechanics

A new script `sloan_mae_delta_rescore_v11.py` implements the corrected formula. The v1.0 script `sloan_mae_delta_rescore.py` is preserved at commit `189b61c` for transparency. v1.0's output artifacts are preserved in the results directory.

The v1.1 fire is one batch, single pass, no iteration.

### 3.4 What does NOT change

- The v1.2 adjudication artifact at SHA256 `eb615269...` is the same input. No re-judgement.
- v6.1 LOCKED Stan posterior chains, `VALIDATED_OFFSETS` dict, `VARIANCE_MULTIPLIERS` dict are the same inputs. No re-fit.
- The 230 adjudicated player cohort is the same. No scope expansion.
- The 4-stat × 2-season × 3-cohort = 24-cell reporting commitment is the same. No selective reporting.

### 3.5 Pipeline integrity gate (unchanged)

Per v1.0 §3.4: Cohort C (184 non-flip adjudicated players) must show `|delta_mu| < 1e-6` in all cells. The bug did not affect Cohort C because for non-flip players `metadata_bucket == adjudicated_bucket`, so the factor is `exp(0) = 1.0` regardless of formula error — the bug's effect is zero on Cohort C. The integrity check PASSED under v1.0 and is expected to PASS under v1.1.

## 4. Output artifacts (v1.1)

All under `D:/NBA Projections/RMD_SRC_PIPELINE/results/sloan_mae_delta/v1_1_corrected/`:

- `per_player_projections_25-26.parquet` — re-scored under corrected formula.
- `per_player_projections_24-25.parquet` — same.
- `cohort_aggregate_mae_{24-25,25-26}.csv` — per-cell MAE statistics.
- `named_player_table_25-26.csv` — 8 priority flip players.
- `pipeline_integrity_check.md`.
- `SLOAN_MAE_DELTA_v1_1_RESULTS.md` — umbrella report including both v1.0 and v1.1 dispositions.

The v1.0 artifacts at `results/sloan_mae_delta/` (no v1_1_corrected subfolder) are PRESERVED in-place at their commit-189b61c content. The v1.1 results live in the `v1_1_corrected/` subfolder.

## 5. Discipline guards

1. **No threshold adjustment.** The 0.05 / 0.15 REB/game magnitude thresholds, the Wilcoxon p < 0.05 cutoff, the power gate n ≥ 8 are unchanged from v1.0. The bug correction does not enable threshold tuning to engineer a favorable outcome.
2. **No v6.1 re-fit, no Stan re-sample, no adjudication re-run.** v1.1 changes only the post-Stan re-scoring formula at the script level.
3. **No selective reporting.** Both v1.0 and v1.1 results are published. The methodology appendix discloses the bug and its consequence. v1.0's adjudicated-arm numbers stay on the record as a worked example of why bug-vs-result distinction matters under SHA-chained discipline.
4. **No retroactive narrative reshaping.** The Sloan paper's main text uses v1.1 numbers as authoritative. The original v1.0 talk-version claim ("AD REB MAE drops 28%, Giannis 43%") is RETRACTED in favor of v1.1's actual numbers, with the retraction footnoted as a methodology example of how a Stan-aging-curve sign error can produce a false-positive headline. The talk-impact framing must be re-derived from v1.1 numbers without engineering toward v1.0's (false) headline.
5. **The v1.0 commit `189b61c` is NOT amended in git history.** Its files stay at their content. The v1.1 results live in their own subfolder and commit.

## 6. Sign-off

- **Filed by:** Claude Code (claude-opus-4-7[1m])
- **Sign-off requested from:** mr.nathanhumphrey@gmail.com
- **Repo:** https://github.com/mrnathanhumphrey-droid/NBAProjections
- **Lock event:** rename this file (already at `_LOCKED.md` suffix); git add; git commit; append commit-SHA to `SHA_LOCK.txt` under a `## Sloan MAE delta Test 2 v1.1 amendment` section. Then run the v1.1 script. Then write `SLOAN_MAE_DELTA_v1_1_RESULTS.md` integrating both v1.0 and v1.1 dispositions.

---

**End of draft v1.1.**
