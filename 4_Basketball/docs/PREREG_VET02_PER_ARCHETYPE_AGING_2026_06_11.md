# PRE-REG: NBA Stage 1.5 — VET01 Per-Archetype Aging (Batch VET02)

**Locked**: 2026-06-11
**Substrate**: `D:/NBA Projections/data/parquet/veteran_archetypes.parquet` (573 vets × 7 clusters) × `D:/NBA Projections/data/parquet/ctg_players.parquet` (5958 player-seasons, age 18.85-42.76, seasons 2014-2025)
**Pattern anchor**: NHL N02 per-archetype aging (signature-metric-only aging within archetype)

## Why this thread

VET01 shipped tonight (k=7 BIG-FRAME / PERIMETER / RIM_BIG / etc). Stage 1.5 is the per-archetype aging cross-product — required to claim DARKO-competitive per-style age curves. Currently NBA has only REB aging (spatial, style-agnostic). NHL ran N02 to ship per-archetype peak ages; NBA needs the same.

## H1 (load-bearing)

Within each VET01 cluster, the signature metric (the dominant z-feature from VET01) shows a within-player quadratic aging curve whose peak age differs by ≥ 2.0 years from the pooled-across-clusters peak.

## H2 (companion)

BIG-FRAME CREATOR (C4 = LeBron/Giannis/Jokic) peaks LATER on craft (ast_perc) than PERIMETER CREATOR (C2 = Curry/Tatum/Harden) by ≥ 2.0 years — testing the "skill endures, athleticism fades" cross-sport thesis on NBA.

## Cohort

- Within-player demeaned per metric, per archetype
- Per-archetype cohort floors: ≥ 30 player-seasons (per VET01 ctg JOIN: min cluster 281 ps in C4, max 1148 in C1 — all pass)
- Age range 19-40 (drop age < 19 or > 40 for stability)
- Season ≥ 2014 (locked from VET01 substrate)

## Signature metrics per cluster (LOCKED before fit)

Mapped from VET01 dominant-z findings (memory entry):

| Cluster | Label | Signature metrics |
|---|---|---|
| C0 | ENERGY POST BIG | oreb_fg, blk_perc, rim_fg |
| C1 | 3-AND-D MOVEMENT | three_fg, three_perc, stl_per_play |
| C2 | PERIMETER CREATOR | usage, three_fg, ast_perc |
| C3 | MIXED UTILITY WING | efg_perc, three_fg |
| C4 | BIG-FRAME CREATOR | usage, ast_perc, rim_fg, blk_perc |
| C5 | BENCH PLAYMAKER | ast_perc, ast_usage_ratio |
| C6 | RIM BIG/SHOT-BLOCKER | blk_perc, rim_fg, oreb_fg |

## Model spec (LOCKED)

For each (cluster, metric) pair:
1. Subset ctg JOIN vet to cluster, metric not null, MPG ≥ 15, season ≥ 2014
2. Within-player demean: `metric_demean = metric - mean(metric | p_id)`
3. Fit: `metric_demean = b1 * (age - 28) + b2 * (age - 28)^2 + ε`
4. Peak age: 28 - b1 / (2 * b2) if b2 < 0 else "no peak (monotonic)" or "trough (b2>0)"
5. Report b1, b2, peak_age, R², n, p_b2

## Gates (6 total)

1. **G1**: Per-cluster, ≥1 signature metric has b2 < 0 (parabola DOWN = real peak), p_b2 < 0.05
2. **G2**: Cross-cluster peak-age range on a shared metric (usage OR ast_perc, both signatures of C2 + C4) ≥ 2.0 years
3. **G3**: Per-cluster signature-metric fit R² > 0.005 (within-player demean signal-to-noise floor — same as NHL N02 floor)
4. **G4**: BIG-FRAME CREATOR (C4) peak age on `ast_perc` LATER than PERIMETER CREATOR (C2) peak by ≥ 2.0 years (H2 directional)
5. **G5**: RIM-related metrics (rim_fg, blk_perc) peak EARLIER than craft metrics (ast_perc) by ≥ 2.0 years within C0/C4/C6
6. **G6**: At least 5 of 7 clusters produce ≥1 sig-metric fit that passes G3

SHIP_CLEAN = 6/6, SHIP_CAVEAT = 4-5/6, DISCONFIRMED = ≤3/6

## Anti-cheat

- **NO metric swap.** Signature metrics PER CLUSTER LOCKED above.
- **NO age-window tuning.** 19-40 LOCKED.
- **NO MPG threshold change.** 15 LOCKED.
- **NO cluster merging** if a single cluster fails.
- **NO post-hoc peak-age direction flip** in H2. If C2 peaks later than C4 on ast_perc, H2 disconfirms.

## Outputs

- `D:/NBA Projections/data/parquet/per_archetype_aging_curves_vet02.parquet` (one row per (cluster × metric) fit)
- Verdict: `D:/NBA Projections/docs/VET02_PER_ARCHETYPE_AGING_VERDICT_2026_06_11.md`

## Cross-refs

- VET01: `D:/NBA Projections/scripts/veteran_archetypes_v01.py`
- NHL N02 pattern (same cross-product): memory entry `project_nhl_batch_n02_per_archetype_aging_2026_06_10.md`
- NBA REB aging (spatial style-agnostic, predecessor): `D:/NBA Projections/data/parquet/aging_curve_REB.parquet`
