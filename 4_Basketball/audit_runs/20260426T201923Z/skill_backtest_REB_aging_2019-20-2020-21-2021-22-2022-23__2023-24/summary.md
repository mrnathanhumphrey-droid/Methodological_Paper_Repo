# skill fit: backtest_REB_aging_2019-20-2020-21-2021-22-2022-23__2023-24

- run timestamp: `20260426T201923Z`
- stan model: `hierarchical_aging.stan`
- observations: 47,136
- chains: 4 × (500 warmup + 500 sampling)
- wall time: 911.6s (15.2 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0083
- min ESS: 350
- params summarized: 486

### issues
- ESS for age_slope[1]: 350 < 400
- ESS for age_slope[2]: 391 < 400

## validation
- status: **PASSED**
- ✓ **coverage_80_in_band**: 80% CI coverage = 76.9% (target 70-90%)
- ✓ **bias_near_zero**: bias = +0.026 per-36 (target |b| < 0.5)
- ✓ **z_error_well_calibrated**: z-error mean=+0.04, sd=1.27 (target 0±0.3, sd 0.7-1.4)
- ✓ **top_25_tier_accuracy**: top-25 overlap = 80.0% (target ≥ 50%)

## worst misses (|projected - actual|, per-36)
-  3.22  Isaiah Stewart (proj 10.93 vs actual 7.71)
-  2.63  Jarred Vanderbilt (proj 11.15 vs actual 8.52)
-  2.59  Anthony Davis (proj 10.22 vs actual 12.81)
-  2.32  Kevin Love (proj 10.82 vs actual 13.14)
-  2.26  Andre Drummond (proj 16.63 vs actual 18.89)
-  2.17  John Collins (proj 8.73 vs actual 10.90)
-  2.10  Donte DiVincenzo (proj 6.63 vs actual 4.52)
-  2.04  Jalen Green (proj 3.82 vs actual 5.86)
-  2.01  Jevon Carter (proj 4.17 vs actual 2.16)
-  2.00  Daniel Gafford (proj 9.17 vs actual 11.17)

## best hits (smallest error)
-  0.00  Immanuel Quickley (proj 4.70 vs actual 4.69)
-  0.00  Joe Ingles (proj 4.39 vs actual 4.38)
-  0.01  Caleb Martin (proj 5.77 vs actual 5.75)
-  0.02  Terry Rozier (proj 4.34 vs actual 4.36)
-  0.02  Luguentz Dort (proj 4.57 vs actual 4.55)

## backtest metrics
- train: 2019-20,2020-21,2021-22,2022-23
- test: 2023-24
- N players: 195
- empirical out-of-sample SD: 0.670 (added to parameter SD in quadrature)
- MAE: 0.686
- RMSE: 0.908
- bias: +0.026
- coverage 50%: 44.6%
- coverage 80%: 76.9%
- coverage 90%: 83.6%
- z-error: mean=+0.039 sd=1.274
- top-25 tier accuracy: 80.0%
- top-50 tier accuracy: 94.0%
