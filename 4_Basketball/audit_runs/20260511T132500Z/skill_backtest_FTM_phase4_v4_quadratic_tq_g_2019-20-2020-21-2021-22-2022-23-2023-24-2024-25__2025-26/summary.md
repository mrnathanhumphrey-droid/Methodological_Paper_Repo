# skill fit: backtest_FTM_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260511T132500Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 63,455
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3975.5s (66.3 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0179
- min ESS: 232
- params summarized: 905

### issues
- R-hat for mu_player[153]: 1.010 > 1.01
- R-hat for sigma_position: 1.013 > 1.01
- ESS for sigma_position: 360 < 400
- R-hat for sigma_age_player: 1.016 > 1.01
- ESS for sigma_age_player: 232 < 400
- R-hat for age_tilt_player_z[82]: 1.016 > 1.01
- R-hat for age_tilt_player_z[153]: 1.012 > 1.01
- R-hat for age_tilt_player_z[173]: 1.013 > 1.01
- R-hat for age_tilt_player[82]: 1.018 > 1.01
- R-hat for rate_per_36_at_27[153]: 1.010 > 1.01

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 71.4%
- ✓ **bias_near_zero**: bias = -0.427
- ✗ **z_error_well_calibrated**: z-error mean=-0.56, sd=1.29
- ✓ **top_25_tier_accuracy**: top-25 overlap = 84.0%

## backtest metrics (FTM)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FTA
- N players: 105
- empirical OOS SD: 0.642 FTM/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.829
- RMSE: 1.112
- bias: -0.427
- coverage 50%: 42.9%
- coverage 80%: 71.4%
- coverage 90%: 78.1%
- z-error: mean=-0.555 sd=1.292
- top-25 tier accuracy: 84.0%
- top-50 tier accuracy: 80.0%
