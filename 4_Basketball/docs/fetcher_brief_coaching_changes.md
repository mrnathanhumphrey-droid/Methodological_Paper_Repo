# Code Brief: Coaching Change Data — NBA Head Coach by Team x Season

## Why this exists

Career-data-invisible signal. A new head coach almost always means rotation
philosophy changes. Career data shows a player's MPG under their LAST coach.
It can't see the new coach's preferences. From the per-stat residual diagnostic
on v6 23-24 ship, `offseason_traded` x PTS clears SNR 3.92 because trade is a
roster event career data can't see. New head coach is the same kind of event
for the players who didn't move teams.

Per Desktop's prioritization (2026-05-01), this is the #2-priority structural
candidate after roster composition. Smaller cohort (3-6 teams change coaches
per year) but cleaner signal — every player on a coaching-change team gets a
flag, not just those whose specific position-group churned.

## Scope

Backfill: 2014-15 through 2024-25 (matches our box-score / preseason coverage).

For each team x season:
  - head_coach_name
  - head_coach_id (Basketball-Reference unique slug, e.g. `popovgr01`)
  - hire_year (when did they take over THIS team)
  - prior_team (what team did they coach before, if any; else null)
  - is_new_coach_this_season (boolean: head coach != prior season's head coach for this team)
  - coach_archetype (optional, mostly None — see below)

For each coach who has appeared:
  - career_seasons_as_hc
  - career_avg_bench_minutes_used  (summed bench mpg across rosters; rough rotation-depth metric)
  - prior_stops_count

## Source: Basketball-Reference

Coach pages: `https://www.basketball-reference.com/coaches/{coach_slug}.html`
Each page has a season-by-season table: team, season, W, L, playoffs.

Team coach pages: `https://www.basketball-reference.com/teams/{TEAM}/{YEAR}.html`
Each team-season page has a "Coaches" line in the header listing the head coach.

The cleaner approach is **scrape team-season pages**, since those give us
the head_coach assignment per team x season directly without having to
join across coach career tables.

For teams with mid-season coaching changes (e.g. interim coaches), the page
lists multiple coaches. We capture the coach who finished the season as the
"of-record" head coach. Mid-season coaching changes themselves are a
separate signal worth flagging.

## Concurrency / politeness

Basketball-Reference is strict about scraping rate. Use:
- 1 worker
- 1 request per 6 seconds (matches existing NCAA / international briefs)
- Polite UA: `NBAProjectionsResearch/1.0 (educational, contact: ...)`
- Respect 429s with exponential backoff
- Do not parallelize across separate domains within Sports-Reference network

Volume: 30 teams x 11 seasons = 330 page fetches.
At 6 sec each = ~33 minutes wall time. Single run, one-time backfill.

## What to extract per team-season page

```
team_abbr           string  -- e.g. "BOS", "LAL"
season              string  -- "2014-15"
head_coach_name     string  -- "Brad Stevens"
head_coach_slug     string  -- "stevebr99" (Basketball-Reference unique)
games_coached       int     -- 82 if no mid-season change; else <= 82
mid_season_change   bool    -- if multiple HCs that season
prior_hc_name       string  -- if mid-season change, who was fired
fetched_at_utc      timestamp
source_url          string
```

## Output

`data/parquet/coach_team_season.parquet` — primary table, 30 x 11 = 330 rows
plus a few extras for mid-season-change seasons.

Derived view: `data/parquet/coaching_change_flags.parquet`:

```
team_abbr           string
season              string  -- the season we're flagging (e.g., 2023-24 if HC differs from 22-23)
new_coach_this_season   bool
new_coach_name      string
prior_coach_name    string
new_hire_type       enum   "first_time_hc" / "return_after_break" / "lateral_move_from_other_team" / "promoted_from_assistant"
fetched_at_utc      timestamp
```

## Player-flag join (downstream use)

For consumption by the v6.1 ablation harness:

```
player x season -> on_team_with_new_coach (bool) =
    nba_api_id JOIN coach_team_season on team_abbr+season,
    where coaching_change_flags.new_coach_this_season is True
```

This becomes a class column for the noise-floor diagnostic, alongside
`offseason_traded`, `position`, `age_bucket`, etc. Hypothesis: SNR >= 1.5 on
PTS, AST, or MPG residual.

## Validation spot-checks

- 2014-15 GSW HC = "Steve Kerr" (was Mark Jackson 13-14 -> coaching change yes)
- 2018-19 LAL HC = "Luke Walton" -> Frank Vogel 19-20 (change)
- 2023-24 MIL HC = Adrian Griffin (initial), replaced mid-season by Doc Rivers
- 2024-25 LAL HC = JJ Redick (Darvin Ham was 23-24)
- Pop should appear as SAS HC every season 14-15 through 22-23

## Fetcher CLI

```
python -m fetchers.coaching_changes backfill --start 2014-15 --end 2024-25
python -m fetchers.coaching_changes fetch --team BOS --season 2023-24
python -m fetchers.coaching_changes derive-flags --rebuild
python -m fetchers.coaching_changes validate
```

## Auth

None. Public site.

## Estimate

Build effort: ~3-4 hours including parser, ID resolution to nba_api_id, output
schema, validation harness.

Backfill runtime: ~33 min single-run.

## Anti-patterns

- Don't try to parse the full coach-career page (much more complex DOM).
  Team-season pages are cleaner.
- Don't include assistant coaches — out of scope.
- Don't normalize coach names creatively (Brad Stevens -> Bradley Stevens).
  Use the BR slug as the unique key, surface the displayed name as `head_coach_name`.
- Don't count interim coaches as "new coach" if they were already on staff
  (those are continuity hires, not philosophical resets). Use the
  `new_hire_type` enum to flag external lateral moves separately.
- Don't aggregate stats across mid-season change seasons before testing —
  the residual diagnostic should treat them as their own micro-class.

## Reporting

After backfill, report:
  - Row counts per season
  - Number of coaching changes per season (expected: 3-8 per year)
  - Validation spot-check pass/fail for the 5 cases above
  - Sample of mid-season changes captured (expected: ~2-4/year)

## Downstream consumer

This brief feeds into the per-stat residual diagnostic at
`scripts/expanded_class_diagnostic.py`. Once landed, add `coaching_change_flag`
and `mid_season_coaching_change` as additional class columns. Re-run the
SNR sweep. Test top-1 inclusion at SNR>=1.5.

If `coaching_change_flag x AST` (or x PTS) clears SNR>=1.5, add to the v6.1
offset table at the next ship cycle.

## Why not Spotrac / news scraping for this

Spotrac doesn't have head-coach data structured. News scraping coaching changes
is reactively easy (announce dates are public) but produces a less-clean schema
than Basketball-Reference's authoritative team-season pages. Stick with BR for
historical coverage; pivot to news only for forward-tracking of in-season
firings.
