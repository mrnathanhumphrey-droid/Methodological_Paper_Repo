# skill fit: backtest_PTS_phase4_v4_quadratic_tq_g_2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260527T143141Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 85,702
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 10206.4s (170.1 min)

## convergence
- status: **FAILED**
- max R-hat: 1.5221
- min ESS: 7
- params summarized: 1901

### issues
- R-hat for mu_league: 1.344 > 1.01
- R-hat for mu_position[1]: 1.328 > 1.01
- R-hat for mu_position[2]: 1.111 > 1.01
- ESS for mu_position[2]: 114 < 400
- R-hat for mu_position[3]: 1.091 > 1.01
- ESS for mu_position[3]: 71 < 400
- R-hat for mu_player[1]: 1.116 > 1.01
- ESS for mu_player[1]: 23 < 400
- R-hat for mu_player[2]: 1.147 > 1.01
- ESS for mu_player[2]: 18 < 400
- R-hat for mu_player[3]: 1.222 > 1.01
- ESS for mu_player[3]: 386 < 400
- R-hat for mu_player[4]: 1.214 > 1.01
- ESS for mu_player[4]: 13 < 400
- R-hat for mu_player[5]: 1.097 > 1.01
- ESS for mu_player[5]: 26 < 400
- R-hat for mu_player[6]: 1.212 > 1.01
- R-hat for mu_player[7]: 1.194 > 1.01
- R-hat for mu_player[8]: 1.269 > 1.01
- R-hat for mu_player[9]: 1.222 > 1.01
- … +3243 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 76.6%
- ✓ **bias_near_zero**: bias = -0.538
- ✓ **z_error_well_calibrated**: z-error mean=-0.25, sd=1.20
- ✓ **top_25_tier_accuracy**: top-25 overlap = 60.0%

## backtest metrics (PTS)
- train: 2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FGA
- N players: 256
- empirical OOS SD: 1.935 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 47.5%
- MAE: 2.055
- RMSE: 2.749
- bias: -0.538
- coverage 50%: 50.4%
- coverage 80%: 76.6%
- coverage 90%: 82.4%
- z-error: mean=-0.247 sd=1.201
- top-25 tier accuracy: 60.0%
- top-50 tier accuracy: 78.0%
