# Sloan Adjudicated Test 1 — Results

Single-fire analysis under pre-reg `e52505f`. Adjudication artifact SHA256 `eb615269...`. Cross-paper anchor: v1.2 amendment commit `1bfdb4c` on the RMD-SRC paper.

## Per-cell results (3 seasons x 3 stats x 2 buckets)

Columns: n_in (Center) / n_out (non-Center), variance ratio = sigma_Center / sigma_non-Center, bootstrap 95% CI on the ratio (B=1000 with seed 20260601 per spec), Levene's p (median-centered, load-bearing), Bartlett's p + p_F supplementary.

### BLK x Center

| Season | bucket | n_in | n_out | ratio | CI95 | p_levene | disposition |
|---|---|---|---|---|---|---|---|
| 2023-24 | metadata | 21 | 132 | 1.983 | [1.078, 2.782] | 0.0020 | (control) |
| 2023-24 | **adjudicated** | 33 | 120 | **1.748** | [1.120, 2.355] | **0.0124** | **PERSISTS** |
| 2024-25 | metadata | 21 | 110 | 1.245 | [0.893, 1.600] | 0.1116 | (control) |
| 2024-25 | **adjudicated** | 33 | 98 | **2.012** | [1.536, 2.507] | **0.0000** | **PERSISTS** |
| 2025-26 | metadata | 71 | 414 | 1.664 | [1.344, 2.023] | 0.0000 | (control) |
| 2025-26 | **adjudicated** | 114 | 371 | **1.851** | [1.556, 2.214] | **0.0000** | **PERSISTS** |

### PTS x Center

| Season | bucket | n_in | n_out | ratio | CI95 | p_levene | disposition |
|---|---|---|---|---|---|---|---|
| 2023-24 | metadata | 21 | 132 | 0.944 | [0.615, 1.265] | 0.7485 | (control) |
| 2023-24 | **adjudicated** | 33 | 120 | **0.931** | [0.676, 1.203] | **0.6497** | **NULL** |
| 2024-25 | metadata | 21 | 110 | 0.832 | [0.516, 1.135] | 0.2455 | (control) |
| 2024-25 | **adjudicated** | 33 | 98 | **0.755** | [0.550, 0.994] | **0.0969** | **DIRECTIONAL-PERSISTS** |
| 2025-26 | metadata | 71 | 414 | 0.839 | [0.698, 0.975] | 0.1562 | (control) |
| 2025-26 | **adjudicated** | 114 | 371 | **0.828** | [0.706, 0.949] | **0.0469** | **DIRECTIONAL-PERSISTS** |

### REB x Center

| Season | bucket | n_in | n_out | ratio | CI95 | p_levene | disposition |
|---|---|---|---|---|---|---|---|
| 2023-24 | metadata | 21 | 132 | 1.169 | [0.759, 1.532] | 0.4287 | (control) |
| 2023-24 | **adjudicated** | 33 | 120 | **1.476** | [1.115, 1.866] | **0.0019** | **WALK-BACK FALSIFIED** |
| 2024-25 | metadata | 21 | 110 | 2.156 | [1.275, 3.002] | 0.0000 | (control) |
| 2024-25 | **adjudicated** | 33 | 98 | **2.367** | [1.631, 3.182] | **0.0000** | **WALK-BACK FALSIFIED** |
| 2025-26 | metadata | 71 | 414 | 1.748 | [1.444, 2.060] | 0.0000 | (control) |
| 2025-26 | **adjudicated** | 114 | 371 | **1.762** | [1.496, 2.020] | **0.0000** | **WALK-BACK FALSIFIED** |

## Power lift summary

| Stat | Season | n_in_meta | n_in_adj | lift | gate (>=1.30) |
|---|---|---|---|---|---|
| BLK | 2023-24 | 21 | 33 | 1.57 | PASS |
| BLK | 2024-25 | 21 | 33 | 1.57 | PASS |
| BLK | 2025-26 | 71 | 114 | 1.61 | PASS |
| PTS | 2023-24 | 21 | 33 | 1.57 | PASS |
| PTS | 2024-25 | 21 | 33 | 1.57 | PASS |
| PTS | 2025-26 | 71 | 114 | 1.61 | PASS |
| REB | 2023-24 | 21 | 33 | 1.57 | PASS |
| REB | 2024-25 | 21 | 33 | 1.57 | PASS |
| REB | 2025-26 | 71 | 114 | 1.61 | PASS |

## Aggregate verdict

See [aggregate_verdict.md](aggregate_verdict.md) for the 3 x 3 disposition table and aggregate per-hypothesis verdicts.

## Paper integration

Per the pre-reg section 4 published-narrative framework, the result drives a specific cross-league paper revision. The adjudicated arm is reported alongside the metadata arm in cross-league paper section 5.4 (NBA contribution to the 11/11 BLK x Center claim) and section 5.4.1 (REB walk-back). The metadata-bucket numbers above must replicate the existing section 5.5 / 5.4 numbers exactly; the adjudicated-bucket numbers are the new headline.
