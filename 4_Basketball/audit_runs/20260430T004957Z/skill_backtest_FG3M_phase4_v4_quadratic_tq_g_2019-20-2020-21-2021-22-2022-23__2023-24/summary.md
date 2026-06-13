# skill fit: backtest_FG3M_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260430T004957Z`
- stan model: `hierarchical_aging_quadratic_v3_pp_phi.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 2828.0s (47.1 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0717
- min ESS: 79
- params summarized: 910

### issues
- R-hat for mu_league: 1.015 > 1.01
- R-hat for mu_position[2]: 1.011 > 1.01
- R-hat for mu_position[3]: 1.016 > 1.01
- R-hat for mu_player[1]: 1.013 > 1.01
- R-hat for mu_player[3]: 1.016 > 1.01
- ESS for mu_player[3]: 299 < 400
- R-hat for mu_player[5]: 1.017 > 1.01
- R-hat for mu_player[9]: 1.034 > 1.01
- R-hat for mu_player[11]: 1.013 > 1.01
- R-hat for mu_player[12]: 1.012 > 1.01
- R-hat for mu_player[14]: 1.024 > 1.01
- ESS for mu_player[14]: 227 < 400
- R-hat for mu_player[21]: 1.016 > 1.01
- R-hat for mu_player[25]: 1.020 > 1.01
- ESS for mu_player[25]: 200 < 400
- R-hat for mu_player[26]: 1.010 > 1.01
- R-hat for mu_player[35]: 1.012 > 1.01
- R-hat for mu_player[36]: 1.012 > 1.01
- R-hat for mu_player[53]: 1.012 > 1.01
- ESS for mu_player[53]: 380 < 400
- … +294 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 82.1%
- ✓ **bias_near_zero**: bias = +0.002
- ✓ **z_error_well_calibrated**: z-error mean=-0.02, sd=1.02
- ✓ **top_25_tier_accuracy**: top-25 overlap = 56.0%

## backtest metrics (FG3M)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FG3A
- N players: 195
- empirical OOS SD: 0.352 FG3M/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 0.357
- RMSE: 0.464
- bias: +0.002
- coverage 50%: 56.9%
- coverage 80%: 82.1%
- coverage 90%: 88.2%
- z-error: mean=-0.019 sd=1.018
- top-25 tier accuracy: 56.0%
- top-50 tier accuracy: 76.0%
