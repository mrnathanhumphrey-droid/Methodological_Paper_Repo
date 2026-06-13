# skill fit: backtest_FGM_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260430T035452Z`
- stan model: `hierarchical_aging_quadratic_v3_pp_phi.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3892.6s (64.9 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0279
- min ESS: 290
- params summarized: 910

### issues
- R-hat for mu_position[1]: 1.012 > 1.01
- R-hat for mu_player[35]: 1.013 > 1.01
- R-hat for mu_player[144]: 1.012 > 1.01
- R-hat for mu_player[178]: 1.013 > 1.01
- R-hat for sigma_position: 1.021 > 1.01
- ESS for sigma_position: 355 < 400
- R-hat for peak_age_pos[1]: 1.028 > 1.01
- ESS for peak_age_pos[1]: 290 < 400
- R-hat for beta_age_pos[1]: 1.022 > 1.01
- ESS for beta_age_pos[1]: 295 < 400
- R-hat for sigma_age_player: 1.015 > 1.01
- ESS for sigma_age_player: 309 < 400
- R-hat for age_tilt_player_z[132]: 1.012 > 1.01
- R-hat for age_tilt_player_z[144]: 1.010 > 1.01
- R-hat for age_tilt_player[2]: 1.010 > 1.01
- R-hat for age_tilt_player[3]: 1.011 > 1.01
- R-hat for age_tilt_player[8]: 1.018 > 1.01
- R-hat for age_tilt_player[10]: 1.015 > 1.01
- R-hat for age_tilt_player[15]: 1.010 > 1.01
- R-hat for age_tilt_player[16]: 1.011 > 1.01
- … +15 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 82.1%
- ✓ **bias_near_zero**: bias = +0.181
- ✓ **z_error_well_calibrated**: z-error mean=+0.22, sd=1.02
- ✓ **top_25_tier_accuracy**: top-25 overlap = 64.0%

## backtest metrics (FGM)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 195
- empirical OOS SD: 0.702 FGM/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 0.703
- RMSE: 0.873
- bias: +0.181
- coverage 50%: 49.2%
- coverage 80%: 82.1%
- coverage 90%: 87.7%
- z-error: mean=+0.217 sd=1.018
- top-25 tier accuracy: 64.0%
- top-50 tier accuracy: 82.0%
