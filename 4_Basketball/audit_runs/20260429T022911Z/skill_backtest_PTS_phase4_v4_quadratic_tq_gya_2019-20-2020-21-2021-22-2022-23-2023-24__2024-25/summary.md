# skill fit: backtest_PTS_phase4_v4_quadratic_tq_gya_2019-20-2020-21-2021-22-2022-23-2023-24__2024-25

- run timestamp: `20260429T022911Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 60,169
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 9354.0s (155.9 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0436
- min ESS: 165
- params summarized: 905

### issues
- R-hat for mu_league: 1.024 > 1.01
- ESS for mu_league: 274 < 400
- R-hat for sigma_position: 1.044 > 1.01
- ESS for sigma_position: 165 < 400
- ESS for peak_age_pos[1]: 394 < 400
- ESS for peak_age_pos[2]: 386 < 400
- ESS for beta_age_pos[2]: 394 < 400
- R-hat for age_tilt_player_z[121]: 1.011 > 1.01
- R-hat for rate_per_36_league_at_27: 1.024 > 1.01
- ESS for rate_per_36_league_at_27: 274 < 400
- R-hat for age_curve_position[1,7]: 1.010 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 87.4%
- ✓ **bias_near_zero**: bias = -0.055
- ✓ **z_error_well_calibrated**: z-error mean=-0.04, sd=0.94
- ✓ **top_25_tier_accuracy**: top-25 overlap = 76.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24
- test: 2024-25
- mates_usage_stat: FGA
- N players: 183
- empirical OOS SD: 2.095 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 64.7%
- MAE: 1.920
- RMSE: 2.327
- bias: -0.055
- coverage 50%: 49.2%
- coverage 80%: 87.4%
- coverage 90%: 94.0%
- z-error: mean=-0.039 sd=0.944
- top-25 tier accuracy: 76.0%
- top-50 tier accuracy: 78.0%
