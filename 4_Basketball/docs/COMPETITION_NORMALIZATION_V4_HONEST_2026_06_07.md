# Competition Normalization v4 — honest finding on teammate features — 2026-06-07

Follow-up to [v3](COMPETITION_NORMALIZATION_V3_2026_06_07.md). Tested teammate-quality features as a normalization input. The result is informative but **not the win we expected** — banking the honest finding.

## What v4 tried

Added 4 teammate-context features to the GBM training:
- `teammate_pts_per40_top` — best rotation teammate's per-40 pts
- `teammate_pts_per40_mean` — average rotation teammates' per-40
- `prospect_pts_share` — prospect's % of team scoring
- `team_pts_per_game` — tempo proxy

The hypothesis: a guard's 22 ppg next to 4 future-NBA-drafted teammates is different work than 22 ppg carrying scrubs. Teammate features should let the model differentiate.

Substrate: 104 historical 2023-24 prospects (only seasons we have NCAA game logs for) had teammate features computed. 397 older prospects (2014-22) had NaN. 67 NCAA 2026 prospects had real teammate features; 4 intl 2026 prospects had NaN.

## Result: honest finding

**Holdout lifts marginally improved but the forward projection broke:**

| Target | v3 lift | v4 lift |
|---|---:|---:|
| reb_per36 | +37% | +40.7% |
| ast_per36 | +30% | +29.3% |
| blk_per36 | +31% | +33.3% |
| gp | +27% | +25.4% |
| draft_pick | +15% | +14.2% |

Marginal training-side improvement, but the forward 2026 projection went sideways because:

1. **Intl prospects (Suigo, Lopez, De Larrea, Kayil) all got NaN teammate features** → LightGBM pooled them into a single leaf → all received IDENTICAL predictions (pick 12.67, mpg 24.13, pts 14.68). The intl signal lost.

2. **Role-player NCAA prospects over-penalized.** Maliq Brown (Duke, 6% pts_share) dropped from oc3 #10 to oc4 #60 because the model read his low share as "not an NBA prospect" in a 104-row training sample. Dillon Mitchell #9 → #47.

3. **High-share role-player NCAA prospects over-rewarded.** Christian Anderson (Texas Tech, 23% share) jumped #24 → #6.

## Why this happened

- **Sample size**: 104 prospects with teammate features is too small to learn a reliable teammate effect coefficient. The GBM over-fit on the training set + mishandled NaN on the forward intl pool.
- **NaN handling for forward projection**: LightGBM treats NaN as a categorical signal during training; when ALL intl prospects share NaN, they all get the same leaf. Honest fix would require teammate-feature imputation per league bucket.
- **Teammate effect is multiplicative, not additive**: a guard who scores 22 ppg next to a lottery-pick big is different from a guard who scores 22 ppg next to a lottery-pick GUARD. We didn't condition the teammate effect on position interactions.

## What v3 STAYS the headline

The v3 model remains the official outcome-calibrated board:
- League weightings calibrated from real historical anchors (Hezonja/Vezenkov/LaMelo/Wemby/Sarr/Risacher)
- Survivorship-signal diagnostic surfaces bias quantitatively
- Cardinal rule held (raw observations only)

v4 lessons banked:
1. **Teammate features need MORE than 100-row training sample** to learn coefficients
2. **NaN imputation strategy matters** when adding features that don't apply to entire pool
3. **Teammate-quality is a real signal but needs careful feature engineering** (position-conditioned, per-stat, possibly shrunk)

## Where teammate context DOES belong

As a **diagnostic surface layer** on the lottery board, not as a model input. Each prospect's profile should display:
- Their team's tempo (`team_pts_per_game`)
- Their share of team production (`prospect_pts_share`)
- Their best rotation teammate's per-40 (`teammate_pts_per40_top`)

This gives the human reader honest context ("Maliq Brown 6% share at Duke = role player on stacked roster") without trying to fold it into the regression coefficient.

## Teammate context for 2026 board (transparency layer)

Top "carrying-the-team" prospects (highest `prospect_pts_share`):
- Nick Martinelli (Northwestern) — 31% — carry job
- **AJ Dybantsa (BYU) — 30%** — primary at BYU
- Ebuka Okorie (Stanford) — 28%
- **Cameron Boozer (Duke) — 27%** — primary at Duke despite stacked roster
- Bennett Stirtz (Iowa) — 27%
- Acuff Jr. (Arkansas) — 25%

Top "stacked-roster" prospects (highest `teammate_pts_per40_top`, rotation-filtered):
- Richie Saunders (BYU) — 29.14 (alongside Dybantsa)
- Amari Allen (Alabama) — 28.66
- **Flory Bidunga (Kansas) — 27.88**
- Isaiah Evans (Duke) — 27.22
- Maliq Brown (Duke) — 27.22
- John Blackwell (Wisconsin) — 25.79
- Caleb Wilson (UNC) — 25.79

## Outstanding for v5+

- Position-conditioned teammate features (e.g., "elite-finishing-big teammate" boost for guard's ast translation)
- Per-stat-class teammate effects (different teammate variables matter for pts vs ast vs blk)
- Direction-of-move covariate for the crossover graph (the user's original "Idea 1" survivorship correction)
- Advanced metric features when NCAA PBP is integrated (PSI / STD / FDQ on prospects)

## Cross-cuts

- [[project-nba-competition-normalization-2026-06-07]] — v1/v2/v3 substrate; v4 finding banked here as honest non-improvement
- [[feedback-bold-timestamped-predictions]] — including honest "this didn't work" findings is part of the discipline
- [[feedback-raw-data-only-no-projecting-on-projections]] — held throughout
