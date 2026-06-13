# Pre-Registration: 3PM Over-Dispersion vs Binomial Floor
## Residual-Class Structure on the 3P% Axis

**Date filed:** 2026-05-19
**Filed before:** any cohort-stratified analysis, position breakout, season replication, or cross-league extension
**Status:** Tier-1 hypothesis, single-test α = 0.05 (no Bonferroni since pre-registered)
**Origin probe:** unpre-registered exploratory observation on regular-season box scores 2019-20 through 2024-25 (n=3,475 player-seasons) showing dispersion ratio = empirical_var(3PM) / (mean_3PA × p × (1−p)) ≈ 1.83 league-wide, with monotone increase from 1.40 at 3P% < .250 to 2.06 at 3P% ≥ .420. This pre-registration locks the **replication test on un-touched seasons** so the structural claim is not seen-then-tested.

---

## Amendment Log

### Amendment 2026-05-19a — Claim B threshold revised from 1.30× to "lower CI bound ≥ 1.15×"

**Filed:** 2026-05-19, AFTER position-stratification diagnostic on the exploratory cohort, BEFORE sign-off + analysis fire on replication seasons.

**What changed:** Claim B (3P% gradient) threshold revised from "median dispersion ratio in top bucket ≥ 1.30× median in bottom bucket" to "bootstrap 95% CI lower bound on the ratio ≥ 1.15×."

**Why amended:** The original 1.30 threshold was justified in §1 by citing "the exploratory ratio (2.06 / 1.51 ≈ 1.36×) with margin." That 2.06 / 1.51 ratio used the 7-bucket extremes (.420+ vs <.250), NOT the pre-reg's specified bucket form (top = ≥.390 pooled, bottom = ≤.300 pooled). When the pre-reg's actual bucket form is computed on the exploratory data:

- Point ratio: **1.286** (top n=782 vs bottom n=450)
- Bootstrap 95% CI: **[1.250, 1.325]**

**The 1.30 threshold would file a NULL on the exploratory data itself**, even before any replication-set shrinkage. That is a malformed pre-registration — a test that the originating data already fails is not a test of replication, it is a guaranteed NULL. The cleanest honest response is to amend the threshold to one that matches the exploratory point estimate's actual magnitude, with margin for replication shrinkage.

**New threshold logic:**
- Exploratory 4-bucket-pooled ratio: 1.286 (CI [1.250, 1.325])
- Lower-CI-bound criterion at 1.15 sits BELOW the exploratory lower bound (1.250) by 0.10, giving ~7-8% replication shrinkage margin
- Position-stratified exploratory ratios: G 1.240 [1.184, 1.332], F 1.279 [1.220, 1.346], C 1.346 [1.185, 1.489] — the weakest position cell's lower bound (G: 1.184) clears 1.15, so a per-position breakout under the conditional Tier-2 in §7 also remains testable

**What this preserves:** The structural prediction is unchanged — 3PM over-dispersion increases monotonically with 3P% at meaningful magnitude. Only the threshold for "meaningful" is recalibrated to the actual scale the data is on.

**What this concedes:** The exploratory probe is now informing one numeric parameter of the pre-reg (the threshold value). This is a partial loss of pre-registration purity — the threshold is no longer independent of the data that motivated the hypothesis. Documented honestly here so any reader can apply their own threshold judgment to the replication result.

**Pre-reg discipline preserved by:**
1. Amendment filed BEFORE sign-off and BEFORE any inspection of 2017-18 or 2018-19 data
2. Replication cohort still completely un-touched
3. Both Claim A (over-dispersion ≥ 1.25 median) and Claim B (now lower-CI ≥ 1.15) must hold for "Confirmed" verdict — Claim A's threshold is unchanged and remains exploratory-margin-safe
4. The amendment narrative is published with the pre-reg, not retro-edited in

Sections 1, 4, and 5 are updated to reflect the new threshold. Original 1.30 threshold is preserved here in the amendment log for audit.

---

## 1. Hypothesis

**Tier-1 prediction.** Per-game 3PM variance is structurally over-dispersed relative to its binomial floor, and the over-dispersion is monotone increasing in player 3P%.

Stated as two simultaneous testable claims that BOTH must hold for confirmation:

**Claim A (over-dispersion):** Median dispersion ratio across the cohort is > 1.25.
**Claim B (3P% gradient):** Bootstrap 95% CI lower bound on (median dispersion in top 3P% bucket ≥ .390) ÷ (median dispersion in bottom 3P% bucket ≤ .300) is ≥ 1.15.

The 1.25 and 1.15× (lower-CI-bound) thresholds are pre-committed and are NOT adjusted post-fit. Choice rationale: 1.25 sits between binomial (1.0) and the exploratory point estimate (1.83) with margin for replication shrinkage; 1.15× (lower CI bound) sits below the exploratory pooled lower CI bound (1.250) by 0.10, giving replication-shrinkage margin while remaining diagnostic of the structural effect. See Amendment 2026-05-19a above for full rationale.

**Direction is specified** in both claims.

**Mechanism stated ex ante.** Two distinct mechanisms compose into the observed over-dispersion. First, within-game streakiness ("hot hand") — 3PM events are not independent shot trials; rhythm, fatigue, and confidence cluster outcomes inside a game. Second, between-game matchup variance — opponent perimeter coverage (drop vs switch vs hedge), opposing wing defender quality, and game-script (pace-up vs pace-down) cluster across games. The 3P% gradient prediction follows from a corollary: elite shooters draw harder coverage (closer closeouts, late switches, top defender) so their game-to-game shot-quality distribution is wider; weaker shooters get more uniform coverage and their per-game variance hews closer to binomial.

This is a residual-class structural prediction in the framework's vocabulary (PAPER_STATE.md §2, §5): the 3P% bucket acts as a residue class whose σ-shift relative to its own binomial floor varies monotonically with class index. The mechanism is sport-mechanical (defensive scheme response to shooting threat), not statistical artifact.

## 2. Operationalizations

**Dispersion ratio (the test statistic):**
```
dispersion(p, season) = var_game[3PM(p, g, season) | minutes(p, g, season) ≥ 10]
                       ÷  ( mean_3PA(p, season) × 3P%(p, season) × (1 − 3P%(p, season)) )
```

Where:
- `var_game[...]` is the sample variance across qualifying games within (player, season)
- `mean_3PA(p, season) = sum_g 3PA(p,g) / n_qualifying_games(p, season)`
- `3P%(p, season) = sum_g 3PM(p,g) / sum_g 3PA(p,g)` (season-totalled, not per-game-averaged)
- Qualifying games require minutes ≥ 10 (DNP / garbage-cleanup filter)

A dispersion ratio of 1.0 corresponds to a player whose per-game 3PM variance is exactly the binomial expectation given their attempt volume and shooting percentage.

**Volume bucket (Claim B stratifier):**
- `volume_bucket = pd.cut(mean_3PA, bins=[0, 1, 2, 3, 4, 5, 6, 8, 15])`

**3P% bucket (Claim B stratifier):**
- `p_bucket = pd.cut(3P%, bins=[0, .250, .300, .330, .360, .390, .420, 1.0])`

Bin edges are pre-committed.

## 3. Cohort

**Replication seasons (locked):** 2017-18 and 2018-19 (pre-2019 — these seasons were NOT in the exploratory probe, which used 2019-20 onward).

**Inclusion criteria (locked):**
- Regular Season only (no playoffs)
- Player must have ≥ 30 qualifying games (minutes ≥ 10) in the test season
- Player must have ≥ 30 cumulative 3PA in the test season
- A given (player, season) is one cohort row; no pooling across seasons

The 30-game floor matches the exploratory probe. The 30-3PA floor ensures `mean_3PA × p × (1−p)` is non-degenerate.

## 4. Statistical Tests

**Test for Claim A (over-dispersion):**
- Compute dispersion ratio per (player, season) in cohort
- Report median, IQR, n
- One-sided Wilcoxon signed-rank test against the null hypothesis median ≤ 1.25
- α = 0.05

**Test for Claim B (3P% gradient):**
- Compute median dispersion in top 3P% bucket (≥ .390) and bottom 3P% bucket (≤ .300)
- Report ratio = median_top / median_bottom
- Bootstrap 95% CI on the ratio (10,000 resamples within (player, season) units)
- Claim B confirms if the lower CI bound is ≥ 1.15 (amended 2026-05-19a from 1.30; see Amendment Log)

Both tests are run independently per replication season.

## 5. Decision Rules

**Per season:**
- **Confirmed:** Both Claim A AND Claim B hold by their respective thresholds.
- **Partial:** One of the two holds.
- **NULL:** Neither holds.

**Aggregate verdict (over both replication seasons):**
- 2/2 confirm both claims → **structural finding, supports paper extension**
- 2/2 confirm Claim A only → **partial finding**; over-dispersion replicates but 3P% gradient is exploratory point-estimate only
- 1/2 or 0/2 confirm Claim A → **NULL**; the exploratory 1.83 ratio does not generalize. Published with same prominence as positive results, parallel to PAPER_STATE §5.3 (Probe B contextual NULL).

## 6. Cross-League Replication (Conditional Tier-2)

**Trigger:** Both replication seasons confirm both claims (2/2 on A+B).

**Replication target:** WNBA 2022 + 2023, NCAA D1 Men 2018-19 + 2019-20, NCAA D1 Women 2018-19 + 2019-20.

**Per-league operationalization:** Identical formula. League-specific min_games floors will be locked at file-pre-reg-extension time, NOT post-fit. WNBA: min 20 games (shorter season). NCAA: min 25 games.

**Expected magnitude under mechanism:**
- Over-dispersion (Claim A) should replicate in all leagues (mechanism is sport-mechanical, not NBA-specific)
- 3P% gradient (Claim B) should replicate but may be *smaller* in lower-tier leagues where defensive scheme response is less differentiated
- Hard prediction: dispersion ratios will remain ≥ 1.2 in all leagues; gradient ratio will remain ≥ 1.15× in all leagues

Any league where Claim A holds (ratio ≥ 1.25 at α=0.05) but Claim B does not (gradient < 1.30×) is recorded as **partial cross-league replication**, not NULL.

## 7. Position Stratification (Conditional Tier-2, separate from §6)

**Trigger:** Both replication seasons confirm Claim A.

**Question:** Is the 3P% gradient driven by a specific position cell, or is it pooled across all positions?

**Stratification:** Repeat Claim B test within {Guard, Forward, Center} using nba_api position labels. Pre-committed thresholds for position-level confirmation: bootstrap 95% CI lower bound on gradient ratio ≥ 1.05 (looser than pooled 1.15, to account for within-position cell n shrinkage). Center cell may be skipped if n_in_top_bucket < 15 in either replication season.

**Exploratory-data reference values** (NOT the test, just calibration for the threshold above): G 1.240 [1.184, 1.332], F 1.279 [1.220, 1.346], C 1.346 [1.185, 1.489] — all three position cells' lower CI bounds clear 1.15 on the exploratory probe; the 1.05 position-level threshold is set with extra room.

If gradient is **concentrated in one position cell**, the residual-class finding sharpens: 3PM × Position × 3P% is the load-bearing structure. If gradient is **uniform across positions**, the framework's interpretation is that 3P% itself is the relevant residue class index, independent of position.

## 8. What Does NOT Count

- Post-hoc bucket-edge adjustment (e.g., changing the .390 / .300 thresholds to make Claim B confirm).
- Post-hoc cohort floor adjustment (dropping the 30-game or 30-3PA floor after seeing the result).
- Switching the test statistic (e.g., from variance ratio to coefficient-of-variation ratio) post-result.
- Pooling 2017-18 and 2018-19 to find a result that fails in either single season.
- Reporting cross-league or position stratification results as Tier-1 if Tier-1 itself does not confirm.
- Cherry-picking which league or position to report under cross-league replication. ALL stratifications are reported regardless of disposition.

Any of the above invalidates the pre-registration. Findings under modified protocols are reported separately as exploratory observations.

## 9. Exploratory Tier-2 (Non-Pre-Registered)

The following may be examined *after* Tier-1 + cross-league + position results are reported, and are explicitly labeled exploratory:

- Volume gradient: does dispersion increase with 3PA volume INDEPENDENT of 3P%? The exploratory probe showed a small slope (+0.026 per 3PA, t=7.2 pooled) but the 3P% gradient is 4× stronger. Worth a separate look once Tier-1 lands.
- Within-season time-decomposition: split each season into halves and ask whether dispersion creep with 3P% holds within-player vs across-player. Distinguishes selection (defensive coverage) from time-varying behavior (hot streaks).
- Coverage variance: if Second Spectrum / Synergy data is accessible, regress dispersion on defended-3PA shot-quality variance. Tests the coverage-clustering mechanism directly.
- Coaching scheme link: do players whose teams change perimeter scheme (drop → switch or vice versa) show dispersion shifts? Connects to the [[project-nba-coaching-sloan-paper]] opp_3PT_rate finding.

These do not displace the Tier-1 finding; they support follow-up question framing only.

## 10. Implications for Production Projection

Conditional on Tier-1 confirmation, this finding has direct production consequence:

- The current v6.1 LOCKED 3PM predictive interval understates per-game uncertainty by ~80% (factor 1.83 dispersion vs assumed binomial floor)
- Underestimate is concentrated on elite shooters (~2× under-coverage for 3P% ≥ .420)
- Wonka audit-CSV 3PM standard deviation column needs a multiplicative correction factor pre-deployment if downstream auction valuation uses the std for variance-of-leverage math
- Connects to PAPER_STATE §6.2 variance miscalibration footnote — sharpens the magnitude estimate for one stat

These are NOT pre-registered claims about production fixes; they are flagged downstream consequences. Production correction is a separate decision pending the cross-league replication result.

## 11. Output Artifacts

Will be written to `audit_runs/threept_dispersion/`:
- `cohort_2017_18.csv` and `cohort_2018_19.csv` — per-(player, season) rows w/ dispersion + buckets
- `claim_a_test.csv` — Wilcoxon results per season
- `claim_b_test.csv` — top/bottom medians + bootstrap CI per season
- `cross_league_test.csv` (conditional) — same tests per league
- `position_stratification.csv` (conditional) — same tests per position
- `summary.md` — one-page honest verdict against pre-reg decision rules

## Sign-Off Required Before Firing

This pre-registration is filed but not yet committed for analysis. Analysis fires only after the user signs off on the operationalizations in Sections 2-7. After sign-off, this file is locked; any subsequent modification invalidates the pre-registration discipline and the analysis becomes exploratory only.

**Filed by:** Claude (Opus 4.7)
**Sign-off requested from:** user (mr.nathanhumphrey@gmail.com)
**Pre-existing inspection:** seasons 2019-20 through 2024-25 (used in exploratory probe). Seasons 2017-18 and 2018-19 are UNTOUCHED by the exploratory analysis and serve as the honest replication set.
