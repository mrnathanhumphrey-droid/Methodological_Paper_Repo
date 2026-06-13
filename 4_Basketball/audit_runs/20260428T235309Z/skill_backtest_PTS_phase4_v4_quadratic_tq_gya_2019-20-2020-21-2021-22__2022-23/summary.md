# skill fit: backtest_PTS_phase4_v4_quadratic_tq_gya_2019-20-2020-21-2021-22__2022-23

- run timestamp: `20260428T235309Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 34,052
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 4268.5s (71.1 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0398
- min ESS: 132
- params summarized: 905

### issues
- R-hat for mu_position[1]: 1.010 > 1.01
- R-hat for mu_player[49]: 1.010 > 1.01
- R-hat for mu_player[59]: 1.010 > 1.01
- R-hat for mu_player[70]: 1.013 > 1.01
- R-hat for mu_player[101]: 1.019 > 1.01
- R-hat for mu_player[111]: 1.014 > 1.01
- R-hat for mu_player[128]: 1.011 > 1.01
- R-hat for mu_player[131]: 1.010 > 1.01
- R-hat for mu_player[148]: 1.011 > 1.01
- R-hat for mu_player[165]: 1.013 > 1.01
- R-hat for mu_player[185]: 1.011 > 1.01
- ESS for sigma_position: 398 < 400
- R-hat for sigma_age_player: 1.040 > 1.01
- ESS for sigma_age_player: 132 < 400
- R-hat for age_tilt_player_z[11]: 1.013 > 1.01
- R-hat for age_tilt_player_z[32]: 1.012 > 1.01
- R-hat for age_tilt_player_z[53]: 1.011 > 1.01
- R-hat for age_tilt_player_z[148]: 1.013 > 1.01
- R-hat for age_tilt_player_z[156]: 1.015 > 1.01
- R-hat for age_tilt_player_z[167]: 1.010 > 1.01
- … +17 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 82.4%
- ✓ **bias_near_zero**: bias = -0.150
- ✓ **z_error_well_calibrated**: z-error mean=-0.07, sd=1.15
- ✓ **top_25_tier_accuracy**: top-25 overlap = 84.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22
- test: 2022-23
- mates_usage_stat: FGA
- N players: 199
- empirical OOS SD: 1.781 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 70.3%
- MAE: 1.878
- RMSE: 2.508
- bias: -0.150
- coverage 50%: 51.8%
- coverage 80%: 82.4%
- coverage 90%: 85.4%
- z-error: mean=-0.066 sd=1.149
- top-25 tier accuracy: 84.0%
- top-50 tier accuracy: 76.0%
