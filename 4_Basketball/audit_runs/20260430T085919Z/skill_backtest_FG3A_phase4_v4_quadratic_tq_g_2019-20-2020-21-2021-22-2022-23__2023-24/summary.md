# skill fit: backtest_FG3A_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260430T085919Z`
- stan model: `hierarchical_aging_quadratic_v3_pp_phi.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 5699.7s (95.0 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0179
- min ESS: 240
- params summarized: 910

### issues
- R-hat for mu_player[44]: 1.012 > 1.01
- R-hat for mu_player[110]: 1.012 > 1.01
- R-hat for peak_age_pos[2]: 1.018 > 1.01
- ESS for peak_age_pos[2]: 240 < 400
- R-hat for gamma_pos[1]: 1.014 > 1.01
- R-hat for beta_age_pos[1]: 1.011 > 1.01
- ESS for beta_age_pos[2]: 364 < 400
- R-hat for age_tilt_player_z[129]: 1.013 > 1.01
- R-hat for age_tilt_player[80]: 1.010 > 1.01
- R-hat for age_tilt_player[124]: 1.012 > 1.01
- R-hat for age_tilt_player[129]: 1.010 > 1.01
- R-hat for age_tilt_player[193]: 1.014 > 1.01
- R-hat for rate_per_36_at_27[44]: 1.012 > 1.01
- R-hat for rate_per_36_at_27[110]: 1.012 > 1.01
- R-hat for age_curve_position[1,15]: 1.012 > 1.01
- R-hat for age_curve_position[1,16]: 1.013 > 1.01
- R-hat for age_curve_position[1,17]: 1.014 > 1.01
- R-hat for age_curve_position[1,18]: 1.015 > 1.01
- R-hat for age_curve_position[1,19]: 1.016 > 1.01
- R-hat for age_curve_position[1,20]: 1.016 > 1.01
- … +4 more

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 75.4%
- ✓ **bias_near_zero**: bias = +0.114
- ✓ **z_error_well_calibrated**: z-error mean=+0.05, sd=1.19
- ✗ **top_25_tier_accuracy**: top-25 overlap = 40.0%

## backtest metrics (FG3A)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FG3A
- N players: 195
- empirical OOS SD: 0.844 FG3A/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 1.032
- RMSE: 1.345
- bias: +0.114
- coverage 50%: 42.1%
- coverage 80%: 75.4%
- coverage 90%: 82.6%
- z-error: mean=+0.046 sd=1.187
- top-25 tier accuracy: 40.0%
- top-50 tier accuracy: 72.0%
