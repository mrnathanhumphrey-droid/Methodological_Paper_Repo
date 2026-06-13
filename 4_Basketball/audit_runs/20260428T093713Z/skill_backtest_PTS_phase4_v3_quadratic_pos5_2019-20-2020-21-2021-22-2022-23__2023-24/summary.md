# skill fit: backtest_PTS_phase4_v3_quadratic_pos5_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260428T093713Z`
- stan model: `hierarchical_aging_quadratic_v1.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 8300.2s (138.3 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0149
- min ESS: 452
- params summarized: 960

### issues
- R-hat for mu_player[99]: 1.014 > 1.01
- R-hat for mu_player[181]: 1.012 > 1.01
- R-hat for beta_age_pos[5]: 1.011 > 1.01
- R-hat for age_tilt_player_z[25]: 1.014 > 1.01
- R-hat for age_tilt_player_z[30]: 1.011 > 1.01
- R-hat for age_tilt_player_z[48]: 1.011 > 1.01
- R-hat for age_tilt_player_z[165]: 1.015 > 1.01
- R-hat for age_tilt_player_z[181]: 1.012 > 1.01
- R-hat for age_tilt_player_z[191]: 1.011 > 1.01
- R-hat for age_tilt_player[25]: 1.012 > 1.01
- R-hat for rate_per_36_at_27[99]: 1.014 > 1.01
- R-hat for rate_per_36_at_27[181]: 1.011 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 83.6%
- ✓ **bias_near_zero**: bias = +0.574
- ✓ **z_error_well_calibrated**: z-error mean=+0.24, sd=0.98
- ✓ **top_25_tier_accuracy**: top-25 overlap = 76.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 195
- empirical OOS SD: 1.974 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 1.899
- RMSE: 2.375
- bias: +0.574
- coverage 50%: 47.2%
- coverage 80%: 83.6%
- coverage 90%: 90.3%
- z-error: mean=+0.239 sd=0.978
- top-25 tier accuracy: 76.0%
- top-50 tier accuracy: 80.0%
