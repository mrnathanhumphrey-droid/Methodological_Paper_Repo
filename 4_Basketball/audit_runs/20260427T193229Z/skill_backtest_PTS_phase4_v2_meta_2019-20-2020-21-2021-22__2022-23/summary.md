# skill fit: backtest_PTS_phase4_v2_meta_2019-20-2020-21-2021-22__2022-23

- run timestamp: `20260427T193229Z`
- stan model: `hierarchical_aging_pace_usage_v2.stan`
- observations: 34,052
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 2373.9s (39.6 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0228
- min ESS: 181
- params summarized: 891

### issues
- R-hat for mu_player[4]: 1.010 > 1.01
- R-hat for mu_player[30]: 1.010 > 1.01
- R-hat for mu_player[31]: 1.019 > 1.01
- R-hat for mu_player[42]: 1.011 > 1.01
- R-hat for mu_player[83]: 1.012 > 1.01
- R-hat for mu_player[93]: 1.011 > 1.01
- R-hat for mu_player[146]: 1.010 > 1.01
- R-hat for mu_player[181]: 1.013 > 1.01
- R-hat for mu_player[185]: 1.010 > 1.01
- R-hat for mu_player[193]: 1.010 > 1.01
- R-hat for mu_player[194]: 1.011 > 1.01
- ESS for sigma_position: 271 < 400
- R-hat for age_slope_player_sd: 1.023 > 1.01
- ESS for age_slope_player_sd: 181 < 400
- R-hat for age_slope_player_z[25]: 1.011 > 1.01
- R-hat for age_slope_player_z[108]: 1.011 > 1.01
- R-hat for age_slope_player_z[146]: 1.010 > 1.01
- R-hat for age_slope_player_z[150]: 1.011 > 1.01
- R-hat for age_slope_player_z[181]: 1.013 > 1.01
- R-hat for age_slope_player_z[185]: 1.011 > 1.01
- … +25 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 77.4%
- ✓ **bias_near_zero**: bias = -0.096
- ✓ **z_error_well_calibrated**: z-error mean=-0.04, sd=1.19
- ✓ **top_25_tier_accuracy**: top-25 overlap = 88.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22
- test: 2022-23
- mates_usage_stat: FGA
- N players: 199
- empirical OOS SD: 1.781 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 70.3%
- MAE: 1.977
- RMSE: 2.613
- bias: -0.096
- coverage 50%: 49.2%
- coverage 80%: 77.4%
- coverage 90%: 82.4%
- z-error: mean=-0.044 sd=1.192
- top-25 tier accuracy: 88.0%
- top-50 tier accuracy: 70.0%
