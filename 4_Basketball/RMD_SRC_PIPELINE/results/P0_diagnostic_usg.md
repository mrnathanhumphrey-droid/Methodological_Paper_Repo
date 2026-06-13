# Step 0/1 — P0 partition diagnostic

Locked SHA: `db0ed9a899c28691183cd5b640f460c10f3c2a75`

K_raw materialized = 34 / 36 possible
K_final after collapse = **19**
Qualifying player-seasons: 2,798
Merges applied: 15

## Final cells (post-collapse), by season

| cell_id | 2019-20 | 2020-21 | 2021-22 | 2022-23 | 2023-24 | 2024-25 | 2025-26 | TOTAL | MIN/season |
|---|---|---|---|---|---|---|---|---|---|
| `Guard|Soph_Early|Mid_usage` | 48 | 52 | 47 | 48 | 45 | 42 | 54 | 336 | 42 |
| `Forward|Soph_Early|Mid_usage` | 37 | 34 | 41 | 41 | 40 | 38 | 50 | 281 | 34 |
| `Guard|Rookie|Mid_usage` | 40 | 36 | 43 | 29 | 23 | 36 | 39 | 246 | 23 |
| `Forward|Mid|Mid_usage` | 25 | 34 | 32 | 38 | 33 | 31 | 27 | 220 | 25 |
| `Guard|Mid|Mid_usage` | 28 | 30 | 27 | 27 | 32 | 36 | 30 | 210 | 27 |
| `Center|Mid|Mid_usage` | 25 | 26 | 25 | 21 | 21 | 25 | 29 | 172 | 21 |
| `Forward|Soph_Early|Low_usage` | 28 | 20 | 20 | 26 | 23 | 22 | 16 | 155 | 16 |
| `Forward|Rookie|Mid_usage` | 20 | 21 | 20 | 19 | 16 | 22 | 16 | 134 | 16 |
| `Center|Soph_Early|Mid_usage` | 18 | 20 | 19 | 17 | 20 | 21 | 14 | 129 | 14 |
| `Guard|Soph_Early|Low_usage` | 13 | 11 | 21 | 18 | 17 | 21 | 13 | 114 | 11 |
| `Guard|Mid|High_usage` | 14 | 15 | 18 | 15 | 13 | 18 | 16 | 109 | 13 |
| `Guard|Soph_Early|High_usage` | 12 | 16 | 15 | 16 | 19 | 16 | 15 | 109 | 12 |
| `Forward|Rookie|Low_usage` | 13 | 21 | 15 | 16 | 17 | 13 | 13 | 108 | 13 |
| `Forward|Mid|Low_usage` | 12 | 11 | 15 | 11 | 22 | 17 | 19 | 107 | 11 |
| `Guard|Deep_vet|Mid_usage` | 9 | 7 | 13 | 15 | 15 | 16 | 8 | 83 | 7 |
| `Guard|Rookie|Low_usage` | 10 | 13 | 8 | 12 | 17 | 8 | 8 | 76 | 8 |
| `Guard|Mid|Low_usage` | 11 | 12 | 11 | 9 | 7 | 9 | 15 | 74 | 7 |
| `Center|Rookie|Mid_usage` | 9 | 7 | 8 | 12 | 8 | 11 | 13 | 68 | 7 |
| `Forward|Deep_vet|Mid_usage` | 9 | 9 | 11 | 8 | 10 | 9 | 11 | 67 | 8 |

## Merge log (sparse-cell collapse)

| target (merged into neighbor) | neighbor | axis | target total | target min/season |
|---|---|---|---|---|
| `Center|Soph_Early|High_usage` | `Center|Soph_Early|Mid_usage` | role_cohort | 6 | 0 |
| `Forward|Rookie|High_usage` | `Forward|Rookie|Mid_usage` | role_cohort | 8 | 0 |
| `Center|Mid|High_usage` | `Center|Mid|Mid_usage` | role_cohort | 12 | 0 |
| `Center|Deep_vet|Low_usage` | `Center|Deep_vet|Mid_usage` | role_cohort | 13 | 0 |
| `Forward|Deep_vet|Low_usage` | `Forward|Deep_vet|Mid_usage` | role_cohort | 16 | 1 |
| `Forward|Deep_vet|High_usage` | `Forward|Deep_vet|Mid_usage` | role_cohort | 17 | 1 |
| `Guard|Deep_vet|Low_usage` | `Guard|Deep_vet|Mid_usage` | role_cohort | 19 | 1 |
| `Guard|Rookie|High_usage` | `Guard|Rookie|Mid_usage` | role_cohort | 27 | 1 |
| `Center|Deep_vet|Mid_usage` | `Center|Mid|Mid_usage` | years_pro | 27 | 2 |
| `Guard|Deep_vet|High_usage` | `Guard|Deep_vet|Mid_usage` | role_cohort | 27 | 2 |
| `Center|Rookie|Low_usage` | `Center|Rookie|Mid_usage` | role_cohort | 31 | 2 |
| `Forward|Soph_Early|High_usage` | `Forward|Soph_Early|Mid_usage` | role_cohort | 36 | 4 |
| `Forward|Mid|High_usage` | `Forward|Mid|Mid_usage` | role_cohort | 44 | 5 |
| `Center|Mid|Low_usage` | `Center|Mid|Mid_usage` | role_cohort | 46 | 4 |
| `Center|Soph_Early|Low_usage` | `Center|Soph_Early|Mid_usage` | role_cohort | 48 | 3 |

## Bucket-level coverage diagnostics
- Missing `debut_year` dropped: 0
- Missing position dropped: 0
- Empty position string defaulted to Guard: 0
- Rookie / no-prior-USG default to Mid_usage: 277 (9.9% of qualifying)
