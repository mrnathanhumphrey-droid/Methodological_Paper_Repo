# skill fit: backtest_FGM_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260511T121835Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 63,455
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 5231.8s (87.2 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0354
- min ESS: 164
- params summarized: 905

### issues
- R-hat for mu_league: 1.011 > 1.01
- R-hat for mu_position[1]: 1.014 > 1.01
- R-hat for mu_position[2]: 1.011 > 1.01
- R-hat for mu_player[45]: 1.011 > 1.01
- R-hat for mu_player[47]: 1.014 > 1.01
- R-hat for mu_player[68]: 1.011 > 1.01
- R-hat for mu_player[97]: 1.011 > 1.01
- R-hat for mu_player[98]: 1.012 > 1.01
- R-hat for mu_player[102]: 1.014 > 1.01
- R-hat for mu_player[110]: 1.011 > 1.01
- R-hat for mu_player[120]: 1.011 > 1.01
- R-hat for mu_player[129]: 1.020 > 1.01
- R-hat for mu_player[138]: 1.011 > 1.01
- R-hat for mu_player[157]: 1.010 > 1.01
- R-hat for mu_player[159]: 1.011 > 1.01
- R-hat for mu_player[161]: 1.011 > 1.01
- ESS for mu_player[161]: 377 < 400
- R-hat for mu_player[173]: 1.011 > 1.01
- R-hat for mu_player[196]: 1.012 > 1.01
- R-hat for sigma_position: 1.035 > 1.01
- … +94 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 83.8%
- ✓ **bias_near_zero**: bias = -0.186
- ✓ **z_error_well_calibrated**: z-error mean=-0.20, sd=1.07
- ✓ **top_25_tier_accuracy**: top-25 overlap = 80.0%

## backtest metrics (FGM)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: FGA
- N players: 105
- empirical OOS SD: 0.822 FGM/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.5%
- MAE: 0.774
- RMSE: 1.016
- bias: -0.186
- coverage 50%: 46.7%
- coverage 80%: 83.8%
- coverage 90%: 88.6%
- z-error: mean=-0.200 sd=1.074
- top-25 tier accuracy: 80.0%
- top-50 tier accuracy: 86.0%
