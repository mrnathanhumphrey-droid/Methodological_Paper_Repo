# skill fit: backtest_FGA_phase4_v3_quadratic_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260429T180249Z`
- stan model: `hierarchical_aging_quadratic_v1.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 4247.5s (70.8 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0136
- min ESS: 259
- params summarized: 900

### issues
- ESS for peak_age_pos[1]: 364 < 400
- ESS for peak_age_pos[2]: 259 < 400
- R-hat for beta_age_pos[1]: 1.011 > 1.01
- ESS for beta_age_pos[1]: 384 < 400
- ESS for beta_age_pos[2]: 274 < 400
- R-hat for age_tilt_player_z[61]: 1.011 > 1.01
- R-hat for age_tilt_player[44]: 1.013 > 1.01
- R-hat for age_tilt_player[87]: 1.014 > 1.01
- R-hat for rate_per_36_at_27[67]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[108]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[125]: 1.010 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 75.9%
- ✓ **bias_near_zero**: bias = +0.254
- ✓ **z_error_well_calibrated**: z-error mean=+0.14, sd=1.15
- ✓ **top_25_tier_accuracy**: top-25 overlap = 68.0%

## backtest metrics (FGA)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 195
- empirical OOS SD: 1.401 FGA/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 1.541
- RMSE: 1.930
- bias: +0.254
- coverage 50%: 46.7%
- coverage 80%: 75.9%
- coverage 90%: 83.6%
- z-error: mean=+0.139 sd=1.152
- top-25 tier accuracy: 68.0%
- top-50 tier accuracy: 74.0%
