# Phase 2 — Hierarchical Bayesian Skill Model Design

Locked 2026-04-26. Implementation in `models/skill/` (TBD). This doc fixes the
structure before any Stan is written so model debugging stays interpretable.

Cross-refs:
- `docs/projection_model_spec.md` §3.2 (skill estimation)
- `docs/spec_amendments.md` §B (advanced-metric fusion — V2 of this doc)
- `docs/projection_contract.md` (downstream output contract)

---

## 0. Decomposition recap

Per spec §3.1:

```
projected_stat(p, s, c) = skill(p, c) × context_modifier(p, s)
```

Phase 2 estimates `skill(p, c)` only — context (minutes, usage, role projections)
is Phase 4. A skill estimate is **per-minute or per-usage**, not per-game.

V1 (this doc) ships skill estimation from box-score history alone. The
advanced-metric fusion (amendment §B) is V2 of this model — same hierarchical
backbone, additional likelihood term feeding from DARKO + bbref BPM.

## 1. Per-stat decomposition

Per spec §3.2, different stats have different right-units. Locked assignments:

| Stat | Unit | Reason |
|---|---|---|
| `REB`, `OREB`, `DREB`, `BLK`, `STL`, `MIN` | per-minute | Stable across role changes; pace-driven |
| `PTS`, `FGA`, `FTA`, `AST`, `TOV` | per-usage | Scale with offensive role; role change = usage change |
| `3PM`, `3PA` | per-minute × team-3PT-context | Hybrid: shooting skill is personal but volume depends on system |
| `FG_pct`, `FT_pct`, `3P_pct` | ratio (made / attempted) | Spec §3.8 — projected via numerator/denominator separately |
| `FGM`, `FTM` | derived (FGA × FG_pct, FTA × FT_pct) | Coherent with the ratio model |

The `FGM = FGA × FG_pct` derivation has joint-posterior implications (see §6).

## 2. Hierarchical structure (3 levels)

```
league-level prior (sabermetric-literature informed)
       │
       ├── position-level offset (G / F / C)
       │           │
       │           └── player-level skill (the quantity we ultimately want)
```

Concretely for one stat (per-minute REB shown):

```stan
parameters {
  real mu_league;              // league-mean per-minute REB rate
  vector[3] mu_position;        // G / F / C offset from league mean
  vector[N_players] mu_player;  // each player's deviation from their position mean
  real<lower=0> sigma_position;
  real<lower=0> sigma_player;
}

model {
  // Hyperpriors (population-level)
  mu_league       ~ normal(<lit_value>, <lit_sd>);   // sabermetric literature
  sigma_position  ~ exponential(2);
  sigma_player    ~ exponential(2);

  // Position effect: shrinkage toward league mean
  mu_position     ~ normal(0, sigma_position);

  // Player effect: shrinkage toward position mean
  mu_player       ~ normal(0, sigma_player);

  // Likelihood (per-game observation, see §3)
  for (i in 1:N_obs) {
    // theta = exp(mu_league + mu_position[pos[i]] + mu_player[player[i]])
    obs_count[i] ~ neg_binomial_2(
      theta * minutes[i],
      phi
    );
  }
}
```

Hierarchy gives shrinkage automatically: a 3-game rookie with 2 rebounds in
a small sample gets pulled toward the position mean (G ≈ 4.5 rpg/minute);
a 10-year veteran's posterior is data-dominated.

## 3. Likelihood choice per stat type

Spec doesn't lock these; my locked choices below have rationale.

### Counting per-game stats (REB, AST, STL, BLK, TOV, FGA, FTA, 3PA, FGM, FTM, 3PM)

**Negative binomial** with `mean = theta * minutes`.

- Why not Poisson: per-minute rates aren't memoryless; opponent defense,
  game flow, foul trouble create overdispersion. NB's extra shape parameter
  absorbs that without needing an extra random effect.
- `theta` is the per-minute rate (skill estimate); `minutes` carries the
  game-specific exposure. This factorization lets the same skill model
  generate projections for any minutes assumption.

### Per-usage stats (PTS, AST, TOV)

For these the exposure is **possessions used**, not minutes. We approximate:
```
usage_possessions ≈ minutes × team_pace × usage_rate / 100
```
Same NB likelihood with the right exposure term.

Phase 4 will project `team_pace` and `usage_rate` per player-team
combination; Phase 2 backs out `usage_rate` from historical box scores
(USG% column from `LeagueDashPlayerStats`, which we already cache).

### Ratio stats (FG_pct, FT_pct, 3P_pct)

**Beta-binomial** per spec §3.8. For each player-game observation:
```
makes ~ Binomial(attempts, true_pct)
true_pct ~ Beta(alpha, beta)   // hierarchical, position-specific
```

Conjugate, fast, naturally handles small-sample shrinkage. A 2-of-3 FT shooter
gets a posterior centered well below their raw rate because the position-
level prior pulls toward (~78%, sd ~5%) rather than fitting 2/3.

### MIN

Per-game observation but bounded [0, 48]. Likelihood: **truncated normal**
with player-level mean and league-level sd. MIN is more about role/health
than skill — Phase 2 estimates the per-player baseline mean; Phase 4 adjusts
for context (DNPs, blowouts, role changes).

## 4. Recency weighting

Spec §3.2: half-life ~1.5 seasons.

Implementation: per-game weights in the likelihood:

```
weight(game) = 0.5 ^ (seasons_back / 1.5)
```

A game from 2 seasons ago: weight = `0.5^(2/1.5) ≈ 0.40`.
A game from 4 seasons ago: weight ≈ 0.16.

In Stan this is a `target += weight * neg_binomial_2_lpmf(...)` pattern
inside the loop. Tested approach; doesn't break NUTS.

The half-life itself is a hyperparameter we calibrate on held-out seasons
(spec §4.4). Default 1.5 is reasonable but might tune to 1.2 or 1.8.

## 5. Stability filter (per spec §3.2)

Drop or downweight games that aren't representative of skill:

| Filter | Rule | Action |
|---|---|---|
| Garbage time | Final score margin > 25 in 4Q AND minutes_played < 10 | Drop |
| Back-to-back fatigue | Game within 24h of prior game | 0.7× weight |
| Blowout exits | Player benched in 3Q+, didn't return | Truncate stats |
| Foul trouble | Player exited Q1 with 2 fouls (ungame-flow) | Drop |

Implemented via a `_is_stable_rotation_game()` filter in
`models/skill/stability.py`. Uses `schedule.parquet` for back-to-back
detection and box scores for the rest.

V1 punts on foul trouble + blowout exits (need play-by-play data we don't
have); V1.1 adds them via pbpstats once stats.nba.com unblocks.

## 6. Joint posterior across stats

Spec §3.9 + §1.1 require **joint samples** — each MCMC draw produces a
complete projection vector preserving inter-stat correlations.

Approach: fit one big model with all stats jointly, with a multivariate
prior on `mu_player` per player. The covariance structure picks up
correlations like:
- High-FGA → high-PTS (offensive volume)
- High-AST → moderate-TOV (creation generates turnovers)
- High-OREB → moderate-FGM (offensive board → putback)

Stan implementation uses an LKJ prior on the correlation matrix:

```stan
parameters {
  matrix[N_players, N_stats] mu_player_raw;
  cholesky_factor_corr[N_stats] L_corr;
  vector<lower=0>[N_stats] tau;
}

transformed parameters {
  matrix[N_players, N_stats] mu_player =
    mu_player_raw * diag_pre_multiply(tau, L_corr)';
}

model {
  L_corr ~ lkj_corr_cholesky(2.0);
  tau ~ exponential(2);
  to_vector(mu_player_raw) ~ std_normal();
  // ...
}
```

This is more compute than per-stat-independent fits but is non-negotiable
per spec — joint structure is the value-add over consensus baselines.

## 7. Prior specification (informative, sabermetric-literature based)

Each stat's `mu_league` prior comes from one of:

1. **5-season league averages** from our own `historical_box_scores.parquet` —
   strongest source, internal to project
2. **Sabermetric literature** (Dean Oliver's Basketball on Paper, Daryl
   Morey's APBR-era publications, modern public analytics writers like
   Seth Partnow / Krishna Narsu) — for things like aging-curve shapes
3. **Weakly informative** when neither applies — `Normal(empirical_mean, 0.5 * empirical_sd)`

Each prior gets one row in `priors_log.md` (per spec §10.3): value, source,
strength, sensitivity-analysis result.

## 8. Build order

Phase 2 ships in 5 sub-steps. Each runs the embedded audit before the next
starts (per spec §5.5).

1. **Single-stat single-player Stan model** — fit Curry's per-minute REB
   skill against his 2019-25 game logs. Validate posterior peaks near
   his observed rate, has reasonable spread, MCMC converges (R-hat < 1.01).
2. **Hierarchical wrap** — extend to all 1068 players with position-level
   pooling. Validate rookies get pulled toward position means, vets are
   data-dominated.
3. **Multi-stat vectorization** — generalize to all 18 stats with the
   per-stat unit assignments from §1. Independent fits initially.
4. **Joint covariance** — add LKJ-prior multivariate structure per §6.
   Validate joint samples preserve known correlations (PTS-FGA, AST-TOV).
5. **Recency + stability filter** — apply weighting and game-drop logic
   from §4-5. Validate effects on a synthetic test (e.g., a player with
   role change mid-history; new role should dominate).

Each sub-step writes posterior summary CSVs + diagnostic plots to
`audit_runs/{ts}/skill_phase2_step{N}/`.

## 9. Compute targets

- **MCMC chains**: 4 chains (Stan default) × 2000 iterations (1000 warmup)
- **Step 1-2** (single stat): seconds per fit on 9950X3D
- **Step 3** (multi-stat independent): minutes per stat × 18 stats = ~30 min
- **Step 4** (joint LKJ): hours, possibly overnight on full data
- **Step 5** (full hierarchy + recency + filter): plan for overnight

If joint LKJ doesn't converge cleanly, fallback is independent stat fits
with post-hoc copula correlation extraction. Worse joint structure but
ships.

## 10. Out of scope for Phase 2

These belong to other phases and shouldn't bleed in:

- Aging curves (§3.4) → Phase 3
- Context projection (§3.3) → Phase 4
- Rookie model (§3.6) → Phase 5
- Games-played model (§3.7) → Phase 5
- Advanced-metric fusion (amendment §B) → Phase 2.5 or V2
- Joint posterior with FGM = FGA × FG_pct deterministic link → Phase 3 with ratios

## 11. First implementation files

```
models/
  __init__.py
  skill/
    __init__.py
    stability.py        # game-filter rules from §5
    recency.py          # half-life weight computation
    priors.py           # league-mean priors from historical data
    stan/
      single_player_rebound.stan      # Step 1
      hierarchical_one_stat.stan      # Step 2
      multi_stat_independent.stan     # Step 3
      joint_lkj.stan                  # Step 4
    fit.py              # cmdstanpy orchestration
    diagnostics.py      # R-hat, ESS, posterior predictive
```

Tests at `tests/test_skill_*` covering: stability filter logic, recency
decay math, prior building, fit-output schema validation. Stan code itself
is tested via the embedded audit on real data, not unit tests.

---

**Open questions to resolve before Step 1**:

1. Position categorization — `player_metadata.position` has values like `G`,
   `F`, `C`, `G-F`, `F-C`. Map hyphenated to primary, or treat as a
   continuous position index? Default: primary (split on `-`, take first).
2. Usage rate source — backfill from `LeagueDashPlayerStats` (have it
   cached) per season per player. Need to wire that into the data layer
   before Step 3.
3. Per-game minutes for the truncated-normal MIN model — there's an
   identifiability trap where MIN influences the exposure for other stats.
   May need to fit MIN separately first, then use posterior mean as
   exposure for the rest. Decide at Step 3.
