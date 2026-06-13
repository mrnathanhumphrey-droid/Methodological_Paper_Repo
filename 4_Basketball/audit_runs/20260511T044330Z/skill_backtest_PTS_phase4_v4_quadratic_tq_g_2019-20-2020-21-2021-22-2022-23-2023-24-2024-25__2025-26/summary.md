# skill fit: backtest_PTS_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260511T044330Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 63,455
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 7822.6s (130.4 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0230
- min ESS: 207
- params summarized: 905

### issues
- R-hat for mu_player[2]: 1.016 > 1.01
- R-hat for mu_player[43]: 1.016 > 1.01
- R-hat for mu_player[76]: 1.010 > 1.01
- R-hat for mu_player[77]: 1.023 > 1.01
- R-hat for mu_player[80]: 1.012 > 1.01
- R-hat for mu_player[96]: 1.010 > 1.01
- R-hat for mu_player[102]: 1.012 > 1.01
- R-hat for mu_player[104]: 1.011 > 1.01
- R-hat for mu_player[145]: 1.016 > 1.01
- R-hat for mu_player[173]: 1.013 > 1.01
- R-hat for mu_player[195]: 1.010 > 1.01
- ESS for sigma_position: 207 < 400
- R-hat for peak_age_pos[1]: 1.012 > 1.01
- ESS for peak_age_pos[1]: 217 < 400
- ESS for beta_age_pos[1]: 271 < 400
- R-hat for age_tilt_player_z[2]: 1.012 > 1.01
- R-hat for age_tilt_player_z[6]: 1.014 > 1.01
- R-hat for age_tilt_player_z[14]: 1.011 > 1.01
- R-hat for age_tilt_player_z[36]: 1.014 > 1.01
- R-hat for age_tilt_player_z[45]: 1.013 > 1.01
- … +31 more

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 77.1%
- ✓ **bias_near_zero**: bias = -0.940
- ✗ **z_error_well_calibrated**: z-error mean=-0.36, sd=1.12
- ✓ **top_25_tier_accuracy**: top-25 overlap = 80.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FGA
- N players: 105
- empirical OOS SD: 2.246 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 2.248
- RMSE: 3.029
- bias: -0.940
- coverage 50%: 54.3%
- coverage 80%: 77.1%
- coverage 90%: 85.7%
- z-error: mean=-0.361 sd=1.124
- top-25 tier accuracy: 80.0%
- top-50 tier accuracy: 86.0%
