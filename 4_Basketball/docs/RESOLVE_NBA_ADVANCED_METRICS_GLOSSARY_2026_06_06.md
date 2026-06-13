# Resolve NBA Advanced Metrics

A stack of metrics that don't exist anywhere else. Box scores tell you *how many*. Public advanced metrics like PER tell you *how good*. Ours tell you *how* — how a player scores, who carries late, who creates space for whom.

A few things to know:

- Every metric was face-validity tested before it shipped. If a metric said Bo Cruz had more impact than Jokić, we threw it out.
- Some metrics are signed. Positive doesn't always mean "better." Several are role indicators, not value judgments.

---

# Offensive metrics

## PSI — Pass Spread Index
*Redistributor vs. funneler*

**What it measures:** Whether a player spreads their assists across many teammates, or sends most of them to one or two top scorers. It's a structural-role indicator, not a value judgment.

**How to read it:** Positive PSI = "spreads the wealth" (Pritchard, KD, Klay). Negative PSI = "feeds the system" — Draymond Green is the most extreme funneler in the NBA (32.6% of his assists go to Curry); Christian Braun sends 42% of his to Jokić.

---

## STD — Shot-Type Diversity
*Versatile scorer vs. specialist*

**What it measures:** How spread out a player's shot diet is across the seven shot zones on the court. A single number for "do they shoot from everywhere or one spot?"

**How to read it:** High = shoots from everywhere (Mikal Bridges, Embiid the only Center cracking the top 25). Low = specialist; the bottom is dominated by rim-only Centers (Gobert, Hayes). Giannis ranks low — confirms the long-running take that he doesn't shoot enough from outside.

---

## STD-pos — Shot-Type Diversity by Position
*Most versatile shooter for your archetype*

**What it measures:** Same as STD, but ranks players against others at their position. "Is Embiid versatile *for a Center*" instead of "is Embiid versatile vs all NBA players."

**How to read it:** Surfaces the most versatile and most specialized at each position. Most versatile: Ryan Rollins (PG), Josh Green (SG), Mikal Bridges (SF), Jaden McDaniels (PF), Wendell Carter Jr. (C). Most specialized: James Harden (PG), Sam Merrill (SG), Ausar Thompson (SF), Zion (PF), Rudy Gobert (C).

---

## ADI — Action Diversity Index
*Does this player have one move, or every move?*

**What it measures:** Variety of *shot type* — not where the shot is, but how it's created (rim attack, jumper, pullup, floater, hook, post-up). Some players have one signature move; others have the full encyclopedia.

**How to read it:** **Nikola Jokić is #1** — the most varied offensive vocabulary in the league. Vučević, Jaren Jackson Jr., Cunningham, Bam, Brunson all top 10. Bottom: pure rim runners (Trayce Jackson-Davis is 93% rim) or pure shooters (Sam Merrill is 66% jumpers).

---

## And1R — And-1 Rate
*Finishing through contact*

**What it measures:** What percent of a player's makes also draw a foul on the same play. Isolates a specific skill: finishing through contact instead of getting deflected.

**How to read it:** Top: KAT and Edwards convert nearly 1 of every 5 makes into and-1s. Luka, Giannis, DeRozan, Paul George, Zion all in the 22–23% range. Bottom: pure jump-shooters who don't initiate contact (Sam Merrill, Beal, Strus).

---

## DFC — Drive Foul Conversion
*The aggressive-driver test*

**What it measures:** Of all the times a player drives to the basket, how often do they draw a shooting foul. Isolates aggression: who attacks the rim hard enough that defenders have to foul.

**How to read it:** Cam Thomas at 20.8% is the highest rate in the NBA. KD, Luka, Banchero, Giannis, Edwards all 17–20%. A clean wrinkle: Edwards is high in DFC but low in And1R — he draws fouls on drives but doesn't always finish through them.

---

## FDQ — Foul-Draw Quality
*Drawing fouls when it matters*

**What it measures:** Not all and-1s are equal — a clutch and-1 means more than a 30-point-blowout and-1. FDQ surfaces who reliably draws fouls in the moments that count.

**How to read it:** **Jalen Brunson is #1.** Of any high-volume scorer in the NBA, Brunson gets fouled on clutch makes the most often. Trae Young, Cam Johnson, Brandon Miller, Edwards, DeRozan, Bam Adebayo all top of the leaderboard.

---

## TPS — Trailing-Team Production
*Who delivers when the team is behind?*

**What it measures:** Scoring efficiency split three ways — when the team is down 5+, when the game is close, and when the team is up 5+. Tells you who scores well in which game-state.

**How to read it:** Top trailing-team scorers are mostly rim attackers (Jarrett Allen, Shai, Zubac, Giannis). Top close-game scorers are the actual clutch list: Paul George, McCollum, De'Aaron Fox, Mikal Bridges, Jokić, Naz Reid. Bottom in trailing-team: star shooters whose efficiency drops when forced to carry (Mitchell, Lillard, Haliburton, Edwards, Klay).

---

# Defensive metrics

## RPV — Rim Protection Value
*The Gobert / Wembanyama / Brook Lopez index*

**What it measures:** How much a defender takes the rim away — opponent makes at the basket fall when they're on the floor.

**How to read it:** Higher = bigger rim deterrent. Wembanyama #1 by a wide margin. Brook Lopez, Walker Kessler, Gafford, Gobert, Bam, AD all elite tier. The most face-valid metric in the defensive suite.

---

## TADEC — Teammate-Adjusted Defensive Event Creation
*Who creates the steals, blocks, and deflections themselves?*

**What it measures:** Defensive events a player generates that wouldn't happen without them — independent of which teammates they're playing alongside.

**How to read it:** Top = creates events the team would otherwise miss. Wembanyama, Matisse Thybulle, Alex Caruso, Toumani Camara lead. These are players whose defensive event totals are theirs, not their lineup's.

---

## DHA — Defensive Headroom-to-Activate
*Who turns it on in the playoffs?*

**What it measures:** How much a player's defensive engagement rises from the regular season into the playoffs. Catches "has another gear" vs. "already at max year-round."

**How to read it:** High DHA = leaves defense on the table in the regular season, picks it up when it matters. Low DHA = already max effort year-round. Neither is "better" — they're different defensive personalities.

---

## DES — Defensive Engagement Stability
*Predictable vs. boom-or-bust defenders*

**What it measures:** How consistent a player's defensive engagement is from regime to regime. The "is this defender reliable game to game" indicator.

**How to read it:** High = predictable defender, same engagement every regime (Draymond Green, Bam Adebayo, AD, Marcus Smart). Low = boom-or-bust, hard to project. Doesn't grade defensive quality — grades forecastability.

---

## PESC — Pair Event-Share Coupling
*Which defensive duos split work vs. activate together?*

**What it measures:** Whether two teammates' defensive contributions rise together or trade off across the season.

**How to read it:** Negative = shift-defenders, they trade off the load (Butler/Bam is this archetype). Positive = both activate together. Most famous defensive pairs land negative — when one is racking up events, the other dials back. It's structure, not a flaw.

---

## DFS — Defensive Footprint Stability
*The coach version of DES*

**What it measures:** How steady a head coach's defensive identity stays from year to year. A fingerprint of "how much does this coach's defense vary over time."

**How to read it:** Spoelstra ranks last, Carlisle 27, Budenholzer 25, Thibs 23 — not because their schemes are inconsistent, but because long tenures span multiple roster eras with different defensive personalities. Read it as a footprint stability, not as a grade on scheme quality.

---

## ERDR — Effective Resolve Defensive Rating (composite)
*The three-axis defensive grade*

**What it measures:** The official Resolve defensive rating — but not a single number. It's a 3-axis vector: RPV (deterrence), TADEC (event creation), DHA (engagement shift).

**How to read it:** A player can be elite on one axis and average on another. Wembanyama is elite on all three. Brook Lopez elite on RPV, average on TADEC. Thybulle elite on TADEC, middling on RPV. There's also **ERDR-adj** that adjusts for offensive usage — identifies defenders whose impact is earned, not bought by being a low-usage offensive player.

---

*Last updated 2026-06-06.*
