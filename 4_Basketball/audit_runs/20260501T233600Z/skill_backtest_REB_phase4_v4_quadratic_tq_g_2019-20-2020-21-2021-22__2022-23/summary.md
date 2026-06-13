# skill fit: backtest_REB_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22__2022-23

- run timestamp: `20260501T233600Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 34,052
- chains: 2 × (400 warmup + 400 sampling)
- wall time: 2634.1s (43.9 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0482
- min ESS: 45
- params summarized: 905

### issues
- R-hat for mu_player[1]: 1.017 > 1.01
- ESS for mu_player[1]: 270 < 400
- ESS for mu_player[2]: 291 < 400
- ESS for mu_player[3]: 310 < 400
- ESS for mu_player[5]: 348 < 400
- ESS for mu_player[6]: 387 < 400
- ESS for mu_player[7]: 281 < 400
- ESS for mu_player[8]: 210 < 400
- R-hat for mu_player[9]: 1.020 > 1.01
- ESS for mu_player[9]: 139 < 400
- R-hat for mu_player[10]: 1.014 > 1.01
- ESS for mu_player[10]: 268 < 400
- R-hat for mu_player[11]: 1.016 > 1.01
- ESS for mu_player[11]: 221 < 400
- ESS for mu_player[12]: 330 < 400
- R-hat for mu_player[14]: 1.020 > 1.01
- ESS for mu_player[14]: 125 < 400
- ESS for mu_player[15]: 265 < 400
- ESS for mu_player[17]: 279 < 400
- R-hat for mu_player[18]: 1.020 > 1.01
- … +418 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 72.9%
- ✓ **bias_near_zero**: bias = +0.164
- ✓ **z_error_well_calibrated**: z-error mean=+0.23, sd=1.30
- ✓ **top_25_tier_accuracy**: top-25 overlap = 80.0%

## backtest metrics (REB)
- train: 2019-20,2020-21,2021-22
- test: 2022-23
- mates_usage_stat: REB
- N players: 199
- empirical OOS SD: 0.587 REB/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 70.3%
- MAE: 0.747
- RMSE: 1.002
- bias: +0.164
- coverage 50%: 42.7%
- coverage 80%: 72.9%
- coverage 90%: 79.9%
- z-error: mean=+0.231 sd=1.297
- top-25 tier accuracy: 80.0%
- top-50 tier accuracy: 86.0%
