# skill fit: backtest_FGA_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260504T145949Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 64,126
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 6335.7s (105.6 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0162
- min ESS: 397
- params summarized: 905

### issues
- R-hat for mu_player[13]: 1.012 > 1.01
- R-hat for mu_player[72]: 1.016 > 1.01
- R-hat for mu_player[91]: 1.011 > 1.01
- R-hat for mu_player[120]: 1.010 > 1.01
- R-hat for mu_player[173]: 1.013 > 1.01
- R-hat for peak_age_pos[1]: 1.010 > 1.01
- ESS for peak_age_pos[1]: 397 < 400
- ESS for beta_age_pos[1]: 397 < 400
- R-hat for age_tilt_player_z[13]: 1.016 > 1.01
- R-hat for age_tilt_player_z[15]: 1.011 > 1.01
- R-hat for age_tilt_player_z[72]: 1.014 > 1.01
- R-hat for age_tilt_player_z[91]: 1.011 > 1.01
- R-hat for age_tilt_player_z[104]: 1.011 > 1.01
- R-hat for age_tilt_player_z[125]: 1.011 > 1.01
- R-hat for age_tilt_player_z[144]: 1.011 > 1.01
- R-hat for age_tilt_player_z[170]: 1.010 > 1.01
- R-hat for beta_young_on_tank: 1.010 > 1.01
- R-hat for age_tilt_player[72]: 1.013 > 1.01
- R-hat for age_tilt_player[139]: 1.012 > 1.01
- R-hat for rate_per_36_at_27[13]: 1.012 > 1.01
- … +5 more

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 95.5%
- ✓ **bias_near_zero**: bias = -0.542
- ✗ **z_error_well_calibrated**: z-error mean=-0.31, sd=0.56
- ✓ **top_25_tier_accuracy**: top-25 overlap = 76.0%

## backtest metrics (FGA)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FGA
- N players: 133
- empirical OOS SD: 1.577 FGA/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.836
- RMSE: 1.117
- bias: -0.542
- coverage 50%: 73.7%
- coverage 80%: 95.5%
- coverage 90%: 97.0%
- z-error: mean=-0.313 sd=0.558
- top-25 tier accuracy: 76.0%
- top-50 tier accuracy: 94.0%
