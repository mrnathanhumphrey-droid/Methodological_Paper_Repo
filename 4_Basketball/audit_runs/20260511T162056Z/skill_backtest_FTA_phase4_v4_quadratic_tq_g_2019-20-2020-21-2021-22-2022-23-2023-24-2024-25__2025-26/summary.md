# skill fit: backtest_FTA_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260511T162056Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 63,455
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 4380.0s (73.0 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0172
- min ESS: 202
- params summarized: 905

### issues
- R-hat for mu_player[22]: 1.011 > 1.01
- R-hat for mu_player[134]: 1.010 > 1.01
- R-hat for peak_age_pos[1]: 1.011 > 1.01
- ESS for peak_age_pos[1]: 387 < 400
- R-hat for peak_age_pos[2]: 1.010 > 1.01
- R-hat for beta_age_pos[2]: 1.017 > 1.01
- R-hat for sigma_age_player: 1.012 > 1.01
- ESS for sigma_age_player: 202 < 400
- R-hat for age_tilt_player[13]: 1.012 > 1.01
- R-hat for age_tilt_player[14]: 1.012 > 1.01
- R-hat for age_tilt_player[17]: 1.017 > 1.01
- R-hat for age_tilt_player[66]: 1.014 > 1.01
- R-hat for age_tilt_player[69]: 1.011 > 1.01
- R-hat for age_tilt_player[94]: 1.013 > 1.01
- R-hat for age_tilt_player[185]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[134]: 1.010 > 1.01
- R-hat for age_curve_position[3,8]: 1.010 > 1.01

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 72.4%
- ✓ **bias_near_zero**: bias = -0.519
- ✗ **z_error_well_calibrated**: z-error mean=-0.57, sd=1.29
- ✓ **top_25_tier_accuracy**: top-25 overlap = 72.0%

## backtest metrics (FTA)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FTA
- N players: 105
- empirical OOS SD: 0.768 FTA/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.990
- RMSE: 1.338
- bias: -0.519
- coverage 50%: 42.9%
- coverage 80%: 72.4%
- coverage 90%: 79.0%
- z-error: mean=-0.571 sd=1.292
- top-25 tier accuracy: 72.0%
- top-50 tier accuracy: 86.0%
