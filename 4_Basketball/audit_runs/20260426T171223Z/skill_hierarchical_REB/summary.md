# skill fit: hierarchical_REB

- run timestamp: `20260426T171223Z`
- stan model: `hierarchical_one_stat.stan`
- observations: 20,794
- chains: 4 × (200 warmup + 200 sampling)
- wall time: 1336.1s (22.3 min)

## convergence
- status: **FAILED**
- max R-hat: 1.1013
- min ESS: 33
- params summarized: 164

### issues
- R-hat for mu_league: 1.010 > 1.01
- ESS for mu_league: 326 < 400
- R-hat for sigma_position: 1.022 > 1.01
- ESS for sigma_position: 260 < 400
- R-hat for sigma_player: 1.076 > 1.01
- ESS for sigma_player: 39 < 400
- ESS for z_position[1]: 323 < 400
- R-hat for z_position[2]: 1.011 > 1.01
- ESS for z_position[2]: 281 < 400
- ESS for z_position[3]: 288 < 400
- R-hat for z_player[1]: 1.094 > 1.01
- ESS for z_player[1]: 37 < 400
- R-hat for z_player[2]: 1.086 > 1.01
- ESS for z_player[2]: 34 < 400
- R-hat for z_player[3]: 1.101 > 1.01
- ESS for z_player[3]: 37 < 400
- R-hat for z_player[4]: 1.013 > 1.01
- ESS for z_player[4]: 149 < 400
- R-hat for z_player[5]: 1.019 > 1.01
- ESS for z_player[5]: 139 < 400
- … +119 more

## validation
- status: **FAILED**
- ✗ **shrinkage_pattern**: insufficient volume contrast: high=50 low=0
- ✓ **position_ordering_REB**: REB ordering: actual=['C', 'F', 'G'] expected=['C', 'F', 'G']
- ✗ **top_performers**: top-10 contains 2 of expected (need >= 3)

## top rebounders (per-36)
- 14.56  Jonas Valančiūnas
- 14.18  Rudy Gobert
- 13.12  Domantas Sabonis
- 12.95  Ivica Zubac
- 12.94  Giannis Antetokounmpo
- 12.63  Kevon Looney
- 12.52  Nikola Jokić
- 12.05  Jarrett Allen
- 11.99  Mason Plumlee
- 11.83  Nikola Vučević
- 11.47  Bobby Portis
- 10.35  Bam Adebayo
-  9.70  Julius Randle
-  8.84  Josh Hart
-  8.43  Naz Reid
