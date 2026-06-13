# skill fit: backtest_AST_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24__2024-25

- run timestamp: `20260502T062901Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 53,237
- chains: 2 × (400 warmup + 400 sampling)
- wall time: 4270.2s (71.2 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0186
- min ESS: 186
- params summarized: 905

### issues
- ESS for mu_position[2]: 362 < 400
- R-hat for mu_player[5]: 1.011 > 1.01
- R-hat for mu_player[17]: 1.010 > 1.01
- R-hat for mu_player[41]: 1.013 > 1.01
- R-hat for mu_player[42]: 1.011 > 1.01
- R-hat for mu_player[54]: 1.010 > 1.01
- R-hat for mu_player[55]: 1.015 > 1.01
- R-hat for mu_player[120]: 1.019 > 1.01
- R-hat for mu_player[146]: 1.011 > 1.01
- R-hat for mu_player[191]: 1.014 > 1.01
- ESS for peak_age_pos[1]: 195 < 400
- ESS for peak_age_pos[2]: 316 < 400
- ESS for gamma_pos[1]: 359 < 400
- ESS for beta_age_pos[1]: 186 < 400
- R-hat for beta_age_pos[2]: 1.017 > 1.01
- ESS for beta_age_pos[2]: 223 < 400
- ESS for beta_age_pos[3]: 309 < 400
- R-hat for sigma_age_player: 1.013 > 1.01
- ESS for sigma_age_player: 207 < 400
- R-hat for age_tilt_player_z[38]: 1.012 > 1.01
- … +28 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 83.2%
- ✓ **bias_near_zero**: bias = +0.140
- ✓ **z_error_well_calibrated**: z-error mean=+0.17, sd=1.06
- ✓ **top_25_tier_accuracy**: top-25 overlap = 76.0%

## backtest metrics (AST)
- train: 2019-20,2020-21,2021-22,2022-23,2023-24
- test: 2024-25
- mates_usage_stat: AST
- N players: 119
- empirical OOS SD: 0.665 AST/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 46.1%
- MAE: 0.702
- RMSE: 0.999
- bias: +0.140
- coverage 50%: 47.1%
- coverage 80%: 83.2%
- coverage 90%: 88.2%
- z-error: mean=+0.166 sd=1.063
- top-25 tier accuracy: 76.0%
- top-50 tier accuracy: 86.0%
