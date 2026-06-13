# skill fit: backtest_REB_phase4_v4_quadratic_tq_g_2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260527T172543Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 85,702
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 10432.4s (173.9 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0515
- min ESS: 96
- params summarized: 1901

### issues
- R-hat for mu_player[2]: 1.024 > 1.01
- R-hat for mu_player[65]: 1.010 > 1.01
- R-hat for mu_player[99]: 1.010 > 1.01
- R-hat for mu_player[278]: 1.011 > 1.01
- R-hat for mu_player[303]: 1.010 > 1.01
- R-hat for mu_player[345]: 1.012 > 1.01
- R-hat for mu_player[414]: 1.011 > 1.01
- R-hat for sigma_player: 1.012 > 1.01
- R-hat for sigma_age_player: 1.052 > 1.01
- ESS for sigma_age_player: 96 < 400
- R-hat for age_tilt_player_z[177]: 1.013 > 1.01
- R-hat for age_tilt_player_z[263]: 1.011 > 1.01
- R-hat for age_tilt_player_z[366]: 1.018 > 1.01
- R-hat for age_tilt_player_z[368]: 1.014 > 1.01
- R-hat for age_tilt_player_z[369]: 1.013 > 1.01
- R-hat for age_tilt_player[2]: 1.011 > 1.01
- R-hat for age_tilt_player[25]: 1.011 > 1.01
- R-hat for age_tilt_player[30]: 1.011 > 1.01
- R-hat for age_tilt_player[65]: 1.011 > 1.01
- R-hat for age_tilt_player[89]: 1.010 > 1.01
- … +44 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 83.6%
- ✓ **bias_near_zero**: bias = +0.125
- ✓ **z_error_well_calibrated**: z-error mean=+0.14, sd=1.03
- ✓ **top_25_tier_accuracy**: top-25 overlap = 84.0%

## backtest metrics (REB)
- train: 2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: REB
- N players: 256
- empirical OOS SD: 0.680 REB/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 47.5%
- MAE: 0.698
- RMSE: 0.910
- bias: +0.125
- coverage 50%: 47.3%
- coverage 80%: 83.6%
- coverage 90%: 88.3%
- z-error: mean=+0.139 sd=1.034
- top-25 tier accuracy: 84.0%
- top-50 tier accuracy: 88.0%
