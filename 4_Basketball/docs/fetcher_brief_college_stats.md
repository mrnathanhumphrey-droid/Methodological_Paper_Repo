# Code Brief: NCAA Division I College Stats — Rookie Career Prior

## Why this exists

Our v6 NBA projection engine handles veterans well (career-blend + live update). Rookies fail because they have no NBA career data when we project them at preseason. The fix: **use NCAA per-40 stats as their "career prior"** — same architecture as veteran career-blend, just different data source.

Per the rookie audit, we have 843 rookies who debuted 2014-2024. Most went to NCAA D1; a subset went international or G-League (covered in separate brief). This fetch covers the NCAA pathway.

## Source

**Primary**: Sports-Reference College Basketball — `https://www.sports-reference.com/cbb/`

URL patterns:
- Per-player: `https://www.sports-reference.com/cbb/players/{player-slug}-1.html`
- School roster page: `https://www.sports-reference.com/cbb/schools/{school}/men/{year}.html`
- Conference / season aggregate pages
- Player names mostly follow `firstname-lastname-1` pattern; multiple players with same name get -2, -3 suffixes

**Secondary** (for cross-reference): `https://stats.ncaa.org/players/` (NCAA's own stats site)

## What to extract

For each player who appears in our `nba_draft_data.parquet` with `pre_nba_team_type=ncaa`, plus all NCAA D1 players who appear in our `nba_career_season_totals_rs.parquet` rookie cohort (2014-2024 debuts):

```
nba_api_id          int64?  -- resolved post-fetch via name + draft_year + school cross-ref
player_name_raw     string
school              string  -- "Duke" / "Kentucky" / etc.
school_conference   string  -- "ACC" / "SEC" / "Big Ten" / etc.
ncaa_season         string  -- "2022-23" or just year "2023"
class_year          string  -- "FR" / "SO" / "JR" / "SR" / "GR"
gp                  int
gs                  int
min_total           int
mpg                 float
PTS, REB, AST, STL, BLK, TOV, FGM, FGA, FG3M, FG3A, FTM, FTA, OREB, DREB, PF  int
fg_pct, fg3_pct, ft_pct, efg_pct, ts_pct  float
per40_PTS, per40_REB, per40_AST, ...  float  -- derived
usg_pct             float?  -- USG% if listed (Sports-Reference computes for D1)
ortg, drtg          float?  -- offensive/defensive rating
fetched_at_utc      timestamp
source_url          string
```

For rookies who played multiple NCAA seasons (e.g., 4-year college player), capture each season as separate row. The most recent season is typically what we'll use, but having earlier seasons enables aging-curve modeling later.

## Output

`data/parquet/ncaa_player_seasons.parquet` — append-only, one row per (player, ncaa_season).

`data/parquet/ncaa_to_nba_rookie_join.parquet` — derived view, joins NCAA last-season stats to NBA rookie record:
```
nba_api_id          int64
ncaa_school         string
ncaa_last_season    string
ncaa_class_at_draft string
ncaa_per40_PTS, per40_REB, per40_AST, ...  float  -- their final NCAA season per-40
ncaa_3pct_volume    float  -- 3PT% on volume (>=2 attempts/game)
ncaa_efg_pct        float
ncaa_usg_pct        float?
years_in_college    int     -- 1, 2, 3, 4, 5
```

## Volume

- Rookies who went NCAA D1: ~600 of 843 (rough estimate, ~70% of rookies)
- Multi-year rookies × seasons: ~2,000-3,000 NCAA player-seasons total
- Sports-Reference pages are clean tables, ~1 page per player

## Concurrency / parallelism rules

Sports-Reference rate-limits aggressively. Their crawler-detection has hit our scrapers before (project memory has notes on this).

**Hard rules**:
- 1 worker, 1 request per **6 seconds** (longer than usual — they explicitly state polite scrapers should respect 6s)
- User-Agent: `NBAProjections-CollegeStatsFetcher/1.0 (research; mr.nathanhumphrey@gmail.com)`
- Honor `robots.txt`
- On 429: back off 60 seconds. On 3 consecutive 429s: stop for 1 hour, log critical event.
- No parallel workers — running multiple workers against Sports-Reference will trip detection

At 6 sec/req × 600 player pages = 60 minutes total. Fine for one-shot backfill.

## Player resolution

The hardest part. NCAA player → NBA player matching needs:
1. Name match (exact or fuzzy with first-initial fallback)
2. Draft year match (via `nba_draft_data.parquet`)
3. School name normalization ("North Carolina" / "UNC" / "Tar Heels" — all the same)

Sports-Reference player URLs include a slug that's reasonably stable. Build a mapping:
- For each NBA rookie with `pre_nba_team_type=ncaa`, derive their slug from `player_name + draft_year` and try direct URL fetch
- If 404, try fuzzy: search Sports-Reference's player search API or fall back to school-roster pages and find the player there

Expected resolution rate: 90%+ for rookies who clearly went NCAA. Unresolved go to a `ncaa_unresolved.parquet` for manual review.

## Validation

After backfill:

1. **Wembanyama**: he didn't play NCAA, so should NOT appear in this dataset (he played Metropolitans 92 in France — covered in international brief)
2. **Cooper Flagg**: assuming 2025 draft prospect — should appear with Duke 2024-25 season, ~17-18 PTS / 8-9 REB / 4 AST per game
3. **Brandon Miller (2023 draft)**: Alabama 2022-23 season, ~18.8 PTS / 8.2 REB / 2.1 AST per 40
4. **Jaime Jaquez Jr (2023 draft)**: UCLA 2022-23 season, ~17.8 PTS / 8.2 REB per 40
5. **Coverage**: each rookie class 2014-2024 should have NCAA stats for ~50-70 of the 60-pick draft (reflects the NCAA share of pre-NBA paths)

## Anti-patterns

- Don't fetch career-summary pages — fetch per-season pages so we have year-by-year detail
- Don't try to scrape advanced stats from KenPom or Bart Torvik — they're aggregator stats, basic per-40 from Sports-Reference is sufficient
- Don't follow links to high school stats — out of scope
- Don't fetch women's college basketball — separate dataset, not relevant
- Don't aggregate across schools for transfers — keep per-school per-season granularity (transfers play differently)

## CLI

```
python -m fetchers.ncaa_stats backfill --start-class 2014 --end-class 2024
python -m fetchers.ncaa_stats fetch_player --slug bradon-miller-1
python -m fetchers.ncaa_stats resolve --rebuild  # rebuild ncaa_to_nba_rookie_join
python -m fetchers.ncaa_stats validate
```

## Auth

None. Sports-Reference is public.

## Estimate

Build effort: 8-10 hours (HTML parsing + name/school matching + the joining logic). Backfill runtime: ~60 minutes at 6 sec/req for 600 player pages.

## Reporting

Row counts per ncaa_season, school coverage breakdown, resolution rate to nba_api_id, sample of 20 rookies showing NCAA last season → NBA rookie season for sanity checking.
