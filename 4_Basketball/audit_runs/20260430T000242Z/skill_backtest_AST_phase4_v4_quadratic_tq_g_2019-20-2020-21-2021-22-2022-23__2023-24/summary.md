# skill fit: backtest_AST_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260430T000242Z`
- stan model: `hierarchical_aging_quadratic_v3_pp_phi.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3352.6s (55.9 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0118
- min ESS: 305
- params summarized: 910

### issues
- R-hat for mu_player[81]: 1.012 > 1.01
- R-hat for sigma_age_player: 1.011 > 1.01
- ESS for sigma_age_player: 305 < 400
- R-hat for phi[2]: 1.011 > 1.01
- R-hat for age_tilt_player[154]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[81]: 1.012 > 1.01
- R-hat for phi_position[2]: 1.011 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 77.4%
- ✓ **bias_near_zero**: bias = -0.024
- ✓ **z_error_well_calibrated**: z-error mean=-0.06, sd=1.15
- ✓ **top_25_tier_accuracy**: top-25 overlap = 76.0%

## backtest metrics (AST)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: AST
- N players: 195
- empirical OOS SD: 0.620 AST/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 0.666
- RMSE: 0.883
- bias: -0.024
- coverage 50%: 46.2%
- coverage 80%: 77.4%
- coverage 90%: 83.6%
- z-error: mean=-0.057 sd=1.146
- top-25 tier accuracy: 76.0%
- top-50 tier accuracy: 76.0%
