# skill fit: backtest_TOV_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260430T024953Z`
- stan model: `hierarchical_aging_quadratic_v3_pp_phi.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 2779.6s (46.3 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0569
- min ESS: 66
- params summarized: 910

### issues
- R-hat for mu_player[1]: 1.017 > 1.01
- ESS for mu_player[1]: 323 < 400
- R-hat for mu_player[3]: 1.016 > 1.01
- ESS for mu_player[3]: 292 < 400
- R-hat for mu_player[4]: 1.011 > 1.01
- R-hat for mu_player[5]: 1.010 > 1.01
- R-hat for mu_player[8]: 1.016 > 1.01
- ESS for mu_player[8]: 273 < 400
- ESS for mu_player[12]: 387 < 400
- R-hat for mu_player[14]: 1.010 > 1.01
- R-hat for mu_player[15]: 1.014 > 1.01
- ESS for mu_player[15]: 348 < 400
- ESS for mu_player[16]: 358 < 400
- R-hat for mu_player[17]: 1.018 > 1.01
- ESS for mu_player[17]: 206 < 400
- R-hat for mu_player[18]: 1.014 > 1.01
- R-hat for mu_player[30]: 1.011 > 1.01
- R-hat for mu_player[35]: 1.012 > 1.01
- R-hat for mu_player[37]: 1.010 > 1.01
- R-hat for mu_player[47]: 1.011 > 1.01
- … +270 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 80.5%
- ✓ **bias_near_zero**: bias = +0.113
- ✓ **z_error_well_calibrated**: z-error mean=+0.29, sd=1.04
- ✓ **top_25_tier_accuracy**: top-25 overlap = 68.0%

## backtest metrics (TOV)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: TOV
- N players: 195
- empirical OOS SD: 0.312 TOV/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 0.314
- RMSE: 0.403
- bias: +0.113
- coverage 50%: 49.2%
- coverage 80%: 80.5%
- coverage 90%: 84.6%
- z-error: mean=+0.291 sd=1.039
- top-25 tier accuracy: 68.0%
- top-50 tier accuracy: 78.0%
