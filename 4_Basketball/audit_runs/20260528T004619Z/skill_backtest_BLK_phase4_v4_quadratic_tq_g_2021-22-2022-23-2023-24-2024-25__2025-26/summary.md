# skill fit: backtest_BLK_phase4_v4_quadratic_tq_g_2021-22-2022-23-2023-24-2024-25__2025-26

- run timestamp: `20260528T004619Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 85,702
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 6099.2s (101.7 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0698
- min ESS: 51
- params summarized: 1901

### issues
- R-hat for mu_player[72]: 1.010 > 1.01
- R-hat for mu_player[77]: 1.011 > 1.01
- R-hat for mu_player[96]: 1.010 > 1.01
- R-hat for mu_player[154]: 1.013 > 1.01
- R-hat for mu_player[225]: 1.023 > 1.01
- R-hat for mu_player[233]: 1.012 > 1.01
- R-hat for mu_player[254]: 1.016 > 1.01
- R-hat for mu_player[259]: 1.010 > 1.01
- R-hat for mu_player[260]: 1.011 > 1.01
- R-hat for mu_player[285]: 1.013 > 1.01
- R-hat for mu_player[313]: 1.014 > 1.01
- R-hat for mu_player[323]: 1.013 > 1.01
- R-hat for mu_player[379]: 1.016 > 1.01
- R-hat for mu_player[388]: 1.011 > 1.01
- R-hat for mu_player[417]: 1.010 > 1.01
- R-hat for peak_age_pos[3]: 1.011 > 1.01
- R-hat for sigma_age_player: 1.070 > 1.01
- ESS for sigma_age_player: 51 < 400
- R-hat for age_tilt_player_z[47]: 1.014 > 1.01
- R-hat for age_tilt_player_z[57]: 1.012 > 1.01
- … +210 more

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 82.4%
- ✓ **bias_near_zero**: bias = +0.052
- ✓ **z_error_well_calibrated**: z-error mean=+0.21, sd=1.08
- ✓ **top_25_tier_accuracy**: top-25 overlap = 80.0%

## backtest metrics (BLK)
- train: 2021-22,2022-23,2023-24,2024-25
- test: 2025-26
- mates_usage_stat: BLK
- N players: 256
- empirical OOS SD: 0.177 BLK/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 47.5%
- MAE: 0.187
- RMSE: 0.271
- bias: +0.052
- coverage 50%: 52.0%
- coverage 80%: 82.4%
- coverage 90%: 85.5%
- z-error: mean=+0.212 sd=1.082
- top-25 tier accuracy: 80.0%
- top-50 tier accuracy: 68.0%
