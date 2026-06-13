# skill fit: backtest_AST_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260511T070745Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 63,455
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 4419.0s (73.6 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0232
- min ESS: 351
- params summarized: 905

### issues
- R-hat for mu_player[30]: 1.011 > 1.01
- R-hat for sigma_age_player: 1.012 > 1.01
- ESS for sigma_age_player: 351 < 400
- R-hat for age_tilt_player_z[133]: 1.023 > 1.01
- R-hat for age_tilt_player[133]: 1.014 > 1.01
- R-hat for rate_per_36_at_27[30]: 1.010 > 1.01
- R-hat for age_curve_position[3,7]: 1.010 > 1.01
- R-hat for age_curve_position[3,8]: 1.010 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 83.8%
- ✓ **bias_near_zero**: bias = +0.063
- ✓ **z_error_well_calibrated**: z-error mean=+0.06, sd=1.06
- ✓ **top_25_tier_accuracy**: top-25 overlap = 72.0%

## backtest metrics (AST)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: AST
- N players: 105
- empirical OOS SD: 0.683 AST/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.618
- RMSE: 0.872
- bias: +0.063
- coverage 50%: 59.0%
- coverage 80%: 83.8%
- coverage 90%: 88.6%
- z-error: mean=+0.056 sd=1.063
- top-25 tier accuracy: 72.0%
- top-50 tier accuracy: 84.0%
