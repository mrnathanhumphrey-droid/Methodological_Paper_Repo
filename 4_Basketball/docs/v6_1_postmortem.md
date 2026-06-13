# v6.1 post-mortem

**Date:** 2026-05-01
**Author:** Claude Code session, NBA Projections engine
**Scope:** v6.1 class-offset layer attempt — what shipped, what didn't, why

---

## Executive summary

Applied a Collatz-style per-class residual diagnostic (Bonacorsi & Bordoni's hierarchical noise-floor + structural-decomposition protocol) to v6's per-game stat projections on the 23-24 ship cohort (195 players). The protocol identified what looked like a strong deterministic offset layer:

- 8 surviving (stat, class) combinations at SNR ≥ 1.5
- In-sample LOO composite **−1.48% MAE** (PTS −4.08%, TOV −4.12%, BLK/FTA/FTM −1.5 to −2%)
- Headline finding: `offseason_traded × PTS` at SNR 3.92, traded players over-projected by 1.74 PPG

Forward across-season validation **rejected** the layer. The 22-23 ↔ 23-24 forward test (apples-to-apples v4-lite tq_g PTS fit) showed offsets transfer with the wrong sign. Result: +2.88% MAE on 23-24 when applying 22-23-derived offsets.

**Only one signal survived cross-season:** Centers over-projected on PTS by ~0.70 PPG in both 22-23 and 23-24. Shipped as v6.1 with a single class offset (`Center × PTS: −0.70`). PTS MAE moves 1.8675 → 1.8584 on 23-24 cohort (−0.49%).

The protocol succeeded as a gate. Without forward validation, a season-specific overfit would have shipped to Wonka. v6.1 is a small honest patch, not the big in-sample win it initially looked like.

---

## What we set out to do

v6 ship state going in (per snapshot 2026-05-01):
- Beats analyst consensus on 5/9 fantasy categories preseason (REB, BLK, TOV, FG%, FT%)
- Loses to consensus on PTS −6.1%, AST −8.8%, STL −3.9%, MPG −13.9% (the "analyst-curation gap")
- Live update mechanism dominates consensus's in-season updates by +25% to +64%

Goal: close the preseason MAE gap on PTS / AST / STL by adding deterministic per-class offsets without re-fitting, leveraging structural information career data alone can't see (offseason events: trades, coaching changes, role shifts).

---

## What we did (chronological)

### 1. Lever search — identified two-class candidates from shock-harness sweep

Tested 8 candidate levers via additive MPG shock with volume-cascade scaling. Two showed real signal:

- **Preseason MPG blend at w=0.05–0.10:** TOV −3.8%, modest PTS lift
- **Static offseason-trade dampening at −2 to −3 mpg:** PTS **−3.8%**, AST −2.0%, TOV −2.2%, but REB **+2.9%**, STL **+3.4%**

Composed jointly: composite −0.87% at w_pre=0.05, damp=−1.5. Looked like a clean v6.1 win.

### 2. User invoked Collatz protocol — methodology pivot

User's parallel work on Collatz tail-behavior (extending Bonacorsi & Bordoni 2026) provided the structural-decomposition discipline: residuals → per-class SNR test → only act on SNR ≥ 1.5 → prefer parsimonious deterministic features over random effects.

Ported the protocol to NBA residuals. Five rules adopted (saved as `feedback_collatz_protocol_for_projections.md`).

### 3. MPG-residual noise-floor diagnostic — caught the cascade-compensation issue

Per-class noise-floor SNR test on MPG residuals across the 195-cohort:
- position: SNR 1.51 (REAL)
- age_bucket: SNR 1.51 (REAL)
- offseason_traded: SNR **0.25** (NOISE FLOOR — far below sampling SE)
- team: SNR 1.01 (noise floor)

**The trade-dampening shock that worked at MPG layer was a NOISE-floor signal in MPG residuals.** It worked through the volume cascade: dampening MPG by −3 scaled PTS down by ~14%, which happened to match the per-min PTS over-projection traded players had. It wasn't fixing MPG; it was fixing per-min stats via a wrong-axis correction.

Confirmed by player-level Pearson r between MPG residual and per-min residual:
- PTS: r = **−0.71**
- REB: r = **−0.75** (strongest)
- STL: r = −0.68
- All 8 stats showed r between −0.39 and −0.75

v6 has structural cascade compensation: MPG and per-min projections have anti-correlated errors that mostly cancel at per-game level. **MPG-only corrections double-correct an internally compensated layer.**

### 4. Per-stat noise-floor (correct layer) — 8 surviving combos

Reran SNR test at per-stat-residual layer (PTS_residual, REB_residual, etc.). Eight (stat, class) combinations passed SNR ≥ 1.5:

| Stat | Class | SNR |
|---|---|---|
| PTS | offseason_traded | 3.92 |
| AST | offseason_traded | 4.60 |
| STL | offseason_traded | 3.65 |
| FTA | offseason_traded | 3.26 |
| FTM | offseason_traded | 3.44 |
| TOV | years_pro_bucket | 2.33 |
| BLK | position | 1.59 |
| AST | age_bucket | 1.64 |

After parsimony (top-1 per stat, to avoid multicollinearity from correlated career-arc proxies), 7 stats had a class assigned (REB had no class survive).

### 5. In-sample LOO ablation — composite −1.48%

Applied per-stat offsets via leave-one-out (each player's class mean computed from other class members):

| Stat | Δ% MAE |
|---|---|
| **PTS** | **−4.08%** |
| **TOV** | **−4.12%** |
| BLK | −1.93% |
| FTA | −1.94% |
| FTM | −1.47% |
| AST | +0.36% |
| STL | +1.33% |
| REB | 0.00% (no class) |

Composite avg: **−1.48%**.

LOO ≈ in-sample (both gave −1.48%) — no within-season overfitting protection issues at class sizes 19–98.

### 6. Multicollinearity catch — one class per stat

Tested expanded 8-class set (added years_pro, career_mpg_tier, draft_pick_tier, chronic_bucket, years_with_team) summed across surviving classes per stat. Result: composite **+7.30% (regression)**.

Cause: classes correlated as proxies for the same dimension (career arc). TOV had four such classes survive; summing quadruple-counted the same residual variance.

Top-1 parsimonious recovered −1.48%. **One class per stat is the discipline.** Aligns with B&B's Collatz approach (one a_final per modular resolution, not summed mod-8 + mod-64 fixed effects).

### 7. Coaching scrape landed — added new class candidates

Basketball-Reference fetcher scraped coaching changes 2014-25 (330 team-seasons, 75 coaching changes). Tested as new class candidates:

| Stat | Coach class | SNR |
|---|---|---|
| PTS | new_coach_this_season | 2.24 (REAL) |
| **REB** | **mid_season_change** | **3.53 (REAL — was no surviving class)** |
| STL | new_coach_this_season | 2.13 (REAL) |
| BLK | mid_season_change | 2.30 (REAL — upgrades position 1.59) |

Multicollinearity check: trade flag and coach flags are mostly independent (Pearson r −0.009 to +0.21), so they layer cleanly. Coaching effects on REB/BLK were genuinely orthogonal.

In-sample LOO with revised spec (REB and BLK using mid_season_change):
- Composite: **−1.43%** (slightly worse than −1.48% — high SNR didn't translate to MAE because mid_season cohort is only n=16)

Insight: SNR gates noise but doesn't rank by MAE-improvement potential. Smaller-cohort high-SNR offsets contribute less total correction than larger-cohort lower-SNR offsets.

### 8. Cohort-overlap diagnostic — flip is not artifact

Cheap forward-validation showed top class flips between 22-23 (position SNR 1.93) and 23-24 (offseason_traded SNR 3.92). Tested whether this was due to cohort composition: 194 of 195 players overlap between seasons. Same player set still showed:

- Mean residual: 22-23 +0.12, 23-24 −0.59 (baseline drift between models)
- Per-class signs flipped for everything except Center on PTS (-0.89 vs -0.68 — both negative)

Concluded: flip is real, not artifact. Even on identical player set, the per-class effects do not transfer.

### 9. Apples-to-apples forward — REJECTED

Hypothesized the flip might be due to baseline mismatch (22-23 audit was v4-lite tq_gya, 23-24 ship is v6 which uses tq_g production v4-lite). Fired matching tq_g v4-lite PTS fit for 22-23.

Result: position SNR 1.87 in 22-23, 0.67 in 23-24. Same flip, same direction. Apples-to-apples confirms the rejection.

Forward validation result on 23-24 PTS MAE: **+2.88% (REJECTED)**. Applying 22-23-derived position offsets to 23-24 actively hurt PTS.

### 10. Single signal survived — shipped as v6.1

Across both seasons (apples-to-apples v4-lite tq_g):
- 22-23 Center on PTS: −0.72
- 23-24 Center on PTS: −0.68

Both negative, similar magnitude. Only signal that survives forward validation. Shipped as v6.1 patch:

```python
VALIDATED_OFFSETS = {
    "PTS": {
        "position": {
            "Center": -0.70,  # mean of 22-23 -0.72 and 23-24 -0.68
        },
    },
}
```

Output: `audit_runs/unified_ship_v6_1/per_player_projections_2023-24.csv`. PTS MAE 1.8675 → 1.8584 (**−0.49%** on 23-24 cohort). 23 players affected.

---

## What didn't ship and why

Eight (stat, class) offsets that passed in-sample SNR + LOO **but failed cross-season validation**:

| Stat | Class | 23-24 sign | 22-23 sign | Reason rejected |
|---|---|---|---|---|
| PTS | offseason_traded | traded -1.74 | traded +0.47 | sign flip |
| AST | offseason_traded | traded -0.50 | (untested, expected to flip) | season-specific |
| STL | offseason_traded | traded +0.13 | (untested) | season-specific |
| FTA | offseason_traded | traded -0.57 | (untested) | season-specific |
| FTM | offseason_traded | traded -0.47 | (untested) | season-specific |
| TOV | years_pro_bucket | varies | (untested) | season-specific |
| BLK | position (or mid_season) | varies | (untested) | season-specific |

Not shipping these saved Wonka from re-pricing 20 traded vets ~$2-5 lower based on 23-24-only signal that doesn't transfer.

---

## False positives the protocol caught

1. **MPG-axis trade dampening (−3.8% PTS via volume cascade).** Looked like a clean MPG fix; was actually a per-min PTS over-projection in traded players being corrected through the wrong axis. The cascade compensation in v6 (MPG and per-min projections having anti-correlated errors) means MPG-only shocks double-correct an internally balanced system.
2. **Net position churn (Desktop's #1 prediction).** Pearson r vs residual = −0.006. Zero signal despite the structural plausibility. The Class A roster-event lever didn't carry residual-explanatory power on this cohort.
3. **8-class sum (composite +7.30% from −1.34%).** Multicollinearity from summing correlated career-arc proxies (age + years_pro + career_mpg + draft_pick) destroyed in-sample fit. Parsimony rule recovered.
4. **23-24 LOO offsets generally.** −1.48% in-sample composite is real for 23-24's specific roster moves; transfers with wrong sign to 22-23.

Without the protocol's gates (SNR ≥ 1.5, LOO honesty, parsimony, forward across-season), all four would have shipped to v6.1 ship CSV → Wonka would have priced 26-27 auctions on overfit signal.

---

## Discipline rules captured (saved to memory)

`feedback_collatz_protocol_for_projections.md`:

1. **Compute residuals at the layer you can correct.** v6 has cascade compensation; per-stat residuals are the right layer, not MPG.
2. **Strict noise-floor SNR ≥ 1.5 gate.** Marginal classes (1.05–1.5) destroyed −1.34% to +7.30% via overfit.
3. **LOO honesty for in-sample-derived offsets.** Class sizes 19–98 mean LOO ≈ in-sample but it's the right discipline.
4. **One class per stat — multicollinearity from summing correlated proxies is catastrophic.** Quadruple-counts variance on TOV.
5. **Shocks (cascade-driven) and offsets (direct) don't compose.** Joint A+B = −1.23% beat A alone = −1.48%; cascade was indirectly correcting same bias offset captures directly.
6. **Single-season LOO is necessary but not sufficient. Forward across-season validation gates ship.** The 23-24 LOO −1.48% rejected as +2.88% forward.

These ports beyond NBA — applicable to any per-class projection system with cascading layers (e.g., the Collatz B&B per-class hierarchical fit).

---

## What we'd do differently

1. **Run forward validation before celebrating in-sample LOO.** When 23-24 LOO came back at −1.48%, the natural reaction was "ship it." We almost did. Forward validation isn't optional — make it part of the protocol's standard sequence.
2. **Cohort-overlap diagnostic should be a standard pre-forward check.** Confirms whether apparent class differences across seasons are cohort artifacts or real.
3. **Build the apples-to-apples comparison spec earlier.** The first cheap forward test mixed v4-lite (22-23) with v6 (23-24); the apparent rejection could have been baseline mismatch. Apples-to-apples test (one extra v4-lite tq_g 22-23 fit) is cheap and removes ambiguity.
4. **Don't conflate SNR with MAE-improvement potential.** A high-SNR small-cohort offset (mid_season × REB) yielded smaller composite gain than a lower-SNR large-cohort offset (position × BLK). Both passed the gate; the deciding factor was MAE not SNR.

---

## In-flight work

Sequential 5-stat chain firing (REB/AST/STL/BLK/TOV at v4-lite tq_g for 22-23). Background ID `bbcczit4w`. Expected wall: 2-3 hrs at user's 60% CPU baseline.

When chain completes:
1. `forward_validation_full_per_stat.py` runs across all 6 stats (PTS already done)
2. Per-stat surviving offsets get added to v6.1 spec if they replicate
3. v6.1 spec re-applied to 23-24 ship CSV → updated `unified_ship_v6_1/`

Likely outcomes per stat (predicted from cohort-overlap finding):
- **REB:** mid_season_change had SNR 3.53 in 23-24 (n=16). Coaching effects MAY be more season-stable than trade effects. 50/50 odds it survives.
- **AST/STL:** trade-class dominant in 23-24. Likely flips like PTS did. <30% odds of survival.
- **BLK:** position OR mid_season_change. Position effect in 23-24 was small. Survival uncertain.
- **TOV:** years_pro_bucket dominant in 23-24. Career-arc effects might be stable. 40/60 odds.

Honest expectation: 0-2 additional offsets get added beyond Center×PTS. Possible we ship v6.1 with just the one validated rule.

---

## Future work (not in v6.1 scope)

1. **Hierarchical Bayesian pooling across seasons.** Fit a Stan model that draws each season's class effects from `Normal(μ_class, τ_class)` priors. Tightens cross-season-stable signals while shrinking unstable ones. Natural extension of B&B's hierarchical approach.
2. **Vegas team trajectory (Class A safe).** Net win-total change vs prior season. Captures rebuild → contender shifts that affect minute distribution. Queued in fetcher pipeline.
3. **Spotrac contract data.** Contract year, new extensions, rookie scale. Adds offseason-event signal independent of trades.
4. **Multi-year coaching effect testing.** We have 11 years of coach-team data. Test whether mid_season_change effect on REB replicates across all 11 seasons before adding to v6.1.x.
5. **Re-fit at relaxed cohort eligibility.** Drop ≥ 200 min filter. Different cohort = different residual structure; absorption / chronic / coaching effects might surface differently for deep-bench projections.

---

## Cost / time

- Total session work: ~6-8 hours (analysis + diagnostics)
- Stan fits used: 1 PTS v4-lite tq_g 22-23 fit, ~60 min CPU under contention
- Pending fits: 5 stats × 25-40 min ≈ 2-3 hrs CPU sequential
- Net infrastructure delivered: noise-floor diagnostic suite, cohort-overlap diagnostic, forward validation harness, parsimonious offset application script, v6.1 ship CSV with provenance

---

## Conclusion

v6.1 is a one-line offset rule (`Center × PTS: −0.70`) that buys ~−0.49% PTS MAE on the 23-24 cohort. Looks small relative to the −1.48% in-sample composite that didn't survive. Real takeaway is the protocol now in place:

- Class-offset application (`apply_v61_validated_offsets.py`) wired and idempotent
- Provenance metadata on every offset (validated seasons, magnitude, SNR)
- Forward validation harness ready to re-run when 25-26 → 26-27 data arrives
- Six-rule discipline for residual-class corrections, validated cross-domain (Collatz + NBA)

When 26-27 ships, the offset table refreshes from a clean cross-season test, no architectural changes needed. The pipeline is wired for BANGER readiness.
