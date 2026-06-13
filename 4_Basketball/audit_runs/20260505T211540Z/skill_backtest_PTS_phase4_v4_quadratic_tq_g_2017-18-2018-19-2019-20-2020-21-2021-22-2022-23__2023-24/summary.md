# skill fit: backtest_PTS_phase4_v4_quadratic_tq_g_2017-18-2018-19-2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260505T211540Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 70,243
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 9495.1s (158.3 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0316
- min ESS: 169
- params summarized: 905

### issues
- R-hat for mu_player[24]: 1.015 > 1.01
- R-hat for mu_player[58]: 1.011 > 1.01
- R-hat for mu_player[121]: 1.011 > 1.01
- R-hat for mu_player[152]: 1.014 > 1.01
- R-hat for sigma_position: 1.032 > 1.01
- ESS for sigma_position: 169 < 400
- R-hat for peak_age_pos[1]: 1.011 > 1.01
- ESS for peak_age_pos[1]: 239 < 400
- ESS for peak_age_pos[2]: 363 < 400
- ESS for beta_age_pos[1]: 251 < 400
- ESS for beta_age_pos[2]: 373 < 400
- R-hat for age_tilt_player_z[24]: 1.010 > 1.01
- R-hat for age_tilt_player_z[33]: 1.010 > 1.01
- R-hat for age_tilt_player_z[80]: 1.013 > 1.01
- R-hat for age_tilt_player_z[145]: 1.012 > 1.01
- R-hat for age_tilt_player_z[159]: 1.012 > 1.01
- R-hat for beta_alpha_promotion: 1.012 > 1.01
- R-hat for age_tilt_player[32]: 1.011 > 1.01
- R-hat for age_tilt_player[70]: 1.011 > 1.01
- R-hat for age_tilt_player[159]: 1.010 > 1.01
- … +6 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 86.3%
- ✓ **bias_near_zero**: bias = +0.460
- ✓ **z_error_well_calibrated**: z-error mean=+0.17, sd=0.91
- ✓ **top_25_tier_accuracy**: top-25 overlap = 76.0%

## backtest metrics (PTS)
- train: 2017-18,2018-19,2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 153
- empirical OOS SD: 2.253 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 34.6%
- MAE: 1.948
- RMSE: 2.393
- bias: +0.460
- coverage 50%: 51.6%
- coverage 80%: 86.3%
- coverage 90%: 90.8%
- z-error: mean=+0.171 sd=0.909
- top-25 tier accuracy: 76.0%
- top-50 tier accuracy: 86.0%
