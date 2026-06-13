# Step 2 — Trajectory classification (arm = off_feast)

Locked SHA v1.0: `cd40b46`
(v1.1 amendment not in scope)

Cells classified: 60
Training window: 2019-20 -> 2023-24 (5 seasons)
Thresholds: eps_mu = 0.02, eps_var = 0.05

## Regime distribution (overall)

| Regime | Count |
|---|---|
| Stationary | 26 |
| Edge | 14 |
| Diffusing | 11 |
| Contracting | 8 |
| Concentrating | 1 |

## Regime distribution by observable

| Observable | Concentrating | Contracting | Diffusing | Edge | Stationary |
|---|---|---|---|---|---|
| PTS_per36 | 0 | 0 | 0 | 5 | 10 |
| REB_per36 | 1 | 2 | 1 | 3 | 8 |
| AST_per36 | 0 | 1 | 5 | 2 | 7 |
| BLK_per36 | 0 | 5 | 5 | 4 | 1 |

## Normalization fallback (mu_bar < 0.01 or var_bar < 1e-06)
Cells using absolute slope: 0


## Per-cell regime ledger

| cell_id | observable | r_mu | r_var | regime |
|---|---|---|---|---|
| `Perimeter|Deep_vet|Mid_usage` | AST_per36 | +0.0207 | -0.0487 | Edge |
| `Perimeter|Deep_vet|Mid_usage` | BLK_per36 | +0.0365 | +0.0640 | Diffusing |
| `Perimeter|Deep_vet|Mid_usage` | PTS_per36 | -0.0010 | +0.0175 | Stationary |
| `Perimeter|Deep_vet|Mid_usage` | REB_per36 | -0.0299 | -0.0042 | Edge |
| `Perimeter|Mid|High_usage` | AST_per36 | -0.0196 | -0.0378 | Stationary |
| `Perimeter|Mid|High_usage` | BLK_per36 | -0.0266 | -0.0782 | Contracting |
| `Perimeter|Mid|High_usage` | PTS_per36 | -0.0121 | -0.0437 | Stationary |
| `Perimeter|Mid|High_usage` | REB_per36 | +0.0001 | +0.0008 | Stationary |
| `Perimeter|Mid|Low_usage` | AST_per36 | +0.0463 | +0.0618 | Diffusing |
| `Perimeter|Mid|Low_usage` | BLK_per36 | +0.0234 | +0.0424 | Edge |
| `Perimeter|Mid|Low_usage` | PTS_per36 | -0.0009 | -0.0304 | Stationary |
| `Perimeter|Mid|Low_usage` | REB_per36 | +0.0034 | +0.0397 | Stationary |
| `Perimeter|Mid|Mid_usage` | AST_per36 | +0.0175 | +0.0282 | Stationary |
| `Perimeter|Mid|Mid_usage` | BLK_per36 | +0.0104 | +0.0414 | Stationary |
| `Perimeter|Mid|Mid_usage` | PTS_per36 | +0.0132 | +0.0123 | Stationary |
| `Perimeter|Mid|Mid_usage` | REB_per36 | -0.0168 | -0.0105 | Stationary |
| `Perimeter|Rookie|Low_usage` | AST_per36 | +0.0703 | +0.1341 | Diffusing |
| `Perimeter|Rookie|Low_usage` | BLK_per36 | -0.0561 | -0.0467 | Edge |
| `Perimeter|Rookie|Low_usage` | PTS_per36 | -0.0047 | -0.0102 | Stationary |
| `Perimeter|Rookie|Low_usage` | REB_per36 | -0.0047 | +0.0447 | Stationary |
| `Perimeter|Rookie|Mid_usage` | AST_per36 | -0.0131 | -0.0117 | Stationary |
| `Perimeter|Rookie|Mid_usage` | BLK_per36 | +0.0816 | +0.1006 | Diffusing |
| `Perimeter|Rookie|Mid_usage` | PTS_per36 | +0.0183 | +0.1348 | Edge |
| `Perimeter|Rookie|Mid_usage` | REB_per36 | +0.0106 | +0.0564 | Edge |
| `Perimeter|Soph_Early|High_usage` | AST_per36 | +0.0582 | +0.0801 | Diffusing |
| `Perimeter|Soph_Early|High_usage` | BLK_per36 | -0.0665 | -0.0647 | Contracting |
| `Perimeter|Soph_Early|High_usage` | PTS_per36 | -0.0044 | +0.0090 | Stationary |
| `Perimeter|Soph_Early|High_usage` | REB_per36 | -0.0574 | -0.1279 | Contracting |
| `Perimeter|Soph_Early|Low_usage` | AST_per36 | +0.0200 | +0.0262 | Stationary |
| `Perimeter|Soph_Early|Low_usage` | BLK_per36 | +0.0499 | +0.2182 | Diffusing |
| `Perimeter|Soph_Early|Low_usage` | PTS_per36 | +0.0164 | +0.0163 | Stationary |
| `Perimeter|Soph_Early|Low_usage` | REB_per36 | -0.0525 | -0.0892 | Contracting |
| `Perimeter|Soph_Early|Mid_usage` | AST_per36 | -0.0057 | -0.0151 | Stationary |
| `Perimeter|Soph_Early|Mid_usage` | BLK_per36 | -0.0281 | -0.0586 | Contracting |
| `Perimeter|Soph_Early|Mid_usage` | PTS_per36 | -0.0065 | +0.0249 | Stationary |
| `Perimeter|Soph_Early|Mid_usage` | REB_per36 | -0.0188 | -0.0023 | Stationary |
| `Rim|Mid|Low_usage` | AST_per36 | +0.0749 | +0.1934 | Diffusing |
| `Rim|Mid|Low_usage` | BLK_per36 | -0.0874 | -0.0991 | Contracting |
| `Rim|Mid|Low_usage` | PTS_per36 | -0.0131 | +0.0600 | Edge |
| `Rim|Mid|Low_usage` | REB_per36 | -0.0138 | +0.0418 | Stationary |
| `Rim|Mid|Mid_usage` | AST_per36 | +0.0991 | +0.0961 | Diffusing |
| `Rim|Mid|Mid_usage` | BLK_per36 | -0.1170 | -0.0977 | Contracting |
| `Rim|Mid|Mid_usage` | PTS_per36 | +0.0028 | +0.0096 | Stationary |
| `Rim|Mid|Mid_usage` | REB_per36 | -0.0398 | -0.0184 | Edge |
| `Rim|Rookie|Low_usage` | AST_per36 | +0.0070 | +0.0084 | Stationary |
| `Rim|Rookie|Low_usage` | BLK_per36 | +0.0228 | +0.0052 | Edge |
| `Rim|Rookie|Low_usage` | PTS_per36 | -0.0039 | -0.0933 | Edge |
| `Rim|Rookie|Low_usage` | REB_per36 | +0.0204 | -0.0650 | Concentrating |
| `Rim|Rookie|Mid_usage` | AST_per36 | +0.0400 | +0.0171 | Edge |
| `Rim|Rookie|Mid_usage` | BLK_per36 | +0.0288 | +0.0332 | Edge |
| `Rim|Rookie|Mid_usage` | PTS_per36 | -0.0290 | -0.0237 | Edge |
| `Rim|Rookie|Mid_usage` | REB_per36 | +0.0494 | +0.1078 | Diffusing |
| `Rim|Soph_Early|Low_usage` | AST_per36 | +0.0167 | +0.0397 | Stationary |
| `Rim|Soph_Early|Low_usage` | BLK_per36 | +0.0334 | +0.1192 | Diffusing |
| `Rim|Soph_Early|Low_usage` | PTS_per36 | -0.0082 | -0.0421 | Stationary |
| `Rim|Soph_Early|Low_usage` | REB_per36 | +0.0130 | +0.0091 | Stationary |
| `Rim|Soph_Early|Mid_usage` | AST_per36 | -0.0556 | -0.0950 | Contracting |
| `Rim|Soph_Early|Mid_usage` | BLK_per36 | +0.0228 | +0.0505 | Diffusing |
| `Rim|Soph_Early|Mid_usage` | PTS_per36 | +0.0287 | +0.0358 | Edge |
| `Rim|Soph_Early|Mid_usage` | REB_per36 | -0.0080 | +0.0076 | Stationary |
