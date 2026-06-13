# Step 0/1 SPATIAL — P0 partition diagnostic (arm = def_feast_mpg)

Axis: court-region-of-feast. Locked SHA: `cd40b46`

K_raw materialized = 36 / 36
K_final after collapse = **25**
Player-seasons in partition: 2,798
Profile-Sparse excluded: 0
Merges applied: 11

## region x v1.0 position confusion

| region | Center | Forward | Guard |
|---|---|---|---|
| Hybrid | 105 | 413 | 526 |
| Perimeter | 59 | 268 | 580 |
| RimProtector | 205 | 391 | 251 |

## Final cells (post-collapse), by season

| cell_id | 2019-20 | 2020-21 | 2021-22 | 2022-23 | 2023-24 | 2024-25 | 2025-26 | TOTAL | MIN/season |
|---|---|---|---|---|---|---|---|---|---|
| `Perimeter|Mid|Rotation` | 30 | 29 | 23 | 20 | 23 | 34 | 37 | 196 | 20 |
| `Hybrid|Soph_Early|Rotation` | 21 | 22 | 23 | 25 | 20 | 30 | 22 | 163 | 20 |
| `RimProtector|Rookie|Rotation` | 25 | 21 | 24 | 20 | 23 | 21 | 21 | 155 | 20 |
| `Hybrid|Mid|Starter` | 19 | 23 | 21 | 21 | 20 | 26 | 18 | 148 | 18 |
| `Hybrid|Soph_Early|Starter` | 19 | 22 | 16 | 23 | 23 | 18 | 26 | 147 | 16 |
| `Perimeter|Soph_Early|Rotation` | 17 | 20 | 20 | 25 | 21 | 21 | 20 | 144 | 17 |
| `Perimeter|Mid|Starter` | 14 | 17 | 24 | 20 | 24 | 18 | 24 | 141 | 14 |
| `RimProtector|Soph_Early|Rotation` | 17 | 13 | 15 | 22 | 17 | 24 | 21 | 129 | 13 |
| `Hybrid|Soph_Early|Bench` | 13 | 16 | 23 | 13 | 26 | 10 | 21 | 122 | 10 |
| `Hybrid|Rookie|Rotation` | 18 | 25 | 19 | 13 | 12 | 14 | 19 | 120 | 12 |
| `RimProtector|Soph_Early|Bench` | 19 | 19 | 17 | 12 | 18 | 19 | 15 | 119 | 12 |
| `Hybrid|Mid|Rotation` | 19 | 15 | 13 | 13 | 16 | 18 | 18 | 112 | 13 |
| `Perimeter|Soph_Early|Starter` | 19 | 14 | 18 | 19 | 14 | 12 | 13 | 109 | 12 |
| `RimProtector|Rookie|Bench` | 16 | 17 | 14 | 16 | 13 | 14 | 14 | 104 | 13 |
| `RimProtector|Soph_Early|Starter` | 18 | 17 | 16 | 13 | 13 | 15 | 10 | 102 | 10 |
| `Hybrid|Rookie|Bench` | 12 | 12 | 15 | 23 | 10 | 16 | 10 | 98 | 10 |
| `Perimeter|Rookie|Rotation` | 13 | 13 | 12 | 9 | 12 | 13 | 19 | 91 | 9 |
| `RimProtector|Mid|Bench` | 10 | 10 | 15 | 17 | 10 | 15 | 13 | 90 | 10 |
| `Perimeter|Soph_Early|Bench` | 13 | 10 | 15 | 14 | 12 | 11 | 14 | 89 | 10 |
| `RimProtector|Mid|Rotation` | 11 | 17 | 18 | 11 | 15 | 8 | 9 | 89 | 8 |
| `Hybrid|Deep_vet|Rotation` | 14 | 6 | 13 | 8 | 12 | 11 | 15 | 79 | 6 |
| `Perimeter|Deep_vet|Rotation` | 5 | 11 | 10 | 14 | 14 | 14 | 5 | 73 | 5 |
| `Perimeter|Rookie|Bench` | 8 | 10 | 10 | 7 | 11 | 12 | 6 | 64 | 6 |
| `RimProtector|Mid|Starter` | 6 | 8 | 9 | 11 | 11 | 8 | 6 | 59 | 6 |
| `Hybrid|Mid|Bench` | 5 | 8 | 6 | 9 | 8 | 9 | 10 | 55 | 5 |

## Merge log

| target | into | axis | total | min/season |
|---|---|---|---|---|
| `RimProtector|Deep_vet|Starter` | `RimProtector|Deep_vet|Rotation` | role_cohort | 4 | 0 |
| `RimProtector|Deep_vet|Rotation` | `RimProtector|Deep_vet|Bench` | role_cohort | 12 | 0 |
| `Perimeter|Deep_vet|Bench` | `Perimeter|Deep_vet|Rotation` | role_cohort | 15 | 0 |
| `Hybrid|Deep_vet|Bench` | `Hybrid|Deep_vet|Rotation` | role_cohort | 21 | 1 |
| `Perimeter|Rookie|Starter` | `Perimeter|Rookie|Rotation` | role_cohort | 24 | 1 |
| `RimProtector|Deep_vet|Bench` | `RimProtector|Mid|Bench` | years_pro | 25 | 1 |
| `Hybrid|Rookie|Starter` | `Hybrid|Rookie|Rotation` | role_cohort | 28 | 3 |
| `Perimeter|Deep_vet|Starter` | `Perimeter|Deep_vet|Rotation` | role_cohort | 30 | 3 |
| `Hybrid|Deep_vet|Starter` | `Hybrid|Deep_vet|Rotation` | role_cohort | 36 | 2 |
| `RimProtector|Rookie|Starter` | `RimProtector|Rookie|Rotation` | role_cohort | 44 | 1 |
| `Perimeter|Mid|Bench` | `Perimeter|Mid|Rotation` | role_cohort | 63 | 3 |
