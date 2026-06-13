# skill fit: backtest_FTA_phase4_v4_quadratic_tq_g_2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260528T095241Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 85,702
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 4593.2s (76.6 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0372
- min ESS: 133
- params summarized: 1901

### issues
- ESS for mu_position[2]: 316 < 400
- R-hat for mu_player[74]: 1.011 > 1.01
- R-hat for mu_player[162]: 1.010 > 1.01
- R-hat for mu_player[189]: 1.011 > 1.01
- R-hat for mu_player[216]: 1.017 > 1.01
- R-hat for mu_player[219]: 1.012 > 1.01
- R-hat for peak_age_pos[1]: 1.020 > 1.01
- ESS for peak_age_pos[1]: 236 < 400
- ESS for peak_age_pos[2]: 361 < 400
- R-hat for beta_age_pos[1]: 1.021 > 1.01
- ESS for beta_age_pos[1]: 238 < 400
- ESS for beta_age_pos[2]: 362 < 400
- R-hat for sigma_age_player: 1.037 > 1.01
- ESS for sigma_age_player: 133 < 400
- R-hat for age_tilt_player_z[73]: 1.010 > 1.01
- R-hat for age_tilt_player_z[233]: 1.010 > 1.01
- R-hat for age_tilt_player_z[264]: 1.012 > 1.01
- R-hat for age_tilt_player_z[298]: 1.017 > 1.01
- R-hat for age_tilt_player_z[338]: 1.011 > 1.01
- R-hat for age_tilt_player_z[339]: 1.012 > 1.01
- … +20 more

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 75.0%
- ✓ **bias_near_zero**: bias = -0.379
- ✗ **z_error_well_calibrated**: z-error mean=-0.47, sd=1.30
- ✓ **top_25_tier_accuracy**: top-25 overlap = 64.0%

## backtest metrics (FTA)
- train: 2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FTA
- N players: 256
- empirical OOS SD: 0.677 FTA/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 47.5%
- MAE: 0.870
- RMSE: 1.169
- bias: -0.379
- coverage 50%: 41.4%
- coverage 80%: 75.0%
- coverage 90%: 81.2%
- z-error: mean=-0.472 sd=1.303
- top-25 tier accuracy: 64.0%
- top-50 tier accuracy: 72.0%
