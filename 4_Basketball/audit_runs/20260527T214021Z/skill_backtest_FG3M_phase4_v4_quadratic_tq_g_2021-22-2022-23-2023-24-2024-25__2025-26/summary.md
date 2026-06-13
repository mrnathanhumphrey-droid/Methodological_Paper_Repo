# skill fit: backtest_FG3M_phase4_v4_quadratic_tq_g_2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260527T214021Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 85,702
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 7463.7s (124.4 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0133
- min ESS: 260
- params summarized: 1901

### issues
- R-hat for mu_player[143]: 1.011 > 1.01
- R-hat for mu_player[182]: 1.010 > 1.01
- R-hat for mu_player[208]: 1.010 > 1.01
- R-hat for mu_player[364]: 1.010 > 1.01
- R-hat for gamma_pos[2]: 1.011 > 1.01
- ESS for sigma_age_player: 260 < 400
- R-hat for age_tilt_player_z[204]: 1.011 > 1.01
- R-hat for age_tilt_player_z[276]: 1.012 > 1.01
- R-hat for age_tilt_player_z[278]: 1.013 > 1.01
- R-hat for age_tilt_player_z[292]: 1.011 > 1.01
- R-hat for age_tilt_player_z[338]: 1.011 > 1.01
- R-hat for age_tilt_player_z[398]: 1.011 > 1.01
- R-hat for age_tilt_player[204]: 1.012 > 1.01
- R-hat for age_tilt_player[211]: 1.011 > 1.01
- R-hat for age_tilt_player[278]: 1.010 > 1.01
- R-hat for age_tilt_player[381]: 1.013 > 1.01
- R-hat for rate_per_36_at_27[143]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[208]: 1.012 > 1.01
- R-hat for rate_per_36_at_27[364]: 1.011 > 1.01
- R-hat for age_curve_position[2,19]: 1.010 > 1.01
- … +5 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 80.1%
- ✓ **bias_near_zero**: bias = +0.020
- ✓ **z_error_well_calibrated**: z-error mean=+0.02, sd=1.06
- ✓ **top_25_tier_accuracy**: top-25 overlap = 64.0%

## backtest metrics (FG3M)
- train: 2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FG3A
- N players: 256
- empirical OOS SD: 0.358 FG3M/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 47.5%
- MAE: 0.372
- RMSE: 0.489
- bias: +0.020
- coverage 50%: 52.7%
- coverage 80%: 80.1%
- coverage 90%: 85.5%
- z-error: mean=+0.021 sd=1.061
- top-25 tier accuracy: 64.0%
- top-50 tier accuracy: 70.0%
