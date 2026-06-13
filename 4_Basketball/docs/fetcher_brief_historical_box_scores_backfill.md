# Code Brief: Historical Box-Score Backfill — 2014-15 through 2018-19

## Why this exists

The NBA projection engine at `D:\NBA Projections` currently has per-game box scores for seasons 2019-20 through 2024-25 only (`data/parquet/historical_box_scores.parquet`, ~150K rows, 6 seasons). The 11-season hierarchical Bayesian residual-class offset model needs more history. Backfilling 5 additional seasons (2014-15, 2015-16, 2016-17, 2017-18, 2018-19) unlocks:

1. Three additional usable test-season audits (17-18, 18-19, 19-20 each gain a 3-prior-season training set).
2. Cross-season validation across 8 seasons instead of 2, killing the "1-2 season fluke" failure mode that has invalidated multiple offset proposals already.
3. The `hierarchical_multi_year_offsets.stan` shrinkage model crosses its `n_years >= 3` threshold for meaningful between-year pooling.

All adjacent tables (coaching changes, transactions, draft data, player metadata) already cover the older era. Box scores are the only gap.

## Source

`nba_api` Python library (https://github.com/swar/nba_api). Endpoints used:

- **`PlayerGameLog`** — per-(player, season, season-type) game log. The existing implementation at `ingestion/historical_box_scores.py` already wraps this. Returns one row per game played by the player, with all box-score columns we need.
- **`LeagueDashPlayerStats`** OR **`CommonAllPlayers`** — used only once per season to enumerate which `nba_api_id`s appeared in that season. We need this because we don't already have the active-player set for older seasons.

No auth, no API key, no cost. Endpoint is public on `stats.nba.com`. Standard `nba_api` client library handles all the headers / cookies the site requires.

## Reuse the existing pipeline

**Do not reimplement.** The repo already has a clean per-player-per-season fetcher with caching, retry, and throttling: `ingestion/historical_box_scores.py`. It's been used to build the existing 6-season parquet.

The function signature:

```python
from ingestion.historical_box_scores import build_historical_box_scores

build_historical_box_scores(
    player_ids=[...],                       # list of nba_api_ids active in target seasons
    seasons=['2014-15', '2015-16', '2016-17', '2017-18', '2018-19'],
    season_types=('Regular Season',),       # playoffs not used downstream
    seasons_per_player={pid: [active_seasons_for_pid]},  # optional, but saves throttle time
)
```

**Caching is keyed at (player, season, season_type) granularity** — already enforced by `ingestion/cache.py` + `ingestion/nba_api_wrapper.py`. Re-running is idempotent: a player whose 2015-16 log was already fetched won't re-hit the API.

**Throttling**: `NBA_API_DELAY_S=0.6` by default (set in `nba_api_wrapper.py`). Sustained ~1.5 req/sec. Don't override lower — `stats.nba.com` IP-blacklists on bursts >10 req/sec for sustained periods.

## What needs new code

Just one wrapper script: a player-discovery + driver that calls `build_historical_box_scores` with the right inputs. Suggested name: `scripts/backfill_older_box_scores.py`.

Pseudocode:

```python
from nba_api.stats.endpoints import LeagueDashPlayerStats
from ingestion.historical_box_scores import build_historical_box_scores, load_historical_box_scores
from ingestion.nba_api_wrapper import _throttle  # or wrap your own

TARGET_SEASONS = ['2014-15', '2015-16', '2016-17', '2017-18', '2018-19']

# Step 1: enumerate active players per season
player_seasons = {}  # nba_api_id -> [seasons]
for season in TARGET_SEASONS:
    _throttle()
    df = LeagueDashPlayerStats(season=season,
                                season_type_all_star='Regular Season').get_data_frames()[0]
    for pid in df['PLAYER_ID'].unique():
        player_seasons.setdefault(int(pid), []).append(season)

# Step 2: fetch box scores
player_ids = list(player_seasons.keys())
result = build_historical_box_scores(
    player_ids=player_ids,
    seasons=TARGET_SEASONS,
    seasons_per_player=player_seasons,
)

# Step 3: merge with existing parquet (build_historical_box_scores OVERWRITES,
# so manually concat instead)
existing = load_historical_box_scores()
combined = pd.concat([existing, result], ignore_index=True)
combined = combined.drop_duplicates(subset=['game_id', 'nba_api_id'], keep='first')
combined.to_parquet('data/parquet/historical_box_scores.parquet', index=False)
```

**Critical**: `build_historical_box_scores` writes to the canonical parquet path and overwrites. The driver script must concat with the existing parquet AFTER the fetch returns the new frame, not before. Either:
- Pass `seasons` as the 5 new ones only and concat-merge, OR
- Read existing into memory first, blow away, refetch all 11 seasons, write back. (Not recommended — wastes hours of API traffic.)

The first approach is the right one.

## Schema target — must match exactly

26 columns, in this order:

| Column | dtype | Notes |
|---|---|---|
| `nba_api_id` | int64 | Player ID from nba_api |
| `game_id` | object (str) | nba_api game ID, e.g. `'0021400001'` |
| `game_date` | object (date) | Python `date`, NOT `datetime`. Parse from `'%b %d, %Y'` format. |
| `matchup` | object (str) | e.g. `'LAL vs. GSW'` or `'LAL @ GSW'` |
| `minutes` | int64 | nba_api returns this as int already; some older seasons may need coercion |
| `FGM`, `FGA`, `FG3M`, `FG3A`, `FTM`, `FTA` | int64 | Shooting counts |
| `OREB`, `DREB`, `REB` | int64 | Rebound splits |
| `AST`, `STL`, `BLK`, `TOV`, `PF` | int64 | Other counting stats |
| `PTS` | int64 | Points |
| `plus_minus` | int64 | +/- |
| `is_home` | bool | True if `'@'` NOT in matchup |
| `team_abbr` | object (str) | First 3 chars of matchup (e.g. `'LAL'`) |
| `win` | bool | True if WL == 'W' |
| `season` | object (str) | e.g. `'2014-15'` |
| `season_type` | object (str) | `'Regular Season'` |

The existing `_normalize_log` function in `ingestion/historical_box_scores.py` produces exactly this schema. Don't deviate.

## Volume estimate

Each season has ~22K-26K player-game regular-season rows (varies with roster turnover and 10-day signings). 5 seasons × ~25K = **~125,000 new rows**.

Active players per season range 540-620. Total unique players across 5 seasons: ~900-1100 (significant overlap; ~500 played all 5).

Total fetches: ~2,500 (player, season) combos. At 0.6s throttle, ideal wall time = **~25 minutes**. Realistic with retry overhead and occasional slow endpoints: **1.5-2 hours**.

## Validation criteria

After backfill completes, run these spot-checks:

1. **Row count per season** — target 22,000-26,500 per season. Significant under-count signals missing players or failed seasons.

```python
df = pd.read_parquet('data/parquet/historical_box_scores.parquet')
print(df.groupby('season').size())
```

2. **Known-player game counts** — pick 5 stars per season and verify game count is in expected range:
   - LeBron James 2014-15: 69 games
   - Stephen Curry 2015-16: 79 games (MVP unanimous, +SBs)
   - Russell Westbrook 2016-17: 81 games
   - James Harden 2017-18: 72 games
   - Giannis Antetokounmpo 2018-19: 72 games

3. **No duplicate (game_id, nba_api_id) pairs** — should be exactly one row per player-game:

```python
dup = df.duplicated(subset=['game_id', 'nba_api_id']).sum()
assert dup == 0, f"{dup} duplicate player-game rows"
```

4. **Schema parity** — column list and dtypes must match the existing parquet pre-backfill.

5. **Sample 30 random rows** — sanity-check that fields look right (no nulls in PTS/REB/AST, dates in expected range).

## Player metadata gap (secondary, lower priority)

`player_metadata_enriched.parquet` currently has 1068 players. The older-season backfill may surface ~50-150 additional `nba_api_id`s not already in metadata (career-end-before-2019 players). Without metadata, those rows can't be assigned `position`, `birth_date`, `draft_year`, etc. — which means they can't be class-bucketed for the residual-offset analysis.

**Solution**: after box-score backfill, run a metadata-fill pass:

```python
from nba_api.stats.endpoints import CommonPlayerInfo

box = pd.read_parquet('data/parquet/historical_box_scores.parquet')
meta = pd.read_parquet('data/parquet/player_metadata_enriched.parquet')
new_pids = set(box['nba_api_id'].unique()) - set(meta['nba_api_id'].unique())

new_rows = []
for pid in new_pids:
    _throttle()
    info = CommonPlayerInfo(player_id=pid).get_data_frames()[0]
    new_rows.append({
        'nba_api_id': int(pid),
        'name': info.iloc[0]['DISPLAY_FIRST_LAST'],
        'birth_date': info.iloc[0]['BIRTHDATE'],
        'height_inches': parse_height(info.iloc[0]['HEIGHT']),
        'weight_lbs': info.iloc[0]['WEIGHT'],
        'position': info.iloc[0]['POSITION'],
        'draft_year': info.iloc[0]['DRAFT_YEAR'],
        'draft_pick': info.iloc[0]['DRAFT_NUMBER'],
    })
extra = pd.DataFrame(new_rows)
combined_meta = pd.concat([meta, extra], ignore_index=True).drop_duplicates(
    subset=['nba_api_id'], keep='first')
combined_meta.to_parquet('data/parquet/player_metadata_enriched.parquet', index=False)
```

Volume: ~50-150 calls = ~1-2 minutes added wall time.

## Anti-patterns

- **Don't override `NBA_API_DELAY_S` lower than 0.6.** IP blacklist takes 24+ hours to lift.
- **Don't fetch playoff data.** Downstream code uses regular-season only.
- **Don't refetch the existing 6 seasons.** Cache should already cover them; even so, only fetch the 5 new ones.
- **Don't try the `LeagueGameLog` endpoint as a single bulk fetch.** It returns team-game rows, not player-game rows; you'd then need per-game `BoxScoreTraditionalV2` calls (~1230 games/season × 5 = 6,150 extra fetches just for box-score expansion). The per-player-per-season approach has fewer requests AND already has cache hits.
- **Don't skip the `seasons_per_player` argument.** A player who only played 14-15 + 15-16 doesn't need a 16-17/17-18/18-19 fetch attempt; passing the active-seasons map cuts the request count nearly in half.
- **Don't write to the parquet incrementally during the fetch loop.** Build in memory, write once at the end. Atomic writes prevent half-finished data after a crash.

## CLI structure (suggested)

```bash
python scripts/backfill_older_box_scores.py --discover-players
# Enumerates active player_ids per target season, writes a staging file
# data/parquet/_staging_older_player_seasons.parquet (or similar)

python scripts/backfill_older_box_scores.py --fetch
# Reads staging file, runs build_historical_box_scores, writes a staging
# parquet data/parquet/_staging_older_box_scores.parquet

python scripts/backfill_older_box_scores.py --merge
# Concats staging with existing historical_box_scores.parquet, dedups,
# writes final parquet. Backs up the existing one to a timestamped copy first.

python scripts/backfill_older_box_scores.py --validate
# Runs the validation checks listed above. Exits non-zero on failure.

python scripts/backfill_older_box_scores.py --metadata-fill
# Optional secondary pass for newly-discovered nba_api_ids missing from
# player_metadata_enriched.parquet.
```

Idempotent throughout. Re-running `--fetch` should hit cache for already-fetched (player, season) pairs and finish in seconds.

## Reporting on completion

Required:
- Per-season row counts in the new parquet (compare with existing 19-20 baselines)
- Total new rows added
- Total unique nba_api_ids added across the 5 seasons
- Number of nba_api_ids missing from `player_metadata_enriched.parquet` post-fetch (and whether `--metadata-fill` was run)
- Any failed (player, season) pairs with error reason
- Sample of 5 random rows for sanity check
- Wall time + cache-hit rate

## Estimate

- Build effort: 1-2 hours of clean implementation (fetcher driver script + validation harness; backbone already exists)
- Backfill runtime: 1.5-2 hours fetch + 1-2 minutes metadata fill
- Total elapsed: ~2-4 hours from start to validated parquet

## Output paths

- `data/parquet/historical_box_scores.parquet` (extended in-place; existing data preserved)
- `data/parquet/player_metadata_enriched.parquet` (extended if `--metadata-fill` run)
- Backup of pre-backfill state: `data/parquet/historical_box_scores.parquet.backup_<YYYYMMDD>` (created automatically by `--merge` step)

## Downstream impact (informational, not required for fetcher)

After this backfill ships, two things become possible:

1. **`scripts/fire_multi_year_audits.sh`** can be extended: TRAIN_FOR map currently has empty/partial entries for 19-20, 20-21, 21-22 because they need older box scores. After backfill, those become full 3-prior-season trains, unlocking 24 additional v4-lite tq_g audits.

2. **`scripts/hierarchical_multi_year_runner.py --fit`** becomes meaningful: with 8 seasons of audits per stat (vs current 2), the Stan shrinkage model produces non-prior-dominated posteriors.

These are NOT the fetcher's responsibility — they fire after the data lands.
