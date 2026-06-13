# skill fit: backtest_FTM_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260504T131407Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 64,126
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 4258.4s (71.0 min)

## convergence
- status: **FAILED**
- max R-hat: 1.2788
- min ESS: 12
- params summarized: 905

### issues
- R-hat for mu_league: 1.033 > 1.01
- ESS for mu_league: 147 < 400
- R-hat for mu_position[1]: 1.054 > 1.01
- ESS for mu_position[1]: 110 < 400
- R-hat for mu_position[2]: 1.070 > 1.01
- ESS for mu_position[2]: 39 < 400
- R-hat for mu_position[3]: 1.089 > 1.01
- ESS for mu_position[3]: 31 < 400
- R-hat for mu_player[1]: 1.048 > 1.01
- ESS for mu_player[1]: 70 < 400
- R-hat for mu_player[2]: 1.221 > 1.01
- R-hat for mu_player[3]: 1.196 > 1.01
- ESS for mu_player[3]: 14 < 400
- R-hat for mu_player[4]: 1.157 > 1.01
- R-hat for mu_player[5]: 1.070 > 1.01
- ESS for mu_player[5]: 226 < 400
- R-hat for mu_player[6]: 1.250 > 1.01
- R-hat for mu_player[7]: 1.171 > 1.01
- ESS for mu_player[7]: 16 < 400
- R-hat for mu_player[8]: 1.080 > 1.01
- … +1531 more

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 94.7%
- ✓ **bias_near_zero**: bias = -0.168
- ✗ **z_error_well_calibrated**: z-error mean=-0.22, sd=0.61
- ✓ **top_25_tier_accuracy**: top-25 overlap = 88.0%

## backtest metrics (FTM)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FTA
- N players: 133
- empirical OOS SD: 0.643 FTM/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.358
- RMSE: 0.506
- bias: -0.168
- coverage 50%: 79.7%
- coverage 80%: 94.7%
- coverage 90%: 97.0%
- z-error: mean=-0.217 sd=0.605
- top-25 tier accuracy: 88.0%
- top-50 tier accuracy: 86.0%
