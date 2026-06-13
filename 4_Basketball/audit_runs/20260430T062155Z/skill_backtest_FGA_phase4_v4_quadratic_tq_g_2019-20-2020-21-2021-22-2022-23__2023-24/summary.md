# skill fit: backtest_FGA_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260430T062155Z`
- stan model: `hierarchical_aging_quadratic_v3_pp_phi.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 5391.6s (89.9 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0311
- min ESS: 200
- params summarized: 910

### issues
- R-hat for mu_player[11]: 1.011 > 1.01
- R-hat for mu_player[46]: 1.015 > 1.01
- R-hat for mu_player[57]: 1.011 > 1.01
- R-hat for mu_player[65]: 1.019 > 1.01
- R-hat for mu_player[74]: 1.010 > 1.01
- R-hat for mu_player[93]: 1.011 > 1.01
- R-hat for mu_player[110]: 1.011 > 1.01
- R-hat for mu_player[124]: 1.011 > 1.01
- R-hat for mu_player[175]: 1.011 > 1.01
- ESS for sigma_position: 391 < 400
- R-hat for peak_age_pos[1]: 1.024 > 1.01
- ESS for peak_age_pos[1]: 200 < 400
- R-hat for peak_age_pos[2]: 1.031 > 1.01
- ESS for peak_age_pos[2]: 289 < 400
- R-hat for beta_age_pos[1]: 1.024 > 1.01
- ESS for beta_age_pos[1]: 207 < 400
- R-hat for beta_age_pos[2]: 1.028 > 1.01
- ESS for beta_age_pos[2]: 263 < 400
- R-hat for age_tilt_player_z[39]: 1.012 > 1.01
- R-hat for age_tilt_player_z[46]: 1.011 > 1.01
- … +18 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 78.5%
- ✓ **bias_near_zero**: bias = +0.278
- ✓ **z_error_well_calibrated**: z-error mean=+0.16, sd=1.14
- ✓ **top_25_tier_accuracy**: top-25 overlap = 68.0%

## backtest metrics (FGA)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 195
- empirical OOS SD: 1.401 FGA/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 1.556
- RMSE: 1.927
- bias: +0.278
- coverage 50%: 44.1%
- coverage 80%: 78.5%
- coverage 90%: 85.6%
- z-error: mean=+0.156 sd=1.144
- top-25 tier accuracy: 68.0%
- top-50 tier accuracy: 74.0%
