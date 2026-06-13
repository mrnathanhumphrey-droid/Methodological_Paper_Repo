# skill fit: phase4_v1_REB_lineup_smoke

- run timestamp: `20260427T015837Z`
- stan model: `hierarchical_aging_lineup_v1.stan`
- observations: 32,200
- chains: 4 × (400 warmup + 400 sampling)
- wall time: 1430.4s (23.8 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0153
- min ESS: 377
- params summarized: 410

### issues
- ESS for mu_league: 393 < 400
- R-hat for mu_player[42]: 1.011 > 1.01
- R-hat for mu_player[75]: 1.012 > 1.01
- ESS for beta_lineup_skill_interaction: 377 < 400
- R-hat for age_slope_player[75]: 1.015 > 1.01
- R-hat for reb_per_36_at_27[42]: 1.011 > 1.01
- R-hat for reb_per_36_at_27[75]: 1.012 > 1.01
- ESS for reb_per_36_league_at_27: 393 < 400
- ESS for lineup_lift_specialist_strong: 377 < 400
- ESS for lineup_lift_roleplayer_strong: 377 < 400
