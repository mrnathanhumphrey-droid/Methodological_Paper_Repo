# Rookie Decomp Suite — 2026-06-07

A production-grade rookie projection system. End-to-end pipeline from pre-NBA priors (NCAA / international / combine / draft slot) to NBA Year-1 outcome projection with calibrated intervals and named comps. Slots into the v6 architecture as the empirical-Bayes anchor for incoming rookies.

## What's in the suite

| Script | Output | Purpose |
|---|---|---|
| `decomp_01_build_rookies_master.py` | `rookies_master.parquet` | Master spine: every drafted player 2014-24 unified with pre-NBA features + NBA Year-1/2/3 outcome |
| `decomp_02_translation_factors.py` | `rookie_translation_factors.parquet` + `ROOKIE_DECOMP_TRANSLATION_FACTORS.md` | Per-stat OLS slope NCAA/intl per-40 → NBA Y1 per-36, by source × position bucket |
| `decomp_03_signal_source.py` | `rookie_signal_source.parquet` + `ROOKIE_DECOMP_SIGNAL_SOURCE.md` | Per Y1 outcome stat, top predictors across 3 input families (pre-NBA / combine / draft) |
| `decomp_04_archetype_clusters.py` | `rookie_archetypes.parquet` + `ROOKIE_DECOMP_ARCHETYPES.md` | KMeans K=8 on combine + pre-NBA features; per-cluster Y1 distributions + named labels |
| `decomp_05_rookie_priors_production.py` | `rookie_priors.parquet` | ★ Production deliverable — per-player Y1 point + 7-level percentiles + archetype + nearest comps + confidence |
| `decomp_06_calibration_holdout.py` | (stdout report) | Honest holdout test on 2022-23 with training restricted to ≤2021 |

## Headline findings

### Translation factors (NCAA per-40 → NBA Y1 per-36)
- **NCAA blocks R²=0.662** — the strongest single signal in the suite. Big who blocks in college → big who blocks in NBA, full stop.
- **NCAA rebounds R²=0.599**, **assists R²=0.538** — strong-to-elite translation
- **NCAA pts R²=0.077** — near-noise. **College scoring rate barely predicts NBA rookie scoring rate.** Usage and role change too much.
- **International translation is weaker than NCAA across the board** — wider league-quality variance pollutes the signal

### Signal source — what predicts what
- Rookie pts/36 is best predicted by **draft_pick** (R²=0.10), not college scoring (R²=0.077). NBA-allocated usage dominates.
- Rookie reb/36 can be predicted at R²>0.48 from **height-no-shoes alone** or **standing reach alone**. You barely need the stats; you need the build.
- Rookie blk/36 is the most-predictable stat in the suite: NCAA blk R²=0.662, then reach R²=0.449, wingspan R²=0.436, height R²=0.396. Stack them and you have a very tight projection.
- Rookie ast/36 inversely correlates with height (R²=0.37) — entirely structural, but a load-bearing signal
- Rookie **mpg is almost entirely a function of draft pick** (R²=0.264). Teams allocate minutes by where they drafted you, not by what your combine measurables say.

### Archetypes (K=8 clusters, named post-hoc)
- Defensive Big (n=21): 1.75 blk/36, 8.99 reb/36, 0.09 fg3% — pure rim protectors
- Stretch Big (n=66): 8.91 reb/36, 1.35 blk/36, 1.05 fg3m/36
- Score-First Wing (n=60): 14.91 pts/36, 1.10 fg3m/36, 21.71 mpg
- Wing Shooter (n=42): 13.97 mpg, 2.25 fg3m/36, 0.34 fg3%
- Pass-First PG (n=62): 4.89 ast/36, 1.36 stl/36
- Utility Wing × 3 (n=234 combined)

### 2024 class sample priors

| Player | Pick | Archetype | mpg | pts/36 | reb/36 | ast/36 | blk/36 | Top comps |
|---|---:|---|---:|---:|---:|---:|---:|---|
| Risacher | 1 | Utility Wing 3 | 22.3 | 14.2 | 5.3 | 3.8 | 0.5 | Troy Brown Jr / Kyshawn George / Bryce McGowens |
| Sarr | 2 | Stretch Big | 20.2 | 14.5 | 8.9 | 1.8 | 1.4 | PJ Washington / OG Anunoby / Ausar Thompson |
| Sheppard | 3 | Pass-First PG | 20.5 | 14.0 | 4.5 | 4.9 | 0.5 | KJ Simpson / Jamal Shead / Devin Carter |
| Castle | 4 | Utility Wing 2 | 21.5 | 13.9 | 5.5 | 3.1 | 0.5 | Tyrese Maxey / Desmond Bane / Franz Wagner |
| Clingan | 7 | Stretch Big | 19.5 | 14.4 | 9.2 | 2.1 | 1.8 | Zach Edey / Bobby Portis / Quinten Post |
| Buzelis | 11 | Utility Wing | 18.5 | 13.2 | 6.0 | 3.0 | 2.0 | Chet Holmgren / Brandon Clarke / Joel Embiid |

Castle → Maxey/Bane/Franz Wagner is the cleanest comp set in the table. Buzelis → Holmgren is a structural match.

## Calibration (honest holdout: train ≤2021, test 2022-23)

| Interval | Target | Actual coverage | Status |
|---|---:|---:|---|
| 50% | 50% | **45.6%** | Slightly under-covered (intervals too narrow ~9%) |
| 80% | 80% | **75.8%** | Slightly under-covered |
| 95% | 95% | **91.0%** | Slightly under-covered |

Bias near zero across every stat — no systematic over/under projection. v2 should widen intervals ~10% to hit nominal coverage.

Per-stat MAE:
- pts/36: 2.92 (range ~10-20, ~30% error)
- reb/36: 1.66 (range ~3-12, ~25% error)
- mpg: 6.16 (range ~10-30, ~30% error)
- gp: 15.95 (range 5-82, ~22% error)

These are realistic rookie projection error rates given that rookie role allocation is the dominant source of variance.

## How it slots into the v6 production projection layer

The `rookie_priors.parquet` row format is designed to drop into the existing empirical-Bayes anchor seat that veterans get from `player_career_season_totals_rs`. For any incoming rookie (no NBA history), the v6 player projection layer should:

1. Look up the rookie by `nba_api_id`
2. Use `{stat}_mean` as the empirical-Bayes prior point estimate
3. Use `{stat}_sd` derived from the percentile spread as the prior precision
4. Use `confidence` as the EB shrinkage strength (high confidence → trust the prior strongly; low confidence → fall back further toward archetype mean)
5. Optionally surface `archetype` + `nearest_comps` on the projection page for context

## Outstanding

- **Interval widening for v2** — empirically calibrated multiplier per-stat to hit 50/80/95 nominal coverage
- **International league-tier translation** — EuroLeague vs B.League vs Aussie NBL coefficients differ; currently lumped together
- **Year 2 / Year 3 forward projection** — the priors only cover Y1 outcome; sophomore + Y3 priors would let us extend to dynasty fantasy applications
- **2025 + 2026 class priors** — substrate needs the new draft-class scrape + combine pull when published

## Cross-cuts

- Substrate built on existing `rookie_career_prior.parquet` + `player_career_season_totals_rs.parquet`
- Cardinal rule [[feedback-raw-data-only-no-projecting-on-projections]]: NO third-party rookie projections (ESPN's draft rankings, Tankathon, RealGM consensus) used as inputs — raw box-score + combine measurables only
- Will eventually feed Wonka Resolve NBA draft prep + dynasty rookie board
- Companion to defensive metrics suite at `defensive_metrics/` and offensive metrics suite at [[project-nba-novel-offensive-metrics-2026-06-06]]
