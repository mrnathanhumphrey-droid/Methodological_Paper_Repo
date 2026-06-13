# skill fit: backtest_PTS_phase4_v3_quadratic_tq_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260428T152248Z`
- stan model: `hierarchical_aging_quadratic_v2.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 5207.1s (86.8 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0225
- min ESS: 306
- params summarized: 899

### issues
- R-hat for mu_position[1]: 1.012 > 1.01
- R-hat for mu_player[17]: 1.011 > 1.01
- R-hat for mu_player[36]: 1.010 > 1.01
- R-hat for mu_player[41]: 1.013 > 1.01
- R-hat for mu_player[46]: 1.012 > 1.01
- R-hat for mu_player[55]: 1.013 > 1.01
- R-hat for mu_player[61]: 1.011 > 1.01
- R-hat for mu_player[76]: 1.010 > 1.01
- R-hat for mu_player[177]: 1.015 > 1.01
- R-hat for mu_player[197]: 1.017 > 1.01
- R-hat for sigma_position: 1.018 > 1.01
- ESS for sigma_position: 306 < 400
- R-hat for peak_age_pos[1]: 1.011 > 1.01
- ESS for peak_age_pos[1]: 340 < 400
- R-hat for beta_age_pos[1]: 1.012 > 1.01
- ESS for beta_age_pos[1]: 344 < 400
- R-hat for age_tilt_player_z[15]: 1.014 > 1.01
- R-hat for age_tilt_player_z[26]: 1.014 > 1.01
- R-hat for age_tilt_player_z[41]: 1.014 > 1.01
- R-hat for age_tilt_player_z[44]: 1.015 > 1.01
- … +27 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 83.6%
- ✓ **bias_near_zero**: bias = +0.593
- ✓ **z_error_well_calibrated**: z-error mean=+0.25, sd=0.97
- ✓ **top_25_tier_accuracy**: top-25 overlap = 72.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 195
- empirical OOS SD: 1.974 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 1.887
- RMSE: 2.359
- bias: +0.593
- coverage 50%: 49.7%
- coverage 80%: 83.6%
- coverage 90%: 91.3%
- z-error: mean=+0.248 sd=0.974
- top-25 tier accuracy: 72.0%
- top-50 tier accuracy: 80.0%
