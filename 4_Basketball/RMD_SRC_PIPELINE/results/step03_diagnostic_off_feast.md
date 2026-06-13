# Step 3 — response validation (arm = off_feast)

Locked v1.0 SHA: `cd40b46`
(v1.1 amendment not in scope)

## Headline
- Cells classified at Step 2: **60**
- Cells passing all 3 Step-3 checks: **0**  (0.0%)
- Pass by individual check (cells passing this check):
  - Hartigan dip  (p ≥ 0.05): 0/60
  - Permutation   (modal ≥ 60%): 19/60
  - LOSO 5-fold   (≥ 3 match orig): 53/60

## Pass rate by original Step-2 regime
| regime | n | clean | % clean |
|---|---|---|---|
| Concentrating | 1 | 0 | 0.0% |
| Contracting | 8 | 0 | 0.0% |
| Diffusing | 11 | 0 | 0.0% |
| Edge | 14 | 0 | 0.0% |
| Stationary | 26 | 0 | 0.0% |

## F2 preview (Stationary auto-clean + non-Stationary passing Step 3, excluding Edge)
| observable | n_cells | n_Stationary | n_Edge | n_nonStat_clean | terminates_cleanly (pre-Step-4) | % of (n - Edge) |
|---|---|---|---|---|---|---|
| AST_per36 | 15 | 7 | 2 | 0 | 7 | 53.8% |
| BLK_per36 | 15 | 1 | 4 | 0 | 1 | 9.1% |
| PTS_per36 | 15 | 10 | 5 | 0 | 10 | 100.0% |
| REB_per36 | 15 | 8 | 3 | 0 | 8 | 66.7% |

## Non-Stationary cells passing Step 3 (load-bearing for Step 4 4a/4b)

*(none)*

## Full per-cell ledger
| cell_id | observable | regime | dip | perm | loso | clean | failed |
|---|---|---|---|---|---|---|---|
| `Perimeter|Deep_vet|Mid_usage` | AST_per36 | Edge | 0.000 | 0.47 | 5/5 | N | dip|perm |
| `Perimeter|Deep_vet|Mid_usage` | BLK_per36 | Diffusing | 0.000 | 0.15 | 4/5 | N | dip|perm |
| `Perimeter|Deep_vet|Mid_usage` | PTS_per36 | Stationary | 0.000 | 1.00 | 5/5 | N | dip |
| `Perimeter|Deep_vet|Mid_usage` | REB_per36 | Edge | 0.000 | 0.33 | 4/5 | N | dip|perm |
| `Perimeter|Mid|High_usage` | AST_per36 | Stationary | 0.000 | 0.60 | 3/5 | N | dip |
| `Perimeter|Mid|High_usage` | BLK_per36 | Contracting | 0.000 | 0.23 | 3/5 | N | dip|perm |
| `Perimeter|Mid|High_usage` | PTS_per36 | Stationary | 0.000 | 0.77 | 3/5 | N | dip |
| `Perimeter|Mid|High_usage` | REB_per36 | Stationary | 0.000 | 0.70 | 4/5 | N | dip |
| `Perimeter|Mid|Low_usage` | AST_per36 | Diffusing | 0.000 | 0.12 | 3/5 | N | dip|perm |
| `Perimeter|Mid|Low_usage` | BLK_per36 | Edge | 0.000 | 0.58 | 2/5 | N | dip|perm|loso |
| `Perimeter|Mid|Low_usage` | PTS_per36 | Stationary | 0.000 | 0.77 | 5/5 | N | dip |
| `Perimeter|Mid|Low_usage` | REB_per36 | Stationary | 0.000 | 0.45 | 3/5 | N | dip|perm |
| `Perimeter|Mid|Mid_usage` | AST_per36 | Stationary | 0.000 | 0.70 | 2/5 | N | dip|loso |
| `Perimeter|Mid|Mid_usage` | BLK_per36 | Stationary | 0.000 | 0.18 | 2/5 | N | dip|perm|loso |
| `Perimeter|Mid|Mid_usage` | PTS_per36 | Stationary | 0.000 | 1.00 | 5/5 | N | dip |
| `Perimeter|Mid|Mid_usage` | REB_per36 | Stationary | 0.000 | 0.97 | 4/5 | N | dip |
| `Perimeter|Rookie|Low_usage` | AST_per36 | Diffusing | 0.000 | 0.18 | 5/5 | N | dip|perm |
| `Perimeter|Rookie|Low_usage` | BLK_per36 | Edge | 0.000 | 0.35 | 4/5 | N | dip|perm |
| `Perimeter|Rookie|Low_usage` | PTS_per36 | Stationary | 0.000 | 0.52 | 3/5 | N | dip|perm |
| `Perimeter|Rookie|Low_usage` | REB_per36 | Stationary | 0.000 | 0.50 | 2/5 | N | dip|perm|loso |
| `Perimeter|Rookie|Mid_usage` | AST_per36 | Stationary | 0.000 | 0.77 | 4/5 | N | dip |
| `Perimeter|Rookie|Mid_usage` | BLK_per36 | Diffusing | 0.000 | 0.33 | 4/5 | N | dip|perm |
| `Perimeter|Rookie|Mid_usage` | PTS_per36 | Edge | 0.000 | 0.53 | 3/5 | N | dip|perm |
| `Perimeter|Rookie|Mid_usage` | REB_per36 | Edge | 0.000 | 0.40 | 2/5 | N | dip|perm|loso |
| `Perimeter|Soph_Early|High_usage` | AST_per36 | Diffusing | 0.000 | 0.15 | 4/5 | N | dip|perm |
| `Perimeter|Soph_Early|High_usage` | BLK_per36 | Contracting | 0.000 | 0.28 | 3/5 | N | dip|perm |
| `Perimeter|Soph_Early|High_usage` | PTS_per36 | Stationary | 0.000 | 1.00 | 5/5 | N | dip |
| `Perimeter|Soph_Early|High_usage` | REB_per36 | Contracting | 0.000 | 0.21 | 5/5 | N | dip|perm |
| `Perimeter|Soph_Early|Low_usage` | AST_per36 | Stationary | 0.000 | 0.32 | 2/5 | N | dip|perm|loso |
| `Perimeter|Soph_Early|Low_usage` | BLK_per36 | Diffusing | 0.000 | 0.28 | 4/5 | N | dip|perm |
| `Perimeter|Soph_Early|Low_usage` | PTS_per36 | Stationary | 0.000 | 0.45 | 3/5 | N | dip|perm |
| `Perimeter|Soph_Early|Low_usage` | REB_per36 | Contracting | 0.000 | 0.15 | 5/5 | N | dip|perm |
| `Perimeter|Soph_Early|Mid_usage` | AST_per36 | Stationary | 0.000 | 0.97 | 4/5 | N | dip |
| `Perimeter|Soph_Early|Mid_usage` | BLK_per36 | Contracting | 0.000 | 0.14 | 3/5 | N | dip|perm |
| `Perimeter|Soph_Early|Mid_usage` | PTS_per36 | Stationary | 0.000 | 1.00 | 4/5 | N | dip |
| `Perimeter|Soph_Early|Mid_usage` | REB_per36 | Stationary | 0.000 | 0.85 | 3/5 | N | dip |
| `Rim|Mid|Low_usage` | AST_per36 | Diffusing | 0.000 | 0.28 | 5/5 | N | dip|perm |
| `Rim|Mid|Low_usage` | BLK_per36 | Contracting | 0.000 | 0.26 | 5/5 | N | dip|perm |
| `Rim|Mid|Low_usage` | PTS_per36 | Edge | 0.000 | 0.45 | 3/5 | N | dip|perm |
| `Rim|Mid|Low_usage` | REB_per36 | Stationary | 0.000 | 0.67 | 3/5 | N | dip |
| `Rim|Mid|Mid_usage` | AST_per36 | Diffusing | 0.000 | 0.17 | 5/5 | N | dip|perm |
| `Rim|Mid|Mid_usage` | BLK_per36 | Contracting | 0.000 | 0.27 | 5/5 | N | dip|perm |
| `Rim|Mid|Mid_usage` | PTS_per36 | Stationary | 0.000 | 0.73 | 4/5 | N | dip |
| `Rim|Mid|Mid_usage` | REB_per36 | Edge | 0.000 | 0.37 | 4/5 | N | dip|perm |
| `Rim|Rookie|Low_usage` | AST_per36 | Stationary | 0.000 | 0.82 | 5/5 | N | dip |
| `Rim|Rookie|Low_usage` | BLK_per36 | Edge | 0.000 | 0.53 | 3/5 | N | dip|perm |
| `Rim|Rookie|Low_usage` | PTS_per36 | Edge | 0.000 | 0.55 | 3/5 | N | dip|perm |
| `Rim|Rookie|Low_usage` | REB_per36 | Concentrating | 0.000 | 0.03 | 3/5 | N | dip|perm |
| `Rim|Rookie|Mid_usage` | AST_per36 | Edge | 0.000 | 0.68 | 4/5 | N | dip |
| `Rim|Rookie|Mid_usage` | BLK_per36 | Edge | 0.000 | 0.38 | 3/5 | N | dip|perm |
| `Rim|Rookie|Mid_usage` | PTS_per36 | Edge | 0.000 | 0.62 | 4/5 | N | dip |
| `Rim|Rookie|Mid_usage` | REB_per36 | Diffusing | 0.000 | 0.15 | 5/5 | N | dip|perm |
| `Rim|Soph_Early|Low_usage` | AST_per36 | Stationary | 0.000 | 0.28 | 4/5 | N | dip|perm |
| `Rim|Soph_Early|Low_usage` | BLK_per36 | Diffusing | 0.000 | 0.12 | 4/5 | N | dip|perm |
| `Rim|Soph_Early|Low_usage` | PTS_per36 | Stationary | 0.000 | 0.38 | 1/5 | N | dip|perm|loso |
| `Rim|Soph_Early|Low_usage` | REB_per36 | Stationary | 0.000 | 0.65 | 4/5 | N | dip |
| `Rim|Soph_Early|Mid_usage` | AST_per36 | Contracting | 0.000 | 0.25 | 4/5 | N | dip|perm |
| `Rim|Soph_Early|Mid_usage` | BLK_per36 | Diffusing | 0.000 | 0.24 | 3/5 | N | dip|perm |
| `Rim|Soph_Early|Mid_usage` | PTS_per36 | Edge | 0.000 | 0.27 | 4/5 | N | dip|perm |
| `Rim|Soph_Early|Mid_usage` | REB_per36 | Stationary | 0.000 | 0.37 | 4/5 | N | dip|perm |
