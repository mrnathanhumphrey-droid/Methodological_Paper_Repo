# skill fit: backtest_BLK_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260429T084118Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 2305.8s (38.4 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0586
- min ESS: 60
- params summarized: 905

### issues
- R-hat for mu_player[82]: 1.011 > 1.01
- R-hat for mu_player[92]: 1.011 > 1.01
- R-hat for mu_player[146]: 1.011 > 1.01
- R-hat for mu_player[196]: 1.019 > 1.01
- R-hat for sigma_age_player: 1.059 > 1.01
- ESS for sigma_age_player: 60 < 400
- R-hat for age_tilt_player_z[61]: 1.010 > 1.01
- R-hat for age_tilt_player_z[103]: 1.013 > 1.01
- R-hat for age_tilt_player_z[141]: 1.011 > 1.01
- R-hat for age_tilt_player[1]: 1.011 > 1.01
- ESS for age_tilt_player[1]: 343 < 400
- R-hat for age_tilt_player[2]: 1.017 > 1.01
- R-hat for age_tilt_player[3]: 1.011 > 1.01
- R-hat for age_tilt_player[8]: 1.010 > 1.01
- R-hat for age_tilt_player[10]: 1.012 > 1.01
- R-hat for age_tilt_player[12]: 1.017 > 1.01
- R-hat for age_tilt_player[14]: 1.016 > 1.01
- R-hat for age_tilt_player[17]: 1.011 > 1.01
- R-hat for age_tilt_player[18]: 1.015 > 1.01
- R-hat for age_tilt_player[23]: 1.012 > 1.01
- … +91 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 84.1%
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
- coverage 50%: 53.3%
- coverage 80%: 84.1%
- coverage 90%: 90.3%
- z-error: mean=-0.257 sd=1.003
- top-25 tier accuracy: 76.0%
- top-50 tier accuracy: 84.0%
