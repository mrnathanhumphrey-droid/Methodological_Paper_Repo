# Step 2 — Trajectory classification (arm = def_feast)

Locked SHA v1.0: `cd40b46`
(v1.1 amendment not in scope)

Cells classified: 88
Training window: 2019-20 -> 2023-24 (5 seasons)
Thresholds: eps_mu = 0.02, eps_var = 0.05

## Regime distribution (overall)

| Regime | Count |
|---|---|
| Edge | 35 |
| Diffusing | 19 |
| Stationary | 19 |
| Contracting | 14 |
| Drifting | 1 |

## Regime distribution by observable

| Observable | Contracting | Diffusing | Drifting | Edge | Stationary |
|---|---|---|---|---|---|
| PTS_per36 | 1 | 1 | 1 | 8 | 11 |
| REB_per36 | 5 | 3 | 0 | 10 | 4 |
| AST_per36 | 2 | 8 | 0 | 10 | 2 |
| BLK_per36 | 6 | 7 | 0 | 7 | 2 |

## Normalization fallback (mu_bar < 0.01 or var_bar < 1e-06)
Cells using absolute slope: 0


## Per-cell regime ledger

| cell_id | observable | r_mu | r_var | regime |
|---|---|---|---|---|
| `Hybrid|Deep_vet|Mid_usage` | AST_per36 | +0.0866 | -0.0359 | Edge |
| `Hybrid|Deep_vet|Mid_usage` | BLK_per36 | +0.0503 | +0.1837 | Diffusing |
| `Hybrid|Deep_vet|Mid_usage` | PTS_per36 | +0.0407 | +0.0377 | Edge |
| `Hybrid|Deep_vet|Mid_usage` | REB_per36 | -0.0489 | -0.1411 | Contracting |
| `Hybrid|Mid|High_usage` | AST_per36 | -0.0235 | -0.0252 | Edge |
| `Hybrid|Mid|High_usage` | BLK_per36 | -0.0600 | -0.1111 | Contracting |
| `Hybrid|Mid|High_usage` | PTS_per36 | -0.0171 | -0.0183 | Stationary |
| `Hybrid|Mid|High_usage` | REB_per36 | +0.0085 | +0.0947 | Edge |
| `Hybrid|Mid|Low_usage` | AST_per36 | +0.0246 | +0.0676 | Diffusing |
| `Hybrid|Mid|Low_usage` | BLK_per36 | +0.0452 | +0.1136 | Diffusing |
| `Hybrid|Mid|Low_usage` | PTS_per36 | -0.0109 | +0.0208 | Stationary |
| `Hybrid|Mid|Low_usage` | REB_per36 | +0.0107 | +0.0177 | Stationary |
| `Hybrid|Mid|Mid_usage` | AST_per36 | +0.0216 | +0.0713 | Diffusing |
| `Hybrid|Mid|Mid_usage` | BLK_per36 | -0.0168 | -0.0189 | Stationary |
| `Hybrid|Mid|Mid_usage` | PTS_per36 | +0.0073 | +0.0374 | Stationary |
| `Hybrid|Mid|Mid_usage` | REB_per36 | -0.0371 | +0.0214 | Edge |
| `Hybrid|Rookie|Low_usage` | AST_per36 | +0.0662 | +0.0372 | Edge |
| `Hybrid|Rookie|Low_usage` | BLK_per36 | -0.0208 | -0.0378 | Edge |
| `Hybrid|Rookie|Low_usage` | PTS_per36 | +0.0044 | +0.0010 | Stationary |
| `Hybrid|Rookie|Low_usage` | REB_per36 | -0.0011 | -0.0635 | Edge |
| `Hybrid|Rookie|Mid_usage` | AST_per36 | -0.0399 | -0.0085 | Edge |
| `Hybrid|Rookie|Mid_usage` | BLK_per36 | +0.1293 | +0.2361 | Diffusing |
| `Hybrid|Rookie|Mid_usage` | PTS_per36 | -0.0159 | +0.0083 | Stationary |
| `Hybrid|Rookie|Mid_usage` | REB_per36 | +0.0748 | +0.1928 | Diffusing |
| `Hybrid|Soph_Early|High_usage` | AST_per36 | +0.0257 | +0.0429 | Edge |
| `Hybrid|Soph_Early|High_usage` | BLK_per36 | -0.0726 | -0.0830 | Contracting |
| `Hybrid|Soph_Early|High_usage` | PTS_per36 | +0.0061 | +0.0276 | Stationary |
| `Hybrid|Soph_Early|High_usage` | REB_per36 | -0.0306 | -0.1662 | Contracting |
| `Hybrid|Soph_Early|Low_usage` | AST_per36 | +0.0192 | +0.0502 | Edge |
| `Hybrid|Soph_Early|Low_usage` | BLK_per36 | +0.0376 | +0.2294 | Diffusing |
| `Hybrid|Soph_Early|Low_usage` | PTS_per36 | +0.0314 | +0.1335 | Diffusing |
| `Hybrid|Soph_Early|Low_usage` | REB_per36 | -0.0392 | -0.0182 | Edge |
| `Hybrid|Soph_Early|Mid_usage` | AST_per36 | -0.0625 | -0.0792 | Contracting |
| `Hybrid|Soph_Early|Mid_usage` | BLK_per36 | -0.0160 | -0.0402 | Stationary |
| `Hybrid|Soph_Early|Mid_usage` | PTS_per36 | +0.0135 | +0.0099 | Stationary |
| `Hybrid|Soph_Early|Mid_usage` | REB_per36 | -0.0113 | -0.0312 | Stationary |
| `Perimeter|Deep_vet|Mid_usage` | AST_per36 | -0.0226 | +0.0047 | Edge |
| `Perimeter|Deep_vet|Mid_usage` | BLK_per36 | -0.0602 | -0.0112 | Edge |
| `Perimeter|Deep_vet|Mid_usage` | PTS_per36 | -0.0709 | +0.0367 | Edge |
| `Perimeter|Deep_vet|Mid_usage` | REB_per36 | -0.0177 | +0.1684 | Edge |
| `Perimeter|Mid|High_usage` | AST_per36 | -0.0332 | -0.0724 | Contracting |
| `Perimeter|Mid|High_usage` | BLK_per36 | +0.0233 | +0.0040 | Edge |
| `Perimeter|Mid|High_usage` | PTS_per36 | -0.0250 | -0.1045 | Contracting |
| `Perimeter|Mid|High_usage` | REB_per36 | -0.0137 | -0.1552 | Edge |
| `Perimeter|Mid|Low_usage` | AST_per36 | +0.0984 | +0.1426 | Diffusing |
| `Perimeter|Mid|Low_usage` | BLK_per36 | -0.1162 | -0.0926 | Contracting |
| `Perimeter|Mid|Low_usage` | PTS_per36 | -0.0181 | -0.0703 | Edge |
| `Perimeter|Mid|Low_usage` | REB_per36 | -0.0696 | -0.0740 | Contracting |
| `Perimeter|Mid|Mid_usage` | AST_per36 | +0.0735 | +0.0619 | Diffusing |
| `Perimeter|Mid|Mid_usage` | BLK_per36 | -0.0517 | +0.0020 | Edge |
| `Perimeter|Mid|Mid_usage` | PTS_per36 | +0.0043 | +0.0075 | Stationary |
| `Perimeter|Mid|Mid_usage` | REB_per36 | -0.0485 | -0.1390 | Contracting |
| `Perimeter|Rookie|Mid_usage` | AST_per36 | +0.0331 | +0.0534 | Diffusing |
| `Perimeter|Rookie|Mid_usage` | BLK_per36 | -0.0784 | -0.0748 | Contracting |
| `Perimeter|Rookie|Mid_usage` | PTS_per36 | -0.0273 | +0.1976 | Drifting |
| `Perimeter|Rookie|Mid_usage` | REB_per36 | -0.0428 | -0.0157 | Edge |
| `Perimeter|Soph_Early|Low_usage` | AST_per36 | +0.0294 | +0.0794 | Diffusing |
| `Perimeter|Soph_Early|Low_usage` | BLK_per36 | +0.0138 | +0.1767 | Edge |
| `Perimeter|Soph_Early|Low_usage` | PTS_per36 | +0.0159 | -0.0444 | Stationary |
| `Perimeter|Soph_Early|Low_usage` | REB_per36 | -0.0369 | -0.0445 | Edge |
| `Perimeter|Soph_Early|Mid_usage` | AST_per36 | +0.0229 | -0.0158 | Edge |
| `Perimeter|Soph_Early|Mid_usage` | BLK_per36 | -0.0590 | -0.0711 | Contracting |
| `Perimeter|Soph_Early|Mid_usage` | PTS_per36 | -0.0097 | +0.0417 | Stationary |
| `Perimeter|Soph_Early|Mid_usage` | REB_per36 | -0.0425 | -0.0619 | Contracting |
| `RimProtector|Mid|Low_usage` | AST_per36 | +0.0041 | +0.0357 | Stationary |
| `RimProtector|Mid|Low_usage` | BLK_per36 | +0.0040 | -0.1238 | Edge |
| `RimProtector|Mid|Low_usage` | PTS_per36 | +0.0288 | +0.0293 | Edge |
| `RimProtector|Mid|Low_usage` | REB_per36 | +0.0831 | +0.0625 | Diffusing |
| `RimProtector|Mid|Mid_usage` | AST_per36 | +0.1109 | +0.1619 | Diffusing |
| `RimProtector|Mid|Mid_usage` | BLK_per36 | -0.0850 | -0.1572 | Contracting |
| `RimProtector|Mid|Mid_usage` | PTS_per36 | +0.0326 | +0.0170 | Edge |
| `RimProtector|Mid|Mid_usage` | REB_per36 | -0.0084 | -0.0557 | Edge |
| `RimProtector|Rookie|Low_usage` | AST_per36 | +0.0440 | +0.0858 | Diffusing |
| `RimProtector|Rookie|Low_usage` | BLK_per36 | +0.0288 | +0.0527 | Diffusing |
| `RimProtector|Rookie|Low_usage` | PTS_per36 | -0.0129 | -0.1074 | Edge |
| `RimProtector|Rookie|Low_usage` | REB_per36 | +0.0288 | +0.0681 | Diffusing |
| `RimProtector|Rookie|Mid_usage` | AST_per36 | -0.0007 | -0.0412 | Stationary |
| `RimProtector|Rookie|Mid_usage` | BLK_per36 | +0.0361 | +0.0321 | Edge |
| `RimProtector|Rookie|Mid_usage` | PTS_per36 | +0.0314 | +0.0166 | Edge |
| `RimProtector|Rookie|Mid_usage` | REB_per36 | +0.0089 | +0.0165 | Stationary |
| `RimProtector|Soph_Early|Low_usage` | AST_per36 | +0.0006 | -0.0523 | Edge |
| `RimProtector|Soph_Early|Low_usage` | BLK_per36 | +0.0614 | +0.0865 | Diffusing |
| `RimProtector|Soph_Early|Low_usage` | PTS_per36 | -0.0197 | -0.0808 | Edge |
| `RimProtector|Soph_Early|Low_usage` | REB_per36 | +0.0037 | -0.0004 | Stationary |
| `RimProtector|Soph_Early|Mid_usage` | AST_per36 | +0.0182 | +0.0851 | Edge |
| `RimProtector|Soph_Early|Mid_usage` | BLK_per36 | +0.0430 | +0.0586 | Diffusing |
| `RimProtector|Soph_Early|Mid_usage` | PTS_per36 | -0.0034 | +0.0193 | Stationary |
| `RimProtector|Soph_Early|Mid_usage` | REB_per36 | +0.0066 | +0.0930 | Edge |
