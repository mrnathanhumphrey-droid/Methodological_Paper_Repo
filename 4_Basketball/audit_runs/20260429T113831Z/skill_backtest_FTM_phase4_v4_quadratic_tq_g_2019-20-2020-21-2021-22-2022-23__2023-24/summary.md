# skill fit: backtest_FTM_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260429T113831Z`
- stan model: `hierarchical_aging_quadratic_v3.stan`
- observations: 47,136
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 3956.4s (65.9 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0264
- min ESS: 115
- params summarized: 905

### issues
- R-hat for mu_player[1]: 1.016 > 1.01
- ESS for mu_player[12]: 362 < 400
- R-hat for mu_player[22]: 1.013 > 1.01
- R-hat for mu_player[26]: 1.012 > 1.01
- R-hat for mu_player[29]: 1.010 > 1.01
- R-hat for mu_player[35]: 1.011 > 1.01
- R-hat for mu_player[37]: 1.013 > 1.01
- R-hat for mu_player[48]: 1.013 > 1.01
- R-hat for mu_player[50]: 1.012 > 1.01
- R-hat for mu_player[61]: 1.011 > 1.01
- R-hat for mu_player[64]: 1.010 > 1.01
- R-hat for mu_player[72]: 1.012 > 1.01
- R-hat for mu_player[99]: 1.011 > 1.01
- R-hat for mu_player[114]: 1.011 > 1.01
- R-hat for mu_player[117]: 1.012 > 1.01
- R-hat for mu_player[118]: 1.011 > 1.01
- R-hat for mu_player[120]: 1.014 > 1.01
- ESS for mu_player[120]: 351 < 400
- R-hat for mu_player[128]: 1.015 > 1.01
- R-hat for mu_player[134]: 1.014 > 1.01
- … +132 more

## validation
- status: **FAILED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 81.0%
- ✓ **bias_near_zero**: bias = +0.307
- ✗ **z_error_well_calibrated**: z-error mean=+0.41, sd=0.97
- ✓ **top_25_tier_accuracy**: top-25 overlap = 68.0%

## backtest metrics (FTM)
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- mates_usage_stat: FTA
- N players: 195
- empirical OOS SD: 0.582 FTM/36
- pace coverage (train): 100.0%
- mates-usage coverage (train): 67.3%
- MAE: 0.606
- RMSE: 0.787
- bias: +0.307
- coverage 50%: 48.2%
- coverage 80%: 81.0%
- coverage 90%: 86.7%
- z-error: mean=+0.408 sd=0.972
- top-25 tier accuracy: 68.0%
- top-50 tier accuracy: 78.0%
