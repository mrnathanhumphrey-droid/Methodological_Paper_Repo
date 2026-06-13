# skill fit: backtest_PTS_phase4_v3_quadratic_2019-20-2020-21-2021-22-2022-23-2023-24__2024-25

- run timestamp: `20260428T071826Z`
- stan model: `hierarchical_aging_quadratic_v1.stan`
- observations: 60,169
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 13046.9s (217.4 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0159
- min ESS: 300
- params summarized: 900

### issues
- R-hat for mu_player[14]: 1.016 > 1.01
- R-hat for mu_player[194]: 1.013 > 1.01
- R-hat for sigma_position: 1.015 > 1.01
- ESS for sigma_position: 300 < 400
- R-hat for peak_age_pos[1]: 1.014 > 1.01
- ESS for peak_age_pos[1]: 391 < 400
- ESS for peak_age_pos[2]: 396 < 400
- R-hat for beta_age_pos[1]: 1.013 > 1.01
- R-hat for age_tilt_player_z[14]: 1.015 > 1.01
- R-hat for age_tilt_player_z[77]: 1.011 > 1.01
- R-hat for age_tilt_player_z[112]: 1.010 > 1.01
- R-hat for age_tilt_player_z[133]: 1.010 > 1.01
- R-hat for age_tilt_player[135]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[14]: 1.016 > 1.01
- R-hat for rate_per_36_at_27[194]: 1.013 > 1.01
- R-hat for peak_to_27_ratio[1]: 1.010 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 85.8%
- ✓ **bias_near_zero**: bias = -0.013
- ✓ **z_error_well_calibrated**: z-error mean=-0.02, sd=0.98
- ✓ **top_25_tier_accuracy**: top-25 overlap = 72.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24
- test: 2024-25
- mates_usage_stat: FGA
- N players: 183
- empirical OOS SD: 2.095 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 64.7%
- MAE: 1.997
- RMSE: 2.432
- bias: -0.013
- coverage 50%: 44.8%
- coverage 80%: 85.8%
- coverage 90%: 93.4%
- z-error: mean=-0.023 sd=0.985
- top-25 tier accuracy: 72.0%
- top-50 tier accuracy: 74.0%
