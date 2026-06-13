# skill fit: backtest_PTS_phase4_v5_quadratic_tq_gw_2021-22-2022-23__2023-24

- run timestamp: `20260428T203655Z`
- stan model: `hierarchical_aging_quadratic_v4.stan`
- observations: 1,547
- chains: 2 × (50 warmup + 50 sampling)
- wall time: 44.0s (0.7 min)

## convergence
- status: **FAILED**
- max R-hat: 1.1439
- min ESS: 14
- params summarized: 151

### issues
- ESS for mu_league: 105 < 400
- R-hat for mu_position[1]: 1.034 > 1.01
- ESS for mu_position[1]: 70 < 400
- ESS for mu_position[2]: 99 < 400
- R-hat for mu_position[3]: 1.014 > 1.01
- ESS for mu_position[3]: 47 < 400
- R-hat for mu_player[1]: 1.010 > 1.01
- ESS for mu_player[1]: 101 < 400
- R-hat for mu_player[2]: 1.024 > 1.01
- ESS for mu_player[2]: 94 < 400
- ESS for mu_player[3]: 107 < 400
- R-hat for mu_player[4]: 1.112 > 1.01
- ESS for mu_player[4]: 14 < 400
- R-hat for mu_player[5]: 1.012 > 1.01
- ESS for mu_player[5]: 65 < 400
- ESS for mu_player[6]: 67 < 400
- R-hat for mu_player[7]: 1.048 > 1.01
- ESS for mu_player[7]: 93 < 400
- ESS for mu_player[8]: 93 < 400
- R-hat for mu_player[9]: 1.018 > 1.01
- … +210 more

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 40.0%
- ✓ **bias_near_zero**: bias = -0.893
- ✗ **z_error_well_calibrated**: z-error mean=-0.47, sd=1.38
- ✗ **top_25_tier_accuracy**: top-25 overlap = nan%

## backtest metrics (PTS)
- train: 2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 10
- empirical OOS SD: 1.330 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 10.0%
- MAE: 3.184
- RMSE: 3.552
- bias: -0.893
- coverage 50%: 10.0%
- coverage 80%: 40.0%
- coverage 90%: 70.0%
- z-error: mean=-0.473 sd=1.379
- top-25 tier accuracy: nan%
- top-50 tier accuracy: nan%
