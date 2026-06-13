# Spec Amendments

Amendments to `projection_model_spec.md` accumulate here. The drift log
(`spec_drift_from_wonka.md`) covers fixes to the original; this file holds
**new requirements** that change the project's design after spec freeze.

When this list grows past ~5 items, fold them into a unified spec rewrite.

---

## 2026-04-25 — Advanced metrics as core inputs + audit dimension

User decision. Three coordinated changes across data, modeling, and audit.

### A. Data layer (amends §2.1) — RAPM, EPM, lineup data are now required inputs

**RAPM (Regularized Adjusted Plus-Minus)** and **EPM (Estimated Plus-Minus)**
are first-class inputs to the projection model alongside box scores. Source
candidates (decision pending separate research):

- DARKO daily metrics (`darko.app`) — historical RAPM-style + projections
- Dunks & Threes EPM (`dunksandthrees.com`) — public CSV downloads
- bball-index LEBRON (`bball-index.com`) — alternative composite metric
- basketball-reference BPM/VORP — already easily scrape-able

Lineup data **graduates from stretch goal to core requirement.** The
`LeagueDashLineups` endpoint provides 5-man unit minutes, off/def ratings,
and on/off splits. Phase 1 ingestion module ships with the rest of the data
foundation.

**Impact on Phase 1 (Foundation):**
- Add `ingestion/lineups.py` — wraps `LeagueDashLineups`
- Add `ingestion/advanced_metrics.py` — scrapers for RAPM + EPM + LEBRON
- Add data quality checks for the new tables (no nulls in lineup_id, sensible
  rating ranges -20 to +20, etc.)

**Impact on Phase 2 timeline:**
- Schema and join keys for advanced metrics need to be solid before skill
  estimation begins (advanced metrics are FEATURES of the skill model, not
  separate outputs)
- Estimate +1 week to Phase 2 to accommodate metric-source integration

### B. Skill estimation (amends §3.2) — Bayesian-hierarchical fusion of box-score and advanced-metric skill

Original spec specified per-minute and per-usage rates from box scores as the
only skill signal. The amendment adds advanced metrics as parallel skill
signals with **learned-weight Bayesian fusion**.

The hierarchical structure becomes:

```
For each player p, category c:
  box_skill[p, c]  ~ derived from per-minute box-score history (existing)
  adv_skill[p, c]  ~ derived from RAPM/EPM/LEBRON via category-specific mappings
  
  fused_skill[p, c] ~ w_box[c] · box_skill[p, c] + w_adv[c] · adv_skill[p, c]
  
  where w_box[c], w_adv[c] are CATEGORY-SPECIFIC weights LEARNED from
  historical performance (not fixed). Sum to 1 by construction.
```

The category-specific learning matters: advanced metrics encode defensive
impact (BLK/STL) and team-context-aware offense (AST under different
teammate skill) better than per-minute box rates. Per-minute box rates are
still better predictors of pure volume stats (FGA, FTM) where lineup
context noise dominates.

**Implementation:**
- Each weight pair `(w_box[c], w_adv[c])` has a Beta-Dirichlet prior fit
  from prior-season holdouts where both signals exist
- Posterior over weights is a project-level parameter (shared across
  players) — the model learns "advanced metrics are 70% of the signal for
  defensive cats, 30% for scoring volume" from data, not from priors
- Per-player skill estimation samples from the joint posterior over
  `(box_skill, adv_skill, weights)` so uncertainty in the weight learning
  propagates into per-player projections

**Mapping advanced metrics → category contributions:**

EPM and RAPM produce single composite numbers (offensive impact +
defensive impact). The model needs per-category contributions. Strategy:

- For each player-season where both box stats AND advanced metrics exist,
  fit a regression of advanced metric ~ box stats per category
- Residuals capture the "advanced-metric-specific" signal per player per
  category (the part not explained by box stats)
- Use these residuals as the `adv_skill[p, c]` quantity feeding the fusion

This sounds complex; in practice it's a 2-stage Bayesian regression that
runs once per metric per category — modest compute.

**Impact on Phases 2-3 timeline:** +1.5 weeks total (week per stage).

### C. Embedded audit (amends §5.5) — Advanced-metric disagreement detection

The audit harness gains a new dimension: **projection vs. historical
advanced-metric disagreement.**

Mechanism:
1. For each historical season we backtest, compute the advanced-metric
   "expected per-game outputs" by reverse-mapping (RAPM/EPM/LEBRON →
   per-cat means via the same mapping used in Section B above).
2. Compare our model's projection to both:
   - actual box-score outcomes (existing, primary)
   - advanced-metric implied expected outcomes (new)
3. Flag players where our projection disagrees with **both** actuals AND
   advanced-metric expectations as high-investigation targets — strong signal
   the model has a systematic blind spot for that player archetype.
4. Also flag players where projection matches actuals but disagrees with
   advanced metrics, and vice versa — useful for understanding where each
   signal source is telling us different things.

**Output additions to `audit_runs/{timestamp}/`:**
- `vs_advanced_metrics.csv` — per-player disagreement table
- `archetype_blind_spots.md` — player groups where projection-vs-actuals AND
  projection-vs-advanced-metrics both disagree

**Pass-gate addition:** if projection disagrees with both signals on >5% of
the player universe in any category, the run flags FAIL pending review.

**Impact on Phase 6 timeline:** +0.5 weeks.

---

## Cumulative timeline impact

Original: 28 weeks. With these amendments: ~31 weeks. Still ships pre-2026-27
season if work starts immediately and Phase 5 doesn't slip (rookies remain
the longest pole).

If timeline pressure mounts, the descope order is:

1. **First cut: ML parallel track** (already lowest priority per original spec)
2. **Second cut: advanced-metric audit dimension** (Phase 6) — keep model
   amendments, drop the audit comparison, add it back V1.1
3. **DO NOT cut: advanced metrics in skill model** — that's the point of
   this amendment
4. **DO NOT cut: lineup data ingestion** — required input

---

## Appendix — source decision pending

The exact RAPM/EPM/LEBRON source list isn't locked yet. WebFetch each
candidate's data page before committing. Critical decision factors:

- **Public availability** (CSV download or scrapeable HTML; not paywalled)
- **Historical depth** (need 2014-15+ to match rookie-class training window)
- **Update frequency** (daily for live use; per-season aggregate also useful)
- **License terms** (research use OK; redistribution constraints?)

### Verified 2026-04-25

- **DARKO** (`darko.app`) — VIABLE. Public CSV download from leaderboard
  ("Download CSV" button). Provides DPM (composite) + Off + Def + Box +
  On/Off splits. Updated nightly. Historical via season selector. **No
  scraping policy visible** — treat the public CSV as intended for export.
  TODO: capture the actual CSV download endpoint URL via browser network
  panel (not on the rendered page); parser scaffold is in place.

- **Dunks & Threes** (`dunksandthrees.com`) — PAYWALLED. Subscription
  required. **Dropped from V1 source list.** No reasonable scraping path.

- **basketball-reference advanced** (`basketball-reference.com`) — VIABLE.
  Per-season `/leagues/NBA_<endyear>_advanced.html` table. Provides BPM
  (composite) + OBPM + DBPM + VORP + PER + WS + USG% + TS%. Pinned as the
  EPM-equivalent signal substituting for the dropped Dunks & Threes source.
  Already integrated into `ingestion/advanced_metrics.py`.

- **bball-index LEBRON** — TBD, lower priority. Verify CSV availability
  later if we want a third independent source.

### Source matrix going into Phase 2

| Signal           | Source              | Status        | Composite | Off/Def split |
|------------------|---------------------|---------------|-----------|---------------|
| DARKO DPM        | darko.app           | viable        | DPM       | yes           |
| BPM / VORP       | basketball-reference | viable        | BPM       | OBPM/DBPM     |
| LEBRON           | bball-index.com     | unverified    | LEBRON    | yes           |
| EPM              | dunksandthrees.com  | DROPPED       | n/a       | n/a           |

Two independent signals (DARKO + bbref) are sufficient for Phase 2 fusion.
LEBRON adds a third if it ships; not blocking.
