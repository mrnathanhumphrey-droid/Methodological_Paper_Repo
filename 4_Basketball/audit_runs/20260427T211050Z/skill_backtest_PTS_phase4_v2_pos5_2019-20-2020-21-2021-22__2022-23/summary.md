# skill fit: backtest_PTS_phase4_v2_pos5_2019-20-2020-21-2021-22__2022-23

- run timestamp: `20260427T211050Z`
- stan model: `hierarchical_aging_pace_usage_v2.stan`
- observations: 34,052
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 2246.6s (37.4 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0142
- min ESS: 258
- params summarized: 945

### issues
- R-hat for mu_position[1]: 1.011 > 1.01
- R-hat for sigma_position: 1.014 > 1.01
- ESS for age_slope_player_sd: 258 < 400
- R-hat for age_slope_player_z[50]: 1.012 > 1.01
- R-hat for age_slope_player_z[86]: 1.013 > 1.01
- R-hat for age_slope_player_z[116]: 1.011 > 1.01
- R-hat for age_slope_player_z[190]: 1.011 > 1.01
- R-hat for age_slope_player[86]: 1.010 > 1.01
- R-hat for age_slope_player[148]: 1.012 > 1.01
- R-hat for rate_per_36_at_27[148]: 1.010 > 1.01
- R-hat for rate_per_36_position_at_27[1]: 1.011 > 1.01
- R-hat for age_curve_position[1,9]: 1.011 > 1.01
- R-hat for age_curve_position[1,10]: 1.012 > 1.01
- R-hat for age_curve_position[1,11]: 1.012 > 1.01
- R-hat for age_curve_position[1,12]: 1.012 > 1.01
- R-hat for age_curve_position[1,13]: 1.011 > 1.01
- R-hat for age_curve_position[1,14]: 1.011 > 1.01

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 77.9%
- ✓ **bias_near_zero**: bias = -0.069
- ✓ **z_error_well_calibrated**: z-error mean=-0.03, sd=1.19
- ✓ **top_25_tier_accuracy**: top-25 overlap = 88.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22
- test: 2022-23
- mates_usage_stat: FGA
- N players: 199
- empirical OOS SD: 1.781 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 70.3%
- MAE: 1.991
- RMSE: 2.605
- bias: -0.069
- coverage 50%: 47.2%
- coverage 80%: 77.9%
- coverage 90%: 82.4%
- z-error: mean=-0.033 sd=1.190
- top-25 tier accuracy: 88.0%
- top-50 tier accuracy: 72.0%
