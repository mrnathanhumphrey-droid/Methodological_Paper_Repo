# Code Brief: Rotation Reports — Hashtag Basketball + Rotoworld + NBC Sports Edge

## Why this exists

Rotation reports differ from depth charts: they explicitly describe the *expected role* per player ("primary handler," "stretch 4," "primary backup at PG and SG," "fringe rotation behind X and Y"). They synthesize depth chart + minutes projection + role description into a paragraph per player.

These provide the **third leg of corroboration** alongside Vegas markets (implied MPG) and depth charts (depth_order). Where all three agree, high confidence; where they disagree, signal noise or genuine uncertainty.

## Sources

### Primary

1. **Hashtag Basketball**: `https://hashtagbasketball.com/fantasy-basketball-projections` and `https://hashtagbasketball.com/fantasy-basketball-rankings`
   - Public, free to view aggregate projections + rankings
   - Has player-by-player blurbs / role descriptions on individual player pages
   - Updated through preseason and weekly during season

2. **NBC Sports Edge** (formerly Rotoworld): `https://www.nbcsportsedge.com/basketball/nba`
   - Public news ticker with player-specific notes
   - Each note is a structured "Player Update" paragraph from their analysts
   - Historical archive accessible via pagination back several years

3. **CBS Sports Fantasy Notes**: `https://www.cbssports.com/fantasy/basketball/news/`
   - Public, news-ticker format
   - Each entry is a structured player news item with analyst commentary

4. **The Action Network player pages** (separate from their odds product): `https://www.actionnetwork.com/nba/players/{player-slug}`
   - Free, has player-specific role notes in addition to odds

### Backfill

Wayback Machine for all four. Snapshot dates: same cadence as depth charts (Sep 15 / Oct 1 / Oct 15 / Oct 23 / Nov 1 / Nov 15 / Dec 1 / Dec 25 / Jan 15 / Feb 15 / Mar 15 / Apr 1 of each backfill year).

## What to extract

Each "rotation report" or "player update" item has a structured record:

```
report_id           string  -- hash of (source + url + date + first_50_chars_text)
snapshot_date       date    -- when this update was published
captured_at_utc     timestamp
source              string  -- "hashtag" / "nbc_sports_edge" / "cbs_sports" / "action_network"
nba_api_id          int64?
player_name         string
team_abbr           string
title               string  -- short header / news headline
body                string  -- full text of the analyst note
url                 string  -- canonical link
extracted_signals   array<struct>  -- structured pulls from the body (see below)
fetched_at_utc      timestamp
```

### Local extraction (no API cost)

Run regex/keyword extraction on `body` to populate `extracted_signals`. Same patterns as the historical_preseason_reports brief:

1. **MPG forecast** — explicit minutes references like "expected to play 30 mpg," "in line for 28-32 minutes"
2. **Role assertion** — "starter," "primary backup," "6th man," "fringe rotation"
3. **Depth chart slot** — "starting at the 1," "backup PG"
4. **Injury status / availability** — "out 4-6 weeks," "questionable for opener"
5. **Rotation context** — "behind Player X and Player Y," "ahead of Player Z"
6. **Trade rumor / move signal** — "could be moved," "available for the right price"

Each extracted signal:
```
{
  "pattern_type": "mpg_forecast" | "role" | "depth_order" | "injury" | "rotation_context" | "trade_signal",
  "matched_text": "literal regex match",
  "context": "50 chars before + after",
  "extracted_value": string,
  "confidence": float
}
```

Cross-reference against the **historical_preseason_reports.parquet** schema if that's already built — same extraction logic should apply, share the regex library.

## Output

`data/parquet/rotation_reports.parquet` — one row per (source, player, date) update event.

Optionally derive a per-player aggregate view at `data/parquet/rotation_reports_aggregate.parquet`:
```
nba_api_id, season, last_30_days_n_updates, mean_forecasted_mpg, role_consensus, 
last_injury_status, last_rotation_context, n_trade_signals_30d
```

## Volume estimate

- Hashtag: ~50 active players blurbs × ~weekly updates = ~200 rows/month during preseason, ~800 rows/month during season
- NBC Sports Edge: ~30 player updates/day during preseason, ~50/day during season — high-volume ticker
- CBS Sports: similar to NBC
- Action Network: ~10 player updates/day

Per season total: ~25,000 rows across all four sources for an active 6-month season window.

Historical backfill (3 seasons × 12 snapshot dates): ~5,000-10,000 rows depending on archive completeness.

## Concurrency / parallelism rules

**Run all 4 sources in parallel.** Each is a separate domain with separate rate limits:

- **Hashtag Basketball**: 1 worker, 1 req/2sec. ~10 minutes for full preseason archive scrape.
- **NBC Sports Edge**: 2 concurrent workers (their archive is page-by-page, safe to parallelize), each at 1 req/sec. ~5 minutes for a season.
- **CBS Sports**: 1 worker, 1 req/2sec. Their pagination is straightforward.
- **Action Network**: 1 worker, 1 req/2sec.

**Wayback Machine for historical**: 1 worker, 1 req/3sec — global Wayback throttle. **Do not parallelize Wayback fetches** across sources.

**Aggregate**: live snapshot of all four ~5-10 minutes. Full backfill including Wayback ~3-5 hours for 3 seasons × 4 sources.

**Anti-ban**:
- User-Agent: `NBAProjections-RotationReports/1.0 (research; nathanhumphrey@gmail.com)`
- Cache aggressively in `data/cache/rotation_reports/{source}/` — never re-fetch the same URL
- On 429/503: exponential backoff with jitter, halt that source for 30 minutes if 3 consecutive failures
- No proxies. If a source bans us, the rate was wrong — adjust.

## Validation

1. **Hashtag preseason 2023-24**: should have player blurbs for at least 200 fantasy-relevant players. Spot-check Wembanyama's blurb mentions "starter" and "rookie of year" and probable 30+ MPG.

2. **NBC Sports Edge mid-season**: any random week in Jan 2024 should have ~200-400 player updates across the league.

3. **Embiid Jan 2024 meniscus**: NBC Sports Edge / CBS Sports should both have multiple updates around 2024-01-30 mentioning surgery, out-for-season.

4. **Pascal Siakam trade Jan 2024**: rotation reports across sources should reflect his new role in IND starting ~2024-01-20.

5. **Coverage**: each source should have at least 50 updates per week during the regular season. Significantly fewer = parser broken or hitting paywall.

## Anti-patterns

- Don't fetch comments / reader reactions on these articles
- Don't fetch the writers' bio pages or social profiles
- Don't deeply chase outbound links to ESPN+ / The Athletic — those are paywalled
- Don't try to scrape Hashtag Basketball's premium tools (paywall) — basic projections + free blurbs are sufficient
- Don't deduplicate across sources during ingestion — same player report from different analysts is signal, not noise

## CLI structure

```
python -m fetchers.rotation_reports snapshot                # live: all 4 sources, today
python -m fetchers.rotation_reports snapshot --source hashtag
python -m fetchers.rotation_reports backfill --start 2023-09-01 --end 2024-04-15 --weekly
python -m fetchers.rotation_reports extract                 # rerun local extraction on existing rows
python -m fetchers.rotation_reports aggregate               # rebuild rotation_reports_aggregate.parquet
python -m fetchers.rotation_reports validate
```

## Auth

None required for the basic / free tiers. Skip all "premium" / paywalled features.

## Estimate

Build effort: 10-14 hours for 4-source scraper + extraction layer + aggregate computation. Each source has its own DOM structure to parse; the regex extraction layer should be shared with the historical_preseason_reports fetcher.

## Reporting

After each snapshot/backfill: row counts per source × snapshot, top 10 most-mentioned players in last 7 days (sanity check freshness), extraction quality metrics (% of rows with at least one structured signal extracted, target >60%).

## What this unlocks downstream

- Per-player "rotation report consensus" feature: how many sources flagged this player for an MPG change in last 14 days, sentiment-coded
- Cross-corroboration: where Vegas + depth charts + rotation reports all agree, high confidence; where they diverge, our model gets wider posterior on that player
- Backtest: did Oct 2023 rotation reports predict 23-24 MPG better than naive? Better than v6 alone?
