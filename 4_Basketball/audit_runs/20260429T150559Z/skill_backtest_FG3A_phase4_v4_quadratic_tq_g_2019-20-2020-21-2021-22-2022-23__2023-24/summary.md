# skill fit: backtest_FG3A_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260429T150559Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 5197.8s (86.6 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0283
- min ESS: 208
- params summarized: 905

### issues
- R-hat for mu_player[44]: 1.011 > 1.01
- ESS for mu_player[44]: 378 < 400
- R-hat for mu_player[52]: 1.013 > 1.01
- R-hat for mu_player[56]: 1.011 > 1.01
- ESS for mu_player[56]: 350 < 400
- R-hat for mu_player[73]: 1.013 > 1.01
- ESS for mu_player[81]: 390 < 400
- ESS for mu_player[110]: 385 < 400
- R-hat for mu_player[134]: 1.011 > 1.01
- ESS for mu_player[151]: 369 < 400
- R-hat for mu_player[164]: 1.010 > 1.01
- R-hat for peak_age_pos[2]: 1.012 > 1.01
- ESS for peak_age_pos[2]: 208 < 400
- R-hat for gamma_pos[1]: 1.028 > 1.01
- ESS for gamma_pos[1]: 305 < 400
- R-hat for beta_age_pos[2]: 1.015 > 1.01
- ESS for beta_age_pos[2]: 259 < 400
- R-hat for age_tilt_player_z[3]: 1.013 > 1.01
- R-hat for age_tilt_player_z[190]: 1.013 > 1.01
- R-hat for age_tilt_player[3]: 1.011 > 1.01
- … +26 more

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 74.9%
- ✓ **bias_near_zero**: bias = +0.111
- ✓ **z_error_well_calibrated**: z-error mean=+0.04, sd=1.20
- ✗ **top_25_tier_accuracy**: top-25 overlap = 40.0%

## backtest metrics (FG3A)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FG3A
- N players: 195
- empirical OOS SD: 0.844 FG3A/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 1.036
- RMSE: 1.350
- bias: +0.111
- coverage 50%: 42.1%
- coverage 80%: 74.9%
- coverage 90%: 82.1%
- z-error: mean=+0.043 sd=1.196
- top-25 tier accuracy: 40.0%
- top-50 tier accuracy: 72.0%
