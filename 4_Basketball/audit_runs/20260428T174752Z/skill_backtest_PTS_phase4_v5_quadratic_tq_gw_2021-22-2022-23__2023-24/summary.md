# skill fit: backtest_PTS_phase4_v5_quadratic_tq_gw_2021-22-2022-23__2023-24

- run timestamp: `20260428T174752Z`
- stan model: `hierarchical_aging_quadratic_v4.stan`
- observations: 1,547
- chains: 2 × (50 warmup + 50 sampling)
- wall time: 70.2s (1.2 min)

## convergence
- status: **FAILED**
- max R-hat: 1.1044
- min ESS: 29
- params summarized: 151

### issues
- ESS for mu_league: 200 < 400
- ESS for mu_position[1]: 86 < 400
- ESS for mu_position[2]: 81 < 400
- R-hat for mu_position[3]: 1.029 > 1.01
- ESS for mu_position[3]: 107 < 400
- ESS for mu_player[1]: 88 < 400
- R-hat for mu_player[2]: 1.019 > 1.01
- ESS for mu_player[2]: 70 < 400
- R-hat for mu_player[3]: 1.015 > 1.01
- ESS for mu_player[3]: 96 < 400
- ESS for mu_player[4]: 54 < 400
- ESS for mu_player[5]: 104 < 400
- R-hat for mu_player[6]: 1.020 > 1.01
- ESS for mu_player[6]: 50 < 400
- R-hat for mu_player[7]: 1.029 > 1.01
- ESS for mu_player[7]: 179 < 400
- R-hat for mu_player[8]: 1.024 > 1.01
- ESS for mu_player[8]: 77 < 400
- ESS for mu_player[9]: 112 < 400
- R-hat for mu_player[10]: 1.022 > 1.01
- … +231 more

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 70.0%
- ✓ **bias_near_zero**: bias = -0.476
- ✓ **z_error_well_calibrated**: z-error mean=-0.13, sd=1.07
- ✗ **top_25_tier_accuracy**: top-25 overlap = nan%

## backtest metrics (PTS)
- train: 2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 10
- empirical OOS SD: 1.330 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 10.0%
- MAE: 2.520
- RMSE: 2.967
- bias: -0.476
- coverage 50%: 30.0%
- coverage 80%: 70.0%
- coverage 90%: 80.0%
- z-error: mean=-0.126 sd=1.074
- top-25 tier accuracy: nan%
- top-50 tier accuracy: nan%
