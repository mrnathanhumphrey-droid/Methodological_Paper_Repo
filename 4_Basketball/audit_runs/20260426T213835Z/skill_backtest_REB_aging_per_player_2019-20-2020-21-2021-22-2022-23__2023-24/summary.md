# skill fit: backtest_REB_aging_per_player_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260426T213835Z`
- stan model: `hierarchical_aging_per_player.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 2138.0s (35.6 min)

## convergence
- status: **PASSED**
- max R-hat: 1.0096
- min ESS: 568
- params summarized: 887

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 79.5% (target 70-90%)
- ✓ **bias_near_zero**: bias = +0.054 per-36 (target |b| < 0.5)
- ✓ **z_error_well_calibrated**: z-error mean=+0.05, sd=1.11 (target 0±0.3, sd 0.7-1.4)
- ✓ **top_25_tier_accuracy**: top-25 overlap = 84.0% (target ≥ 50%)

## worst misses (|projected - actual|, per-36)
-  3.61  John Collins (proj 7.29 vs actual 10.90)
-  3.43  Bobby Portis (proj 14.29 vs actual 10.86)
-  2.66  Isaiah Stewart (proj 10.37 vs actual 7.71)
-  2.58  Jaren Jackson Jr. (proj 8.77 vs actual 6.19)
-  2.33  Jarred Vanderbilt (proj 10.85 vs actual 8.52)
-  2.26  Kevon Looney (proj 14.89 vs actual 12.63)
-  1.94  Jalen Green (proj 3.92 vs actual 5.86)
-  1.90  Naz Reid (proj 9.66 vs actual 7.75)
-  1.85  Jevon Carter (proj 4.01 vs actual 2.16)
-  1.69  Brook Lopez (proj 7.79 vs actual 6.10)

## best hits (smallest error)
-  0.01  Corey Kispert (proj 3.91 vs actual 3.92)
-  0.01  Eric Gordon (proj 2.33 vs actual 2.32)
-  0.02  Taurean Prince (proj 3.94 vs actual 3.93)
-  0.02  Tim Hardaway Jr. (proj 4.33 vs actual 4.31)
-  0.03  Giannis Antetokounmpo (proj 11.74 vs actual 11.77)

## backtest metrics
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- N players: 195
- empirical out-of-sample SD: 0.670 (added to parameter SD in quadrature)
- MAE: 0.685
- RMSE: 0.905
- bias: +0.054
- coverage 50%: 49.2%
- coverage 80%: 79.5%
- coverage 90%: 87.7%
- z-error: mean=+0.053 sd=1.113
- top-25 tier accuracy: 84.0%
- top-50 tier accuracy: 90.0%
