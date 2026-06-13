# Code Brief: Twitter/X Fetcher for NBA Beat-Writer Signals

You are building a Python fetcher that monitors NBA beat-writer accounts on Twitter/X and produces a structured parquet of relevant tweets for the NBA projection engine at `D:\NBA Projections`. This runs as a daily automation; cost-effectiveness is critical.

## Critical context

**Pricing model**: per-resource (per-tweet), not per-tier.
- Posts: Read = $0.005 per tweet
- User: Read = $0.010 per user
- Skip everything else (Media, Analytics, Following/Followers, etc. — they cost money and we don't need them)

**Monthly budget target**: $25-35 steady-state. Hard cap at $50/month. Halt fetching at 80% of cap ($40) to leave headroom.

**Historical search limitation**: Basic tier Recent search has 7-day lookback only. Full archive search (back to 2006) is Pro-tier and significantly more expensive. **Build for forward monitoring only**, do NOT attempt historical backfill via API.

## Goal of the fetcher

Monitor a curated list of NBA beat writers and aggregators, capture tweets matching rotation/injury/depth-chart keywords, output to a parquet file. Output is consumed downstream by the projection engine to build per-player rotation/injury features.

## Account configuration

Maintain three tiers in a config file `D:\NBA Projections\config\twitter_accounts.json`:

```json
{
  "tier_1_daily_full_timeline": ["wojespn", "ShamsCharania"],
  "tier_2_keyword_filtered": [
    "TimBontemps", "MarcStein", "NickFriedell", "JamalCollier", 
    "MikeAReports", "ZachLowe_NBA", "HoopsRumors", "ChrisBHaynes",
    /* ~28 beat writers total, one per team — see The Athletic NBA staff page */
  ],
  "tier_3_weekly": ["RotoWorld_BK", "HoopsHype"]
}
```

Account list maintenance: write a CLI subcommand `python -m fetchers.twitter sync_accounts` that re-validates the account list and resolves any handle changes. Cost: ~$0.30 one-time for User: Read on ~30 accounts.

## Fetch rules (cost-critical)

### Tier 1: Woj + Shams — daily, full timeline, no keyword filter

Endpoint: `GET /2/users/{id}/tweets`

Query parameters:
- `since_id={last_seen_tweet_id_for_account}` — never re-fetch
- `exclude=retweets,replies` — filter at API
- `max_results=100`
- `tweet.fields=text,created_at,id,author_id` (only what we need)
- DO NOT request `user.fields`, `media.fields`, `expansions=`, etc.

Run frequency: daily, UTC midnight.

Expected cost: ~30 new tweets/day × 2 accounts × 30 days = 1,800 posts × $0.005 = **$9/month**.

### Tier 2: Beat writers — every 2 days, keyword-filtered search

Endpoint: `GET /2/tweets/search/recent`

Query construction (combine multiple authors in one call to amortize):

```
(from:beat_writer_1 OR from:beat_writer_2 OR ... OR from:beat_writer_N)
  (starting OR rotation OR "depth chart" OR DNP OR "minutes restriction" 
   OR demoted OR promoted OR "ruled out" OR cleared OR injury OR scratch
   OR "two-way" OR "G League")
  -is:retweet -is:reply lang:en
```

Constraints:
- Twitter search query has a per-call character limit (~512 chars depending on API version). If 28 accounts in one query exceeds, split into 2-3 batched queries.
- Pass `since_id={oldest_last_seen_id_in_batch}`
- `max_results=100`, paginate via `next_token` if more

Run frequency: every 2 days.

Seasonal keyword additions (modify keyword block by date):
- September 1 - October 22: append `OR camp OR scrimmage OR "preseason game"`
- February 1 - February 15: append `OR trade OR deal OR moved OR acquired`
- March 1 - April 15: append `OR playoff OR seeding OR "rest day"`

Expected cost: ~5 keyword-matching tweets/day per account × 28 accounts × 30 days = ~2,500 posts × $0.005 = **$12.50/month**.

### Tier 3: Aggregators — weekly, keyword-filtered

Same endpoint and query pattern as Tier 2, ~3 accounts. Run weekly.

Expected cost: ~$1/month.

## Caching (MANDATORY)

Maintain three local files:

**1. `D:\NBA Projections\data\parquet\twitter_basketball_signals.parquet`** — primary output. Append new tweets, never overwrite. Schema below.

**2. `D:\NBA Projections\config\twitter_state.json`** — fetch state per account:
```json
{
  "wojespn": {"last_seen_tweet_id": "1834...", "last_fetched_utc": "2026-04-30T00:00:00Z"},
  "ShamsCharania": {"last_seen_tweet_id": "1834...", "last_fetched_utc": "2026-04-30T00:00:00Z"},
  ...
}
```
Read on every fetch to derive `since_id`. Update after every successful fetch.

**3. `D:\NBA Projections\data\parquet\twitter_usage.parquet`** — daily usage tracker:
```
date | posts_fetched | api_calls | estimated_cost | monthly_running_cost
```
Write one row per day. Compute month-to-date cost from this table.

## Halt condition

Before each fetch cycle, read `twitter_usage.parquet` and compute month-to-date cost. If `monthly_running_cost >= $40`, **halt all non-tier-1 fetches** for the rest of the calendar month. Log the halt event. Resume next month.

If `monthly_running_cost >= $50`, halt ALL fetches including tier-1 (this is an emergency stop, indicates something is broken — review logs).

## Output schema (`twitter_basketball_signals.parquet`)

```
tweet_id           string  -- canonical Twitter tweet id
author             string  -- handle without @, lowercase
author_id          string  -- numeric Twitter user id
created_at         timestamp(UTC)
text               string  -- raw tweet text
url                string  -- "https://twitter.com/{author}/status/{tweet_id}"
mentions_player_ids array<int64>  -- nba_api_id list, derived locally from text via regex against player_metadata names
topic_tags         array<string>  -- subset of [trade, injury, rotation, signing, lineup, scratch, other]
fetched_at_utc     timestamp(UTC)
```

After fetching, run two local-only post-processing steps (zero API cost):

**1. Player mention extraction**: for each tweet, regex-match against the canonical player names from `D:\NBA Projections\data\parquet\player_metadata_enriched.parquet`. Record the list of matched `nba_api_id` values in `mentions_player_ids`. Use last-name-only match with team disambiguation when ambiguous.

**2. Topic classification**: simple keyword-based classifier:
- "trade" / "deal" / "acquired" / "shipped" → topic = `trade`
- "out" / "DNP" / "ruled out" / "questionable" / "doubtful" / "injury" / body parts → topic = `injury`
- "starting" / "rotation" / "depth chart" / "minutes" → topic = `rotation`
- "signed" / "two-way" / "G League" → topic = `signing`
- "lineup" / "starting five" / "starters" → topic = `lineup`
- "scratch" / "rested" → topic = `scratch`
- else → `other`

Multiple tags allowed per tweet.

## CLI structure

```
python -m fetchers.twitter run                    # daily fetch cycle
python -m fetchers.twitter sync_accounts          # one-time / quarterly account list refresh
python -m fetchers.twitter status                 # report month-to-date cost + last-fetched per account
python -m fetchers.twitter halt                   # manual emergency halt (writes halt flag)
python -m fetchers.twitter resume                 # clear halt flag
```

Schedule via cron / Windows Task Scheduler:
- `run` every 6 hours during normal operation (still hits "daily for tier-1" since since_id de-dupes)
- `status` weekly, output to log

## Auth

Read API credentials from environment variables:
- `TWITTER_API_KEY`
- `TWITTER_API_SECRET`
- `TWITTER_BEARER_TOKEN`

Or from a local file `~/.config/twitter_api.json` if env vars not set. Never hard-code or commit secrets.

## Error handling rules

1. **Rate limit (429)**: respect `Retry-After` header. If no header, back off 60 seconds and retry once. If retry fails, halt this run, resume next scheduled cycle.

2. **Transient 5xx**: 3 retries with exponential backoff (5s, 30s, 120s).

3. **Auth failure (401/403)**: halt all fetches, log critical error, alert via stderr. Do not retry.

4. **Empty result**: not an error. Update `last_fetched_utc`, do not advance `last_seen_tweet_id`.

5. **Keyword query exceeds character limit**: log a critical error. Reduce account batch size in tier-2/3 query and re-emit. Do not silently truncate.

## What NOT to build

- Do not fetch user details after the one-time `sync_accounts` operation
- Do not fetch tweet conversations / threads / quote contexts
- Do not fetch media attachments
- Do not implement full-archive search even if accidentally available
- Do not implement followers/following lookups
- Do not retain raw Twitter API responses (only the extracted fields above)
- Do not add a UI / dashboard — this is a headless fetcher
- Do not de-duplicate across the parquet aggressively beyond `tweet_id` primary key

## Test plan

Before merging:
1. **Dry-run mode**: add `--dry-run` flag that logs intended queries + cost estimate without making real API calls
2. **Cost smoke test**: actual run for 1 day with hard cap at $1, verify usage tracker updates correctly
3. **Halt test**: set monthly cost to $45 manually in usage tracker, verify tier-2/3 halts
4. **Schema validation**: ensure parquet schema matches spec; spot-check 10 tweets have valid `mentions_player_ids`

## Reporting

After each `run`, log to stderr in this format:
```
[twitter-fetch] 2026-04-30T00:00:00Z run complete
  tier_1: 27 new tweets ($0.135)
  tier_2: 0 calls (skipped, ran 18hr ago)
  tier_3: 0 calls (skipped, ran 5d ago)
  month_to_date: $12.45 of $50.00 cap (24.9%)
  next_run: 2026-04-30T06:00:00Z
```

## Estimate

Build effort: 6-10 hours for a clean implementation of the core fetcher + tests. Add 2-4 hours if integrating with an existing project structure.
