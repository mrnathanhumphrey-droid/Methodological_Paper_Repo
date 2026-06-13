# skill fit: backtest_REB_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260504T051549Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 64,126
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 5159.9s (86.0 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0334
- min ESS: 105
- params summarized: 905

### issues
- R-hat for mu_player[17]: 1.012 > 1.01
- R-hat for mu_player[21]: 1.013 > 1.01
- ESS for mu_player[24]: 386 < 400
- R-hat for mu_player[34]: 1.010 > 1.01
- R-hat for mu_player[65]: 1.010 > 1.01
- R-hat for mu_player[68]: 1.011 > 1.01
- R-hat for mu_player[78]: 1.013 > 1.01
- R-hat for mu_player[160]: 1.011 > 1.01
- R-hat for mu_player[170]: 1.011 > 1.01
- R-hat for sigma_age_player: 1.033 > 1.01
- ESS for sigma_age_player: 105 < 400
- R-hat for age_tilt_player_z[53]: 1.014 > 1.01
- R-hat for age_tilt_player_z[59]: 1.014 > 1.01
- R-hat for age_tilt_player[12]: 1.014 > 1.01
- R-hat for age_tilt_player[20]: 1.011 > 1.01
- ESS for age_tilt_player[20]: 375 < 400
- R-hat for age_tilt_player[21]: 1.015 > 1.01
- R-hat for age_tilt_player[24]: 1.014 > 1.01
- R-hat for age_tilt_player[59]: 1.018 > 1.01
- R-hat for age_tilt_player[68]: 1.011 > 1.01
- … +20 more

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 97.7%
- ✓ **bias_near_zero**: bias = -0.141
- ✗ **z_error_well_calibrated**: z-error mean=-0.16, sd=0.52
- ✓ **top_25_tier_accuracy**: top-25 overlap = 96.0%

## backtest metrics (REB)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: REB
- N players: 133
- empirical OOS SD: 0.744 REB/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.364
- RMSE: 0.520
- bias: -0.141
- coverage 50%: 82.0%
- coverage 80%: 97.7%
- coverage 90%: 99.2%
- z-error: mean=-0.156 sd=0.517
- top-25 tier accuracy: 96.0%
- top-50 tier accuracy: 96.0%
