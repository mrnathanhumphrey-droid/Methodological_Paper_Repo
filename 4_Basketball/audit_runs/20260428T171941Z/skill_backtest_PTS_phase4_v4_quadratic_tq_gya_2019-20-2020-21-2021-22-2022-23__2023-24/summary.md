# skill fit: backtest_PTS_phase4_v4_quadratic_tq_gya_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260428T171941Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 5302.5s (88.4 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0173
- min ESS: 220
- params summarized: 905

### issues
- R-hat for mu_player[16]: 1.010 > 1.01
- R-hat for mu_player[64]: 1.011 > 1.01
- R-hat for mu_player[125]: 1.011 > 1.01
- R-hat for mu_player[150]: 1.012 > 1.01
- R-hat for mu_player[195]: 1.017 > 1.01
- ESS for sigma_position: 220 < 400
- R-hat for age_tilt_player_z[10]: 1.011 > 1.01
- R-hat for age_tilt_player_z[24]: 1.014 > 1.01
- R-hat for age_tilt_player_z[60]: 1.013 > 1.01
- R-hat for age_tilt_player_z[150]: 1.012 > 1.01
- R-hat for age_tilt_player_z[165]: 1.010 > 1.01
- R-hat for age_tilt_player_z[195]: 1.013 > 1.01
- R-hat for age_tilt_player[195]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[16]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[64]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[125]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[150]: 1.012 > 1.01
- R-hat for rate_per_36_at_27[165]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[188]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[195]: 1.017 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 84.6%
- ✓ **bias_near_zero**: bias = +0.604
- ✓ **z_error_well_calibrated**: z-error mean=+0.25, sd=0.97
- ✓ **top_25_tier_accuracy**: top-25 overlap = 72.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 195
- empirical OOS SD: 1.974 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 1.871
- RMSE: 2.361
- bias: +0.604
- coverage 50%: 49.7%
- coverage 80%: 84.6%
- coverage 90%: 90.8%
- z-error: mean=+0.252 sd=0.967
- top-25 tier accuracy: 72.0%
- top-50 tier accuracy: 82.0%
