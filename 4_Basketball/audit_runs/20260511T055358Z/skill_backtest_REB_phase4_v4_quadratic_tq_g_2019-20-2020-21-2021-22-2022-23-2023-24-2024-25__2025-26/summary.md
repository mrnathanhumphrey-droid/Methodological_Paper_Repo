# skill fit: backtest_REB_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260511T055358Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 63,455
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 4220.7s (70.3 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0264
- min ESS: 134
- params summarized: 905

### issues
- R-hat for mu_player[56]: 1.017 > 1.01
- R-hat for sigma_age_player: 1.026 > 1.01
- ESS for sigma_age_player: 134 < 400
- R-hat for age_tilt_player_z[17]: 1.012 > 1.01
- R-hat for age_tilt_player_z[116]: 1.010 > 1.01
- R-hat for age_tilt_player_z[142]: 1.012 > 1.01
- R-hat for age_tilt_player_z[198]: 1.013 > 1.01
- R-hat for age_tilt_player[52]: 1.010 > 1.01
- R-hat for age_tilt_player[80]: 1.011 > 1.01
- R-hat for age_tilt_player[82]: 1.010 > 1.01
- R-hat for age_tilt_player[181]: 1.010 > 1.01
- R-hat for age_tilt_player[188]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[56]: 1.016 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 87.6%
- ✓ **bias_near_zero**: bias = +0.083
- ✓ **z_error_well_calibrated**: z-error mean=+0.08, sd=0.95
- ✓ **top_25_tier_accuracy**: top-25 overlap = 88.0%

## backtest metrics (REB)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: REB
- N players: 105
- empirical OOS SD: 0.749 REB/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.657
- RMSE: 0.852
- bias: +0.083
- coverage 50%: 55.2%
- coverage 80%: 87.6%
- coverage 90%: 90.5%
- z-error: mean=+0.082 sd=0.950
- top-25 tier accuracy: 88.0%
- top-50 tier accuracy: 96.0%
