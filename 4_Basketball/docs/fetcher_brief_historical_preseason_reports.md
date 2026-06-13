# Code Brief: Historical Preseason Reporting Scrape (Reddit + Public Sources)

## Why this exists

We need historical preseason reporting (training camp announcements, beat-writer MPG forecasts, coach quotes about rotation) for the **2019-20 through 2024-25** seasons to validate signal strength on backtest. Beat writers and coaches frequently make explicit MPG forecasts ("Coach said Player X will play 30-32 mpg," "Player X locked into the starting lineup"). These are independent of FantasyPros/Hashtag aggregations and let us measure how much of the consensus advantage at preseason is recoverable from primary-source reporting alone.

**Twitter API has 7-day historical lookback only** — historical Twitter content is not feasible. Instead, this brief targets **Reddit threads, archived blogs, and public news articles** which retain years of history.

## Goal

Build a fetcher that captures preseason-window content (September 1 - October 31 of each year for 2019-2024) from primary sources, extracts player-level MPG / role / starting-lineup quotes, and produces a structured parquet for backtest validation.

## Sources, in priority order

### Source 1: Reddit (highest leverage — Reddit retains full history, content is free)

**Subreddits**:
- `r/nba` — general NBA discussion, often compiles beat writer reports
- `r/fantasybball` — preseason megathreads, roto rankings discussion
- `r/{team}` for all 30 NBA team subreddits (e.g., `r/lakers`, `r/warriors`, `r/celtics`, `r/torontoraptors`, etc.)

**Search queries** per subreddit (use Reddit's search API or `pmaw` library):
- `training camp`
- `depth chart`
- `starting lineup`
- `rotation`
- `minutes per game`
- `preseason`
- `beat writer report`

**Time filters**: posts from September 1 - October 31 of each target year (2019, 2020, 2021, 2022, 2023, 2024).

**Tools to use**:
- **Reddit API** via `praw` (Python Reddit API Wrapper) — free, requires OAuth app registration at https://www.reddit.com/prefs/apps
- Rate limit: 60 requests/minute for OAuth, 600/10min — plenty for our scale
- Reddit's search has known quirks: `time_filter='year'` works for last year, older needs combined `query + sort='new' + after_utc`
- **Camas** (https://camas.unddit.com or successor) — third-party Reddit archive search if Reddit's native search misses content
- **Reveddit** (https://www.reveddit.com) — surfaces deleted content; sometimes coaches/beat writers' tweets get screenshot to Reddit then deleted

**For each post matching**, extract:
- `post_id`, `subreddit`, `created_utc`, `author`, `score`, `num_comments`
- `title` (raw), `selftext` (raw, often the body of analysis posts)
- `url` (canonical Reddit permalink)
- Top-level **comments** with score >= 5 (filters out bot replies and low-effort jokes)

### Source 2: Wayback Machine archives of public NBA news + fantasy sites

**Targets** (capture September-October snapshots for each backfill year):
- `https://www.rotowire.com/basketball/news.php` — daily news ticker
- `https://www.hoopshype.com/news/nba/` — general NBA news
- `https://basketball.realgm.com/news/all` — RealGM news archive
- `https://www.cbssports.com/fantasy/basketball/news/` — fantasy news
- `https://hoopshabit.com/category/nba/` — public team analysis

For each Wayback snapshot, capture article titles + bodies + dates. Don't follow paywalls (ESPN+, The Athletic, Bleacher Report Premium — skip all).

### Source 3: Public team-blog archives (free / no paywall)

A handful of team-specific public blogs maintain free archives back several years:
- LakersOutsiders.com, LakersBlog (legacy URLs via Wayback)
- BlogABull.com (Bulls)
- CelticsBlog.com (free tier)
- Bleav network team-specific shows (transcripts public)
- Locked On NBA per-team podcast transcripts (search YouTube for transcripts)

These vary in availability; treat as best-effort secondary sources.

### Source 4: NBA.com official articles + team press releases

- `https://www.nba.com/news` — general NBA news, free
- `https://www.nba.com/{team}/news` per team
- Wayback snapshots needed for older content

These often quote coaches at training camp media days — high-quality MPG forecasts.

## Output

Produce one canonical parquet at `D:\NBA Projections\data\parquet\historical_preseason_reports.parquet`:

```
report_id           string  -- hash of (source + url + paragraph_idx) for dedup
source              string  -- reddit_post / reddit_comment / rotowire / hoopshype / realgm / nba_dot_com / wayback_*
source_url          string  -- canonical URL
posted_at_utc       timestamp(UTC)
season_target       string  -- e.g. "2023-24" — derived from posted_at month/year
team_abbr           string?  -- if team subreddit or team-specific article
author              string?  -- redditor or article byline
title               string?
text                string  -- raw text of the post/article/comment
mentioned_players   array<int64>  -- nba_api_id list, derived from regex match
quote_extractions   array<struct>  -- structured quotes (see below)
fetched_at_utc      timestamp(UTC)
```

### Structured quote extraction

The valuable signal isn't the whole article body — it's the specific quotes/predictions about MPG. Run a local extraction step (no API cost) on each fetched piece of text:

For each text, search for these patterns and extract a structured record:

**Pattern 1: Explicit MPG forecast**
- Regex examples: `(\d{1,2})(?:-(\d{1,2}))?\s*(?:mpg|minutes|min(?:utes)? per game)`
- Capture: low_mpg, high_mpg (if range), context_window (50 chars before + after)

**Pattern 2: Starting lineup / role assertion**
- Patterns: `(starting|will start|locked in|first-team|in the starting (lineup|five))`, `(will come off the bench|6th man|bench (rotation|role))`, `(starting at the (PG|SG|SF|PF|C))`
- Capture: role_type ("starter" / "bench" / "deep_bench"), position (if specified), confidence ("locked" / "expected" / "likely" / "competing")

**Pattern 3: Depth chart position**
- Patterns: `(starter|backup|primary backup|third-string|depth chart at \w+)`
- Capture: depth_order (1, 2, 3, 4)

**Pattern 4: Injury / availability constraint**
- Patterns: bound to body parts (knee, ankle, achilles, surgery, recovery, return)
- Capture: body_part, status ("out" / "limited" / "questionable" / "ramp-up"), expected_return (if mentioned)

For each extracted quote, write a struct row in `quote_extractions`:

```
{
  "pattern_type": "mpg_forecast" | "role" | "depth_order" | "injury",
  "matched_text": "the literal regex match",
  "context": "the 50 chars before + 50 after",
  "player_id": int64?,  -- nba_api_id of mentioned player, if extractable
  "extracted_value": string,  -- "32-34 mpg" or "starter" or "out 4-6 weeks"
  "confidence": float  -- 0.5 if ambiguous, 1.0 if explicit
}
```

This is the structured signal we'll join against actual MPG to measure backtest signal strength.

## Volume estimate

- Reddit posts: ~50 relevant posts × 30 subreddits × 6 years = ~9,000 posts
- Reddit comments per post (top 20 by score): ~9,000 × 20 = ~180,000 comments
- Wayback snapshots: ~50 snapshots × 5 sites × 6 years = ~1,500 articles
- Total raw rows: ~190,000

After quote extraction: probably ~10,000 structured quote rows (most posts are noise, only some contain explicit MPG forecasts).

## Throttling + cost

- **Reddit API**: free, throttle to 60 calls/min. Total ~9,000 post fetches + 9,000 comment-tree fetches = 18,000 calls = 5 hours at 60/min. Run in background, no urgency.
- **Wayback Machine**: free, throttle to ~1 req/3sec. ~1,500 fetches = 75 minutes.
- **No budget cap needed** — both sources are free, rate-limit is the bottleneck.

## Validation

Before declaring complete, spot-check:

1. **2023-24 Wembanyama**: there should be 50+ Reddit posts in r/NBASpurs and r/nba between Sep 1 - Oct 23, 2023 mentioning him. Quote extractions should include "starting at PF" or "30+ mpg expected" type forecasts.

2. **2023-24 Damian Lillard MIL**: after the trade announcement (Sep 27, 2023), there should be a flood of posts in r/MkeBucks discussing his expected role. At least one quote about "starter," "primary handler," or specific MPG forecast should be extracted.

3. **2022-23 trade-deadline preseason context for Bradley Beal staying in Washington**: r/washingtonwizards should have preseason content from Sep-Oct 2022 about his role. Note this was before he got the no-trade clause/Phoenix trade.

4. **Coverage check per season**: each of 2019-20 through 2024-25 should have at least 500 quote extractions. Light coverage years (e.g., 2020-21 was a delayed-start season due to COVID, preseason was December 2020 not October 2020) need date-window adjustment.

## CLI structure

```
python -m fetchers.historical_preseason --years 2019,2020,2021,2022,2023,2024 --sources reddit,wayback
python -m fetchers.historical_preseason --year 2023 --subreddit nba --dry-run  # preview queries without fetching
python -m fetchers.historical_preseason --validate  # run validation spot-checks
```

## Auth

- Reddit API: read-only OAuth credentials in `~/.config/reddit_api.json` or env vars `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`. Register an app at https://www.reddit.com/prefs/apps — choose "script" type, no callback URL needed.
- Wayback Machine: no auth required. Polite User-Agent header.

## Anti-patterns

- Don't follow paywalled article links (ESPN+, The Athletic, Bleacher Report Premium, Yahoo Sports premium)
- Don't fetch user-flair, post-flair, or moderation logs from Reddit
- Don't fetch Reddit images / videos / external link previews
- Don't deeply nest into comment threads beyond top 20 by score (diminishing returns vs. cost)
- Don't try to scrape Twitter via Wayback — Twitter's archived snapshots are mostly broken (auth gates on most pages)
- Don't OCR images or video transcripts (out of scope; YouTube transcript API is separate optional path)

## Player name resolution

For each text, run a local regex match against `D:\NBA Projections\data\parquet\player_metadata_enriched.parquet` `name` column. Use last-name match with disambiguation:

- If last name is unique in the active player pool (e.g., "Antetokounmpo"), match directly
- If last name is ambiguous (e.g., "Williams" — many players), require first initial or full first name
- For traded players, allow team-context disambiguation (subreddit team or article team_abbr provides context)

Store unmatched mentions as `unresolved_mentions: array<string>` for later manual review.

## Topic classification (local, free)

For each Reddit post / article, assign zero or more topic tags:
- `training_camp` — content from training camp window (Sep 24 - Oct 5)
- `preseason_game` — content discussing preseason exhibition games (Oct 5 - Oct 22)
- `media_day` — content from team media days (typically late Sep)
- `trade_aftermath` — content discussing role implications of off-season trade
- `injury_update` — content about preseason injury status
- `rotation_battle` — content about a contested rotation slot ("X vs Y for starting role")
- `rookie_role` — content about rookies' projected roles

## Schema for joining downstream

After fetch lands, the downstream join is:
```
historical_preseason_reports
  -> aggregate per (player_id, season_target):
     - count of MPG forecasts
     - mean / median forecasted MPG (from extracted ranges)
     - count of "starter" assertions vs "bench" assertions
     - injury concern signal score
  -> compare against actual season MPG
  -> measure signal strength via correlation + MAE reduction in v6 with feature included
```

## Estimate

Build effort: 12-20 hours for clean implementation including the regex extraction layer. Larger if topic classifier ends up needing better-than-keyword logic.

## Reporting on completion

- Total rows captured per source × year
- Total structured quote extractions
- Top 10 most-mentioned players per season (sanity check)
- Sample 20 quote extractions per pattern_type for manual quality review
- Coverage gaps if any (e.g., a subreddit returned zero posts for a year — investigate)
