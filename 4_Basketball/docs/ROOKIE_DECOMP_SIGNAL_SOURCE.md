# Rookie Decomp — Signal Source Cascade

Window: 2014-24 draft years, Y1 GP >= 25.
Univariate regressions of each candidate input vs each Y1 NBA outcome per-36 stat.

## Per-target top 5 predictors (by |corr|)

### NBA Y1 pts_per36

| Family | Input | n | Corr | R² | Slope |
|---|---|---:|---:|---:|---:|
| DRAFT | draft_pick | 367 | -0.320 | +0.102 | -0.0745 |
| PRE_NBA | ncaa_pts_per40 | 296 | +0.277 | +0.077 | +0.2498 |
| DRAFT | draft_round | 367 | -0.261 | +0.068 | -2.0155 |
| PRE_NBA | intl_pts_per40 | 214 | +0.207 | +0.043 | +0.1009 |
| PRE_NBA | intl_stl_per40 | 214 | -0.167 | +0.028 | -0.4704 |
| PRE_NBA | ncaa_stl_per40 | 296 | -0.142 | +0.020 | -0.7873 |
| PRE_NBA | ncaa_blk_per40 | 296 | +0.128 | +0.016 | +0.4012 |
| COMBINE | combine_standing_vertical_inches | 195 | -0.115 | +0.013 | -0.1300 |

### NBA Y1 reb_per36

| Family | Input | n | Corr | R² | Slope |
|---|---|---:|---:|---:|---:|
| PRE_NBA | ncaa_reb_per40 | 296 | +0.774 | +0.599 | +0.6389 |
| COMBINE | combine_height_no_shoes_inches | 259 | +0.697 | +0.486 | +0.5705 |
| COMBINE | combine_standing_reach_inches | 259 | +0.696 | +0.485 | +0.3778 |
| PRE_NBA | intl_reb_per40 | 214 | +0.695 | +0.483 | +0.4194 |
| COMBINE | combine_wingspan_inches | 259 | +0.675 | +0.456 | +0.4578 |
| COMBINE | combine_weight_lbs | 257 | +0.665 | +0.443 | +0.0754 |
| COMBINE | combine_height_with_shoes_inches | 193 | +0.653 | +0.426 | +0.5370 |
| PRE_NBA | ncaa_blk_per40 | 296 | +0.644 | +0.415 | +1.4295 |

### NBA Y1 ast_per36

| Family | Input | n | Corr | R² | Slope |
|---|---|---:|---:|---:|---:|
| PRE_NBA | ncaa_ast_per40 | 296 | +0.733 | +0.538 | +0.6835 |
| PRE_NBA | intl_ast_per40 | 214 | +0.665 | +0.443 | +0.4309 |
| COMBINE | combine_height_with_shoes_inches | 193 | -0.613 | +0.376 | -0.3480 |
| COMBINE | combine_height_no_shoes_inches | 259 | -0.595 | +0.354 | -0.3313 |
| COMBINE | combine_standing_reach_inches | 259 | -0.564 | +0.318 | -0.2081 |
| COMBINE | combine_wingspan_inches | 259 | -0.545 | +0.297 | -0.2514 |
| COMBINE | combine_weight_lbs | 257 | -0.464 | +0.215 | -0.0356 |
| PRE_NBA | ncaa_reb_per40 | 296 | -0.407 | +0.166 | -0.2350 |

### NBA Y1 stl_per36

| Family | Input | n | Corr | R² | Slope |
|---|---|---:|---:|---:|---:|
| PRE_NBA | ncaa_stl_per40 | 296 | +0.626 | +0.392 | +0.4012 |
| PRE_NBA | intl_ast_per40 | 214 | +0.385 | +0.148 | +0.0617 |
| PRE_NBA | ncaa_ast_per40 | 296 | +0.362 | +0.131 | +0.0785 |
| COMBINE | combine_height_no_shoes_inches | 259 | -0.341 | +0.116 | -0.0470 |
| PRE_NBA | intl_stl_per40 | 214 | +0.324 | +0.105 | +0.1209 |
| COMBINE | combine_height_with_shoes_inches | 193 | -0.303 | +0.092 | -0.0436 |
| COMBINE | combine_standing_reach_inches | 259 | -0.290 | +0.084 | -0.0265 |
| COMBINE | combine_weight_lbs | 257 | -0.246 | +0.060 | -0.0046 |

### NBA Y1 blk_per36

| Family | Input | n | Corr | R² | Slope |
|---|---|---:|---:|---:|---:|
| PRE_NBA | ncaa_blk_per40 | 296 | +0.814 | +0.662 | +0.4688 |
| PRE_NBA | intl_blk_per40 | 214 | +0.678 | +0.460 | +0.3943 |
| COMBINE | combine_standing_reach_inches | 259 | +0.670 | +0.449 | +0.0976 |
| COMBINE | combine_wingspan_inches | 259 | +0.660 | +0.436 | +0.1201 |
| COMBINE | combine_height_no_shoes_inches | 259 | +0.629 | +0.396 | +0.1382 |
| COMBINE | combine_height_with_shoes_inches | 193 | +0.594 | +0.353 | +0.1328 |
| PRE_NBA | ncaa_reb_per40 | 296 | +0.576 | +0.331 | +0.1234 |
| PRE_NBA | intl_reb_per40 | 214 | +0.551 | +0.304 | +0.0958 |

### NBA Y1 fg3m_per36

| Family | Input | n | Corr | R² | Slope |
|---|---|---:|---:|---:|---:|
| PRE_NBA | intl_fg3m_per40 | 214 | +0.578 | +0.334 | +0.3516 |
| PRE_NBA | ncaa_blk_per40 | 296 | -0.440 | +0.193 | -0.3495 |
| PRE_NBA | ncaa_reb_per40 | 296 | -0.431 | +0.186 | -0.1276 |
| COMBINE | combine_wingspan_inches | 259 | -0.415 | +0.173 | -0.1054 |
| PRE_NBA | intl_reb_per40 | 214 | -0.363 | +0.131 | -0.0897 |
| COMBINE | combine_hand_length_inches | 258 | -0.358 | +0.129 | -0.7646 |
| PRE_NBA | intl_fg_pct | 214 | -0.355 | +0.126 | -3.6793 |
| COMBINE | combine_weight_lbs | 257 | -0.337 | +0.114 | -0.0143 |

### NBA Y1 tov_per36

| Family | Input | n | Corr | R² | Slope |
|---|---|---:|---:|---:|---:|
| PRE_NBA | ncaa_tov_per40 | 296 | +0.489 | +0.240 | +0.4804 |
| PRE_NBA | intl_ast_per40 | 214 | +0.338 | +0.114 | +0.0989 |
| PRE_NBA | ncaa_ast_per40 | 296 | +0.302 | +0.091 | +0.1235 |
| COMBINE | combine_bench_press_reps | 62 | -0.225 | +0.051 | -0.0282 |
| COMBINE | combine_height_with_shoes_inches | 193 | -0.224 | +0.050 | -0.0535 |
| DRAFT | draft_pick | 367 | -0.223 | +0.050 | -0.0114 |
| COMBINE | combine_height_no_shoes_inches | 259 | -0.198 | +0.039 | -0.0458 |
| COMBINE | combine_standing_reach_inches | 259 | -0.160 | +0.026 | -0.0246 |

### NBA Y1 mpg

| Family | Input | n | Corr | R² | Slope |
|---|---|---:|---:|---:|---:|
| DRAFT | draft_pick | 367 | -0.514 | +0.264 | -0.2549 |
| DRAFT | draft_round | 367 | -0.362 | +0.131 | -5.9535 |
| COMBINE | combine_bench_press_reps | 62 | +0.188 | +0.035 | +0.2461 |
| PRE_NBA | ncaa_tov_per40 | 296 | +0.134 | +0.018 | +1.3356 |
| COMBINE | combine_three_quarter_sprint_seconds | 194 | -0.121 | +0.015 | -7.1340 |
| PRE_NBA | ncaa_pts_per40 | 296 | +0.118 | +0.014 | +0.2342 |
| PRE_NBA | intl_ast_per40 | 214 | +0.115 | +0.013 | +0.2667 |
| COMBINE | combine_lane_agility_seconds | 195 | -0.105 | +0.011 | -1.7247 |
