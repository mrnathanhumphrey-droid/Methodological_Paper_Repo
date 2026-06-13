# skill fit: backtest_REB_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24__2024-25

- run timestamp: `20260502T051745Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 53,237
- chains: 2 × (400 warmup + 400 sampling)
- wall time: 4536.0s (75.6 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0240
- min ESS: 182
- params summarized: 905

### issues
- R-hat for mu_player[5]: 1.011 > 1.01
- R-hat for mu_player[52]: 1.014 > 1.01
- R-hat for mu_player[83]: 1.014 > 1.01
- R-hat for mu_player[84]: 1.018 > 1.01
- R-hat for mu_player[94]: 1.014 > 1.01
- R-hat for mu_player[95]: 1.010 > 1.01
- R-hat for mu_player[102]: 1.012 > 1.01
- R-hat for mu_player[112]: 1.024 > 1.01
- R-hat for mu_player[129]: 1.011 > 1.01
- R-hat for mu_player[136]: 1.015 > 1.01
- R-hat for mu_player[151]: 1.011 > 1.01
- R-hat for mu_player[183]: 1.010 > 1.01
- ESS for sigma_age_player: 182 < 400
- R-hat for age_tilt_player_z[52]: 1.012 > 1.01
- R-hat for age_tilt_player_z[67]: 1.013 > 1.01
- R-hat for age_tilt_player_z[86]: 1.010 > 1.01
- R-hat for age_tilt_player_z[94]: 1.013 > 1.01
- R-hat for age_tilt_player_z[102]: 1.013 > 1.01
- R-hat for age_tilt_player_z[119]: 1.012 > 1.01
- R-hat for age_tilt_player_z[137]: 1.016 > 1.01
- … +19 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 88.2%
- ✓ **bias_near_zero**: bias = -0.097
- ✓ **z_error_well_calibrated**: z-error mean=-0.10, sd=0.94
- ✓ **top_25_tier_accuracy**: top-25 overlap = 96.0%

## backtest metrics (REB)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24
- test: 2024-25
- mates_usage_stat: REB
- N players: 119
- empirical OOS SD: 0.736 REB/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.1%
- MAE: 0.647
- RMSE: 0.922
- bias: -0.097
- coverage 50%: 63.0%
- coverage 80%: 88.2%
- coverage 90%: 92.4%
- z-error: mean=-0.098 sd=0.942
- top-25 tier accuracy: 96.0%
- top-50 tier accuracy: 92.0%
