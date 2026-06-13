# skill fit: backtest_STL_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260504T083648Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 64,126
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3002.1s (50.0 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0526
- min ESS: 163
- params summarized: 905

### issues
- R-hat for mu_league: 1.012 > 1.01
- ESS for mu_position[1]: 357 < 400
- ESS for mu_position[2]: 357 < 400
- R-hat for mu_player[16]: 1.010 > 1.01
- R-hat for mu_player[19]: 1.015 > 1.01
- R-hat for mu_player[32]: 1.010 > 1.01
- R-hat for mu_player[38]: 1.011 > 1.01
- R-hat for mu_player[45]: 1.013 > 1.01
- R-hat for mu_player[52]: 1.012 > 1.01
- R-hat for mu_player[92]: 1.012 > 1.01
- R-hat for mu_player[111]: 1.011 > 1.01
- R-hat for mu_player[122]: 1.011 > 1.01
- R-hat for mu_player[126]: 1.013 > 1.01
- R-hat for sigma_player: 1.010 > 1.01
- R-hat for beta_age_pos[1]: 1.013 > 1.01
- ESS for beta_age_pos[1]: 367 < 400
- ESS for beta_age_pos[2]: 358 < 400
- R-hat for sigma_age_player: 1.053 > 1.01
- ESS for sigma_age_player: 163 < 400
- R-hat for age_tilt_player_z[28]: 1.014 > 1.01
- … +92 more

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 95.5%
- ✓ **bias_near_zero**: bias = -0.057
- ✗ **z_error_well_calibrated**: z-error mean=-0.22, sd=0.68
- ✓ **top_25_tier_accuracy**: top-25 overlap = 80.0%

## backtest metrics (STL)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: STL
- N players: 133
- empirical OOS SD: 0.211 STL/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.139
- RMSE: 0.184
- bias: -0.057
- coverage 50%: 68.4%
- coverage 80%: 95.5%
- coverage 90%: 96.2%
- z-error: mean=-0.216 sd=0.680
- top-25 tier accuracy: 80.0%
- top-50 tier accuracy: 88.0%
