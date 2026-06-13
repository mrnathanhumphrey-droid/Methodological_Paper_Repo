# skill fit: backtest_BLK_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260511T094942Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 63,455
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 2864.2s (47.7 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0237
- min ESS: 212
- params summarized: 905

### issues
- R-hat for mu_player[21]: 1.011 > 1.01
- R-hat for mu_player[75]: 1.012 > 1.01
- R-hat for mu_player[77]: 1.013 > 1.01
- R-hat for mu_player[129]: 1.011 > 1.01
- R-hat for mu_player[147]: 1.011 > 1.01
- R-hat for mu_player[168]: 1.013 > 1.01
- R-hat for sigma_age_player: 1.024 > 1.01
- ESS for sigma_age_player: 212 < 400
- R-hat for age_tilt_player_z[5]: 1.010 > 1.01
- R-hat for age_tilt_player_z[21]: 1.010 > 1.01
- R-hat for age_tilt_player_z[69]: 1.010 > 1.01
- R-hat for age_tilt_player_z[87]: 1.014 > 1.01
- R-hat for age_tilt_player_z[94]: 1.012 > 1.01
- R-hat for age_tilt_player_z[101]: 1.011 > 1.01
- R-hat for age_tilt_player_z[115]: 1.010 > 1.01
- R-hat for age_tilt_player_z[120]: 1.015 > 1.01
- R-hat for age_tilt_player_z[171]: 1.014 > 1.01
- R-hat for age_tilt_player_z[172]: 1.011 > 1.01
- R-hat for age_tilt_player_z[174]: 1.014 > 1.01
- R-hat for age_tilt_player_z[180]: 1.011 > 1.01
- … +7 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 81.9%
- ✓ **bias_near_zero**: bias = +0.046
- ✓ **z_error_well_calibrated**: z-error mean=+0.22, sd=1.09
- ✓ **top_25_tier_accuracy**: top-25 overlap = 84.0%

## backtest metrics (BLK)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: BLK
- N players: 105
- empirical OOS SD: 0.182 BLK/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.170
- RMSE: 0.245
- bias: +0.046
- coverage 50%: 59.0%
- coverage 80%: 81.9%
- coverage 90%: 88.6%
- z-error: mean=+0.217 sd=1.087
- top-25 tier accuracy: 84.0%
- top-50 tier accuracy: 82.0%
