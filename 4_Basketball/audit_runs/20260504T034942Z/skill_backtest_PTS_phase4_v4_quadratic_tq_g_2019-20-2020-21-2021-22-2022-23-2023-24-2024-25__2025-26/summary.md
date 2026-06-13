# skill fit: backtest_PTS_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260504T034942Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 64,126
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 8072.7s (134.5 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0367
- min ESS: 225
- params summarized: 905

### issues
- R-hat for mu_player[30]: 1.012 > 1.01
- R-hat for mu_player[70]: 1.011 > 1.01
- R-hat for mu_player[116]: 1.014 > 1.01
- R-hat for mu_player[135]: 1.010 > 1.01
- R-hat for mu_player[162]: 1.011 > 1.01
- R-hat for sigma_position: 1.037 > 1.01
- ESS for sigma_position: 225 < 400
- R-hat for peak_age_pos[1]: 1.014 > 1.01
- R-hat for peak_age_pos[2]: 1.014 > 1.01
- R-hat for beta_age_pos[1]: 1.015 > 1.01
- R-hat for beta_age_pos[2]: 1.016 > 1.01
- ESS for beta_age_pos[2]: 353 < 400
- R-hat for age_tilt_player_z[75]: 1.014 > 1.01
- R-hat for age_tilt_player_z[77]: 1.011 > 1.01
- R-hat for age_tilt_player_z[78]: 1.010 > 1.01
- R-hat for age_tilt_player[60]: 1.010 > 1.01
- R-hat for age_tilt_player[62]: 1.010 > 1.01
- R-hat for age_tilt_player[170]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[30]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[70]: 1.010 > 1.01
- … +9 more

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 95.5%
- ✓ **bias_near_zero**: bias = -0.749
- ✗ **z_error_well_calibrated**: z-error mean=-0.30, sd=0.54
- ✓ **top_25_tier_accuracy**: top-25 overlap = 88.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FGA
- N players: 133
- empirical OOS SD: 2.239 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 1.239
- RMSE: 1.568
- bias: -0.749
- coverage 50%: 72.9%
- coverage 80%: 95.5%
- coverage 90%: 98.5%
- z-error: mean=-0.297 sd=0.539
- top-25 tier accuracy: 88.0%
- top-50 tier accuracy: 92.0%
