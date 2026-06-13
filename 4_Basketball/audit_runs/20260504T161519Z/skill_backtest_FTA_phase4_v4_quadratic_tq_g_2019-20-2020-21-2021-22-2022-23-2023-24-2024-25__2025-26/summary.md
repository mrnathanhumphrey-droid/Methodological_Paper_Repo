# skill fit: backtest_FTA_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260504T161519Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 64,126
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 4523.1s (75.4 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0121
- min ESS: 248
- params summarized: 905

### issues
- R-hat for beta_age_pos[3]: 1.010 > 1.01
- R-hat for sigma_age_player: 1.012 > 1.01
- ESS for sigma_age_player: 248 < 400
- R-hat for age_tilt_player_z[99]: 1.012 > 1.01
- R-hat for age_tilt_player[46]: 1.010 > 1.01
- R-hat for age_tilt_player[99]: 1.012 > 1.01

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 96.2%
- ✓ **bias_near_zero**: bias = -0.202
- ✗ **z_error_well_calibrated**: z-error mean=-0.22, sd=0.58
- ✓ **top_25_tier_accuracy**: top-25 overlap = 88.0%

## backtest metrics (FTA)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FTA
- N players: 133
- empirical OOS SD: 0.768 FTA/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.426
- RMSE: 0.585
- bias: -0.202
- coverage 50%: 73.7%
- coverage 80%: 96.2%
- coverage 90%: 97.7%
- z-error: mean=-0.217 sd=0.579
- top-25 tier accuracy: 88.0%
- top-50 tier accuracy: 90.0%
