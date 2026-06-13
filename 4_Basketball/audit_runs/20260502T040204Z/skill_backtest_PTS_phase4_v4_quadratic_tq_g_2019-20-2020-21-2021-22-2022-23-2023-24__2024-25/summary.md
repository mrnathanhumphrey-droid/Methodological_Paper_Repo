# skill fit: backtest_PTS_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24__2024-25

- run timestamp: `20260502T040204Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 53,237
- chains: 2 × (400 warmup + 400 sampling)
- wall time: 6441.8s (107.4 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0381
- min ESS: 130
- params summarized: 905

### issues
- R-hat for mu_league: 1.014 > 1.01
- ESS for mu_league: 312 < 400
- R-hat for mu_player[13]: 1.017 > 1.01
- R-hat for mu_player[25]: 1.022 > 1.01
- R-hat for mu_player[30]: 1.011 > 1.01
- R-hat for mu_player[89]: 1.012 > 1.01
- R-hat for mu_player[90]: 1.012 > 1.01
- R-hat for mu_player[94]: 1.012 > 1.01
- R-hat for mu_player[110]: 1.016 > 1.01
- R-hat for mu_player[126]: 1.016 > 1.01
- R-hat for mu_player[142]: 1.011 > 1.01
- R-hat for mu_player[161]: 1.011 > 1.01
- R-hat for mu_player[172]: 1.018 > 1.01
- R-hat for mu_player[175]: 1.012 > 1.01
- R-hat for mu_player[177]: 1.038 > 1.01
- R-hat for mu_player[192]: 1.021 > 1.01
- R-hat for sigma_position: 1.028 > 1.01
- ESS for sigma_position: 130 < 400
- R-hat for peak_age_pos[1]: 1.013 > 1.01
- ESS for peak_age_pos[1]: 275 < 400
- … +44 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 84.9%
- ✓ **bias_near_zero**: bias = -0.178
- ✓ **z_error_well_calibrated**: z-error mean=-0.10, sd=0.96
- ✓ **top_25_tier_accuracy**: top-25 overlap = 84.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24
- test: 2024-25
- mates_usage_stat: FGA
- N players: 119
- empirical OOS SD: 2.134 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.1%
- MAE: 1.911
- RMSE: 2.384
- bias: -0.178
- coverage 50%: 50.4%
- coverage 80%: 84.9%
- coverage 90%: 90.8%
- z-error: mean=-0.096 sd=0.958
- top-25 tier accuracy: 84.0%
- top-50 tier accuracy: 86.0%
