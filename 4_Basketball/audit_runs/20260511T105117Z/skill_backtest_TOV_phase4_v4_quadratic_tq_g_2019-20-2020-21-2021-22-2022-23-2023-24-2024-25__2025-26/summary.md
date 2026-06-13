# skill fit: backtest_TOV_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260511T105117Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 63,455
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3688.9s (61.5 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0283
- min ESS: 113
- params summarized: 905

### issues
- ESS for mu_player[1]: 373 < 400
- R-hat for mu_player[21]: 1.011 > 1.01
- ESS for mu_player[32]: 391 < 400
- R-hat for mu_player[96]: 1.012 > 1.01
- R-hat for mu_player[149]: 1.010 > 1.01
- R-hat for mu_player[178]: 1.012 > 1.01
- R-hat for sigma_player: 1.015 > 1.01
- R-hat for sigma_age_player: 1.028 > 1.01
- ESS for sigma_age_player: 113 < 400
- R-hat for age_tilt_player_z[6]: 1.011 > 1.01
- R-hat for age_tilt_player_z[15]: 1.010 > 1.01
- R-hat for age_tilt_player_z[18]: 1.011 > 1.01
- R-hat for age_tilt_player_z[24]: 1.010 > 1.01
- R-hat for age_tilt_player_z[30]: 1.013 > 1.01
- R-hat for age_tilt_player_z[129]: 1.011 > 1.01
- R-hat for age_tilt_player_z[169]: 1.010 > 1.01
- R-hat for age_tilt_player_z[183]: 1.010 > 1.01
- R-hat for age_tilt_player[1]: 1.010 > 1.01
- ESS for age_tilt_player[1]: 360 < 400
- R-hat for age_tilt_player[9]: 1.013 > 1.01
- … +23 more

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 79.0%
- ✓ **bias_near_zero**: bias = -0.135
- ✗ **z_error_well_calibrated**: z-error mean=-0.36, sd=1.12
- ✓ **top_25_tier_accuracy**: top-25 overlap = 72.0%

## backtest metrics (TOV)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: TOV
- N players: 105
- empirical OOS SD: 0.347 TOV/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.376
- RMSE: 0.473
- bias: -0.135
- coverage 50%: 44.8%
- coverage 80%: 79.0%
- coverage 90%: 80.0%
- z-error: mean=-0.355 sd=1.120
- top-25 tier accuracy: 72.0%
- top-50 tier accuracy: 78.0%
