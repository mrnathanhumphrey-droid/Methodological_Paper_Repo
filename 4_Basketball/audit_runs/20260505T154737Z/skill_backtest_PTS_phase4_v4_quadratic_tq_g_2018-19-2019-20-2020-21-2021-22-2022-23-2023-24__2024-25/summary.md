# skill fit: backtest_PTS_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25

- run timestamp: `20260505T154737Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 68,336
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 8651.5s (144.2 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0227
- min ESS: 253
- params summarized: 905

### issues
- R-hat for mu_player[41]: 1.012 > 1.01
- R-hat for mu_player[54]: 1.016 > 1.01
- R-hat for mu_player[74]: 1.010 > 1.01
- R-hat for mu_player[123]: 1.011 > 1.01
- R-hat for mu_player[182]: 1.011 > 1.01
- R-hat for sigma_position: 1.023 > 1.01
- ESS for sigma_position: 253 < 400
- ESS for peak_age_pos[1]: 282 < 400
- ESS for beta_age_pos[1]: 309 < 400
- R-hat for sigma_age_player: 1.016 > 1.01
- R-hat for age_tilt_player_z[25]: 1.010 > 1.01
- R-hat for age_tilt_player_z[54]: 1.010 > 1.01
- R-hat for age_tilt_player_z[101]: 1.013 > 1.01
- R-hat for age_tilt_player_z[108]: 1.019 > 1.01
- R-hat for age_tilt_player_z[136]: 1.011 > 1.01
- R-hat for age_tilt_player_z[137]: 1.012 > 1.01
- R-hat for age_tilt_player_z[156]: 1.013 > 1.01
- R-hat for age_tilt_player[25]: 1.010 > 1.01
- R-hat for age_tilt_player[31]: 1.011 > 1.01
- R-hat for age_tilt_player[52]: 1.010 > 1.01
- … +7 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 88.5%
- ✓ **bias_near_zero**: bias = -0.122
- ✓ **z_error_well_calibrated**: z-error mean=-0.06, sd=0.90
- ✓ **top_25_tier_accuracy**: top-25 overlap = 88.0%

## backtest metrics (PTS)
- train: 2018-19,2019-20,2020-21,2021-22,2022-23,2023-24
- test: 2024-25
- mates_usage_stat: FGA
- N players: 131
- empirical OOS SD: 2.293 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 41.1%
- MAE: 1.887
- RMSE: 2.350
- bias: -0.122
- coverage 50%: 56.5%
- coverage 80%: 88.5%
- coverage 90%: 93.9%
- z-error: mean=-0.060 sd=0.903
- top-25 tier accuracy: 88.0%
- top-50 tier accuracy: 84.0%
