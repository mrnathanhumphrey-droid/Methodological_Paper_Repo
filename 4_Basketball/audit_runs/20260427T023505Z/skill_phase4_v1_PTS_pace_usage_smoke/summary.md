# skill fit: phase4_v1_PTS_pace_usage_smoke

- run timestamp: `20260427T023505Z`
- stan model: `hierarchical_aging_pace_usage_v1.stan`
- observations: 32,200
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 1411.8s (23.5 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0126
- min ESS: 228
- params summarized: 411

### issues
- R-hat for mu_player[42]: 1.012 > 1.01
- R-hat for mu_player[53]: 1.013 > 1.01
- R-hat for sigma_position: 1.012 > 1.01
- ESS for sigma_position: 355 < 400
- R-hat for age_slope_position[1]: 1.011 > 1.01
- ESS for age_slope_position[1]: 228 < 400
- ESS for age_slope_position[2]: 240 < 400
- ESS for age_slope_position[3]: 388 < 400
- ESS for age_slope_player_sd: 391 < 400
- R-hat for pts_per_36_at_27[42]: 1.012 > 1.01
- R-hat for pts_per_36_at_27[53]: 1.013 > 1.01
- ESS for age_curve_position[1,1]: 362 < 400
- ESS for age_curve_position[1,2]: 398 < 400
- ESS for age_curve_position[1,14]: 386 < 400
- ESS for age_curve_position[1,15]: 341 < 400
- ESS for age_curve_position[1,16]: 312 < 400
- ESS for age_curve_position[1,17]: 292 < 400
- R-hat for age_curve_position[1,18]: 1.010 > 1.01
- ESS for age_curve_position[1,18]: 278 < 400
- R-hat for age_curve_position[1,19]: 1.011 > 1.01
- … +20 more
