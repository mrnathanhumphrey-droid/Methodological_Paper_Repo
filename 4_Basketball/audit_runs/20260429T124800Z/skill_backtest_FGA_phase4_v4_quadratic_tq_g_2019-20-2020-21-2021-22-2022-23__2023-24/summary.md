# skill fit: backtest_FGA_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260429T124800Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 4163.3s (69.4 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0154
- min ESS: 285
- params summarized: 905

### issues
- R-hat for mu_player[8]: 1.014 > 1.01
- R-hat for mu_player[19]: 1.011 > 1.01
- R-hat for mu_player[71]: 1.012 > 1.01
- R-hat for mu_player[76]: 1.012 > 1.01
- R-hat for mu_player[145]: 1.013 > 1.01
- R-hat for peak_age_pos[1]: 1.012 > 1.01
- ESS for peak_age_pos[1]: 285 < 400
- R-hat for beta_age_pos[1]: 1.012 > 1.01
- ESS for beta_age_pos[1]: 358 < 400
- R-hat for age_tilt_player_z[67]: 1.015 > 1.01
- R-hat for age_tilt_player_z[105]: 1.014 > 1.01
- R-hat for age_tilt_player[19]: 1.014 > 1.01
- R-hat for rate_per_36_at_27[8]: 1.014 > 1.01
- R-hat for rate_per_36_at_27[19]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[71]: 1.012 > 1.01
- R-hat for rate_per_36_at_27[76]: 1.012 > 1.01
- R-hat for rate_per_36_at_27[145]: 1.014 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 79.0%
- ✓ **bias_near_zero**: bias = +0.275
- ✓ **z_error_well_calibrated**: z-error mean=+0.15, sd=1.15
- ✓ **top_25_tier_accuracy**: top-25 overlap = 68.0%

## backtest metrics (FGA)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 195
- empirical OOS SD: 1.401 FGA/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 1.561
- RMSE: 1.934
- bias: +0.275
- coverage 50%: 45.1%
- coverage 80%: 79.0%
- coverage 90%: 86.2%
- z-error: mean=+0.155 sd=1.153
- top-25 tier accuracy: 68.0%
- top-50 tier accuracy: 72.0%
