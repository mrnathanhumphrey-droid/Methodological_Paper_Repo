# Step 2 — Trajectory classification (arm = mpg_adj)

Locked SHA v1.0: `db0ed9a899c28691183cd5b640f460c10f3c2a75`
(v1.1 amendment not in scope)

Cells classified: 100
Training window: 2019-20 -> 2023-24 (5 seasons)
Thresholds: eps_mu = 0.02, eps_var = 0.05

## Regime distribution (overall)

| Regime | Count |
|---|---|
| Edge | 42 |
| Stationary | 30 |
| Diffusing | 16 |
| Contracting | 10 |
| Drifting | 1 |
| Concentrating | 1 |

## Regime distribution by observable

| Observable | Concentrating | Contracting | Diffusing | Drifting | Edge | Stationary |
|---|---|---|---|---|---|---|
| PTS_per36 | 0 | 0 | 1 | 0 | 15 | 9 |
| REB_per36 | 0 | 5 | 2 | 0 | 9 | 9 |
| AST_per36 | 0 | 2 | 8 | 0 | 7 | 8 |
| BLK_per36 | 1 | 3 | 5 | 1 | 11 | 4 |

## Normalization fallback (mu_bar < 0.01 or var_bar < 1e-06)
Cells using absolute slope: 0


## Per-cell regime ledger

| cell_id | observable | r_mu | r_var | regime |
|---|---|---|---|---|
| `Center|Mid|Bench` | AST_per36 | +0.0184 | +0.1470 | Edge |
| `Center|Mid|Bench` | BLK_per36 | -0.0793 | +0.0048 | Edge |
| `Center|Mid|Bench` | PTS_per36 | -0.0247 | -0.0102 | Edge |
| `Center|Mid|Bench` | REB_per36 | +0.0318 | +0.1131 | Diffusing |
| `Center|Mid|Rotation` | AST_per36 | +0.0676 | +0.0742 | Diffusing |
| `Center|Mid|Rotation` | BLK_per36 | -0.0607 | -0.0893 | Contracting |
| `Center|Mid|Rotation` | PTS_per36 | +0.0192 | -0.0064 | Stationary |
| `Center|Mid|Rotation` | REB_per36 | +0.0048 | -0.0265 | Stationary |
| `Center|Mid|Starter` | AST_per36 | +0.1005 | +0.1448 | Diffusing |
| `Center|Mid|Starter` | BLK_per36 | -0.0571 | -0.0813 | Contracting |
| `Center|Mid|Starter` | PTS_per36 | +0.0205 | -0.0120 | Edge |
| `Center|Mid|Starter` | REB_per36 | -0.0296 | -0.0955 | Contracting |
| `Center|Rookie|Bench` | AST_per36 | +0.0952 | +0.1594 | Diffusing |
| `Center|Rookie|Bench` | BLK_per36 | -0.0847 | -0.0386 | Edge |
| `Center|Rookie|Bench` | PTS_per36 | -0.0378 | +0.0159 | Edge |
| `Center|Rookie|Bench` | REB_per36 | -0.0120 | -0.0343 | Stationary |
| `Center|Rookie|Rotation` | AST_per36 | +0.1243 | +0.1514 | Diffusing |
| `Center|Rookie|Rotation` | BLK_per36 | +0.0998 | +0.1120 | Diffusing |
| `Center|Rookie|Rotation` | PTS_per36 | -0.0012 | +0.0269 | Stationary |
| `Center|Rookie|Rotation` | REB_per36 | +0.0438 | +0.0707 | Diffusing |
| `Center|Soph_Early|Bench` | AST_per36 | -0.0013 | +0.0360 | Stationary |
| `Center|Soph_Early|Bench` | BLK_per36 | -0.0156 | +0.0848 | Edge |
| `Center|Soph_Early|Bench` | PTS_per36 | -0.0037 | +0.0448 | Stationary |
| `Center|Soph_Early|Bench` | REB_per36 | -0.0073 | +0.0760 | Edge |
| `Center|Soph_Early|Rotation` | AST_per36 | -0.0862 | -0.1793 | Contracting |
| `Center|Soph_Early|Rotation` | BLK_per36 | +0.0124 | +0.0291 | Stationary |
| `Center|Soph_Early|Rotation` | PTS_per36 | -0.0259 | -0.0254 | Edge |
| `Center|Soph_Early|Rotation` | REB_per36 | -0.0199 | +0.0066 | Stationary |
| `Forward|Deep_vet|Rotation` | AST_per36 | +0.0596 | -0.0417 | Edge |
| `Forward|Deep_vet|Rotation` | BLK_per36 | -0.0240 | +0.2197 | Drifting |
| `Forward|Deep_vet|Rotation` | PTS_per36 | +0.0326 | +0.0570 | Diffusing |
| `Forward|Deep_vet|Rotation` | REB_per36 | -0.0642 | -0.0655 | Contracting |
| `Forward|Mid|Bench` | AST_per36 | +0.0937 | +0.1184 | Diffusing |
| `Forward|Mid|Bench` | BLK_per36 | +0.0000 | -0.0059 | Stationary |
| `Forward|Mid|Bench` | PTS_per36 | +0.0193 | -0.0519 | Edge |
| `Forward|Mid|Bench` | REB_per36 | -0.0459 | -0.0469 | Edge |
| `Forward|Mid|Rotation` | AST_per36 | +0.0869 | +0.1723 | Diffusing |
| `Forward|Mid|Rotation` | BLK_per36 | -0.0368 | -0.0424 | Edge |
| `Forward|Mid|Rotation` | PTS_per36 | +0.0069 | +0.0154 | Stationary |
| `Forward|Mid|Rotation` | REB_per36 | -0.0415 | -0.0538 | Contracting |
| `Forward|Mid|Starter` | AST_per36 | -0.0393 | -0.1015 | Contracting |
| `Forward|Mid|Starter` | BLK_per36 | -0.0091 | -0.0607 | Edge |
| `Forward|Mid|Starter` | PTS_per36 | -0.0020 | -0.0066 | Stationary |
| `Forward|Mid|Starter` | REB_per36 | -0.0133 | +0.0508 | Edge |
| `Forward|Rookie|Bench` | AST_per36 | +0.0112 | +0.0483 | Stationary |
| `Forward|Rookie|Bench` | BLK_per36 | -0.0620 | +0.0341 | Edge |
| `Forward|Rookie|Bench` | PTS_per36 | -0.0178 | +0.0705 | Edge |
| `Forward|Rookie|Bench` | REB_per36 | -0.0451 | +0.0079 | Edge |
| `Forward|Rookie|Rotation` | AST_per36 | +0.0371 | +0.0666 | Diffusing |
| `Forward|Rookie|Rotation` | BLK_per36 | +0.0111 | -0.0292 | Stationary |
| `Forward|Rookie|Rotation` | PTS_per36 | +0.0215 | -0.0143 | Edge |
| `Forward|Rookie|Rotation` | REB_per36 | +0.0188 | +0.0516 | Edge |
| `Forward|Soph_Early|Bench` | AST_per36 | +0.0328 | +0.0488 | Edge |
| `Forward|Soph_Early|Bench` | BLK_per36 | +0.0641 | +0.1393 | Diffusing |
| `Forward|Soph_Early|Bench` | PTS_per36 | +0.0007 | +0.0412 | Stationary |
| `Forward|Soph_Early|Bench` | REB_per36 | -0.0178 | -0.0141 | Stationary |
| `Forward|Soph_Early|Rotation` | AST_per36 | +0.0116 | -0.0118 | Stationary |
| `Forward|Soph_Early|Rotation` | BLK_per36 | -0.0912 | -0.1001 | Contracting |
| `Forward|Soph_Early|Rotation` | PTS_per36 | -0.0319 | -0.0073 | Edge |
| `Forward|Soph_Early|Rotation` | REB_per36 | -0.0878 | -0.1159 | Contracting |
| `Forward|Soph_Early|Starter` | AST_per36 | +0.0193 | -0.0326 | Stationary |
| `Forward|Soph_Early|Starter` | BLK_per36 | -0.0158 | -0.0322 | Stationary |
| `Forward|Soph_Early|Starter` | PTS_per36 | +0.0101 | -0.0280 | Stationary |
| `Forward|Soph_Early|Starter` | REB_per36 | -0.0198 | -0.0457 | Stationary |
| `Guard|Deep_vet|Rotation` | AST_per36 | +0.0118 | -0.0173 | Stationary |
| `Guard|Deep_vet|Rotation` | BLK_per36 | +0.0293 | -0.0930 | Concentrating |
| `Guard|Deep_vet|Rotation` | PTS_per36 | -0.0194 | +0.0214 | Stationary |
| `Guard|Deep_vet|Rotation` | REB_per36 | -0.0008 | +0.0457 | Stationary |
| `Guard|Mid|Bench` | AST_per36 | +0.0856 | +0.0492 | Edge |
| `Guard|Mid|Bench` | BLK_per36 | +0.1790 | +0.1138 | Diffusing |
| `Guard|Mid|Bench` | PTS_per36 | -0.0027 | -0.0807 | Edge |
| `Guard|Mid|Bench` | REB_per36 | +0.0336 | -0.0193 | Edge |
| `Guard|Mid|Rotation` | AST_per36 | +0.0500 | +0.0926 | Diffusing |
| `Guard|Mid|Rotation` | BLK_per36 | +0.0085 | +0.0596 | Edge |
| `Guard|Mid|Rotation` | PTS_per36 | +0.0062 | +0.0153 | Stationary |
| `Guard|Mid|Rotation` | REB_per36 | +0.0171 | +0.0669 | Edge |
| `Guard|Mid|Starter` | AST_per36 | +0.0021 | -0.0479 | Stationary |
| `Guard|Mid|Starter` | BLK_per36 | +0.0209 | +0.0423 | Edge |
| `Guard|Mid|Starter` | PTS_per36 | -0.0315 | -0.0292 | Edge |
| `Guard|Mid|Starter` | REB_per36 | -0.0320 | -0.0936 | Contracting |
| `Guard|Rookie|Bench` | AST_per36 | -0.0058 | +0.0292 | Stationary |
| `Guard|Rookie|Bench` | BLK_per36 | +0.0243 | +0.0544 | Diffusing |
| `Guard|Rookie|Bench` | PTS_per36 | -0.0056 | +0.1100 | Edge |
| `Guard|Rookie|Bench` | REB_per36 | -0.0374 | +0.0198 | Edge |
| `Guard|Rookie|Rotation` | AST_per36 | -0.0032 | -0.0332 | Stationary |
| `Guard|Rookie|Rotation` | BLK_per36 | +0.0627 | +0.0768 | Diffusing |
| `Guard|Rookie|Rotation` | PTS_per36 | -0.0142 | +0.1568 | Edge |
| `Guard|Rookie|Rotation` | REB_per36 | -0.0029 | +0.0006 | Stationary |
| `Guard|Soph_Early|Bench` | AST_per36 | -0.0250 | -0.0408 | Edge |
| `Guard|Soph_Early|Bench` | BLK_per36 | -0.0079 | +0.0774 | Edge |
| `Guard|Soph_Early|Bench` | PTS_per36 | +0.0086 | -0.0733 | Edge |
| `Guard|Soph_Early|Bench` | REB_per36 | -0.0408 | -0.0488 | Edge |
| `Guard|Soph_Early|Rotation` | AST_per36 | +0.0285 | +0.0102 | Edge |
| `Guard|Soph_Early|Rotation` | BLK_per36 | +0.0312 | +0.0359 | Edge |
| `Guard|Soph_Early|Rotation` | PTS_per36 | +0.0201 | +0.0455 | Edge |
| `Guard|Soph_Early|Rotation` | REB_per36 | +0.0075 | +0.0029 | Stationary |
| `Guard|Soph_Early|Starter` | AST_per36 | +0.0259 | +0.0474 | Edge |
| `Guard|Soph_Early|Starter` | BLK_per36 | +0.0365 | +0.0284 | Edge |
| `Guard|Soph_Early|Starter` | PTS_per36 | +0.0219 | +0.0283 | Edge |
| `Guard|Soph_Early|Starter` | REB_per36 | -0.0066 | +0.0269 | Stationary |
