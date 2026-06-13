# skill fit: backtest_PTS_phase4_v3_quadratic_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260428T021017Z`
- stan model: `hierarchical_aging_quadratic_v1.stan`
- observations: 2,933
- chains: 2 × (50 warmup + 50 sampling)
- wall time: 108.0s (1.8 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0885
- min ESS: 22
- params summarized: 140

### issues
- R-hat for mu_league: 1.048 > 1.01
- ESS for mu_league: 101 < 400
- ESS for mu_position[1]: 128 < 400
- R-hat for mu_position[2]: 1.049 > 1.01
- ESS for mu_position[2]: 63 < 400
- R-hat for mu_position[3]: 1.046 > 1.01
- ESS for mu_position[3]: 53 < 400
- ESS for mu_player[1]: 92 < 400
- R-hat for mu_player[2]: 1.014 > 1.01
- ESS for mu_player[2]: 84 < 400
- R-hat for mu_player[3]: 1.013 > 1.01
- ESS for mu_player[3]: 120 < 400
- ESS for mu_player[4]: 114 < 400
- ESS for mu_player[5]: 79 < 400
- ESS for mu_player[6]: 106 < 400
- ESS for mu_player[7]: 90 < 400
- ESS for mu_player[8]: 83 < 400
- R-hat for mu_player[9]: 1.028 > 1.01
- ESS for mu_player[9]: 66 < 400
- ESS for mu_player[10]: 141 < 400
- … +208 more

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 50.0%
- ✗ **bias_near_zero**: bias = -1.099
- ✗ **z_error_well_calibrated**: z-error mean=-0.61, sd=1.60
- ✗ **top_25_tier_accuracy**: top-25 overlap = nan%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 10
- empirical OOS SD: 1.730 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 20.0%
- MAE: 3.098
- RMSE: 3.702
- bias: -1.099
- coverage 50%: 20.0%
- coverage 80%: 50.0%
- coverage 90%: 80.0%
- z-error: mean=-0.611 sd=1.596
- top-25 tier accuracy: nan%
- top-50 tier accuracy: nan%
