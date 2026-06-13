# skill fit: backtest_STL_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260429T080246Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 2197.0s (36.6 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0197
- min ESS: 239
- params summarized: 905

### issues
- R-hat for mu_player[76]: 1.010 > 1.01
- R-hat for sigma_age_player: 1.020 > 1.01
- ESS for sigma_age_player: 239 < 400
- R-hat for age_tilt_player_z[20]: 1.013 > 1.01
- R-hat for age_tilt_player_z[23]: 1.012 > 1.01
- R-hat for age_tilt_player_z[112]: 1.016 > 1.01
- R-hat for age_tilt_player_z[115]: 1.014 > 1.01
- R-hat for age_tilt_player_z[118]: 1.011 > 1.01
- R-hat for age_tilt_player_z[135]: 1.012 > 1.01
- R-hat for age_tilt_player_z[137]: 1.013 > 1.01
- R-hat for age_tilt_player_z[160]: 1.010 > 1.01
- R-hat for age_tilt_player_z[169]: 1.011 > 1.01
- R-hat for age_tilt_player[2]: 1.011 > 1.01
- R-hat for age_tilt_player[10]: 1.011 > 1.01
- R-hat for age_tilt_player[14]: 1.012 > 1.01
- R-hat for age_tilt_player[36]: 1.011 > 1.01
- R-hat for age_tilt_player[39]: 1.012 > 1.01
- R-hat for age_tilt_player[48]: 1.010 > 1.01
- R-hat for age_tilt_player[49]: 1.014 > 1.01
- R-hat for age_tilt_player[50]: 1.011 > 1.01
- … +24 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 81.5%
- ✓ **bias_near_zero**: bias = -0.017
- ✓ **z_error_well_calibrated**: z-error mean=-0.07, sd=1.07
- ✓ **top_25_tier_accuracy**: top-25 overlap = 60.0%

## backtest metrics (STL)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: STL
- N players: 195
- empirical OOS SD: 0.184 STL/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 0.189
- RMSE: 0.246
- bias: -0.017
- coverage 50%: 49.2%
- coverage 80%: 81.5%
- coverage 90%: 88.2%
- z-error: mean=-0.075 sd=1.072
- top-25 tier accuracy: 60.0%
- top-50 tier accuracy: 70.0%
