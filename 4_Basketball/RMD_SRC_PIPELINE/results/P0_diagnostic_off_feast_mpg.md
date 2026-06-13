# Step 0/1 SPATIAL — P0 partition diagnostic (arm = off_feast_mpg)

Axis: court-region-of-feast. Locked SHA: `cd40b46`

K_raw materialized = 32 / 36
K_final after collapse = **19**
Player-seasons in partition: 2,790
Profile-Sparse excluded: 8
Merges applied: 13

## region x v1.0 position confusion

| region | Center | Forward | Guard |
|---|---|---|---|
| Paint | 16 | 11 | 15 |
| Perimeter | 95 | 762 | 1213 |
| Profile-Sparse | 4 | 3 | 1 |
| Rim | 254 | 296 | 128 |

## Final cells (post-collapse), by season

| cell_id | 2019-20 | 2020-21 | 2021-22 | 2022-23 | 2023-24 | 2024-25 | 2025-26 | TOTAL | MIN/season |
|---|---|---|---|---|---|---|---|---|---|
| `Perimeter|Soph_Early|Rotation` | 36 | 38 | 42 | 51 | 45 | 56 | 48 | 316 | 36 |
| `Perimeter|Soph_Early|Starter` | 47 | 46 | 42 | 43 | 40 | 37 | 39 | 294 | 37 |
| `Perimeter|Mid|Starter` | 32 | 42 | 46 | 42 | 46 | 39 | 43 | 290 | 32 |
| `Perimeter|Mid|Rotation` | 39 | 41 | 29 | 26 | 27 | 38 | 36 | 236 | 26 |
| `Perimeter|Soph_Early|Bench` | 24 | 31 | 38 | 23 | 35 | 24 | 36 | 211 | 23 |
| `Perimeter|Rookie|Rotation` | 26 | 26 | 30 | 16 | 26 | 31 | 40 | 195 | 16 |
| `Perimeter|Rookie|Bench` | 27 | 28 | 22 | 31 | 27 | 33 | 23 | 191 | 22 |
| `Rim|Mid|Rotation` | 12 | 19 | 23 | 17 | 22 | 21 | 20 | 134 | 12 |
| `Rim|Soph_Early|Rotation` | 19 | 17 | 16 | 21 | 13 | 19 | 15 | 120 | 13 |
| `Perimeter|Mid|Bench` | 17 | 12 | 12 | 19 | 18 | 16 | 21 | 115 | 12 |
| `Rim|Soph_Early|Bench` | 20 | 13 | 16 | 15 | 19 | 16 | 14 | 113 | 13 |
| `Rim|Rookie|Rotation` | 17 | 19 | 13 | 14 | 12 | 10 | 12 | 97 | 10 |
| `Perimeter|Deep_vet|Rotation` | 11 | 11 | 16 | 10 | 13 | 14 | 10 | 85 | 10 |
| `Rim|Rookie|Bench` | 9 | 11 | 17 | 16 | 7 | 9 | 9 | 78 | 7 |
| `Perimeter|Rookie|Starter` | 13 | 14 | 12 | 12 | 9 | 7 | 5 | 72 | 5 |
| `Perimeter|Deep_vet|Starter` | 8 | 6 | 7 | 13 | 9 | 12 | 10 | 65 | 6 |
| `Rim|Soph_Early|Starter` | 9 | 7 | 8 | 12 | 10 | 8 | 10 | 64 | 7 |
| `Rim|Mid|Bench` | 6 | 6 | 11 | 8 | 10 | 11 | 10 | 62 | 6 |
| `Rim|Mid|Starter` | 7 | 6 | 8 | 9 | 7 | 10 | 5 | 52 | 5 |

## Merge log

| target | into | axis | total | min/season |
|---|---|---|---|---|
| `Paint|Deep_vet|Bench` | `Paint|Mid|Bench` | years_pro | 2 | 0 |
| `Paint|Rookie|Rotation` | `Paint|Rookie|Bench` | role_cohort | 2 | 0 |
| `Paint|Soph_Early|Bench` | `Paint|Rookie|Bench` | years_pro | 3 | 0 |
| `Rim|Deep_vet|Starter` | `Rim|Deep_vet|Rotation` | role_cohort | 5 | 0 |
| `Paint|Mid|Bench` | `Paint|Mid|Rotation` | role_cohort | 6 | 0 |
| `Paint|Mid|Starter` | `Paint|Mid|Rotation` | role_cohort | 6 | 0 |
| `Paint|Rookie|Bench` | `Rim|Rookie|Bench` | region | 8 | 0 |
| `Paint|Soph_Early|Starter` | `Rim|Soph_Early|Starter` | region | 10 | 0 |
| `Rim|Deep_vet|Bench` | `Rim|Deep_vet|Rotation` | role_cohort | 12 | 0 |
| `Rim|Rookie|Starter` | `Rim|Rookie|Rotation` | role_cohort | 24 | 0 |
| `Paint|Mid|Rotation` | `Rim|Mid|Rotation` | region | 24 | 1 |
| `Rim|Deep_vet|Rotation` | `Rim|Mid|Rotation` | years_pro | 24 | 1 |
| `Perimeter|Deep_vet|Bench` | `Perimeter|Deep_vet|Rotation` | role_cohort | 34 | 2 |
