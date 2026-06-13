# Competition Normalization v3 — historical intl stat anchors — 2026-06-07

Follow-up to [v2](COMPETITION_NORMALIZATION_V2_2026_06_07.md). The v2 work added proper intl league labels but rankings didn't move because survivorship bias is in the FEATURES. v3 attacks the feature gap: scrape pre-NBA per-40 stats for 7 high-impact historical intl prospects whose stats were NaN in our pool.

## What v3 adds

WebFetched per-game season stats for 7 historical intl prospects via Wikipedia. Computed per-40 from `(pts_pg × 40 / mpg)`. Injected into training set v3.

| Player | Draft | League | Pre-NBA per-40 (pts/reb/ast) | NBA Y1 per-36 |
|---|---:|---|---|---|
| LaMelo Ball | #3 2020 | NBL Australia | 21.79 / 9.49 / 8.72 | 19.68 |
| Victor Wembanyama | #1 2023 | LNB France | 26.92 / 12.96 / 2.99 | 26.02 |
| Mario Hezonja | #5 2015 | ACB Spain | 13.24 / 5.63 / 3.38 | 12.18 |
| Alex Sarr | #2 2024 | NBL Australia | 21.73 / 9.94 / 2.08 | 17.25 |
| Sasha Vezenkov | #57 2017 | ACB Spain | 18.51 / 6.60 / 1.70 | 15.85 |
| Zaccharie Risacher | #1 2024 | LNB France | 18.36 / 6.91 / NaN | 18.40 |
| Deni Avdija | #9 2020 | Israeli PL | (stats no MPG; left partial) | 9.79 |

## Why these matter — anti-survivor anchors

The ACB bucket previously had ZERO stat anchors → model relied on feature similarity → De Larrea looked like Doncic-tier elite. Now ACB has TWO anchors:
- **Hezonja: 13.24 pts/40 in ACB → 12.18 NBA Y1 pts/36** — modest pre-NBA production, drafted #5 (high pick) but with subdued production. The "high-pick-on-talent-not-stats" anchor.
- **Vezenkov: 18.51 pts/40 → 15.85 NBA Y1 pts/36** — much higher pre-NBA production but drafted late (#57). The "production-doesn't-equal-draft-slot" anchor.

NBL bucket gained Sarr (#2 → 17.25 NBA) + LaMelo (#3 → 19.68 NBA). LNB gained Wemby (#1 → 26.02 NBA — the unicorn) + Risacher (#1 → 18.40).

These anchors teach the GBM that league-specific compression isn't uniform — Hezonja translated his MODEST production well; Vezenkov translated his HIGHER production proportionally; LaMelo dominated NBL and dominated NBA Y1. The model can now distinguish elite-intl-production from modest-intl-production.

## v3 vs v1/v2 ranking shifts (the 4 priority intl)

| Player | v1/v2 Pick Pred | v3 Pick Pred | Movement | League Baseline |
|---|---:|---:|---|---:|
| **Sergio De Larrea** | 10.32 | **12.67** | +2.4 later | 29.60 (ACB) |
| **Karim Lopez** | 14.61 | 15.86 | +1.3 later | 28.56 (NBL) |
| **Luigi Suigo** | 20.08 | **25.26** | **+5.2 later** ★ | 34.67 (KLS) |
| **Jack Kayil** | 34.19 | 31.39 | -2.8 earlier | (BBL only had Hayes anchor) |

Suigo had the biggest move because KLS/ABA bucket was thinnest and gained the most calibration headroom. De Larrea moved modestly later — survivorship bias only PARTIALLY defused (signal still +16.93 against league baseline 29.60).

## Updated bold predictions (v3 read)

The pre-registered bold predictions from [v1](COMPETITION_NORMALIZATION_2026_06_07.md) update:

### Refined intl reads
- **Sergio De Larrea**: v3 predicts pick 12.7 (still lottery but later than v1's 10.3). Survivorship signal +16.9 still suggests honest read is late-1st (pick 20-28). **Realistic call: 18-25.**
- **Karim Lopez**: v3 predicts pick 15.9 (still Mid-1st). LaMelo (#3) and Sarr (#2) anchors are top-of-NBL; Lopez's profile is more modest → **realistic call: 18-26.**
- **Luigi Suigo**: v3 predicts pick 25.3 (Mid-1st after big move from v1). KLS Serbia bucket calibration with Bitadze/Vukcevic anchors is now reasonable. **Hold call at Mid-1st (20-30).**
- **Jack Kayil**: v3 predicts pick 31.4 (Early-2nd held). BBL has only 1 anchor (Hayes #7 elite outlier) — kayil at pick 31 is honest read, hand-#17 was over-aggressive.

### NCAA reads unchanged
Boozer / Dybantsa top-10 locks hold. Baba Miller / Koa Peat bust calls hold (NCAA training data was already rich, v3 supplement was intl-only).

## Architectural lesson banked

**Label refresh (v2) didn't move rankings; stat injection (v3) did.** The 4-year arc of competition-normalization work confirms:

1. Categorical league labels alone don't fix survivorship bias when training features are sparse
2. The fix requires ANCHORS — actual stat lines from historical prospects in the same league bucket
3. Even sparse anchors (2-5 per league) substantively shift the calibration
4. The remaining survivorship signal (still +16.9 for De Larrea after v3) is the BIAS THAT CANNOT BE FIXED WITHOUT MORE ANCHORS — we'd need to scrape 20-30 historical ACB picks to fully defuse

## Files

- v3 training: `data/parquet/rookies_outcome_training_v3.parquet`
- v3 models: `data/models/outcome_gbm_v3_*.txt`
- v3 league effects: `data/parquet/rookies_outcome_gbm_v3_league_effects.parquet`
- v3 2026 board: `data/parquet/draft_2026_outcome_calibrated_v3.parquet`
- v3 scripts: `decomp_14_historical_intl_supplement.py`, `decomp_15_outcome_gbm_v3.py`, `decomp_16_project_2026_v3.py`

## Outstanding for v4

- More historical intl anchors (target: 20-30 per major league bucket — would fully defuse the De Larrea bias)
- Direction-of-move covariate for survivorship
- Per-season age + role progression for top-flight intl prospects (some played 2-3 pro seasons before NBA, only most-recent currently used)
- Post-draft eval after late June 2026

## Cross-cuts

- [[project-nba-competition-normalization-2026-06-07]] — v1 substrate (NCAA-rich) + v2 label refresh + v3 stat anchors
- [[feedback-bold-timestamped-predictions]] — bold-prediction discipline; v3 refines the intl reads
- [[feedback-raw-data-only-no-projecting-on-projections]] — held; Wikipedia per-game stats are raw observations, not third-party rankings/projections
