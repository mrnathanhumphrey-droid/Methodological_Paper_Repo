# skill fit: backtest_STL_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260511T090151Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 63,455
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3017.7s (50.3 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0252
- min ESS: 191
- params summarized: 905

### issues
- R-hat for mu_position[1]: 1.018 > 1.01
- ESS for mu_position[1]: 204 < 400
- R-hat for mu_position[2]: 1.014 > 1.01
- R-hat for mu_position[3]: 1.021 > 1.01
- ESS for mu_position[3]: 352 < 400
- R-hat for mu_player[8]: 1.011 > 1.01
- R-hat for mu_player[11]: 1.012 > 1.01
- ESS for mu_player[11]: 311 < 400
- R-hat for mu_player[24]: 1.012 > 1.01
- R-hat for mu_player[41]: 1.010 > 1.01
- R-hat for mu_player[51]: 1.011 > 1.01
- R-hat for mu_player[62]: 1.012 > 1.01
- R-hat for mu_player[78]: 1.013 > 1.01
- R-hat for mu_player[132]: 1.012 > 1.01
- R-hat for mu_player[138]: 1.013 > 1.01
- R-hat for mu_player[141]: 1.015 > 1.01
- R-hat for mu_player[145]: 1.010 > 1.01
- R-hat for mu_player[165]: 1.010 > 1.01
- R-hat for mu_player[166]: 1.010 > 1.01
- R-hat for mu_player[167]: 1.010 > 1.01
- … +112 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 83.8%
- ✓ **bias_near_zero**: bias = -0.053
- ✓ **z_error_well_calibrated**: z-error mean=-0.22, sd=0.98
- ✓ **top_25_tier_accuracy**: top-25 overlap = 68.0%

## backtest metrics (STL)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: STL
- N players: 105
- empirical OOS SD: 0.212 STL/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.197
- RMSE: 0.248
- bias: -0.053
- coverage 50%: 52.4%
- coverage 80%: 83.8%
- coverage 90%: 86.7%
- z-error: mean=-0.221 sd=0.977
- top-25 tier accuracy: 68.0%
- top-50 tier accuracy: 78.0%
