# skill fit: hierarchical_TOV_aging

- run timestamp: `20260426T204539Z`
- stan model: `hierarchical_aging.stan`
- observations: 20,794
- chains: 4 × (500 warmup + 500 sampling)
- wall time: 232.4s (3.9 min)

## convergence
- status: **FAILED**
- max R-hat: 1.0572
- min ESS: 84
- params summarized: 186

### issues
- R-hat for mu_league: 1.012 > 1.01
- R-hat for mu_player[3]: 1.013 > 1.01
- R-hat for mu_player[4]: 1.020 > 1.01
- ESS for mu_player[4]: 398 < 400
- R-hat for mu_player[6]: 1.031 > 1.01
- ESS for mu_player[6]: 159 < 400
- R-hat for mu_player[8]: 1.038 > 1.01
- ESS for mu_player[8]: 99 < 400
- R-hat for mu_player[9]: 1.020 > 1.01
- ESS for mu_player[9]: 309 < 400
- R-hat for mu_player[10]: 1.016 > 1.01
- R-hat for mu_player[11]: 1.017 > 1.01
- R-hat for mu_player[13]: 1.011 > 1.01
- ESS for mu_player[16]: 398 < 400
- R-hat for mu_player[18]: 1.011 > 1.01
- R-hat for mu_player[19]: 1.015 > 1.01
- ESS for mu_player[19]: 379 < 400
- R-hat for mu_player[20]: 1.010 > 1.01
- R-hat for mu_player[22]: 1.013 > 1.01
- R-hat for mu_player[23]: 1.019 > 1.01
- … +120 more
