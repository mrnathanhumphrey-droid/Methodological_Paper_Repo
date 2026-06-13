# skill fit: backtest_PTS_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260429T035950Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 5291.8s (88.2 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0178
- min ESS: 204
- params summarized: 905

### issues
- R-hat for mu_player[1]: 1.011 > 1.01
- R-hat for mu_player[20]: 1.018 > 1.01
- R-hat for mu_player[51]: 1.015 > 1.01
- R-hat for mu_player[68]: 1.012 > 1.01
- R-hat for mu_player[94]: 1.011 > 1.01
- R-hat for mu_player[117]: 1.012 > 1.01
- R-hat for mu_player[131]: 1.014 > 1.01
- R-hat for mu_player[135]: 1.012 > 1.01
- R-hat for mu_player[173]: 1.017 > 1.01
- R-hat for mu_player[193]: 1.012 > 1.01
- R-hat for mu_player[200]: 1.010 > 1.01
- ESS for mu_player[200]: 393 < 400
- R-hat for sigma_position: 1.012 > 1.01
- ESS for sigma_position: 204 < 400
- R-hat for peak_age_pos[1]: 1.014 > 1.01
- R-hat for peak_age_pos[2]: 1.012 > 1.01
- R-hat for beta_age_pos[1]: 1.013 > 1.01
- R-hat for beta_age_pos[2]: 1.011 > 1.01
- R-hat for age_tilt_player_z[9]: 1.010 > 1.01
- R-hat for age_tilt_player_z[18]: 1.010 > 1.01
- … +43 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 84.6%
- ✓ **bias_near_zero**: bias = +0.592
- ✓ **z_error_well_calibrated**: z-error mean=+0.25, sd=0.96
- ✓ **top_25_tier_accuracy**: top-25 overlap = 72.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 195
- empirical OOS SD: 1.974 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 1.867
- RMSE: 2.343
- bias: +0.592
- coverage 50%: 50.8%
- coverage 80%: 84.6%
- coverage 90%: 90.8%
- z-error: mean=+0.251 sd=0.965
- top-25 tier accuracy: 72.0%
- top-50 tier accuracy: 82.0%
