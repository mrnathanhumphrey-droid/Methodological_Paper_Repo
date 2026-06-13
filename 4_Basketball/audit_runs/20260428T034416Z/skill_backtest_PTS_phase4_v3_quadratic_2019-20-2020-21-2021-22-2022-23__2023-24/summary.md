# skill fit: backtest_PTS_phase4_v3_quadratic_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260428T034416Z`
- stan model: `hierarchical_aging_quadratic_v1.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 5536.9s (92.3 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0131
- min ESS: 320
- params summarized: 900

### issues
- R-hat for mu_player[27]: 1.013 > 1.01
- R-hat for mu_player[39]: 1.011 > 1.01
- R-hat for mu_player[118]: 1.011 > 1.01
- R-hat for mu_player[142]: 1.012 > 1.01
- R-hat for mu_player[144]: 1.010 > 1.01
- R-hat for mu_player[173]: 1.010 > 1.01
- R-hat for mu_player[190]: 1.013 > 1.01
- R-hat for sigma_position: 1.013 > 1.01
- ESS for sigma_position: 320 < 400
- ESS for peak_age_pos[2]: 371 < 400
- R-hat for age_tilt_player_z[4]: 1.011 > 1.01
- R-hat for age_tilt_player_z[66]: 1.011 > 1.01
- R-hat for age_tilt_player_z[70]: 1.012 > 1.01
- R-hat for age_tilt_player_z[133]: 1.011 > 1.01
- R-hat for age_tilt_player_z[146]: 1.010 > 1.01
- R-hat for age_tilt_player_z[190]: 1.011 > 1.01
- R-hat for age_tilt_player_z[193]: 1.013 > 1.01
- R-hat for age_tilt_player[173]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[27]: 1.013 > 1.01
- R-hat for rate_per_36_at_27[39]: 1.010 > 1.01
- … +5 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 83.1%
- ✓ **bias_near_zero**: bias = +0.561
- ✓ **z_error_well_calibrated**: z-error mean=+0.23, sd=0.97
- ✓ **top_25_tier_accuracy**: top-25 overlap = 76.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 195
- empirical OOS SD: 1.974 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 1.882
- RMSE: 2.353
- bias: +0.561
- coverage 50%: 47.7%
- coverage 80%: 83.1%
- coverage 90%: 92.3%
- z-error: mean=+0.233 sd=0.973
- top-25 tier accuracy: 76.0%
- top-50 tier accuracy: 82.0%
