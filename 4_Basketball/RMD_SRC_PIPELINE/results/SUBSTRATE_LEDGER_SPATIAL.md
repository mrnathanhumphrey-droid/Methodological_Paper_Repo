# NBA RMD-SRC SPATIAL re-axis — Substrate Ledger

Locked under spatial pre-reg SHA `cd40b46`. Does NOT modify the position-arm `SUBSTRATE_LEDGER.md`.

## Headline by arm
| Arm | K | F1 fires? | F2 clean | F2 fires? | F4 mean κ | F4 any≥0.40? | Step5 mean r | Comp vs v6.1 (P/T/L) |
|---|---|---|---|---|---|---|---|---|
| `off_feast` | 15 | N | 26/46 = 56.5% | N | -0.079 | N | +0.770 | 0/60/0 |
| `def_feast` | 22 | N | 19/53 = 35.8% | Y | -0.003 | N | +0.742 | 0/88/0 |
| `usg` | 19 | N | 32/53 = 60.4% | N | +0.015 | N | +0.796 | 0/76/0 |

## F4 detail — Cohen κ per (arm, observable)
| Arm | PTS | REB | AST | BLK |
|---|---|---|---|---|
| `off_feast` | -0.114 | -0.010 | -0.016 | -0.176 |
| `def_feast` | +0.002 | -0.115 | +0.021 | +0.078 |
| `usg` | +0.057 | -0.042 | +0.073 | -0.027 |

## §9.2 — spatial vs position (usg) comparative
| Arm | ΔF2-clean | ΔF4-mean-κ | Δdip-pass | disposition |
|---|---|---|---|---|
| `off_feast` | -0.039 | -0.094 | +0.000 | position-dominant |
| `def_feast` | -0.245 | -0.019 | +0.000 | position-dominant |

## Cross-arm regime κ (off_feast vs def_feast), per observable

- PTS_per36: κ = +0.078
- REB_per36: κ = +0.027
- AST_per36: κ = +0.081
- BLK_per36: κ = +0.231

## Prediction verdicts (timestamped 2026-06-10)
- **P1_court_region_transfers** (cal 0.6): **MISS** — off_feast F4 kappa>=0.40 on >=1 obs (position failed ~0)
- **P2_BLK_relocates_to_rim** (cal 0.55): **HIT** — BLK x RimProtector tightens (Concentrating/Contracting) + transfers
- **P3_offense_clean_defense_coupled** (cal 0.65): **MISS** — off_feast beats def_feast on F2-clean AND mean-F4-kappa
