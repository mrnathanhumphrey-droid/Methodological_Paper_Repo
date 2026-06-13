# 2026 NBA Draft Class — Decomp v1.2 (2026-06-07) — 100% coverage

**Updated 2026-06-07 (v1.2):** All 72 prospects now fully projected. Intl substrate gap closed via WebFetch + multi-source aggregation:
- **Jack Kayil** (Alba Berlin, German BBL): 38 GP / 21.2 mpg / 12.6 ppg / 2.7 rpg / 3.5 apg / 0.9 spg / 33.7% 3PT — from scoutbasketball.com + alba.berlin
- **Karim Lopez** (NZ Breakers, NBL Australia): 30 GP / 25.6 mpg / 11.9 ppg / 6.1 rpg / 1.9 apg / 1.0 bpg — from nzbreakers.basketball
- **Sergio De Larrea** (Valencia, ACB Spain 2024-25): 30 GP / 17.2 mpg / 9.6 ppg / 3.0 rpg / 3.7 apg — from basketnews.com + basketballstats.net
- **Luigi Suigo** (KK Mega Basket, ABA): 26 GP / 17.9 mpg / 7.9 ppg / 5.1 rpg / 1.0 bpg — from Wikipedia

All four ranked in v1.2 board. **Jack Kayil at #17 with D'Angelo Russell / Nico Mannion comps** — strong landing for a 2026 BBL Best Young Player. **De Larrea #16 — Mudiay / RJ Hampton comps**. Lopez #58 Stretch Big. Suigo #69 Defensive Big.

**v1.1 → v1.2 sourcing lesson banked:** RealGM / ProBallers / official-league sites consistently return 403 to WebFetch. The viable intl pipeline is: (1) DuckDuckGo HTML search to find quoted snippets across the web, (2) hit the specific URLs that returned per-game numbers, (3) prefer scoutbasketball.com (covers BBL, NBL, several Euro leagues), nzbreakers.basketball + team-official sites, and Wikipedia for tournament stats.

---

# 2026 NBA Draft Class — Decomp v1.1 (2026-06-07)

**v1.1 historical note:** Added Suigo via Wikipedia, fixed Nate Ament alias. 69 of 72 coverage. Then v1.2 closed the remaining 3.

---

# 2026 NBA Draft Class — Decomp v1 (2026-06-07)

Pre-draft projections built on top of the [Rookie Decomp Suite](ROOKIE_DECOMP_SUITE_2026_06_07.md). Trained on 2014-24 historical rookies; applied to the 2026 class using their pre-NBA stats + position.

## What's new in v1 vs v0

- **2025-26 NCAA season scraped** (196,876 game-rows, 12,482 players from sportsdataverse hoopR-mbb-data) — unblocks the elite freshman class including Dybantsa (BYU 25.5 ppg), Boozer (Duke 22.5 ppg), Acuff (Arkansas 22.8 ppg), Peat (Arizona), Yessoufou (Baylor), Cenac Jr. (Houston), Philon Jr. (Alabama)
- **Name aliases** added: "Anicet Dybantsa" → "AJ Dybantsa", "Labaron Philon" → "Labaron Philon Jr.", "Christopher Cenac Jr." → "Chris Cenac Jr."
- **Cameron Boozer added** — not on the 2026 combine invitee list but obvious lottery pick
- **Coverage**: 67 of 72 prospects fully projected (was 50 of 71 in v0)

## Top 15 board (v1.1)

| Rank | Player | Pos | Archetype | Pts/36 | Reb/36 | Ast/36 | Blk/36 | Comp 1 | Comp 2 |
|---:|---|---|---|---:|---:|---:|---:|---|---|
| 1 | **Cameron Boozer** | PF | Score-First Wing | 15.1 | 8.6 | 3.1 | 0.9 | Jabari Smith Jr. | Ben Simmons |
| 2 | Baba Miller | PF | Score-First Wing | 13.8 | 8.8 | 3.0 | 1.1 | Darius Bazley | Day'Ron Sharpe |
| 3 | **Nate Ament** | PF | Score-First Wing | 14.6 | 7.4 | 2.5 | 0.9 | **Paolo Banchero** | **Brandon Miller** |
| 4 | **Koa Peat** | PF | Score-First Wing | 14.2 | 7.1 | 2.8 | 1.0 | Darius Bazley | Romeo Langford |
| 5 | Joshua Jefferson | PF | Utility Wing | 13.6 | 6.3 | 4.4 | 0.6 | Jalen Suggs | Ben Simmons |
| 6 | **Jeremy Fears Jr.** | PG | Utility Wing | 13.4 | 4.1 | 6.1 | 0.4 | Lonzo Ball | Emmanuel Mudiay |
| 7 | Tyler Tanner | PG | Utility Wing | 13.8 | 4.6 | 4.4 | 0.5 | Spencer Dinwiddie | Malachi Flynn |
| 8 | **AJ Dybantsa** | SF | Utility Wing | 14.6 | 5.7 | 3.7 | 0.5 | RJ Barrett | Anthony Edwards |
| 9 | **Darius Acuff Jr.** | PG | Utility Wing | 14.2 | 4.3 | 4.8 | 0.5 | TyTy Washington Jr. | R.J. Hampton |
| 10 | **Labaron Philon Jr.** | PG | Utility Wing | 14.5 | 4.5 | 4.4 | 0.4 | D'Angelo Russell | Payton Pritchard |
| 11 | Kingston Flemings | PG | Utility Wing | 13.5 | 4.8 | 4.5 | 0.5 | Spencer Dinwiddie | Jerian Grant |
| 11 | Amari Allen | SF | Utility Wing | 13.4 | 7.8 | 3.2 | 0.4 | Jaylen Brown | Jonah Bolden |
| 12 | Christian Anderson | PG | Utility Wing | 13.4 | 4.4 | 5.0 | 0.4 | Nico Mannion | Tyrone Wallace |
| 13 | Nicholas Boyd | PG | Utility Wing | 14.2 | 4.7 | 4.1 | 0.4 | Payton Pritchard | Bennedict Mathurin |
| 14 | Ja'Kobi Gillespie | PG | Utility Wing | 13.5 | 4.2 | 4.4 | 0.4 | Kira Lewis Jr. | Nico Mannion |
| 15 | Peter Suder | SG | Utility Wing | 13.2 | 5.2 | 3.4 | 0.5 | Spencer Dinwiddie | Desmond Bane |

## Standout comps

- **Boozer → Jabari Smith Jr. + Ben Simmons** is a clean Score-First PF comp set
- **Dybantsa → RJ Barrett + Anthony Edwards** matches the high-usage Duke/BYU SF freshman archetype
- **Jeremy Fears Jr. → Lonzo Ball** — both 6'2 PGs with elite vision-first profile (Fears 6.14 ast/36 projected)
- **Philon Jr. → D'Angelo Russell** — both lefty PGs with mid-range scoring + assist mix
- **Joshua Jefferson → Jalen Suggs + Ben Simmons** — point forward profile

## Likely lottery picks projected

| Player | Projected Y1 value | Rank | Notes |
|---|---:|---:|---|
| Cameron Boozer | 1214 | 1 | Box-score king; mock #1 consensus |
| Baba Miller | 1162 | 2 | Florida State PF |
| Koa Peat | 1098 | 3 | Arizona freshman |
| Joshua Jefferson | 1054 | 4 | Iowa State |
| Jeremy Fears Jr. | 1045 | 5 | Michigan State PG |
| AJ Dybantsa | 1009 | 7 | BYU SF — consensus top-3 mock |
| Chris Cenac Jr. | 900 | 24 | Houston freshman — Aaron Gordon comp |
| Darryn Peterson | 915 | 16 | Kansas SG — TJ Warren comp |
| Tounde Yessoufou | 899 | 25 | Baylor SF |
| Brayden Burries | 907 | 21 | Arizona freshman SG |
| Caleb Wilson | 890 | 29 | UNC PF (Darius Bazley / Santi Aldama comp) |

## Remaining gaps for v2

- **5 prospects still unmatched** — Nathaniel Ament, Sergio De Larrea, Jack Kayil, Karim Lopez, Luigi Suigo (mostly intl). Need 2025-26 EuroLeague / ACB / NZ NBL refresh.
- **2026 combine measurements** — NBA Stats API still returning invitee names + positions only. No height / wingspan / vertical numbers live yet (re-fetch script: `draft_prep_2026_01_refresh_combine.py`).
- **Position-aware archetypes need work** — some bigs collapsed into "Score-First Wing" rather than getting their own "Stretch Big" cluster; manual position floor handles obvious bigs but borderline cases (PF/Wing tweeners) get the wing label.
- **Calibration multiplier (~10% interval widening)** carried over from v0 calibration test — should be applied here too.

## Cardinal rule held

Zero third-party rankings used as inputs ([[feedback-raw-data-only-no-projecting-on-projections]]). The board ranking is derived from raw NCAA stats translated through 2014-24 historical regressions, NOT from ESPN / Tankathon / Athletic mock rankings.

## Files

- Candidate pool: `data/parquet/draft_2026_candidate_pool.parquet` (72 prospects)
- Projections: `data/parquet/draft_2026_projections.parquet` (72 × 102 cols)
- Scripts: `scripts/draft_prep_2026_*.py` + `scripts/draft_prep_2026_v1_scrape_ncaa_2025_26.py`
