# skill fit: backtest_PTS_phase4_v3_quadratic_2019-20-2020-21__2021-22

- run timestamp: `20260428T034051Z`
- stan model: `hierarchical_aging_quadratic_v1.stan`
- observations: 21,122
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 1589.1s (26.5 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0341
- min ESS: 60
- params summarized: 888

### issues
- ESS for mu_player[1]: 184 < 400
- R-hat for mu_player[4]: 1.021 > 1.01
- ESS for mu_player[4]: 119 < 400
- ESS for mu_player[15]: 226 < 400
- R-hat for mu_player[26]: 1.013 > 1.01
- R-hat for mu_player[47]: 1.010 > 1.01
- R-hat for mu_player[91]: 1.012 > 1.01
- R-hat for mu_player[137]: 1.018 > 1.01
- ESS for mu_player[146]: 288 < 400
- R-hat for mu_player[148]: 1.013 > 1.01
- ESS for mu_player[148]: 156 < 400
- ESS for mu_player[157]: 384 < 400
- R-hat for mu_player[173]: 1.011 > 1.01
- ESS for mu_player[177]: 309 < 400
- ESS for mu_player[178]: 389 < 400
- ESS for sigma_position: 353 < 400
- R-hat for peak_age_pos[2]: 1.012 > 1.01
- ESS for gamma_pos[1]: 394 < 400
- R-hat for gamma_pos[2]: 1.010 > 1.01
- R-hat for sigma_age_player: 1.034 > 1.01
- … +77 more

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 66.3%
- ✓ **bias_near_zero**: bias = +0.053
- ✓ **z_error_well_calibrated**: z-error mean=-0.01, sd=1.38
- ✓ **top_25_tier_accuracy**: top-25 overlap = 76.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21
- test: 2021-22
- mates_usage_stat: FGA
- N players: 193
- empirical OOS SD: 1.470 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 72.1%
- MAE: 2.105
- RMSE: 2.634
- bias: +0.053
- coverage 50%: 35.8%
- coverage 80%: 66.3%
- coverage 90%: 76.7%
- z-error: mean=-0.011 sd=1.379
- top-25 tier accuracy: 76.0%
- top-50 tier accuracy: 72.0%
