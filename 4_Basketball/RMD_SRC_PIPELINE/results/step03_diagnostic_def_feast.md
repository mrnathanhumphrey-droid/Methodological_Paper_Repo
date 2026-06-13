# Step 3 — response validation (arm = def_feast)

Locked v1.0 SHA: `cd40b46`
(v1.1 amendment not in scope)

## Headline
- Cells classified at Step 2: **88**
- Cells passing all 3 Step-3 checks: **0**  (0.0%)
- Pass by individual check (cells passing this check):
  - Hartigan dip  (p ≥ 0.05): 0/88
  - Permutation   (modal ≥ 60%): 16/88
  - LOSO 5-fold   (≥ 3 match orig): 72/88

## Pass rate by original Step-2 regime
| regime | n | clean | % clean |
|---|---|---|---|
| Contracting | 14 | 0 | 0.0% |
| Diffusing | 19 | 0 | 0.0% |
| Drifting | 1 | 0 | 0.0% |
| Edge | 35 | 0 | 0.0% |
| Stationary | 19 | 0 | 0.0% |

## F2 preview (Stationary auto-clean + non-Stationary passing Step 3, excluding Edge)
| observable | n_cells | n_Stationary | n_Edge | n_nonStat_clean | terminates_cleanly (pre-Step-4) | % of (n - Edge) |
|---|---|---|---|---|---|---|
| AST_per36 | 22 | 2 | 10 | 0 | 2 | 16.7% |
| BLK_per36 | 22 | 2 | 7 | 0 | 2 | 13.3% |
| PTS_per36 | 22 | 11 | 8 | 0 | 11 | 78.6% |
| REB_per36 | 22 | 4 | 10 | 0 | 4 | 33.3% |

## Non-Stationary cells passing Step 3 (load-bearing for Step 4 4a/4b)

*(none)*

## Full per-cell ledger
| cell_id | observable | regime | dip | perm | loso | clean | failed |
|---|---|---|---|---|---|---|---|
| `Hybrid|Deep_vet|Mid_usage` | AST_per36 | Edge | 0.000 | 0.70 | 4/5 | N | dip |
| `Hybrid|Deep_vet|Mid_usage` | BLK_per36 | Diffusing | 0.000 | 0.41 | 4/5 | N | dip|perm |
| `Hybrid|Deep_vet|Mid_usage` | PTS_per36 | Edge | 0.000 | 0.67 | 3/5 | N | dip |
| `Hybrid|Deep_vet|Mid_usage` | REB_per36 | Contracting | 0.000 | 0.35 | 5/5 | N | dip|perm |
| `Hybrid|Mid|High_usage` | AST_per36 | Edge | 0.001 | 0.27 | 4/5 | N | dip|perm |
| `Hybrid|Mid|High_usage` | BLK_per36 | Contracting | 0.000 | 0.29 | 4/5 | N | dip|perm |
| `Hybrid|Mid|High_usage` | PTS_per36 | Stationary | 0.036 | 0.77 | 3/5 | N | dip |
| `Hybrid|Mid|High_usage` | REB_per36 | Edge | 0.025 | 0.48 | 3/5 | N | dip|perm |
| `Hybrid|Mid|Low_usage` | AST_per36 | Diffusing | 0.000 | 0.20 | 4/5 | N | dip|perm |
| `Hybrid|Mid|Low_usage` | BLK_per36 | Diffusing | 0.000 | 0.29 | 3/5 | N | dip|perm |
| `Hybrid|Mid|Low_usage` | PTS_per36 | Stationary | 0.000 | 0.73 | 4/5 | N | dip |
| `Hybrid|Mid|Low_usage` | REB_per36 | Stationary | 0.000 | 0.23 | 3/5 | N | dip|perm |
| `Hybrid|Mid|Mid_usage` | AST_per36 | Diffusing | 0.000 | 0.22 | 4/5 | N | dip|perm |
| `Hybrid|Mid|Mid_usage` | BLK_per36 | Stationary | 0.000 | 0.03 | 2/5 | N | dip|perm|loso |
| `Hybrid|Mid|Mid_usage` | PTS_per36 | Stationary | 0.000 | 0.90 | 4/5 | N | dip |
| `Hybrid|Mid|Mid_usage` | REB_per36 | Edge | 0.000 | 0.43 | 4/5 | N | dip|perm |
| `Hybrid|Rookie|Low_usage` | AST_per36 | Edge | 0.000 | 0.62 | 3/5 | N | dip |
| `Hybrid|Rookie|Low_usage` | BLK_per36 | Edge | 0.000 | 0.23 | 2/5 | N | dip|perm|loso |
| `Hybrid|Rookie|Low_usage` | PTS_per36 | Stationary | 0.000 | 0.42 | 4/5 | N | dip|perm |
| `Hybrid|Rookie|Low_usage` | REB_per36 | Edge | 0.000 | 0.60 | 2/5 | N | dip|loso |
| `Hybrid|Rookie|Mid_usage` | AST_per36 | Edge | 0.000 | 0.62 | 3/5 | N | dip |
| `Hybrid|Rookie|Mid_usage` | BLK_per36 | Diffusing | 0.000 | 0.32 | 5/5 | N | dip|perm |
| `Hybrid|Rookie|Mid_usage` | PTS_per36 | Stationary | 0.000 | 0.38 | 3/5 | N | dip|perm |
| `Hybrid|Rookie|Mid_usage` | REB_per36 | Diffusing | 0.000 | 0.21 | 5/5 | N | dip|perm |
| `Hybrid|Soph_Early|High_usage` | AST_per36 | Edge | 0.010 | 0.38 | 4/5 | N | dip|perm |
| `Hybrid|Soph_Early|High_usage` | BLK_per36 | Contracting | 0.000 | 0.20 | 4/5 | N | dip|perm |
| `Hybrid|Soph_Early|High_usage` | PTS_per36 | Stationary | 0.027 | 0.73 | 4/5 | N | dip |
| `Hybrid|Soph_Early|High_usage` | REB_per36 | Contracting | 0.000 | 0.22 | 3/5 | N | dip|perm |
| `Hybrid|Soph_Early|Low_usage` | AST_per36 | Edge | 0.000 | 0.48 | 2/5 | N | dip|perm|loso |
| `Hybrid|Soph_Early|Low_usage` | BLK_per36 | Diffusing | 0.000 | 0.10 | 4/5 | N | dip|perm |
| `Hybrid|Soph_Early|Low_usage` | PTS_per36 | Diffusing | 0.000 | 0.19 | 3/5 | N | dip|perm |
| `Hybrid|Soph_Early|Low_usage` | REB_per36 | Edge | 0.000 | 0.57 | 3/5 | N | dip|perm |
| `Hybrid|Soph_Early|Mid_usage` | AST_per36 | Contracting | 0.000 | 0.22 | 4/5 | N | dip|perm |
| `Hybrid|Soph_Early|Mid_usage` | BLK_per36 | Stationary | 0.000 | 0.25 | 2/5 | N | dip|perm|loso |
| `Hybrid|Soph_Early|Mid_usage` | PTS_per36 | Stationary | 0.000 | 0.97 | 4/5 | N | dip |
| `Hybrid|Soph_Early|Mid_usage` | REB_per36 | Stationary | 0.000 | 0.53 | 3/5 | N | dip|perm |
| `Perimeter|Deep_vet|Mid_usage` | AST_per36 | Edge | 0.000 | 0.35 | 3/5 | N | dip|perm |
| `Perimeter|Deep_vet|Mid_usage` | BLK_per36 | Edge | 0.000 | 0.45 | 4/5 | N | dip|perm |
| `Perimeter|Deep_vet|Mid_usage` | PTS_per36 | Edge | 0.000 | 0.53 | 3/5 | N | dip|perm |
| `Perimeter|Deep_vet|Mid_usage` | REB_per36 | Edge | 0.000 | 0.62 | 4/5 | N | dip |
| `Perimeter|Mid|High_usage` | AST_per36 | Contracting | 0.000 | 0.11 | 3/5 | N | dip|perm |
| `Perimeter|Mid|High_usage` | BLK_per36 | Edge | 0.000 | 0.28 | 3/5 | N | dip|perm |
| `Perimeter|Mid|High_usage` | PTS_per36 | Contracting | 0.001 | 0.12 | 3/5 | N | dip|perm |
| `Perimeter|Mid|High_usage` | REB_per36 | Edge | 0.003 | 0.53 | 3/5 | N | dip|perm |
| `Perimeter|Mid|Low_usage` | AST_per36 | Diffusing | 0.000 | 0.27 | 5/5 | N | dip|perm |
| `Perimeter|Mid|Low_usage` | BLK_per36 | Contracting | 0.000 | 0.30 | 4/5 | N | dip|perm |
| `Perimeter|Mid|Low_usage` | PTS_per36 | Edge | 0.000 | 0.45 | 2/5 | N | dip|perm|loso |
| `Perimeter|Mid|Low_usage` | REB_per36 | Contracting | 0.000 | 0.28 | 4/5 | N | dip|perm |
| `Perimeter|Mid|Mid_usage` | AST_per36 | Diffusing | 0.000 | 0.20 | 4/5 | N | dip|perm |
| `Perimeter|Mid|Mid_usage` | BLK_per36 | Edge | 0.000 | 0.38 | 1/5 | N | dip|perm|loso |
| `Perimeter|Mid|Mid_usage` | PTS_per36 | Stationary | 0.000 | 1.00 | 5/5 | N | dip |
| `Perimeter|Mid|Mid_usage` | REB_per36 | Contracting | 0.000 | 0.33 | 5/5 | N | dip|perm |
| `Perimeter|Rookie|Mid_usage` | AST_per36 | Diffusing | 0.000 | 0.06 | 3/5 | N | dip|perm |
| `Perimeter|Rookie|Mid_usage` | BLK_per36 | Contracting | 0.000 | 0.34 | 3/5 | N | dip|perm |
| `Perimeter|Rookie|Mid_usage` | PTS_per36 | Drifting | 0.000 | 0.10 | 5/5 | N | dip|perm |
| `Perimeter|Rookie|Mid_usage` | REB_per36 | Edge | 0.000 | 0.35 | 4/5 | N | dip|perm |
| `Perimeter|Soph_Early|Low_usage` | AST_per36 | Diffusing | 0.000 | 0.28 | 4/5 | N | dip|perm |
| `Perimeter|Soph_Early|Low_usage` | BLK_per36 | Edge | 0.000 | 0.37 | 2/5 | N | dip|perm|loso |
| `Perimeter|Soph_Early|Low_usage` | PTS_per36 | Stationary | 0.000 | 0.25 | 3/5 | N | dip|perm |
| `Perimeter|Soph_Early|Low_usage` | REB_per36 | Edge | 0.000 | 0.43 | 2/5 | N | dip|perm|loso |
| `Perimeter|Soph_Early|Mid_usage` | AST_per36 | Edge | 0.000 | 0.55 | 3/5 | N | dip|perm |
| `Perimeter|Soph_Early|Mid_usage` | BLK_per36 | Contracting | 0.000 | 0.27 | 4/5 | N | dip|perm |
| `Perimeter|Soph_Early|Mid_usage` | PTS_per36 | Stationary | 0.000 | 0.63 | 3/5 | N | dip |
| `Perimeter|Soph_Early|Mid_usage` | REB_per36 | Contracting | 0.000 | 0.14 | 4/5 | N | dip|perm |
| `RimProtector|Mid|Low_usage` | AST_per36 | Stationary | 0.000 | 0.10 | 2/5 | N | dip|perm|loso |
| `RimProtector|Mid|Low_usage` | BLK_per36 | Edge | 0.000 | 0.43 | 3/5 | N | dip|perm |
| `RimProtector|Mid|Low_usage` | PTS_per36 | Edge | 0.000 | 0.40 | 1/5 | N | dip|perm|loso |
| `RimProtector|Mid|Low_usage` | REB_per36 | Diffusing | 0.000 | 0.15 | 3/5 | N | dip|perm |
| `RimProtector|Mid|Mid_usage` | AST_per36 | Diffusing | 0.000 | 0.29 | 5/5 | N | dip|perm |
| `RimProtector|Mid|Mid_usage` | BLK_per36 | Contracting | 0.000 | 0.34 | 5/5 | N | dip|perm |
| `RimProtector|Mid|Mid_usage` | PTS_per36 | Edge | 0.000 | 0.57 | 3/5 | N | dip|perm |
| `RimProtector|Mid|Mid_usage` | REB_per36 | Edge | 0.000 | 0.38 | 4/5 | N | dip|perm |
| `RimProtector|Rookie|Low_usage` | AST_per36 | Diffusing | 0.000 | 0.20 | 3/5 | N | dip|perm |
| `RimProtector|Rookie|Low_usage` | BLK_per36 | Diffusing | 0.000 | 0.30 | 2/5 | N | dip|perm|loso |
| `RimProtector|Rookie|Low_usage` | PTS_per36 | Edge | 0.000 | 0.52 | 5/5 | N | dip|perm |
| `RimProtector|Rookie|Low_usage` | REB_per36 | Diffusing | 0.000 | 0.17 | 3/5 | N | dip|perm |
| `RimProtector|Rookie|Mid_usage` | AST_per36 | Stationary | 0.000 | 0.48 | 4/5 | N | dip|perm |
| `RimProtector|Rookie|Mid_usage` | BLK_per36 | Edge | 0.000 | 0.25 | 1/5 | N | dip|perm|loso |
| `RimProtector|Rookie|Mid_usage` | PTS_per36 | Edge | 0.000 | 0.47 | 3/5 | N | dip|perm |
| `RimProtector|Rookie|Mid_usage` | REB_per36 | Stationary | 0.000 | 0.32 | 3/5 | N | dip|perm |
| `RimProtector|Soph_Early|Low_usage` | AST_per36 | Edge | 0.000 | 0.67 | 2/5 | N | dip|loso |
| `RimProtector|Soph_Early|Low_usage` | BLK_per36 | Diffusing | 0.000 | 0.11 | 4/5 | N | dip|perm |
| `RimProtector|Soph_Early|Low_usage` | PTS_per36 | Edge | 0.000 | 0.47 | 1/5 | N | dip|perm|loso |
| `RimProtector|Soph_Early|Low_usage` | REB_per36 | Stationary | 0.000 | 0.65 | 4/5 | N | dip |
| `RimProtector|Soph_Early|Mid_usage` | AST_per36 | Edge | 0.000 | 0.47 | 3/5 | N | dip|perm |
| `RimProtector|Soph_Early|Mid_usage` | BLK_per36 | Diffusing | 0.000 | 0.14 | 2/5 | N | dip|perm|loso |
| `RimProtector|Soph_Early|Mid_usage` | PTS_per36 | Stationary | 0.000 | 0.90 | 4/5 | N | dip |
| `RimProtector|Soph_Early|Mid_usage` | REB_per36 | Edge | 0.000 | 0.38 | 5/5 | N | dip|perm |
