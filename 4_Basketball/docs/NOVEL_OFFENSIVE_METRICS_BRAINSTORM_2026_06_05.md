# Novel offensive metrics brainstorm — 2026-06-05

Purpose: identify candidate offensive metrics that are (a) novel vs public stat sources, (b) feasible with our substrate, (c) testable as falsifiable variance-signature additions to the existing methodology suite.

Companion to desktop's offensive variance-signature suite (ROEI / ESPS / TLOR / CROVC / UVDS / CSOP / IFVD / LMOC / PBAP + EORR composite + EVSH calibration + ODAD cross-product + aging-curve regime detection). **This doc fills the categories desktop didn't touch.**

## Substrate audit (what we have right now)

| Substrate | Coverage | What it unlocks |
|---|---|---|
| PBP parquet | 2019-20 → 2024-25, ~600k events/season, shot coordinates (x_legacy/y_legacy), shot_distance, shot_result, action_type, sub_type, clock, score_home/away, description text, action sequence ordering | Sequence/timing/spatial-shot/context metrics |
| Shotchart parquet | 2019-20 → 2024-25, shot zones + LOC_X/Y per shot | Shot-distribution + zone-specific metrics |
| Box-score (BBRef) | All seasons, traditional + advanced | Production baselines for normalization |
| CTG (Cleaning the Glass) | scraped subset | Filtered-possession efficiency, location data |
| DARKO DPM | full | Public-best impact metric baseline |
| v4-lite projection | 18-stat posteriors with joint samples | Calibrated uncertainty for any new metric we ship |
| Synergy play-types | NOT in stack | Would unlock iso/PnR/spot-up/post-up granularity |
| Second Spectrum / NBA tracking | NOT in stack | Would unlock defender distance, gravity, off-ball location |

**Feasibility tags** used below: **T1** (build today with current PBP+shotchart+box-score), **T2** (build in a week with engineering — touch sequencing, possession tagging, etc.), **T3** (needs Synergy or tracking subscription).

---

## Category 1 — Off-ball gravity (the Reggie/Klay problem)

The most-loved player class in public discourse is the off-ball threat (Klay, Reggie, Korver). Public stats measure their points but not the *attention they consume*, which is the actual mechanism.

| Metric | What it measures | Feasibility | Why novel |
|---|---|---|---|
| **GAP — Gravity-Adjusted Points** | Player points generated MINUS expected via gravity alone. Defenders MUST close out a 38% 3PT shooter even on a poor possession; that's "free" attention. GAP isolates *generative* scoring from "they have to guard me anyway" benefits. | **T3 ideal** (defender distance), **T2 proxy** (catch-and-shoot share + 3PT% as gravity proxy) | Nobody publishes a gravity-adjusted points number |
| **Skill-Specific Gravity** | Decompose gravity by skill: defenders react DIFFERENTLY to drive-threat vs shoot-threat vs lob-threat. Public "gravity" treats it as monolithic. | **T3** | Frontier |
| **Corner-Camp Tax** | % of off-ball time camping the deepest corner positions. High = spacer/low utility. Negative-signal stat for the "stretch four" archetype the public over-prices. | **T2** (need possession tagging to know off-ball context); **T3 ideal** | Public corner-3 stats only count attempts, not camping behavior |
| **Off-Ball Generation Rate (OBGR)** | % of off-ball actions (cuts, screens, relocates) that result in either (a) shot for self, (b) shot for teammate within 2 passes, or (c) drawn-help leading to scramble | **T2 from PBP sequences** | Closest public metric is "screen assists" (vague + low-signal) |
| **Relocate-After-Shot Rate** | After taking a shot, does the player relocate or stand? Klay relocates; many spot-up shooters stand. Predictive of teammate efficiency on next possession. | **T2 with possession-end tagging** | Brand-new |

## Category 2 — Decision quality & processing (the IQ frontier)

Currently invisible in public stats. This is where the "high BBIQ" eye-test concretizes.

| Metric | What it measures | Feasibility | Why novel |
|---|---|---|---|
| **HSA — Half-Second Adherence** | % of touches where player releases the ball (shot/pass) within 0.5s. Spurs analytics concept ("the 0.5 rule"). Identifies quick decision processors. | **T2** (touch tagging + clock-delta) | Internal NBA orgs use this; nobody publishes it |
| **PDT — Pass Decision Time** | Average time from receive-to-decision (pass or shot or drive). Slow processors get jumped; fast processors break defenses. | **T2** | Same |
| **xDV — Expected Decision Value Residual** | For each receive event, model the optimal next-action value given context (defender pressure, shot clock, teammate openness). Player's actual decision EV minus xDV = decision quality residual. Pure measurement of basketball IQ on offense. | **T2-T3** (xDV model needs careful spec) | Frontier; the closest thing is EPV (Cervone et al.) but that's not productized |
| **Read Diversity Index** | Distribution of next-actions taken given identical pre-catch situations. High = unpredictable, low = scoutable. | **T2** | Frontier |
| **Pre-Pass Look Sequence** | For passers: do they look-off before throwing? (Manning-style). PBP has no eye data so this is **T3** unless inferred from defender shift patterns. | **T3** | Frontier |

## Category 3 — Hustle generators that nobody measures

NBA "hustle stats" (deflections, loose balls, screen assists) are too crude. Real hustle is per-opportunity rate, not per-game count.

| Metric | What it measures | Feasibility | Why novel |
|---|---|---|---|
| **LBROI — Loose-Ball ROI** | Denominator = loose-ball events within X feet of the player; numerator = how many recovered. Per-opportunity rate. | **T2** (PBP gives loose-ball events; proximity needs tracking or proxy) | Public "loose balls recovered" is a raw count |
| **SQC — Screen Quality Conversion** | For screen-setters, conversion rate of screens → quality action (shot/drive/draw-help) divided by screens set. | **T2** (screen events approximated from PBP descriptions) | "Screen assists" is the closest public metric but it's coarse |
| **CVI — Closeout Velocity Index** | How hard does player close out on 3PT shooters? Final defender distance + closeout time. (Offensive-relevant: which off-ball shooters get LIGHT closeouts because the defender doesn't fear them?) | **T3** (needs tracking) | Frontier |
| **50/50 Win Rate** | In transition scrambles, who comes out with the ball. | **T2** | Nobody publishes |
| **OBA — Offensive Rebound After Own Miss** | Per-attempt rate of getting your own miss back (a leak in current ORB%). | **T1** (PBP descriptions identify miss → next event) | Frontier sub-metric |
| **FBR — Floor-Burn Rate** | Possessions ending in player diving/sliding for the ball. (Offensive analog: dive for loose balls + tip-outs) | **T2** | Public hustle stats track "loose balls" but not the body-investment angle |

## Category 4 — Creativity & unpredictability (Shannon's offensive metrics)

| Metric | What it measures | Feasibility | Why novel |
|---|---|---|---|
| **PPE — Pass-Pattern Entropy** | Shannon entropy of pass-target distribution. High entropy = passes to many different teammates from many positions = creative & hard to defend. Low entropy = predictable. | **T1** (assist sub-types in PBP) | Frontier; nobody applies info-theory to passing |
| **STD — Shot-Type Diversity** | Shannon entropy across (corner3, top3, mid, drive, post, putback, transition). Diversity premium for hard-to-scout players. | **T1** (shotchart zones) | Nobody publishes shot-type entropy as a single number |
| **ADI — Action Diversity Index** | Entropy across initiated play-types (drive, post-up, P&R-ball, P&R-roll, spot-up, cut, ISO, transition). Hard-to-scout players score high. | **T2-T3** (needs Synergy ideal; PBP description parsing as proxy) | Frontier |
| **Surprise Premium** | Bayesian update of EV given unexpected action. Penalized if surprise is low-EV (chucker tax). Reward unexpected high-EV plays. | **T2** | Frontier |
| **Defender Misdirection Score** | % of plays where the player's pre-action move successfully misdirects the defender (telegraphed shot fake → blow-by, behind-the-back to a teammate the defender wasn't ready for). | **T3** | Frontier |
| **Cross-Match Vulnerability** | Variance of opponent's defensive scheme vs a player's chosen counter. High variance + sustained efficiency = "they can't game-plan against him". | **T2-T3** | Closest is "vs zone vs man" splits but not as composite |

## Category 5 — Foul drawing as an offensive skill

Currently buried in FTA totals. Drawing fouls is a real skill that varies massively across players and contexts.

| Metric | What it measures | Feasibility | Why novel |
|---|---|---|---|
| **And1R — And-1 Rate** | % of made shots that draw a foul. Different from FTA/FGA ratio. Identifies players who *finish through contact*. | **T1** (PBP has "And 1" descriptions) | Surfaced but not as a primary metric publicly |
| **FDQ — Foul-Draw Quality** | Drawing fouls in high-leverage spots (close-game late minutes) vs garbage time. | **T1** (PBP has clock + score) | Frontier |
| **DFC — Drive Foul Conversion** | % of drives that result in FTA. Identifies attack-oriented finishers. | **T1** (PBP descriptions identify drives) | Frontier composite |
| **SFG — Sneaky Foul Generation** | Being fouled on off-ball cuts, screens, rebounds (effort fouls vs shooting fouls). | **T1** (PBP differentiates shooting foul vs personal) | Frontier |
| **FT-EFF — FT-Drawing Efficiency** | FTAs per (touch_count × usage_rate) — controls for volume to surface true skill | **T2** | Nobody publishes a normalized version |

## Category 6 — Scheme read-and-react (vs defense type)

Currently completely invisible in public stats. Some players annihilate zones, others vanish against switching.

| Metric | What it measures | Feasibility | Why novel |
|---|---|---|---|
| **vs-Zone Efficiency** | TS% / drive rate / pass rate in possessions where opp plays zone vs man | **T3** (needs scheme detection; PBP doesn't tag zone vs man) | Frontier |
| **Switch-Hunt Effectiveness** | Possessions initiated to find a switch mismatch + conversion rate. | **T3** (Synergy) | Frontier |
| **vs-Drop Mid-Range Game** | Mid-range conversion vs drop pick-and-roll coverage. | **T2-T3** | Frontier |
| **vs-Blitz Response Time** | When trapped, decision time + accuracy. | **T3** | Frontier |
| **Coverage-Diversity Premium** | EV against the rarest opponent coverages (low-frequency = low-prep) | **T3** | Frontier |

## Category 7 — Touch & possession dynamics

| Metric | What it measures | Feasibility | Why novel |
|---|---|---|---|
| **TAR — Touch-to-Action Ratio** | Average touches before scoring action. Low = decisive, high = methodical. | **T2** (touch sequences from PBP) | Frontier |
| **PEPT — Possession-End Probability per Touch** | Which players' touches end the possession most often. Distinguishes finishers from connectors. | **T2** | Frontier composite |
| **DE — Dribble Economy** | Points generated per dribble. Identifies "every dribble has a purpose" archetype. | **T3** (need dribble counts; tracking) | Frontier |
| **TOPE — Time-of-Possession Efficiency** | Points generated per second of dominant ball-holding. | **T3** | Frontier |
| **PV — Possession-Value Trajectory** | EV evolution across the possession's lifespan with this player handling | **T3** | Frontier |

## Category 8 — Late-clock / pressure mastery

PBP has the clock natively, so most of this is **T1**.

| Metric | What it measures | Feasibility | Why novel |
|---|---|---|---|
| **LCV — Late-Clock EPV** | Per-possession value when shot clock < 7s. Some players THRIVE here (Bird, Curry, Booker), others wilt. | **T1** | Frontier |
| **CSC — Catch-and-Shoot Clock Profile** | Early-clock vs late-clock conversion rates. | **T1** | Closest is overall C&S%; the clock-split is novel |
| **DSP — Decision Speed Under Pressure** | Does decision time SHRINK or STRETCH in late-clock vs early-clock? Veteran players often shrink. | **T2** | Frontier |
| **CET — Clutch EV Trajectory** | Possession-by-possession EV in clutch (≤5 pts, last 5 min) — does player escalate or fade? | **T2** | Frontier |

## Category 9 — Conditioning & game-state context

| Metric | What it measures | Feasibility | Why novel |
|---|---|---|---|
| **PFE — Per-Minute Fatigue Erosion** | EV decline as minutes-played count rises within a game. The Westbrook-finishing-strong vs the LeBron-coasting distinction. | **T1** | Public minutes data is just count; PFE is the slope |
| **B2B Decay** | Production drop on back-to-back nights. (Currently buried in "rest day splits".) | **T1** | Surfaced but not productized |
| **Cold-Start Coefficient** | First 2 min off bench: production vs typical. Some players need warmup; some come in firing. | **T1** | Frontier sub-metric |
| **GSL — Game-State Leverage Production** | Production weighted by leverage index (close-game late minutes) | **T1** | Closest is "clutch stats" but binary; LEV is continuous |
| **TPS — Trailing-Team Production** | Scoring rate when team down 5+ vs ≤5. The "garbage time inflater" tax. | **T1** | Public has clutch but not the trailing-vs-leading split |
| **LP — Lead-Protection Rate** | Per-possession EV when team is up 5-10 (don't blow the lead). | **T1** | Frontier |

## Category 10 — Style archetypes (unsupervised)

Position labels (PG/SG/SF/PF/C) are obsolete. Better: unsupervised clustering on play-style vectors.

| Metric | What it measures | Feasibility | Why novel |
|---|---|---|---|
| **Style Vector** | Per-player vector across (shot-type distribution, touch sequencing, screen usage, off-ball pattern, transition usage) | **T2** | Some private versions exist; no public clustering produced as a product |
| **Archetype Clusters** | k-means or HDBSCAN on Style Vectors — produces 8-15 modern archetypes (e.g., "low-usage 3&D wing", "scoring lead guard", "stretch big", "screen-and-roll center", "movement shooter") | **T2** | Frontier as a published product |
| **Connector Score** | Passes that lead to scores generated by OTHER players within 2 passes. (Jokic vs JJJ distinction.) | **T1** | Closest is secondary assists; CS is a normalized version |
| **Hub vs Spoke** | Passes generated FROM you vs passes received BY you, normalized | **T1** | Frontier |
| **Glue Composite** | Off-rebounds + secondary assists + screen assists + deflection turnovers caused. The unglamorous winning stats. | **T1** | Public components exist; the composite isn't packaged |

## Category 11 — Skill-specific aging

Desktop's brainstorm mentions aging-curve regime detection. Add a layer:

| Metric | What it measures | Feasibility |
|---|---|---|
| **Per-Skill Aging Curves** | Shoot vs handle vs defend vs lateral quickness — each declines on a different curve. Currently treated monolithically via age. | **T2** |
| **Mileage Adjustment** | Career minutes loaded → aging curve shift. High-mileage stars decline faster than preserved stars. | **T2** |
| **Skill Cliff Detection** | Statistical change-point detection on each skill independently. | **T2** |

## The synthesis — how this fits desktop's variance-signature suite

Desktop's brainstorm = **how does VARIANCE behave across regimes** (ROEI variance shift in playoffs; ESPS shot-zone stability; UVDS usage decoupling).

This brainstorm = **what's the CONTENT being made stable** (gravity, decision speed, hustle, creativity, scheme read).

They are **complementary**, not competing. The joint product:

- Desktop's suite: "Player X has stable variance across regimes."
- This suite:     "Player X is stable BECAUSE he has high HSA, high PPE, and high LCV."

A player with high ESPS (stable shot profile) might score that way because of high PPE (creative passer who finds his spots) or because of low Read Diversity (one-note finisher whose role is well-defined). Joint metrics resolve the mechanism.

### Tiered ship priority

**Beachhead (T1, build this week, validate on existing PBP):**
1. **PPE — Pass-Pattern Entropy** — pure info-theory on assist sub-types; cheap, novel, instantly interpretable
2. **STD — Shot-Type Diversity** — Shannon entropy on shotchart zones
3. **And1R / FDQ / DFC / SFG** — the four foul-drawing breakdowns
4. **LCV — Late-Clock EPV** — clock-split on possession value
5. **PFE — Per-Minute Fatigue Erosion** — within-game EV decline regression
6. **TPS — Trailing-Team Production** — context-aware production split
7. **CS — Connector Score** — secondary-assist composite
8. **And1R surfaced as a standalone metric** — most underrated offensive skill in public discourse

These 8 are all **T1**, each becomes one parquet → one viz on the website, each is novel vs public stats. **Two-week sprint.**

**Mid-term (T2, build in a month):**
- HSA / PDT / xDV (decision quality bundle) — requires touch sequencing from PBP
- ADI / Style Vector / Archetype Clusters — requires play-type tagging
- LBROI / SQC / OBGR (hustle bundle) — requires possession-context tagging
- TAR / PEPT (touch dynamics) — requires possession sequencing

**Long-term (T3, needs substrate buy):**
- GAP / Skill-Specific Gravity / CVI / Misdirection — needs tracking subscription
- vs-Zone / vs-Switch / vs-Drop / vs-Blitz — needs Synergy
- DE / TOPE — needs tracking

**Synthesis composite — "Resolve Offensive Intelligence" (ROI):**
- Decision (HSA + xDV)
- Creativity (PPE + STD + ADI)
- Off-ball gravity (GAP or proxy)
- Hustle generation (LBROI + SQC + OBGR)
- Late-clock mastery (LCV + DSP)

Calibrated, posterior-distribution-shipped (mirroring EVSH for honest intervals).

## Cross-cuts with the rest of the stack

- **Joint with defensive suite** → Desktop's ODAD (offense-defense allocation differential) is the right axis for the website's "position-on-the-field" view
- **Joint with v4-lite** → these metrics feed back as features into the 18-stat projection; backtest whether including (say) PPE as a covariate lifts the AST projection
- **Joint with playoff machinery** → most of these have a playoff vs regular-season variance, which is the desktop frame (ROEI, CROVC for offensive side)

## The website pitch this enables

Most public NBA stat sites publish: PER, BPM, RAPM, DARKO, EPM, BBRef advanced.

We can publish: variance-signature regime stability (desktop) + decision-speed / creativity-entropy / hustle-rate / foul-skill / late-clock mastery (this doc) + the ODAD joint surface.

**Nobody else has this combined.** The methodology page documents (a) the validated defensive substrate, (b) the offensive composite as variance + content, (c) the calibrated-interval discipline. Three competitive moats stacked.

## Open questions / unknowns

1. **xDV / EPV** — proper expected-value modeling needs careful design. Cervone et al. published EPV in 2014 academically; nobody has reproduced it productized.
2. **Synergy data** — is a Synergy subscription on the table? Many T2 metrics jump to T1 with it.
3. **Tracking data** — is NBA Advanced Stats subscription (or Second Spectrum / Sportradar) on the table for the player-tracking work?
4. **xRoll on PPE** — the entropy framework might be more interesting with a position-cohort baseline (Centers have lower PPE because they pass less; need to normalize)
5. **Are we measuring or building?** — some metrics are PURE measurement (PPE), others require a predictive sub-model (xDV). The latter requires its own pre-reg/validation cycle.

## Recommended first move

Build PPE on the 2024-25 PBP data. ~half day of work, immediate face-validity check (Jokic / Haliburton / LeBron / CP3 should top the list; bench scorers and one-track finishers should bottom out), and if the rankings face-validate, that's the entire offensive entropy lane unlocked for the same scaffolding (STD / ADI / Read Diversity all use the same Shannon framework).
