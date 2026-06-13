# skill fit: backtest_REB_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260426T190600Z`
- stan model: `hierarchical_one_stat.stan`
- observations: 47,136
- chains: 4 × (500 warmup + 500 sampling)
- wall time: 208.7s (3.5 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0139
- min ESS: 2477
- params summarized: 411

### issues
- R-hat for mu_player[20]: 1.010 > 1.01
- R-hat for mu_player[21]: 1.011 > 1.01
- R-hat for mu_player[44]: 1.011 > 1.01
- R-hat for mu_player[96]: 1.011 > 1.01
- R-hat for mu_player[108]: 1.010 > 1.01
- R-hat for mu_player[133]: 1.012 > 1.01
- R-hat for mu_player[165]: 1.014 > 1.01
- R-hat for mu_player[168]: 1.012 > 1.01
- R-hat for mu_player[190]: 1.010 > 1.01
- R-hat for reb_per_36[21]: 1.011 > 1.01
- R-hat for reb_per_36[44]: 1.011 > 1.01
- R-hat for reb_per_36[96]: 1.011 > 1.01
- R-hat for reb_per_36[133]: 1.012 > 1.01
- R-hat for reb_per_36[165]: 1.014 > 1.01
- R-hat for reb_per_36[168]: 1.013 > 1.01
- R-hat for reb_per_36[190]: 1.010 > 1.01

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 29.2% (target 70-90%)
- ✓ **bias_near_zero**: bias = +0.219 per-36 (target |b| < 0.5)
- ✗ **z_error_well_calibrated**: z-error mean=+1.11, sd=4.35 (target 0±0.3, sd 0.7-1.4)
- ✓ **top_25_tier_accuracy**: top-25 overlap = 80.0% (target ≥ 50%)

## worst misses (|projected - actual|, per-36)
-  3.56  Isaiah Stewart (proj 11.27 vs actual 7.71)
-  2.94  Jarred Vanderbilt (proj 11.46 vs actual 8.52)
-  2.33  Donte DiVincenzo (proj 6.85 vs actual 4.52)
-  2.16  Anthony Davis (proj 10.64 vs actual 12.81)
-  2.14  Jevon Carter (proj 4.30 vs actual 2.16)
-  2.14  Kyle Anderson (proj 7.66 vs actual 5.52)
-  2.02  Andre Drummond (proj 16.88 vs actual 18.89)
-  1.96  Jalen Green (proj 3.89 vs actual 5.86)
-  1.92  Doug McDermott (proj 4.27 vs actual 2.35)
-  1.92  Dejounte Murray (proj 7.30 vs actual 5.38)

## best hits (smallest error)
-  0.00  Dorian Finney-Smith (proj 5.90 vs actual 5.90)
-  0.00  Keldon Johnson (proj 6.66 vs actual 6.66)
-  0.00  Jaxson Hayes (proj 8.62 vs actual 8.62)
-  0.00  Torrey Craig (proj 7.43 vs actual 7.43)
-  0.01  Corey Kispert (proj 3.92 vs actual 3.92)

## backtest metrics
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- N players: 195
- MAE: 0.699
- RMSE: 0.935
- bias: +0.219
- coverage 50%: 16.4%
- coverage 80%: 29.2%
- coverage 90%: 33.3%
- z-error: mean=+1.113 sd=4.346
- top-25 tier accuracy: 80.0%
- top-50 tier accuracy: 94.0%
