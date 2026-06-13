# Step 3 — response validation (arm = usg_adj)

Locked v1.0 SHA: `db0ed9a899c28691183cd5b640f460c10f3c2a75`
(v1.1 amendment not in scope)

## Headline
- Cells classified at Step 2: **84**
- Cells passing all 3 Step-3 checks: **0**  (0.0%)
- Pass by individual check (cells passing this check):
  - Hartigan dip  (p ≥ 0.05): 0/84
  - Permutation   (modal ≥ 60%): 27/84
  - LOSO 5-fold   (≥ 3 match orig): 72/84

## Pass rate by original Step-2 regime
| regime | n | clean | % clean |
|---|---|---|---|
| Concentrating | 2 | 0 | 0.0% |
| Contracting | 10 | 0 | 0.0% |
| Diffusing | 13 | 0 | 0.0% |
| Drifting | 1 | 0 | 0.0% |
| Edge | 25 | 0 | 0.0% |
| Stationary | 33 | 0 | 0.0% |

## F2 preview (Stationary auto-clean + non-Stationary passing Step 3, excluding Edge)
| observable | n_cells | n_Stationary | n_Edge | n_nonStat_clean | terminates_cleanly (pre-Step-4) | % of (n - Edge) |
|---|---|---|---|---|---|---|
| AST_per36 | 21 | 8 | 4 | 0 | 8 | 47.1% |
| BLK_per36 | 21 | 4 | 8 | 0 | 4 | 30.8% |
| PTS_per36 | 21 | 11 | 6 | 0 | 11 | 73.3% |
| REB_per36 | 21 | 10 | 7 | 0 | 10 | 71.4% |

## Non-Stationary cells passing Step 3 (load-bearing for Step 4 4a/4b)

*(none)*

## Full per-cell ledger
| cell_id | observable | regime | dip | perm | loso | clean | failed |
|---|---|---|---|---|---|---|---|
| `Center|Mid|Low_usage` | AST_per36 | Diffusing | 0.000 | 0.24 | 4/5 | N | dip|perm |
| `Center|Mid|Low_usage` | BLK_per36 | Contracting | 0.000 | 0.23 | 4/5 | N | dip|perm |
| `Center|Mid|Low_usage` | PTS_per36 | Stationary | 0.000 | 0.58 | 3/5 | N | dip|perm |
| `Center|Mid|Low_usage` | REB_per36 | Edge | 0.000 | 0.62 | 4/5 | N | dip |
| `Center|Mid|Mid_usage` | AST_per36 | Diffusing | 0.000 | 0.27 | 5/5 | N | dip|perm |
| `Center|Mid|Mid_usage` | BLK_per36 | Contracting | 0.000 | 0.09 | 4/5 | N | dip|perm |
| `Center|Mid|Mid_usage` | PTS_per36 | Edge | 0.000 | 0.45 | 4/5 | N | dip|perm |
| `Center|Mid|Mid_usage` | REB_per36 | Stationary | 0.000 | 0.72 | 3/5 | N | dip |
| `Center|Rookie|Low_usage` | AST_per36 | Diffusing | 0.000 | 0.37 | 4/5 | N | dip|perm |
| `Center|Rookie|Low_usage` | BLK_per36 | Stationary | 0.000 | 0.28 | 3/5 | N | dip|perm |
| `Center|Rookie|Low_usage` | PTS_per36 | Contracting | 0.000 | 0.15 | 4/5 | N | dip|perm |
| `Center|Rookie|Low_usage` | REB_per36 | Stationary | 0.000 | 0.33 | 1/5 | N | dip|perm|loso |
| `Center|Rookie|Mid_usage` | AST_per36 | Diffusing | 0.000 | 0.18 | 4/5 | N | dip|perm |
| `Center|Rookie|Mid_usage` | BLK_per36 | Edge | 0.000 | 0.85 | 5/5 | N | dip |
| `Center|Rookie|Mid_usage` | PTS_per36 | Edge | 0.000 | 0.45 | 5/5 | N | dip|perm |
| `Center|Rookie|Mid_usage` | REB_per36 | Edge | 0.000 | 0.55 | 4/5 | N | dip|perm |
| `Center|Soph_Early|Low_usage` | AST_per36 | Edge | 0.000 | 0.60 | 3/5 | N | dip |
| `Center|Soph_Early|Low_usage` | BLK_per36 | Edge | 0.000 | 0.40 | 5/5 | N | dip|perm |
| `Center|Soph_Early|Low_usage` | PTS_per36 | Stationary | 0.000 | 0.50 | 3/5 | N | dip|perm |
| `Center|Soph_Early|Low_usage` | REB_per36 | Stationary | 0.000 | 0.77 | 4/5 | N | dip |
| `Center|Soph_Early|Mid_usage` | AST_per36 | Contracting | 0.000 | 0.33 | 5/5 | N | dip|perm |
| `Center|Soph_Early|Mid_usage` | BLK_per36 | Stationary | 0.000 | 0.67 | 4/5 | N | dip |
| `Center|Soph_Early|Mid_usage` | PTS_per36 | Stationary | 0.000 | 0.68 | 3/5 | N | dip |
| `Center|Soph_Early|Mid_usage` | REB_per36 | Edge | 0.000 | 0.70 | 5/5 | N | dip |
| `Forward|Deep_vet|Mid_usage` | AST_per36 | Edge | 0.000 | 0.62 | 4/5 | N | dip |
| `Forward|Deep_vet|Mid_usage` | BLK_per36 | Drifting | 0.000 | 0.15 | 2/5 | N | dip|perm|loso |
| `Forward|Deep_vet|Mid_usage` | PTS_per36 | Diffusing | 0.000 | 0.03 | 1/5 | N | dip|perm|loso |
| `Forward|Deep_vet|Mid_usage` | REB_per36 | Contracting | 0.000 | 0.15 | 3/5 | N | dip|perm |
| `Forward|Mid|Low_usage` | AST_per36 | Diffusing | 0.000 | 0.21 | 5/5 | N | dip|perm |
| `Forward|Mid|Low_usage` | BLK_per36 | Edge | 0.000 | 0.62 | 4/5 | N | dip |
| `Forward|Mid|Low_usage` | PTS_per36 | Edge | 0.000 | 0.43 | 3/5 | N | dip|perm |
| `Forward|Mid|Low_usage` | REB_per36 | Edge | 0.000 | 0.40 | 3/5 | N | dip|perm |
| `Forward|Mid|Mid_usage` | AST_per36 | Stationary | 0.000 | 0.62 | 4/5 | N | dip |
| `Forward|Mid|Mid_usage` | BLK_per36 | Stationary | 0.000 | 0.25 | 1/5 | N | dip|perm|loso |
| `Forward|Mid|Mid_usage` | PTS_per36 | Stationary | 0.000 | 0.80 | 4/5 | N | dip |
| `Forward|Mid|Mid_usage` | REB_per36 | Edge | 0.000 | 0.27 | 4/5 | N | dip|perm |
| `Forward|Rookie|Low_usage` | AST_per36 | Stationary | 0.000 | 0.45 | 3/5 | N | dip|perm |
| `Forward|Rookie|Low_usage` | BLK_per36 | Contracting | 0.000 | 0.33 | 4/5 | N | dip|perm |
| `Forward|Rookie|Low_usage` | PTS_per36 | Stationary | 0.000 | 0.35 | 4/5 | N | dip|perm |
| `Forward|Rookie|Low_usage` | REB_per36 | Stationary | 0.000 | 0.63 | 4/5 | N | dip |
| `Forward|Rookie|Mid_usage` | AST_per36 | Diffusing | 0.000 | 0.14 | 4/5 | N | dip|perm |
| `Forward|Rookie|Mid_usage` | BLK_per36 | Diffusing | 0.000 | 0.16 | 5/5 | N | dip|perm |
| `Forward|Rookie|Mid_usage` | PTS_per36 | Edge | 0.000 | 0.35 | 4/5 | N | dip|perm |
| `Forward|Rookie|Mid_usage` | REB_per36 | Edge | 0.000 | 0.47 | 5/5 | N | dip|perm |
| `Forward|Soph_Early|Low_usage` | AST_per36 | Stationary | 0.000 | 0.48 | 2/5 | N | dip|perm|loso |
| `Forward|Soph_Early|Low_usage` | BLK_per36 | Diffusing | 0.000 | 0.11 | 3/5 | N | dip|perm |
| `Forward|Soph_Early|Low_usage` | PTS_per36 | Stationary | 0.000 | 0.80 | 3/5 | N | dip |
| `Forward|Soph_Early|Low_usage` | REB_per36 | Contracting | 0.000 | 0.24 | 4/5 | N | dip|perm |
| `Forward|Soph_Early|Mid_usage` | AST_per36 | Stationary | 0.000 | 0.60 | 4/5 | N | dip |
| `Forward|Soph_Early|Mid_usage` | BLK_per36 | Edge | 0.000 | 0.45 | 4/5 | N | dip|perm |
| `Forward|Soph_Early|Mid_usage` | PTS_per36 | Stationary | 0.000 | 0.87 | 4/5 | N | dip |
| `Forward|Soph_Early|Mid_usage` | REB_per36 | Edge | 0.000 | 0.33 | 5/5 | N | dip|perm |
| `Guard|Deep_vet|Mid_usage` | AST_per36 | Stationary | 0.000 | 0.52 | 2/5 | N | dip|perm|loso |
| `Guard|Deep_vet|Mid_usage` | BLK_per36 | Concentrating | 0.000 | 0.03 | 2/5 | N | dip|perm|loso |
| `Guard|Deep_vet|Mid_usage` | PTS_per36 | Stationary | 0.000 | 0.43 | 2/5 | N | dip|perm|loso |
| `Guard|Deep_vet|Mid_usage` | REB_per36 | Stationary | 0.000 | 0.90 | 3/5 | N | dip |
| `Guard|Mid|High_usage` | AST_per36 | Stationary | 0.000 | 0.48 | 3/5 | N | dip|perm |
| `Guard|Mid|High_usage` | BLK_per36 | Edge | 0.000 | 0.43 | 2/5 | N | dip|perm|loso |
| `Guard|Mid|High_usage` | PTS_per36 | Edge | 0.001 | 0.33 | 3/5 | N | dip|perm |
| `Guard|Mid|High_usage` | REB_per36 | Contracting | 0.000 | 0.29 | 3/5 | N | dip|perm |
| `Guard|Mid|Low_usage` | AST_per36 | Diffusing | 0.000 | 0.07 | 5/5 | N | dip|perm |
| `Guard|Mid|Low_usage` | BLK_per36 | Edge | 0.000 | 0.42 | 2/5 | N | dip|perm|loso |
| `Guard|Mid|Low_usage` | PTS_per36 | Contracting | 0.000 | 0.12 | 2/5 | N | dip|perm|loso |
| `Guard|Mid|Low_usage` | REB_per36 | Stationary | 0.000 | 0.60 | 4/5 | N | dip |
| `Guard|Mid|Mid_usage` | AST_per36 | Edge | 0.000 | 0.50 | 4/5 | N | dip|perm |
| `Guard|Mid|Mid_usage` | BLK_per36 | Diffusing | 0.000 | 0.33 | 4/5 | N | dip|perm |
| `Guard|Mid|Mid_usage` | PTS_per36 | Stationary | 0.000 | 1.00 | 4/5 | N | dip |
| `Guard|Mid|Mid_usage` | REB_per36 | Stationary | 0.000 | 1.00 | 5/5 | N | dip |
| `Guard|Rookie|Mid_usage` | AST_per36 | Stationary | 0.000 | 0.65 | 3/5 | N | dip |
| `Guard|Rookie|Mid_usage` | BLK_per36 | Diffusing | 0.000 | 0.21 | 4/5 | N | dip|perm |
| `Guard|Rookie|Mid_usage` | PTS_per36 | Edge | 0.000 | 0.62 | 3/5 | N | dip |
| `Guard|Rookie|Mid_usage` | REB_per36 | Stationary | 0.000 | 0.97 | 3/5 | N | dip |
| `Guard|Soph_Early|High_usage` | AST_per36 | Edge | 0.000 | 0.40 | 5/5 | N | dip|perm |
| `Guard|Soph_Early|High_usage` | BLK_per36 | Edge | 0.000 | 0.13 | 3/5 | N | dip|perm |
| `Guard|Soph_Early|High_usage` | PTS_per36 | Stationary | 0.000 | 1.00 | 4/5 | N | dip |
| `Guard|Soph_Early|High_usage` | REB_per36 | Stationary | 0.000 | 0.87 | 4/5 | N | dip |
| `Guard|Soph_Early|Low_usage` | AST_per36 | Diffusing | 0.000 | 0.13 | 4/5 | N | dip|perm |
| `Guard|Soph_Early|Low_usage` | BLK_per36 | Edge | 0.000 | 0.25 | 2/5 | N | dip|perm|loso |
| `Guard|Soph_Early|Low_usage` | PTS_per36 | Concentrating | 0.000 | 0.07 | 4/5 | N | dip|perm |
| `Guard|Soph_Early|Low_usage` | REB_per36 | Contracting | 0.000 | 0.24 | 4/5 | N | dip|perm |
| `Guard|Soph_Early|Mid_usage` | AST_per36 | Stationary | 0.000 | 0.48 | 3/5 | N | dip|perm |
| `Guard|Soph_Early|Mid_usage` | BLK_per36 | Stationary | 0.000 | 0.58 | 4/5 | N | dip|perm |
| `Guard|Soph_Early|Mid_usage` | PTS_per36 | Stationary | 0.000 | 0.83 | 3/5 | N | dip |
| `Guard|Soph_Early|Mid_usage` | REB_per36 | Stationary | 0.000 | 0.63 | 3/5 | N | dip |
