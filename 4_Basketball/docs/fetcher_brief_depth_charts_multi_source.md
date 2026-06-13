# Code Brief: Multi-Source NBA Depth Chart Aggregator

## Why this exists

Depth charts published by ESPN, RotoWire, Lineups.com, and FantasyPros translate beat-writer reports + coach quotes + training camp coverage into structured rotation data. Each is an analyst-curated output, but they're independent of each other — aggregating across them gives consensus depth chart with disagreement signal (where the sources disagree, the rotation is genuinely contested).

We have one stale snapshot at `data/parquet/depth_charts.parquet` (150 rows, ESPN-only, April 2026). We need a multi-source live aggregator + historical backfill via Wayback Machine.

This complements the Vegas markets ingestion: depth charts give per-position depth_order; Vegas gives implied MPG. Cross-checking the two surfaces signal vs noise.

## Sources

### Primary live sources

1. **ESPN**: `https://www.espn.com/nba/team/depth/_/name/{team_abbr}` — per-team depth chart. Team abbr lower-case (e.g., `lal`, `gsw`). Public, no auth.

2. **RotoWire**: `https://www.rotowire.com/basketball/depth-charts.php` — single-page all-team depth chart. Public, no auth, has a "premium" overlay but the basic depth chart is free.

3. **Lineups.com**: `https://www.lineups.com/nba/depth-chart` — single-page all-team. Public.

4. **FantasyPros**: `https://www.fantasypros.com/nba/depth-charts.php` — single-page all-team. Free; requires no auth for depth chart view.

### Historical backfill

Wayback Machine snapshots of all four sites. URL pattern: `https://web.archive.org/web/{YYYYMMDD}/{original_url}`.

For 23-24 backtest: snapshot dates Sep 15, Oct 1, Oct 15, Oct 23 (opening night), Nov 1, Nov 15, Dec 1, Dec 25, Jan 15, Feb 15, Mar 15, Apr 1.

Same dates for 22-23, 21-22 if doing multi-season validation.

## What to extract

For each source × team × position × depth_slot, capture:

```
snapshot_date       date
source              string  -- "espn" / "rotowire" / "lineups" / "fantasypros"
team_abbr           string
position            string  -- "PG" / "SG" / "SF" / "PF" / "C" (canonical 5)
depth_order         int     -- 1=starter, 2=primary backup, 3=tertiary, 4+=deep bench
player_name_raw     string
nba_api_id          int64?  -- resolved post-fetch
injury_flag         bool?   -- some sources flag injured starters; capture when present
status_note         string? -- "questionable" / "out" / "ramp-up" / etc when present
fetched_at_utc      timestamp
source_url          string
```

Some sources use different position taxonomies (e.g., "F" combined for SF/PF). Normalize to canonical PG/SG/SF/PF/C using the per-source mapping.

**Normalization cases**:
- ESPN uses PG/SG/SF/PF/C natively → no remap
- RotoWire uses PG/SG/SF/PF/C → no remap
- Lineups.com sometimes uses "F" for combined SF/PF → split based on player's listed position metadata
- FantasyPros uses PG/SG/SF/PF/C → no remap

For each player encountered, also capture their listed position(s) from the source — this is the source's positional assignment, separate from the depth chart slot.

## Output

`data/parquet/depth_charts_history.parquet` — append-only, one row per (snapshot_date, source, team, position, depth_order).

`data/parquet/depth_chart_disagreements.parquet` — derived view, computed after each fetch cycle. For each (snapshot_date, team, player), count how many sources have them at depth_order=1 vs 2 vs 3+. Disagreement = sources don't agree on the player's depth_order. High disagreement = contested rotation slot.

Schema for disagreements:
```
snapshot_date       date
team_abbr           string
nba_api_id          int64
player_name         string
position            string
n_sources           int     -- how many sources have this player listed
depth_order_min     int     -- best (lowest) depth across sources
depth_order_max     int     -- worst (highest) depth across sources
depth_order_mode    int     -- modal depth across sources
disagreement_score  float   -- normalized: 0=full consensus, 1=max disagreement
```

## Volume estimate

Live: 30 teams × 5 positions × ~3 depth slots × 4 sources = ~1,800 rows per snapshot. Daily snapshots Aug 1 - Apr 15 = ~250 days × 1,800 = ~450,000 rows.

Historical backfill (12 dates × 3 seasons × 4 sources): ~12 × 1,800 × 3 = ~65,000 rows.

Disagreements view: ~30 teams × ~12 rotation players × 250 dates = ~90,000 rows.

Tiny compared to the full box score archive.

## Concurrency / parallelism rules

**Run all 4 live sources in parallel across separate workers.** Each source has its own throttle:

- **ESPN**: per-team URL = 30 requests per snapshot. Run 3 concurrent workers, each at 1 req/2sec. ~20 sec per snapshot.
- **RotoWire**: single-page. 1 worker, 1 request, no throttle needed at this volume.
- **Lineups.com**: single-page. 1 worker, 1 request.
- **FantasyPros**: single-page. 1 worker, 1 request.

**Wayback Machine** for historical backfill: max 1 worker at 1 req/3sec across ALL Wayback queries (their CDN is shared and aggressively rate-limits). Don't parallelize Wayback fetches across multiple workers — it'll trip the global Wayback throttle.

**Aggregate**: live snapshot completes in ~30 seconds total. Historical backfill takes ~10 minutes for the full 65k-row dataset.

**Anti-ban hygiene**:
- Polite User-Agent: `NBAProjections-DepthChartAggregator/1.0 (research; nathanhumphrey@gmail.com)`
- Honor robots.txt directives
- On 429/503: exponential backoff with jitter, halt that source after 3 consecutive failures
- Don't IP-rotate. If banned, the rate was wrong — fix it, don't proxy.

## Validation

After each backfill, spot-check:

1. **2023-24 opening night ESPN snapshot (2023-10-23)**: Wembanyama at SAS PF depth_order=1; Lillard at MIL PG depth_order=1; Jordan Poole at WAS SG depth_order=1.

2. **Cross-source agreement on undisputed starters**: LeBron/Curry/Embiid/Doncic should be depth_order=1 across all 4 sources at every snapshot. If any source has them lower, the parser is broken.

3. **Disagreement signal on contested rotations**: 2023-10-23 OKC PF — Holmgren / Williams / Pokusevski rotation was unsettled; sources should disagree. If all 4 agree exactly, suspicious.

4. **Position normalization**: spot-check 20 players across sources, confirm position assignments match.

5. **Coverage check**: each snapshot should have ≥120 starters (30 teams × 5 positions, allowing for some teams playing small ball). Significantly fewer = parser broken.

## Anti-patterns

- Don't fetch player profile pages from depth chart sources — extract everything from the depth chart page itself
- Don't infer depth_order from "minutes" data on the same page (some sources show MPG alongside) — depth_order is the analyst's stated rotation, MPG is observed; keep them separate
- Don't try to scrape paywalled premium depth chart features (RotoWire premium, FantasyPros premium) — basic free version is sufficient
- Don't deduplicate across sources during ingestion — keep per-source rows for the disagreement signal

## CLI structure

```
python -m fetchers.depth_charts snapshot                     # all 4 sources, today's date
python -m fetchers.depth_charts snapshot --source espn       # single source
python -m fetchers.depth_charts backfill --start 2023-09-01 --end 2024-04-15 --weekly
python -m fetchers.depth_charts compute_disagreements        # rebuild disagreements parquet
python -m fetchers.depth_charts validate
```

## Auth

None required. All sources are public.

## Estimate

Build effort: 8-12 hours for 4-source parser + Wayback backfill + disagreement computation. The HTML parsing is moderate complexity per source (each has its own table layout); the player name → nba_api_id resolution layer is reusable from other fetchers.

## Reporting

After each snapshot/backfill: row counts per source × snapshot, coverage gaps, disagreement statistics (mean disagreement_score, top 10 contested rotations).

## What this unlocks downstream

- Depth_order as a categorical feature on the v6 MPG model (1=starter → high MPG prior, 4+=deep bench → low MPG prior)
- Disagreement_score as an uncertainty multiplier — high disagreement = wider posterior on MPG
- Cross-validation against Vegas implied MPG: where they agree, high confidence; where they disagree, investigate
- Historical backfill for 23-24 backtest validation: did multi-source depth chart at 2023-10-23 predict actual 23-24 MPG better than naive?
