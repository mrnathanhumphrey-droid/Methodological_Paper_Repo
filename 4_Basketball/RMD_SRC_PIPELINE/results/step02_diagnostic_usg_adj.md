# Step 2 — Trajectory classification (arm = usg_adj)

Locked SHA v1.0: `db0ed9a899c28691183cd5b640f460c10f3c2a75`
(v1.1 amendment not in scope)

Cells classified: 84
Training window: 2019-20 -> 2023-24 (5 seasons)
Thresholds: eps_mu = 0.02, eps_var = 0.05

## Regime distribution (overall)

| Regime | Count |
|---|---|
| Stationary | 33 |
| Edge | 25 |
| Diffusing | 13 |
| Contracting | 10 |
| Concentrating | 2 |
| Drifting | 1 |

## Regime distribution by observable

| Observable | Concentrating | Contracting | Diffusing | Drifting | Edge | Stationary |
|---|---|---|---|---|---|---|
| PTS_per36 | 1 | 2 | 1 | 0 | 6 | 11 |
| REB_per36 | 0 | 4 | 0 | 0 | 7 | 10 |
| AST_per36 | 0 | 1 | 8 | 0 | 4 | 8 |
| BLK_per36 | 1 | 3 | 4 | 1 | 8 | 4 |

## Normalization fallback (mu_bar < 0.01 or var_bar < 1e-06)
Cells using absolute slope: 0


## Per-cell regime ledger

| cell_id | observable | r_mu | r_var | regime |
|---|---|---|---|---|
| `Center|Mid|Low_usage` | AST_per36 | +0.0422 | +0.1162 | Diffusing |
| `Center|Mid|Low_usage` | BLK_per36 | -0.0800 | -0.0892 | Contracting |
| `Center|Mid|Low_usage` | PTS_per36 | -0.0158 | +0.0097 | Stationary |
| `Center|Mid|Low_usage` | REB_per36 | +0.0056 | +0.0719 | Edge |
| `Center|Mid|Mid_usage` | AST_per36 | +0.0899 | +0.1283 | Diffusing |
| `Center|Mid|Mid_usage` | BLK_per36 | -0.0629 | -0.0721 | Contracting |
| `Center|Mid|Mid_usage` | PTS_per36 | +0.0251 | -0.0094 | Edge |
| `Center|Mid|Mid_usage` | REB_per36 | -0.0082 | -0.0417 | Stationary |
| `Center|Rookie|Low_usage` | AST_per36 | +0.1083 | +0.1914 | Diffusing |
| `Center|Rookie|Low_usage` | BLK_per36 | -0.0174 | +0.0219 | Stationary |
| `Center|Rookie|Low_usage` | PTS_per36 | -0.0609 | -0.0623 | Contracting |
| `Center|Rookie|Low_usage` | REB_per36 | +0.0086 | -0.0399 | Stationary |
| `Center|Rookie|Mid_usage` | AST_per36 | +0.1317 | +0.0930 | Diffusing |
| `Center|Rookie|Mid_usage` | BLK_per36 | +0.0399 | +0.0274 | Edge |
| `Center|Rookie|Mid_usage` | PTS_per36 | +0.0316 | +0.0336 | Edge |
| `Center|Rookie|Mid_usage` | REB_per36 | +0.0351 | +0.0334 | Edge |
| `Center|Soph_Early|Low_usage` | AST_per36 | +0.0058 | +0.0635 | Edge |
| `Center|Soph_Early|Low_usage` | BLK_per36 | +0.0074 | +0.1194 | Edge |
| `Center|Soph_Early|Low_usage` | PTS_per36 | -0.0041 | +0.0447 | Stationary |
| `Center|Soph_Early|Low_usage` | REB_per36 | -0.0040 | +0.0185 | Stationary |
| `Center|Soph_Early|Mid_usage` | AST_per36 | -0.1020 | -0.1749 | Contracting |
| `Center|Soph_Early|Mid_usage` | BLK_per36 | +0.0016 | +0.0171 | Stationary |
| `Center|Soph_Early|Mid_usage` | PTS_per36 | -0.0194 | -0.0064 | Stationary |
| `Center|Soph_Early|Mid_usage` | REB_per36 | -0.0187 | +0.0836 | Edge |
| `Forward|Deep_vet|Mid_usage` | AST_per36 | +0.0596 | -0.0417 | Edge |
| `Forward|Deep_vet|Mid_usage` | BLK_per36 | -0.0240 | +0.2197 | Drifting |
| `Forward|Deep_vet|Mid_usage` | PTS_per36 | +0.0326 | +0.0570 | Diffusing |
| `Forward|Deep_vet|Mid_usage` | REB_per36 | -0.0642 | -0.0655 | Contracting |
| `Forward|Mid|Low_usage` | AST_per36 | +0.0570 | +0.1038 | Diffusing |
| `Forward|Mid|Low_usage` | BLK_per36 | +0.0202 | +0.0088 | Edge |
| `Forward|Mid|Low_usage` | PTS_per36 | +0.0275 | +0.0443 | Edge |
| `Forward|Mid|Low_usage` | REB_per36 | -0.0371 | -0.0369 | Edge |
| `Forward|Mid|Mid_usage` | AST_per36 | +0.0022 | -0.0070 | Stationary |
| `Forward|Mid|Mid_usage` | BLK_per36 | -0.0169 | +0.0295 | Stationary |
| `Forward|Mid|Mid_usage` | PTS_per36 | +0.0013 | +0.0004 | Stationary |
| `Forward|Mid|Mid_usage` | REB_per36 | -0.0231 | +0.0240 | Edge |
| `Forward|Rookie|Low_usage` | AST_per36 | +0.0141 | +0.0200 | Stationary |
| `Forward|Rookie|Low_usage` | BLK_per36 | -0.0756 | -0.1154 | Contracting |
| `Forward|Rookie|Low_usage` | PTS_per36 | +0.0118 | -0.0234 | Stationary |
| `Forward|Rookie|Low_usage` | REB_per36 | -0.0116 | -0.0448 | Stationary |
| `Forward|Rookie|Mid_usage` | AST_per36 | +0.0343 | +0.0635 | Diffusing |
| `Forward|Rookie|Mid_usage` | BLK_per36 | +0.0408 | +0.0935 | Diffusing |
| `Forward|Rookie|Mid_usage` | PTS_per36 | +0.0097 | +0.0621 | Edge |
| `Forward|Rookie|Mid_usage` | REB_per36 | +0.0055 | +0.0976 | Edge |
| `Forward|Soph_Early|Low_usage` | AST_per36 | +0.0194 | -0.0084 | Stationary |
| `Forward|Soph_Early|Low_usage` | BLK_per36 | +0.0254 | +0.1113 | Diffusing |
| `Forward|Soph_Early|Low_usage` | PTS_per36 | -0.0015 | -0.0002 | Stationary |
| `Forward|Soph_Early|Low_usage` | REB_per36 | -0.0596 | -0.0909 | Contracting |
| `Forward|Soph_Early|Mid_usage` | AST_per36 | +0.0071 | +0.0120 | Stationary |
| `Forward|Soph_Early|Mid_usage` | BLK_per36 | -0.0634 | -0.0371 | Edge |
| `Forward|Soph_Early|Mid_usage` | PTS_per36 | -0.0187 | +0.0357 | Stationary |
| `Forward|Soph_Early|Mid_usage` | REB_per36 | -0.0362 | +0.0000 | Edge |
| `Guard|Deep_vet|Mid_usage` | AST_per36 | +0.0118 | -0.0173 | Stationary |
| `Guard|Deep_vet|Mid_usage` | BLK_per36 | +0.0293 | -0.0930 | Concentrating |
| `Guard|Deep_vet|Mid_usage` | PTS_per36 | -0.0194 | +0.0214 | Stationary |
| `Guard|Deep_vet|Mid_usage` | REB_per36 | -0.0008 | +0.0457 | Stationary |
| `Guard|Mid|High_usage` | AST_per36 | -0.0136 | -0.0459 | Stationary |
| `Guard|Mid|High_usage` | BLK_per36 | -0.0270 | -0.0119 | Edge |
| `Guard|Mid|High_usage` | PTS_per36 | -0.0197 | -0.0564 | Edge |
| `Guard|Mid|High_usage` | REB_per36 | -0.0291 | -0.0990 | Contracting |
| `Guard|Mid|Low_usage` | AST_per36 | +0.0617 | +0.0712 | Diffusing |
| `Guard|Mid|Low_usage` | BLK_per36 | +0.0274 | +0.0437 | Edge |
| `Guard|Mid|Low_usage` | PTS_per36 | -0.0215 | -0.0876 | Contracting |
| `Guard|Mid|Low_usage` | REB_per36 | +0.0188 | +0.0313 | Stationary |
| `Guard|Mid|Mid_usage` | AST_per36 | +0.0523 | +0.0473 | Edge |
| `Guard|Mid|Mid_usage` | BLK_per36 | +0.0675 | +0.0724 | Diffusing |
| `Guard|Mid|Mid_usage` | PTS_per36 | +0.0071 | +0.0176 | Stationary |
| `Guard|Mid|Mid_usage` | REB_per36 | +0.0033 | -0.0016 | Stationary |
| `Guard|Rookie|Mid_usage` | AST_per36 | -0.0110 | +0.0219 | Stationary |
| `Guard|Rookie|Mid_usage` | BLK_per36 | +0.0483 | +0.0892 | Diffusing |
| `Guard|Rookie|Mid_usage` | PTS_per36 | -0.0200 | +0.1416 | Edge |
| `Guard|Rookie|Mid_usage` | REB_per36 | -0.0154 | +0.0411 | Stationary |
| `Guard|Soph_Early|High_usage` | AST_per36 | +0.0398 | +0.0280 | Edge |
| `Guard|Soph_Early|High_usage` | BLK_per36 | +0.0308 | +0.0199 | Edge |
| `Guard|Soph_Early|High_usage` | PTS_per36 | +0.0099 | +0.0018 | Stationary |
| `Guard|Soph_Early|High_usage` | REB_per36 | -0.0163 | -0.0340 | Stationary |
| `Guard|Soph_Early|Low_usage` | AST_per36 | +0.0441 | +0.0509 | Diffusing |
| `Guard|Soph_Early|Low_usage` | BLK_per36 | +0.0177 | +0.2243 | Edge |
| `Guard|Soph_Early|Low_usage` | PTS_per36 | +0.0390 | -0.0847 | Concentrating |
| `Guard|Soph_Early|Low_usage` | REB_per36 | -0.0433 | -0.0832 | Contracting |
| `Guard|Soph_Early|Mid_usage` | AST_per36 | -0.0068 | -0.0160 | Stationary |
| `Guard|Soph_Early|Mid_usage` | BLK_per36 | +0.0165 | +0.0028 | Stationary |
| `Guard|Soph_Early|Mid_usage` | PTS_per36 | +0.0165 | +0.0333 | Stationary |
| `Guard|Soph_Early|Mid_usage` | REB_per36 | -0.0029 | +0.0163 | Stationary |
