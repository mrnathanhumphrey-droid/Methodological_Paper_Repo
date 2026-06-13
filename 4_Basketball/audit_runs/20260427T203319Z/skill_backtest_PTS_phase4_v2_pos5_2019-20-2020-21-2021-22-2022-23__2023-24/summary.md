# skill fit: backtest_PTS_phase4_v2_pos5_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260427T203319Z`
- stan model: `hierarchical_aging_pace_usage_v2.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3044.5s (50.7 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0264
- min ESS: 146
- params summarized: 945

### issues
- ESS for mu_position[1]: 395 < 400
- ESS for mu_player[6]: 339 < 400
- R-hat for mu_player[12]: 1.015 > 1.01
- ESS for mu_player[12]: 345 < 400
- R-hat for mu_player[15]: 1.026 > 1.01
- R-hat for mu_player[28]: 1.012 > 1.01
- ESS for mu_player[28]: 309 < 400
- R-hat for mu_player[29]: 1.011 > 1.01
- R-hat for mu_player[30]: 1.011 > 1.01
- R-hat for mu_player[32]: 1.011 > 1.01
- R-hat for mu_player[43]: 1.013 > 1.01
- R-hat for mu_player[44]: 1.012 > 1.01
- ESS for mu_player[44]: 339 < 400
- R-hat for mu_player[47]: 1.011 > 1.01
- R-hat for mu_player[51]: 1.013 > 1.01
- R-hat for mu_player[62]: 1.010 > 1.01
- ESS for mu_player[70]: 334 < 400
- R-hat for mu_player[81]: 1.016 > 1.01
- R-hat for mu_player[93]: 1.018 > 1.01
- R-hat for mu_player[94]: 1.011 > 1.01
- … +166 more

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 82.1%
- ✓ **bias_near_zero**: bias = +0.786
- ✗ **z_error_well_calibrated**: z-error mean=+0.32, sd=1.00
- ✓ **top_25_tier_accuracy**: top-25 overlap = 72.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 195
- empirical OOS SD: 1.974 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 2.050
- RMSE: 2.545
- bias: +0.786
- coverage 50%: 41.5%
- coverage 80%: 82.1%
- coverage 90%: 88.2%
- z-error: mean=+0.319 sd=1.005
- top-25 tier accuracy: 72.0%
- top-50 tier accuracy: 80.0%
