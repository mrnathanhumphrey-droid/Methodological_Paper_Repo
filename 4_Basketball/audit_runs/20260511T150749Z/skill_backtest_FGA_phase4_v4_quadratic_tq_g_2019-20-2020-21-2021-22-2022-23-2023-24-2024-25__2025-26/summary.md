# skill fit: backtest_FGA_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260511T150749Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 63,455
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 6156.4s (102.6 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0143
- min ESS: 342
- params summarized: 905

### issues
- R-hat for mu_player[54]: 1.011 > 1.01
- R-hat for mu_player[128]: 1.010 > 1.01
- R-hat for mu_player[190]: 1.010 > 1.01
- R-hat for peak_age_pos[1]: 1.010 > 1.01
- ESS for peak_age_pos[1]: 342 < 400
- ESS for beta_age_pos[1]: 394 < 400
- R-hat for age_tilt_player_z[25]: 1.014 > 1.01
- R-hat for age_tilt_player_z[128]: 1.011 > 1.01
- R-hat for age_tilt_player_z[190]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[54]: 1.011 > 1.01
- R-hat for rate_per_36_at_27[128]: 1.010 > 1.01

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 78.1%
- ✓ **bias_near_zero**: bias = -0.524
- ✗ **z_error_well_calibrated**: z-error mean=-0.30, sd=1.18
- ✓ **top_25_tier_accuracy**: top-25 overlap = 76.0%

## backtest metrics (FGA)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FGA
- N players: 105
- empirical OOS SD: 1.580 FGA/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 1.626
- RMSE: 2.106
- bias: -0.524
- coverage 50%: 44.8%
- coverage 80%: 78.1%
- coverage 90%: 87.6%
- z-error: mean=-0.305 sd=1.176
- top-25 tier accuracy: 76.0%
- top-50 tier accuracy: 86.0%
