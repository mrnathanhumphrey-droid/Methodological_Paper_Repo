# skill fit: backtest_REB_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260429T043548Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 2,933
- chains: 4 × (5 warmup + 5 sampling)
- wall time: 0.3s (0.0 min)

## convergence
- status: **PASSED**
- params summarized: 145

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 90.0%
- ✓ **bias_near_zero**: bias = +0.414
- ✓ **z_error_well_calibrated**: z-error mean=+0.02, sd=1.01
- ✗ **top_25_tier_accuracy**: top-25 overlap = nan%

## backtest metrics (REB)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: REB
- N players: 10
- empirical OOS SD: 0.800 REB/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 20.0%
- MAE: 1.457
- RMSE: 1.692
- bias: +0.414
- coverage 50%: 40.0%
- coverage 80%: 90.0%
- coverage 90%: 90.0%
- z-error: mean=+0.021 sd=1.006
- top-25 tier accuracy: nan%
- top-50 tier accuracy: nan%
