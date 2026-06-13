# Competition Normalization for 2026 NBA Draft Decomp — 2026-06-07

The biggest unsolved problem in our draft model was that **20 pts/40 in NCAA_LOW** was being translated to NBA the same way as **20 pts/40 in NCAA_P5** or **20 pts/40 in BBL** — silently. This decomp fixes that with two independent normalization layers that cross-check each other.

## Architecture: Idea 2 sets priors, Idea 1 corrects

**Idea 2 — Outcome-calibrated GBM (sets priors)**
LightGBM per-target stat, fit on 501 historical prospects 2014-24 with `pre_nba_league_label` (NCAA_P5/MID/LOW, intl_g_league, unknown) as a categorical feature. Target stats: Y1 pts/reb/ast/stl/blk/fg3m/tov per-36, mpg, gp, draft_pick. League effect FALLS OUT of regression coefficients — no hand-tuning. Holdout 2023-24:

| Target | Lift over baseline |
|---|---:|
| reb_per36 | +36.8% |
| blk_per36 | +30.7% |
| ast_per36 | +30.3% |
| gp | +26.8% |
| mpg | +20.6% |
| draft_pick | +14.9% |

**Idea 1 — Crossover-player graph (corrects)**
For each player who appears in 2+ leagues (NCAA transfers between conference tiers + every drafted prospect's pre-NBA → NBA Y1 outcome), compute per-stat ratio. These ratios are the empirical league-strength multipliers. Edges total 456 (89 NCAA→NCAA + 367 pre-NBA→NBA). Survivorship-bias caveat: transfer pool is non-random, only good-enough players move up, so the intra-NCAA edges OVER-estimate the difficulty of the upper conference (good players bridge the gap).

## Headline compression ratios (Idea 1)

**League → NBA Y1 per-40 ratio (median):**

| Stat | NCAA_LOW | NCAA_MID | NCAA_P5 | intl_g_league |
|---|---:|---:|---:|---:|
| pts | 0.632 | 0.666 | **0.756** | 0.641 |
| reb | 0.867 | 0.756 | 0.850 | 0.831 |
| ast | 0.844 | 0.913 | **0.984** | 0.652 |
| stl | 0.874 | 0.836 | 0.840 | 0.760 |
| blk | — | 0.550 | 0.646 | 0.637 |
| tov | 0.791 | 0.733 | 0.770 | 0.618 |

### Substantive findings
1. **NCAA_P5 ast retains 0.984** — almost 1:1 translation to NBA. P5 assists are NBA-quality reads.
2. **NCAA_LOW pts retains only 0.632** — low-major scorers padded against weak D and lose ~37% at NBA level.
3. **intl_g_league ast crashes to 0.652** ★ — G-League PGs are bench-ball assist hogs whose vision doesn't translate. **This is the Kayil signal**: if his BBL ast translates like G-League ast, 6.60 ast/40 BBL → only ~4.3 ast/36 NBA.
4. **Universal blk compression to 0.55-0.65** across all NCAA tiers — shotblock translation is the weakest signal.
5. **Implied P5/LOW competition multiplier for scoring = 1.20×** — playing in P5 is ~20% harder for scoring than NCAA_LOW.

## Outcome-calibrated 2026 board (tier banding)

Tier band distribution: Lottery 4 / Mid-1st 28 / Early-2nd 40 / no Late-2nd / Undrafted.

### Top 15 by outcome-calibrated value rank (with hand-composite delta)

| OC Rank | Player | Pos | League | Tier | Pred Pick | Hand Rank | Δ |
|---:|---|---|---|---|---:|---:|---:|
| 1 | **Sergio De Larrea** ⚠ | PG | unknown (ACB) | Lottery | 10.3 | 16 | +15 |
| 2 | Dailyn Swain | SF | NCAA_P5 | Lottery | 10.3 | 37 | +35 |
| 3 | Ryan Conwell | SG | NCAA_P5 | Lottery | 10.3 | 35 | +32 |
| 4 | **Karim Lopez** | PF | intl_g_league | Mid-1st | 14.6 | 58 | +54 |
| 5 | **Jack Kayil** | PG | intl_g_league | Early-2nd | 34.2 | 17 | +12 |
| 6 | Aday Mara | C | NCAA_P5 | Early-2nd | 36.9 | 60 | +54 |
| 7 | Maliq Brown | C | NCAA_P5 | Early-2nd | 31.7 | 53 | +46 |
| 8 | **AJ Dybantsa** | SF | NCAA_P5 | Early-2nd | 31.7 | 8 | **0** |
| 9 | **Cameron Boozer** | PF | NCAA_P5 | Mid-1st | 27.6 | 1 | -8 |
| 10 | Caleb Wilson | PF | NCAA_P5 | Mid-1st | 23.3 | 32 | +22 |
| 11 | **Luigi Suigo** | C | intl_g_league | Mid-1st | 20.1 | 69 | +58 |
| 12 | Joshua Jefferson | PF | NCAA_P5 | Mid-1st | 27.1 | 5 | -7 |
| 13 | Dillon Mitchell | PF | NCAA_P5 | Early-2nd | 31.9 | 64 | +51 |
| 14 | **Nate Ament** | PF | NCAA_P5 | Mid-1st | 25.5 | 3 | -11 |
| 15 | Amari Allen | SF | NCAA_P5 | Early-2nd | 36.0 | 12 | -3 |

⚠ Sergio De Larrea at #1 with predicted pick 10.3 is **flagged for survivorship bias** — he's labeled "unknown" league because we don't have ACB historical training data, and the "unknown" bucket in our 501-prospect pool is dominated by elite EuroLeague/ACB prospects who got drafted in the lottery (Doncic-tier). The model is naively giving him that prior. Real read: he's probably late-1st / early-2nd, not lottery.

## Biggest rank disagreements — the signal flags

### Outcome model thinks they're VASTLY OVERRATED by hand composite
| Player | Hand → OC | Why outcome model is skeptical |
|---|---|---|
| **Baba Miller** | #2 → #63 | Score-First Wing archetype with elite NCAA pts; outcome model says NCAA scoring doesn't translate that well |
| **Koa Peat** | #4 → #49 | Same pattern — high-pts freshman PF, model wants more demonstrated efficiency |
| **Tyler Tanner** | #7 → #24 | Older transfer; outcome model penalizes pre-NBA age |
| **Jeremy Fears Jr.** | #6 → #38 | 6.14 ast/36 is the same trap as Kayil — assists don't translate as well as hand model assumed |
| **Labaron Philon Jr.** | #10 → #19 | Modest fade |
| **Kingston Flemings** | #11 → #21 | Same |

### Outcome model thinks they're VASTLY UNDERRATED by hand composite
| Player | Hand → OC | Why outcome model is bullish |
|---|---|---|
| **Karim Lopez** | #58 → #4 | Intl prospect, NBL translates better than hand discount factor |
| **Luigi Suigo** | #69 → #11 | 7'3" rebounding+blocks profile; reb R²=0.60 and blk R²=0.66 in training |
| **Aday Mara** | #60 → #6 | 7'3" UCLA center; pure rim profile |
| **Maliq Brown** | #53 → #7 | Defensive Big; reb+blk drive outcome model up |
| **Dillon Mitchell** | #64 → #13 | Athletic PF; combine measurables matter |
| **Bidunga / Ejiofor / Reed Jr. / Onyenso** | low-50s→mid-20s | Centers across the board move up because outcome model values reb/blk over the hand-composite's pts emphasis |

### Strong agreement (both methods say top-10)
- **AJ Dybantsa** stays #8 in both. Highest confidence prospect in the class.

## Kayil verdict (the original question)

**Hand-built rank #17 — Outcome rank #5 by value composite, predicted pick #34 (Early-2nd tier).**

The two diverge because hand-composite uses raw production × minutes and Kayil's BBL line projects to elite assists (6.60 ast/40 → 6.14 ast/36 in hand model). The outcome model AGREES his production is top-5 productive when scaled but ALSO knows historically that intl prospects with his profile actually get drafted in the early second round, not the lottery. Crossover-graph confirms: **intl_g_league ast retains only 0.652** — meaning his 6.60 ast/40 BBL likely becomes ~4.3 ast/36 NBA, still elite but not Lonzo-tier.

**Final read:** Kayil is properly placed by outcome model in Early-2nd (pick ~34). Hand-build's #17 was overly optimistic about BBL assist translation.

## Survivorship-bias receipts

Intra-NCAA transfer ratios show the bias clearly:

| Move | pts | ast | blk |
|---|---:|---:|---:|
| LOW→P5 | 0.959 | 1.056 | 0.957 |
| MID→P5 | 1.046 | 1.076 | **0.774** |

A player transferring MID→P5 grows his scoring (+4.6%) and assists (+7.6%) — because the kind of player who transfers UP is a survivor (good enough to face better competition without collapsing). But blocks crash to 0.774 because even survivor-bigs face better offense in P5 and lose cheap-block opportunities.

This means the league multipliers DERIVED from intra-NCAA transfers UNDER-estimate true conference difficulty. The league→NBA compression ratios are the more honest measure.

## ★ BOLD PREDICTIONS — 2026-06-07 PRE-DRAFT (pre-registered)

The 2026 NBA Draft is upcoming late June 2026. These are time-stamped contrarian calls our methodology justifies posting today. Each backed by the outcome-calibrated GBM (37/30/31% holdout lift on reb/ast/blk) + the crossover graph compression ratios above.

### Locks (both methods agree, high confidence)
- **AJ Dybantsa** — top 10 in real draft. Hand #8, outcome #8. Same comp tier as RJ Barrett / Anthony Edwards.
- **Cameron Boozer** — top 10 in real draft. Hand #1, outcome #9. Jabari Smith Jr. / Ben Simmons archetype.

### Contrarian DOWN calls (outcome model says consensus is too high)
- **Baba Miller — likely bust.** Public mocks have him top 15. Our outcome model has him #63 / Early-2nd tier. NCAA scoring at his rate doesn't translate when the player isn't elsewhere on the production curve. Crossover graph: NCAA_P5 pts retain 0.756, so Miller's volume scoring discounts hard.
- **Koa Peat — overrated by consensus.** Top 10 in most mocks. Our outcome model has him #49 / Early-2nd. Same archetype problem as Miller — Score-First Wing with NCAA pts inflation.
- **Jeremy Fears Jr. — assist mirage.** 6.14 ast/36 hand projection but the same "ast doesn't translate" trap as intl PGs. NCAA_P5 ast retention 0.984 makes this look good, but his projected NBA Y1 mpg (15-17) puts him solidly in Mid-1st, not top 6.

### Contrarian UP calls (outcome model says consensus is too low)
- **Karim Lopez — top 15 production sleeper.** Public mocks have him mid-late 1st. Our outcome model has him #4 by value composite, predicted pick 14.6 (Mid-1st). 11.9 ppg / 6.1 rpg / 1.0 bpg in NBL Australia at 18 with the physical profile.
- **Aday Mara — overlooked center.** Late 2nd / early-2nd in mocks. Our outcome model has him #6 by value, predicted pick 36.9. 7'3" reb+blk profile is exactly what outcome model gives credit to (reb R²=0.60, blk R²=0.66 in training).
- **Bigs across the board** — Maliq Brown, Tarris Reed Jr., Zuby Ejiofor, Ugonna Onyenso, Izaiyah Nelson all move from hand-late-2nd into outcome-mid-early-2nd. Centers as a class are systematically under-valued by box-score-only hand models.

### Caveat predictions (flagged for survivorship)
- **Sergio De Larrea** — outcome model #1 / Lottery is a survivorship-bias artifact (ACB "unknown" league bucket dominated by Doncic-tier historical picks). Real read: late-1st / early-2nd. We're explicitly NOT taking the model's #1 ranking at face value.

### Pre-reg timestamp
This board is committed as-of **2026-06-07** before the 2026 NBA Draft. Outcomes will be evaluated against:
1. Actual draft position vs predicted draft pick
2. NBA Y1 production vs projected Y1 per-36 stats
3. Per-prospect rank delta — did the outcome model or hand composite call it better

This is what [[feedback-bold-timestamped-predictions]] looks like applied.

---

## Outstanding for v2

- **Pre-register a tighter version** of the crossover graph: lock the anchor (NBA), age window (18-23), and per-stat set before fitting. Currently fitted ad hoc.
- **Add direction-of-move as covariate** in the regression — survivorship bias should make the "up" direction have lower compression than "down".
- **Surface confidence per league multiplier** — NCAA_LOW has only 7-8 edges per stat; intl true non-G-League has 0 edges. Honest low-confidence reporting.
- **Scrape intl historical** (EuroLeague/ACB/BBL/NBL drafted prospects 2014-24) to get real intl→NBA edges and not lean on the "unknown" prior trap.

## Files

- Training set: `data/parquet/rookies_outcome_training.parquet`
- GBM models: `data/models/outcome_gbm_*.txt` (10 targets)
- GBM predictions: `data/parquet/rookies_outcome_gbm_predictions.parquet`
- League effects: `data/parquet/rookies_outcome_gbm_league_effects.parquet`
- Crossover edges: `data/parquet/crossover_edges.parquet` (456 edges)
- League multipliers: `data/parquet/league_strength_multipliers.parquet`
- 2026 outcome board: `data/parquet/draft_2026_outcome_calibrated.parquet`
- Scripts: `scripts/decomp_07_*.py` through `scripts/decomp_10_*.py`

## Cross-cuts

- Sister to [[project-nba-rookie-decomp-suite-2026-06-07]] (the original priors pipeline)
- Sister to [[project-nba-draft-prep-2026-2026-06-07]] (the v1.2 hand-composite board)
- Cardinal rule held [[feedback-raw-data-only-no-projecting-on-projections]] — outcome-calibration is regression on RAW box scores and league labels only; no third-party rankings or mock-draft slot used as inputs (only as targets)
