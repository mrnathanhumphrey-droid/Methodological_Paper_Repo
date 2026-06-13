# skill fit: backtest_TOV_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260429T092552Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 2667.7s (44.5 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0535
- min ESS: 51
- params summarized: 905

### issues
- ESS for mu_player[1]: 393 < 400
- ESS for mu_player[5]: 383 < 400
- R-hat for mu_player[8]: 1.017 > 1.01
- R-hat for mu_player[14]: 1.010 > 1.01
- R-hat for mu_player[15]: 1.018 > 1.01
- ESS for mu_player[15]: 319 < 400
- R-hat for mu_player[17]: 1.012 > 1.01
- R-hat for mu_player[24]: 1.022 > 1.01
- ESS for mu_player[24]: 200 < 400
- R-hat for mu_player[33]: 1.016 > 1.01
- R-hat for mu_player[47]: 1.015 > 1.01
- R-hat for mu_player[118]: 1.011 > 1.01
- R-hat for mu_player[148]: 1.014 > 1.01
- ESS for mu_player[148]: 240 < 400
- R-hat for mu_player[165]: 1.011 > 1.01
- R-hat for mu_player[167]: 1.012 > 1.01
- R-hat for mu_player[177]: 1.010 > 1.01
- R-hat for mu_player[200]: 1.010 > 1.01
- R-hat for sigma_position: 1.013 > 1.01
- R-hat for beta_age_pos[1]: 1.017 > 1.01
- … +162 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 80.5%
- ✓ **bias_near_zero**: bias = +0.112
- ✓ **z_error_well_calibrated**: z-error mean=+0.29, sd=1.04
- ✓ **top_25_tier_accuracy**: top-25 overlap = 72.0%

## backtest metrics (TOV)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: TOV
- N players: 195
- empirical OOS SD: 0.312 TOV/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 0.313
- RMSE: 0.402
- bias: +0.112
- coverage 50%: 47.7%
- coverage 80%: 80.5%
- coverage 90%: 85.6%
- z-error: mean=+0.289 sd=1.035
- top-25 tier accuracy: 72.0%
- top-50 tier accuracy: 78.0%
