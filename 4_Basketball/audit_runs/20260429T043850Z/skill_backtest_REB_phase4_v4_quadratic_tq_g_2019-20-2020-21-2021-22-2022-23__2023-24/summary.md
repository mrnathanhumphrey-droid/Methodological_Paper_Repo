# skill fit: backtest_REB_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260429T043850Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 2,933
- chains: 4 × (20 warmup + 20 sampling)
- wall time: 26.8s (0.4 min)

## convergence
- status: **FAILED**
- max R-hat: 1.2195
- min ESS: 39
- params summarized: 145

### issues
- R-hat for mu_league: 1.019 > 1.01
- ESS for mu_league: 123 < 400
- R-hat for mu_position[1]: 1.036 > 1.01
- ESS for mu_position[1]: 93 < 400
- R-hat for mu_position[2]: 1.029 > 1.01
- ESS for mu_position[2]: 104 < 400
- ESS for mu_position[3]: 125 < 400
- R-hat for mu_player[1]: 1.018 > 1.01
- ESS for mu_player[1]: 84 < 400
- ESS for mu_player[2]: 125 < 400
- ESS for mu_player[3]: 84 < 400
- R-hat for mu_player[4]: 1.039 > 1.01
- ESS for mu_player[4]: 91 < 400
- R-hat for mu_player[5]: 1.056 > 1.01
- ESS for mu_player[5]: 80 < 400
- R-hat for mu_player[6]: 1.046 > 1.01
- ESS for mu_player[6]: 94 < 400
- R-hat for mu_player[7]: 1.017 > 1.01
- ESS for mu_player[7]: 95 < 400
- ESS for mu_player[8]: 130 < 400
- … +225 more

## validation
- status: **FAILED**
- ✗ **coverage_80_in_band**: 80% CI coverage = 60.0%
- ✓ **bias_near_zero**: bias = +0.003
- ✓ **z_error_well_calibrated**: z-error mean=-0.06, sd=1.03
- ✗ **top_25_tier_accuracy**: top-25 overlap = nan%

## backtest metrics (REB)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: REB
- N players: 10
- empirical OOS SD: 0.800 REB/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 20.0%
- MAE: 0.957
- RMSE: 1.258
- bias: +0.003
- coverage 50%: 40.0%
- coverage 80%: 60.0%
- coverage 90%: 70.0%
- z-error: mean=-0.056 sd=1.030
- top-25 tier accuracy: nan%
- top-50 tier accuracy: nan%
