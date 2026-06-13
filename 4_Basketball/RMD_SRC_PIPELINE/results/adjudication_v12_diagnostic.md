# v1.2 adjudication diagnostic

Locked v1.2 SHA: `1bfdb4c0dfa2b3754f67e9c2f91b2ab26fa01866`
Verdicts artifact SHA256: `eb615269f09159e0d0ceaf071812b84750578d81a9a53b01dff5a1ac2ac9dcbd`

## Headline
- Total adjudication targets: **230**
- Successful verdicts: **230**
- Failed verdicts (route to v1.0 metadata bucket): **0**
- **Positionless (no_fit)** verdicts: **0**

## Final bucket distribution
- Center: 60
- Forward: 110
- Guard: 60
- Positionless: 0

## Metadata vs adjudicated agreement
- Unchanged (adjudicator confirmed metadata bucket): 132
- Changed (adjudicator overrode metadata): 98
- Override rate: 42.6%

## Flip matrix (metadata -> adjudicated)
| metadata | adjudicated | count |
|---|---|---|
| Guard | Forward | 50 |
| Forward | Center | 46 |
| Forward | Guard | 2 |

## Confidence distribution (overall)
| confidence | count | % |
|---|---|---|
| high | 140 | 60.9% |
| medium | 90 | 39.1% |
| low | 0 | 0.0% |

## Confidence distribution (flipped verdicts only)
| confidence | count | % of flips |
|---|---|---|
| high | 42 | 42.9% |
| medium | 56 | 57.1% |
| low | 0 | 0.0% |

## Named flip examples (up to 8 per flip type)

### Guard -> Forward (n=50)
| player | confidence | rationale (clipped) |
|---|---|---|
| Nicolas Batum | high | Batum is 6'7" and played exclusively as a wing/3-and-D forward during the 2019-26 window, primarily with the Clippers. Yahoo lists him PF/SF with PF primary. His per-36 profile ... |
| DeMar DeRozan | high | In the 2019-26 window DeRozan played as a scoring forward — elbow/mid-range hub at SF/PF for San Antonio, Chicago, and Sacramento. Yahoo primary position is PF. Height (6'6") is... |
| Ben Simmons | medium | Simmons at 6'10" with 8.35 REB/36 and near-zero three-point shooting (0.02 FG3M/36) profiles as a big-man forward despite his 8.3 AST/36. His defensive assignments and reboundin... |
| Jaylen Brown | medium | At 6'6" (78 in), Brown sits at the Guard-Forward boundary. Yahoo primary is SF, eligible SF/SG. Per-36: REB 6.56, AST 3.93, BLK 0.41 — balanced wing profile, not AST-dominant (g... |
| Josh Hart | medium | Hart is 6'5" which nominally leans Guard, but his on-court archetype in the 2019-26 window is clearly Forward. His REB/36 of 8.8 is elite for any non-center and well above guard... |
| Dillon Brooks | medium | Brooks is a 6'7" 3-and-D wing whose 2019-26 archetype is perimeter forward. His career stat profile (REB/36 4.03, AST/36 2.48, BLK/36 0.30, 3PM/36 2.41) fits a wing forward: mod... |
| Svi Mykhailiuk | medium | Mykhailiuk is a 6'7" perimeter shooter whose Yahoo primary position is SF and who profiles as a stretch wing. His per-36 stats show moderate REB (4.01) and AST (2.75) with very ... |
| Josh Okogie | medium | At 6'4" Okogie sits at the Guard/Forward boundary, but his Yahoo primary position (SF), low AST per-36 (2.11), and moderate REB (5.79) point to a wing/3-and-D forward archetype ... |

### Forward -> Center (n=46)
| player | confidence | rationale (clipped) |
|---|---|---|
| Kevin Love | medium | At 6'10" with a REB/36 of 11.7 and Yahoo primary position of C, Love fits the Center bucket in the 2019-26 window. His role in Cleveland and Miami was as a stretch-5 / stretch-4... |
| Taj Gibson | high | Gibson is 6'9" with a classic interior big-man stat profile: 8.61 REB/36, only 1.7 AST/36, 1.16 BLK/36, and virtually no three-point production (0.3 FG3M/36). In the 2019-26 win... |
| Anthony Davis | high | Davis at 6'10" (82 in) with REB/36=11.54 and BLK/36=2.24 fits the Center archetype cleanly. In the 2019-26 window he has served as the Lakers' primary rim anchor and shot-blocke... |
| Kelly Olynyk | medium | At 7'0" and with Yahoo primary position of C, Olynyk's 2019-26 archetype is a stretch center. His 1.72 3PM/36 and 4.84 AST/36 reflect a face-up, passing big rather than a tradit... |
| Mason Plumlee | high | Plumlee is 7'0" (84 inches), Yahoo-listed as C at primary position, and his counting stats confirm a Center archetype: 12.1 REB/36, zero three-point attempts, 1.03 BLK/36. The e... |
| Giannis Antetokounmpo | medium | At 6'11" with Yahoo primary position C and REB 13.02/36, Giannis operates in the 2019-26 window as a paint-dominant, rim-running big who defends center/PF archetypes. His minima... |
| Dwight Powell | high | Powell is 6'10" and functions as a rim-running center in Dallas's offense during the 2019-26 window — a screen-and-roll dive man with negligible 3-point shooting (0.13 per 36). ... |
| Kristaps Porziņģis | high | At 86 inches (7'2"), Porzingis is well above the Center threshold. His Yahoo primary position is C. His per-36 profile — REB 9.4, BLK 1.97, AST 2.6 — is a canonical Center arche... |

### Forward -> Guard (n=2)
| player | confidence | rationale (clipped) |
|---|---|---|
| Luka Dončić | high | Dončić functions as the primary ball-handler and playmaker in every season of the 2019-26 window. Despite being 6'8", Yahoo lists him PG/SG with PG primary. His per-36 AST (8.66... |
| Tyrese Martin | medium | At 6'6" (78 inches) with Yahoo primary position PG and eligibility spanning PG/SG/SF, Martin's archetype in the 2019-26 window is a combo guard / 3-and-D wing who occupies backc... |
