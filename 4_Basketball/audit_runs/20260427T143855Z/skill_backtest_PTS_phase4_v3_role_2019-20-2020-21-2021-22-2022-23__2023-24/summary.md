# skill fit: backtest_PTS_phase4_v3_role_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260427T143855Z`
- stan model: `hierarchical_aging_pace_usage_v3.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3930.2s (65.5 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0149
- min ESS: 242
- params summarized: 893

### issues
- R-hat for mu_player[52]: 1.015 > 1.01
- R-hat for mu_player[110]: 1.012 > 1.01
- R-hat for mu_player[168]: 1.014 > 1.01
- R-hat for mu_player[184]: 1.012 > 1.01
- R-hat for sigma_position: 1.013 > 1.01
- ESS for sigma_position: 242 < 400
- R-hat for age_slope_player_z[13]: 1.011 > 1.01
- R-hat for age_slope_player_z[30]: 1.011 > 1.01
- R-hat for age_slope_player_z[35]: 1.010 > 1.01
- R-hat for age_slope_player_z[44]: 1.011 > 1.01
- R-hat for age_slope_player_z[77]: 1.012 > 1.01
- R-hat for age_slope_player_z[168]: 1.011 > 1.01
- R-hat for age_slope_player[62]: 1.011 > 1.01
- R-hat for age_slope_player[77]: 1.011 > 1.01
- R-hat for age_slope_player[168]: 1.014 > 1.01
- R-hat for rate_per_36_at_27[52]: 1.015 > 1.01
- R-hat for rate_per_36_at_27[110]: 1.012 > 1.01
- R-hat for rate_per_36_at_27[168]: 1.014 > 1.01
- R-hat for rate_per_36_at_27[184]: 1.011 > 1.01

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 82.1%
- ✓ **bias_near_zero**: bias = +0.805
- ✗ **z_error_well_calibrated**: z-error mean=+0.32, sd=1.01
- ✓ **top_25_tier_accuracy**: top-25 overlap = 72.0%

## backtest metrics (PTS)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FGA
- N players: 195
- empirical OOS SD: 1.974 PTS/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 2.061
- RMSE: 2.561
- bias: +0.805
- coverage 50%: 43.6%
- coverage 80%: 82.1%
- coverage 90%: 86.7%
- z-error: mean=+0.324 sd=1.009
- top-25 tier accuracy: 72.0%
- top-50 tier accuracy: 80.0%
