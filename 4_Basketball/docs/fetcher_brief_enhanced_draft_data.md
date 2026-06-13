# Code Brief: Enhanced NBA Draft Data + Combine Measurables

## Why this exists

We have `draft_year` and `draft_pick` for 537 of 843 rookies who debuted 2014-2024, but missing:
- `draft_round` (have pick, missing round)
- `drafted_by_team` (which team selected the rookie — important because the original drafted-team often differs from the rookie's first NBA team after trades/draft-night deals)
- All info for 306 undrafted players (currently NaN draft_pick)
- Combine measurables (wingspan, lane agility, vertical) — predictive of NBA outcomes

This is a focused fetch to plug the rookie projection's foundational data gap.

## Sources

### Primary: Basketball-Reference draft pages

URL pattern: `https://www.basketball-reference.com/draft/NBA_{YEAR}.html`

Single page per draft year with structured table containing:
- Round (1 or 2)
- Pick number (1-60 typically; 2024 had only 58 picks, etc.)
- Drafted by team (3-letter abbr)
- Player name
- College / international team / high school
- Years played in NBA
- Career stats summary (we don't need these — we already have them)

Backfill: 2014 through 2025 drafts (12 drafts).

### Primary: Basketball-Reference combine measurables

URL: `https://www.basketball-reference.com/draft/NBA_{YEAR}_combine.html`

Per-rookie measurables from the NBA Draft Combine:
- Height without shoes / with shoes (often 1-2 inches taller than what's listed in metadata)
- Weight
- Wingspan (huge predictor)
- Standing reach
- Body fat %
- Hand length / width
- Lane agility time
- Shuttle run time
- Three-quarter sprint time
- Standing vertical
- Max vertical

Note: not every rookie attends the combine (high lottery picks often skip), so coverage will be ~70-80% per draft year.

### Secondary: NBA.com draft summary

`https://www.nba.com/draft/{year}` — provides the same draft results plus team-trade history (e.g., "Pick 26 originally belonged to NYK but traded to OKC pre-draft"). Useful for the rare case where Basketball-Reference doesn't capture pick trades cleanly.

### Secondary: Undrafted free agent tracking

For the 306 undrafted players we have, we need to capture:
- Year they entered the NBA (`debut_year` already in our metadata)
- Pre-NBA team (G-League, international, etc.)
- Sign date and signing team

Source: combination of Pro Sports Transactions (already queued) + Basketball-Reference player profile pages.

## Output

`data/parquet/nba_draft_data.parquet`:
```
draft_year          int
draft_round         int
draft_pick          int     -- overall pick number, 1-60 typically
drafted_by_team     string  -- 3-letter abbr of team that originally selected
nba_api_id          int64?  -- resolved post-fetch
player_name_raw     string
pre_nba_team        string  -- "Duke" / "Real Madrid" / "G League Ignite" / etc.
pre_nba_team_type   string  -- "ncaa" / "international" / "g_league" / "high_school" / "other"
fetched_at_utc      timestamp
```

`data/parquet/nba_combine_measurables.parquet`:
```
draft_year          int
nba_api_id          int64?
player_name_raw     string
height_no_shoes_inches      float?
height_with_shoes_inches    float?
weight_lbs                  float?
wingspan_inches             float?
standing_reach_inches       float?
body_fat_pct                float?
hand_length_inches          float?
hand_width_inches           float?
lane_agility_seconds        float?
shuttle_run_seconds         float?
three_quarter_sprint_seconds float?
standing_vertical_inches    float?
max_vertical_inches         float?
fetched_at_utc              timestamp
```

`data/parquet/nba_undrafted_signings.parquet`:
```
nba_api_id          int64
debut_year          int
first_team_abbr     string  -- first NBA team they signed with
contract_type       string  -- "two_way" / "exhibit_10" / "standard" / "10_day" / "training_camp"
signing_date        date?
pre_nba_team        string?
pre_nba_team_type   string?
fetched_at_utc      timestamp
```

## Volume

- Drafts: 12 years × ~60 picks = ~720 rows
- Combine: 12 years × ~50 attendees = ~600 rows
- Undrafted: ~300 rows total

Trivial dataset. Single fetch run.

## Concurrency / parallelism rules

Basketball-Reference is robust but rate-limited. **1 request per 3 seconds is polite.** Across 24 pages (12 drafts × 2 pages each: draft + combine), total runtime ~80 seconds at 3 sec/req. Sequential single worker is fine.

Wayback fallback if a Basketball-Reference page is unreachable: same 3 sec throttle.

User-Agent: `NBAProjections-DraftDataFetcher/1.0 (research; mr.nathanhumphrey@gmail.com)`

## Validation

After backfill:

1. **2023 draft**: Wembanyama appears at pick=1, drafted_by=SAS, pre_nba_team="Metropolitans 92 (France)"
2. **2023 draft**: Brandon Miller at pick=2, drafted_by=CHO
3. **2018 draft**: Trae Young at pick=5 — should show drafted_by=DAL (he was drafted by Dallas, traded to Atlanta on draft night for Doncic)
4. **2014 draft**: Nikola Jokic at pick=41, drafted_by=DEN — second-round legend, validation that round-2 picks are captured
5. **Combine 2023**: Wembanyama wingspan should be ~96 inches (he's known for absurd 8-foot wingspan); standing reach ~9'9"
6. **Coverage check**: each draft year should have 60 first-and-second round picks captured. Combine should have 30-50 attendees per year.

## Anti-patterns

- Don't follow per-player profile links from the draft page (we have player metadata already)
- Don't try to extract historical draft trades (other than the original drafted_by) — too noisy, marginal value
- Don't fetch international draft pages (FIBA / European leagues have different drafts; out of scope)
- Don't extract per-game career stats from these tables — we have them already in our career_season_totals parquets

## CLI

```
python -m fetchers.draft_data backfill --start 2014 --end 2025
python -m fetchers.draft_data combine --start 2014 --end 2025
python -m fetchers.draft_data undrafted --backfill
python -m fetchers.draft_data validate
```

## Auth

None. Basketball-Reference is public.

## Estimate

Build effort: 4-6 hours. The HTML tables are very clean and consistent across years. The undrafted-signings derivation is the main complexity — needs cross-reference with Pro Sports Transactions (already queued) and player profile pages.

Backfill runtime: 5-10 minutes total.

## Reporting

Row counts per parquet, missing-data rates per field (especially wingspan and lane_agility — combine attendance varies), spot-check sample of high-pick rookies.
