# skill fit: backtest_REB_aging_per_player_recency_v2_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260427T041321Z`
- stan model: `hierarchical_aging_per_player_v2.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 2231.7s (37.2 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0176
- min ESS: 365
- params summarized: 887

### issues
- R-hat for mu_player[113]: 1.010 > 1.01
- R-hat for mu_player[145]: 1.010 > 1.01
- ESS for age_slope_player_sd: 365 < 400
- R-hat for age_slope_player_z[11]: 1.014 > 1.01
- R-hat for age_slope_player_z[25]: 1.011 > 1.01
- R-hat for age_slope_player_z[152]: 1.018 > 1.01
- R-hat for age_slope_player_z[183]: 1.011 > 1.01
- R-hat for age_slope_player[152]: 1.011 > 1.01
- R-hat for reb_per_36_at_27[113]: 1.010 > 1.01
- R-hat for reb_per_36_at_27[145]: 1.010 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 83.1% (target 70-90%)
- ✓ **bias_near_zero**: bias = +0.052 per-36 (target |b| < 0.5)
- ✓ **z_error_well_calibrated**: z-error mean=+0.06, sd=0.98 (target 0±0.3, sd 0.7-1.4)
- ✓ **top_25_tier_accuracy**: top-25 overlap = 84.0% (target ≥ 50%)

## worst misses (|projected - actual|, per-36)
-  3.02  John Collins (proj 7.88 vs actual 10.90)
-  2.66  Isaiah Stewart (proj 10.37 vs actual 7.71)
-  2.25  Jarred Vanderbilt (proj 10.77 vs actual 8.52)
-  1.94  Jalen Green (proj 3.92 vs actual 5.86)
-  1.93  Jevon Carter (proj 4.09 vs actual 2.16)
-  1.89  Jaren Jackson Jr. (proj 8.07 vs actual 6.19)
-  1.83  Bobby Portis (proj 12.69 vs actual 10.86)
-  1.75  Naz Reid (proj 9.50 vs actual 7.75)
-  1.67  Daniel Gafford (proj 9.49 vs actual 11.17)
-  1.65  Donte DiVincenzo (proj 6.18 vs actual 4.52)

## best hits (smallest error)
-  0.00  Kenrich Williams (proj 7.31 vs actual 7.31)
-  0.02  Cole Anthony (proj 6.18 vs actual 6.16)
-  0.03  Damian Lillard (proj 4.44 vs actual 4.47)
-  0.03  Terry Rozier (proj 4.32 vs actual 4.36)
-  0.04  Obi Toppin (proj 6.70 vs actual 6.66)

## backtest metrics
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- N players: 195
- empirical out-of-sample SD: 0.670 (added to parameter SD in quadrature)
- MAE: 0.631
- RMSE: 0.816
- bias: +0.052
- coverage 50%: 52.3%
- coverage 80%: 83.1%
- coverage 90%: 90.8%
- z-error: mean=+0.062 sd=0.983
- top-25 tier accuracy: 84.0%
- top-50 tier accuracy: 92.0%
