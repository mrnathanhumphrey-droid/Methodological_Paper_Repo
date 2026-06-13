# skill fit: backtest_FTA_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260429T184541Z`
- stan model: `hierarchical_aging_quadratic_v3_pp_phi.stan`
- observations: 4,336
- chains: 4 × (20 warmup + 20 sampling)
- wall time: 38.1s (0.6 min)

## convergence
- status: **FAILED**
- max R-hat: 1.1802
- min ESS: 38
- params summarized: 170

### issues
- R-hat for mu_league: 1.051 > 1.01
- ESS for mu_league: 130 < 400
- ESS for mu_position[1]: 152 < 400
- ESS for mu_position[2]: 121 < 400
- R-hat for mu_position[3]: 1.015 > 1.01
- ESS for mu_position[3]: 74 < 400
- R-hat for mu_player[1]: 1.058 > 1.01
- ESS for mu_player[1]: 61 < 400
- R-hat for mu_player[2]: 1.061 > 1.01
- ESS for mu_player[2]: 55 < 400
- ESS for mu_player[3]: 102 < 400
- ESS for mu_player[4]: 123 < 400
- R-hat for mu_player[5]: 1.035 > 1.01
- ESS for mu_player[5]: 93 < 400
- R-hat for mu_player[6]: 1.062 > 1.01
- ESS for mu_player[6]: 65 < 400
- ESS for mu_player[7]: 109 < 400
- ESS for mu_player[8]: 152 < 400
- R-hat for mu_player[9]: 1.179 > 1.01
- ESS for mu_player[9]: 112 < 400
- … +269 more

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 60.0%
- ✓ **bias_near_zero**: bias = +0.210
- ✗ **z_error_well_calibrated**: z-error mean=+0.16, sd=1.66
- ✗ **top_25_tier_accuracy**: top-25 overlap = nan%

## backtest metrics (FTA)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FTA
- N players: 15
- empirical OOS SD: 0.576 FTA/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 21.7%
- MAE: 1.289
- RMSE: 1.722
- bias: +0.210
- coverage 50%: 33.3%
- coverage 80%: 60.0%
- coverage 90%: 66.7%
- z-error: mean=+0.164 sd=1.662
- top-25 tier accuracy: nan%
- top-50 tier accuracy: nan%
