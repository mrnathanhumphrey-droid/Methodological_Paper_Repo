# Code Brief: International + G-League Stats — Rookie Career Prior

## Why this exists

Some rookies skip the NCAA path entirely:
- **International leagues**: EuroLeague, Spanish ACB, French LNB, Australian NBL, Israeli league (Maccabi), Greek league
- **G-League** (NBA's own developmental league)
- **Overtime Elite / NBA Academy** (newer pathways)
- **Direct from high school** (rare, mostly pre-2006 rule change but Mikey Williams, etc.)

Same v6 architecture as veterans — we just need pre-NBA stats as the "career prior" data slot. NCAA-only stats fetcher (separate brief) covers ~70% of rookies; this fills the remaining ~30%.

Notable rookies who went non-NCAA in recent classes:
- Wembanyama (2023): Metropolitans 92 — French LNB
- Bilal Coulibaly (2023): Metropolitans 92 — French LNB
- Scoot Henderson (2023): G League Ignite
- Amen + Ausar Thompson (2023): Overtime Elite
- LaMelo Ball (2020): Australian NBL
- RJ Hampton (2020): Australian NBL
- Killian Hayes (2020): German BBL (Ratiopharm Ulm)
- Théo Maledon (2020): French LNB
- Kostas Antetokounmpo, Goran Dragić, Luka Doncic — historical international examples

## Sources by league

### G-League (highest priority — easiest fetch)

`nba_api` Python library — already in our venv.

Endpoint: `LeagueGameLog(league_id_nullable='20', season=...)` for game logs.
Plus: `PlayerGameLog(league_id_nullable='20', player_id=..., season=...)` for per-player aggregation.

The `league_id` value `'20'` is G-League. G-League data is in stats.nba.com just like NBA.

Backfill seasons: 2014-15 through 2024-25.

### EuroLeague

`https://www.euroleaguebasketball.net/euroleague/stats/` — has a public stats page with downloadable data per season.

Backup source: `https://www.basketball-reference.com/euro/euroleague/` — Sports-Reference's EuroLeague archive (cleaner table format but lags 1-2 seasons behind real-time).

### Spanish ACB

`https://www.acb.com/estadisticas-individuales/` — Spanish league official stats.

Or `https://www.basketball-reference.com/euro/spain/` — Sports-Reference aggregation.

### French LNB Pro A (Wemby, Coulibaly, Maledon's league)

`https://www.lnb.fr/elite/statistiques/individuelles/` — French league official stats.

Or `https://www.basketball-reference.com/euro/france/`.

### Australian NBL (LaMelo, RJ Hampton, etc.)

`https://nbl.com.au/stats` — official.

### Israeli BSL (Maccabi etc.)

`https://www.basket.co.il` — Hebrew, but stats tables are language-neutral.

### Overtime Elite + NBA Academy

`https://overtimeelite.com/stats` — Overtime Elite official.

NBA Academy: stats often unavailable publicly; may need to skip these prospects (rare cohort, ~5 per draft class).

## Recommended approach: aggregator-first

Sports-Reference has a meta-archive at `https://www.basketball-reference.com/international/` covering most major leagues with consistent schema. Use this as the primary scrape, fall back to per-league official sites only where Sports-Reference is missing recent seasons.

## What to extract

Per player × season × league:

```
nba_api_id          int64?  -- resolved post-fetch
player_name_raw     string
league              string  -- "g_league" / "euroleague" / "acb" / "lnb_france" / "nbl_australia" / "bsl_israel" / "ote" / "nba_academy"
team               string  -- e.g. "Metropolitans 92" / "Real Madrid" / "G League Ignite"
season             string   -- "2022-23"
gp                  int
gs                  int?    -- if available
min_total           int
mpg                 float
PTS, REB, AST, STL, BLK, TOV, FGM, FGA, FG3M, FG3A, FTM, FTA, OREB, DREB, PF  int
fg_pct, fg3_pct, ft_pct  float
per40_*  float (derived)
fetched_at_utc      timestamp
source              string  -- "sports_reference" / "g_league_nba_api" / "euroleague_official" / etc.
source_url          string
```

## Output

`data/parquet/international_player_seasons.parquet` — one row per (player, season, league).

`data/parquet/international_to_nba_rookie_join.parquet` — derived view, last pre-NBA season for each rookie:
```
nba_api_id, league, last_pre_nba_season, last_team, 
per40_PTS, per40_REB, per40_AST, per40_STL, per40_BLK, per40_TOV,
3pct_volume, efg_pct, usg_pct (if computed), years_pre_nba
```

## Volume

- G-League: ~150 rookies who came through G-League pathway over 11 seasons. Most also have ~1 season of stats. ~150 rows.
- EuroLeague + ACB + LNB + NBL + BSL: ~60-80 international rookies. ~150-200 rows (some played multiple international seasons).
- OTE + NBA Academy: ~10-20 players. Limited data.

Total: ~400-500 rows. Tiny.

## Concurrency / parallelism rules

Different sources have different rules. **Run sources in parallel since they're separate domains, but each source uses its own throttle**:

- **G-League via nba_api**: SAME stats.nba.com endpoint. Use 1 worker, 1 req/2sec, share the throttle pool with any other nba_api calls. Don't run alongside NBA box score backfills.
- **Sports-Reference international**: 1 worker, 1 req/6 sec (same as NCAA brief — Sports-Reference is strict).
- **EuroLeague official**: 1 worker, 1 req/2sec, polite UA.
- **ACB / LNB / NBL / BSL official sites**: 1 worker each, 1 req/3sec.
- **Overtime Elite**: 1 worker, 1 req/2sec.

Three independent worker domains can run in parallel (Sports-Reference, EuroLeague, NBA G-League) without crossing rate limits.

Total runtime: ~30 minutes for full backfill if run in parallel; ~1.5 hours if sequential.

## Player resolution

Hardest source. International player names often have:
- Multiple transliterations (Doncic / Dončić)
- Different naming order (Asian / Eastern European naming conventions)
- Suffix differences (Antetokounmpo Jr. vs III)
- Team-context disambiguation needed

Resolution approach:
1. Cross-reference `nba_draft_data.parquet` for `pre_nba_team` and `pre_nba_team_type=international` or `pre_nba_team_type=g_league`
2. Match `nba_draft_data.player_name_raw` against international parquet `player_name_raw`
3. Use `pre_nba_team` as disambiguation key (e.g., "Metropolitans 92" matches Wembanyama's draft team)
4. Use draft year to filter to the relevant season
5. Manual review of unmatched: write to `international_unresolved.parquet`

Expected resolution rate: 80-85% (lower than NCAA due to name transliteration challenges).

## Validation

1. **Wembanyama 2022-23**: Metropolitans 92 (French LNB), should show ~21 PPG, ~10 RPG, ~3 BPG over ~34 games. Pace-adjusted (slower than NBA).

2. **Scoot Henderson 2022-23**: G League Ignite, ~17 PPG, 5 RPG, 6 APG over ~19 games.

3. **LaMelo Ball 2019-20**: Australian NBL (Illawarra Hawks), ~17 PPG, ~7 RPG, ~7 APG over ~12 games before injury.

4. **Coulibaly 2022-23**: Metropolitans 92 alongside Wemby, much smaller role (~10 PPG).

5. **Coverage check per league**: G-League should have ~150 NBA-bound players over 11 years. EuroLeague should have ~30-40.

## Anti-patterns

- Don't aggregate stats across leagues for one player who played in multiple (e.g., a guy who played EuroLeague, then ACB, then NBA) — keep separate league rows
- Don't include exhibition games / preseason from international leagues (out of scope)
- Don't try to scrape FIBA international team stats (national team play, completely different competition format)
- Don't worry about non-NBA-bound international players — only fetch players who appear in our `nba_career_season_totals_rs.parquet` or `nba_draft_data.parquet`
- Don't try Hebrew/non-Latin name normalization perfectly — capture raw, resolve manually for the residual

## CLI

```
python -m fetchers.international_stats backfill --leagues g_league,euroleague,acb,lnb,nbl,bsl,ote
python -m fetchers.international_stats fetch --league g_league --start 2014-15 --end 2024-25
python -m fetchers.international_stats resolve --rebuild
python -m fetchers.international_stats validate
```

## Auth

None for any source. All public.

## Estimate

Build effort: 12-18 hours (multi-source parsers + name resolution complexity). Each league site has different DOM, but Sports-Reference covers most cleanly.

Backfill runtime: 30 min (parallel) to 1.5 hr (sequential).

## Reporting

- Row counts per league × season
- Resolution rate per league (expect 80-95% on G-League which uses NBA player IDs natively, 70-85% on international with name resolution)
- Sample 20 unresolved international names for manual review
- Spot-check headline rookies as listed in validation criteria

## Downstream integration

Once landed, both this and the NCAA brief feed into a unified rookie career-prior table. v6's existing logic that uses `career_season_totals_rs` for veteran priors gets a parallel rookie path:

```
veteran_career_prior      (from nba_career_season_totals_rs) — existing
rookie_ncaa_career_prior  (from ncaa_player_seasons)         — new
rookie_intl_career_prior  (from international_player_seasons) — new
```

Then v6 MPG model applies same Bayesian blend logic, with the rookie pathway substituting NCAA/international per-40 for NBA career per-36 in the prior calculation. Same architecture, different data plug.
