# skill fit: backtest_STL_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260430T012828Z`
- stan model: `hierarchical_aging_quadratic_v3_pp_phi.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 2304.7s (38.4 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0390
- min ESS: 105
- params summarized: 910

### issues
- R-hat for mu_player[2]: 1.018 > 1.01
- R-hat for mu_player[59]: 1.020 > 1.01
- R-hat for mu_player[60]: 1.010 > 1.01
- R-hat for mu_player[151]: 1.011 > 1.01
- R-hat for mu_player[175]: 1.011 > 1.01
- R-hat for peak_age_pos[1]: 1.011 > 1.01
- ESS for gamma_pos[1]: 366 < 400
- R-hat for beta_age_pos[1]: 1.019 > 1.01
- R-hat for sigma_age_player: 1.039 > 1.01
- ESS for sigma_age_player: 105 < 400
- R-hat for age_tilt_player_z[101]: 1.013 > 1.01
- R-hat for age_tilt_player[1]: 1.010 > 1.01
- R-hat for age_tilt_player[2]: 1.036 > 1.01
- ESS for age_tilt_player[2]: 249 < 400
- R-hat for age_tilt_player[6]: 1.015 > 1.01
- R-hat for age_tilt_player[12]: 1.015 > 1.01
- R-hat for age_tilt_player[16]: 1.014 > 1.01
- R-hat for age_tilt_player[17]: 1.012 > 1.01
- R-hat for age_tilt_player[18]: 1.011 > 1.01
- R-hat for age_tilt_player[21]: 1.012 > 1.01
- … +74 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 82.1%
- ✓ **bias_near_zero**: bias = -0.016
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
- bias: -0.016
- coverage 50%: 48.7%
- coverage 80%: 82.1%
- coverage 90%: 88.7%
- z-error: mean=-0.073 sd=1.075
- top-25 tier accuracy: 60.0%
- top-50 tier accuracy: 70.0%
