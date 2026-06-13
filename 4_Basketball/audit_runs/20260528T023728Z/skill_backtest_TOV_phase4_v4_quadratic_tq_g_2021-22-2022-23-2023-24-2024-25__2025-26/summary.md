# skill fit: backtest_TOV_phase4_v4_quadratic_tq_g_2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260528T023728Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 85,702
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 6660.2s (111.0 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0722
- min ESS: 52
- params summarized: 1901

### issues
- ESS for mu_position[2]: 397 < 400
- R-hat for mu_player[1]: 1.014 > 1.01
- ESS for mu_player[1]: 256 < 400
- R-hat for mu_player[14]: 1.015 > 1.01
- R-hat for mu_player[20]: 1.021 > 1.01
- ESS for mu_player[20]: 204 < 400
- R-hat for mu_player[34]: 1.018 > 1.01
- ESS for mu_player[34]: 232 < 400
- R-hat for mu_player[36]: 1.010 > 1.01
- R-hat for mu_player[57]: 1.010 > 1.01
- R-hat for mu_player[91]: 1.014 > 1.01
- R-hat for mu_player[127]: 1.013 > 1.01
- R-hat for mu_player[186]: 1.010 > 1.01
- R-hat for mu_player[215]: 1.011 > 1.01
- R-hat for mu_player[247]: 1.013 > 1.01
- R-hat for mu_player[260]: 1.013 > 1.01
- R-hat for mu_player[283]: 1.011 > 1.01
- R-hat for mu_player[317]: 1.013 > 1.01
- R-hat for mu_player[340]: 1.012 > 1.01
- R-hat for mu_player[356]: 1.011 > 1.01
- … +283 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 76.2%
- ✓ **bias_near_zero**: bias = -0.092
- ✓ **z_error_well_calibrated**: z-error mean=-0.26, sd=1.23
- ✓ **top_25_tier_accuracy**: top-25 overlap = 52.0%

## backtest metrics (TOV)
- train: 2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: TOV
- N players: 256
- empirical OOS SD: 0.317 TOV/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 47.5%
- MAE: 0.363
- RMSE: 0.475
- bias: -0.092
- coverage 50%: 46.9%
- coverage 80%: 76.2%
- coverage 90%: 81.2%
- z-error: mean=-0.261 sd=1.230
- top-25 tier accuracy: 52.0%
- top-50 tier accuracy: 68.0%
