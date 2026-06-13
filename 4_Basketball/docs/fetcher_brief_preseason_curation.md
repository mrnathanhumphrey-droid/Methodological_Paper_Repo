# Fetcher Brief: 26-27 Preseason Curation Layer

## Why this exists

Our v6 NBA projection ship beats consensus on 5 of 9 fantasy categories at preseason. We did this with **zero access to the preseason curation layer** that analysts use (depth charts, preseason games, injury reports, training camp news). We want to ingest that layer from primary sources (not by ingesting their projections — that would taint our independence) and measure how each addition closes the MPG MAE gap to consensus.

**Current preseason MPG MAE**: 2.99
**Consensus preseason MPG MAE**: 2.63
**Gap to close**: 0.36

Each ingestion below has an estimated MAE-improvement contribution. After landing, we'll backtest on 23-24 (re-run v6 with the new feature plugged in) to measure actual lift.

## Convention for all outputs

- All parquets land in `D:\NBA Projections\data\parquet\`
- Use `nba_api_id` as canonical player key (join via `player_metadata_enriched.parquet`)
- Use `team_abbr` (3-letter) as canonical team key
- Include `fetched_at_utc` timestamp on every row
- Report row counts + spot-check coverage when complete

## Priority 1 — Preseason game box scores (highest EV, lowest effort)

**Estimated MPG MAE saved**: 0.05-0.08 (3-5 games of actual minutes data per player)

**Source**: nba_api Python library (already in our venv)

**Endpoints**:
- `LeagueGameLog(season_type_nullable='Pre Season', season=...)` — game IDs
- `BoxScoreTraditionalV2(game_id=...)` — player stats per game

**Backfill seasons**: 2019-20 through 2024-25 (preseason exhibition games typically Sep 30 - Oct 22 each year)

**Output**: `preseason_box_scores.parquet`

Schema:
- `game_id`, `game_date`, `season` (e.g. "2023-24"), `season_type`="Pre Season"
- `nba_api_id`, `player_name`, `team_abbr`, `team_id`
- `minutes` (decimal)
- `FGM`, `FGA`, `FG3M`, `FG3A`, `FTM`, `FTA`, `OREB`, `DREB`, `REB`, `AST`, `STL`, `BLK`, `TOV`, `PF`, `PTS`
- `plus_minus`

**Volume**: ~5000 rows per season (10-12 teams × 4-7 preseason games × 12-15 players each).

**Validation**:
- 2023-24 preseason: Wembanyama should have 4-5 game appearances on SAS averaging 25+ mpg
- 2023-24 preseason: Joel Embiid should have 1-2 game appearances on PHI (he typically rests preseason)
- 2023-24 preseason: total games per team should be 4-7 (varies by team)

**Integration plan**:
- Compute per-player preseason MPG average (when GP >= 2)
- Add as a covariate to v6 MPG career-blend with weight ~3 equivalent-games
- Backtest: re-run 23-24 ship with this feature, measure MPG MAE change

## Priority 2 — Historical depth charts via Wayback Machine

**Estimated MPG MAE saved**: 0.10-0.15 (the single biggest signal — coach-stated rotation intent)

**Sources** (in order):
1. ESPN: `https://www.espn.com/nba/team/depth/_/name/{team_abbr}` (e.g., `name/lal` for Lakers)
2. RotoWire: `https://www.rotowire.com/basketball/depth-charts.php`

**Via Wayback**: `https://web.archive.org/web/{YYYYMMDD}/{original_url}`

**Snapshot dates** (for 23-24 backtest first, then we extend to other seasons):
- 2023-09-15 (training camp opens)
- 2023-09-30 (camp + early preseason)
- 2023-10-15 (right before opening night)
- 2023-10-23 (opening night)
- 2023-11-15 (early-season adjustments)

**Output**: `depth_charts_history.parquet`

Schema:
- `snapshot_date` (date)
- `requested_date` (date — what we asked for, for fallback tracking)
- `wayback_url` (str)
- `source` ("espn" or "rotowire")
- `team_abbr`
- `position` ("PG"/"SG"/"SF"/"PF"/"C")
- `depth_order` (1=starter, 2=primary backup, 3=tertiary, etc.)
- `player_name` (raw — will join to nba_api_id later)
- `injury_flag` (bool — present in some sources)

**Volume**: 30 teams × 5 positions × ~3 depth slots × 5 dates × 2 sources = ~4500 rows for one season backfill.

**Validation**:
- 2023-10-15 ESPN: Wembanyama at SAS PF depth_order=1 (he was a Day-1 starter)
- 2023-10-15 ESPN: Damian Lillard at MIL PG depth_order=1 (after his trade from POR)
- 2023-10-15 ESPN: Jordan Poole at WAS depth_order=1 SG (after trade from GSW)

**Integration plan**:
- Encode `depth_order` as a feature: 1=starter, 2=key bench, 3=fringe rotation, 4+=deep bench
- Build a position-aware MPG model with depth_order as the dominant feature
- Backtest: 23-24 ship with depth_order, measure MPG MAE change especially on the off-season-trade cohort (where depth_order is most informative)

## Priority 3 — Pro Sports Transactions DB (injury + transaction backfill)

**Estimated MPG MAE saved**: 0.05-0.10 (refines chronic injury flag with categorized injury types)

**Source**: `https://www.prosportstransactions.com/basketball/Search/Search.php`

The site has a search interface filterable by sport, date range, and category. Two distinct datasets: "Injuries" and "Movement."

**Backfill range**: 2014-15 forward (gives us 10+ years of injury history per veteran)

**Output**: `pro_sports_injuries.parquet` and `pro_sports_transactions.parquet`

Injuries schema:
- `transaction_date`
- `team_abbr`
- `player_name` (raw)
- `description` (raw text)
- `body_part` (parsed: knee, ankle, achilles, back, hamstring, etc.)
- `injury_type` (parsed: surgery, sprain, strain, soreness, fracture, etc.)
- `severity` (parsed: out-for-season, indefinite, day-to-day, etc.)
- `return_date_estimate` (parsed when present)

Transactions schema:
- `transaction_date`
- `transaction_type` (trade, signing, waiver, two-way, etc.)
- `from_team_abbr`, `to_team_abbr`
- `player_name`
- `contract_terms` (raw text)

**Volume**: ~30,000 injury events + ~10,000 transactions over a decade.

**Throttling**: 1 request/sec is polite. Backfill 10 years × ~3000 events/year = ~30 minutes total at that pace.

**Validation**:
- Joel Embiid should have 50+ injury events back to 2014-15 with body parts like knee, foot, back
- Kyrie Irving's Brooklyn → Dallas trade should appear with date 2023-02-06
- Klay Thompson's ACL tear (June 2019) should be in the dataset with body_part=knee, severity=out-for-season

**Integration plan**:
- Build chronic injury feature: count of "out-for-season" or "surgery" events in last 3 years per player
- Categorize chronic risk: structural (achilles, ACL, meniscus) vs muscular (hamstring, calf) vs durability (back, foot)
- Add as feature to MPG model — different multipliers per category
- Backtest: 23-24 with this feature, measure MPG MAE change especially on Embiid/Kawhi/Zion/Beal cohort

## Priority 4 — Coaching change tracking

**Estimated MPG MAE saved**: 0.02-0.05 (small but cheap)

**Source**: `https://www.basketball-reference.com/coaches/` (per-coach pages with team history)

Plus offseason coaching change announcements scraped from Wikipedia per-team pages (NBA team Wikipedia pages list head coaches with start/end dates).

**Backfill range**: All coaching tenures 2014-15 forward.

**Output**: `coaching_history.parquet`

Schema:
- `coach_name`
- `team_abbr`
- `season` (e.g. "2023-24")
- `start_date`, `end_date` (NULL if ongoing)
- `replaced_who` (predecessor coach name, optional)
- `coaching_career_seasons` (count, derived)

**Volume**: ~30 teams × ~10 seasons × ~1.5 coach changes per team-season = ~450 rows.

**Validation**:
- 2023-24 PHI: Nick Nurse should appear (replaced Doc Rivers June 2023)
- 2023-24 MIL: Adrian Griffin → Doc Rivers (mid-season change Jan 2024)
- 2023-24 TOR: Darko Rajakovic (rookie head coach, replaced Nurse)

**Integration plan**:
- New-coach flag (rookie HC or first season with new team)
- Compute coach's historical "rotation depth" (how many players average 20+ MPG under them)
- Use as MPG model feature — new coaches typically expand rotations / shorten benches differently
- Backtest measure on 23-24 cohort affected by coaching changes (PHI, MIL, TOR, etc.)

## Priority 5 — Twitter beat writer signals (BUDGET-CAPPED)

**Estimated MPG MAE saved**: 0.03-0.05 (mostly captures training camp battle outcomes + injury status late-breaking)

**HARD CONSTRAINTS**:
- **Maximum spend: $50/month** (cap at API tier that allows ~10k tweets/month)
- **Maximum API calls: 100/day** during normal operation
- **Cache aggressively**: every tweet stored locally — never re-fetch same tweet_id
- **Skip retweets** entirely (halves volume, retweets rarely add new info)
- **Pause requests if 80% of monthly budget consumed before month-end**

**Targeted accounts only — DO NOT crawl Twitter generally**:

Tier 1 (highest signal, fetch daily):
- `@wojespn` (Adrian Wojnarowski)
- `@ShamsCharania`

Tier 2 (per-team beat writers, fetch 2x/week):
- One primary beat writer per team (use The Athletic's NBA staff page as the canonical list)
- ~30 accounts total

Tier 3 (aggregators, fetch weekly):
- `@HoopsRumors`
- `@RotoWorld_BK`

**Filter keywords** for relevance (only store tweets matching at least one):
- "starting", "rotation", "depth chart"
- "minutes restriction", "load management"
- "DNP-CD", "DNP coach's decision"
- "back from injury", "cleared to play", "ruled out", "questionable"
- "demoted", "replaced", "promoted", "moved to bench"
- "starting at PG/SG/SF/PF/C"

**Output**: `twitter_basketball_signals.parquet`

Schema:
- `tweet_id` (str), `author` (str), `created_at` (timestamp)
- `text` (raw)
- `url`
- `is_retweet` (bool — should always be False given filter)
- `mentions_player_ids` (list of nba_api_id from regex match against player_metadata names)
- `topic_tags` (list: trade / injury / rotation / signing / lineup / other)
- `monthly_budget_tracker` (running cost for the month, helps debug rate limits)

**Volume**: ~100-500 tweets/week × 26 weeks (preseason through end of season) = ~5000-13000 tweets per season. Budget allows for it.

**Integration plan**:
- For each tweet, extract player_id mentions + topic tags
- Build daily aggregate features: "player X has Y rotation/injury mentions in last 14 days"
- Add as feature to MPG model — sentiment-coded (positive: "back", "starting", "promoted"; negative: "demoted", "out", "DNP-CD")
- Backtest is harder here since we don't have historical tweet data; main use is forward-looking for 26-27

## Anti-priorities (do not bother)

- ESPN ranking pages — paywalled, OCR-required
- The Athletic — paywalled, TOS prohibits scraping
- Hashtag Basketball — they're a comparison target, not a source
- FantasyPros — would taint independence claim
- Reddit r/nba — too noisy
- Generic NBA news aggregators — duplicates of beat writer content

## Order of operations recommendation

The order below maximizes "MPG MAE saved per hour of engineering":

1. **Priority 1: Preseason game box scores** (~2 hours engineering, biggest signal-per-effort)
2. **Priority 2: Depth charts via Wayback** (~5 hours, biggest absolute signal, free)
3. **Priority 3: Pro Sports Transactions** (~10 hours including parsing, replaces our chronic flag)
4. **Priority 4: Coaching changes** (~3 hours, modest effort modest gain)
5. **Priority 5: Twitter** (~5 hours engineering + ongoing $50/mo cap)

Each can be done independently. Run them in parallel if you have parallel fetcher capacity. After each lands, I'll re-run the 23-24 backtest and report which MAE moved how much. Cumulatively expected to close most of the 0.36 MPG gap to consensus.

## Backtest design (so you know what success looks like)

After each ingestion lands, the validation runs:
1. Re-build v6 ship for 23-24 with the new feature included
2. Compare MPG MAE on the 195-player ship cohort vs current v6 MAE 2.99
3. Cohort breakdown: stable stars / off-season trades / mid-season trades / stable bench
4. Per-game stat MAE cascade (should track MPG improvement proportionally)

Target after all 5 ingestions: MPG MAE ~2.65 (matching consensus). With live-update on top, dominant by November 15.

Report on completion: row counts + validation spot-checks + monthly cost (Twitter only) + any blockers.
