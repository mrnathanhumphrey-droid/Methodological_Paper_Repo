# Code Brief: Vegas Markets — Team Markets + Player Props

## ⚠️ CRITICAL ARCHITECTURE RULE — READ FIRST

The distinction is **target-leaking vs structural**, not Vegas-vs-non-Vegas. Two classes of Vegas data with different rules:

### CLASS A: TEAM-LEVEL DERIVATIVE SIGNAL (safe to ingest as input feature)

These reflect team strength, matchup quality, schedule difficulty — they don't directly predict the player-level stats we're modeling. Safe to use as features in v6:

- ✅ **Team season win totals** (over/under regular-season wins)
- ✅ **Game point spreads** (team-level matchup signal)
- ✅ **Implied team totals** (derivative of team strength + matchup)
- ✅ **Conference / division / championship futures** (long-term team strength)

Logic: ingesting "Boston is projected for 58 wins" is structurally similar to ingesting any other team strength estimate. It's a calibrated team rating, not a player projection.

### CLASS B: PLAYER-LEVEL DIRECT PROJECTION (target leakage — VALIDATION ONLY)

These are direct projections of the same stats we're modeling. Ingesting them as input features collapses our independence and our ability to beat the market:

- ❌ **Player season-long PPG / RPG / APG / 3PM / MPG over/unders** — direct target leakage
- ❌ **Awards odds (MVP / ROY / DPOY / 6MOY / All-NBA)** — aggregated player evaluation = player-level target leakage
- ❌ **Anytime / first-basket / specific-game player props** — derivative player prediction

**Permitted uses for Class B**:
- ✅ Validation: compare v6 MAE vs Vegas-implied MAE on actuals
- ✅ Divergence detection: surface (player, stat) where v6 disagrees with market by >Xσ — these become tradable signals for the betting layer
- ✅ Calibration sanity check: flag absurd v6 outputs that diverge from market by huge magnitudes (likely bugs)

**Hard rule**: Class B data lands in its own parquets that are NOT consumed by v6 projection code or by the audit-CSV export to Wonka. Only validation/analysis tools and the eyes-only betting layer read Class B parquets.

### The principle

Depth charts say "Flagg is the projected starter" — structural fact, safe to ingest.
Vegas player MPG props say "the market thinks Flagg plays 31.5 MPG" — direct projection of our target, target leakage.

Apply this lens to every external data source. Structural / derivative / health → safe. Direct player-stat projection → target leakage.

## Why this exists

Sportsbook player props are the **single highest-density curation signal available**. The market for "Cooper Flagg PPG over/under 17.5" reflects every coach quote, training camp report, depth chart speculation, and beat writer note — priced by sharps with money on the line. Ingesting these gives us the analyst-curation aggregate without ingesting any individual analyst projection.

The NBA projection engine at `D:\NBA Projections` will use Vegas player props as:
1. A consensus-MPG anchor that's independent of FantasyPros / Hashtag
2. A measured-confidence signal (line movement, juice asymmetry indicate market certainty)
3. A backtest validation target for our own projections (did we beat the market on PPG O/U?)

## Source priority

### Primary sources (in order)

1. **The Odds API** (`https://the-odds-api.com/`) — paid API but reasonable. ~$30-50/month for 500 requests/day. Covers DraftKings, FanDuel, BetMGM, ESPN BET, Caesars across season-long player props. CLEANEST option.

2. **Action Network** (`https://www.actionnetwork.com/nba/odds`) — free public web scrape, good coverage of player props and awards. Updated throughout offseason and preseason.

3. **OddsShark** (`https://www.oddsshark.com/nba`) — public, free. Has season-long futures (MVP odds, win totals) and limited player props.

4. **Sportsbook Review** (`https://www.sportsbookreview.com/betting-odds/nba-basketball/`) — public, free. Has historical line tracking which is unique value.

### Direct sportsbook sites (fallback if APIs/aggregators fail)

- DraftKings: `https://sportsbook.draftkings.com/leagues/basketball/nba` → futures/awards/season-props sections
- FanDuel: `https://sportsbook.fanduel.com/navigation/nba` → similar layout
- BetMGM: `https://sports.betmgm.com/en/sports/basketball-7/betting/usa-9`

**TOS warning**: direct sportsbook scraping is in a legal gray area. They have ToS prohibiting automated access. The Odds API is the legal/commercial path. If forced to scrape direct, throttle aggressively (1 req/10sec) and don't republish the data.

## What to scrape

### A. Season-long player props (highest priority)

Per player, capture:
- **Points per game (PPG) over/under** — the killer signal for our purposes
- **Rebounds per game (RPG) over/under**
- **Assists per game (APG) over/under**
- **3-pointers made per game (3PM) over/under**
- **Steals + Blocks per game over/under** (often listed combined)
- **Minutes per game (MPG) over/under** — when offered (less common but ESPN BET sometimes has it)
- **Fantasy points per game over/under** (when offered)

For each prop, capture:
- The line (e.g., 17.5 PPG)
- The over juice (e.g., -110)
- The under juice (e.g., -110)
- Implied probability (computed from juice)
- Implied "fair line" (the line the market would set if juice were balanced)

### B. Team futures

- Win totals (over/under regular season wins)
- Division odds
- Conference championship odds
- NBA championship odds
- Make/miss playoffs odds

These provide team-strength priors that affect player MPG indirectly (good teams have shorter rotations).

### C. Awards (these reveal individual-player expectation distributions)

- MVP odds per player
- Rookie of the Year odds (especially valuable for projecting rookies)
- Defensive Player of the Year odds
- 6th Man of the Year odds (signals expected bench role)
- All-NBA odds
- All-Star odds

Award odds for non-favorites carry information: a +5000 6MOY candidate is implicitly projected as a key bench player; a +200 6MOY candidate is the consensus elite bench player. This translates to MPG expectations.

### D. Game-line opening markets (preseason / early-season only — secondary priority)

Once preseason games begin, opening point spreads on individual games encode market team-strength assessments. Lower priority than season-long props but useful corroboration.

## Backfill

For 2023-24 season retrospectively (for backtest):
- The Odds API has historical data going back to ~2020 (paid tier feature)
- Action Network has limited archive
- Sportsbook Review has the best historical line database (the most useful retrospective source)
- Wayback Machine snapshots of all of the above

For each backfill year, capture three snapshots:
- Late September (right before season starts) — opening lines
- Early November (after ~10 games) — adjusted lines
- All-Star break — mid-season recalibration (less useful for our preseason use case but interesting for in-season comparisons)

For 26-27 forward, scrape live with weekly snapshots from late August through opening night.

## Output

`data/parquet/vegas_player_props.parquet`:
```
snapshot_date       date
season              string  -- e.g. "2023-24"
sportsbook          string  -- "DraftKings" / "FanDuel" / "BetMGM" / "ESPN BET" / "Caesars"
nba_api_id          int64?  -- resolved from player_name
player_name         string
prop_type           string  -- "PPG" / "RPG" / "APG" / "3PM" / "STL_BLK_combined" / "MPG" / "FPPG"
line                float
over_juice          int     -- e.g. -110, +120
under_juice         int
implied_over_prob   float
implied_under_prob  float
fair_line           float   -- adjusted for juice asymmetry
volume_indicator    string?  -- "high" / "medium" / "low" if site reports it
opened_line         float?  -- for line movement tracking
opened_at_utc       timestamp?  -- when this line first appeared
fetched_at_utc      timestamp
source_url          string
```

`data/parquet/vegas_team_futures.parquet`:
```
snapshot_date       date
season              string
sportsbook          string
team_abbr           string
market_type         string  -- "win_total" / "division_odds" / "conference_champ" / "nba_champ" / "playoff_yes_no"
line                float?  -- for win_total
odds                int     -- American odds (+150 / -200)
implied_prob        float
fetched_at_utc      timestamp
source_url          string
```

`data/parquet/vegas_awards.parquet`:
```
snapshot_date       date
season              string
sportsbook          string
award_type          string  -- "MVP" / "ROY" / "DPOY" / "6MOY" / "All-NBA" / "All-Star"
nba_api_id          int64?
player_name         string
odds                int
implied_prob        float
implied_share       float   -- normalized share (raw probs sum to >100% due to juice; normalize)
fetched_at_utc      timestamp
source_url          string
```

## Volume estimate

- Player props: ~200 players × 5 prop types × 4 sportsbooks = ~4,000 rows per snapshot
- Team futures: 30 teams × 5 markets × 4 sportsbooks = ~600 rows per snapshot
- Awards: 6 awards × ~30 candidates × 4 sportsbooks = ~720 rows per snapshot
- Per snapshot: ~5,300 rows

For 26-27 with weekly snapshots from Aug-Apr (~36 weeks): ~190,000 rows total. Tiny dataset.

## Concurrency / parallelism rules

This fetcher targets multiple independent sources. **Run them in parallel where possible without tripping rate limits or IP bans.** Specifically:

- **The Odds API**: single concurrent worker. The plan-based rate limit (500 req/day = ~6/min sustained) means parallel workers don't help and risk hitting daily cap faster.
- **Action Network**: max 2 concurrent workers, each at ≤1 req/sec.  Polite UA header.
- **OddsShark**: max 1 worker at 1 req/2sec.
- **Sportsbook Review**: max 1 worker at 1 req/2sec.
- **Direct sportsbook scrapes** (DraftKings/FanDuel/BetMGM): max 1 worker per book, ≥10 sec between requests, randomize jitter ±2 sec to avoid detectable patterns. Rotate User-Agent headers from a small pool.

**Aggregate parallelism**: 4-5 sources can run simultaneously across separate workers since they're independent domains. Use Python `asyncio.gather` or `concurrent.futures.ThreadPoolExecutor` with a global rate-limit semaphore PER DOMAIN (not global).

**Backoff on 429 / 503**: exponential with jitter. After 3 consecutive failures from one source, halt that source for the run; continue others.

**IP rotation**: not needed at these polite rates. If you ever hit a ban, that's a sign throttling was too aggressive — fix the rate, don't proxy around the ban.

## Throttling + cost

- **The Odds API**: paid, ~$30-50/month for our volume. Recommended path. Allows 500 req/day on Plus tier; we need ~50 req/day average so ~$30 plan suffices.

- **Action Network direct scrape**: free, rate-limit ~1 req/sec polite. ~30 minutes per snapshot.

- **OddsShark/Sportsbook Review**: free, polite scrape. ~15 min each per snapshot.

- **Direct sportsbooks**: ToS issues, only as fallback.

Total estimated cost: $30-50/month if using The Odds API for current data, free for backfill via Wayback / Sportsbook Review historical.

## Implied probability + fair line math

American odds → implied probability:
- Negative odds (favorite): `prob = abs(odds) / (abs(odds) + 100)`
- Positive odds (underdog): `prob = 100 / (odds + 100)`

Fair line (juice-adjusted): if over and under both have juice (e.g., over -115, under -105), the raw probabilities sum to >100%. Normalize:
- `raw_over = -115 → 0.535`
- `raw_under = -105 → 0.512`
- Total = 1.047 (4.7% juice)
- `fair_over_prob = 0.535 / 1.047 = 0.511`
- `fair_under_prob = 0.512 / 1.047 = 0.489`

The fair line for the underlying stat is the line at which fair probabilities cross 50%. For symmetric stats (rebounds, assists), the listed line IS approximately the fair line if juice is balanced. For asymmetric markets, compute fair line as: fair_line = listed_line + skew_adjustment, where skew_adjustment = (over_juice - under_juice) / 200 in stat units.

## Validation criteria

After each backfill, spot-check:

1. **2023-24 Wembanyama ROY odds**: at season start should be -200 to -300 (heavy favorite). At MVP odds: should appear at +5000 to +10000 (longshot but on the board).

2. **2023-24 Joel Embiid PPG over/under**: should be ~30 PPG at major books. Actual was 34.7, so the market under-projected — captures legitimate market expectation.

3. **2023-24 Trae Young APG over/under**: should be ~10 APG at major books. Actual was 10.8, market was very close — captures consensus.

4. **2023-24 Wins futures**: Boston should have ~55-58 win total. They actually won 64, market under-projected. Validates that win-total signals are real but not always precisely calibrated.

5. **Coverage check**: each snapshot should have ≥150 distinct players in player_props.parquet. Significantly fewer means the scrape missed sections.

## Anti-patterns

- Don't scrape player props that aren't season-long (game-by-game props are different beast, way more volume, less signal for season projection)
- Don't fetch live odds during games (out of scope; we want season-long static markets)
- Don't try to consolidate odds across books into a single "consensus odds" — keep per-book rows so we can analyze book-disagreement signal
- Don't scrape parlays or boost markets (different products)
- Don't store individual bet records or user data (TOS issues, not useful for projection)

## CLI structure

```
python -m fetchers.vegas_markets snapshot --date 2026-09-15  # take snapshot of all markets
python -m fetchers.vegas_markets snapshot --type player_props  # only player props
python -m fetchers.vegas_markets backfill --start 2023-09-01 --end 2024-04-15 --weekly  # historical
python -m fetchers.vegas_markets validate
```

## Auth + rate limiting

- The Odds API: API key in `THE_ODDS_API_KEY` env var
- Action Network/OddsShark/etc.: no auth, polite User-Agent + 1 req/sec throttle
- All fetches: cache aggressively in `data/cache/vegas/` to avoid re-fetching same snapshot

## Estimate

Build effort: 10-15 hours for The Odds API integration + Action Network scrape + parsing + storage. The Odds API does most of the heavy lifting; their docs are clean and the response JSON is structured.

Adding Sportsbook Review historical archive: +5 hours for that scraper (more complex HTML).

## Reporting

After each snapshot: row counts per parquet, sportsbook coverage breakdown, any failed markets, top 10 most-bet props (by volume_indicator if available).

## What this unlocks downstream

The market's PPG / RPG / APG over-unders are *implicit MPG forecasts* via simple math:
- If Cooper Flagg PPG O/U is 17.5 and his expected per-36 PPG is 19, then implied MPG = 17.5 / 19 × 36 = 33.2 mpg
- We can derive market-implied MPG for every player without needing to scrape MPG props directly

This becomes a feature in v6+: blend our projection with market-implied with a tunable weight. The Bayesian framing: market is one expert, v6 is another, blend by confidence. Low-disagreement props (book consensus, low juice) get higher weight; high-disagreement props (book divergence, wide juice) get lower weight.
