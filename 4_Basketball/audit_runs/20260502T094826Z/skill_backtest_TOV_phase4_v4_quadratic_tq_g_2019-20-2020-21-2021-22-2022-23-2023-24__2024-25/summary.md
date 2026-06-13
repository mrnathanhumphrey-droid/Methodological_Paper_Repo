# skill fit: backtest_TOV_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24__2024-25

- run timestamp: `20260502T094826Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 53,237
- chains: 2 × (400 warmup + 400 sampling)
- wall time: 3160.7s (52.7 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0545
- min ESS: 30
- params summarized: 905

### issues
- ESS for mu_league: 320 < 400
- ESS for mu_position[1]: 362 < 400
- ESS for mu_position[2]: 280 < 400
- ESS for mu_position[3]: 345 < 400
- ESS for mu_player[1]: 79 < 400
- R-hat for mu_player[2]: 1.011 > 1.01
- R-hat for mu_player[6]: 1.027 > 1.01
- ESS for mu_player[11]: 333 < 400
- ESS for mu_player[13]: 133 < 400
- ESS for mu_player[15]: 348 < 400
- ESS for mu_player[16]: 342 < 400
- ESS for mu_player[17]: 339 < 400
- R-hat for mu_player[21]: 1.012 > 1.01
- ESS for mu_player[21]: 209 < 400
- ESS for mu_player[23]: 222 < 400
- ESS for mu_player[24]: 380 < 400
- ESS for mu_player[28]: 270 < 400
- R-hat for mu_player[30]: 1.019 > 1.01
- ESS for mu_player[30]: 123 < 400
- ESS for mu_player[32]: 357 < 400
- … +399 more

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 92.4%
- ✓ **bias_near_zero**: bias = -0.088
- ✓ **z_error_well_calibrated**: z-error mean=-0.21, sd=1.07
- ✓ **top_25_tier_accuracy**: top-25 overlap = 72.0%

## backtest metrics (TOV)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24
- test: 2024-25
- mates_usage_stat: TOV
- N players: 119
- empirical OOS SD: 0.337 TOV/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.1%
- MAE: 0.311
- RMSE: 0.444
- bias: -0.088
- coverage 50%: 54.6%
- coverage 80%: 92.4%
- coverage 90%: 93.3%
- z-error: mean=-0.207 sd=1.067
- top-25 tier accuracy: 72.0%
- top-50 tier accuracy: 90.0%
