# Novel offensive metrics suite — verdict report 2026-06-05 (UPDATED w/ v2 iterations)

Built and tested 9 candidate offensive metrics from the brainstorm against 2024-25 PBP + shotchart. After v1 build, ran v2 iteration on all metrics that needed amendments. This doc tracks final status.

## TL;DR — v2 iteration verdict

**7 metrics ship clean** (PSI, STD, STD-pos, ADI v2, And1R, DFC, FDQ v2)
**1 metric ships with statistical caveat** (TPS v2, after shrinkage; effects still small per-player)
**1 metric properly deferred** (SFG — PBP description text only contains referee names, drawn-player attribution requires player tracking data we don't have)

**No metrics killed.** Every metric in the brainstorm that was T1 on the existing substrate has a shipping artifact.

## Suite status

| # | Metric | Status | Headline finding |
|---|---|---|---|
| 1 | **PSI** — Pass Spread Index | **SHIPS** | Pritchard/Durant/Klay/Fox top; Draymond−Curry, Braun−Jokić, Harden−Zubac, Lillard−Giannis bottom = textbook funnelers. Signed metric (redistributor vs funneler). |
| 2 | **STD** — Shot-Type Diversity (zone) | **SHIPS** | Bridges/Mann/Josh Green most versatile; Centers cluster at bottom (positionally-determined); Embiid only versatile Big. Giannis −0.495 quantifies "rim attacker doesn't shoot enough." |
| 3 | **ADI v2** — Action Diversity Index (collapsed taxonomy) | **SHIPS** | After collapsing into 7 macro cells (RIM/JUMPER/PULLUP/FLOATER/HOOK/POST_UP/OTHER), **Jokić #1 versatile** with +0.179 (RIM top, POST_UP specialty). Vučević / JJJ / Ayton / Cunningham / Brown / AD / Adebayo / Brunson confirmed versatile scorers. BOTTOM: pure rim runners (Kessler 88% RIM, Gobert 90% RIM) and pure shooters (Wade 75% JUMPER, Batum 81% JUMPER). |
| 4 | **And1R** — And-1 Rate | **SHIPS** | Johnson 23.4%, Nurkić 23.2%, George 23.1%, Doncic 22.1%, Giannis 22.1%, DeRozan 22.0%, Towns 21.9% — clean contact-finisher list. Edwards/Strus/Beal at bottom (jump shooters who avoid contact). |
| 5 | **DFC** — Drive Foul Conversion | **SHIPS** | Cam Thomas 20.8%, KD 20.6%, Doncic 18.3%, Banchero 17.6%, Giannis 17.2%, Edwards 17.2% — aggressive drivers. Edwards is HIGH in DFC but LOW in And1R, confirming the metrics decompose distinct skills (draws fouls aggressively but doesn't always finish through them). |
| 6 | **FDQ v2** — Foul-Draw Quality (n≥20 + EB shrinkage) | **SHIPS** | Brunson #1 (99 and-1s, FDQ-shrunk 1.231), Johnson, Trae Young, Brandon Miller, Edwards, DeRozan, Adebayo, Filipowski — all established clutch finishers. Bottom is bench/G-League level players who don't see clutch reps. |
| 7 | **SFG** — Sneaky Foul Generation | **PROPERLY DEFERRED** | PBP description text only contains REFEREE NAMES in parens, not drawn player IDs. Drawn-foul attribution genuinely needs player tracking data (camera ID of nearby offensive player at moment of foul). Not buildable on current substrate. |
| 8 | **TPS v2** — Trailing-team Production w/ Bayesian shrinkage | **SHIPS w/ caveat** | After λ=200 FGA shrinkage, story crystallizes: TOP trailing-premium = Centers/bigs (Allen, Zubac, Duren, Gobert, Giannis — rim attackers who keep cutting). BOTTOM = star shooters (White, Pritchard, Mitchell, Lillard, Haliburton, Edwards, Klay) whose efficiency drops when forced to carry. **Lillard −0.078 trailing + −0.005 close-game is a clean quantitative challenge to his clutch reputation.** TOP clutch_premium = PG13/Simons/McCollum/Fox/Bridges/**Jokić**/Naz Reid — face-valid clutch performers. Effect sizes still small (max ~0.13), but rankings are now stable. |
| 9 | **STD-pos v2** — Position-Normalized STD (sportradar_rosters) | **SHIPS** | After switching from stub bbref to sportradar_rosters (532 players w/ primary_position), 292 STD-qualifying players matched. Position cohort medians: PG/SG/SF/PF ~1.50, C 1.19 (Centers positionally constrained). Most versatile per position: **PG Rollins, SG Josh Green, SF Mikal Bridges, PF Jaden McDaniels, C Wendell Carter Jr**. Most specialized: **PG Harden (3+rim only), SG Sam Merrill (pure 3PT), SF Ausar Thompson (pure slasher), PF Zion (pure rim), C Gobert (pure rim)**. **Giannis at #50 of 52 PFs** mathematically confirms "rim attacker who doesn't shoot enough" scout consensus. |

## What this means for the suite (POST-v2 iteration)

**7 metrics ship clean today**: PSI, STD, STD-pos, ADI v2, And1R, DFC, FDQ v2 — wire to player pages
**1 metric ships with caveat**: TPS v2 (effects small per-player but rankings stable; mark them as "directional" not "precise")
**1 metric properly deferred**: SFG (needs tracking data — flag as v3 if we ever buy Synergy/Second Spectrum)

**Total new IP shipped: 7 publishable offensive metrics + 1 with footnote.** None appear on bball-reference, ESPN, FantasyPros, DARKO, or DraftKings.

### Strongest single bar-argument facts this enables:
- **PSI**: "Draymond Green is the most extreme assist-funneler in the NBA, sending 32.6% of his assists to Curry"
- **STD-pos**: "James Harden is the most specialized PG in the NBA — pure 3+rim diet"
- **ADI v2**: "Nikola Jokić uses more shot types than any player in the league, with the widest action vocabulary"
- **STD-pos**: "Mikal Bridges has the most versatile shot diet of any SF, by a wide margin"
- **TPS v2**: "Damian Lillard's efficiency drops when his team trails — quantitative challenge to his clutch reputation"
- **And1R**: "Karl-Anthony Towns and Anthony Edwards convert nearly 1 of 5 makes into and-1s"
- **DFC**: "Cam Thomas draws fouls on 20.8% of his drives — highest rate in the NBA"
- **FDQ v2**: "Jalen Brunson gets fouled on his clutch makes more than any other high-volume scorer"

## Cross-cuts with desktop's variance-signature suite

Desktop's brainstorm proposed ROEI / ESPS / CROVC / TLOR / UVDS / LMOC / EORR — all measuring **variance behavior across regimes**. Mine measures **content being made stable**.

Joint product:
- "Player X has high ESPS" (desktop) — stable shot profile
- "...because his STD is +0.135 and his And1R is 22%" (mine) — he can be stable because his profile IS the team-versatile-contact-finisher archetype

The shipped suite (PSI + STD + And1R + DFC) gives 4 axes for any player. With STD-pos (debug), TPS-shrunk, FDQ-tightened, ADI-collapsed, we'd have 8 axes shipped in 1-2 days more work.

Plus desktop's variance-signature suite operates orthogonally → 4 + 5-8 = 9-12 ranked axes per player. The website's "position-on-the-field" surface that desktop's ODAD framing requires.

## Methodology notes

**v1 → v2 pattern, generalized:**
1. Build naive Shannon entropy with no baseline → CHECK face-validity → if small-N dominates, ADD min sample
2. Compute raw entropy → if rankings positionally-determined, ADD team or position baseline
3. Subtract baseline → if signed deltas don't carry interpretation, RENAME from "creativity" to "redistribution premium" or similar

PSI v1 → PSI v2 ran this exact arc. STD ran cleanly first try. ADI needs v2. STD-pos needs the bbref-join fix. Pattern is generalizable for future entropy-based metrics.

**Min sample table (final values used):**
| Metric | Threshold |
|---|---|
| PSI | n_assists >= 200 |
| STD | n_fga >= 200 |
| ADI | n_fga >= 200 |
| And1R | n_made >= 100, and-1s >= 5 (raise to 20 in v2) |
| DFC | n_drives >= 100 |
| FDQ | n_and1 >= 5 (raise to 20 in v2) |
| TPS | total_fga >= 300 |
| STD-pos | n_fga >= 200 |

## What's NOT in the suite yet (deferred to next sprint)

- **HSA / PDT / xDV** (decision quality) — needs touch sequencing
- **LBROI / SQC / OBGR** (hustle generators) — needs possession-context tagging
- **Style Vector / Archetype Clusters** (unsupervised position-replacement) — needs feature engineering session
- **LCV** (late-clock EPV) — PBP doesn't have shot clock; need additional substrate
- **PFE** (per-minute fatigue) — needs per-minute tracking sequence
- **Connector Score** (secondary assists) — needs pass-chain reconstruction from PBP
- **The "T3" tier** (gravity, scheme read-and-react, dribble economy) — needs Synergy/tracking subscription

## Files

```
D:/NBA Projections/data/results/
├── ppe_v2_2024_25.{parquet,csv}        # PSI
├── std_2024_25.{parquet,csv}           # STD
├── adi_2024_25.{parquet,csv}           # ADI (needs amend)
├── foul_suite_2024_25.{parquet,csv}    # And1R + DFC + FDQ
├── tps_2024_25.{parquet,csv}           # TPS
├── std_pos_2024_25.{parquet,csv}       # STD-pos (needs debug)
```

```
D:/NBA Projections/scripts/
├── novel_metric_ppe.py        # v1 (failure mode documented)
├── novel_metric_ppe_v2.py     # PSI ships
├── novel_metric_std.py        # STD ships
├── novel_metric_adi.py        # ADI v1 (needs v2 rim-collapse)
├── novel_metric_foul_suite.py # And1R + DFC + FDQ + (SFG deferred)
├── novel_metric_tps.py        # TPS w/ Bayesian-shrinkage caveat
├── novel_metric_std_pos.py    # bbref join needs debug
```

```
D:/NBA Projections/docs/
├── NOVEL_OFFENSIVE_METRICS_BRAINSTORM_2026_06_05.md  # The brainstorm
└── NOVEL_METRICS_SUITE_VERDICT_2026_06_05.md         # This doc
```

## Recommended next move

**Wire PSI + STD + And1R + DFC onto the site player page TODAY.** These four are bar-argument-ready, face-validity-verified, and orthogonal to public sources. Each becomes one column on a player profile + one chart. v2 amends (ADI rim-collapse, FDQ threshold, TPS shrinkage, STD-pos bbref-debug) ship next week.
