# Step 0/1 — P0 partition diagnostic (arm = mpg)

Locked SHA v1.0: `db0ed9a899c28691183cd5b640f460c10f3c2a75`
Locked SHA v1.1: `4d0602df832d5a45402a212acf48b19a4dfee070`

K_raw materialized = 36 / 36 possible
K_final after collapse = **21**
Qualifying player-seasons: 2,798
Merges applied: 15

## Final cells (post-collapse), by season

| cell_id | 2019-20 | 2020-21 | 2021-22 | 2022-23 | 2023-24 | 2024-25 | 2025-26 | TOTAL | MIN/season |
|---|---|---|---|---|---|---|---|---|---|
| `Guard|Soph_Early|Rotation` | 26 | 35 | 26 | 33 | 26 | 38 | 29 | 213 | 26 |
| `Guard|Soph_Early|Starter` | 26 | 29 | 29 | 30 | 28 | 27 | 29 | 198 | 26 |
| `Guard|Rookie|Rotation` | 34 | 27 | 30 | 19 | 22 | 22 | 34 | 188 | 19 |
| `Forward|Soph_Early|Rotation` | 24 | 14 | 25 | 31 | 27 | 27 | 27 | 175 | 14 |
| `Center|Mid|Rotation` | 25 | 26 | 25 | 21 | 21 | 25 | 29 | 172 | 21 |
| `Guard|Mid|Starter` | 18 | 26 | 27 | 22 | 29 | 23 | 22 | 167 | 18 |
| `Guard|Mid|Rotation` | 28 | 24 | 21 | 22 | 17 | 27 | 24 | 163 | 17 |
| `Guard|Soph_Early|Bench` | 21 | 15 | 28 | 19 | 27 | 14 | 24 | 148 | 14 |
| `Forward|Rookie|Rotation` | 19 | 27 | 22 | 18 | 20 | 19 | 16 | 141 | 16 |
| `Forward|Soph_Early|Bench` | 17 | 22 | 21 | 16 | 18 | 18 | 23 | 135 | 16 |
| `Guard|Rookie|Bench` | 16 | 22 | 21 | 22 | 18 | 22 | 13 | 134 | 13 |
| `Forward|Mid|Starter` | 15 | 17 | 19 | 23 | 19 | 21 | 19 | 133 | 15 |
| `Center|Soph_Early|Rotation` | 18 | 20 | 19 | 17 | 20 | 21 | 14 | 129 | 14 |
| `Forward|Soph_Early|Starter` | 24 | 18 | 15 | 20 | 18 | 15 | 16 | 126 | 15 |
| `Forward|Mid|Rotation` | 13 | 22 | 19 | 12 | 18 | 15 | 15 | 114 | 12 |
| `Forward|Rookie|Bench` | 14 | 15 | 13 | 17 | 13 | 16 | 13 | 101 | 13 |
| `Guard|Deep_vet|Rotation` | 9 | 7 | 13 | 15 | 15 | 16 | 8 | 83 | 7 |
| `Forward|Mid|Bench` | 9 | 6 | 9 | 14 | 18 | 12 | 12 | 80 | 6 |
| `Center|Rookie|Rotation` | 9 | 7 | 8 | 12 | 8 | 11 | 13 | 68 | 7 |
| `Forward|Deep_vet|Rotation` | 9 | 9 | 11 | 8 | 10 | 9 | 11 | 67 | 8 |
| `Guard|Mid|Bench` | 7 | 7 | 8 | 7 | 6 | 13 | 15 | 63 | 6 |

## Merge log (sparse-cell collapse)

| target | into_neighbor | axis | total | min/season |
|---|---|---|---|---|
| `Center|Rookie|Starter` | `Center|Rookie|Rotation` | role_cohort | 7 | 0 |
| `Center|Deep_vet|Starter` | `Center|Deep_vet|Rotation` | role_cohort | 8 | 0 |
| `Center|Deep_vet|Bench` | `Center|Deep_vet|Rotation` | role_cohort | 9 | 0 |
| `Forward|Deep_vet|Bench` | `Forward|Deep_vet|Rotation` | role_cohort | 17 | 0 |
| `Guard|Deep_vet|Bench` | `Guard|Deep_vet|Rotation` | role_cohort | 23 | 1 |
| `Forward|Deep_vet|Starter` | `Forward|Deep_vet|Rotation` | role_cohort | 26 | 2 |
| `Center|Deep_vet|Rotation` | `Center|Mid|Rotation` | years_pro | 27 | 2 |
| `Center|Rookie|Bench` | `Center|Rookie|Rotation` | role_cohort | 31 | 2 |
| `Center|Soph_Early|Starter` | `Center|Soph_Early|Rotation` | role_cohort | 34 | 3 |
| `Guard|Deep_vet|Starter` | `Guard|Deep_vet|Rotation` | role_cohort | 36 | 3 |
| `Center|Mid|Bench` | `Center|Mid|Rotation` | role_cohort | 40 | 4 |
| `Forward|Rookie|Starter` | `Forward|Rookie|Rotation` | role_cohort | 42 | 3 |
| `Guard|Rookie|Starter` | `Guard|Rookie|Rotation` | role_cohort | 47 | 2 |
| `Center|Soph_Early|Bench` | `Center|Soph_Early|Rotation` | role_cohort | 47 | 3 |
| `Center|Mid|Starter` | `Center|Mid|Rotation` | role_cohort | 48 | 5 |
