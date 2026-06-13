# skill fit: backtest_AST_phase4_v4_quadratic_tq_g_2017-18-2018-19-2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260506T002014Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 70,243
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 5362.8s (89.4 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0111
- min ESS: 505
- params summarized: 905

### issues
- R-hat for mu_player[179]: 1.010 > 1.01
- R-hat for age_tilt_player_z[45]: 1.011 > 1.01
- R-hat for age_tilt_player[63]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[179]: 1.010 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 76.5%
- ✓ **bias_near_zero**: bias = -0.086
- ✓ **z_error_well_calibrated**: z-error mean=-0.12, sd=1.12
- ✓ **top_25_tier_accuracy**: top-25 overlap = 72.0%

## backtest metrics (AST)
- train: 2017-18,2018-19,2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: AST
- N players: 153
- empirical OOS SD: 0.686 AST/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 34.6%
- MAE: 0.688
- RMSE: 0.912
- bias: -0.086
- coverage 50%: 53.6%
- coverage 80%: 76.5%
- coverage 90%: 82.4%
- z-error: mean=-0.125 sd=1.120
- top-25 tier accuracy: 72.0%
- top-50 tier accuracy: 86.0%
