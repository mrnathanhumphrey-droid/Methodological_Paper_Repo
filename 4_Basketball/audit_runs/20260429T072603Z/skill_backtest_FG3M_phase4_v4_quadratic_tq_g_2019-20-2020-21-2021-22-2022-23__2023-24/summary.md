# skill fit: backtest_FG3M_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260429T072603Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3371.8s (56.2 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0286
- min ESS: 159
- params summarized: 905

### issues
- R-hat for mu_player[35]: 1.010 > 1.01
- R-hat for sigma_age_player: 1.029 > 1.01
- ESS for sigma_age_player: 159 < 400
- R-hat for age_tilt_player_z[54]: 1.010 > 1.01
- R-hat for age_tilt_player[5]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[123]: 1.012 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 82.1%
- ✓ **bias_near_zero**: bias = +0.002
- ✓ **z_error_well_calibrated**: z-error mean=-0.02, sd=1.02
- ✓ **top_25_tier_accuracy**: top-25 overlap = 56.0%

## backtest metrics (FG3M)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FG3A
- N players: 195
- empirical OOS SD: 0.352 FG3M/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 0.358
- RMSE: 0.464
- bias: +0.002
- coverage 50%: 55.4%
- coverage 80%: 82.1%
- coverage 90%: 87.2%
- z-error: mean=-0.019 sd=1.016
- top-25 tier accuracy: 56.0%
- top-50 tier accuracy: 76.0%
