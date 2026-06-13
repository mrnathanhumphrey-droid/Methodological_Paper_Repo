# skill fit: backtest_PTS_phase4_v3_quadratic_2019-20-2020-21-2021-22__2022-23

- run timestamp: `20260428T031417Z`
- stan model: `hierarchical_aging_quadratic_v1.stan`
- observations: 34,052
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3282.2s (54.7 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0236
- min ESS: 196
- params summarized: 900

### issues
- R-hat for mu_player[6]: 1.012 > 1.01
- R-hat for mu_player[8]: 1.011 > 1.01
- R-hat for mu_player[42]: 1.015 > 1.01
- R-hat for mu_player[63]: 1.011 > 1.01
- R-hat for mu_player[96]: 1.011 > 1.01
- R-hat for sigma_position: 1.024 > 1.01
- ESS for sigma_position: 196 < 400
- R-hat for sigma_age_player: 1.011 > 1.01
- ESS for sigma_age_player: 234 < 400
- R-hat for age_tilt_player_z[15]: 1.011 > 1.01
- R-hat for age_tilt_player_z[21]: 1.014 > 1.01
- R-hat for age_tilt_player_z[22]: 1.012 > 1.01
- R-hat for age_tilt_player_z[41]: 1.010 > 1.01
- R-hat for age_tilt_player_z[63]: 1.018 > 1.01
- R-hat for age_tilt_player_z[83]: 1.010 > 1.01
- R-hat for age_tilt_player_z[93]: 1.014 > 1.01
- R-hat for age_tilt_player_z[131]: 1.011 > 1.01
- R-hat for age_tilt_player_z[168]: 1.011 > 1.01
- R-hat for age_tilt_player_z[191]: 1.016 > 1.01
- R-hat for rate_per_36_at_27[6]: 1.011 > 1.01
- … +5 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 80.9%
- ✓ **bias_near_zero**: bias = -0.151
- ✓ **z_error_well_calibrated**: z-error mean=-0.06, sd=1.16
- ✓ **top_25_tier_accuracy**: top-25 overlap = 84.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22
- test: 2022-23
- mates_usage_stat: FGA
- N players: 199
- empirical OOS SD: 1.781 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 70.3%
- MAE: 1.882
- RMSE: 2.535
- bias: -0.151
- coverage 50%: 50.3%
- coverage 80%: 80.9%
- coverage 90%: 84.4%
- z-error: mean=-0.064 sd=1.161
- top-25 tier accuracy: 84.0%
- top-50 tier accuracy: 76.0%
