# Step 3 — response validation (arm = usg)

Locked v1.0 SHA: `db0ed9a899c28691183cd5b640f460c10f3c2a75`
(v1.1 amendment not in scope)

## Headline
- Cells classified at Step 2: **76**
- Cells passing all 3 Step-3 checks: **0**  (0.0%)
- Pass by individual check (cells passing this check):
  - Hartigan dip  (p ≥ 0.05): 0/76
  - Permutation   (modal ≥ 60%): 20/76
  - LOSO 5-fold   (≥ 3 match orig): 66/76

## Pass rate by original Step-2 regime
| regime | n | clean | % clean |
|---|---|---|---|
| Concentrating | 2 | 0 | 0.0% |
| Contracting | 6 | 0 | 0.0% |
| Diffusing | 12 | 0 | 0.0% |
| Drifting | 1 | 0 | 0.0% |
| Edge | 23 | 0 | 0.0% |
| Stationary | 32 | 0 | 0.0% |

## F2 preview (Stationary auto-clean + non-Stationary passing Step 3, excluding Edge)
| observable | n_cells | n_Stationary | n_Edge | n_nonStat_clean | terminates_cleanly (pre-Step-4) | % of (n - Edge) |
|---|---|---|---|---|---|---|
| AST_per36 | 19 | 6 | 7 | 0 | 6 | 50.0% |
| BLK_per36 | 19 | 6 | 4 | 0 | 6 | 40.0% |
| PTS_per36 | 19 | 10 | 6 | 0 | 10 | 76.9% |
| REB_per36 | 19 | 10 | 6 | 0 | 10 | 76.9% |

## Non-Stationary cells passing Step 3 (load-bearing for Step 4 4a/4b)

*(none)*

## Full per-cell ledger
| cell_id | observable | regime | dip | perm | loso | clean | failed |
|---|---|---|---|---|---|---|---|
| `Center|Mid|Mid_usage` | AST_per36 | Diffusing | 0.000 | 0.28 | 5/5 | N | dip|perm |
| `Center|Mid|Mid_usage` | BLK_per36 | Contracting | 0.000 | 0.12 | 4/5 | N | dip|perm |
| `Center|Mid|Mid_usage` | PTS_per36 | Edge | 0.000 | 0.35 | 4/5 | N | dip|perm |
| `Center|Mid|Mid_usage` | REB_per36 | Stationary | 0.000 | 0.90 | 5/5 | N | dip |
| `Center|Rookie|Mid_usage` | AST_per36 | Edge | 0.000 | 0.50 | 2/5 | N | dip|perm|loso |
| `Center|Rookie|Mid_usage` | BLK_per36 | Stationary | 0.000 | 0.20 | 3/5 | N | dip|perm |
| `Center|Rookie|Mid_usage` | PTS_per36 | Edge | 0.000 | 0.50 | 1/5 | N | dip|perm|loso |
| `Center|Rookie|Mid_usage` | REB_per36 | Stationary | 0.000 | 0.13 | 4/5 | N | dip|perm |
| `Center|Soph_Early|Mid_usage` | AST_per36 | Contracting | 0.000 | 0.26 | 5/5 | N | dip|perm |
| `Center|Soph_Early|Mid_usage` | BLK_per36 | Edge | 0.000 | 0.70 | 4/5 | N | dip |
| `Center|Soph_Early|Mid_usage` | PTS_per36 | Edge | 0.000 | 0.40 | 4/5 | N | dip|perm |
| `Center|Soph_Early|Mid_usage` | REB_per36 | Edge | 0.000 | 0.53 | 3/5 | N | dip|perm |
| `Forward|Deep_vet|Mid_usage` | AST_per36 | Edge | 0.000 | 0.62 | 4/5 | N | dip |
| `Forward|Deep_vet|Mid_usage` | BLK_per36 | Drifting | 0.000 | 0.16 | 3/5 | N | dip|perm |
| `Forward|Deep_vet|Mid_usage` | PTS_per36 | Diffusing | 0.000 | 0.03 | 3/5 | N | dip|perm |
| `Forward|Deep_vet|Mid_usage` | REB_per36 | Edge | 0.000 | 0.58 | 4/5 | N | dip|perm |
| `Forward|Mid|Low_usage` | AST_per36 | Diffusing | 0.000 | 0.28 | 5/5 | N | dip|perm |
| `Forward|Mid|Low_usage` | BLK_per36 | Stationary | 0.000 | 0.13 | 2/5 | N | dip|perm|loso |
| `Forward|Mid|Low_usage` | PTS_per36 | Stationary | 0.000 | 0.57 | 3/5 | N | dip|perm |
| `Forward|Mid|Low_usage` | REB_per36 | Stationary | 0.000 | 0.45 | 3/5 | N | dip|perm |
| `Forward|Mid|Mid_usage` | AST_per36 | Stationary | 0.000 | 0.60 | 3/5 | N | dip |
| `Forward|Mid|Mid_usage` | BLK_per36 | Stationary | 0.000 | 0.30 | 2/5 | N | dip|perm|loso |
| `Forward|Mid|Mid_usage` | PTS_per36 | Stationary | 0.000 | 0.73 | 4/5 | N | dip |
| `Forward|Mid|Mid_usage` | REB_per36 | Stationary | 0.000 | 0.93 | 4/5 | N | dip |
| `Forward|Rookie|Low_usage` | AST_per36 | Diffusing | 0.000 | 0.26 | 4/5 | N | dip|perm |
| `Forward|Rookie|Low_usage` | BLK_per36 | Contracting | 0.000 | 0.30 | 3/5 | N | dip|perm |
| `Forward|Rookie|Low_usage` | PTS_per36 | Edge | 0.000 | 0.57 | 3/5 | N | dip|perm |
| `Forward|Rookie|Low_usage` | REB_per36 | Edge | 0.000 | 0.38 | 3/5 | N | dip|perm |
| `Forward|Rookie|Mid_usage` | AST_per36 | Stationary | 0.000 | 0.28 | 3/5 | N | dip|perm |
| `Forward|Rookie|Mid_usage` | BLK_per36 | Diffusing | 0.000 | 0.22 | 5/5 | N | dip|perm |
| `Forward|Rookie|Mid_usage` | PTS_per36 | Edge | 0.000 | 0.58 | 1/5 | N | dip|perm|loso |
| `Forward|Rookie|Mid_usage` | REB_per36 | Edge | 0.000 | 0.57 | 5/5 | N | dip|perm |
| `Forward|Soph_Early|Low_usage` | AST_per36 | Stationary | 0.000 | 0.48 | 4/5 | N | dip|perm |
| `Forward|Soph_Early|Low_usage` | BLK_per36 | Diffusing | 0.000 | 0.21 | 5/5 | N | dip|perm |
| `Forward|Soph_Early|Low_usage` | PTS_per36 | Stationary | 0.000 | 0.73 | 4/5 | N | dip |
| `Forward|Soph_Early|Low_usage` | REB_per36 | Stationary | 0.000 | 0.78 | 5/5 | N | dip |
| `Forward|Soph_Early|Mid_usage` | AST_per36 | Stationary | 0.000 | 0.38 | 1/5 | N | dip|perm|loso |
| `Forward|Soph_Early|Mid_usage` | BLK_per36 | Edge | 0.000 | 0.33 | 4/5 | N | dip|perm |
| `Forward|Soph_Early|Mid_usage` | PTS_per36 | Stationary | 0.000 | 1.00 | 5/5 | N | dip |
| `Forward|Soph_Early|Mid_usage` | REB_per36 | Edge | 0.000 | 0.30 | 5/5 | N | dip|perm |
| `Guard|Deep_vet|Mid_usage` | AST_per36 | Stationary | 0.000 | 0.50 | 3/5 | N | dip|perm |
| `Guard|Deep_vet|Mid_usage` | BLK_per36 | Concentrating | 0.000 | 0.06 | 3/5 | N | dip|perm |
| `Guard|Deep_vet|Mid_usage` | PTS_per36 | Stationary | 0.000 | 0.38 | 3/5 | N | dip|perm |
| `Guard|Deep_vet|Mid_usage` | REB_per36 | Stationary | 0.000 | 0.83 | 4/5 | N | dip |
| `Guard|Mid|High_usage` | AST_per36 | Edge | 0.000 | 0.63 | 2/5 | N | dip|loso |
| `Guard|Mid|High_usage` | BLK_per36 | Stationary | 0.000 | 0.37 | 2/5 | N | dip|perm|loso |
| `Guard|Mid|High_usage` | PTS_per36 | Stationary | 0.000 | 0.73 | 3/5 | N | dip |
| `Guard|Mid|High_usage` | REB_per36 | Contracting | 0.000 | 0.19 | 3/5 | N | dip|perm |
| `Guard|Mid|Low_usage` | AST_per36 | Diffusing | 0.000 | 0.08 | 5/5 | N | dip|perm |
| `Guard|Mid|Low_usage` | BLK_per36 | Stationary | 0.000 | 0.15 | 3/5 | N | dip|perm |
| `Guard|Mid|Low_usage` | PTS_per36 | Contracting | 0.000 | 0.10 | 3/5 | N | dip|perm |
| `Guard|Mid|Low_usage` | REB_per36 | Diffusing | 0.000 | 0.17 | 5/5 | N | dip|perm |
| `Guard|Mid|Mid_usage` | AST_per36 | Edge | 0.000 | 0.37 | 4/5 | N | dip|perm |
| `Guard|Mid|Mid_usage` | BLK_per36 | Diffusing | 0.000 | 0.32 | 4/5 | N | dip|perm |
| `Guard|Mid|Mid_usage` | PTS_per36 | Stationary | 0.000 | 1.00 | 4/5 | N | dip |
| `Guard|Mid|Mid_usage` | REB_per36 | Stationary | 0.000 | 1.00 | 5/5 | N | dip |
| `Guard|Rookie|Low_usage` | AST_per36 | Diffusing | 0.000 | 0.23 | 5/5 | N | dip|perm |
| `Guard|Rookie|Low_usage` | BLK_per36 | Edge | 0.000 | 0.32 | 3/5 | N | dip|perm |
| `Guard|Rookie|Low_usage` | PTS_per36 | Stationary | 0.000 | 0.58 | 4/5 | N | dip|perm |
| `Guard|Rookie|Low_usage` | REB_per36 | Stationary | 0.000 | 0.30 | 3/5 | N | dip|perm |
| `Guard|Rookie|Mid_usage` | AST_per36 | Stationary | 0.000 | 0.80 | 4/5 | N | dip |
| `Guard|Rookie|Mid_usage` | BLK_per36 | Diffusing | 0.000 | 0.31 | 5/5 | N | dip|perm |
| `Guard|Rookie|Mid_usage` | PTS_per36 | Edge | 0.000 | 0.73 | 5/5 | N | dip |
| `Guard|Rookie|Mid_usage` | REB_per36 | Edge | 0.000 | 0.32 | 2/5 | N | dip|perm|loso |
| `Guard|Soph_Early|High_usage` | AST_per36 | Edge | 0.000 | 0.43 | 5/5 | N | dip|perm |
| `Guard|Soph_Early|High_usage` | BLK_per36 | Edge | 0.000 | 0.17 | 3/5 | N | dip|perm |
| `Guard|Soph_Early|High_usage` | PTS_per36 | Stationary | 0.000 | 1.00 | 4/5 | N | dip |
| `Guard|Soph_Early|High_usage` | REB_per36 | Stationary | 0.000 | 0.75 | 4/5 | N | dip |
| `Guard|Soph_Early|Low_usage` | AST_per36 | Edge | 0.000 | 0.57 | 2/5 | N | dip|perm|loso |
| `Guard|Soph_Early|Low_usage` | BLK_per36 | Diffusing | 0.000 | 0.28 | 4/5 | N | dip|perm |
| `Guard|Soph_Early|Low_usage` | PTS_per36 | Concentrating | 0.000 | 0.02 | 4/5 | N | dip|perm |
| `Guard|Soph_Early|Low_usage` | REB_per36 | Contracting | 0.000 | 0.22 | 3/5 | N | dip|perm |
| `Guard|Soph_Early|Mid_usage` | AST_per36 | Edge | 0.000 | 0.35 | 4/5 | N | dip|perm |
| `Guard|Soph_Early|Mid_usage` | BLK_per36 | Stationary | 0.000 | 0.53 | 4/5 | N | dip|perm |
| `Guard|Soph_Early|Mid_usage` | PTS_per36 | Stationary | 0.000 | 0.73 | 4/5 | N | dip |
| `Guard|Soph_Early|Mid_usage` | REB_per36 | Stationary | 0.000 | 0.63 | 3/5 | N | dip |
