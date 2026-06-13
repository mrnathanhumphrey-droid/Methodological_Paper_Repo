# skill fit: backtest_FGM_phase4_v4_quadratic_tq_g_2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260528T045035Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 85,702
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 7977.1s (133.0 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0170
- min ESS: 221
- params summarized: 1901

### issues
- R-hat for mu_player[15]: 1.011 > 1.01
- R-hat for mu_player[23]: 1.011 > 1.01
- R-hat for mu_player[249]: 1.011 > 1.01
- R-hat for mu_player[368]: 1.015 > 1.01
- R-hat for mu_player[449]: 1.011 > 1.01
- R-hat for sigma_position: 1.017 > 1.01
- ESS for sigma_position: 236 < 400
- R-hat for peak_age_pos[1]: 1.011 > 1.01
- ESS for peak_age_pos[1]: 221 < 400
- R-hat for beta_age_pos[1]: 1.014 > 1.01
- ESS for beta_age_pos[1]: 223 < 400
- R-hat for sigma_age_player: 1.015 > 1.01
- ESS for sigma_age_player: 271 < 400
- R-hat for age_tilt_player_z[25]: 1.011 > 1.01
- R-hat for age_tilt_player_z[124]: 1.010 > 1.01
- R-hat for age_tilt_player_z[159]: 1.014 > 1.01
- R-hat for age_tilt_player_z[208]: 1.010 > 1.01
- R-hat for age_tilt_player_z[240]: 1.012 > 1.01
- R-hat for age_tilt_player_z[272]: 1.012 > 1.01
- R-hat for age_tilt_player_z[300]: 1.012 > 1.01
- … +19 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 77.7%
- ✓ **bias_near_zero**: bias = -0.052
- ✓ **z_error_well_calibrated**: z-error mean=-0.07, sd=1.14
- ✓ **top_25_tier_accuracy**: top-25 overlap = 60.0%

## backtest metrics (FGM)
- train: 2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FGA
- N players: 256
- empirical OOS SD: 0.711 FGM/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 47.5%
- MAE: 0.733
- RMSE: 0.951
- bias: -0.052
- coverage 50%: 48.4%
- coverage 80%: 77.7%
- coverage 90%: 86.3%
- z-error: mean=-0.074 sd=1.138
- top-25 tier accuracy: 60.0%
- top-50 tier accuracy: 76.0%
