# skill fit: backtest_PTS_phase4_v5_quadratic_tq_gw_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260428T223334Z`
- stan model: `hierarchical_aging_quadratic_v4.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 6923.7s (115.4 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0269
- min ESS: 165
- params summarized: 911

### issues
- R-hat for mu_position[3]: 1.010 > 1.01
- R-hat for mu_player[122]: 1.011 > 1.01
- R-hat for mu_player[131]: 1.013 > 1.01
- R-hat for sigma_position: 1.027 > 1.01
- ESS for sigma_position: 165 < 400
- R-hat for age_tilt_player_z[18]: 1.010 > 1.01
- R-hat for age_tilt_player_z[23]: 1.010 > 1.01
- R-hat for age_tilt_player_z[53]: 1.010 > 1.01
- R-hat for age_tilt_player_z[57]: 1.013 > 1.01
- R-hat for age_tilt_player_z[71]: 1.013 > 1.01
- R-hat for age_tilt_player_z[73]: 1.013 > 1.01
- R-hat for age_tilt_player_z[77]: 1.010 > 1.01
- R-hat for age_tilt_player_z[121]: 1.011 > 1.01
- R-hat for age_tilt_player_z[131]: 1.017 > 1.01
- R-hat for age_tilt_player[95]: 1.011 > 1.01
- R-hat for age_tilt_player[121]: 1.012 > 1.01
- R-hat for age_tilt_player[131]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[122]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[131]: 1.012 > 1.01
- R-hat for rate_per_36_position_at_27[3]: 1.011 > 1.01
- … +5 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 83.6%
- ✓ **bias_near_zero**: bias = +0.613
- ✓ **z_error_well_calibrated**: z-error mean=+0.26, sd=0.97
- ✓ **top_25_tier_accuracy**: top-25 overlap = 72.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 195
- empirical OOS SD: 1.974 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 1.893
- RMSE: 2.377
- bias: +0.613
- coverage 50%: 49.7%
- coverage 80%: 83.6%
- coverage 90%: 89.7%
- z-error: mean=+0.256 sd=0.973
- top-25 tier accuracy: 72.0%
- top-50 tier accuracy: 80.0%
