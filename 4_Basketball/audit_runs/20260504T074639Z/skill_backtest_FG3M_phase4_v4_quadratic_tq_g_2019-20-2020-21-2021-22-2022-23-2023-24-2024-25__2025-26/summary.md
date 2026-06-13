# skill fit: backtest_FG3M_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260504T074639Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 64,126
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 4090.0s (68.2 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0251
- min ESS: 186
- params summarized: 905

### issues
- R-hat for mu_player[146]: 1.011 > 1.01
- R-hat for mu_player[177]: 1.011 > 1.01
- R-hat for sigma_age_player: 1.025 > 1.01
- ESS for sigma_age_player: 186 < 400
- R-hat for age_tilt_player_z[66]: 1.011 > 1.01
- R-hat for age_tilt_player_z[145]: 1.014 > 1.01
- R-hat for age_tilt_player_z[150]: 1.017 > 1.01
- R-hat for age_tilt_player[51]: 1.011 > 1.01
- R-hat for age_tilt_player[82]: 1.010 > 1.01
- R-hat for age_tilt_player[93]: 1.010 > 1.01
- R-hat for age_tilt_player[101]: 1.011 > 1.01
- R-hat for age_tilt_player[102]: 1.010 > 1.01
- R-hat for age_tilt_player[123]: 1.012 > 1.01
- R-hat for age_tilt_player[134]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[146]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[177]: 1.012 > 1.01

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 97.7%
- ✓ **bias_near_zero**: bias = -0.038
- ✗ **z_error_well_calibrated**: z-error mean=-0.08, sd=0.57
- ✓ **top_25_tier_accuracy**: top-25 overlap = 88.0%

## backtest metrics (FG3M)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FG3A
- N players: 133
- empirical OOS SD: 0.388 FG3M/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.199
- RMSE: 0.275
- bias: -0.038
- coverage 50%: 82.0%
- coverage 80%: 97.7%
- coverage 90%: 97.7%
- z-error: mean=-0.078 sd=0.571
- top-25 tier accuracy: 88.0%
- top-50 tier accuracy: 90.0%
