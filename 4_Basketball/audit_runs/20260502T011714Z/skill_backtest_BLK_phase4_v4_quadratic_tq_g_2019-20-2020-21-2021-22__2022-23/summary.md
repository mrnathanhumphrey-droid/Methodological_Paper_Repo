# skill fit: backtest_BLK_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22__2022-23

- run timestamp: `20260502T011714Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 34,052
- chains: 2 × (400 warmup + 400 sampling)
- wall time: 1469.7s (24.5 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0606
- min ESS: 41
- params summarized: 905

### issues
- ESS for mu_position[1]: 318 < 400
- R-hat for mu_position[2]: 1.011 > 1.01
- ESS for mu_position[2]: 259 < 400
- R-hat for mu_player[1]: 1.034 > 1.01
- ESS for mu_player[1]: 55 < 400
- R-hat for mu_player[2]: 1.010 > 1.01
- ESS for mu_player[2]: 304 < 400
- ESS for mu_player[3]: 140 < 400
- R-hat for mu_player[4]: 1.019 > 1.01
- ESS for mu_player[4]: 113 < 400
- R-hat for mu_player[5]: 1.034 > 1.01
- ESS for mu_player[5]: 76 < 400
- R-hat for mu_player[6]: 1.026 > 1.01
- ESS for mu_player[6]: 126 < 400
- R-hat for mu_player[7]: 1.025 > 1.01
- ESS for mu_player[7]: 75 < 400
- R-hat for mu_player[11]: 1.014 > 1.01
- ESS for mu_player[11]: 238 < 400
- R-hat for mu_player[12]: 1.015 > 1.01
- ESS for mu_player[12]: 229 < 400
- … +814 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 83.9%
- ✓ **bias_near_zero**: bias = +0.035
- ✓ **z_error_well_calibrated**: z-error mean=+0.14, sd=1.04
- ✓ **top_25_tier_accuracy**: top-25 overlap = 84.0%

## backtest metrics (BLK)
- train: 2019-20,2020-21,2021-22
- test: 2022-23
- mates_usage_stat: BLK
- N players: 199
- empirical OOS SD: 0.168 BLK/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 70.3%
- MAE: 0.174
- RMSE: 0.260
- bias: +0.035
- coverage 50%: 55.3%
- coverage 80%: 83.9%
- coverage 90%: 88.4%
- z-error: mean=+0.141 sd=1.040
- top-25 tier accuracy: 84.0%
- top-50 tier accuracy: 82.0%
