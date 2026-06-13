# skill fit: backtest_FG3A_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260511T175226Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 63,455
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 5483.6s (91.4 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0135
- min ESS: 754
- params summarized: 905

### issues
- R-hat for mu_player[67]: 1.013 > 1.01
- R-hat for mu_player[80]: 1.014 > 1.01
- R-hat for age_tilt_player_z[5]: 1.010 > 1.01
- R-hat for age_tilt_player_z[18]: 1.010 > 1.01
- R-hat for age_tilt_player[67]: 1.011 > 1.01
- R-hat for age_tilt_player[78]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[67]: 1.012 > 1.01
- R-hat for rate_per_36_at_27[80]: 1.013 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 78.1%
- ✓ **bias_near_zero**: bias = -0.141
- ✓ **z_error_well_calibrated**: z-error mean=-0.17, sd=1.10
- ✓ **top_25_tier_accuracy**: top-25 overlap = 88.0%

## backtest metrics (FG3A)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FG3A
- N players: 105
- empirical OOS SD: 0.887 FG3A/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.915
- RMSE: 1.161
- bias: -0.141
- coverage 50%: 45.7%
- coverage 80%: 78.1%
- coverage 90%: 84.8%
- z-error: mean=-0.166 sd=1.104
- top-25 tier accuracy: 88.0%
- top-50 tier accuracy: 80.0%
