# Step 3 — response validation (arm = mpg)

Locked v1.0 SHA: `db0ed9a899c28691183cd5b640f460c10f3c2a75`
Locked v1.1 SHA: `4d0602df832d5a45402a212acf48b19a4dfee070`

## Headline
- Cells classified at Step 2: **84**
- Cells passing all 3 Step-3 checks: **0**  (0.0%)
- Pass by individual check (cells passing this check):
  - Hartigan dip  (p ≥ 0.05): 0/84
  - Permutation   (modal ≥ 60%): 17/84
  - LOSO 5-fold   (≥ 3 match orig): 67/84

## Pass rate by original Step-2 regime
| regime | n | clean | % clean |
|---|---|---|---|
| Concentrating | 1 | 0 | 0.0% |
| Contracting | 4 | 0 | 0.0% |
| Diffusing | 9 | 0 | 0.0% |
| Drifting | 1 | 0 | 0.0% |
| Edge | 35 | 0 | 0.0% |
| Stationary | 34 | 0 | 0.0% |

## F2 preview (Stationary auto-clean + non-Stationary passing Step 3, excluding Edge)
| observable | n_cells | n_Stationary | n_Edge | n_nonStat_clean | terminates_cleanly (pre-Step-4) | % of (n - Edge) |
|---|---|---|---|---|---|---|
| AST_per36 | 21 | 8 | 6 | 0 | 8 | 53.3% |
| BLK_per36 | 21 | 8 | 7 | 0 | 8 | 57.1% |
| PTS_per36 | 21 | 9 | 11 | 0 | 9 | 90.0% |
| REB_per36 | 21 | 9 | 11 | 0 | 9 | 90.0% |

## Non-Stationary cells passing Step 3 (load-bearing for Step 4 4a/4b)

*(none)*

## Full per-cell ledger
| cell_id | observable | regime | dip | perm | loso | clean | failed |
|---|---|---|---|---|---|---|---|
| `Center|Mid|Rotation` | AST_per36 | Diffusing | 0.000 | 0.28 | 5/5 | N | dip|perm |
| `Center|Mid|Rotation` | BLK_per36 | Contracting | 0.000 | 0.12 | 4/5 | N | dip|perm |
| `Center|Mid|Rotation` | PTS_per36 | Edge | 0.000 | 0.35 | 4/5 | N | dip|perm |
| `Center|Mid|Rotation` | REB_per36 | Stationary | 0.000 | 0.90 | 5/5 | N | dip |
| `Center|Rookie|Rotation` | AST_per36 | Edge | 0.000 | 0.50 | 2/5 | N | dip|perm|loso |
| `Center|Rookie|Rotation` | BLK_per36 | Stationary | 0.000 | 0.20 | 3/5 | N | dip|perm |
| `Center|Rookie|Rotation` | PTS_per36 | Edge | 0.000 | 0.50 | 1/5 | N | dip|perm|loso |
| `Center|Rookie|Rotation` | REB_per36 | Stationary | 0.000 | 0.13 | 4/5 | N | dip|perm |
| `Center|Soph_Early|Rotation` | AST_per36 | Contracting | 0.000 | 0.26 | 5/5 | N | dip|perm |
| `Center|Soph_Early|Rotation` | BLK_per36 | Edge | 0.000 | 0.70 | 4/5 | N | dip |
| `Center|Soph_Early|Rotation` | PTS_per36 | Edge | 0.000 | 0.40 | 4/5 | N | dip|perm |
| `Center|Soph_Early|Rotation` | REB_per36 | Edge | 0.000 | 0.53 | 3/5 | N | dip|perm |
| `Forward|Deep_vet|Rotation` | AST_per36 | Edge | 0.000 | 0.62 | 4/5 | N | dip |
| `Forward|Deep_vet|Rotation` | BLK_per36 | Drifting | 0.000 | 0.16 | 3/5 | N | dip|perm |
| `Forward|Deep_vet|Rotation` | PTS_per36 | Diffusing | 0.000 | 0.03 | 3/5 | N | dip|perm |
| `Forward|Deep_vet|Rotation` | REB_per36 | Edge | 0.000 | 0.58 | 4/5 | N | dip|perm |
| `Forward|Mid|Bench` | AST_per36 | Diffusing | 0.000 | 0.35 | 4/5 | N | dip|perm |
| `Forward|Mid|Bench` | BLK_per36 | Edge | 0.000 | 0.40 | 2/5 | N | dip|perm|loso |
| `Forward|Mid|Bench` | PTS_per36 | Stationary | 0.000 | 0.20 | 1/5 | N | dip|perm|loso |
| `Forward|Mid|Bench` | REB_per36 | Edge | 0.000 | 0.62 | 2/5 | N | dip|loso |
| `Forward|Mid|Rotation` | AST_per36 | Diffusing | 0.000 | 0.28 | 5/5 | N | dip|perm |
| `Forward|Mid|Rotation` | BLK_per36 | Edge | 0.000 | 0.35 | 2/5 | N | dip|perm|loso |
| `Forward|Mid|Rotation` | PTS_per36 | Stationary | 0.000 | 0.82 | 5/5 | N | dip |
| `Forward|Mid|Rotation` | REB_per36 | Stationary | 0.000 | 0.50 | 4/5 | N | dip|perm |
| `Forward|Mid|Starter` | AST_per36 | Stationary | 0.000 | 0.42 | 4/5 | N | dip|perm |
| `Forward|Mid|Starter` | BLK_per36 | Stationary | 0.000 | 0.52 | 2/5 | N | dip|perm|loso |
| `Forward|Mid|Starter` | PTS_per36 | Edge | 0.001 | 0.38 | 4/5 | N | dip|perm |
| `Forward|Mid|Starter` | REB_per36 | Stationary | 0.000 | 0.62 | 4/5 | N | dip |
| `Forward|Rookie|Bench` | AST_per36 | Diffusing | 0.000 | 0.24 | 4/5 | N | dip|perm |
| `Forward|Rookie|Bench` | BLK_per36 | Stationary | 0.000 | 0.25 | 2/5 | N | dip|perm|loso |
| `Forward|Rookie|Bench` | PTS_per36 | Stationary | 0.000 | 0.25 | 3/5 | N | dip|perm |
| `Forward|Rookie|Bench` | REB_per36 | Stationary | 0.000 | 0.80 | 5/5 | N | dip |
| `Forward|Rookie|Rotation` | AST_per36 | Stationary | 0.000 | 0.43 | 2/5 | N | dip|perm|loso |
| `Forward|Rookie|Rotation` | BLK_per36 | Stationary | 0.000 | 0.18 | 1/5 | N | dip|perm|loso |
| `Forward|Rookie|Rotation` | PTS_per36 | Stationary | 0.000 | 0.33 | 3/5 | N | dip|perm |
| `Forward|Rookie|Rotation` | REB_per36 | Edge | 0.000 | 0.33 | 5/5 | N | dip|perm |
| `Forward|Soph_Early|Bench` | AST_per36 | Stationary | 0.000 | 0.58 | 4/5 | N | dip|perm |
| `Forward|Soph_Early|Bench` | BLK_per36 | Edge | 0.000 | 0.35 | 4/5 | N | dip|perm |
| `Forward|Soph_Early|Bench` | PTS_per36 | Edge | 0.000 | 0.17 | 3/5 | N | dip|perm |
| `Forward|Soph_Early|Bench` | REB_per36 | Stationary | 0.000 | 0.55 | 3/5 | N | dip|perm |
| `Forward|Soph_Early|Rotation` | AST_per36 | Stationary | 0.000 | 0.40 | 4/5 | N | dip|perm |
| `Forward|Soph_Early|Rotation` | BLK_per36 | Stationary | 0.000 | 0.62 | 3/5 | N | dip |
| `Forward|Soph_Early|Rotation` | PTS_per36 | Stationary | 0.000 | 0.95 | 3/5 | N | dip |
| `Forward|Soph_Early|Rotation` | REB_per36 | Edge | 0.000 | 0.35 | 4/5 | N | dip|perm |
| `Forward|Soph_Early|Starter` | AST_per36 | Edge | 0.000 | 0.27 | 1/5 | N | dip|perm|loso |
| `Forward|Soph_Early|Starter` | BLK_per36 | Stationary | 0.000 | 0.18 | 4/5 | N | dip|perm |
| `Forward|Soph_Early|Starter` | PTS_per36 | Edge | 0.001 | 0.05 | 4/5 | N | dip|perm |
| `Forward|Soph_Early|Starter` | REB_per36 | Contracting | 0.000 | 0.13 | 5/5 | N | dip|perm |
| `Guard|Deep_vet|Rotation` | AST_per36 | Stationary | 0.000 | 0.50 | 3/5 | N | dip|perm |
| `Guard|Deep_vet|Rotation` | BLK_per36 | Concentrating | 0.000 | 0.06 | 3/5 | N | dip|perm |
| `Guard|Deep_vet|Rotation` | PTS_per36 | Stationary | 0.000 | 0.38 | 3/5 | N | dip|perm |
| `Guard|Deep_vet|Rotation` | REB_per36 | Stationary | 0.000 | 0.83 | 4/5 | N | dip |
| `Guard|Mid|Bench` | AST_per36 | Edge | 0.000 | 0.32 | 2/5 | N | dip|perm|loso |
| `Guard|Mid|Bench` | BLK_per36 | Diffusing | 0.001 | 0.33 | 4/5 | N | dip|perm |
| `Guard|Mid|Bench` | PTS_per36 | Edge | 0.000 | 0.45 | 4/5 | N | dip|perm |
| `Guard|Mid|Bench` | REB_per36 | Edge | 0.000 | 0.42 | 5/5 | N | dip|perm |
| `Guard|Mid|Rotation` | AST_per36 | Diffusing | 0.000 | 0.15 | 5/5 | N | dip|perm |
| `Guard|Mid|Rotation` | BLK_per36 | Edge | 0.000 | 0.32 | 4/5 | N | dip|perm |
| `Guard|Mid|Rotation` | PTS_per36 | Stationary | 0.000 | 0.63 | 4/5 | N | dip |
| `Guard|Mid|Rotation` | REB_per36 | Edge | 0.000 | 0.18 | 5/5 | N | dip|perm |
| `Guard|Mid|Starter` | AST_per36 | Stationary | 0.000 | 0.48 | 3/5 | N | dip|perm |
| `Guard|Mid|Starter` | BLK_per36 | Stationary | 0.000 | 0.32 | 1/5 | N | dip|perm|loso |
| `Guard|Mid|Starter` | PTS_per36 | Edge | 0.000 | 0.43 | 4/5 | N | dip|perm |
| `Guard|Mid|Starter` | REB_per36 | Edge | 0.000 | 0.15 | 3/5 | N | dip|perm |
| `Guard|Rookie|Bench` | AST_per36 | Edge | 0.000 | 0.58 | 4/5 | N | dip|perm |
| `Guard|Rookie|Bench` | BLK_per36 | Edge | 0.000 | 0.40 | 2/5 | N | dip|perm|loso |
| `Guard|Rookie|Bench` | PTS_per36 | Edge | 0.000 | 0.40 | 5/5 | N | dip|perm |
| `Guard|Rookie|Bench` | REB_per36 | Edge | 0.000 | 0.50 | 5/5 | N | dip|perm |
| `Guard|Rookie|Rotation` | AST_per36 | Stationary | 0.000 | 0.60 | 4/5 | N | dip |
| `Guard|Rookie|Rotation` | BLK_per36 | Diffusing | 0.000 | 0.35 | 4/5 | N | dip|perm |
| `Guard|Rookie|Rotation` | PTS_per36 | Edge | 0.000 | 0.50 | 3/5 | N | dip|perm |
| `Guard|Rookie|Rotation` | REB_per36 | Edge | 0.000 | 0.30 | 2/5 | N | dip|perm|loso |
| `Guard|Soph_Early|Bench` | AST_per36 | Contracting | 0.000 | 0.06 | 4/5 | N | dip|perm |
| `Guard|Soph_Early|Bench` | BLK_per36 | Diffusing | 0.000 | 0.18 | 4/5 | N | dip|perm |
| `Guard|Soph_Early|Bench` | PTS_per36 | Edge | 0.000 | 0.58 | 4/5 | N | dip|perm |
| `Guard|Soph_Early|Bench` | REB_per36 | Edge | 0.000 | 0.43 | 3/5 | N | dip|perm |
| `Guard|Soph_Early|Rotation` | AST_per36 | Stationary | 0.000 | 0.27 | 3/5 | N | dip|perm |
| `Guard|Soph_Early|Rotation` | BLK_per36 | Edge | 0.000 | 0.63 | 2/5 | N | dip|loso |
| `Guard|Soph_Early|Rotation` | PTS_per36 | Stationary | 0.000 | 1.00 | 5/5 | N | dip |
| `Guard|Soph_Early|Rotation` | REB_per36 | Stationary | 0.000 | 1.00 | 5/5 | N | dip |
| `Guard|Soph_Early|Starter` | AST_per36 | Edge | 0.000 | 0.17 | 2/5 | N | dip|perm|loso |
| `Guard|Soph_Early|Starter` | BLK_per36 | Stationary | 0.000 | 0.53 | 3/5 | N | dip|perm |
| `Guard|Soph_Early|Starter` | PTS_per36 | Stationary | 0.000 | 1.00 | 5/5 | N | dip |
| `Guard|Soph_Early|Starter` | REB_per36 | Stationary | 0.000 | 0.98 | 3/5 | N | dip |
