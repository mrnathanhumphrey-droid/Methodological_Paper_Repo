# Step 0/1 SPATIAL — P0 partition diagnostic (arm = off_feast)

Axis: court-region-of-feast. Locked SHA: `cd40b46`

K_raw materialized = 34 / 36
K_final after collapse = **15**
Player-seasons in partition: 2,790
Profile-Sparse excluded: 8
Merges applied: 19

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
| `Perimeter|Soph_Early|Mid_usage` | 62 | 73 | 75 | 69 | 66 | 64 | 81 | 490 | 62 |
| `Perimeter|Mid|Mid_usage` | 50 | 51 | 46 | 49 | 47 | 54 | 52 | 349 | 46 |
| `Perimeter|Rookie|Mid_usage` | 50 | 45 | 47 | 38 | 35 | 53 | 53 | 321 | 35 |
| `Perimeter|Soph_Early|Low_usage` | 28 | 23 | 30 | 30 | 33 | 33 | 22 | 199 | 22 |
| `Rim|Mid|Mid_usage` | 18 | 21 | 32 | 26 | 31 | 32 | 24 | 184 | 18 |
| `Rim|Soph_Early|Mid_usage` | 27 | 22 | 24 | 26 | 23 | 25 | 26 | 173 | 22 |
| `Perimeter|Deep_vet|Mid_usage` | 19 | 17 | 23 | 23 | 22 | 26 | 20 | 150 | 17 |
| `Perimeter|Mid|High_usage` | 17 | 22 | 24 | 23 | 22 | 21 | 21 | 150 | 17 |
| `Perimeter|Mid|Low_usage` | 21 | 22 | 17 | 15 | 22 | 18 | 27 | 142 | 15 |
| `Perimeter|Rookie|Low_usage` | 16 | 23 | 17 | 21 | 27 | 18 | 15 | 137 | 15 |
| `Perimeter|Soph_Early|High_usage` | 17 | 19 | 17 | 18 | 21 | 20 | 20 | 132 | 17 |
| `Rim|Soph_Early|Low_usage` | 21 | 15 | 14 | 20 | 17 | 17 | 10 | 114 | 10 |
| `Rim|Rookie|Mid_usage` | 16 | 16 | 21 | 15 | 8 | 9 | 8 | 93 | 8 |
| `Rim|Mid|Low_usage` | 7 | 10 | 13 | 11 | 12 | 13 | 16 | 82 | 7 |
| `Rim|Rookie|Low_usage` | 10 | 14 | 8 | 14 | 9 | 8 | 11 | 74 | 8 |

## Merge log

| target | into | axis | total | min/season |
|---|---|---|---|---|
| `Paint|Mid|High_usage` | `Paint|Mid|Mid_usage` | role_cohort | 1 | 0 |
| `Paint|Mid|Low_usage` | `Paint|Mid|Mid_usage` | role_cohort | 1 | 0 |
| `Paint|Rookie|High_usage` | `Paint|Rookie|Mid_usage` | role_cohort | 1 | 0 |
| `Paint|Soph_Early|Low_usage` | `Paint|Soph_Early|Mid_usage` | role_cohort | 1 | 0 |
| `Paint|Deep_vet|Mid_usage` | `Paint|Mid|Mid_usage` | years_pro | 2 | 0 |
| `Paint|Rookie|Low_usage` | `Paint|Rookie|Mid_usage` | role_cohort | 2 | 0 |
| `Paint|Soph_Early|High_usage` | `Paint|Soph_Early|Mid_usage` | role_cohort | 2 | 0 |
| `Rim|Deep_vet|High_usage` | `Rim|Deep_vet|Mid_usage` | role_cohort | 4 | 0 |
| `Paint|Rookie|Mid_usage` | `Paint|Soph_Early|Mid_usage` | years_pro | 5 | 0 |
| `Rim|Rookie|High_usage` | `Rim|Rookie|Mid_usage` | role_cohort | 5 | 0 |
| `Rim|Deep_vet|Low_usage` | `Rim|Deep_vet|Mid_usage` | role_cohort | 12 | 0 |
| `Rim|Mid|High_usage` | `Rim|Mid|Mid_usage` | role_cohort | 14 | 1 |
| `Rim|Soph_Early|High_usage` | `Rim|Soph_Early|Mid_usage` | role_cohort | 17 | 1 |
| `Paint|Soph_Early|Mid_usage` | `Paint|Mid|Mid_usage` | years_pro | 18 | 0 |
| `Rim|Deep_vet|Mid_usage` | `Rim|Mid|Mid_usage` | years_pro | 24 | 1 |
| `Perimeter|Rookie|High_usage` | `Perimeter|Rookie|Mid_usage` | role_cohort | 29 | 3 |
| `Perimeter|Deep_vet|Low_usage` | `Perimeter|Deep_vet|Mid_usage` | role_cohort | 35 | 3 |
| `Perimeter|Deep_vet|High_usage` | `Perimeter|Deep_vet|Mid_usage` | role_cohort | 40 | 3 |
| `Paint|Mid|Mid_usage` | `Rim|Mid|Mid_usage` | region | 42 | 1 |
