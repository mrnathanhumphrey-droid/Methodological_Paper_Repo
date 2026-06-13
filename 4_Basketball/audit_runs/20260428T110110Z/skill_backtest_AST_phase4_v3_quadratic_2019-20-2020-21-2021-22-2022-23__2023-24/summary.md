# skill fit: backtest_AST_phase4_v3_quadratic_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260428T110110Z`
- stan model: `hierarchical_aging_quadratic_v1.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 5021.6s (83.7 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0220
- min ESS: 265
- params summarized: 900

### issues
- R-hat for mu_player[9]: 1.013 > 1.01
- R-hat for peak_age_pos[2]: 1.021 > 1.01
- ESS for peak_age_pos[2]: 265 < 400
- R-hat for beta_age_pos[2]: 1.022 > 1.01
- ESS for beta_age_pos[2]: 289 < 400
- R-hat for sigma_age_player: 1.012 > 1.01
- ESS for sigma_age_player: 350 < 400
- R-hat for age_tilt_player_z[49]: 1.013 > 1.01
- R-hat for age_tilt_player[116]: 1.010 > 1.01
- R-hat for age_tilt_player[148]: 1.012 > 1.01
- R-hat for rate_per_36_at_27[5]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[9]: 1.014 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 75.4%
- ✓ **bias_near_zero**: bias = -0.030
- ✓ **z_error_well_calibrated**: z-error mean=-0.07, sd=1.16
- ✓ **top_25_tier_accuracy**: top-25 overlap = 76.0%

## backtest metrics (AST)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: AST
- N players: 195
- empirical OOS SD: 0.620 AST/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 0.684
- RMSE: 0.902
- bias: -0.030
- coverage 50%: 47.7%
- coverage 80%: 75.4%
- coverage 90%: 84.1%
- z-error: mean=-0.072 sd=1.156
- top-25 tier accuracy: 76.0%
- top-50 tier accuracy: 76.0%
