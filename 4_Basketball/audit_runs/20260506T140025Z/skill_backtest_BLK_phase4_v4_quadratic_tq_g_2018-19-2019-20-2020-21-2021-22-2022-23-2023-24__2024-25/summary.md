# skill fit: backtest_BLK_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25

- run timestamp: `20260506T140025Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 68,336
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3519.3s (58.7 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0393
- min ESS: 184
- params summarized: 905

### issues
- R-hat for mu_player[83]: 1.012 > 1.01
- R-hat for mu_player[84]: 1.010 > 1.01
- R-hat for mu_player[126]: 1.014 > 1.01
- R-hat for mu_player[138]: 1.014 > 1.01
- R-hat for mu_player[156]: 1.012 > 1.01
- R-hat for mu_player[174]: 1.014 > 1.01
- R-hat for mu_player[177]: 1.012 > 1.01
- R-hat for sigma_age_player: 1.039 > 1.01
- ESS for sigma_age_player: 184 < 400
- R-hat for age_tilt_player_z[15]: 1.011 > 1.01
- R-hat for age_tilt_player_z[23]: 1.010 > 1.01
- R-hat for age_tilt_player_z[45]: 1.013 > 1.01
- R-hat for age_tilt_player_z[65]: 1.012 > 1.01
- R-hat for age_tilt_player_z[66]: 1.011 > 1.01
- R-hat for age_tilt_player_z[76]: 1.015 > 1.01
- R-hat for age_tilt_player_z[83]: 1.013 > 1.01
- R-hat for age_tilt_player_z[84]: 1.011 > 1.01
- R-hat for age_tilt_player_z[90]: 1.017 > 1.01
- R-hat for age_tilt_player_z[122]: 1.010 > 1.01
- R-hat for age_tilt_player_z[140]: 1.010 > 1.01
- … +26 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 86.3%
- ✓ **bias_near_zero**: bias = +0.020
- ✓ **z_error_well_calibrated**: z-error mean=+0.08, sd=0.93
- ✓ **top_25_tier_accuracy**: top-25 overlap = 72.0%

## backtest metrics (BLK)
- train: 2018-19,2019-20,2020-21,2021-22,2022-23,2023-24
- test: 2024-25
- mates_usage_stat: BLK
- N players: 131
- empirical OOS SD: 0.186 BLK/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 41.1%
- MAE: 0.165
- RMSE: 0.217
- bias: +0.020
- coverage 50%: 52.7%
- coverage 80%: 86.3%
- coverage 90%: 92.4%
- z-error: mean=+0.078 sd=0.930
- top-25 tier accuracy: 72.0%
- top-50 tier accuracy: 86.0%
