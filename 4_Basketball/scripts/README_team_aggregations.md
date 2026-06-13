# Team Aggregations — Usage and Caveat

`produce_team_aggregations.py YYYY-MM-DD` reads
`audit_runs/rs_projections_{date}/rs_projections.parquet` (output of
`produce_regular_season_projections.py`) and emits two new parquets in the
same directory:

- `team_aggregations.parquet` — per (game_id, team_abbr): team box totals
  (PTS/REB/AST/BLK/STL/TOV/FG3M + M/A pairs + derived FG%/FT%/3P%).
- `game_aggregations.parquet` — per game_id: home/away team box totals
  + projected_total + projected_spread.

## When to use which artifact

**For player props (per-player stat lines):** use `rs_projections.parquet`.
Phase 1c v1.1 architecture; shrinkage on 16 cells; rolling_emp elsewhere.

**For team box totals conditional on lineup actually played
(backtest / consistency check):** use `team_aggregations.parquet`.

**For game-level totals / sides bets / pace / OffRtg / DefRtg:** use
`audit_runs/game_predictions_2025_26_phase3_*/per_team_game_predictions.csv`
(separate game-level model). The team aggregator's `projected_total` and
`projected_spread` are diagnostics, NOT production totals/sides.

## Why the player-sum undercounts team totals

Cross-check on 2025-11-01 vs 2026-04-10 (vs actual game_pts):

| Date | Player-sum MAE vs actual | game_pred MAE vs actual | Δ player-sum vs game_pred |
|---|---:|---:|---:|
| 2025-11-01 | 18.4 PTS | 11.2 PTS | −10.2 PTS |
| 2026-04-10 | 42.2 PTS | 13.4 PTS | −36.9 PTS |

The player-sum drift grows late-season because:
- Player projections are conditional on the player appearing in the box score.
- Late-season teams rest starters / play deep-bench guys / tank.
- Deep-bench guys have low projected lines.
- Sum of low-projected lines undercounts what teams actually score.

The game-level `game_predictions` model uses team-level features (rolling
OffRtg/DefRtg/pace) which capture this correctly regardless of which 10
players take the floor.

**Bottom line:** use game_predictions for totals/sides; use rs_projections
for player props.
