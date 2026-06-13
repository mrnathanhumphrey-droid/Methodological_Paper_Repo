# Code Brief: Pro Sports Transactions DB — NBA Injury + Transaction Backfill

## Why this exists

The NBA projection engine at `D:\NBA Projections` lacks structured player injury history and transaction data. Our existing `injuries.parquet` and `transactions.parquet` are empty schemas. We need this data to:

1. Build a primary-source-derived chronic injury feature (replacing the current weak games-missed-% formula)
2. Have authoritative trade/signing dates for backtest validation of role-change signals
3. Categorize chronic injury risk by type (structural / muscular / durability) — Wonka's hand-curated tier system shows the categorical distinction matters

Pro Sports Transactions DB is the canonical free public source. It's structured, well-maintained, and goes back to 1990+.

## Source

`https://www.prosportstransactions.com/basketball/Search/Search.php`

The site has a search form that accepts:
- Sport: Basketball (already filtered if you go through `/basketball/`)
- Date range: from / to (mm/dd/yyyy)
- Player name (optional — leave blank for all)
- Team (optional — leave blank for all)
- Transaction Category — checkboxes for: Injuries, Movement, Personal, Disciplinary, Legal

Form submit → paginated HTML table with columns: Date, Team, Acquired, Relinquished, Notes.

The "Acquired" column lists players gaining a status (e.g., "activated from IL," "signed by team"). The "Relinquished" column lists players losing a status (e.g., "placed on IL," "waived"). The "Notes" column has injury type / contract terms in free-text.

## Backfill scope

**Date range**: October 2014 — December 2025 (10+ NBA seasons).

**Two distinct fetches**, output to two parquets:

### Fetch 1: Injuries

Search filter: only "Injuries" category checked.

Output: `data/parquet/pro_sports_injuries.parquet`

Schema:
```
event_id            string  -- hash of (date + player + team + notes_first_30_chars), used for dedup
event_date          date
team_abbr           string  -- 3-letter; will need translation from full team name
player_name_raw     string  -- as listed on the site (e.g., "DeMarcus Cousins")
nba_api_id          int64?  -- resolved via name → metadata join, NULL if unmatched
acquired_status     string?  -- "activated from injured list" / "returned to lineup" / NULL
relinquished_status string?  -- "placed on IL" / "DTD" / "out indefinitely" / NULL
notes_raw           string  -- the full Notes column text
body_part           string?  -- parsed: knee, ankle, achilles, back, hamstring, foot, hand, etc.
injury_type         string?  -- parsed: surgery, sprain, strain, soreness, fracture, bruise, etc.
severity            string?  -- parsed: out-for-season, indefinite, DTD, GTD, longterm, surgery
return_date_estimate date?  -- parsed when explicit (e.g., "expected to return Nov 15")
fetched_at_utc      timestamp
```

Volume estimate: ~3,000 injury events per season × 11 seasons = ~33,000 rows.

### Fetch 2: Transactions (Movement category)

Search filter: only "Movement" category checked.

Output: `data/parquet/pro_sports_transactions.parquet`

Schema:
```
event_id            string  -- hash of (date + player + team + notes_first_30_chars)
event_date          date
team_abbr           string
player_name_raw     string
nba_api_id          int64?
acquired_status     string?  -- "signed", "claimed off waivers", "traded to" / NULL
relinquished_status string?  -- "waived", "traded from", "released" / NULL
notes_raw           string
transaction_type    string?  -- parsed: trade / signing / waiver / two-way / 10-day / sign-and-trade / etc.
counterparty_team   string?  -- for trades, the other team involved
contract_terms      string?  -- parsed when present: years, dollars, options
fetched_at_utc      timestamp
```

Volume estimate: ~1,000 transactions per season × 11 seasons = ~11,000 rows.

## Site structure / how to scrape

Each search query returns a paginated HTML table. Pagination uses `start` query parameter, default page size is 25 rows.

**Example search URL** (injuries Oct 1 2014 - Dec 31 2014):
```
https://www.prosportstransactions.com/basketball/Search/SearchResults.php?
  Player=&Team=&BeginDate=2014-10-01&EndDate=2014-12-31
  &ILChkBx=yes
  &Submit=Search
  &start=0
```

Iterate `start=0, 25, 50, ...` until results page returns empty table.

**Suggested chunking**: Search 6-month windows (e.g., 2014-10-01 to 2015-03-31, then 2015-04-01 to 2015-09-30, etc.) to keep each search under ~5000 results, which translates to ~200 paginated requests per chunk. 22 chunks × 200 pages = ~4,400 requests total.

## Throttling

The site is robust but has no published rate limit. Polite practice: **1 request per 2 seconds**. At that pace:
- 4,400 requests × 2 sec = ~2.5 hours total backfill

No auth required. Use User-Agent: `NBAProjections-DataBackfill/1.0 (research; nathanhumphrey@gmail.com)` — being identifiable is courteous.

## Local extraction (after fetch, no API cost)

After raw HTML rows are stored, run a parsing pass to populate the structured columns:

### Body part extraction (regex over `notes_raw`)

Match common body part keywords:
```
knee, ankle, achilles, foot, toe, calf, shin, hamstring, quad(riceps)?, 
groin, hip, back, spine, lumbar, neck, shoulder, elbow, wrist, hand, 
finger, thumb, head, concussion, illness, COVID, oblique, ribs?, 
abdom(en|inal), eye, jaw, nose, face
```

Take the first match. Multi-injury entries (rare) are acceptable as: store the first, keep raw notes for re-parse later.

### Injury type extraction

Match common injury type keywords:
```
surgery, surgical, sprain(ed)?, strain(ed)?, soreness, fracture, broken,
bruise, contusion, tear, torn, ruptured?, dislocat(ed|ion), inflammation,
tendinitis, tendinopathy, impingement, stinger, sprained, hyperextended
```

### Severity extraction

Look for severity keywords:
```
out for season → severity = "out_for_season"
out indefinitely / no timeline → "indefinite"
day-to-day | DTD → "day_to_day"
game-time decision | GTD → "game_time_decision"
expected to return [date] → severity = "short_term"
will miss [N] (weeks|months) → "medium_term" if weeks, "long_term" if months
surgery → "surgery"
```

### Return date parsing

Match patterns like:
- "expected to return Oct 15"
- "out until November"
- "will be reevaluated in 4-6 weeks"

Convert to absolute date based on `event_date + relative_offset`. For ambiguous month names without year, use event_date's year.

### Player ID resolution

After raw fetch, run name resolution against `data/parquet/player_metadata_enriched.parquet`. Since names can match multiple players across history (e.g., multiple "James Johnson" players have existed), use:

1. Exact name match → use that nba_api_id if unique
2. Last-name + team match → if the team_abbr matches a player's career history at that date
3. If still ambiguous: leave nba_api_id = NULL, log to `data/parquet/pro_sports_unresolved.parquet` for manual review

Expected unresolved rate: <5% on injuries, <2% on transactions.

## Validation criteria

After backfill completes, spot-check:

1. **Joel Embiid**: should have 50+ injury events from 2014-15 forward. Body parts should include knee, foot, back. At least one event with severity="surgery".

2. **Klay Thompson ACL**: should have an event around June 2019 with body_part="knee", injury_type="torn"/"surgery", severity="out_for_season".

3. **Kyrie Irving Brooklyn → Dallas trade**: in transactions, an event around 2023-02-06 with transaction_type="trade", from BKN to DAL.

4. **Damian Lillard POR → MIL trade**: 2023-09-27 with from POR to MIL.

5. **2023-24 Joel Embiid meniscus**: an event around 2024-01-30 with body_part="knee" or "meniscus", severity="out_for_season" or "surgery".

6. **Coverage**: each season-year should have ~3,000 injury events and ~1,000 transactions. Significantly fewer indicates a missing date range.

## Anti-patterns

- Don't fetch other sports (NHL, MLB, NFL) — site has them, we don't need them
- Don't fetch Personal/Disciplinary/Legal categories — out of scope for projection
- Don't try to access player profile pages — search-result table has all the data
- Don't deeply parse contract dollar amounts — `contract_terms` raw is fine, parse only year/option counts if present
- Don't follow embedded links from the Notes column to other articles — out of scope

## CLI structure

```
python -m fetchers.pro_sports_transactions backfill --start 2014-10-01 --end 2025-12-31 --category injuries
python -m fetchers.pro_sports_transactions backfill --start 2014-10-01 --end 2025-12-31 --category movement
python -m fetchers.pro_sports_transactions extract  # run local parsing pass on already-fetched raw rows
python -m fetchers.pro_sports_transactions resolve  # run name → nba_api_id resolution pass
python -m fetchers.pro_sports_transactions validate  # run spot-check validations
```

Idempotent: re-running `backfill` should detect existing event_ids and skip. Use a `--force` flag to override and re-fetch.

## Output

Two parquets at `D:\NBA Projections\data\parquet\`:
- `pro_sports_injuries.parquet`
- `pro_sports_transactions.parquet`

Plus the unresolved-mentions parquet for manual review.

## Estimate

Build effort: 8-12 hours for clean implementation (HTML scraping is the easy part; the regex parsers and name resolution are the time sink).

Backfill runtime: ~2.5 hours for the actual fetch, additional ~10 minutes for the local extraction passes.

Free of any cost — site has no paywall and no API charges.

## Reporting on completion

- Total rows captured per parquet
- Per-season row counts (sanity check coverage)
- Body-part extraction quality: % of injury rows with body_part populated (target >85%)
- Severity extraction quality: % of injury rows with severity populated (target >70%)
- Player ID resolution rate: % rows with nba_api_id non-null (target >95%)
- Sample 30 rows per parquet for manual quality review
- Any failed date ranges or pages with reason
