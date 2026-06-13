# skill fit: backtest_BLK_phase4_v4_quadratic_tq_g_2017-18-2018-19-2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260506T150621Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 70,243
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3949.4s (65.8 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0183
- min ESS: 192
- params summarized: 905

### issues
- R-hat for mu_player[23]: 1.010 > 1.01
- R-hat for mu_player[110]: 1.017 > 1.01
- R-hat for mu_player[120]: 1.018 > 1.01
- R-hat for sigma_age_player: 1.015 > 1.01
- ESS for sigma_age_player: 192 < 400
- R-hat for age_tilt_player_z[91]: 1.010 > 1.01
- R-hat for age_tilt_player_z[123]: 1.015 > 1.01
- R-hat for age_tilt_player_z[143]: 1.015 > 1.01
- R-hat for age_tilt_player_z[164]: 1.012 > 1.01
- R-hat for beta_alpha_promotion: 1.014 > 1.01
- R-hat for age_tilt_player[3]: 1.012 > 1.01
- R-hat for age_tilt_player[24]: 1.014 > 1.01
- R-hat for age_tilt_player[25]: 1.011 > 1.01
- R-hat for age_tilt_player[52]: 1.012 > 1.01
- R-hat for age_tilt_player[155]: 1.012 > 1.01
- R-hat for age_tilt_player[177]: 1.011 > 1.01
- R-hat for age_tilt_player[182]: 1.011 > 1.01
- R-hat for age_tilt_player[190]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[110]: 1.015 > 1.01
- R-hat for rate_per_36_at_27[120]: 1.018 > 1.01
- … +1 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 89.5%
- ✓ **bias_near_zero**: bias = -0.038
- ✓ **z_error_well_calibrated**: z-error mean=-0.18, sd=0.91
- ✓ **top_25_tier_accuracy**: top-25 overlap = 84.0%

## backtest metrics (BLK)
- train: 2017-18,2018-19,2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: BLK
- N players: 153
- empirical OOS SD: 0.192 BLK/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 34.6%
- MAE: 0.161
- RMSE: 0.222
- bias: -0.038
- coverage 50%: 55.6%
- coverage 80%: 89.5%
- coverage 90%: 93.5%
- z-error: mean=-0.181 sd=0.907
- top-25 tier accuracy: 84.0%
- top-50 tier accuracy: 78.0%
