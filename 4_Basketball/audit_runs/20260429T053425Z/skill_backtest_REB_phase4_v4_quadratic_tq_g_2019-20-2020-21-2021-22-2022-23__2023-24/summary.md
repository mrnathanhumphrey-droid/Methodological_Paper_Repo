# skill fit: backtest_REB_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260429T053425Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3217.0s (53.6 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0142
- min ESS: 285
- params summarized: 905

### issues
- R-hat for mu_player[27]: 1.011 > 1.01
- R-hat for mu_player[55]: 1.014 > 1.01
- R-hat for sigma_age_player: 1.011 > 1.01
- ESS for sigma_age_player: 285 < 400
- R-hat for age_tilt_player_z[31]: 1.012 > 1.01
- R-hat for age_tilt_player_z[46]: 1.012 > 1.01
- R-hat for age_tilt_player_z[94]: 1.010 > 1.01
- R-hat for age_tilt_player_z[151]: 1.012 > 1.01
- R-hat for age_tilt_player_z[185]: 1.011 > 1.01
- R-hat for beta_young_on_tank: 1.011 > 1.01
- R-hat for age_tilt_player[46]: 1.010 > 1.01
- R-hat for age_tilt_player[70]: 1.013 > 1.01
- R-hat for age_tilt_player[151]: 1.012 > 1.01
- R-hat for rate_per_36_at_27[27]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[55]: 1.014 > 1.01
- R-hat for young_on_tank_lift: 1.011 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 84.1%
- ✓ **bias_near_zero**: bias = +0.036
- ✓ **z_error_well_calibrated**: z-error mean=+0.04, sd=0.97
- ✓ **top_25_tier_accuracy**: top-25 overlap = 84.0%

## backtest metrics (REB)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: REB
- N players: 195
- empirical OOS SD: 0.670 REB/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 0.631
- RMSE: 0.815
- bias: +0.036
- coverage 50%: 53.8%
- coverage 80%: 84.1%
- coverage 90%: 89.2%
- z-error: mean=+0.040 sd=0.975
- top-25 tier accuracy: 84.0%
- top-50 tier accuracy: 92.0%
