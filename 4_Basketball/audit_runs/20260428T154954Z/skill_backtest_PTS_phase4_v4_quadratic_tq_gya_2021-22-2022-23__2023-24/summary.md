# skill fit: backtest_PTS_phase4_v4_quadratic_tq_gya_2021-22-2022-23__2023-24

- run timestamp: `20260428T154954Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 1,547
- chains: 2 × (50 warmup + 50 sampling)
- wall time: 54.6s (0.9 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0797
- min ESS: 27
- params summarized: 145

### issues
- R-hat for mu_league: 1.038 > 1.01
- ESS for mu_league: 115 < 400
- ESS for mu_position[1]: 115 < 400
- ESS for mu_position[2]: 79 < 400
- ESS for mu_position[3]: 119 < 400
- R-hat for mu_player[1]: 1.014 > 1.01
- ESS for mu_player[1]: 89 < 400
- ESS for mu_player[2]: 92 < 400
- R-hat for mu_player[3]: 1.017 > 1.01
- ESS for mu_player[3]: 46 < 400
- R-hat for mu_player[4]: 1.029 > 1.01
- ESS for mu_player[4]: 56 < 400
- ESS for mu_player[5]: 110 < 400
- ESS for mu_player[6]: 73 < 400
- R-hat for mu_player[7]: 1.058 > 1.01
- ESS for mu_player[7]: 100 < 400
- ESS for mu_player[8]: 89 < 400
- ESS for mu_player[9]: 109 < 400
- R-hat for mu_player[10]: 1.036 > 1.01
- ESS for mu_player[10]: 104 < 400
- … +189 more

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 30.0%
- ✓ **bias_near_zero**: bias = -0.922
- ✗ **z_error_well_calibrated**: z-error mean=-0.48, sd=1.38
- ✗ **top_25_tier_accuracy**: top-25 overlap = nan%

## backtest metrics (PTS)
- train: 2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 10
- empirical OOS SD: 1.330 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 10.0%
- MAE: 3.249
- RMSE: 3.609
- bias: -0.922
- coverage 50%: 10.0%
- coverage 80%: 30.0%
- coverage 90%: 50.0%
- z-error: mean=-0.483 sd=1.383
- top-25 tier accuracy: nan%
- top-50 tier accuracy: nan%
