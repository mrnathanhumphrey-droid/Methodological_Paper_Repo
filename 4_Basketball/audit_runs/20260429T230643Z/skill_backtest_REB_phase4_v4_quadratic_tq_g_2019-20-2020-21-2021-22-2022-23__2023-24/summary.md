# skill fit: backtest_REB_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260429T230643Z`
- stan model: `hierarchical_aging_quadratic_v3_pp_phi.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3185.1s (53.1 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0129
- min ESS: 306
- params summarized: 910

### issues
- R-hat for mu_player[116]: 1.012 > 1.01
- ESS for sigma_age_player: 306 < 400
- R-hat for age_tilt_player_z[44]: 1.011 > 1.01
- R-hat for age_tilt_player_z[68]: 1.011 > 1.01
- R-hat for age_tilt_player_z[114]: 1.013 > 1.01
- R-hat for age_tilt_player_z[116]: 1.012 > 1.01
- R-hat for age_tilt_player[44]: 1.011 > 1.01
- R-hat for age_tilt_player[116]: 1.012 > 1.01
- R-hat for rate_per_36_at_27[116]: 1.012 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 85.6%
- ✓ **bias_near_zero**: bias = +0.037
- ✓ **z_error_well_calibrated**: z-error mean=+0.04, sd=0.97
- ✓ **top_25_tier_accuracy**: top-25 overlap = 84.0%

## backtest metrics (REB)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: REB
- N players: 195
- empirical OOS SD: 0.670 REB/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 0.630
- RMSE: 0.814
- bias: +0.037
- coverage 50%: 55.4%
- coverage 80%: 85.6%
- coverage 90%: 89.7%
- z-error: mean=+0.045 sd=0.970
- top-25 tier accuracy: 84.0%
- top-50 tier accuracy: 92.0%
