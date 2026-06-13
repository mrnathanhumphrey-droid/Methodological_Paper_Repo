# 2026 NBA Draft Class — Decomp v0 (2026-06-07)

Pre-draft projections for the 2026 NBA Draft class, using the trained rookie priors pipeline (translation factors + archetype clusters from 2014-24 historical) applied to the 71-prospect 2026 NBA Combine invitee pool.

## Status: v0 (50 of 71 prospects fully projected)

| Cohort | n | Status |
|---|---:|---|
| Upperclassmen (2024-25 NCAA stats on disk) | 50 | ✅ Full projection — archetype + per-stat point + 7-percentile interval + 3 comps |
| Freshmen + intl (2025-26 stats not yet scraped) | 21 | ⚠️ Position-baseline only — flagged `INSUFFICIENT_DATA_NEEDS_2025_26_SCRAPE` |

The 21 unprojected include the top of the 2026 class: **AJ Dybantsa (Anicet Dybantsa)**, **Darryn Peterson**, **Koa Peat**, **Tounde Yessoufou**, **Brayden Burries**, **Christopher Cenac Jr.**, **Cameron Boozer** (not in combine list), **Sergio De Larrea**, **Hannes Steinbach** (intl). For these we need to scrape 2025-26 NCAA + 2025-26 EuroLeague / pro-league stats.

## Top 30 by projected pts/36 (full-data cohort)

| Player | Pos | Archetype | Pts/36 | Reb/36 | Ast/36 | Blk/36 | 3pm/36 | Top comp |
|---|---|---|---:|---:|---:|---:|---:|---|
| Yaxel Lendeborg | PF | Stretch Big | 13.9 | 9.2 | 3.0 | 1.3 | 1.1 | Darius Bazley |
| Keyshawn Hall | SF | Utility Wing | 13.7 | 5.9 | 3.2 | 0.5 | 1.6 | Jaden Ivey |
| Otega Oweh | SG | Utility Wing | 13.7 | 5.4 | 2.4 | 0.5 | 1.6 | Mikal Bridges |
| Isaiah Evans | SG | Wing Shooter | 13.7 | 3.9 | 2.2 | 0.3 | 2.3 | Sam Merrill |
| Richie Saunders | SG | Utility Wing | 13.6 | 5.2 | 2.3 | 0.5 | 1.6 | Mikal Bridges |
| Nick Martinelli | PF | Utility Wing | 13.6 | 5.4 | 2.2 | 0.4 | 1.6 | Jamal Murray |
| Andrej Stojakovic | SF | Utility Wing | 13.5 | 5.1 | 2.3 | 0.7 | 1.6 | Andrew Wiggins |
| Zuby Ejiofor | C | Stretch Big | 13.5 | 8.2 | 1.9 | 1.2 | 1.1 | Darius Bazley |
| Tyler Bilodeau | PF | Utility Wing | 13.4 | 5.5 | 2.4 | 0.5 | 1.6 | Saddiq Bey |
| Bennett Stirtz | PG | Pass-First PG | 13.4 | 4.6 | 4.2 | 0.4 | 1.6 | Spencer Dinwiddie |
| John Blackwell | SG | Utility Wing | 13.3 | 5.4 | 2.5 | 0.4 | 1.6 | Jamal Murray |
| Bruce Thornton | PG | Pass-First PG | 13.3 | 4.5 | 3.3 | 0.4 | 1.6 | Spencer Dinwiddie |
| Tobe Awaka | C | Stretch Big | 13.3 | 10.0 | 1.7 | 1.0 | 1.1 | Jahlil Okafor |
| Ja'Kobi Gillespie | PG | Pass-First PG | 13.3 | 4.3 | 4.4 | 0.4 | 1.6 | Malachi Flynn |
| Peter Suder | SG | Pass-First PG | 13.2 | 5.3 | 4.0 | 0.5 | 1.6 | Desmond Bane |
| Alex Karaban | PF | Stretch Big | 13.2 | 6.9 | 2.3 | 1.2 | 1.1 | De'Andre Hunter |

## Standouts in the full-data cohort

- **Yaxel Lendeborg** (UAB PF transfer): Stretch Big archetype, 9.2 reb/36, 1.3 blk/36, 1.1 3pm/36 — a versatile big who projects to play immediately.
- **Tobe Awaka** (Mary­land C): the cleanest interior rebounder in the projection set — 10.0 reb/36 projected, Jahlil Okafor / Jordan Bell comp.
- **Isaiah Evans** (Duke SG): only Wing Shooter archetype in the full-data top 25 — 2.3 3pm/36, Sam Merrill comp.
- **Bennett Stirtz, Bruce Thornton, Ja'Kobi Gillespie**: three Pass-First PG archetypes all projecting 4+ ast/36, Spencer Dinwiddie / Malachi Flynn comps.
- **Flory Bidunga** (Kansas C, has stats): 3.87 blk/40 in college → projects as Defensive Big archetype.

## Archetype distribution

| Archetype | n | Notes |
|---|---:|---|
| Utility Wing (×3 subclusters) | 51 | Catch-all — the deepest bucket |
| Defensive Big | 11 | Rim protectors |
| Stretch Big | 8 | Versatile bigs |
| Pass-First PG | (rolled into Utility Wing 3) | Stirtz, Thornton, Gillespie |
| Wing Shooter | 1 | Isaiah Evans solo |

## What's missing for v1

To project the 21 elite freshman + intl prospects (the top of the draft), we need:

1. **2025-26 NCAA season stats scrape** — covers Dybantsa (BYU), Peterson (Kansas), Peat (Arizona), Yessoufou (Baylor), Burries (Arizona), Cenac Jr. (Houston), Acuff Jr. (Arkansas), Bidunga sophomore year (was projected from 2024-25 frosh year), Bennett Stirtz / Bruce Thornton (have 2024-25; would want 2025-26 updated)
2. **2025-26 EuroLeague / international refresh** — covers De Larrea, Lopez, Steinbach, Suigo, Yessoufou (Centerville?)
3. **2026 NBA combine measurements** — NBA Stats API still returning invitee names only; measurements may not be live yet (re-fetch periodically until they appear). Currently every prospect projected without combine z-scores.

The pipeline is ready to ingest any of these scrapes the moment they land — just re-run scripts 02 + 03.

## Files

- Candidate pool: `D:/NBA Projections/data/parquet/draft_2026_candidate_pool.parquet`
- Projections: `D:/NBA Projections/data/parquet/draft_2026_projections.parquet` (71 × 102 cols)
- Scripts: `D:/NBA Projections/scripts/draft_prep_2026_0{1,2,3}_*.py`

## Cross-cuts

- Built on top of [[project-nba-rookie-decomp-suite-2026-06-07]] (translation factors + archetypes + priors pipeline)
- Cardinal rule held [[feedback-raw-data-only-no-projecting-on-projections]]: no third-party mock drafts (ESPN / Tankathon / The Ringer) used as inputs — combine list is just the eligibility pool
