# skill fit: backtest_STL_phase4_v4_quadratic_tq_g_2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260527T230431Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 85,702
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 5040.4s (84.0 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0450
- min ESS: 129
- params summarized: 1901

### issues
- R-hat for mu_position[2]: 1.022 > 1.01
- ESS for mu_position[2]: 274 < 400
- R-hat for mu_position[3]: 1.018 > 1.01
- ESS for mu_position[3]: 225 < 400
- ESS for mu_player[1]: 369 < 400
- R-hat for mu_player[7]: 1.012 > 1.01
- R-hat for mu_player[15]: 1.011 > 1.01
- R-hat for mu_player[74]: 1.010 > 1.01
- R-hat for mu_player[200]: 1.011 > 1.01
- R-hat for mu_player[218]: 1.010 > 1.01
- R-hat for mu_player[246]: 1.012 > 1.01
- R-hat for mu_player[277]: 1.010 > 1.01
- R-hat for mu_player[362]: 1.014 > 1.01
- R-hat for mu_player[426]: 1.010 > 1.01
- R-hat for sigma_position: 1.010 > 1.01
- R-hat for sigma_player: 1.010 > 1.01
- ESS for gamma_pos[1]: 370 < 400
- R-hat for gamma_pos[2]: 1.021 > 1.01
- ESS for gamma_pos[2]: 289 < 400
- R-hat for gamma_pos[3]: 1.016 > 1.01
- … +151 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 80.1%
- ✓ **bias_near_zero**: bias = -0.055
- ✓ **z_error_well_calibrated**: z-error mean=-0.20, sd=1.14
- ✓ **top_25_tier_accuracy**: top-25 overlap = 72.0%

## backtest metrics (STL)
- train: 2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: STL
- N players: 256
- empirical OOS SD: 0.217 STL/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 47.5%
- MAE: 0.234
- RMSE: 0.318
- bias: -0.055
- coverage 50%: 49.6%
- coverage 80%: 80.1%
- coverage 90%: 86.3%
- z-error: mean=-0.195 sd=1.137
- top-25 tier accuracy: 72.0%
- top-50 tier accuracy: 70.0%
