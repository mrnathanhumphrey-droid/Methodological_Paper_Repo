# skill fit: backtest_BLK_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260504T092852Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 64,126
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3117.3s (52.0 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0181
- min ESS: 229
- params summarized: 905

### issues
- R-hat for mu_player[50]: 1.011 > 1.01
- R-hat for mu_player[51]: 1.010 > 1.01
- R-hat for mu_player[104]: 1.011 > 1.01
- R-hat for mu_player[156]: 1.011 > 1.01
- ESS for beta_age_pos[1]: 324 < 400
- R-hat for sigma_age_player: 1.014 > 1.01
- ESS for sigma_age_player: 229 < 400
- R-hat for age_tilt_player_z[42]: 1.010 > 1.01
- R-hat for age_tilt_player_z[54]: 1.018 > 1.01
- R-hat for age_tilt_player_z[107]: 1.010 > 1.01
- R-hat for age_tilt_player_z[114]: 1.010 > 1.01
- R-hat for age_tilt_player_z[166]: 1.010 > 1.01
- R-hat for age_tilt_player_z[177]: 1.011 > 1.01
- ESS for age_tilt_player[28]: 390 < 400
- ESS for age_tilt_player[70]: 377 < 400
- ESS for age_tilt_player[191]: 330 < 400
- R-hat for rate_per_36_at_27[51]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[104]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[156]: 1.010 > 1.01
- ESS for age_curve_position[1,4]: 393 < 400
- … +4 more

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 97.7%
- ✓ **bias_near_zero**: bias = -0.004
- ✗ **z_error_well_calibrated**: z-error mean=-0.00, sd=0.62
- ✓ **top_25_tier_accuracy**: top-25 overlap = 84.0%

## backtest metrics (BLK)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: BLK
- N players: 133
- empirical OOS SD: 0.182 BLK/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.106
- RMSE: 0.141
- bias: -0.004
- coverage 50%: 74.4%
- coverage 80%: 97.7%
- coverage 90%: 99.2%
- z-error: mean=-0.004 sd=0.623
- top-25 tier accuracy: 84.0%
- top-50 tier accuracy: 92.0%
