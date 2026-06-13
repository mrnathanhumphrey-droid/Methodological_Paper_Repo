# Step 0/1 — P0 partition diagnostic (arm = usg_adj)

Locked SHA v1.0: `db0ed9a899c28691183cd5b640f460c10f3c2a75`
(v1.1 amendment not in scope)

K_raw materialized = 36 / 36 possible
K_final after collapse = **21**
Qualifying player-seasons: 2,798
Merges applied: 15

## Final cells (post-collapse), by season

| cell_id | 2019-20 | 2020-21 | 2021-22 | 2022-23 | 2023-24 | 2024-25 | 2025-26 | TOTAL | MIN/season |
|---|---|---|---|---|---|---|---|---|---|
| `Guard|Soph_Early|Mid_usage` | 45 | 49 | 43 | 43 | 41 | 36 | 40 | 297 | 36 |
| `Forward|Soph_Early|Mid_usage` | 35 | 31 | 39 | 38 | 38 | 37 | 50 | 268 | 31 |
| `Guard|Rookie|Mid_usage` | 47 | 40 | 44 | 37 | 27 | 29 | 42 | 266 | 27 |
| `Guard|Mid|Mid_usage` | 28 | 30 | 27 | 26 | 31 | 32 | 28 | 202 | 26 |
| `Forward|Mid|Mid_usage` | 21 | 30 | 28 | 33 | 27 | 26 | 25 | 190 | 21 |
| `Center|Mid|Mid_usage` | 24 | 21 | 27 | 23 | 26 | 32 | 27 | 180 | 21 |
| `Forward|Soph_Early|Low_usage` | 25 | 18 | 21 | 25 | 24 | 27 | 19 | 159 | 18 |
| `Forward|Rookie|Mid_usage` | 18 | 20 | 20 | 19 | 21 | 27 | 17 | 142 | 17 |
| `Center|Soph_Early|Mid_usage` | 14 | 19 | 23 | 19 | 17 | 21 | 25 | 138 | 14 |
| `Forward|Rookie|Low_usage` | 13 | 25 | 14 | 15 | 20 | 14 | 14 | 115 | 13 |
| `Guard|Soph_Early|High_usage` | 12 | 15 | 13 | 15 | 18 | 16 | 15 | 104 | 12 |
| `Guard|Mid|High_usage` | 13 | 14 | 17 | 14 | 12 | 17 | 14 | 101 | 12 |
| `Forward|Mid|Low_usage` | 12 | 10 | 10 | 9 | 18 | 11 | 19 | 89 | 9 |
| `Center|Soph_Early|Low_usage` | 13 | 12 | 7 | 15 | 17 | 12 | 6 | 82 | 6 |
| `Guard|Soph_Early|Low_usage` | 12 | 9 | 17 | 11 | 9 | 11 | 7 | 76 | 7 |
| `Center|Mid|Low_usage` | 7 | 12 | 9 | 8 | 10 | 12 | 16 | 74 | 7 |
| `Guard|Deep_vet|Mid_usage` | 9 | 7 | 12 | 13 | 13 | 14 | 6 | 74 | 6 |
| `Forward|Deep_vet|Mid_usage` | 9 | 9 | 11 | 9 | 10 | 9 | 11 | 68 | 9 |
| `Guard|Mid|Low_usage` | 10 | 11 | 11 | 9 | 6 | 8 | 9 | 64 | 6 |
| `Center|Rookie|Mid_usage` | 9 | 6 | 11 | 7 | 5 | 10 | 9 | 57 | 5 |
| `Center|Rookie|Low_usage` | 5 | 7 | 5 | 10 | 8 | 10 | 7 | 52 | 5 |

## Merge log (sparse-cell collapse)

| target | into_neighbor | axis | total | min/season |
|---|---|---|---|---|
| `Center|Deep_vet|High_usage` | `Center|Deep_vet|Mid_usage` | role_cohort | 1 | 0 |
| `Center|Rookie|High_usage` | `Center|Rookie|Mid_usage` | role_cohort | 2 | 0 |
| `Forward|Rookie|High_usage` | `Forward|Rookie|Mid_usage` | role_cohort | 6 | 0 |
| `Center|Soph_Early|High_usage` | `Center|Soph_Early|Mid_usage` | role_cohort | 9 | 0 |
| `Guard|Deep_vet|Low_usage` | `Guard|Deep_vet|Mid_usage` | role_cohort | 14 | 1 |
| `Center|Deep_vet|Low_usage` | `Center|Deep_vet|Mid_usage` | role_cohort | 15 | 0 |
| `Forward|Deep_vet|High_usage` | `Forward|Deep_vet|Mid_usage` | role_cohort | 19 | 1 |
| `Forward|Deep_vet|Low_usage` | `Forward|Deep_vet|Mid_usage` | role_cohort | 19 | 2 |
| `Center|Mid|High_usage` | `Center|Mid|Mid_usage` | role_cohort | 23 | 2 |
| `Guard|Deep_vet|High_usage` | `Guard|Deep_vet|Mid_usage` | role_cohort | 24 | 2 |
| `Guard|Rookie|High_usage` | `Guard|Rookie|Mid_usage` | role_cohort | 27 | 1 |
| `Center|Deep_vet|Mid_usage` | `Center|Mid|Mid_usage` | years_pro | 35 | 2 |
| `Forward|Soph_Early|High_usage` | `Forward|Soph_Early|Mid_usage` | role_cohort | 38 | 4 |
| `Forward|Mid|High_usage` | `Forward|Mid|Mid_usage` | role_cohort | 41 | 4 |
| `Guard|Rookie|Low_usage` | `Guard|Rookie|Mid_usage` | role_cohort | 48 | 4 |
