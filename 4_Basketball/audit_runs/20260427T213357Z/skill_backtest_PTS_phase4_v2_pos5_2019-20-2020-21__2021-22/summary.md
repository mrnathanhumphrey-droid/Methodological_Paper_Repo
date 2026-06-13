# skill fit: backtest_PTS_phase4_v2_pos5_2019-20-2020-21__2021-22

- run timestamp: `20260427T213357Z`
- stan model: `hierarchical_aging_pace_usage_v2.stan`
- observations: 21,122
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 1383.1s (23.1 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0733
- min ESS: 45
- params summarized: 933

### issues
- R-hat for mu_player[1]: 1.016 > 1.01
- ESS for mu_player[1]: 282 < 400
- R-hat for mu_player[2]: 1.018 > 1.01
- R-hat for mu_player[4]: 1.035 > 1.01
- ESS for mu_player[4]: 105 < 400
- R-hat for mu_player[14]: 1.011 > 1.01
- R-hat for mu_player[15]: 1.012 > 1.01
- ESS for mu_player[15]: 271 < 400
- R-hat for mu_player[17]: 1.014 > 1.01
- ESS for mu_player[33]: 266 < 400
- R-hat for mu_player[39]: 1.014 > 1.01
- R-hat for mu_player[71]: 1.011 > 1.01
- R-hat for mu_player[80]: 1.011 > 1.01
- R-hat for mu_player[100]: 1.012 > 1.01
- R-hat for mu_player[112]: 1.010 > 1.01
- R-hat for mu_player[120]: 1.010 > 1.01
- R-hat for mu_player[126]: 1.012 > 1.01
- R-hat for mu_player[131]: 1.012 > 1.01
- R-hat for mu_player[133]: 1.013 > 1.01
- R-hat for mu_player[141]: 1.011 > 1.01
- … +164 more

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 65.8%
- ✓ **bias_near_zero**: bias = +0.013
- ✗ **z_error_well_calibrated**: z-error mean=-0.04, sd=1.44
- ✓ **top_25_tier_accuracy**: top-25 overlap = 76.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21
- test: 2021-22
- mates_usage_stat: FGA
- N players: 193
- empirical OOS SD: 1.470 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 72.1%
- MAE: 2.168
- RMSE: 2.745
- bias: +0.013
- coverage 50%: 37.3%
- coverage 80%: 65.8%
- coverage 90%: 73.1%
- z-error: mean=-0.035 sd=1.443
- top-25 tier accuracy: 76.0%
- top-50 tier accuracy: 74.0%
