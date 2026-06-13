# Fetcher Brief: Analyst-Curation Layer for NBA Projections

## Context (for the fetcher agent)

We have an NBA projection engine at `D:\NBA Projections` that produces 9-cat fantasy stat projections (PTS, REB, AST, STL, BLK, TOV, FG%, FT%, 3PM) on a per-player per-game basis. Our v6 ship beats consensus on 5 of 9 cats but loses on PTS, AST, STL, MPG due to a structural gap: we lack the *human-curation signal* that aggregators like FantasyPros and Hashtag Basketball use (depth chart curation, injury status, trade rumors, training camp reports, summer league observations).

We want to close this gap with **independent primary-source data scraping**, not by ingesting their projections (which would taint our independence claim).

The MPG gap to consensus is 14% (our 2.99 vs their 2.63). Closing it is worth probably ~10-15% on every per-game stat that cascades through MPG.

## Output convention

All outputs land at `D:\NBA Projections\data\parquet\` as parquet files. Use `nba_api_id` as the canonical player key (join via `data\parquet\player_metadata_enriched.parquet`). For team key, use `team_abbr` (3-letter code) and resolve trade situations using effective dates.

Every parquet must include `fetched_at_utc` timestamp column.

Validation criteria below each task — fetcher should sanity-check row counts and coverage before declaring complete.

## Priority 1: Pro Sports Transactions Database (highest EV)

Source: `https://www.prosportstransactions.com/basketball/Search/Search.php`

**Goal**: per-player historical injury timeline back to 2014-15.

The site has a search interface where you select Sport=Basketball and date range; it returns a paginated table of every transaction. Filter to "Injuries" and "Movement" to get the two distinct datasets.

**Extract per row**:
- `transaction_date` (date)
- `team_abbr` (3-letter)
- `player_name` (raw — needs name → nba_api_id mapping after)
- `description` (raw text — contains injury type, return date estimate, transaction details)
- `transaction_type` (one of: injured-list / activated / placed / waived / signed / traded / etc.)

**Two output parquets**:
1. `injuries_history.parquet`: every "placed on IL", "DTD", "questionable", "out for season" event with body part / injury type extracted from description text
2. `transactions_history.parquet`: trades, signings, waivers — supersedes the empty `transactions.parquet` we have now

**Volume**: ~30,000 injury events + ~10,000 transactions per decade. Pace requests at ~1/sec to be polite; site is robust but has no published rate limit.

**Validation**:
- Coverage check: spot-check Joel Embiid → should have 50+ injury events back to 2014-15
- Coverage check: trade for Kyrie Irving Brooklyn → Dallas should appear in transactions in Feb 2023
- Body-part extraction quality: at least 80% of injury rows should have body_part populated

## Priority 2: Basketball-Reference mid-season trades + dates

Source: `https://www.basketball-reference.com/leagues/NBA_{YEAR}_transactions.html`

**Goal**: exact dates of every mid-season trade from 2014-15 through 2024-25 — supplements Pro Sports Transactions but is more cleanly structured.

**Extract per row**:
- `transaction_date`
- `from_team_abbr`
- `to_team_abbr`
- `players_in` (list of player names going to to_team)
- `players_out` (list going to from_team)
- `picks_or_cash` (other consideration)
- `season` (e.g. "2023-24")

**Output**: `bref_trades.parquet`

**Volume**: ~50-100 trades per season × 11 seasons = ~600-1100 rows.

**Validation**: Kyrie to Dallas (2023-02-06), Marcus Smart to Memphis (2023-06-22), James Harden to Clippers (2023-10-31) — confirm these dates are present.

## Priority 3: Spotrac active contracts

Source: `https://www.spotrac.com/nba/contracts/sort-cap_total/limit-1500/` (paginated by team)

**Goal**: every active NBA contract — used as a trade-probability proxy (expiring contracts have higher mid-season trade risk).

**Extract per row**:
- `player_name`
- `team_abbr`
- `position`
- `age`
- `contract_type` (Veteran / Rookie / Two-Way / Exhibit-10)
- `start_year`, `end_year`
- `cap_hit_each_year` (multi-year salary array)
- `is_player_option` (boolean array per year)
- `is_team_option` (boolean array per year)
- `expiring_this_season` (boolean — derived: end_year == current_season_year)

**Output**: `contracts.parquet`

**Volume**: ~500-600 contracts.

**Validation**: spot-check that Kawhi Leonard's contract appears with an upcoming player option year.

## Priority 4: NBA.com summer league + preseason box scores

Source: nba_api Python library (already installed in our venv).

**Endpoints**:
- Summer league: `LeagueGameLog(league_id_nullable='14')` — Las Vegas + California Classic
- Preseason: `LeagueGameLog(season_type_nullable='Pre Season')`

**Goal**: rookie + 2nd-year role projection — players who blow up in summer league or get heavy preseason minutes signal expanded regular-season role.

**Output**: `summer_league_stats.parquet`, `preseason_stats.parquet`

**Per row**: standard box stats (game_id, player_id, team_id, MIN, PTS, REB, AST, STL, BLK, TOV, FGM, FGA, FG3M, FG3A, FTM, FTA, +/-, season).

**Volume**: ~3000 summer league rows per year, ~5000 preseason rows per year. Backfill 2019-20 onward.

**Validation**: 2023 Summer League — Cam Whitmore (HOU) should have games at ~30 mpg averaging 18+ ppg.

## Priority 5: NBA.com official injury reports

Source: `https://official.nba.com/nba-injury-report-{YYYY-MM-DD}-{HHMMET}/` (PDF, also HTML)

**Goal**: game-day injury status — flagged 30 min before tip. Status codes: Out / Questionable / Probable / Doubtful / Available / Game Time Decision.

**Extract per row**:
- `report_date`, `report_time` (PT/ET)
- `game_id`
- `team_abbr`
- `player_name` → nba_api_id
- `status` (one of Out, Questionable, Probable, Doubtful, Available, GTD)
- `reason` (back, knee, illness, rest, conditioning, etc.)

**Output**: `nba_official_injuries.parquet`

**Volume**: ~200-400 entries per game day × 100+ game days = ~30k entries per season.

**Coverage**: backfill 2022-23 onward (NBA started publishing this format consistently).

**Validation**: any random Tuesday — should have 200+ players listed.

## Priority 6 (Twitter — paid, throttle accordingly)

If user-provided Twitter API access is enabled:

**Targets** (in order of EV):
1. `@wojespn` (Adrian Wojnarowski) — trade leaks, signing leaks, retirement announcements
2. `@ShamsCharania` — same domain, often breaks earlier
3. Per-team beat writers (use Athletic's NBA staff page to identify):
   - Top 10 most-active beat writers by team
   - Filter to tweets containing keywords: "starting", "rotation", "depth chart", "minutes restriction", "back from injury", "DNP-CD"
4. `@HoopsRumors` — aggregated rumor mill
5. `@RotoWorld_BK` — fantasy implications

**Extract per tweet**:
- `tweet_id`, `author`, `created_at`, `text`, `url`, `likes`, `retweets`
- Player mention extraction (run regex against player_name list from metadata)
- Topic classification: trade / injury / rotation / signing / lineup / other

**Output**: `twitter_basketball_signals.parquet`

**Cost control**: cap at $50/month initial budget. Sample top accounts daily, secondary accounts weekly. Skip retweets to halve volume.

**Validation**: any week — should have 100-500 tweets across the priority list.

## Anti-priorities (don't bother with these)

- ESPN ranking pages — paywall blocks scraping; we'd have to OCR
- The Athletic — paywall, TOS prohibits
- Hashtag Basketball — they want to be the customer not the source
- FantasyPros — would taint independence (this is the entire point of doing this work in the first place)
- Reddit r/nba etc — too noisy
- Yahoo NBA news — generic, no value-add over what we have

## Order of operations recommendation

1. Pro Sports Transactions DB injuries first — biggest single-source signal
2. Basketball-Reference trades parallel to that (independent system)
3. Spotrac contracts after — uses some of the trade dates as cross-check
4. NBA summer league + preseason — uses nba_api which we already have
5. NBA official injury reports — needs PDF parsing pipeline
6. Twitter last — most expensive, lowest structured signal

Each of 1-3 can be done independently and in parallel. Get me confirmation when each lands so I can start integrating.
