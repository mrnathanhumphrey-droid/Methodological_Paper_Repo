# Step 0/1 SPATIAL — P0 partition diagnostic (arm = def_feast)

Axis: court-region-of-feast. Locked SHA: `cd40b46`

K_raw materialized = 36 / 36
K_final after collapse = **22**
Player-seasons in partition: 2,798
Profile-Sparse excluded: 0
Merges applied: 14

## region x v1.0 position confusion

| region | Center | Forward | Guard |
|---|---|---|---|
| Hybrid | 105 | 413 | 526 |
| Perimeter | 59 | 268 | 580 |
| RimProtector | 205 | 391 | 251 |

## Final cells (post-collapse), by season

| cell_id | 2019-20 | 2020-21 | 2021-22 | 2022-23 | 2023-24 | 2024-25 | 2025-26 | TOTAL | MIN/season |
|---|---|---|---|---|---|---|---|---|---|
| `Perimeter|Soph_Early|Mid_usage` | 37 | 35 | 42 | 43 | 31 | 28 | 36 | 252 | 28 |
| `Hybrid|Soph_Early|Mid_usage` | 31 | 37 | 33 | 34 | 38 | 25 | 45 | 243 | 25 |
| `RimProtector|Soph_Early|Mid_usage` | 32 | 32 | 36 | 28 | 32 | 45 | 38 | 243 | 28 |
| `Perimeter|Mid|Mid_usage` | 20 | 29 | 22 | 20 | 23 | 29 | 30 | 173 | 20 |
| `Hybrid|Mid|Mid_usage` | 28 | 20 | 22 | 26 | 21 | 32 | 24 | 173 | 20 |
| `RimProtector|Rookie|Mid_usage` | 33 | 16 | 31 | 21 | 21 | 26 | 25 | 173 | 16 |
| `RimProtector|Mid|Mid_usage` | 18 | 24 | 33 | 29 | 27 | 24 | 17 | 172 | 17 |
| `Perimeter|Rookie|Mid_usage` | 21 | 23 | 22 | 16 | 23 | 25 | 25 | 155 | 16 |
| `Hybrid|Rookie|Mid_usage` | 18 | 28 | 20 | 23 | 9 | 21 | 19 | 138 | 9 |
| `Hybrid|Soph_Early|Low_usage` | 16 | 13 | 22 | 17 | 18 | 21 | 13 | 120 | 13 |
| `RimProtector|Soph_Early|Low_usage` | 22 | 17 | 12 | 19 | 16 | 13 | 8 | 107 | 8 |
| `Perimeter|Mid|Low_usage` | 14 | 9 | 12 | 10 | 13 | 12 | 21 | 91 | 9 |
| `Perimeter|Soph_Early|Low_usage` | 12 | 9 | 11 | 15 | 16 | 16 | 11 | 90 | 9 |
| `RimProtector|Rookie|Low_usage` | 8 | 22 | 7 | 15 | 15 | 9 | 10 | 86 | 7 |
| `Hybrid|Rookie|Low_usage` | 12 | 9 | 14 | 13 | 13 | 9 | 10 | 80 | 9 |
| `Hybrid|Deep_vet|Mid_usage` | 14 | 6 | 13 | 8 | 12 | 11 | 15 | 79 | 6 |
| `Perimeter|Deep_vet|Mid_usage` | 5 | 11 | 10 | 14 | 14 | 14 | 5 | 73 | 5 |
| `Perimeter|Mid|High_usage` | 10 | 8 | 13 | 10 | 11 | 11 | 10 | 73 | 8 |
| `Hybrid|Mid|High_usage` | 9 | 13 | 9 | 11 | 11 | 9 | 10 | 72 | 9 |
| `Hybrid|Mid|Low_usage` | 6 | 13 | 9 | 6 | 12 | 12 | 12 | 70 | 6 |
| `Hybrid|Soph_Early|High_usage` | 6 | 10 | 7 | 10 | 13 | 12 | 11 | 69 | 6 |
| `RimProtector|Mid|Low_usage` | 9 | 11 | 9 | 10 | 9 | 7 | 11 | 66 | 7 |

## Merge log

| target | into | axis | total | min/season |
|---|---|---|---|---|
| `RimProtector|Deep_vet|High_usage` | `RimProtector|Deep_vet|Mid_usage` | role_cohort | 2 | 0 |
| `RimProtector|Deep_vet|Low_usage` | `RimProtector|Deep_vet|Mid_usage` | role_cohort | 7 | 0 |
| `Perimeter|Rookie|High_usage` | `Perimeter|Rookie|Mid_usage` | role_cohort | 9 | 0 |
| `RimProtector|Rookie|High_usage` | `RimProtector|Rookie|Mid_usage` | role_cohort | 12 | 0 |
| `Hybrid|Rookie|High_usage` | `Hybrid|Rookie|Mid_usage` | role_cohort | 14 | 0 |
| `Perimeter|Deep_vet|High_usage` | `Perimeter|Deep_vet|Mid_usage` | role_cohort | 19 | 1 |
| `RimProtector|Mid|High_usage` | `RimProtector|Mid|Mid_usage` | role_cohort | 20 | 0 |
| `Perimeter|Deep_vet|Low_usage` | `Perimeter|Deep_vet|Mid_usage` | role_cohort | 20 | 1 |
| `Hybrid|Deep_vet|Low_usage` | `Hybrid|Deep_vet|Mid_usage` | role_cohort | 21 | 0 |
| `Hybrid|Deep_vet|High_usage` | `Hybrid|Deep_vet|Mid_usage` | role_cohort | 23 | 1 |
| `RimProtector|Deep_vet|Mid_usage` | `RimProtector|Mid|Mid_usage` | years_pro | 25 | 1 |
| `RimProtector|Soph_Early|High_usage` | `RimProtector|Soph_Early|Mid_usage` | role_cohort | 33 | 2 |
| `Perimeter|Rookie|Low_usage` | `Perimeter|Rookie|Mid_usage` | role_cohort | 49 | 4 |
| `Perimeter|Soph_Early|High_usage` | `Perimeter|Soph_Early|Mid_usage` | role_cohort | 49 | 4 |
