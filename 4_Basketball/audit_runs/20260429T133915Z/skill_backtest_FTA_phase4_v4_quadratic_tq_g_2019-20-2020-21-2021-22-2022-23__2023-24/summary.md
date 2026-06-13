# skill fit: backtest_FTA_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260429T133915Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3067.6s (51.1 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0193
- min ESS: 194
- params summarized: 905

### issues
- R-hat for mu_player[118]: 1.010 > 1.01
- ESS for peak_age_pos[1]: 301 < 400
- R-hat for peak_age_pos[3]: 1.011 > 1.01
- ESS for beta_age_pos[1]: 325 < 400
- R-hat for sigma_age_player: 1.019 > 1.01
- ESS for sigma_age_player: 194 < 400
- R-hat for age_tilt_player_z[46]: 1.017 > 1.01
- R-hat for age_tilt_player_z[57]: 1.011 > 1.01

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 81.0%
- ✓ **bias_near_zero**: bias = +0.380
- ✗ **z_error_well_calibrated**: z-error mean=+0.42, sd=0.95
- ✓ **top_25_tier_accuracy**: top-25 overlap = 68.0%

## backtest metrics (FTA)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FTA
- N players: 195
- empirical OOS SD: 0.699 FTA/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 0.727
- RMSE: 0.930
- bias: +0.380
- coverage 50%: 49.7%
- coverage 80%: 81.0%
- coverage 90%: 87.2%
- z-error: mean=+0.417 sd=0.952
- top-25 tier accuracy: 68.0%
- top-50 tier accuracy: 80.0%
