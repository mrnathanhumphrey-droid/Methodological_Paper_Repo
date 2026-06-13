# Step 0/1 — P0 partition diagnostic (arm = mpg_adj)

Locked SHA v1.0: `db0ed9a899c28691183cd5b640f460c10f3c2a75`
(v1.1 amendment not in scope)

K_raw materialized = 36 / 36 possible
K_final after collapse = **25**
Qualifying player-seasons: 2,798
Merges applied: 11

## Final cells (post-collapse), by season

| cell_id | 2019-20 | 2020-21 | 2021-22 | 2022-23 | 2023-24 | 2024-25 | 2025-26 | TOTAL | MIN/season |
|---|---|---|---|---|---|---|---|---|---|
| `Guard|Soph_Early|Starter` | 23 | 26 | 27 | 28 | 27 | 25 | 22 | 178 | 22 |
| `Guard|Soph_Early|Rotation` | 25 | 32 | 21 | 26 | 19 | 26 | 22 | 171 | 19 |
| `Forward|Soph_Early|Rotation` | 22 | 12 | 23 | 25 | 26 | 33 | 25 | 166 | 12 |
| `Guard|Mid|Starter` | 17 | 25 | 26 | 21 | 26 | 21 | 20 | 156 | 17 |
| `Guard|Rookie|Rotation` | 31 | 23 | 26 | 18 | 14 | 15 | 29 | 156 | 14 |
| `Forward|Rookie|Rotation` | 19 | 28 | 22 | 17 | 27 | 22 | 20 | 155 | 17 |
| `Guard|Mid|Rotation` | 27 | 23 | 21 | 21 | 17 | 25 | 21 | 155 | 17 |
| `Center|Soph_Early|Rotation` | 17 | 20 | 21 | 28 | 19 | 19 | 22 | 146 | 17 |
| `Forward|Soph_Early|Starter` | 24 | 18 | 16 | 20 | 17 | 17 | 21 | 133 | 16 |
| `Forward|Soph_Early|Bench` | 14 | 19 | 21 | 18 | 19 | 14 | 23 | 128 | 14 |
| `Guard|Soph_Early|Bench` | 21 | 15 | 25 | 15 | 22 | 12 | 18 | 128 | 12 |
| `Forward|Mid|Starter` | 13 | 15 | 16 | 19 | 18 | 18 | 19 | 118 | 13 |
| `Center|Mid|Rotation` | 12 | 18 | 17 | 13 | 16 | 19 | 23 | 118 | 12 |
| `Guard|Rookie|Bench` | 16 | 17 | 18 | 19 | 13 | 14 | 13 | 110 | 13 |
| `Forward|Rookie|Bench` | 12 | 17 | 12 | 17 | 14 | 19 | 11 | 102 | 11 |
| `Forward|Mid|Rotation` | 13 | 20 | 13 | 9 | 14 | 13 | 14 | 96 | 9 |
| `Center|Soph_Early|Bench` | 10 | 11 | 9 | 6 | 15 | 14 | 9 | 74 | 6 |
| `Guard|Deep_vet|Rotation` | 9 | 7 | 12 | 13 | 13 | 14 | 6 | 74 | 6 |
| `Center|Mid|Starter` | 9 | 8 | 12 | 12 | 11 | 13 | 9 | 74 | 8 |
| `Forward|Deep_vet|Rotation` | 9 | 9 | 11 | 9 | 10 | 9 | 11 | 68 | 9 |
| `Forward|Mid|Bench` | 7 | 5 | 9 | 14 | 13 | 6 | 11 | 65 | 5 |
| `Center|Mid|Bench` | 10 | 7 | 7 | 6 | 9 | 12 | 11 | 62 | 6 |
| `Guard|Mid|Bench` | 7 | 7 | 8 | 7 | 6 | 11 | 10 | 56 | 6 |
| `Center|Rookie|Rotation` | 6 | 8 | 7 | 7 | 6 | 11 | 10 | 55 | 6 |
| `Center|Rookie|Bench` | 8 | 5 | 9 | 10 | 7 | 9 | 6 | 54 | 5 |

## Merge log (sparse-cell collapse)

| target | into_neighbor | axis | total | min/season |
|---|---|---|---|---|
| `Center|Deep_vet|Starter` | `Center|Deep_vet|Rotation` | role_cohort | 9 | 0 |
| `Center|Rookie|Starter` | `Center|Rookie|Rotation` | role_cohort | 10 | 0 |
| `Center|Deep_vet|Bench` | `Center|Deep_vet|Rotation` | role_cohort | 14 | 0 |
| `Forward|Deep_vet|Bench` | `Forward|Deep_vet|Rotation` | role_cohort | 14 | 0 |
| `Guard|Deep_vet|Bench` | `Guard|Deep_vet|Rotation` | role_cohort | 21 | 0 |
| `Forward|Deep_vet|Starter` | `Forward|Deep_vet|Rotation` | role_cohort | 29 | 2 |
| `Guard|Deep_vet|Starter` | `Guard|Deep_vet|Rotation` | role_cohort | 32 | 3 |
| `Center|Deep_vet|Rotation` | `Center|Mid|Rotation` | years_pro | 35 | 2 |
| `Guard|Rookie|Starter` | `Guard|Rookie|Rotation` | role_cohort | 42 | 2 |
| `Forward|Rookie|Starter` | `Forward|Rookie|Rotation` | role_cohort | 44 | 3 |
| `Center|Soph_Early|Starter` | `Center|Soph_Early|Rotation` | role_cohort | 47 | 3 |
