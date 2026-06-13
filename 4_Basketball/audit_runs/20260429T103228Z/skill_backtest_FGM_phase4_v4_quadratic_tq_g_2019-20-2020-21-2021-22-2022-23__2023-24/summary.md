# skill fit: backtest_FGM_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260429T103228Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3989.0s (66.5 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0152
- min ESS: 274
- params summarized: 905

### issues
- R-hat for mu_player[162]: 1.015 > 1.01
- R-hat for sigma_position: 1.012 > 1.01
- ESS for sigma_position: 274 < 400
- R-hat for gamma_pos[2]: 1.013 > 1.01
- R-hat for age_tilt_player_z[23]: 1.010 > 1.01
- R-hat for age_tilt_player_z[28]: 1.015 > 1.01
- R-hat for beta_young_on_tank: 1.014 > 1.01
- R-hat for age_tilt_player[38]: 1.010 > 1.01
- R-hat for rate_per_36_at_27[162]: 1.015 > 1.01
- R-hat for young_on_tank_lift: 1.014 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 83.6%
- ✓ **bias_near_zero**: bias = +0.182
- ✓ **z_error_well_calibrated**: z-error mean=+0.22, sd=1.02
- ✓ **top_25_tier_accuracy**: top-25 overlap = 64.0%

## backtest metrics (FGM)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 195
- empirical OOS SD: 0.702 FGM/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 0.705
- RMSE: 0.873
- bias: +0.182
- coverage 50%: 47.7%
- coverage 80%: 83.6%
- coverage 90%: 90.3%
- z-error: mean=+0.216 sd=1.016
- top-25 tier accuracy: 64.0%
- top-50 tier accuracy: 82.0%
