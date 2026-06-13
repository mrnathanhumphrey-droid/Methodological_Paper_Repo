# skill fit: backtest_FG3A_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260504T180404Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 64,126
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 6517.8s (108.6 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0166
- min ESS: 692
- params summarized: 905

### issues
- R-hat for mu_player[82]: 1.011 > 1.01
- R-hat for mu_player[108]: 1.011 > 1.01
- R-hat for mu_player[155]: 1.017 > 1.01
- R-hat for mu_player[185]: 1.014 > 1.01
- R-hat for mu_player[198]: 1.011 > 1.01
- R-hat for age_tilt_player_z[43]: 1.012 > 1.01
- R-hat for age_tilt_player_z[66]: 1.011 > 1.01
- R-hat for age_tilt_player_z[82]: 1.012 > 1.01
- R-hat for age_tilt_player_z[122]: 1.011 > 1.01
- R-hat for age_tilt_player_z[139]: 1.010 > 1.01
- R-hat for age_tilt_player[43]: 1.010 > 1.01
- R-hat for age_tilt_player[82]: 1.011 > 1.01
- R-hat for age_tilt_player[116]: 1.010 > 1.01
- R-hat for age_tilt_player[129]: 1.011 > 1.01
- R-hat for age_tilt_player[157]: 1.013 > 1.01
- R-hat for age_tilt_player[161]: 1.013 > 1.01
- R-hat for rate_per_36_at_27[31]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[82]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[108]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[155]: 1.015 > 1.01
- … +2 more

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 97.0%
- ✓ **bias_near_zero**: bias = -0.062
- ✗ **z_error_well_calibrated**: z-error mean=-0.07, sd=0.56
- ✓ **top_25_tier_accuracy**: top-25 overlap = 88.0%

## backtest metrics (FG3A)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FG3A
- N players: 133
- empirical OOS SD: 0.900 FG3A/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.402
- RMSE: 0.600
- bias: -0.062
- coverage 50%: 85.0%
- coverage 80%: 97.0%
- coverage 90%: 97.7%
- z-error: mean=-0.070 sd=0.556
- top-25 tier accuracy: 88.0%
- top-50 tier accuracy: 88.0%
