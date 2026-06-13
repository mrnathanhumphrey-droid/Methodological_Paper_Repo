# skill fit: backtest_REB_phase4_v4_quadratic_tq_g_2018-19-2019-20-2020-21-2021-22-2022-23-2023-24__2024-25

- run timestamp: `20260505T171359Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 68,336
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 5175.9s (86.3 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0181
- min ESS: 277
- params summarized: 905

### issues
- R-hat for mu_player[29]: 1.010 > 1.01
- R-hat for mu_player[34]: 1.012 > 1.01
- R-hat for mu_player[57]: 1.010 > 1.01
- R-hat for mu_player[110]: 1.015 > 1.01
- R-hat for sigma_age_player: 1.013 > 1.01
- ESS for sigma_age_player: 277 < 400
- R-hat for age_tilt_player_z[1]: 1.012 > 1.01
- R-hat for age_tilt_player_z[131]: 1.018 > 1.01
- R-hat for age_tilt_player_z[173]: 1.013 > 1.01
- R-hat for age_tilt_player_z[174]: 1.011 > 1.01
- R-hat for age_tilt_player[112]: 1.011 > 1.01
- R-hat for age_tilt_player[120]: 1.016 > 1.01
- R-hat for age_tilt_player[131]: 1.010 > 1.01
- R-hat for age_tilt_player[173]: 1.011 > 1.01
- R-hat for age_tilt_player[181]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[34]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[57]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[110]: 1.015 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 87.8%
- ✓ **bias_near_zero**: bias = -0.077
- ✓ **z_error_well_calibrated**: z-error mean=-0.08, sd=0.94
- ✓ **top_25_tier_accuracy**: top-25 overlap = 96.0%

## backtest metrics (REB)
- train: 2018-19,2019-20,2020-21,2021-22,2022-23,2023-24
- test: 2024-25
- mates_usage_stat: REB
- N players: 131
- empirical OOS SD: 0.760 REB/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 41.1%
- MAE: 0.628
- RMSE: 0.910
- bias: -0.077
- coverage 50%: 63.4%
- coverage 80%: 87.8%
- coverage 90%: 91.6%
- z-error: mean=-0.078 sd=0.941
- top-25 tier accuracy: 96.0%
- top-50 tier accuracy: 94.0%
