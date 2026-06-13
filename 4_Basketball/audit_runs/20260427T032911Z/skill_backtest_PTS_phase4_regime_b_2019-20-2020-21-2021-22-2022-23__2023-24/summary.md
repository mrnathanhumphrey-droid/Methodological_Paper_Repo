# skill fit: backtest_PTS_phase4_regime_b_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260427T032911Z`
- stan model: `hierarchical_aging_pace_usage_v1.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3032.2s (50.5 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0175
- min ESS: 263
- params summarized: 891

### issues
- R-hat for mu_player[115]: 1.013 > 1.01
- R-hat for mu_player[124]: 1.014 > 1.01
- R-hat for mu_player[174]: 1.014 > 1.01
- R-hat for mu_player[184]: 1.018 > 1.01
- ESS for sigma_position: 263 < 400
- R-hat for age_slope_player_z[75]: 1.010 > 1.01
- R-hat for age_slope_player_z[152]: 1.010 > 1.01
- R-hat for age_slope_player_z[184]: 1.015 > 1.01
- R-hat for age_slope_player[21]: 1.010 > 1.01
- R-hat for age_slope_player[26]: 1.011 > 1.01
- R-hat for age_slope_player[32]: 1.011 > 1.01
- R-hat for age_slope_player[48]: 1.010 > 1.01
- R-hat for age_slope_player[75]: 1.010 > 1.01
- R-hat for age_slope_player[152]: 1.011 > 1.01
- R-hat for age_slope_player[184]: 1.017 > 1.01
- R-hat for pts_per_36_at_27[115]: 1.012 > 1.01
- R-hat for pts_per_36_at_27[124]: 1.014 > 1.01
- R-hat for pts_per_36_at_27[174]: 1.014 > 1.01
- R-hat for pts_per_36_at_27[184]: 1.016 > 1.01

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 75.4% (target 70-90%)
- ✗ **bias_near_zero**: bias = +1.095 (target |b| < 1.0 PTS/36)
- ✗ **z_error_well_calibrated**: z-error mean=+0.45, sd=1.13
- ✓ **top_25_tier_accuracy**: top-25 overlap = 80.0% (target ≥ 50%)

## backtest metrics
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- N players: 195
- empirical out-of-sample SD: 1.974 pts/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 2.260
- RMSE: 2.826
- bias: +1.095
- coverage 50%: 40.5%
- coverage 80%: 75.4%
- coverage 90%: 83.1%
- z-error: mean=+0.453 sd=1.127
- top-25 tier accuracy: 80.0%
- top-50 tier accuracy: 84.0%
