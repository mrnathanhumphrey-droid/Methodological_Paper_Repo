# skill fit: backtest_FGA_phase4_v4_quadratic_tq_g_2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260528T083558Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 85,702
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 8723.9s (145.4 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0234
- min ESS: 241
- params summarized: 1901

### issues
- R-hat for mu_position[1]: 1.013 > 1.01
- R-hat for mu_player[169]: 1.014 > 1.01
- R-hat for mu_player[188]: 1.014 > 1.01
- R-hat for mu_player[231]: 1.011 > 1.01
- R-hat for mu_player[240]: 1.011 > 1.01
- R-hat for mu_player[254]: 1.023 > 1.01
- R-hat for mu_player[256]: 1.010 > 1.01
- R-hat for mu_player[262]: 1.013 > 1.01
- R-hat for peak_age_pos[1]: 1.014 > 1.01
- ESS for peak_age_pos[1]: 241 < 400
- R-hat for peak_age_pos[2]: 1.012 > 1.01
- ESS for peak_age_pos[2]: 316 < 400
- R-hat for beta_age_pos[1]: 1.013 > 1.01
- ESS for beta_age_pos[1]: 243 < 400
- R-hat for beta_age_pos[2]: 1.012 > 1.01
- ESS for beta_age_pos[2]: 340 < 400
- R-hat for age_tilt_player_z[181]: 1.011 > 1.01
- R-hat for age_tilt_player_z[303]: 1.010 > 1.01
- R-hat for age_tilt_player_z[401]: 1.014 > 1.01
- R-hat for age_tilt_player_z[448]: 1.013 > 1.01
- … +11 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 77.0%
- ✓ **bias_near_zero**: bias = -0.133
- ✓ **z_error_well_calibrated**: z-error mean=-0.11, sd=1.23
- ✓ **top_25_tier_accuracy**: top-25 overlap = 68.0%

## backtest metrics (FGA)
- train: 2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FGA
- N players: 256
- empirical OOS SD: 1.369 FGA/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 47.5%
- MAE: 1.506
- RMSE: 1.991
- bias: -0.133
- coverage 50%: 44.9%
- coverage 80%: 77.0%
- coverage 90%: 83.2%
- z-error: mean=-0.106 sd=1.234
- top-25 tier accuracy: 68.0%
- top-50 tier accuracy: 76.0%
