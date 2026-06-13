# skill fit: backtest_TOV_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22__2022-23

- run timestamp: `20260502T015232Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 34,052
- chains: 2 × (400 warmup + 400 sampling)
- wall time: 2114.1s (35.2 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0406
- min ESS: 38
- params summarized: 905

### issues
- ESS for mu_league: 366 < 400
- ESS for mu_position[2]: 318 < 400
- ESS for mu_position[3]: 122 < 400
- ESS for mu_player[1]: 254 < 400
- ESS for mu_player[2]: 276 < 400
- ESS for mu_player[3]: 340 < 400
- ESS for mu_player[4]: 308 < 400
- ESS for mu_player[5]: 385 < 400
- ESS for mu_player[6]: 330 < 400
- ESS for mu_player[7]: 311 < 400
- ESS for mu_player[8]: 217 < 400
- R-hat for mu_player[9]: 1.011 > 1.01
- ESS for mu_player[14]: 233 < 400
- ESS for mu_player[15]: 233 < 400
- ESS for mu_player[16]: 375 < 400
- ESS for mu_player[19]: 336 < 400
- ESS for mu_player[22]: 377 < 400
- ESS for mu_player[26]: 343 < 400
- ESS for mu_player[27]: 352 < 400
- ESS for mu_player[33]: 294 < 400
- … +427 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 81.9%
- ✓ **bias_near_zero**: bias = -0.030
- ✓ **z_error_well_calibrated**: z-error mean=-0.10, sd=1.11
- ✓ **top_25_tier_accuracy**: top-25 overlap = 68.0%

## backtest metrics (TOV)
- train: 2019-20,2020-21,2021-22
- test: 2022-23
- mates_usage_stat: TOV
- N players: 199
- empirical OOS SD: 0.287 TOV/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 70.3%
- MAE: 0.311
- RMSE: 0.403
- bias: -0.030
- coverage 50%: 48.2%
- coverage 80%: 81.9%
- coverage 90%: 84.9%
- z-error: mean=-0.098 sd=1.108
- top-25 tier accuracy: 68.0%
- top-50 tier accuracy: 84.0%
