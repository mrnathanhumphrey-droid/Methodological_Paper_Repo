# skill fit: backtest_FTA_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260430T072413Z`
- stan model: `hierarchical_aging_quadratic_v3_pp_phi.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3732.2s (62.2 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0186
- min ESS: 173
- params summarized: 910

### issues
- ESS for mu_position[1]: 303 < 400
- R-hat for mu_player[76]: 1.011 > 1.01
- R-hat for mu_player[86]: 1.013 > 1.01
- ESS for sigma_position: 292 < 400
- R-hat for peak_age_pos[1]: 1.011 > 1.01
- ESS for peak_age_pos[1]: 206 < 400
- ESS for beta_age_pos[1]: 212 < 400
- R-hat for sigma_age_player: 1.019 > 1.01
- ESS for sigma_age_player: 173 < 400
- R-hat for age_tilt_player_z[57]: 1.012 > 1.01
- R-hat for age_tilt_player_z[86]: 1.011 > 1.01
- R-hat for age_tilt_player_z[161]: 1.011 > 1.01
- R-hat for age_tilt_player_z[185]: 1.010 > 1.01
- ESS for age_tilt_player[30]: 369 < 400
- R-hat for age_tilt_player[47]: 1.010 > 1.01
- ESS for age_tilt_player[47]: 364 < 400
- R-hat for age_tilt_player[89]: 1.011 > 1.01
- R-hat for age_tilt_player[97]: 1.010 > 1.01
- R-hat for age_tilt_player[120]: 1.012 > 1.01
- ESS for age_tilt_player[120]: 322 < 400
- … +3 more

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 81.5%
- ✓ **bias_near_zero**: bias = +0.379
- ✗ **z_error_well_calibrated**: z-error mean=+0.42, sd=0.95
- ✓ **top_25_tier_accuracy**: top-25 overlap = 72.0%

## backtest metrics (FTA)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FTA
- N players: 195
- empirical OOS SD: 0.699 FTA/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 0.726
- RMSE: 0.930
- bias: +0.379
- coverage 50%: 48.7%
- coverage 80%: 81.5%
- coverage 90%: 87.2%
- z-error: mean=+0.418 sd=0.949
- top-25 tier accuracy: 72.0%
- top-50 tier accuracy: 80.0%
