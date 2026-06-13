# Level 3 game prediction build plan

*Possession-level NBA game prediction layer. Per-player offensive projections (existing) + per-player defensive projections (NEW) + possession-aware aggregation → game-level score margin posterior → win probability.*

## Phase 0 — Foundation sanity check (✅ COMPLETE 2026-05-11)

Level 1 baseline test: sum-of-projected-PTS per team vs actual 25-26 RS game margins.

**Results on 1230 RS games:**
- Margin RMSE: **32.8** (target: ~10-11 to compete with Vegas)
- Win prediction: **62.0%** (floor; Vegas/consensus ~62-66%)
- Total PTS bias: projected 96.86 vs actual 115.61 per team (~85% of actual)

**Diagnosed issues:**
- **Coverage gap (84% of total PTS gap)**: ship CSV covers 9 of 10.8 active players per team-game. Non-ship players account for **32 minutes / ~14 PTS per team-game** uncovered.
- **Per-min under-projection (~15% of gap)**: ship players at 0.448 PTS/min projected vs 0.461 actual (~3% gap).

**Implication:** must address coverage gap (Phase 3) and add per-min calibration (existing v6.2 de-shrinkage is held back due to vet Simpson's paradox; needs different scaling) before any sophisticated aggregation will produce competitive margins.

## Phase 1 — Defensive projection layer (NEW, parallel to skill model)

### 1.1 Data foundation (✅ VALIDATED)

Available defensive data layers:
- `player_def_zone_overall.parquet` (4629 player-seasons, 2019-25). Key field: `pct_plusminus` = (allowed FG%) − (league avg FG%). Negative = good defender.
- `player_def_zone_3pt.parquet`, `player_def_zone_2pt.parquet` — per-zone breakouts.
- `player_def_rim.parquet` (4509 rows) — shots ≤6 feet.
- `player_hustle.parquet` (4610 rows) — contested shots, deflections, charges drawn.
- `player_tracking_defense.parquet` (4677 rows) — STL, BLK, def_rim_fgm.

**Validated stability:** within-player season-to-season correlation of `def_pts_impact` = **r = 0.52** (n=297, 23-24 vs 24-25). Comparable to within-player offensive PTS rate stability. **Real skill, projectable.**

**Validated face validity:**
- Top defenders 23-25: Gobert × 4 seasons, Lopez × 2, Giannis, Draymond, Porziņģis, Allen
- Worst defenders 23-25: Trae Young, Haliburton, Jalen Green, Scoot Henderson (offensive guards / rookies)

### 1.2 Projection schema

**Target variable:** `def_pts_impact_per_game` = `pct_plusminus × d_fga × 2.5 / gp`
- Units: PTS per game saved (negative) or allowed (positive) vs league average defender at same volume
- Range: ~-5 (Gobert) to ~+2.5 (worst defenders)

**Features:**
- Position (G/F/C — defensive role differs by position)
- Age + age² (defensive prime ~25-29, late-career bigs hold longer)
- Years pro (rookies allow more, veteran scheme-knowledge advantage)
- Height/weight (defensive size matters)
- On-court minutes (volume defended, weights the signal)
- Hustle features (contested shots, deflections — defensive activity)

**Model architecture:** parallel to v4-lite skill model:
- Hierarchical NB2 / Gaussian on rate per game
- Per-position aging quadratic
- Player random effects with partial pooling
- Stan v4-lite-defense.stan file (to be authored)

**Output:** per-player projected `def_pts_impact_per_game` + sd, joined to ship CSV.

### 1.3 Stan fit plan (NEXT SESSION COMPUTE)

- Train: 2019-20 through 2024-25 (6 seasons)
- Test: 2025-26 held-out
- 4 chains × 1 thread, ~1-2h per stat
- Likely 4-6 hours total wallclock
- Output: `audit_runs/<timestamp>/skill_backtest_DEFIMPACT_phase4_v4_*` directories

## Phase 2 — Possession-level aggregation model

### 2.1 Team-level rate composition

Per game, each team's expected points scored = `expected_possessions × expected_PPP`, where:

- `expected_possessions` = mean(team_pace, opponent_pace) × game-length adjustment
- `expected_PPP` per team:
  - Offensive contribution = Σ (player offensive contribution per possession × possession share)
  - Defensive adjustment FROM opponent = Σ (opponent defenders' def_pts_impact per possession)
  - Lineup chemistry adjustment (small additional from `lineups_ctg.parquet` net rating effects)

### 2.2 Possession share model

For each player on a team, possession share = (player's MPG / team's total MPG) — this is how much of the team's offense flows through them.

**Refinement:** usage rate differs from minutes share. Usage data exists in `sportradar_usage.parquet`. Per-player `usg_rate` weights more accurately how possessions are consumed.

### 2.3 Defensive matchup

Defensive impact on opponent's offense scales with the defender's minutes share × opponent's possession volume against that defender's position. First-pass: aggregate at team level (5 defenders × their `def_pts_impact_per_game` / 36 × actual minutes).

### 2.4 Architecture decision: linear vs lineup-level

**Tier 1 (linear):** team offense - team defense + home court + rest. Simplest. Misses lineup chemistry but is robust.

**Tier 2 (lineup-aware):** use `lineups_ctg.parquet` (1670 rows, 19-25) for per-lineup net rating effects. Adds chemistry term. More complex, needs roster prediction per game.

**Recommendation:** start with Tier 1, validate, then add Tier 2 as Phase 2.5 if Tier 1 doesn't beat target.

## Phase 3 — Game integration

### 3.1 Per-game inputs

For each scheduled game, need:
- Home team + away team
- Game date + each team's days-since-last-game (rest)
- Each team's expected lineup (depth chart override consumed today's snapshot)
- Each team's expected MPG distribution across lineup
- Pace projection per team (existing data + recent rolling)

### 3.2 Coverage gap fill

Non-ship players (~32 mpg per team-game) need projections too. Sources:
- Recent box-score rolling per-36 stats (last 10 games)
- Career per-36 means
- Default to league-mean per-36 if no data

Build `scripts/extend_ship_to_full_roster.py` that fills in any active player not in the v6.1 ship CSV.

### 3.3 Output schema

Per scheduled game:
- `home_team`, `away_team`, `game_date`
- `home_pts_pred`, `home_pts_sd`
- `away_pts_pred`, `away_pts_sd`
- `margin_pred`, `margin_sd`
- `win_prob_home` (via calibrated logistic on margin)
- `total_pred` (over/under)

Saved to `audit_runs/game_predictions_<season>/per_game_predictions.csv`.

## Phase 4 — Validation harness

### 4.1 Backtest

Apply Phase 3 pipeline to 2024-25 RS games (held-out from Phase 1 Stan fit which trains through 23-24 alternatively). Compute:
- **Margin RMSE** (target: < 12, stretch: < 11)
- **Margin bias** (target: < 0.5 pts on average)
- **Win prediction accuracy** (target: > 66%, stretch: > 68%)
- **Win-prob calibration** — Brier score + reliability diagram

### 4.2 Comparators

- Vegas closing line (margin RMSE ~11, win pct ~66-67%)
- 538 ELO (margin RMSE ~12, win pct ~64-65%)
- Random walk on team rating (margin RMSE ~13-14)

### 4.3 Win-prob calibration

Standard logistic: `P(home_win) = 1 / (1 + exp(-α - β × margin_pred))` calibrated on historical (margin_pred, won) pairs. Typical β ≈ 0.08-0.10.

## Build sequencing

| Session | Phase | Compute | Status |
|---|---|---|---|
| 2026-05-11 | 0, 1.1, 1.2 design | none | ✅ DONE |
| Next session | 1.3 Stan fit (defensive projection) | 4-6h Stan | gated on compute window |
| Next session+1 | 2 possession model | light fit | gated on Phase 1 |
| Next session+2 | 3 game integration + coverage fix | none | sequential after Phase 2 |
| Next session+3 | 4 validation + win-prob calibration | none | sequential after Phase 3 |

Total: ~4 focused sessions for full Level 3 ship.

## Open questions for design review

1. **Defensive target**: per-game total impact vs decomposed (rim vs perimeter)? Decomposed gives finer per-matchup signal but quadruples the Stan fit cost.
2. **Possession share weighting**: minutes vs usage rate? Usage is more accurate but introduces data dependency on sportradar.
3. **Lineup chemistry term**: include in Tier 1 or hold for Tier 2? Adds complexity, value uncertain on n=1230-game cohort.
4. **Home court constant**: fit empirically per-season (declining over the COVID era) or fixed ~+2.5?

## Files produced this session

- `docs/level_3_game_prediction_build_plan.md` (this file)
- Diagnostic outputs in conversation transcript (sanity check + def signal validation)

## Next session entry points

1. **Phase 1 Stan fit**: author `models/stan/hierarchical_def_impact_v1.stan`, fire `cli.backtest_def_impact_overnight --train 2019-25 --test 2025-26`. Mirror v4-lite architecture.
2. **Coverage gap fix**: build `scripts/extend_ship_to_full_roster.py` independently of Stan fit. No fit needed.
3. **Pace projection**: derive per-game pace from rolling team pace + opponent pace mix. Pure data work.
