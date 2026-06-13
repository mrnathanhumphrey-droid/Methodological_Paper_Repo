# skill fit: backtest_PTS_phase4_v3_quadratic_hl10_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260428T135337Z`
- stan model: `hierarchical_aging_quadratic_v1.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 4135.8s (68.9 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0747
- min ESS: 37
- params summarized: 900

### issues
- R-hat for mu_player[1]: 1.049 > 1.01
- ESS for mu_player[1]: 57 < 400
- R-hat for mu_player[4]: 1.022 > 1.01
- ESS for mu_player[4]: 156 < 400
- R-hat for mu_player[8]: 1.011 > 1.01
- R-hat for mu_player[10]: 1.012 > 1.01
- R-hat for mu_player[14]: 1.014 > 1.01
- R-hat for mu_player[15]: 1.010 > 1.01
- ESS for mu_player[15]: 297 < 400
- R-hat for mu_player[26]: 1.014 > 1.01
- R-hat for mu_player[27]: 1.025 > 1.01
- ESS for mu_player[27]: 169 < 400
- R-hat for mu_player[30]: 1.013 > 1.01
- ESS for mu_player[30]: 240 < 400
- R-hat for mu_player[40]: 1.011 > 1.01
- R-hat for mu_player[44]: 1.013 > 1.01
- R-hat for mu_player[45]: 1.015 > 1.01
- R-hat for mu_player[157]: 1.012 > 1.01
- R-hat for mu_player[163]: 1.013 > 1.01
- R-hat for mu_player[166]: 1.011 > 1.01
- … +90 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 82.1%
- ✓ **bias_near_zero**: bias = +0.517
- ✓ **z_error_well_calibrated**: z-error mean=+0.22, sd=0.99
- ✓ **top_25_tier_accuracy**: top-25 overlap = 76.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 195
- empirical OOS SD: 1.974 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 1.894
- RMSE: 2.370
- bias: +0.517
- coverage 50%: 46.2%
- coverage 80%: 82.1%
- coverage 90%: 90.3%
- z-error: mean=+0.223 sd=0.992
- top-25 tier accuracy: 76.0%
- top-50 tier accuracy: 80.0%
