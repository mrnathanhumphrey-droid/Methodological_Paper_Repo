# skill fit: backtest_PTS_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260429T134653Z`
- stan model: `hierarchical_aging_quadratic_v5.stan`
- observations: 4,336
- chains: 4 × (20 warmup + 20 sampling)
- wall time: 80.5s (1.3 min)

## convergence
- status: **FAILED**
- max R-hat: 1.2992
- min ESS: 14
- params summarized: 167

### issues
- R-hat for mu_league: 1.156 > 1.01
- ESS for mu_league: 93 < 400
- R-hat for mu_position[1]: 1.019 > 1.01
- ESS for mu_position[1]: 151 < 400
- ESS for mu_position[2]: 68 < 400
- R-hat for mu_position[3]: 1.055 > 1.01
- ESS for mu_position[3]: 59 < 400
- R-hat for mu_player[1]: 1.158 > 1.01
- ESS for mu_player[1]: 152 < 400
- R-hat for mu_player[2]: 1.077 > 1.01
- ESS for mu_player[2]: 37 < 400
- ESS for mu_player[3]: 147 < 400
- R-hat for mu_player[4]: 1.088 > 1.01
- ESS for mu_player[4]: 79 < 400
- R-hat for mu_player[5]: 1.064 > 1.01
- ESS for mu_player[5]: 48 < 400
- R-hat for mu_player[6]: 1.154 > 1.01
- ESS for mu_player[6]: 26 < 400
- R-hat for mu_player[7]: 1.084 > 1.01
- ESS for mu_player[7]: 39 < 400
- … +255 more

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 100.0%
- ✓ **bias_near_zero**: bias = +0.219
- ✗ **z_error_well_calibrated**: z-error mean=+0.05, sd=0.66
- ✗ **top_25_tier_accuracy**: top-25 overlap = nan%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 15
- empirical OOS SD: 1.717 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 21.7%
- MAE: 1.336
- RMSE: 1.607
- bias: +0.219
- coverage 50%: 66.7%
- coverage 80%: 100.0%
- coverage 90%: 100.0%
- z-error: mean=+0.050 sd=0.661
- top-25 tier accuracy: nan%
- top-50 tier accuracy: nan%
