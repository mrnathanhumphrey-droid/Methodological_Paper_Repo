# skill fit: backtest_BLK_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260430T020327Z`
- stan model: `hierarchical_aging_quadratic_v3_pp_phi.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 2092.7s (34.9 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0167
- min ESS: 185
- params summarized: 910

### issues
- R-hat for mu_player[29]: 1.016 > 1.01
- R-hat for mu_player[47]: 1.013 > 1.01
- R-hat for mu_player[51]: 1.011 > 1.01
- R-hat for mu_player[76]: 1.010 > 1.01
- R-hat for mu_player[92]: 1.010 > 1.01
- R-hat for mu_player[180]: 1.012 > 1.01
- R-hat for mu_player[194]: 1.010 > 1.01
- R-hat for mu_player[198]: 1.011 > 1.01
- R-hat for beta_age_pos[2]: 1.011 > 1.01
- R-hat for sigma_age_player: 1.014 > 1.01
- ESS for sigma_age_player: 185 < 400
- R-hat for age_tilt_player_z[40]: 1.014 > 1.01
- R-hat for age_tilt_player_z[50]: 1.012 > 1.01
- R-hat for age_tilt_player_z[52]: 1.011 > 1.01
- R-hat for age_tilt_player_z[59]: 1.017 > 1.01
- R-hat for age_tilt_player_z[71]: 1.010 > 1.01
- R-hat for age_tilt_player_z[80]: 1.013 > 1.01
- R-hat for age_tilt_player_z[126]: 1.011 > 1.01
- R-hat for age_tilt_player_z[191]: 1.014 > 1.01
- R-hat for age_tilt_player[23]: 1.011 > 1.01
- … +18 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 84.6%
- ✓ **bias_near_zero**: bias = -0.054
- ✓ **z_error_well_calibrated**: z-error mean=-0.26, sd=1.00
- ✓ **top_25_tier_accuracy**: top-25 overlap = 76.0%

## backtest metrics (BLK)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: BLK
- N players: 195
- empirical OOS SD: 0.178 BLK/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 0.171
- RMSE: 0.240
- bias: -0.054
- coverage 50%: 52.3%
- coverage 80%: 84.6%
- coverage 90%: 89.2%
- z-error: mean=-0.257 sd=0.995
- top-25 tier accuracy: 76.0%
- top-50 tier accuracy: 84.0%
