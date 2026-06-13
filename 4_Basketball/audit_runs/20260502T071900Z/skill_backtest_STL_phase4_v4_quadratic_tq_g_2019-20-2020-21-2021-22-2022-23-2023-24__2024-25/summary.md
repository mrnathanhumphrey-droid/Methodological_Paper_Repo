# skill fit: backtest_STL_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24__2024-25

- run timestamp: `20260502T071900Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 53,237
- chains: 2 × (400 warmup + 400 sampling)
- wall time: 2994.2s (49.9 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0328
- min ESS: 100
- params summarized: 905

### issues
- ESS for mu_position[1]: 195 < 400
- ESS for mu_position[2]: 306 < 400
- ESS for mu_position[3]: 255 < 400
- R-hat for mu_player[3]: 1.013 > 1.01
- ESS for mu_player[6]: 378 < 400
- ESS for mu_player[12]: 327 < 400
- ESS for mu_player[17]: 379 < 400
- ESS for mu_player[19]: 369 < 400
- R-hat for mu_player[32]: 1.010 > 1.01
- R-hat for mu_player[36]: 1.012 > 1.01
- ESS for mu_player[37]: 370 < 400
- ESS for mu_player[38]: 393 < 400
- R-hat for mu_player[46]: 1.013 > 1.01
- R-hat for mu_player[59]: 1.011 > 1.01
- R-hat for mu_player[66]: 1.010 > 1.01
- R-hat for mu_player[93]: 1.013 > 1.01
- R-hat for mu_player[99]: 1.011 > 1.01
- R-hat for mu_player[116]: 1.025 > 1.01
- R-hat for mu_player[125]: 1.010 > 1.01
- R-hat for mu_player[153]: 1.014 > 1.01
- … +280 more

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 79.8%
- ✓ **bias_near_zero**: bias = -0.113
- ✗ **z_error_well_calibrated**: z-error mean=-0.48, sd=0.99
- ✓ **top_25_tier_accuracy**: top-25 overlap = 76.0%

## backtest metrics (STL)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24
- test: 2024-25
- mates_usage_stat: STL
- N players: 119
- empirical OOS SD: 0.198 STL/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.1%
- MAE: 0.204
- RMSE: 0.260
- bias: -0.113
- coverage 50%: 48.7%
- coverage 80%: 79.8%
- coverage 90%: 88.2%
- z-error: mean=-0.475 sd=0.995
- top-25 tier accuracy: 76.0%
- top-50 tier accuracy: 82.0%
