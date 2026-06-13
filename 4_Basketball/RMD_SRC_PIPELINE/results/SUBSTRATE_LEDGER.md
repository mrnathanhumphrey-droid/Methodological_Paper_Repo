# NBA Full-Pipeline RMD-SRC — Substrate Ledger

Locked under three commit-SHAs:
- **v1.0 pre-reg:** `db0ed9a899c28691183cd5b640f460c10f3c2a75`
- **v1.1 amendment (MPG-tier parallel arm):** `4d0602df832d5a45402a212acf48b19a4dfee070`
- **v1.2 amendment (position adjudication):** `1bfdb4c0dfa2b3754f67e9c2f91b2ab26fa01866`

## Path A — locked-spec compliance
Steps 0-6 + F1-F4 + comparative arm executed under the locked spec with no rescue. Step 3's Hartigan-dip-on-raw-values check over-fires at 100% across all 4 arms — a substrate-shape finding mirroring Migration's v1.4 diagnosis. Step 4 vacuous (empty input). F2 carried by Stationary count (Edge excluded per section 3.2). F1, F4, Step 5, and comparative arm computed normally.

## Headline by arm

| Arm | K | F1 fires? | F2 clean | F2 fires? | F4 kappa (mean) | F4 fires? | Step 5 mean r | Comp PASS / TIE / LOSE |
|---|---|---|---|---|---|---|---|---|
| `usg` | 19 | N | 32/53 = 60.4% | N | +0.015 | Y | +0.796 | 0 / 76 / 0 |
| `mpg` | 21 | N | 34/49 = 69.4% | N | -0.042 | Y | +0.722 | 0 / 84 / 0 |
| `usg_adj` | 21 | N | 33/59 = 55.9% | N | +0.022 | Y | +0.737 | 0 / 84 / 0 |
| `mpg_adj` | 25 | N | 30/58 = 51.7% | N | -0.024 | Y | +0.693 | 0 / 100 / 0 |

## F1 detail — R^2 of additive linear model per observable

| Arm | PTS_per36 | REB_per36 | AST_per36 | BLK_per36 |
|---|---|---|---|---|
| `usg` | 0.159 | 0.212 | 0.152 | 0.085 |
| `mpg` | 0.096 | 0.212 | 0.107 | 0.084 |
| `usg_adj` | 0.160 | 0.242 | 0.159 | 0.097 |
| `mpg_adj` | 0.099 | 0.241 | 0.118 | 0.096 |

## F4 detail — Cohen kappa per (arm, observable)

| Arm | PTS_per36 | REB_per36 | AST_per36 | BLK_per36 |
|---|---|---|---|---|
| `usg` | +0.057 | -0.042 | +0.073 | -0.027 |
| `mpg` | -0.149 | -0.083 | +0.008 | +0.058 |
| `usg_adj` | +0.074 | +0.027 | +0.097 | -0.111 |
| `mpg_adj` | -0.127 | -0.025 | +0.056 | +0.002 |

## Cross-arm regime kappa (per-player-season per observable)

### PTS_per36

| | usg | mpg | usg_adj | mpg_adj |
|---|---|---|---|---|
| `usg` | 1.000 | +0.246 | +0.567 | +0.186 |
| `mpg` | +0.246 | 1.000 | +0.217 | +0.002 |
| `usg_adj` | +0.567 | +0.217 | 1.000 | +0.188 |
| `mpg_adj` | +0.186 | +0.002 | +0.188 | 1.000 |

### REB_per36

| | usg | mpg | usg_adj | mpg_adj |
|---|---|---|---|---|
| `usg` | 1.000 | +0.304 | +0.344 | +0.070 |
| `mpg` | +0.304 | 1.000 | -0.035 | +0.246 |
| `usg_adj` | +0.344 | -0.035 | 1.000 | +0.151 |
| `mpg_adj` | +0.070 | +0.246 | +0.151 | 1.000 |

### AST_per36

| | usg | mpg | usg_adj | mpg_adj |
|---|---|---|---|---|
| `usg` | 1.000 | +0.395 | +0.383 | +0.387 |
| `mpg` | +0.395 | 1.000 | +0.311 | +0.318 |
| `usg_adj` | +0.383 | +0.311 | 1.000 | +0.380 |
| `mpg_adj` | +0.387 | +0.318 | +0.380 | 1.000 |

### BLK_per36

| | usg | mpg | usg_adj | mpg_adj |
|---|---|---|---|---|
| `usg` | 1.000 | +0.240 | +0.618 | +0.107 |
| `mpg` | +0.240 | 1.000 | +0.198 | +0.299 |
| `usg_adj` | +0.618 | +0.198 | 1.000 | +0.267 |
| `mpg_adj` | +0.107 | +0.299 | +0.267 | 1.000 |

## Step 6 mechanism inference

Per pre-reg section 7 prospective tier: the BLK x Center concentration mechanism was committed ex ante. Under Path A, Step 3 dip over-fires on every cell, so no non-Stationary cell is response-validated. The prospective claim is therefore **not falsified but not confirmed** at the response-validation layer. Retrospective and post-hoc tier mechanisms: none named (no Step 4 sub-partitions to anchor them).

## Path B (v1.3 dip-on-residuals) results

Locked at SHA `f3ede6ccebc29009b666146542465693f6fa721c`. Check D (Hartigan dip on r_pg = y_pg - mu_cell) computed per (cell, observable) per arm. Path A reports above are NOT modified. Original Step 3 Check A continues firing as documented.

### Headline by arm

| Arm | Check D pass | Frac pass | Localization disposition | residual_clean | Path B F2 | F2 fires? | Step 4 eligible | Comp PASS / TIE / LOSE |
|---|---|---|---|---|---|---|---|---|
| `usg` | 0/76 | 0.0% | substrate-level multimodality | 0 | 32/53 = 60.4% | N | 0 | 0 / 76 / 0 |
| `mpg` | 0/84 | 0.0% | substrate-level multimodality | 0 | 34/49 = 69.4% | N | 0 | 0 / 84 / 0 |
| `usg_adj` | 0/84 | 0.0% | substrate-level multimodality | 0 | 33/59 = 55.9% | N | 0 | 0 / 84 / 0 |
| `mpg_adj` | 0/100 | 0.0% | substrate-level multimodality | 0 | 30/58 = 51.7% | N | 0 | 0 / 100 / 0 |

### Aggregate Path B disposition
Mean Frac(Check D PASS) across 4 arms: **0.0%** -> **substrate-level multimodality**.

