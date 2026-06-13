# skill fit: backtest_FGM_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260504T120302Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 64,126
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 5622.9s (93.7 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0122
- min ESS: 348
- params summarized: 905

### issues
- R-hat for mu_player[189]: 1.010 > 1.01
- ESS for sigma_position: 348 < 400
- R-hat for age_tilt_player_z[51]: 1.012 > 1.01
- R-hat for age_tilt_player[21]: 1.010 > 1.01

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 96.2%
- ✓ **bias_near_zero**: bias = -0.208
- ✗ **z_error_well_calibrated**: z-error mean=-0.23, sd=0.57
- ✓ **top_25_tier_accuracy**: top-25 overlap = 92.0%

## backtest metrics (FGM)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FGA
- N players: 133
- empirical OOS SD: 0.821 FGM/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.450
- RMSE: 0.569
- bias: -0.208
- coverage 50%: 72.9%
- coverage 80%: 96.2%
- coverage 90%: 99.2%
- z-error: mean=-0.225 sd=0.568
- top-25 tier accuracy: 92.0%
- top-50 tier accuracy: 90.0%
