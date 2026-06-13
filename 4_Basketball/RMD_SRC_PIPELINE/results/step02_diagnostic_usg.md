# Step 2 — Trajectory classification (arm = usg)

Locked SHA v1.0: `db0ed9a899c28691183cd5b640f460c10f3c2a75`
(v1.1 amendment not in scope)

Cells classified: 76
Training window: 2019-20 -> 2023-24 (5 seasons)
Thresholds: eps_mu = 0.02, eps_var = 0.05

## Regime distribution (overall)

| Regime | Count |
|---|---|
| Stationary | 32 |
| Edge | 23 |
| Diffusing | 12 |
| Contracting | 6 |
| Concentrating | 2 |
| Drifting | 1 |

## Regime distribution by observable

| Observable | Concentrating | Contracting | Diffusing | Drifting | Edge | Stationary |
|---|---|---|---|---|---|---|
| PTS_per36 | 1 | 1 | 1 | 0 | 6 | 10 |
| REB_per36 | 0 | 2 | 1 | 0 | 6 | 10 |
| AST_per36 | 0 | 1 | 5 | 0 | 7 | 6 |
| BLK_per36 | 1 | 2 | 5 | 1 | 4 | 6 |

## Normalization fallback (mu_bar < 0.01 or var_bar < 1e-06)
Cells using absolute slope: 0


## Per-cell regime ledger

| cell_id | observable | r_mu | r_var | regime |
|---|---|---|---|---|
| `Center|Mid|Mid_usage` | AST_per36 | +0.0855 | +0.1634 | Diffusing |
| `Center|Mid|Mid_usage` | BLK_per36 | -0.0465 | -0.0625 | Contracting |
| `Center|Mid|Mid_usage` | PTS_per36 | +0.0351 | +0.0304 | Edge |
| `Center|Mid|Mid_usage` | REB_per36 | +0.0010 | -0.0168 | Stationary |
| `Center|Rookie|Mid_usage` | AST_per36 | +0.0577 | -0.0100 | Edge |
| `Center|Rookie|Mid_usage` | BLK_per36 | -0.0067 | -0.0135 | Stationary |
| `Center|Rookie|Mid_usage` | PTS_per36 | -0.0239 | -0.0060 | Edge |
| `Center|Rookie|Mid_usage` | REB_per36 | -0.0003 | +0.0272 | Stationary |
| `Center|Soph_Early|Mid_usage` | AST_per36 | -0.0757 | -0.0923 | Contracting |
| `Center|Soph_Early|Mid_usage` | BLK_per36 | -0.0083 | +0.1199 | Edge |
| `Center|Soph_Early|Mid_usage` | PTS_per36 | -0.0312 | -0.0102 | Edge |
| `Center|Soph_Early|Mid_usage` | REB_per36 | -0.0095 | +0.0649 | Edge |
| `Forward|Deep_vet|Mid_usage` | AST_per36 | +0.0530 | -0.0088 | Edge |
| `Forward|Deep_vet|Mid_usage` | BLK_per36 | -0.0403 | +0.2566 | Drifting |
| `Forward|Deep_vet|Mid_usage` | PTS_per36 | +0.0304 | +0.0625 | Diffusing |
| `Forward|Deep_vet|Mid_usage` | REB_per36 | -0.0187 | +0.0658 | Edge |
| `Forward|Mid|Low_usage` | AST_per36 | +0.0796 | +0.1548 | Diffusing |
| `Forward|Mid|Low_usage` | BLK_per36 | +0.0138 | +0.0126 | Stationary |
| `Forward|Mid|Low_usage` | PTS_per36 | +0.0165 | +0.0326 | Stationary |
| `Forward|Mid|Low_usage` | REB_per36 | -0.0101 | +0.0416 | Stationary |
| `Forward|Mid|Mid_usage` | AST_per36 | +0.0180 | +0.0211 | Stationary |
| `Forward|Mid|Mid_usage` | BLK_per36 | -0.0016 | +0.0308 | Stationary |
| `Forward|Mid|Mid_usage` | PTS_per36 | +0.0050 | -0.0285 | Stationary |
| `Forward|Mid|Mid_usage` | REB_per36 | -0.0061 | +0.0340 | Stationary |
| `Forward|Rookie|Low_usage` | AST_per36 | +0.0602 | +0.1001 | Diffusing |
| `Forward|Rookie|Low_usage` | BLK_per36 | -0.0454 | -0.0817 | Contracting |
| `Forward|Rookie|Low_usage` | PTS_per36 | +0.0072 | -0.0546 | Edge |
| `Forward|Rookie|Low_usage` | REB_per36 | +0.0085 | -0.0549 | Edge |
| `Forward|Rookie|Mid_usage` | AST_per36 | +0.0161 | -0.0106 | Stationary |
| `Forward|Rookie|Mid_usage` | BLK_per36 | +0.0526 | +0.1120 | Diffusing |
| `Forward|Rookie|Mid_usage` | PTS_per36 | +0.0091 | +0.0501 | Edge |
| `Forward|Rookie|Mid_usage` | REB_per36 | +0.0023 | +0.1040 | Edge |
| `Forward|Soph_Early|Low_usage` | AST_per36 | +0.0016 | -0.0300 | Stationary |
| `Forward|Soph_Early|Low_usage` | BLK_per36 | +0.0824 | +0.1135 | Diffusing |
| `Forward|Soph_Early|Low_usage` | PTS_per36 | +0.0161 | +0.0143 | Stationary |
| `Forward|Soph_Early|Low_usage` | REB_per36 | -0.0102 | -0.0017 | Stationary |
| `Forward|Soph_Early|Mid_usage` | AST_per36 | +0.0191 | +0.0314 | Stationary |
| `Forward|Soph_Early|Mid_usage` | BLK_per36 | -0.0269 | -0.0250 | Edge |
| `Forward|Soph_Early|Mid_usage` | PTS_per36 | -0.0066 | +0.0323 | Stationary |
| `Forward|Soph_Early|Mid_usage` | REB_per36 | -0.0278 | -0.0011 | Edge |
| `Guard|Deep_vet|Mid_usage` | AST_per36 | -0.0053 | -0.0362 | Stationary |
| `Guard|Deep_vet|Mid_usage` | BLK_per36 | +0.0555 | -0.0693 | Concentrating |
| `Guard|Deep_vet|Mid_usage` | PTS_per36 | -0.0167 | +0.0285 | Stationary |
| `Guard|Deep_vet|Mid_usage` | REB_per36 | +0.0033 | +0.0258 | Stationary |
| `Guard|Mid|High_usage` | AST_per36 | -0.0226 | -0.0382 | Edge |
| `Guard|Mid|High_usage` | BLK_per36 | -0.0122 | -0.0004 | Stationary |
| `Guard|Mid|High_usage` | PTS_per36 | -0.0158 | -0.0463 | Stationary |
| `Guard|Mid|High_usage` | REB_per36 | -0.0227 | -0.0748 | Contracting |
| `Guard|Mid|Low_usage` | AST_per36 | +0.0707 | +0.0682 | Diffusing |
| `Guard|Mid|Low_usage` | BLK_per36 | +0.0032 | +0.0100 | Stationary |
| `Guard|Mid|Low_usage` | PTS_per36 | -0.0217 | -0.0990 | Contracting |
| `Guard|Mid|Low_usage` | REB_per36 | +0.0463 | +0.0902 | Diffusing |
| `Guard|Mid|Mid_usage` | AST_per36 | +0.0491 | +0.0493 | Edge |
| `Guard|Mid|Mid_usage` | BLK_per36 | +0.0640 | +0.0684 | Diffusing |
| `Guard|Mid|Mid_usage` | PTS_per36 | +0.0054 | +0.0146 | Stationary |
| `Guard|Mid|Mid_usage` | REB_per36 | +0.0055 | +0.0023 | Stationary |
| `Guard|Rookie|Low_usage` | AST_per36 | +0.0568 | +0.1198 | Diffusing |
| `Guard|Rookie|Low_usage` | BLK_per36 | -0.0606 | -0.0378 | Edge |
| `Guard|Rookie|Low_usage` | PTS_per36 | -0.0065 | +0.0183 | Stationary |
| `Guard|Rookie|Low_usage` | REB_per36 | -0.0095 | +0.0120 | Stationary |
| `Guard|Rookie|Mid_usage` | AST_per36 | -0.0030 | +0.0153 | Stationary |
| `Guard|Rookie|Mid_usage` | BLK_per36 | +0.0940 | +0.1623 | Diffusing |
| `Guard|Rookie|Mid_usage` | PTS_per36 | +0.0033 | +0.1678 | Edge |
| `Guard|Rookie|Mid_usage` | REB_per36 | +0.0165 | +0.0748 | Edge |
| `Guard|Soph_Early|High_usage` | AST_per36 | +0.0407 | +0.0238 | Edge |
| `Guard|Soph_Early|High_usage` | BLK_per36 | +0.0316 | +0.0202 | Edge |
| `Guard|Soph_Early|High_usage` | PTS_per36 | +0.0093 | -0.0030 | Stationary |
| `Guard|Soph_Early|High_usage` | REB_per36 | -0.0167 | -0.0358 | Stationary |
| `Guard|Soph_Early|Low_usage` | AST_per36 | +0.0306 | +0.0087 | Edge |
| `Guard|Soph_Early|Low_usage` | BLK_per36 | +0.0550 | +0.2563 | Diffusing |
| `Guard|Soph_Early|Low_usage` | PTS_per36 | +0.0201 | -0.0944 | Concentrating |
| `Guard|Soph_Early|Low_usage` | REB_per36 | -0.0328 | -0.0594 | Contracting |
| `Guard|Soph_Early|Mid_usage` | AST_per36 | -0.0235 | -0.0227 | Edge |
| `Guard|Soph_Early|Mid_usage` | BLK_per36 | +0.0116 | +0.0299 | Stationary |
| `Guard|Soph_Early|Mid_usage` | PTS_per36 | +0.0049 | +0.0328 | Stationary |
| `Guard|Soph_Early|Mid_usage` | REB_per36 | -0.0058 | +0.0384 | Stationary |
