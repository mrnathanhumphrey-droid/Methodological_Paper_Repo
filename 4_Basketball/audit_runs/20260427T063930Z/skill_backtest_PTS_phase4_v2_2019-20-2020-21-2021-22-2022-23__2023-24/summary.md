# skill fit: backtest_PTS_phase4_v2_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260427T063930Z`
- stan model: `hierarchical_aging_pace_usage_v2.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 4143.8s (69.1 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0144
- min ESS: 346
- params summarized: 891

### issues
- R-hat for mu_player[73]: 1.010 > 1.01
- R-hat for sigma_position: 1.013 > 1.01
- ESS for sigma_position: 346 < 400
- R-hat for age_slope_player_z[46]: 1.012 > 1.01
- R-hat for age_slope_player_z[68]: 1.011 > 1.01
- R-hat for age_slope_player_z[112]: 1.013 > 1.01
- R-hat for age_slope_player_z[118]: 1.014 > 1.01
- R-hat for age_slope_player_z[142]: 1.013 > 1.01
- R-hat for age_slope_player[68]: 1.014 > 1.01
- R-hat for age_slope_player[96]: 1.010 > 1.01
- R-hat for age_slope_player[112]: 1.011 > 1.01
- R-hat for age_slope_player[118]: 1.011 > 1.01
- R-hat for age_slope_player[142]: 1.012 > 1.01
- R-hat for age_slope_player[177]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[73]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[177]: 1.010 > 1.01

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 82.1%
- ✓ **bias_near_zero**: bias = +0.789
- ✗ **z_error_well_calibrated**: z-error mean=+0.32, sd=1.00
- ✓ **top_25_tier_accuracy**: top-25 overlap = 72.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 195
- empirical OOS SD: 1.974 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 2.054
- RMSE: 2.547
- bias: +0.789
- coverage 50%: 42.6%
- coverage 80%: 82.1%
- coverage 90%: 87.2%
- z-error: mean=+0.319 sd=1.003
- top-25 tier accuracy: 72.0%
- top-50 tier accuracy: 80.0%
