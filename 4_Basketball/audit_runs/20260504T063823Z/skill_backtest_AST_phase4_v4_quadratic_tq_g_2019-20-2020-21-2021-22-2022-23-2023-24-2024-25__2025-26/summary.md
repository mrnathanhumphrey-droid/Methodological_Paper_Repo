# skill fit: backtest_AST_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260504T063823Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 64,126
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 4947.3s (82.5 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0228
- min ESS: 375
- params summarized: 905

### issues
- R-hat for mu_player[32]: 1.014 > 1.01
- R-hat for mu_player[150]: 1.011 > 1.01
- R-hat for mu_player[161]: 1.013 > 1.01
- R-hat for peak_age_pos[1]: 1.013 > 1.01
- ESS for peak_age_pos[1]: 399 < 400
- R-hat for beta_age_pos[1]: 1.012 > 1.01
- ESS for beta_age_pos[1]: 375 < 400
- ESS for sigma_age_player: 393 < 400
- R-hat for age_tilt_player_z[32]: 1.012 > 1.01
- R-hat for age_tilt_player[15]: 1.011 > 1.01
- R-hat for age_tilt_player[32]: 1.023 > 1.01
- R-hat for age_tilt_player[57]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[32]: 1.014 > 1.01
- R-hat for rate_per_36_at_27[150]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[161]: 1.013 > 1.01

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 99.2%
- ✓ **bias_near_zero**: bias = +0.030
- ✗ **z_error_well_calibrated**: z-error mean=+0.04, sd=0.47
- ✓ **top_25_tier_accuracy**: top-25 overlap = 92.0%

## backtest metrics (AST)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: AST
- N players: 133
- empirical OOS SD: 0.691 AST/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.300
- RMSE: 0.396
- bias: +0.030
- coverage 50%: 86.5%
- coverage 80%: 99.2%
- coverage 90%: 100.0%
- z-error: mean=+0.041 sd=0.467
- top-25 tier accuracy: 92.0%
- top-50 tier accuracy: 96.0%
