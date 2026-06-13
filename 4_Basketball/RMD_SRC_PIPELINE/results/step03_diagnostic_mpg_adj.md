# Step 3 — response validation (arm = mpg_adj)

Locked v1.0 SHA: `db0ed9a899c28691183cd5b640f460c10f3c2a75`
(v1.1 amendment not in scope)

## Headline
- Cells classified at Step 2: **100**
- Cells passing all 3 Step-3 checks: **0**  (0.0%)
- Pass by individual check (cells passing this check):
  - Hartigan dip  (p ≥ 0.05): 0/100
  - Permutation   (modal ≥ 60%): 20/100
  - LOSO 5-fold   (≥ 3 match orig): 77/100

## Pass rate by original Step-2 regime
| regime | n | clean | % clean |
|---|---|---|---|
| Concentrating | 1 | 0 | 0.0% |
| Contracting | 10 | 0 | 0.0% |
| Diffusing | 16 | 0 | 0.0% |
| Drifting | 1 | 0 | 0.0% |
| Edge | 42 | 0 | 0.0% |
| Stationary | 30 | 0 | 0.0% |

## F2 preview (Stationary auto-clean + non-Stationary passing Step 3, excluding Edge)
| observable | n_cells | n_Stationary | n_Edge | n_nonStat_clean | terminates_cleanly (pre-Step-4) | % of (n - Edge) |
|---|---|---|---|---|---|---|
| AST_per36 | 25 | 8 | 7 | 0 | 8 | 44.4% |
| BLK_per36 | 25 | 4 | 11 | 0 | 4 | 28.6% |
| PTS_per36 | 25 | 9 | 15 | 0 | 9 | 90.0% |
| REB_per36 | 25 | 9 | 9 | 0 | 9 | 56.2% |

## Non-Stationary cells passing Step 3 (load-bearing for Step 4 4a/4b)

*(none)*

## Full per-cell ledger
| cell_id | observable | regime | dip | perm | loso | clean | failed |
|---|---|---|---|---|---|---|---|
| `Center|Mid|Bench` | AST_per36 | Edge | 0.000 | 0.40 | 2/5 | N | dip|perm|loso |
| `Center|Mid|Bench` | BLK_per36 | Edge | 0.000 | 0.27 | 3/5 | N | dip|perm |
| `Center|Mid|Bench` | PTS_per36 | Edge | 0.000 | 0.48 | 3/5 | N | dip|perm |
| `Center|Mid|Bench` | REB_per36 | Diffusing | 0.000 | 0.11 | 5/5 | N | dip|perm |
| `Center|Mid|Rotation` | AST_per36 | Diffusing | 0.000 | 0.21 | 4/5 | N | dip|perm |
| `Center|Mid|Rotation` | BLK_per36 | Contracting | 0.000 | 0.20 | 5/5 | N | dip|perm |
| `Center|Mid|Rotation` | PTS_per36 | Stationary | 0.000 | 0.52 | 4/5 | N | dip|perm |
| `Center|Mid|Rotation` | REB_per36 | Stationary | 0.000 | 0.62 | 3/5 | N | dip |
| `Center|Mid|Starter` | AST_per36 | Diffusing | 0.000 | 0.23 | 5/5 | N | dip|perm |
| `Center|Mid|Starter` | BLK_per36 | Contracting | 0.000 | 0.14 | 5/5 | N | dip|perm |
| `Center|Mid|Starter` | PTS_per36 | Edge | 0.047 | 0.35 | 4/5 | N | dip|perm |
| `Center|Mid|Starter` | REB_per36 | Contracting | 0.000 | 0.12 | 5/5 | N | dip|perm |
| `Center|Rookie|Bench` | AST_per36 | Diffusing | 0.000 | 0.29 | 5/5 | N | dip|perm |
| `Center|Rookie|Bench` | BLK_per36 | Edge | 0.000 | 0.62 | 4/5 | N | dip |
| `Center|Rookie|Bench` | PTS_per36 | Edge | 0.000 | 0.55 | 4/5 | N | dip|perm |
| `Center|Rookie|Bench` | REB_per36 | Stationary | 0.000 | 0.20 | 1/5 | N | dip|perm|loso |
| `Center|Rookie|Rotation` | AST_per36 | Diffusing | 0.000 | 0.23 | 5/5 | N | dip|perm |
| `Center|Rookie|Rotation` | BLK_per36 | Diffusing | 0.000 | 0.35 | 4/5 | N | dip|perm |
| `Center|Rookie|Rotation` | PTS_per36 | Stationary | 0.001 | 0.27 | 2/5 | N | dip|perm|loso |
| `Center|Rookie|Rotation` | REB_per36 | Diffusing | 0.000 | 0.12 | 3/5 | N | dip|perm |
| `Center|Soph_Early|Bench` | AST_per36 | Stationary | 0.000 | 0.17 | 3/5 | N | dip|perm |
| `Center|Soph_Early|Bench` | BLK_per36 | Edge | 0.000 | 0.58 | 4/5 | N | dip|perm |
| `Center|Soph_Early|Bench` | PTS_per36 | Stationary | 0.000 | 0.15 | 3/5 | N | dip|perm |
| `Center|Soph_Early|Bench` | REB_per36 | Edge | 0.000 | 0.52 | 2/5 | N | dip|perm|loso |
| `Center|Soph_Early|Rotation` | AST_per36 | Contracting | 0.000 | 0.30 | 5/5 | N | dip|perm |
| `Center|Soph_Early|Rotation` | BLK_per36 | Stationary | 0.000 | 0.77 | 4/5 | N | dip |
| `Center|Soph_Early|Rotation` | PTS_per36 | Edge | 0.000 | 0.22 | 5/5 | N | dip|perm |
| `Center|Soph_Early|Rotation` | REB_per36 | Stationary | 0.000 | 1.00 | 2/5 | N | dip|loso |
| `Forward|Deep_vet|Rotation` | AST_per36 | Edge | 0.000 | 0.62 | 4/5 | N | dip |
| `Forward|Deep_vet|Rotation` | BLK_per36 | Drifting | 0.000 | 0.15 | 2/5 | N | dip|perm|loso |
| `Forward|Deep_vet|Rotation` | PTS_per36 | Diffusing | 0.000 | 0.03 | 1/5 | N | dip|perm|loso |
| `Forward|Deep_vet|Rotation` | REB_per36 | Contracting | 0.000 | 0.15 | 3/5 | N | dip|perm |
| `Forward|Mid|Bench` | AST_per36 | Diffusing | 0.000 | 0.38 | 5/5 | N | dip|perm |
| `Forward|Mid|Bench` | BLK_per36 | Stationary | 0.000 | 0.05 | 2/5 | N | dip|perm|loso |
| `Forward|Mid|Bench` | PTS_per36 | Edge | 0.000 | 0.60 | 3/5 | N | dip |
| `Forward|Mid|Bench` | REB_per36 | Edge | 0.000 | 0.50 | 4/5 | N | dip|perm |
| `Forward|Mid|Rotation` | AST_per36 | Diffusing | 0.000 | 0.33 | 5/5 | N | dip|perm |
| `Forward|Mid|Rotation` | BLK_per36 | Edge | 0.000 | 0.23 | 2/5 | N | dip|perm|loso |
| `Forward|Mid|Rotation` | PTS_per36 | Stationary | 0.000 | 0.77 | 4/5 | N | dip |
| `Forward|Mid|Rotation` | REB_per36 | Contracting | 0.000 | 0.17 | 3/5 | N | dip|perm |
| `Forward|Mid|Starter` | AST_per36 | Contracting | 0.000 | 0.28 | 5/5 | N | dip|perm |
| `Forward|Mid|Starter` | BLK_per36 | Edge | 0.000 | 0.20 | 4/5 | N | dip|perm |
| `Forward|Mid|Starter` | PTS_per36 | Stationary | 0.003 | 1.00 | 5/5 | N | dip |
| `Forward|Mid|Starter` | REB_per36 | Edge | 0.000 | 0.23 | 4/5 | N | dip|perm |
| `Forward|Rookie|Bench` | AST_per36 | Stationary | 0.000 | 0.45 | 1/5 | N | dip|perm|loso |
| `Forward|Rookie|Bench` | BLK_per36 | Edge | 0.000 | 0.43 | 4/5 | N | dip|perm |
| `Forward|Rookie|Bench` | PTS_per36 | Edge | 0.000 | 0.53 | 3/5 | N | dip|perm |
| `Forward|Rookie|Bench` | REB_per36 | Edge | 0.000 | 0.60 | 5/5 | N | dip |
| `Forward|Rookie|Rotation` | AST_per36 | Diffusing | 0.000 | 0.17 | 4/5 | N | dip|perm |
| `Forward|Rookie|Rotation` | BLK_per36 | Stationary | 0.000 | 0.33 | 2/5 | N | dip|perm|loso |
| `Forward|Rookie|Rotation` | PTS_per36 | Edge | 0.000 | 0.42 | 1/5 | N | dip|perm|loso |
| `Forward|Rookie|Rotation` | REB_per36 | Edge | 0.000 | 0.33 | 2/5 | N | dip|perm|loso |
| `Forward|Soph_Early|Bench` | AST_per36 | Edge | 0.000 | 0.32 | 1/5 | N | dip|perm|loso |
| `Forward|Soph_Early|Bench` | BLK_per36 | Diffusing | 0.000 | 0.24 | 4/5 | N | dip|perm |
| `Forward|Soph_Early|Bench` | PTS_per36 | Stationary | 0.000 | 0.72 | 3/5 | N | dip |
| `Forward|Soph_Early|Bench` | REB_per36 | Stationary | 0.000 | 0.52 | 3/5 | N | dip|perm |
| `Forward|Soph_Early|Rotation` | AST_per36 | Stationary | 0.000 | 0.75 | 4/5 | N | dip |
| `Forward|Soph_Early|Rotation` | BLK_per36 | Contracting | 0.000 | 0.19 | 5/5 | N | dip|perm |
| `Forward|Soph_Early|Rotation` | PTS_per36 | Edge | 0.000 | 0.32 | 5/5 | N | dip|perm |
| `Forward|Soph_Early|Rotation` | REB_per36 | Contracting | 0.000 | 0.33 | 4/5 | N | dip|perm |
| `Forward|Soph_Early|Starter` | AST_per36 | Stationary | 0.000 | 0.30 | 3/5 | N | dip|perm |
| `Forward|Soph_Early|Starter` | BLK_per36 | Stationary | 0.000 | 0.33 | 4/5 | N | dip|perm |
| `Forward|Soph_Early|Starter` | PTS_per36 | Stationary | 0.000 | 1.00 | 5/5 | N | dip |
| `Forward|Soph_Early|Starter` | REB_per36 | Stationary | 0.000 | 0.60 | 3/5 | N | dip |
| `Guard|Deep_vet|Rotation` | AST_per36 | Stationary | 0.000 | 0.52 | 2/5 | N | dip|perm|loso |
| `Guard|Deep_vet|Rotation` | BLK_per36 | Concentrating | 0.000 | 0.03 | 2/5 | N | dip|perm|loso |
| `Guard|Deep_vet|Rotation` | PTS_per36 | Stationary | 0.000 | 0.43 | 2/5 | N | dip|perm|loso |
| `Guard|Deep_vet|Rotation` | REB_per36 | Stationary | 0.000 | 0.90 | 3/5 | N | dip |
| `Guard|Mid|Bench` | AST_per36 | Edge | 0.000 | 0.32 | 2/5 | N | dip|perm|loso |
| `Guard|Mid|Bench` | BLK_per36 | Diffusing | 0.001 | 0.33 | 4/5 | N | dip|perm |
| `Guard|Mid|Bench` | PTS_per36 | Edge | 0.000 | 0.45 | 4/5 | N | dip|perm |
| `Guard|Mid|Bench` | REB_per36 | Edge | 0.000 | 0.42 | 5/5 | N | dip|perm |
| `Guard|Mid|Rotation` | AST_per36 | Diffusing | 0.000 | 0.15 | 5/5 | N | dip|perm |
| `Guard|Mid|Rotation` | BLK_per36 | Edge | 0.000 | 0.33 | 3/5 | N | dip|perm |
| `Guard|Mid|Rotation` | PTS_per36 | Stationary | 0.000 | 0.63 | 4/5 | N | dip |
| `Guard|Mid|Rotation` | REB_per36 | Edge | 0.000 | 0.18 | 4/5 | N | dip|perm |
| `Guard|Mid|Starter` | AST_per36 | Stationary | 0.000 | 0.42 | 3/5 | N | dip|perm |
| `Guard|Mid|Starter` | BLK_per36 | Edge | 0.000 | 0.13 | 1/5 | N | dip|perm|loso |
| `Guard|Mid|Starter` | PTS_per36 | Edge | 0.000 | 0.38 | 4/5 | N | dip|perm |
| `Guard|Mid|Starter` | REB_per36 | Contracting | 0.000 | 0.13 | 5/5 | N | dip|perm |
| `Guard|Rookie|Bench` | AST_per36 | Stationary | 0.000 | 0.32 | 4/5 | N | dip|perm |
| `Guard|Rookie|Bench` | BLK_per36 | Diffusing | 0.000 | 0.24 | 3/5 | N | dip|perm |
| `Guard|Rookie|Bench` | PTS_per36 | Edge | 0.000 | 0.52 | 5/5 | N | dip|perm |
| `Guard|Rookie|Bench` | REB_per36 | Edge | 0.000 | 0.52 | 4/5 | N | dip|perm |
| `Guard|Rookie|Rotation` | AST_per36 | Stationary | 0.000 | 0.47 | 3/5 | N | dip|perm |
| `Guard|Rookie|Rotation` | BLK_per36 | Diffusing | 0.000 | 0.17 | 4/5 | N | dip|perm |
| `Guard|Rookie|Rotation` | PTS_per36 | Edge | 0.000 | 0.80 | 3/5 | N | dip |
| `Guard|Rookie|Rotation` | REB_per36 | Stationary | 0.000 | 0.98 | 5/5 | N | dip |
| `Guard|Soph_Early|Bench` | AST_per36 | Edge | 0.000 | 0.60 | 3/5 | N | dip |
| `Guard|Soph_Early|Bench` | BLK_per36 | Edge | 0.000 | 0.42 | 2/5 | N | dip|perm|loso |
| `Guard|Soph_Early|Bench` | PTS_per36 | Edge | 0.000 | 0.58 | 4/5 | N | dip|perm |
| `Guard|Soph_Early|Bench` | REB_per36 | Edge | 0.000 | 0.40 | 3/5 | N | dip|perm |
| `Guard|Soph_Early|Rotation` | AST_per36 | Edge | 0.000 | 0.25 | 2/5 | N | dip|perm|loso |
| `Guard|Soph_Early|Rotation` | BLK_per36 | Edge | 0.000 | 0.53 | 3/5 | N | dip|perm |
| `Guard|Soph_Early|Rotation` | PTS_per36 | Edge | 0.000 | 0.03 | 2/5 | N | dip|perm|loso |
| `Guard|Soph_Early|Rotation` | REB_per36 | Stationary | 0.000 | 0.65 | 4/5 | N | dip |
| `Guard|Soph_Early|Starter` | AST_per36 | Edge | 0.000 | 0.25 | 3/5 | N | dip|perm |
| `Guard|Soph_Early|Starter` | BLK_per36 | Edge | 0.000 | 0.32 | 2/5 | N | dip|perm|loso |
| `Guard|Soph_Early|Starter` | PTS_per36 | Edge | 0.000 | 0.17 | 4/5 | N | dip|perm |
| `Guard|Soph_Early|Starter` | REB_per36 | Stationary | 0.000 | 1.00 | 4/5 | N | dip |
