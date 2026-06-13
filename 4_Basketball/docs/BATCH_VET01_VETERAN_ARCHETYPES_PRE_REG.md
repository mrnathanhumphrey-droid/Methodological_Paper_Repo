# Batch VET01 — NBA Veteran Playstyle Archetypes (Stage 1 ported BACK to NBA)

**Locked 2026-06-10 BEFORE compute.** The NBA Stage 1 pattern was ported OUT to
NFL (RB/WR/TE/QB), NHL (F/D/G), Golf (bomber/putter-carried). Never back-ported
to NBA veterans — only rookies labeled. This batch closes that loop. Enables
DARKO-style benchmark and per-archetype veteran aging (currently only REB).

## Substrate

- `data/parquet/ctg_players.parquet`: 5,958 (player, season) rows, 2014-2025
  (12 seasons, 1,292 unique players)
- `data/parquet/player_metadata.parquet` (1,068 players × birth_date + position)
- All ctg features pre-computed: usage, shooting splits (rim/short/mid/three),
  AST%, TOV%, BLK%, STL/play, oreb/dreb_fg, true-shooting

## Cohort

```
Filter:    MPG >= 15 per season AND >= 3 qualifying seasons
Aggregate: minutes-weighted career means
Expected n: 400-500 veterans
```

This filter excludes call-ups, deep-bench guys, and short-careers. We want
players whose veteran archetype is observable across multiple seasons.

## Feature family (12 features)

```
USAGE / ROLE:
  usage                (offensive load)
  mpg                  (rotation tier)

SHOOTING PROFILE:
  three_fg             (3PA per FGA = three-rate)
  three_perc           (3pt accuracy)
  rim_fg               (rim-attempt share)
  rim_perc             (rim conversion)
  ft_perc              (free-throw skill)
  efg_perc             (overall shooting efficiency)

PLAYMAKING:
  ast_perc             (assist creation)
  tov_perc             (turnover rate)

DEFENSE / REBOUND:
  blk_perc             (rim protection)
  stl_per_play         (perimeter defense)
  oreb_fg              (offensive rebounding rate)
  dreb_fg              (defensive rebounding rate)
```

## Method

1. Build per-veteran career feature matrix (minutes-weighted).
2. Join position from player_metadata for descriptive label only (not feature).
3. Z-score within cohort.
4. KMeans k=4, 5, 6, 7, 8 — pick by silhouette score.
5. ANOVA per feature + named-player face validity.

## Locked gates

```
G1 silhouette >= 0.12 at chosen k
G2 ANOVA F max >= 30
G3 ANOVA p min <= 1e-15 (large n)
G4 min cluster size >= 20
G5 face validity — at least one cluster looks like "shooting big" (high three_fg
   AND high three_perc AND high blk_perc) AND one looks like "primary
   creator" (high usage + high ast_perc) AND one looks like "3-and-D wing"
   (high three_fg + low usage + decent stl)
G6 named-star sanity — Curry / LeBron / Giannis / Jokic / Embiid / Durant /
   Tatum / Harden / Doncic / Kawhi each land in a face-valid cluster
   (>= 7 of 10 in the cluster a fan would expect)
```

## Decision

```
5-6 / 6 → SHIP_CLEAN
3-4 / 6 → SHIP_CAVEAT
0-2 / 6 → WALK_BACK
```

## What this is NOT

- NOT a projection model (descriptive labels only)
- NOT season-specific — career-aggregate features (a player's "style")
- NOT a rookie pattern (rookies use Y1 stats + combine; veterans use multi-season)
- The NBA RMD-SRC re-axis was off_feast / def_feast (spatial coverage). This
  is DIFFERENT — playstyle-cluster, not spatial.

## What this UNLOCKS

```
- DARKO-style impact benchmark (needs veteran style labels)
- Per-archetype veteran aging arc (mirror NHL N02; currently only REB has been
  done because that's spatial, not playstyle)
- Trade-impact analysis (replace lost wing-shooter with another wing-shooter)
- Free-agency draft drafts (identify veteran-archetype-needs per team)
```

## Files (planned)

```
scripts/
  veteran_archetypes_v01.py
data/parquet/
  veteran_archetypes.parquet
results/
  batch_vet01_verdict.json
docs/
  BATCH_VET01_VETERAN_ARCHETYPES_VERDICTS.md
```
