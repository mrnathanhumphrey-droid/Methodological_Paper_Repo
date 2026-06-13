# skill fit: backtest_BLK_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24__2024-25

- run timestamp: `20260502T085540Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 53,237
- chains: 2 × (400 warmup + 400 sampling)
- wall time: 2883.4s (48.1 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0299
- min ESS: 98
- params summarized: 905

### issues
- ESS for mu_position[1]: 285 < 400
- R-hat for mu_position[2]: 1.011 > 1.01
- R-hat for mu_player[13]: 1.010 > 1.01
- R-hat for mu_player[22]: 1.010 > 1.01
- R-hat for mu_player[23]: 1.012 > 1.01
- R-hat for mu_player[47]: 1.021 > 1.01
- R-hat for mu_player[64]: 1.013 > 1.01
- R-hat for mu_player[92]: 1.011 > 1.01
- R-hat for mu_player[106]: 1.016 > 1.01
- R-hat for mu_player[121]: 1.015 > 1.01
- R-hat for mu_player[183]: 1.011 > 1.01
- R-hat for mu_player[187]: 1.012 > 1.01
- ESS for beta_age_pos[1]: 233 < 400
- ESS for beta_age_pos[2]: 391 < 400
- R-hat for sigma_age_player: 1.010 > 1.01
- ESS for sigma_age_player: 98 < 400
- R-hat for age_tilt_player_z[13]: 1.015 > 1.01
- R-hat for age_tilt_player_z[51]: 1.010 > 1.01
- R-hat for age_tilt_player_z[55]: 1.029 > 1.01
- R-hat for age_tilt_player_z[79]: 1.011 > 1.01
- … +117 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 84.9%
- ✓ **bias_near_zero**: bias = +0.022
- ✓ **z_error_well_calibrated**: z-error mean=+0.08, sd=0.97
- ✓ **top_25_tier_accuracy**: top-25 overlap = 84.0%

## backtest metrics (BLK)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24
- test: 2024-25
- mates_usage_stat: BLK
- N players: 119
- empirical OOS SD: 0.177 BLK/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.1%
- MAE: 0.167
- RMSE: 0.221
- bias: +0.022
- coverage 50%: 52.9%
- coverage 80%: 84.9%
- coverage 90%: 89.1%
- z-error: mean=+0.084 sd=0.968
- top-25 tier accuracy: 84.0%
- top-50 tier accuracy: 80.0%
