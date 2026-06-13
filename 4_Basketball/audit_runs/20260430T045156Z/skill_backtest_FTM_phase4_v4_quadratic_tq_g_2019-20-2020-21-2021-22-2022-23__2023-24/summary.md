# skill fit: backtest_FTM_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260430T045156Z`
- stan model: `hierarchical_aging_quadratic_v3_pp_phi.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3417.6s (57.0 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0259
- min ESS: 181
- params summarized: 910

### issues
- R-hat for mu_player[81]: 1.017 > 1.01
- R-hat for mu_player[88]: 1.011 > 1.01
- R-hat for mu_player[91]: 1.012 > 1.01
- R-hat for mu_player[184]: 1.011 > 1.01
- R-hat for sigma_position: 1.020 > 1.01
- ESS for sigma_position: 280 < 400
- R-hat for peak_age_pos[2]: 1.014 > 1.01
- R-hat for beta_age_pos[2]: 1.012 > 1.01
- R-hat for sigma_age_player: 1.026 > 1.01
- ESS for sigma_age_player: 181 < 400
- R-hat for age_tilt_player_z[32]: 1.012 > 1.01
- R-hat for age_tilt_player_z[81]: 1.012 > 1.01
- R-hat for age_tilt_player_z[109]: 1.010 > 1.01
- R-hat for age_tilt_player_z[120]: 1.011 > 1.01
- R-hat for age_tilt_player_z[182]: 1.011 > 1.01
- R-hat for age_tilt_player_z[183]: 1.012 > 1.01
- R-hat for phi[2]: 1.019 > 1.01
- R-hat for age_tilt_player[131]: 1.010 > 1.01
- R-hat for age_tilt_player[143]: 1.011 > 1.01
- R-hat for age_tilt_player[155]: 1.011 > 1.01
- … +6 more

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 81.5%
- ✓ **bias_near_zero**: bias = +0.304
- ✗ **z_error_well_calibrated**: z-error mean=+0.40, sd=0.97
- ✓ **top_25_tier_accuracy**: top-25 overlap = 68.0%

## backtest metrics (FTM)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FTA
- N players: 195
- empirical OOS SD: 0.582 FTM/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 0.605
- RMSE: 0.783
- bias: +0.304
- coverage 50%: 48.7%
- coverage 80%: 81.5%
- coverage 90%: 86.7%
- z-error: mean=+0.404 sd=0.970
- top-25 tier accuracy: 68.0%
- top-50 tier accuracy: 78.0%
