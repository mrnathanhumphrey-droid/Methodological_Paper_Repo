# skill fit: backtest_AST_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22__2022-23

- run timestamp: `20260502T002346Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 34,052
- chains: 2 × (400 warmup + 400 sampling)
- wall time: 2862.0s (47.7 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0271
- min ESS: 182
- params summarized: 905

### issues
- R-hat for mu_player[19]: 1.011 > 1.01
- R-hat for mu_player[161]: 1.011 > 1.01
- R-hat for beta_age_pos[3]: 1.013 > 1.01
- ESS for sigma_age_player: 182 < 400
- R-hat for age_tilt_player_z[12]: 1.015 > 1.01
- R-hat for age_tilt_player_z[36]: 1.011 > 1.01
- R-hat for age_tilt_player_z[83]: 1.011 > 1.01
- R-hat for age_tilt_player_z[89]: 1.010 > 1.01
- R-hat for age_tilt_player_z[90]: 1.026 > 1.01
- R-hat for age_tilt_player_z[152]: 1.014 > 1.01
- R-hat for age_tilt_player_z[155]: 1.012 > 1.01
- R-hat for age_tilt_player_z[168]: 1.011 > 1.01
- R-hat for age_tilt_player[30]: 1.014 > 1.01
- R-hat for age_tilt_player[62]: 1.013 > 1.01
- R-hat for age_tilt_player[90]: 1.027 > 1.01
- R-hat for age_tilt_player[128]: 1.010 > 1.01
- R-hat for age_tilt_player[147]: 1.011 > 1.01
- R-hat for age_tilt_player[152]: 1.011 > 1.01
- R-hat for age_tilt_player[155]: 1.010 > 1.01
- R-hat for age_tilt_player[170]: 1.010 > 1.01
- … +3 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 80.4%
- ✓ **bias_near_zero**: bias = +0.053
- ✓ **z_error_well_calibrated**: z-error mean=+0.06, sd=1.15
- ✓ **top_25_tier_accuracy**: top-25 overlap = 84.0%

## backtest metrics (AST)
- train: 2019-20,2020-21,2021-22
- test: 2022-23
- mates_usage_stat: AST
- N players: 199
- empirical OOS SD: 0.574 AST/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 70.3%
- MAE: 0.677
- RMSE: 0.877
- bias: +0.053
- coverage 50%: 42.7%
- coverage 80%: 80.4%
- coverage 90%: 84.9%
- z-error: mean=+0.063 sd=1.146
- top-25 tier accuracy: 84.0%
- top-50 tier accuracy: 82.0%
