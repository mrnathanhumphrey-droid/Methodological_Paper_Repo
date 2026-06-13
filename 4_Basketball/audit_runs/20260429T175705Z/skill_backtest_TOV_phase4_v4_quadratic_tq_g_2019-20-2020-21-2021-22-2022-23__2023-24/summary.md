# skill fit: backtest_TOV_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260429T175705Z`
- stan model: `hierarchical_aging_quadratic_v5.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3312.2s (55.2 min)

## convergence
- status: **FAILED**
- max R-hat: 1.1294
- min ESS: 20
- params summarized: 907

### issues
- R-hat for mu_league: 1.047 > 1.01
- ESS for mu_league: 62 < 400
- R-hat for mu_position[1]: 1.121 > 1.01
- ESS for mu_position[1]: 22 < 400
- R-hat for mu_player[1]: 1.016 > 1.01
- ESS for mu_player[1]: 313 < 400
- R-hat for mu_player[2]: 1.069 > 1.01
- ESS for mu_player[2]: 41 < 400
- R-hat for mu_player[3]: 1.012 > 1.01
- ESS for mu_player[3]: 215 < 400
- R-hat for mu_player[4]: 1.016 > 1.01
- ESS for mu_player[4]: 366 < 400
- R-hat for mu_player[5]: 1.017 > 1.01
- ESS for mu_player[5]: 216 < 400
- R-hat for mu_player[6]: 1.040 > 1.01
- ESS for mu_player[6]: 102 < 400
- R-hat for mu_player[7]: 1.019 > 1.01
- R-hat for mu_player[8]: 1.032 > 1.01
- ESS for mu_player[8]: 130 < 400
- R-hat for mu_player[9]: 1.023 > 1.01
- … +1240 more

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 80.0%
- ✓ **bias_near_zero**: bias = +0.125
- ✗ **z_error_well_calibrated**: z-error mean=+0.32, sd=1.06
- ✓ **top_25_tier_accuracy**: top-25 overlap = 68.0%

## backtest metrics (TOV)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: TOV
- N players: 195
- empirical OOS SD: 0.312 TOV/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 0.324
- RMSE: 0.415
- bias: +0.125
- coverage 50%: 44.6%
- coverage 80%: 80.0%
- coverage 90%: 87.2%
- z-error: mean=+0.320 sd=1.062
- top-25 tier accuracy: 68.0%
- top-50 tier accuracy: 82.0%
