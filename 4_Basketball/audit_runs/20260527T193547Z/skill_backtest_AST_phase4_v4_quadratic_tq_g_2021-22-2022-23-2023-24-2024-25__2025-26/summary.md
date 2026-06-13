# skill fit: backtest_AST_phase4_v4_quadratic_tq_g_2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260527T193547Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 85,702
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 7795.3s (129.9 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0199
- min ESS: 315
- params summarized: 1901

### issues
- R-hat for mu_player[11]: 1.011 > 1.01
- R-hat for mu_player[21]: 1.011 > 1.01
- R-hat for mu_player[37]: 1.020 > 1.01
- R-hat for mu_player[51]: 1.011 > 1.01
- R-hat for mu_player[166]: 1.011 > 1.01
- R-hat for mu_player[291]: 1.010 > 1.01
- R-hat for mu_player[437]: 1.011 > 1.01
- ESS for sigma_age_player: 315 < 400
- R-hat for age_tilt_player_z[37]: 1.012 > 1.01
- R-hat for age_tilt_player_z[46]: 1.011 > 1.01
- R-hat for age_tilt_player_z[202]: 1.010 > 1.01
- R-hat for age_tilt_player_z[264]: 1.011 > 1.01
- R-hat for age_tilt_player_z[297]: 1.011 > 1.01
- R-hat for age_tilt_player_z[309]: 1.014 > 1.01
- R-hat for age_tilt_player_z[313]: 1.011 > 1.01
- R-hat for age_tilt_player_z[437]: 1.015 > 1.01
- R-hat for age_tilt_player[37]: 1.014 > 1.01
- R-hat for age_tilt_player[264]: 1.010 > 1.01
- R-hat for age_tilt_player[297]: 1.010 > 1.01
- R-hat for age_tilt_player[345]: 1.011 > 1.01
- … +6 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 78.9%
- ✓ **bias_near_zero**: bias = +0.005
- ✓ **z_error_well_calibrated**: z-error mean=-0.00, sd=1.19
- ✓ **top_25_tier_accuracy**: top-25 overlap = 64.0%

## backtest metrics (AST)
- train: 2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: AST
- N players: 256
- empirical OOS SD: 0.611 AST/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 47.5%
- MAE: 0.659
- RMSE: 0.899
- bias: +0.005
- coverage 50%: 50.4%
- coverage 80%: 78.9%
- coverage 90%: 84.0%
- z-error: mean=-0.004 sd=1.193
- top-25 tier accuracy: 64.0%
- top-50 tier accuracy: 78.0%
