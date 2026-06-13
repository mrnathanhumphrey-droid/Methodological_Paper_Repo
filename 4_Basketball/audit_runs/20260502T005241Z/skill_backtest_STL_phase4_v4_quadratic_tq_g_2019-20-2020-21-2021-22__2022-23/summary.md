# skill fit: backtest_STL_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22__2022-23

- run timestamp: `20260502T005241Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 34,052
- chains: 2 × (400 warmup + 400 sampling)
- wall time: 1730.4s (28.8 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0248
- min ESS: 73
- params summarized: 905

### issues
- ESS for mu_league: 315 < 400
- ESS for mu_position[1]: 316 < 400
- ESS for mu_position[3]: 145 < 400
- ESS for mu_player[2]: 323 < 400
- ESS for mu_player[5]: 371 < 400
- R-hat for mu_player[18]: 1.012 > 1.01
- R-hat for mu_player[27]: 1.012 > 1.01
- R-hat for mu_player[46]: 1.011 > 1.01
- R-hat for mu_player[49]: 1.017 > 1.01
- R-hat for mu_player[78]: 1.012 > 1.01
- ESS for mu_player[108]: 360 < 400
- R-hat for mu_player[121]: 1.014 > 1.01
- ESS for mu_player[126]: 328 < 400
- R-hat for mu_player[132]: 1.012 > 1.01
- R-hat for mu_player[143]: 1.011 > 1.01
- R-hat for mu_player[157]: 1.012 > 1.01
- R-hat for mu_player[168]: 1.010 > 1.01
- ESS for mu_player[169]: 352 < 400
- ESS for mu_player[181]: 324 < 400
- ESS for sigma_position: 249 < 400
- … +139 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 86.9%
- ✓ **bias_near_zero**: bias = +0.040
- ✓ **z_error_well_calibrated**: z-error mean=+0.18, sd=0.91
- ✓ **top_25_tier_accuracy**: top-25 overlap = 72.0%

## backtest metrics (STL)
- train: 2019-20,2020-21,2021-22
- test: 2022-23
- mates_usage_stat: STL
- N players: 199
- empirical OOS SD: 0.176 STL/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 70.3%
- MAE: 0.172
- RMSE: 0.213
- bias: +0.040
- coverage 50%: 52.3%
- coverage 80%: 86.9%
- coverage 90%: 91.5%
- z-error: mean=+0.182 sd=0.915
- top-25 tier accuracy: 72.0%
- top-50 tier accuracy: 70.0%
