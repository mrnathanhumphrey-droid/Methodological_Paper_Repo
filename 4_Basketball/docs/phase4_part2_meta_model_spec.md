# Phase 4 part 2 — Selective projection-time meta-model

**Status:** spec-locked 2026-04-27 after the Stan v3 covariate experiment confirmed cross-sectional features don't transfer to Stan. See `memory/feedback_within_vs_between_signals.md` for the diagnostic principle.

## Architecture

```
final_projection(player, test_season)
  = bayesian_v2(player, test_season)                    # base — no change
  × meta_adjust(player, test_season)                    # NEW post-hoc layer
```

Where `bayesian_v2` is the recency-weighted pace+usage Stan model that's already validated (REB MAE 0.631 vs naive 0.655; PTS MAE 2.054 vs naive 2.012, well-calibrated). The Bayesian layer continues to do what it's good at: per-player skill estimation, aging, recency-weighted likelihood, calibrated posteriors.

`meta_adjust` is a **selective post-hoc multiplier** applied at projection time only:

```python
def meta_adjust(player, test_season):
    if not is_high_impact_trade(player, train_seasons, test_season):
        return 1.0  # no adjustment, model projection unchanged
    role_baseline = team_position_starter_per_36[
        new_team, prev_season, player_position
    ]
    v2_proj = bayesian_v2(player, test_season)
    if abs(v2_proj - role_baseline) < significance_threshold:
        return 1.0  # gap too small, don't bother
    blended_mean = (1 - alpha) * v2_proj + alpha * role_baseline
    multiplier = blended_mean / v2_proj
    return multiplier  # plus widen_sd_proportionally
```

## Detection rules — what counts as "high-impact trade"

A player gets the meta-adjustment if ALL of these hold:

1. **Team change with primary movement.** Their primary team in test season ≠ primary team in the most-recent training season. (Computed via `models.skill.role_shift.detect_team_change` — already built.)
2. **Position-class definable.** Their Yahoo PG/SG/SF/PF/C eligibility resolves (use `player_metadata_enriched.yahoo_primary_position`; fall back to nba_api 3-class only as last resort).
3. **Role-baseline available.** Prev-season starter rate exists for `(new_team, position_class)`. Already built in `compute_team_position5_starter_baselines`.
4. **Significance gate.** `|v2_projection - role_baseline| ≥ threshold`. Tentatively threshold = 1 OOS_SD for the stat (e.g., ≥1.9 PTS/36, ≥0.7 REB/36). Avoids triggering on noise — Stewart staying as DET center doesn't trigger because role_baseline ≈ his own training rate.
5. **Trade-recency match.** Trade happened in the offseason between train and test (not mid-season slop captured in box scores). Detected by `last_train_team ≠ test_team`.

This filters the 177-of-195 over-flag we saw on naive `team_changed=True` down to the actual high-impact movers (the Lillard / Holiday / Harden / Brunson cases). Probably 20-40 players per test season.

## Calibration of α

Pick `α` empirically using a held-out validation season, NOT cross-sectional analysis. Procedure:

1. Hold out one training season (e.g., 2022-23) as validation
2. Train v2 on 2019-20 through 2021-22
3. Project 2022-23
4. Identify high-impact-trade players in that test (per the rules above)
5. Sweep α ∈ {0.1, 0.2, ..., 0.7}; pick the α that minimizes MAE-on-meta-adjusted-players AND keeps coverage 80% in the [70%, 90%] band
6. Lock that α; use for production projection

For the 2026-04-26 PTS analysis we observed:
- Lillard at α=0.5 (against full-position-mean baseline): error 7.64σ → 1.43σ
- Holiday at α=0.5 (against full-position-mean): error stayed bad (his 26.66 BOS-G baseline was Brown, wrong role)
- Lillard at α=0.5 (against starter baseline 21.30): error 7.64σ → 2.08σ

So α=0.5 with starter-baseline targeting works for marquee cases. We need validation-season tuning to confirm.

## Sigma widening

```python
sd_adjusted = sqrt((1 - alpha)² · sd_v2² + alpha² · sd_role²)
where sd_role ≈ empirical_oos_sd  # the role-baseline isn't certain either
```

This keeps coverage calibrated. Already implemented in `models.skill.projection_blending.apply_blend`.

## What changes vs current code

Existing components (all already built and validated):
- `models/skill/role_shift.py` — detection (already correct)
- `models/skill/team_role_baseline.py` — `compute_team_position5_starter_baselines` (already correct)
- `models/skill/projection_blending.py` — `apply_blend`, `widen_posteriors_for_role_events` (already correct)
- v2 Stan + prep — base model (already validated)

What needs to be built (small):
1. `models/skill/projection_meta_model.py` — wraps the detection + significance gate + α blend with the calibration interface
2. CLI flag `--meta-adjust` on `cli.backtest_skill_volume` — applies meta-adjust to v2 projections, saves both pre- and post-adjustment per-player CSVs
3. Calibration script that does the held-out validation sweep on 2022-23 to lock α

What can be DELETED (the failed v3 path):
- `models/skill/stan/hierarchical_aging_pace_usage_v3.stan` — the Stan covariate version that came back null
- The `--role-v3` flag and associated branches in `cli.backtest_skill_volume`
- The `role_projection_meta_df` parameter on `prep_aging_pace_usage_single_stat`

Or keep them as a documented dead end. Probably cleaner to delete and let the architectural-failure note in memory carry the lesson.

## Validation gate (Phase 4 part 2 ships when)

On the 2023-24 PTS test:
- Aggregate MAE drops to ≤ 2.012 (beats naive A — currently we're at 2.054)
- Lillard's error drops below 4 PTS/36 (currently 7.64)
- Coverage 80% remains in [70%, 90%] band (currently 82.1%)
- z-error sd remains in [0.7, 1.4] (currently 1.00)
- top-25 / top-50 accuracy doesn't degrade by more than 2pp (currently 72% / 80%)
- Apply same gate for AST / TOV / FGA after their v2 fits land

## What's NOT in scope for Phase 4 part 2

- Rookie projection (Phase 5 — needs college / international data layer)
- Multi-trade-event handling (player traded mid-season, then traded again — count as one trade event for the test season, use whichever team is primary)
- Coaching changes / system changes — too granular for V1
- Star injury return-to-play timing (Phase 5 GP model territory)

## Build sequence (order of operations next session)

1. **Delete the v3 dead end** (clean the codebase first; it would only confuse future readers)
2. **Build `projection_meta_model.py`** — wrapper around the existing components
3. **Build held-out validation script** — runs v2 on 2019-21 → test 2022-23 with various α
4. **Lock α empirically** based on validation
5. **Backtest 2023-24 PTS with --meta-adjust** — same compute budget as v2/v3, just adds post-hoc layer
6. **If PTS works:** apply same meta-adjust on AST / TOV / FGA backtests (compute, awaits go)
7. **Wonka adapter:** the meta-adjust mean-shift propagates cleanly into Wonka's audit-CSV format; the SD widening propagates into the joint-samples format (Wonka uses both)
