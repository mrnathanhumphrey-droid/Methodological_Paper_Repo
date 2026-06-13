# skill fit: backtest_AST_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260429T062944Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3313.6s (55.2 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0131
- min ESS: 370
- params summarized: 905

### issues
- R-hat for mu_player[11]: 1.012 > 1.01
- R-hat for mu_player[63]: 1.010 > 1.01
- ESS for sigma_age_player: 370 < 400
- R-hat for age_tilt_player_z[101]: 1.011 > 1.01
- R-hat for age_tilt_player[11]: 1.013 > 1.01
- R-hat for rate_per_36_at_27[9]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[63]: 1.010 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 78.5%
- ✓ **bias_near_zero**: bias = -0.023
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
- MAE: 0.668
- RMSE: 0.886
- bias: -0.023
- coverage 50%: 46.2%
- coverage 80%: 78.5%
- coverage 90%: 85.1%
- z-error: mean=-0.058 sd=1.146
- top-25 tier accuracy: 76.0%
- top-50 tier accuracy: 76.0%
