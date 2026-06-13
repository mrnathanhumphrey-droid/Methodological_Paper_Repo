# skill fit: backtest_FG3A_phase4_v4_quadratic_tq_g_2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260528T120205Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 85,702
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 7755.9s (129.3 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0170
- min ESS: 529
- params summarized: 1901

### issues
- R-hat for mu_player[68]: 1.010 > 1.01
- R-hat for mu_player[85]: 1.011 > 1.01
- R-hat for mu_player[171]: 1.010 > 1.01
- R-hat for mu_player[235]: 1.010 > 1.01
- R-hat for mu_player[311]: 1.011 > 1.01
- R-hat for mu_player[402]: 1.011 > 1.01
- R-hat for mu_player[429]: 1.010 > 1.01
- R-hat for mu_player[447]: 1.011 > 1.01
- R-hat for age_tilt_player_z[10]: 1.011 > 1.01
- R-hat for age_tilt_player_z[159]: 1.010 > 1.01
- R-hat for age_tilt_player_z[189]: 1.016 > 1.01
- R-hat for age_tilt_player_z[220]: 1.010 > 1.01
- R-hat for age_tilt_player_z[434]: 1.011 > 1.01
- R-hat for age_tilt_player_z[447]: 1.010 > 1.01
- R-hat for age_tilt_player[10]: 1.010 > 1.01
- R-hat for age_tilt_player[189]: 1.017 > 1.01
- R-hat for age_tilt_player[220]: 1.010 > 1.01
- R-hat for age_tilt_player[429]: 1.010 > 1.01
- R-hat for age_tilt_player[443]: 1.010 > 1.01
- R-hat for age_tilt_player[447]: 1.012 > 1.01
- … +3 more

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 77.3%
- ✓ **bias_near_zero**: bias = +0.044
- ✓ **z_error_well_calibrated**: z-error mean=-0.00, sd=1.17
- ✗ **top_25_tier_accuracy**: top-25 overlap = 48.0%

## backtest metrics (FG3A)
- train: 2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FG3A
- N players: 256
- empirical OOS SD: 0.837 FG3A/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 47.5%
- MAE: 0.988
- RMSE: 1.280
- bias: +0.044
- coverage 50%: 47.7%
- coverage 80%: 77.3%
- coverage 90%: 84.4%
- z-error: mean=-0.000 sd=1.171
- top-25 tier accuracy: 48.0%
- top-50 tier accuracy: 70.0%
