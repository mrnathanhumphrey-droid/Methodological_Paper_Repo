# skill fit: backtest_REB_phase4_v4_quadratic_tq_g_2017-18-2018-19-2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260505T225045Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 70,243
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 5699.4s (95.0 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0147
- min ESS: 347
- params summarized: 905

### issues
- R-hat for mu_league: 1.011 > 1.01
- R-hat for mu_player[15]: 1.010 > 1.01
- R-hat for mu_player[16]: 1.012 > 1.01
- R-hat for mu_player[24]: 1.013 > 1.01
- R-hat for sigma_age_player: 1.010 > 1.01
- ESS for sigma_age_player: 347 < 400
- R-hat for age_tilt_player_z[32]: 1.011 > 1.01
- R-hat for age_tilt_player_z[64]: 1.012 > 1.01
- R-hat for age_tilt_player_z[117]: 1.011 > 1.01
- R-hat for age_tilt_player_z[131]: 1.012 > 1.01
- R-hat for age_tilt_player_z[132]: 1.012 > 1.01
- R-hat for age_tilt_player_z[182]: 1.013 > 1.01
- R-hat for age_tilt_player_z[195]: 1.010 > 1.01
- R-hat for age_tilt_player[64]: 1.015 > 1.01
- R-hat for age_tilt_player[179]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[15]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[16]: 1.012 > 1.01
- R-hat for rate_per_36_at_27[24]: 1.013 > 1.01
- R-hat for rate_per_36_league_at_27: 1.012 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 88.2%
- ✓ **bias_near_zero**: bias = +0.050
- ✓ **z_error_well_calibrated**: z-error mean=+0.06, sd=0.91
- ✓ **top_25_tier_accuracy**: top-25 overlap = 88.0%

## backtest metrics (REB)
- train: 2017-18,2018-19,2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: REB
- N players: 153
- empirical OOS SD: 0.781 REB/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 34.6%
- MAE: 0.653
- RMSE: 0.839
- bias: +0.050
- coverage 50%: 55.6%
- coverage 80%: 88.2%
- coverage 90%: 91.5%
- z-error: mean=+0.059 sd=0.914
- top-25 tier accuracy: 88.0%
- top-50 tier accuracy: 98.0%
