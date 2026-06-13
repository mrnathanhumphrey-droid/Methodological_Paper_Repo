# skill fit: backtest_TOV_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260504T102913Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 64,126
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3616.5s (60.3 min)

## convergence
- status: **PASSED**
- params summarized: 905

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 94.0%
- ✓ **bias_near_zero**: bias = -0.097
- ✗ **z_error_well_calibrated**: z-error mean=-0.22, sd=0.69
- ✓ **top_25_tier_accuracy**: top-25 overlap = 84.0%

## backtest metrics (TOV)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: TOV
- N players: 133
- empirical OOS SD: 0.350 TOV/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.215
- RMSE: 0.307
- bias: -0.097
- coverage 50%: 75.2%
- coverage 80%: 94.0%
- coverage 90%: 94.0%
- z-error: mean=-0.225 sd=0.693
- top-25 tier accuracy: 84.0%
- top-50 tier accuracy: 94.0%
