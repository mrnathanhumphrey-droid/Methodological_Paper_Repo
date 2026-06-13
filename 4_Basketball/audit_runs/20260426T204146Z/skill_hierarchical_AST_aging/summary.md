# skill fit: hierarchical_AST_aging

- run timestamp: `20260426T204146Z`
- stan model: `hierarchical_aging.stan`
- observations: 20,794
- chains: 4 × (500 warmup + 500 sampling)
- wall time: 292.0s (4.9 min)

## convergence
- status: **FAILED**
- max R-hat: 1.1736
- min ESS: 17
- params summarized: 186

### issues
- R-hat for mu_league: 1.017 > 1.01
- R-hat for mu_position[1]: 1.024 > 1.01
- ESS for mu_position[1]: 164 < 400
- R-hat for mu_position[2]: 1.040 > 1.01
- ESS for mu_position[2]: 87 < 400
- R-hat for mu_position[3]: 1.040 > 1.01
- ESS for mu_position[3]: 76 < 400
- R-hat for mu_player[1]: 1.058 > 1.01
- ESS for mu_player[1]: 51 < 400
- R-hat for mu_player[2]: 1.047 > 1.01
- ESS for mu_player[2]: 78 < 400
- R-hat for mu_player[3]: 1.011 > 1.01
- ESS for mu_player[3]: 376 < 400
- R-hat for mu_player[6]: 1.014 > 1.01
- R-hat for mu_player[7]: 1.015 > 1.01
- R-hat for mu_player[8]: 1.035 > 1.01
- ESS for mu_player[8]: 85 < 400
- R-hat for mu_player[9]: 1.024 > 1.01
- R-hat for mu_player[11]: 1.024 > 1.01
- R-hat for mu_player[12]: 1.014 > 1.01
- … +274 more
