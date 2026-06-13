# skill fit: backtest_PTS_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22__2022-23

- run timestamp: `20260501T222551Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 34,052
- chains: 2 × (400 warmup + 400 sampling)
- wall time: 3604.0s (60.1 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0322
- min ESS: 53
- params summarized: 905

### issues
- ESS for mu_position[1]: 349 < 400
- ESS for mu_player[1]: 211 < 400
- R-hat for mu_player[3]: 1.012 > 1.01
- R-hat for mu_player[8]: 1.021 > 1.01
- R-hat for mu_player[16]: 1.010 > 1.01
- ESS for mu_player[16]: 209 < 400
- R-hat for mu_player[19]: 1.013 > 1.01
- R-hat for mu_player[26]: 1.013 > 1.01
- ESS for mu_player[33]: 368 < 400
- R-hat for mu_player[35]: 1.014 > 1.01
- ESS for mu_player[40]: 164 < 400
- R-hat for mu_player[53]: 1.011 > 1.01
- R-hat for mu_player[60]: 1.014 > 1.01
- ESS for mu_player[85]: 308 < 400
- R-hat for mu_player[86]: 1.018 > 1.01
- R-hat for mu_player[93]: 1.016 > 1.01
- R-hat for mu_player[95]: 1.014 > 1.01
- ESS for mu_player[116]: 398 < 400
- R-hat for mu_player[129]: 1.020 > 1.01
- R-hat for mu_player[141]: 1.011 > 1.01
- … +133 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 80.9%
- ✓ **bias_near_zero**: bias = -0.147
- ✓ **z_error_well_calibrated**: z-error mean=-0.07, sd=1.15
- ✓ **top_25_tier_accuracy**: top-25 overlap = 84.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22
- test: 2022-23
- mates_usage_stat: FGA
- N players: 199
- empirical OOS SD: 1.781 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 70.3%
- MAE: 1.864
- RMSE: 2.506
- bias: -0.147
- coverage 50%: 52.3%
- coverage 80%: 80.9%
- coverage 90%: 85.4%
- z-error: mean=-0.066 sd=1.152
- top-25 tier accuracy: 84.0%
- top-50 tier accuracy: 76.0%
