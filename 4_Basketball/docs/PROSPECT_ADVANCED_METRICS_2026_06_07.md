# 2026 NCAA Prospect Advanced Metrics — 2026-06-07

Applied our advanced-metric framework (PSI / STD / FT-drawing / defensive event rate) to the 67 NCAA prospects in the 2026 draft pool, using sportsdataverse hoopR play-by-play data (2,915k events across the 2025-26 NCAA season).

This is the substrate for **OUR LOTTERY BOARD** — going beyond box-score translation to skill-decomposition.

## Metrics built

| Metric | Definition | Source |
|---|---|---|
| **STD** | Shannon entropy across shot subtypes (Dunk/Layup/2pt-jumper/3pt-jumper/Tip/Hook) | PBP `type_text` + text parsing |
| **PSI** | Shannon entropy across assist destinations (who they passed to) | PBP text `(NAME assists)` regex |
| **ft_rate_per40** | Free throws made per 40 minutes (foul-drawing proxy) | PBP `MadeFreeThrow` events |
| **def_event_rate_per40** | (steals + blocks + DREB) per 40 min | PBP `Steal` + `Block Shot` + `Defensive Rebound` |
| **n_assists_made** | Count of assists credited to this player | Text-parsed |
| **prospect_pts_share** | This player's pts / team total | From [decomp_18_teammate_context.py](../scripts/decomp_18_teammate_context.py) |
| **teammate_pts_per40_top** | Best rotation teammate's per-40 pts | Same |

## Leaderboards by metric

### Top 8 redistributors (PSI ≥ 30 assists)

| Player | Pos | OC3 Rank | PSI | n_assists |
|---|---|---:|---:|---:|
| Otega Oweh | SG | 56 | 2.20 | 67 |
| Kingston Flemings | PG | 31 | 2.10 | 134 |
| Ebuka Okorie | PG | 19 | 2.07 | 81 |
| Ja'Kobi Gillespie | PG | 41 | 2.06 | 141 |
| Labaron Philon Jr. | PG | 20 | 2.06 | 110 |
| Nick Martinelli | PF | 68 | 2.06 | 47 |
| Ryan Conwell | SG | 2 | 2.06 | 65 |
| **AJ Dybantsa** | SF | **13** | **2.02** | **95** |

**Read**: AJ Dybantsa as a top-10 redistributor while being BYU's primary scorer (30% pts share, 95 assists) is rare profile. Otega Oweh under-rated by both models — true distributor.

### Top 8 foul-drawers (FT rate per-40)

| Player | Pos | OC3 Rank | FT rate/40 |
|---|---|---:|---:|
| **AJ Dybantsa** | SF | 13 | **9.68** |
| Caleb Wilson | PF | 14 | 9.59 |
| Nate Ament | PF | 16 | 9.56 |
| Zuby Ejiofor | C | 23 | 9.31 |
| Keyshawn Hall | SF | 66 | 8.81 |
| **Cameron Boozer** | PF | 8 | **8.79** |
| Izaiyah Nelson | C | 29 | 8.61 |
| Ebuka Okorie | PG | 19 | 8.31 |

**Read**: Dybantsa #1 AND in top-10 PSI = elite-foul-drawing-AND-redistributor — closest comp is RJ Barrett/Anthony Edwards as we've already projected. Nate Ament's #3 FT rate at Louisville reinforces the Banchero comp from hand-build.

### Top 8 versatile scorers (STD)

| Player | Pos | OC3 Rank | STD | FT rate/40 |
|---|---|---:|---:|---:|
| Henri Veesaar | C | 55 | 1.67 | 4.80 |
| **Ugonna Onyenso** | C | 26 | 1.66 | 2.62 |
| Allen Graves | PF | 36 | 1.64 | 5.67 |
| **Baba Miller** | PF | 53 | 1.55 | 6.03 |
| Zuby Ejiofor | C | 23 | 1.53 | 9.31 |
| Trevon Brazile | PF | 47 | 1.51 | 4.23 |
| Hannes Steinbach | C | 17 | 1.50 | 6.10 |
| Nick Martinelli | PF | 68 | 1.45 | 7.48 |

**Read**: Bigs dominate STD because they have varied shot inventory (dunks + layups + jumpers + 3pts). **Baba Miller (#53 OC) has top-4 STD and decent FT rate** — partial vindication after v3 had him as a bust call. Worth re-flagging.

### Top 8 defensive engines (def event rate per-40)

| Player | Pos | OC3 Rank | def_rate/40 | n_blocks | n_steals |
|---|---|---:|---:|---:|---:|
| Rueben Chinyelu | C | 45 | 14.91 | 36 | 26 |
| **Ugonna Onyenso** | C | 26 | **14.64** | **104** | 22 |
| **Aday Mara** | C | 5 | 13.30 | 103 | 14 |
| **Izaiyah Nelson** | C | 29 | 12.70 | 48 | **56 ★** |
| Tarris Reed Jr. | C | 15 | 12.66 | 69 | 32 |
| Tobe Awaka | C | 67 | 12.56 | 25 | 14 |
| Baba Miller | PF | 53 | 12.35 | 36 | 23 |
| Caleb Wilson | PF | 14 | 12.03 | 33 | 36 |

**Read**: Onyenso's 104 blocks in 672 min is historic — pure rim deterrent. **Izaiyah Nelson 56 steals from a C** is unicorn perimeter-disruption from the post. **Aday Mara 7'3" with STD 1.43 + 103 blocks + def_rate 13.30** — the most underrated prospect in the class.

## The Resolve Top 14 read (synthesizing v3 + advanced metrics)

This is what changes when we combine outcome-calibrated rank with the advanced-metric flags. **NOT yet pre-registered as our lottery board** — pending one more sanity pass — but here's where the substrate points:

### Methodologically AGREED LOCKS (both v3 + advanced concur)
- **AJ Dybantsa** — top-3 lock. PSI 2.02 + FT rate #1 + 30% pts share at BYU. Both methods agree.
- **Cameron Boozer** — top-6 lock. Hand #1 + FT rate top-6 + 27% share at stacked Duke.

### Advanced-metric UPGRADES (v3 rank too low, advanced says elite)
- **Aday Mara** v3 #5 → likely true top-5. Modern 7'3" with shooting + 103 blocks. STD 1.43 elite for size.
- **Ugonna Onyenso** v3 #26 → likely top-10 by defensive profile. 104 blocks in 672 min, STD 1.66.
- **Caleb Wilson** v3 #14 → confirmed top-15. FT rate 9.59 #2 + def_rate 12.03 + STD 1.41.
- **Izaiyah Nelson** v3 #29 → likely mid-1st by steals+block profile. 56 steals from a C unicorn.

### Hand-build DOWNGRADES validated by both v3 AND advanced
- **Baba Miller** v3 says #53, but advanced flags STD top-4. PARTIAL UPGRADE — was hand #2 → outcome #63 → maybe #25-35.
- **Koa Peat** advanced metrics show lower foul-drawing + lower STD than the lottery-comp would need. v3 #49 stands.
- **Jeremy Fears Jr.** PSI 1.97 with 223 assists but only 9 unique targets = funneler not spreader. v3 #38 honest.

### Intl prospects (v3 outcome only, no advanced metrics — no PBP for non-NCAA)
- Sergio De Larrea — v3 #1 Lottery but survivorship signal +16.9 (Doncic prior). Realistic late-1st.
- Karim Lopez — v3 #4 Mid-1st (NBL anchors). Realistic mid-1st.
- Luigi Suigo — v3 #11 Mid-1st (KLS anchors). Realistic mid-late 1st.
- Jack Kayil — v3 #5 Early-2nd (single BBL anchor). Realistic Early-2nd.

## Files

- Advanced metrics: `data/parquet/prospect_advanced_metrics_2026.parquet` (67 NCAA prospects × 30 cols)
- Augmented board: `data/parquet/draft_2026_lottery_board_final.parquet` (72 prospects × 90+ cols, v3 + advanced + teammate context)
- Scripts: `decomp_17_scrape_ncaa_pbp_2025_26.py`, `decomp_18_teammate_context.py`, `decomp_20_prospect_advanced_metrics.py`, `decomp_21_lottery_board_with_advanced.py`

## What's NOT computable from current substrate

- **ADI** (Action Diversity Index) — needs play-type attribution (P&R / iso / post-up etc.); college PBP doesn't tag at that granularity
- **GAP** (off-ball gravity) — needs player tracking, not available for NCAA
- **DCHS** (Defensive Calibration intervals) — too deep for college-level coverage
- **DFC** (Drive Foul Conversion) — would need drive labeling which PBP doesn't provide

## Cross-cuts

- [[project-nba-novel-offensive-metrics-2026-06-06]] — these are the NCAA equivalents (PSI/STD/FDQ/And1R)
- [[project-nba-defensive-metrics-suite-v1-2026-06-05]] — defensive event rate is the NCAA equivalent of TADEC/DHA
- [[project-nba-competition-normalization-2026-06-07]] — combined model + this advanced layer = substrate for OUR lottery board
- [[feedback-bold-timestamped-predictions]] — applied: locks/upgrades/downgrades all timestamped 2026-06-07
- [[feedback-raw-data-only-no-projecting-on-projections]] — held; PBP is raw event data
