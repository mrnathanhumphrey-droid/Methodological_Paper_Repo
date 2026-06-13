# skill fit: backtest_AST_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25

- run timestamp: `20260505T183718Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 68,336
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 4993.4s (83.2 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0132
- min ESS: 464
- params summarized: 905

### issues
- R-hat for age_tilt_player_z[140]: 1.012 > 1.01
- R-hat for age_tilt_player_z[158]: 1.010 > 1.01
- R-hat for age_tilt_player_z[160]: 1.011 > 1.01
- R-hat for age_tilt_player[140]: 1.013 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 84.7%
- ✓ **bias_near_zero**: bias = +0.149
- ✓ **z_error_well_calibrated**: z-error mean=+0.17, sd=1.07
- ✓ **top_25_tier_accuracy**: top-25 overlap = 72.0%

## backtest metrics (AST)
- train: 2018-19,2019-20,2020-21,2021-22,2022-23,2023-24
- test: 2024-25
- mates_usage_stat: AST
- N players: 131
- empirical OOS SD: 0.693 AST/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 41.1%
- MAE: 0.713
- RMSE: 1.005
- bias: +0.149
- coverage 50%: 48.1%
- coverage 80%: 84.7%
- coverage 90%: 89.3%
- z-error: mean=+0.172 sd=1.067
- top-25 tier accuracy: 72.0%
- top-50 tier accuracy: 82.0%
