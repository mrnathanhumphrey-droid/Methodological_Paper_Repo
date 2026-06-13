# skill fit: backtest_FG3M_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260511T081127Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 63,455
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3816.5s (63.6 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0140
- min ESS: 310
- params summarized: 905

### issues
- R-hat for mu_player[3]: 1.010 > 1.01
- R-hat for mu_player[156]: 1.014 > 1.01
- R-hat for sigma_age_player: 1.012 > 1.01
- ESS for sigma_age_player: 310 < 400
- R-hat for age_tilt_player_z[79]: 1.010 > 1.01
- R-hat for age_tilt_player_z[109]: 1.013 > 1.01
- R-hat for age_tilt_player_z[142]: 1.012 > 1.01
- R-hat for age_tilt_player[57]: 1.010 > 1.01
- R-hat for age_tilt_player[142]: 1.010 > 1.01
- R-hat for age_tilt_player[186]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[156]: 1.014 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 80.0%
- ✓ **bias_near_zero**: bias = -0.044
- ✓ **z_error_well_calibrated**: z-error mean=-0.12, sd=1.04
- ✓ **top_25_tier_accuracy**: top-25 overlap = 68.0%

## backtest metrics (FG3M)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FG3A
- N players: 105
- empirical OOS SD: 0.381 FG3M/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.367
- RMSE: 0.482
- bias: -0.044
- coverage 50%: 54.3%
- coverage 80%: 80.0%
- coverage 90%: 87.6%
- z-error: mean=-0.117 sd=1.040
- top-25 tier accuracy: 68.0%
- top-50 tier accuracy: 82.0%
