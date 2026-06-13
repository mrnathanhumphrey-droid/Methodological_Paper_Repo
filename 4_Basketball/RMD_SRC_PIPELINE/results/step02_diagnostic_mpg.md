# Step 2 — Trajectory classification (arm = mpg)

Locked SHA v1.0: `db0ed9a899c28691183cd5b640f460c10f3c2a75`
Locked SHA v1.1: `4d0602df832d5a45402a212acf48b19a4dfee070`

Cells classified: 84
Training window: 2019-20 -> 2023-24 (5 seasons)
Thresholds: eps_mu = 0.02, eps_var = 0.05

## Regime distribution (overall)

| Regime | Count |
|---|---|
| Edge | 35 |
| Stationary | 34 |
| Diffusing | 9 |
| Contracting | 4 |
| Drifting | 1 |
| Concentrating | 1 |

## Regime distribution by observable

| Observable | Concentrating | Contracting | Diffusing | Drifting | Edge | Stationary |
|---|---|---|---|---|---|---|
| PTS_per36 | 0 | 0 | 1 | 0 | 11 | 9 |
| REB_per36 | 0 | 1 | 0 | 0 | 11 | 9 |
| AST_per36 | 0 | 2 | 5 | 0 | 6 | 8 |
| BLK_per36 | 1 | 1 | 3 | 1 | 7 | 8 |

## Normalization fallback (mu_bar < 0.01 or var_bar < 1e-06)
Cells using absolute slope: 0


## Per-cell regime ledger

| cell_id | observable | r_mu | r_var | regime |
|---|---|---|---|---|
| `Center|Mid|Rotation` | AST_per36 | +0.0855 | +0.1634 | Diffusing |
| `Center|Mid|Rotation` | BLK_per36 | -0.0465 | -0.0625 | Contracting |
| `Center|Mid|Rotation` | PTS_per36 | +0.0351 | +0.0304 | Edge |
| `Center|Mid|Rotation` | REB_per36 | +0.0010 | -0.0168 | Stationary |
| `Center|Rookie|Rotation` | AST_per36 | +0.0577 | -0.0100 | Edge |
| `Center|Rookie|Rotation` | BLK_per36 | -0.0067 | -0.0135 | Stationary |
| `Center|Rookie|Rotation` | PTS_per36 | -0.0239 | -0.0060 | Edge |
| `Center|Rookie|Rotation` | REB_per36 | -0.0003 | +0.0272 | Stationary |
| `Center|Soph_Early|Rotation` | AST_per36 | -0.0757 | -0.0923 | Contracting |
| `Center|Soph_Early|Rotation` | BLK_per36 | -0.0083 | +0.1199 | Edge |
| `Center|Soph_Early|Rotation` | PTS_per36 | -0.0312 | -0.0102 | Edge |
| `Center|Soph_Early|Rotation` | REB_per36 | -0.0095 | +0.0649 | Edge |
| `Forward|Deep_vet|Rotation` | AST_per36 | +0.0530 | -0.0088 | Edge |
| `Forward|Deep_vet|Rotation` | BLK_per36 | -0.0403 | +0.2566 | Drifting |
| `Forward|Deep_vet|Rotation` | PTS_per36 | +0.0304 | +0.0625 | Diffusing |
| `Forward|Deep_vet|Rotation` | REB_per36 | -0.0187 | +0.0658 | Edge |
| `Forward|Mid|Bench` | AST_per36 | +0.0541 | +0.1080 | Diffusing |
| `Forward|Mid|Bench` | BLK_per36 | -0.0229 | -0.0084 | Edge |
| `Forward|Mid|Bench` | PTS_per36 | +0.0088 | -0.0195 | Stationary |
| `Forward|Mid|Bench` | REB_per36 | -0.0281 | +0.0250 | Edge |
| `Forward|Mid|Rotation` | AST_per36 | +0.0806 | +0.1271 | Diffusing |
| `Forward|Mid|Rotation` | BLK_per36 | -0.0233 | -0.0265 | Edge |
| `Forward|Mid|Rotation` | PTS_per36 | +0.0106 | +0.0109 | Stationary |
| `Forward|Mid|Rotation` | REB_per36 | -0.0048 | +0.0016 | Stationary |
| `Forward|Mid|Starter` | AST_per36 | -0.0033 | -0.0336 | Stationary |
| `Forward|Mid|Starter` | BLK_per36 | +0.0195 | +0.0032 | Stationary |
| `Forward|Mid|Starter` | PTS_per36 | +0.0045 | -0.0537 | Edge |
| `Forward|Mid|Starter` | REB_per36 | -0.0031 | +0.0436 | Stationary |
| `Forward|Rookie|Bench` | AST_per36 | +0.0599 | +0.0909 | Diffusing |
| `Forward|Rookie|Bench` | BLK_per36 | +0.0138 | +0.0367 | Stationary |
| `Forward|Rookie|Bench` | PTS_per36 | -0.0058 | +0.0398 | Stationary |
| `Forward|Rookie|Bench` | REB_per36 | +0.0095 | +0.0078 | Stationary |
| `Forward|Rookie|Rotation` | AST_per36 | +0.0125 | -0.0277 | Stationary |
| `Forward|Rookie|Rotation` | BLK_per36 | +0.0116 | +0.0230 | Stationary |
| `Forward|Rookie|Rotation` | PTS_per36 | +0.0009 | -0.0096 | Stationary |
| `Forward|Rookie|Rotation` | REB_per36 | +0.0016 | +0.0660 | Edge |
| `Forward|Soph_Early|Bench` | AST_per36 | +0.0093 | +0.0131 | Stationary |
| `Forward|Soph_Early|Bench` | BLK_per36 | +0.0526 | +0.0386 | Edge |
| `Forward|Soph_Early|Bench` | PTS_per36 | +0.0222 | +0.0414 | Edge |
| `Forward|Soph_Early|Bench` | REB_per36 | +0.0047 | +0.0176 | Stationary |
| `Forward|Soph_Early|Rotation` | AST_per36 | +0.0154 | +0.0059 | Stationary |
| `Forward|Soph_Early|Rotation` | BLK_per36 | +0.0024 | +0.0255 | Stationary |
| `Forward|Soph_Early|Rotation` | PTS_per36 | -0.0182 | -0.0157 | Stationary |
| `Forward|Soph_Early|Rotation` | REB_per36 | -0.0320 | -0.0103 | Edge |
| `Forward|Soph_Early|Starter` | AST_per36 | +0.0355 | +0.0334 | Edge |
| `Forward|Soph_Early|Starter` | BLK_per36 | -0.0079 | -0.0025 | Stationary |
| `Forward|Soph_Early|Starter` | PTS_per36 | +0.0209 | +0.0184 | Edge |
| `Forward|Soph_Early|Starter` | REB_per36 | -0.0349 | -0.0825 | Contracting |
| `Guard|Deep_vet|Rotation` | AST_per36 | -0.0053 | -0.0362 | Stationary |
| `Guard|Deep_vet|Rotation` | BLK_per36 | +0.0555 | -0.0693 | Concentrating |
| `Guard|Deep_vet|Rotation` | PTS_per36 | -0.0167 | +0.0285 | Stationary |
| `Guard|Deep_vet|Rotation` | REB_per36 | +0.0033 | +0.0258 | Stationary |
| `Guard|Mid|Bench` | AST_per36 | +0.0856 | +0.0492 | Edge |
| `Guard|Mid|Bench` | BLK_per36 | +0.1790 | +0.1138 | Diffusing |
| `Guard|Mid|Bench` | PTS_per36 | -0.0027 | -0.0807 | Edge |
| `Guard|Mid|Bench` | REB_per36 | +0.0336 | -0.0193 | Edge |
| `Guard|Mid|Rotation` | AST_per36 | +0.0540 | +0.0981 | Diffusing |
| `Guard|Mid|Rotation` | BLK_per36 | +0.0062 | +0.0557 | Edge |
| `Guard|Mid|Rotation` | PTS_per36 | +0.0082 | +0.0157 | Stationary |
| `Guard|Mid|Rotation` | REB_per36 | +0.0158 | +0.0679 | Edge |
| `Guard|Mid|Starter` | AST_per36 | -0.0121 | -0.0461 | Stationary |
| `Guard|Mid|Starter` | BLK_per36 | +0.0172 | +0.0376 | Stationary |
| `Guard|Mid|Starter` | PTS_per36 | -0.0351 | -0.0163 | Edge |
| `Guard|Mid|Starter` | REB_per36 | -0.0212 | -0.0415 | Edge |
| `Guard|Rookie|Bench` | AST_per36 | -0.0224 | +0.0165 | Edge |
| `Guard|Rookie|Bench` | BLK_per36 | +0.0008 | +0.0581 | Edge |
| `Guard|Rookie|Bench` | PTS_per36 | -0.0114 | +0.1030 | Edge |
| `Guard|Rookie|Bench` | REB_per36 | -0.0399 | +0.0228 | Edge |
| `Guard|Rookie|Rotation` | AST_per36 | -0.0098 | -0.0315 | Stationary |
| `Guard|Rookie|Rotation` | BLK_per36 | +0.0918 | +0.1260 | Diffusing |
| `Guard|Rookie|Rotation` | PTS_per36 | -0.0072 | +0.0940 | Edge |
| `Guard|Rookie|Rotation` | REB_per36 | +0.0286 | +0.0381 | Edge |
| `Guard|Soph_Early|Bench` | AST_per36 | -0.0421 | -0.0640 | Contracting |
| `Guard|Soph_Early|Bench` | BLK_per36 | +0.0355 | +0.1796 | Diffusing |
| `Guard|Soph_Early|Bench` | PTS_per36 | +0.0052 | -0.0682 | Edge |
| `Guard|Soph_Early|Bench` | REB_per36 | -0.0247 | -0.0260 | Edge |
| `Guard|Soph_Early|Rotation` | AST_per36 | -0.0043 | -0.0130 | Stationary |
| `Guard|Soph_Early|Rotation` | BLK_per36 | +0.0490 | +0.0471 | Edge |
| `Guard|Soph_Early|Rotation` | PTS_per36 | +0.0050 | +0.0401 | Stationary |
| `Guard|Soph_Early|Rotation` | REB_per36 | +0.0038 | +0.0037 | Stationary |
| `Guard|Soph_Early|Starter` | AST_per36 | +0.0220 | +0.0374 | Edge |
| `Guard|Soph_Early|Starter` | BLK_per36 | +0.0171 | +0.0006 | Stationary |
| `Guard|Soph_Early|Starter` | PTS_per36 | +0.0158 | +0.0195 | Stationary |
| `Guard|Soph_Early|Starter` | REB_per36 | -0.0199 | -0.0223 | Stationary |
