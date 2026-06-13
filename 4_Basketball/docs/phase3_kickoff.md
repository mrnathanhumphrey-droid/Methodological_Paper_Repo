# Phase 3 Kickoff — Aging Curves

Status as of end-of-session 2026-04-26: Phase 2 architecture validated, backtest
harness functional with OOS variance fix. **Next session starts here.**

## Context

The current REB backtest hits **74% coverage on 80% CI** (target 80%) with z-error
sd 1.28 (target 1.0). Remaining gap is the role-change / aging / injury cases —
specifically the worst-miss list:

| Player | Train mean | Test actual | Driver |
|---|---|---|---|
| Isaiah Stewart | 11.27 | 7.71 | Role change → wing |
| Jarred Vanderbilt | 11.46 | 8.52 | Major injury 2023-24 |
| Donte DiVincenzo | 6.85 | 4.52 | Trade to NYK, new role |
| Anthony Davis | 10.64 | 12.81 | High-rebound season |
| Jevon Carter | 4.30 | 2.16 | Minutes drop |

Phase 4 (context) addresses Stewart/DiVincenzo/Carter (role-change). Phase 3
(aging) addresses Davis-style age effects + general age-adjusted projection.
Phase 5 + Wonka structural multipliers handle Vanderbilt-style injury cases.

## Phase 3 scope (per spec §3.4)

> Players develop and decline non-linearly. The model applies aging curve
> adjustments to skill estimates based on age:
>     aged_skill(p, c, age) = skill(p, c) × age_curve_multiplier(age, position, c)
> Aging curves are category- and position-specific.

Curves are fit from historical data: regress per-minute stats against age,
controlled for player fixed effects, find the systematic age-effect.

## Build order (5 sub-steps — mirror Phase 2 pattern)

1. **Empirical aging-curve estimation.** From `historical_box_scores.parquet`
   joined to `player_metadata.birth_date`, compute age at each game. Fit
   smooth (cubic spline or polynomial-in-age) per (stat × position) using
   player fixed effects. Output: aging-curve coefficients per (stat, position)
   with posterior uncertainty.

2. **Stan model: aging-aware skill.** Extend `hierarchical_one_stat.stan` to
   include age as a covariate. The skill model becomes:
   ```
   log_rate[i] = mu_player[player_idx[i]]
              + age_offset[stat, position](age[i])
   ```
   Where `age_offset` is the spline. Player effects now capture age-adjusted
   skill instead of raw skill.

3. **Project forward with aging.** When projecting season N+1, compute aging
   adjustment for each player at next season's age. The aging curve's posterior
   contributes to projection uncertainty (variance term added in quadrature
   alongside OOS).

4. **Multi-stat aging.** Different stats peak at different ages — STL peaks
   earlier than PTS, BLK declines faster than REB. Per-stat aging curves
   are independent fits initially.

5. **Validate.** Re-run REB backtest. Coverage 80% should approach target
   (within 2-3pp). Worst-miss list should compress (Davis, aging-edge cases
   no longer outliers).

## Informative priors from sabermetric literature

Spec §10.3 says priors get documented + sensitivity-tested. For aging:

- **Peak age by stat × position**: literature consensus
  - Volume (PTS, FGA, FTA): peak ~26-28, gentle decline through early 30s, steeper at 33+
  - Athleticism (BLK, STL): peak earlier ~24-26, steeper decline
  - Efficiency (FG_pct, FT_pct): later peak ~28-30, slower decline (FT% declines barely at all)
  - Rebounds: position-dependent — bigs maintain longer than guards/wings

- **Decline rates** are steeper for guard skills (quickness-dependent) than for
  size-dependent skills (REB, BLK).

Source candidates:
- Dean Oliver, *Basketball on Paper*
- Daryl Morey's APBR-era public work
- Modern public analytics (Seth Partnow, Krishna Narsu, Kostya Medvedovsky,
  Goldsberry's writing)

## Files to read at session start

- `D:\NBA Projections\docs\skill_model_design.md` (Phase 2 design — extend)
- `D:\NBA Projections\docs\spec_amendments.md` (per-category fusion notes)
- `D:\NBA Projections\models\skill\backtest.py` (where projection adjustments stack)
- Latest backtest report: `D:\NBA Projections\audit_runs\20260426T191524Z\skill_backtest_REB_*/summary.html`

## Concrete first-action

Empirical exploration: load box scores joined to age, plot per-minute REB
vs age across all data. Look for the curve shape. THAT determines whether
spline / polynomial / piecewise-linear is the right structural choice.

```python
import numpy as np
import pandas as pd
from datetime import date

box = pd.read_parquet('data/parquet/historical_box_scores.parquet')
meta = pd.read_parquet('data/parquet/player_metadata.parquet')
# Join, compute age at game, plot per-min REB vs age by position
```

That's the first 30 minutes of next session. From there: model spec, fit, validate, re-backtest.
