# Phase 4 — Context projection architecture

Empirical foundation: 2026-04-26 cross-stat lineup-mate diagnostic on 167
players with full CtG lineup coverage in train (2019-22+22-23) and test
(2023-24). All correlations are `r(d_co_S, d_S | d_pace)` — partial
correlation of focal player's stat change against co-mate stat change,
controlling for team-pace change.

## Core finding: stat-specific dual-direction structure

The same Δ co_S has *opposite-sign effects* depending on player baseline.
Stratified partial correlations (top-25% vs bottom-25% by player's
training-period S/36):

| Stat | Specialists (top-25%) | Role-players (bottom-25%) | Architecture |
|---|---|---|---|
| REB  | **+0.257** | -0.135 | Interaction: skill-centered × lineup |
| OREB | +0.145 | **-0.325** | Interaction: skill-centered × lineup |
| DREB | +0.063 | -0.164 | Interaction (weaker) |
| AST  | -0.106 | -0.189 | Pace + usage-share subtraction |
| PTS  | -0.031 | **-0.246** | Pace + usage-share subtraction |
| TOV  | -0.140 | +0.157 | Pace covariate |
| FGA  | -0.022 | -0.026 | Pace only |
| FG3A | +0.084 | +0.122 | Small positive both ways (style) |
| BLK  | -0.021 | -0.099 | None — specialist-insulated |
| STL  | +0.079 | -0.025 | None — noise |

Team pace (`d_pace`) marginal correlations: PTS +0.31, TOV +0.25, FGA +0.25,
AST +0.24, FG3A +0.13, REB +0.08, BLK +0.06, STL +0.08, DREB +0.09, OREB ~0.

## Three regimes

### Regime A: specialist-positive / role-negative
**Stats:** REB, OREB, DREB

**Mechanism:** rebounding co-moves with lineup *role*. Specialists (top-25% rebounders) gain when surrounded by other rebounders — confirms role-shift hypothesis from the Portis/JJJ/Stewart deep dive (2026-04-26). Role-players (bottom-25%) lose when surrounded by rebounders — pure displacement.

**Architectural choice:** *interaction* term, not a uniform multiplier.

```
log_rate[i] += beta_lineup_S * (mu_player[p] - mu_league) * lineup_co_S_z[player_season]
```

Where `lineup_co_S_z` is the standardized possession-weighted average of mates' S/36 across the player's CtG lineups in that season. The `(mu_player - mu_league)` centering means specialists (positive deviation) get a positive lift when lineup is rebound-heavy, role-players (negative deviation) get a negative lift.

### Regime B: pace-driven + usage-share subtraction
**Stats:** PTS, AST, TOV, FGA

**Mechanism:** volume stats. Pace explains 25-30% of YoY change. Usage is approximately zero-sum within possessions — when mates take more shots/passes, focal takes fewer.

**Architectural choice:** two separate features.

```
log_rate[i] += beta_pace * (team_pace[player_season] - league_pace)
log_rate[i] -= beta_usage * mates_usage_share[player_season]
```

Where `mates_usage_share` is the possession-weighted sum of mates' S/36 across lineups (sum, not average — total volume taken by mates).

### Regime C: specialist-insulated
**Stats:** BLK, STL, FG3A

**Mechanism:** these stats are dominated by individual specialists or shooting tendency. Lineup-mate effects don't transfer.

**Architectural choice:** *no lineup feature.* Per-player aging model already handles them.

For FG3A specifically: a small "team-style" positive signal exists (+0.08 to +0.12) but it's swamped by individual shooting tendency in the per-player skill term. Adding a feature here adds noise, not signal.

## Build sequence (phase 4 ordered by value × tractability)

1. **REB with lineup interaction** (Regime A on the cleanest signal):
   - Extends `hierarchical_aging_per_player.stan`
   - Adds per-(player, season) feature input
   - Smoke fit on 200-player subset, backtest 2023-24, compare to per-player aging baseline (49.2% / 79.5% / 87.7% coverage)

2. **OREB with lineup interaction** (same architecture, sharper bottom-25% signal):
   - OREB role-player effect r=-0.325 is the sharpest in the diagnostic
   - Validates the architecture on a different stat with the same regime

3. **PTS with pace + usage-share** (Regime B):
   - First test of the two-feature volume-stat model
   - Different architecture from A, validates the regime split

4. **Full multi-stat Phase 4** (assemble all three regimes by stat family):
   - REB, OREB, DREB → Regime A
   - PTS, AST, TOV, FGA → Regime B
   - BLK, STL, FG3A → Regime C (no change from Phase 3)

## Data layer requirements

- ✅ `lineups_ctg.parquet` — already pulled (1670 5-man combos, 6 seasons)
- ✅ `historical_box_scores.parquet` — already pulled
- 🆕 Per-(player, season, stat) `co_S_strength` precomputed feature → save under
  `data/parquet/lineup_features.parquet` for reuse
- 🆕 Per-(team, season) `pace_per_48` precomputed feature → save under same
- 🆕 CtG name-abbreviation map maintained as part of `models.skill.lineup_features`

## Coverage caveat

55% of 200-player backtest set has full CtG lineup coverage. Players without
coverage (rookies, two-ways, mid-season call-ups) need a fallback feature.
First version: when lineup_co_S is missing, set to 0 (neutral lift) so the
model degrades to per-player aging — strictly no worse than Phase 3 baseline.

## Validation gate

Phase 4 v1 ships when, on the same train/test split as the per-player aging
backtest:
- Coverage 80% within [75%, 85%] (vs 79.5% baseline — should improve)
- z-error sd ≤ 1.05 (vs 1.11 baseline)
- Top-3 worst misses removed: Stewart, JJJ, Portis projection error compresses
  from 2.5-2.9σ to <2σ
- No regression on best-hits (Plumlee/Williams etc. should remain accurate)

Bias is allowed to drift slightly (already at +0.054); coverage is the
priority since Phase 4 closes the calibration story.
