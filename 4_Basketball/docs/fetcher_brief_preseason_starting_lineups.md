# Code Brief: Preseason Starting Lineups + Box Score Tracking

## Why this exists

Once preseason exhibition games begin (typically October 1-22), the **starting lineup is a structured fact**, not an analyst's projection. No quote parsing needed — the team announces it, NBA.com records it, the box score reflects it. This is the cleanest, lowest-noise signal we can ingest because it's primary-source, not analyst-curated.

The NBA projection engine at `D:\NBA Projections` will use preseason starting lineups + minutes as:
1. The strongest single MPG anchor before the regular season starts (3-5 games of actual coach decisions per player)
2. Confirmation signal cross-checking depth charts (where coach actually played the listed starter, depth chart was correct)
3. Backtest validation for our role-state model on historical seasons (2019-20 through 2024-25)

**Independence note**: this is purely structural primary data — no target leakage concern. Coach starts player X = factual rotation decision, not a projection of stats. Safe to use as input feature.

## Source

`nba_api` Python library (already in our venv).

### Endpoints to use

1. **`LeagueGameLog(season_type_nullable='Pre Season', season=...)`** — returns all preseason game IDs for the season

2. **`BoxScoreTraditionalV2(game_id=...)`** — for each preseason game, returns player box stats including `MIN` and `START_POSITION` field (which marks "F", "C", "G" for starters, NULL for bench)

3. **`BoxScoreSummaryV2(game_id=...)`** — game header info, helpful for cross-checking team_abbr and game_date

### Backfill scope

Preseason 2019-20 through 2025-26 (7 seasons), then ongoing for 26-27 forward.

Note: 2020-21 had no traditional preseason (COVID-shortened, season started Dec 22, 2020). 2019-20 had standard preseason. 2021-22 onward standard.

## What to extract

### A. Preseason game box scores (per-player, per-game)

`data/parquet/preseason_box_scores.parquet`:

```
game_id             string
game_date           date
season              string  -- "2023-24" etc
season_type         string  -- "Pre Season"
nba_api_id          int64
player_name         string
team_abbr           string
team_id             int64
opp_team_abbr       string
is_home             bool
minutes             float
start_position      string?  -- "G" / "F" / "C" / NULL if bench
is_starter          bool     -- derived: start_position is not NULL
FGM, FGA, FG3M, FG3A, FTM, FTA  int
OREB, DREB, REB, AST, STL, BLK, TOV, PF  int
PTS                 int
plus_minus          float
fetched_at_utc      timestamp
```

### B. Per-player preseason aggregates

After raw box scores land, derive `data/parquet/preseason_player_aggregates.parquet`:

```
nba_api_id          int64
season              string
team_abbr           string  -- last team played for in preseason
gp                  int
gs                  int     -- games started
total_min           float
mpg                 float
mpg_when_starting   float?
mpg_when_bench      float?
n_starts            int
n_bench_apps        int
PTS_per_game        float
REB_per_game        float
AST_per_game        float
STL_per_game        float
BLK_per_game        float
TOV_per_game        float
FG3M_per_game       float
all_per36 versions  float
last_game_date      date
```

This aggregate is the input to the v6 MPG model — gives us preseason MPG and starter-rate per player to blend with career-weighted MPG.

### C. Team starting lineups (5-man combinations)

For each preseason game, capture the full starting 5 as a record:

`data/parquet/preseason_starting_fives.parquet`:

```
game_id             string
game_date           date
season              string
team_abbr           string
starter_pg_id       int64?  -- the player listed at start_position="G" first
starter_sg_id       int64?  -- (NBA.com doesn't strictly distinguish PG/SG via start_position)
starter_sf_id       int64?
starter_pf_id       int64?
starter_c_id        int64?
all_starter_ids     array<int64>  -- canonical: 5 player IDs in starting lineup
fetched_at_utc      timestamp
```

For position assignment within the starting 5, use player_metadata's listed positions to map G/F/C from start_position to specific 1-5 slots. If ambiguous (two listed Gs, etc.), use last-known team depth chart from `depth_charts_history.parquet` if available.

## Volume estimate

Per season: ~30 teams × ~5 preseason games each × ~20 players appearing = ~3,000 rows for box scores. ~150 unique starting-five records.

7 seasons backfill: ~21,000 box score rows + ~1,000 starting-five records. Tiny.

## Concurrency / parallelism rules

`nba_api` calls hit stats.nba.com which has surprisingly aggressive rate limiting. Use these rules:

- **Game ID enumeration** (`LeagueGameLog`): single call per season, no parallelization needed. ~10 seconds total for 7 seasons.

- **Box score fetches** (`BoxScoreTraditionalV2` × N games): **MAX 1 worker, 1 req/2sec**. Stats.nba.com IP-bans aggressively at higher rates (we've seen this on previous endpoints). Per season ~150 games, so ~5 minutes per season; backfill 7 seasons ~35 minutes.

- **Box score summary** (`BoxScoreSummaryV2`): only fetch if `BoxScoreTraditionalV2` doesn't have what we need. Same 1 worker / 1 req/2sec rule.

- **Aggregate computation**: pure pandas, no API calls, runs locally in seconds.

**Key gotcha**: stats.nba.com sometimes returns empty/null bodies on rate-throttle without a proper 429 response. Detect via "empty resultSet" check, treat as throttle, back off 60 seconds.

**No parallelism across `nba_api` endpoints** — they all share IP rate limits at stats.nba.com. One worker total.

**If banned**: stop everything for 1+ hours. Resume from last successfully-fetched game_id. Existing fetcher cache means no duplicate work. Banned-IP recovery is automatic at stats.nba.com (no permanent bans, just sliding-window throttles).

## Validation

After each backfill:

1. **2023-24 preseason Wembanyama**: 4-5 game appearances on SAS, average mpg in 25-30 range, marked as starter (is_starter=True) in most.

2. **2023-24 preseason Embiid**: 1-2 game appearances on PHI maximum (he typically rests preseason). is_starter flag should be True when he plays.

3. **2023-24 preseason Damian Lillard MIL**: 3-5 games on MIL (post-trade), mpg ~25-30, starter=True (he was Day-1 PG).

4. **Coverage check**: each season should have ~150 unique games × ~10 players each = ~1500 unique (player, game) pairs minimum. Significantly fewer = backfill missed games.

5. **Starting lineup coverage**: each season should have ~150 starting_fives records (one per game). If a team played 5 preseason games, we should have 5 starting-fives records for them.

## Anti-patterns

- Don't fetch playoff or summer league games via this fetcher (different endpoint setups)
- Don't try to fetch advanced stats (BoxScoreAdvancedV2) — out of scope, sample size too small in preseason
- Don't fetch shot charts for preseason games (data quality varies, low value)
- Don't aggregate across teams for traded players — preseason is stable (no mid-preseason trades typically), but if a player did play for two teams in preseason (rare), keep both team_abbr rows separate
- Don't compute fantasy points or composite scores — keep raw

## CLI structure

```
python -m fetchers.preseason_box_scores backfill --start 2019 --end 2025
python -m fetchers.preseason_box_scores fetch --season 2025-26  # current season only
python -m fetchers.preseason_box_scores aggregate                # rebuild player aggregates
python -m fetchers.preseason_box_scores starting_fives           # rebuild starting-fives view
python -m fetchers.preseason_box_scores validate
```

Idempotent: re-running detects existing game_ids, skips. Use `--force` to re-fetch.

## Auth

None required — `nba_api` is unauthenticated, calls public stats.nba.com endpoints.

## Estimate

Build effort: 4-6 hours total. The endpoints are well-documented in nba_api, the schema is straightforward. Most of the time is on rate-limit-aware throttling and the aggregation pass.

Backfill runtime: ~35 minutes for 7 seasons of box scores + 5 minutes for aggregates + starting_fives derivation.

Free, no cost.

## Reporting

After each backfill:
- Games fetched per season
- Players covered per season
- Spot-check sample (5 random players, their preseason games)
- Any throttle events / retries
- Coverage gaps if any season had unusually few games

## What this unlocks downstream

- **Preseason MPG aggregate as v6 feature**: weighted ~3 equivalent-games in the live_update Bayesian blend, kicks in mid-October before regular season
- **Cross-validation against depth charts**: player listed as starter in depth chart but never started a preseason game = depth chart wrong, or coach experimenting
- **Cross-validation against rotation reports**: "expected starter at SF" + actually started SF in preseason = high confidence
- **Backtest signal strength**: did 2023-24 preseason MPG predict actual 23-24 regular season MPG better than career-weighted alone?
