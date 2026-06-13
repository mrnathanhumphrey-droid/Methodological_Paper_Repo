# skill fit: backtest_PTS_phase4_v2_pos5_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260427T194208Z`
- stan model: `hierarchical_aging_pace_usage_v2.stan`
- observations: 2,933
- chains: 2 × (50 warmup + 50 sampling)
- wall time: 57.0s (0.9 min)

## convergence
- status: **FAILED**
- max R-hat: 1.1151
- min ESS: 31
- params summarized: 185

### issues
- ESS for mu_league: 104 < 400
- ESS for mu_position[1]: 126 < 400
- ESS for mu_position[2]: 85 < 400
- ESS for mu_position[3]: 102 < 400
- ESS for mu_position[4]: 109 < 400
- R-hat for mu_position[5]: 1.018 > 1.01
- ESS for mu_position[5]: 92 < 400
- R-hat for mu_player[1]: 1.024 > 1.01
- ESS for mu_player[1]: 68 < 400
- R-hat for mu_player[2]: 1.011 > 1.01
- ESS for mu_player[2]: 96 < 400
- ESS for mu_player[3]: 106 < 400
- ESS for mu_player[4]: 96 < 400
- R-hat for mu_player[5]: 1.013 > 1.01
- ESS for mu_player[5]: 96 < 400
- R-hat for mu_player[6]: 1.027 > 1.01
- ESS for mu_player[6]: 53 < 400
- ESS for mu_player[7]: 92 < 400
- R-hat for mu_player[8]: 1.011 > 1.01
- ESS for mu_player[8]: 85 < 400
- … +231 more

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 50.0%
- ✓ **bias_near_zero**: bias = -0.825
- ✗ **z_error_well_calibrated**: z-error mean=-0.42, sd=1.66
- ✗ **top_25_tier_accuracy**: top-25 overlap = nan%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 10
- empirical OOS SD: 1.730 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 20.0%
- MAE: 3.133
- RMSE: 3.858
- bias: -0.825
- coverage 50%: 30.0%
- coverage 80%: 50.0%
- coverage 90%: 50.0%
- z-error: mean=-0.415 sd=1.661
- top-25 tier accuracy: nan%
- top-50 tier accuracy: nan%
