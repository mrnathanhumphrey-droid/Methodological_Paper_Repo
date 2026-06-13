# RESOLVE LOTTERY 2026 — Pre-Registered 2026-06-07

**This board is committed before the 2026 NBA Draft.** Every pick is backed by a methodology trail (outcome-calibrated GBM + production composite + advanced-metric profile + survivorship adjustments + intl-bucket confidence haircut). Outcomes will be evaluated post-draft against actual pick + NBA Year-1 production.

## Methodology

Resolve Score = `0.45 × v3_rank_pct + 0.20 × hand_rank_pct + 0.30 × advanced_signal_pct + survivorship_penalty + intl_low_n_penalty`

Where:
- **v3_rank_pct**: outcome-calibrated LightGBM trained on 501 historical NBA prospects 2014-24 with league/conference categoricals + age + position. Weighted 45% as the load-bearing signal (holdout +27-37% lift over baseline).
- **hand_rank_pct**: production composite (per-40 stats × archetype prior). Weighted 20% as a cross-check.
- **advanced_signal_pct**: average of PSI/STD/FT-rate/def-event-rate from sportsdataverse hoopR PBP (2,915k events). Weighted 30%.
- **survivorship_penalty**: -0.03 × max(0, survivorship_signal − 5). Penalizes intl prospects where v3 model predicts much earlier pick than league baseline (Doncic-tier prior trap).
- **intl_low_n_penalty**: -0.12 for intl prospects with league_n < 10 historical anchors AND no NCAA PBP data. Honest "we don't have enough samples" haircut.

---

## RESOLVE TOP 14

### Pick 1 — Cameron Boozer (Duke, PF)
**Score: 0.80** — v3 #8 / hand #1 / advanced 0.65 (FT rate 8.79 top-6, def_rate 10.61)

The single highest hand-composite score in the class + top-6 foul-drawing + 27% pts share at stacked Duke. Score-First Wing archetype with **Jabari Smith Jr. / Ben Simmons** comps. Methodology converges: both production and outcome models, plus advanced metrics. The lock.

### Pick 2 — Joshua Jefferson (Iowa State, PF)
**Score: 0.77** — v3 #11 / hand #5 / advanced 0.66

Utility Wing 3 archetype with **Jalen Suggs / Ben Simmons** comps. Strong PSI 1.79 + def_rate 10.34. Both models like him, advanced metrics confirm point-forward profile. Iowa State Big 12 schedule = legitimate competition.

### Pick 3 — AJ Dybantsa (BYU, SF)
**Score: 0.75** — v3 #13 / hand #8 / advanced 0.67 (PSI 2.02 top-10, FT rate 9.68 #1)

The most complete profile in the class: top-10 redistributor (PSI 2.02 with 95 assists across 11 targets) AND #1 foul-drawer (9.68 FT/40 over 295 makes) AND 30% pts share at BYU. **RJ Barrett / Anthony Edwards** comps. Resolve takes him #3 not #1 only because Boozer's hand-build edge + Jefferson's def_rate give the synthesizer marginally more confidence in those two.

### Pick 4 — Nate Ament (Louisville, PF)
**Score: 0.73** — v3 #16 / hand #3 / advanced 0.62 (FT rate 9.56 #3)

23.23 pts/40 + 8.77 reb/40 at Louisville with FT rate top-3. **Paolo Banchero / Brandon Miller** comps. Hand-build had him #3, v3 said #16 (was originally unmatched as "Nathaniel Ament"), advanced confirms top-tier foul-drawing. Methodology agreed mid-lottery.

### Pick 5 — Amari Allen (Alabama, SF)
**Score: 0.71** — v3 #12 / hand #12 / advanced 0.52 / survivorship -9.69

Both models agree mid-lottery. PSI 1.98 (top-15 redistributor) + def_event_rate 9.90 + Alabama SEC schedule. **Jaylen Brown / Jonah Bolden** comps. The big survivorship signal here is NEGATIVE (model predicts WORSE than league baseline) which is the opposite of the De Larrea trap — actually a confidence-strengthening read.

### Pick 6 — Caleb Wilson (UNC, PF)
**Score: 0.70** — v3 #14 / hand #32 / advanced 0.73 (FT rate 9.59 #2, def_rate 12.03, STD 1.41)

The advanced-metric UPGRADE of the lottery. v3 had him at #14, hand-build at #32, but advanced metrics say he's a top-10 player by skill profile: #2 foul-drawer, top-8 def_rate, top-15 STD. **Darius Bazley / Santi Aldama** comps. UNC ACC schedule + 21.0 mpg PBP coverage = solid sample.

### Pick 7 — Aday Mara (UCLA, C)
**Score: 0.66** — v3 #5 / hand #60 / advanced 0.68 (STD 1.43, def_rate 13.30, 103 blocks)

**The most under-rated prospect in the class.** 7'3" center with elite STD for size (74 dunks + 70 layups + 27 jumpers + 3 3pts), def_rate 13.30, **103 blocks in 935 minutes**, and **survivorship signal -7.55** (model thinks he's LESS impactful than league baseline — opposite of the Doncic trap). Public mocks have him late-1st / undrafted. We say true top-10. The bold contrarian call of the lottery.

### Pick 8 — Labaron Philon Jr. (Alabama, PG)
**Score: 0.66** — v3 #20 / hand #10 / advanced 0.52 (PSI 2.06 top-5, FT rate 7.76)

Pure pass-first PG with 110 assists across 11 unique targets. **D'Angelo Russell / Payton Pritchard** comps. Survivorship -6.86 (negative = confident read). Alabama SEC schedule.

### Pick 9 — Ebuka Okorie (Stanford, PG)
**Score: 0.63** — v3 #19 / hand #23 / advanced 0.53 (PSI 2.07 top-3, FT rate 8.31)

The pass-first PG sleeper. PSI 2.07 puts him as the **#3 redistributor in the class**, FT rate 8.31 in the top-10. Stanford ACC competition. **Shaedon Sharpe / Deni Avdija** comps. Public mocks have him outside lottery; methodology says top-10.

### Pick 10 — Hannes Steinbach (Washington, C)
**Score: 0.63** — v3 #17 / hand #47 / advanced 0.71 (STD 1.50, def_rate 11.43)

The second advanced-metric upgrade. Hand-build had him #47 (low pre-NBA production) but PBP shows top-10 STD (varied shot inventory) and top-10 def_rate. 7' center with face-up skill. **Aaron Gordon / Lauri Markkanen** archetypal comp.

### Pick 11 — Darryn Peterson (Kansas, SG)
**Score: 0.62** — v3 #21 / hand #19 / advanced 0.51 (FT rate 7.58, modest PSI)

Kansas freshman SG, 14.31 pts/36 projected. **T.J. Warren / Mikal Bridges** comps. Methodology converges around mid-lottery; advanced metrics modest but not weak. Limited NCAA minutes 697 reduces confidence.

### Pick 12 — Jack Kayil (Alba Berlin, PG) ★ LOW CONFIDENCE FLAG
**Score: 0.62** — v3 #4 / hand #17 / advanced N/A (no NCAA PBP) / intl_low_n_penalty -0.12 applied

The only intl prospect in our Top 14. BBL bucket has n=1 historical anchor (Killian Hayes #7 pick). 2026 BBL Best Young Player + FIBA Champions League Best Young Player accolades suggest real talent (12.6 ppg / 3.5 apg / 33.7% 3PT over 38 games for Alba Berlin). **D'Angelo Russell / Nico Mannion** comps. Confidence is the lowest in our top 14 — could be anywhere from #4 to #25.

### Pick 13 — Tyler Tanner (Vanderbilt, PG)
**Score: 0.59** — v3 #32 / hand #7 / advanced 0.53 (PSI 1.85, FT rate 7.24)

Production composite (hand) loved him at #7; v3 said #32. Resolve takes the middle. **Spencer Dinwiddie / Malachi Flynn** archetypal comps. PSI top-15 and reasonable FT rate.

### Pick 14 — Christian Anderson (Texas Tech, PG)
**Score: 0.58** — v3 #24 / hand #13 / advanced 0.37 (PSI 1.90, modest other)

Round out the lottery with a Texas Tech PG. **Nico Mannion / Tyrone Wallace** comps. Lower advanced signal but cross-method agreement at mid-lottery.

---

## OUTSIDE LOTTERY (15-25) — notable mentions

| Rank | Player | Why outside |
|---:|---|---|
| 15 | Maliq Brown (Duke C) | 65 STEALS as a big = defensive unicorn but Duke 6% pts share = role player ceiling |
| 17 | Kingston Flemings (Texas Tech PG) | PSI 2.10 top-3 but other signals modest |
| 18 | Tarris Reed Jr. (Michigan C) | def_rate 12.66 + 69 blocks; v3 #15 / hand #62 |
| 19 | Dillon Mitchell (Texas PF) | v3 #9 but hand #64 — split-method |
| 21 | Zuby Ejiofor (St. John's C) | STD 1.53 + FT rate 9.31 + def_rate 9.70 — borderline lottery |
| 25 | **Baba Miller** (Florida State PF) | Hand #2 but v3 #53 BUST CALL holds despite STD 1.55 — methodology says NOT a top-15 talent |

---

## BOLD PRE-REGISTERED PREDICTIONS

### Public Consensus DISAGREEMENTS we're committing to

**OUR HIGH, CONSENSUS LOW:**
- **Aday Mara at #7** — consensus has him late-1st/undrafted. We say he's a true lottery 7'3" with elite STD + 103 blocks.
- **Caleb Wilson at #6** — consensus mid-1st. Advanced metrics say top-10.
- **Hannes Steinbach at #10** — consensus 2nd round. Top-10 STD + def_rate says lottery.
- **Ebuka Okorie at #9** — consensus 2nd round. PSI #3 in class says lottery PG.
- **Amari Allen at #5** — consensus mid-1st. Methodology converges higher.

**OUR LOW, CONSENSUS HIGH:**
- **Cooper Flagg-style — none in 2026 class.** Boozer is our consensus-agreed #1-3.
- **Koa Peat (Arizona, PF) outside our Top 14** — consensus top-5. Our v3 says #49, advanced metrics don't rescue him. Resolve top 14 doesn't include him.
- **Baba Miller (Florida State, PF) at #25** — consensus top-15. Our v3 #53 bust call holds.
- **Cameron Carr / Ryan Conwell (NCAA P5 sleepers)** — v3 had them top-3 but advanced metrics didn't support; outside our Top 14.
- **Karim Lopez (NBL)** — survivorship penalty + intl_low_n haircut pulled him to #30s.

### Locks (highest confidence)
- **Cameron Boozer + Joshua Jefferson + AJ Dybantsa** as the top-3 of any direction. We don't know which order the actual draft will take but at least one of these three goes #1.

### Specific named contrarian calls (bold-prediction discipline per [[feedback-bold-timestamped-predictions]])
1. **Aday Mara goes top-10 in the actual draft** — public mocks have him outside top-20
2. **Baba Miller doesn't go top-15** — public mocks have him top-5
3. **Caleb Wilson goes top-15 in the actual draft** — public mocks have him 15-25
4. **Hannes Steinbach goes top-20** — public mocks have him 2nd round
5. **Ebuka Okorie goes top-25** — public mocks have him late-2nd / undrafted

---

## Substrate gaps we honestly acknowledge

- **Intl prospects** (De Larrea / Lopez / Suigo / Kayil) have limited per-league anchor data. Kayil at #12 is our LOWEST confidence pick. De Larrea / Lopez / Suigo dropped from lottery due to survivorship signals. We may be wrong about ANY of them; the substrate isn't deep enough for high confidence.
- **NCAA advanced metrics** require PBP we have only for 2025-26 season; we don't have historical training samples with the same features. The 30% weight on advanced is unconditioned on outcome.
- **Defensive metrics for non-Centers** are weak. PSI/STD/FT-rate help guards and forwards; def_rate dominates bigs. Guards may be under-weighted on the defensive side.

---

## Files

- Final synthesized board: `data/parquet/resolve_lottery_2026.parquet`
- v3 outcome-calibrated rank: `data/parquet/draft_2026_outcome_calibrated_v3.parquet`
- Hand-composite rank: `data/parquet/draft_2026_projections.parquet`
- Advanced metrics: `data/parquet/prospect_advanced_metrics_2026.parquet`
- Teammate context: `data/parquet/prospect_teammate_context.parquet`
- Survivorship signals: `data/parquet/draft_2026_outcome_calibrated_v3.parquet` (column: `survivorship_signal`)
- League strength multipliers: `data/parquet/league_strength_multipliers.parquet`
- Crossover edges: `data/parquet/crossover_edges.parquet`

## Methodology trail

- [Rookie Decomp Suite](ROOKIE_DECOMP_SUITE_2026_06_07.md) — base translation factors + archetype clusters
- [Draft Prep v1.2](DRAFT_PREP_2026_v1.md) — initial hand-composite board
- [Competition Normalization v1](COMPETITION_NORMALIZATION_2026_06_07.md) — outcome-calibrated GBM + crossover graph
- [Competition Normalization v2](COMPETITION_NORMALIZATION_V2_2026_06_07.md) — intl label refresh + survivorship diagnostic
- [Competition Normalization v3](COMPETITION_NORMALIZATION_V3_2026_06_07.md) — historical intl stat anchors
- [Competition Normalization v4 honest](COMPETITION_NORMALIZATION_V4_HONEST_2026_06_07.md) — teammate features didn't beat v3
- [Prospect Advanced Metrics](PROSPECT_ADVANCED_METRICS_2026_06_07.md) — NCAA PBP advanced features

## Cardinal rule held throughout

Zero third-party rankings (ESPN / Tankathon / The Ringer / Athletic mock drafts) used as inputs. The combine invitee list is the eligibility pool, not a ranking. All stats are raw box-score, PBP, and per-game observations.

## Post-draft eval (locked plan)

After the 2026 NBA Draft (late June 2026), evaluate Resolve Lottery against:
1. Actual pick number (rank delta per prospect)
2. NBA Year-1 production (per-36 stats vs predicted)
3. Honest accounting of where each method (v3 / hand / advanced / Resolve) called it right vs wrong

This is the receipts trail. Bold predictions get evaluated, not buried.
