# NBA Projections — Paper State as of 2026-05-11

## Headline

**Cross-league cross-method replication of partial pooling of residual classes** in basketball projection, now with **within-NBA cross-season replication including 2025-26** and a **LOO MSE deployment gate** that holds back 0/11 candidate mean offsets — methodologically tightening the framework's claims.

- **BLK × Center couples in 11 of 11 testable cells** across 4 leagues (NBA / WNBA / NCAA D1 men's / NCAA D1 women's) × 2 projection methods (career-mean surgical, hierarchical NB2 Stan). Variance ratios 1.26–2.03, tight magnitude band.
- **Within-NBA cross-season variance replication (2026-05-11)**: `BLK × Guard TIGHTEN ×0.44`, `REB × Guard TIGHTEN ×0.49`, `AST × offseason_traded WIDEN ×1.51` — all 4 seasons (22-23 through 25-26). Same effect as cross-league at a different granularity.
- **AST × deep-vet pro-context null** replicates clean across NBA cross-season (3 seasons) + WNBA surgical (3 seasons × 3 classifiers).
- **PTS × Center directional cross-league**: variance ratio < 1 in 11 of 11 testable cells; reaches formal significance under Stan robustness only at NCAA cohort scale (n_in > 200).
- **REB × Center retracted**: surgical-method coupling does not survive Stan robustness in any league where Stan robustness has been performed (WNBA 0/3, NCAA M 0/2, NCAA W 0/2). Walk-back reported with same prominence as confirmations.
- **LOO MSE deployment gate (2026-05-11)**: 0/11 cross-season-replicated mean offsets clear the 1% population-MAE-improvement threshold. All HOLD. Methodological discipline preserves parsimony — the structure exists at SNR + replication, but doesn't compose into population-MAE deployment.
- **Two pre-registered Tier-1 NULLs reported alongside positives**: contextual-residual-class Probe B (multi-season pooled, §5.3) + PBP score-margin × possession lever (cross-season, §5.8). Discipline preserved by reporting both with the same prominence as confirmations.
- **2025-26 blind validation (train 19-25, test 25-26, n=124 cohort, 4 chains × 400+400 iters)**: PTS MAE **2.2477**, REB 0.66, AST 0.62, BLK 0.17. v6.1 LOCKED single-season blind validation: vet PTS MAE 2.48 (n=119), full-cohort PTS MAE 2.78 (n=451). v6.3-A in-season conjugate update on games 1–30 reduces games-31–82 MAE by 14–18% on PTS / REB / AST.

## Production state

| Layer | Status | Source |
|---|---|---|
| v4-lite Stan posterior | **deployed** | 12-stat NB2 quadratic-aging-tq-gravity, 6-season train |
| v0 cohort widening | **deployed** | Sophs (24-25 H2 lever), 2025 rookies (NCAA hybrid) |
| v6.1 LOCKED levers | **deployed (final-locked 2026-05-05)** | 3 mean offsets + 3 variance tightenings, position+years_pro classes |
| v6.2 de-shrinkage (global γ) | research artifact, not deployed | Over-corrects vets that v6.1 already calibrated |
| v6.3 per-cohort γ | research artifact, not deployed | Fit on 23-24 + 24-25 vet OOS pool (n=284); applied to 25-26 gives PTS −1.9% / REB +0.4% / AST +3.8% (regression). Does not clear OOS-MAE threshold. |
| v6.3-A in-season conjugate | research artifact, not deployed | Per-player Gamma-Poisson update on games 1–30 → games 31–82 MAE reduction 14–18% across PTS / REB / AST |
| Wonka CSV | **deployed (v6.1 LOCKED)** | `D:/Wonka Resolve/audit/data/parsed/nba_projections_projections.csv` |

## Findings (post-cross-league + post-Stan-robustness)

### Position cells

**BLK × Center — robust large-magnitude structural cell.** 11/11 testable cells couple under inclusive classifier matching the NBA Test 1 protocol. Variance ratios under Stan: 1.26–1.84. Variance ratios under surgical: 1.71–2.03. Cohort sizes span n_in = 21 (NBA cross-season Stan-only) to n_in = 224 (NCAA WBB). Magnitude consistency across two orders of magnitude in cohort size.

**PTS × Center — robust small-magnitude directional cell.** 11/11 testable cells show variance ratio < 1.0 (Center variance tighter than non-Center). Under Stan robustness at NCAA cohort sizes, 3 of 4 NCAA Stan cells reach Levene's p < 0.05 (the fourth at p = 0.056 directional). NBA / WNBA cohort sizes are too small (n_in = 21–71) to detect the small effect at formal significance — the directional pattern is real, the formal-significance failure at pro-cohort scale is a power problem.

**REB × Center — retracted.** Surgical method couples 4 of 4 leagues; hierarchical Stan posterior shows 0 of 7 testable cells couple (WNBA Stan 0/3, NCAA M Stan 0/2, NCAA W Stan 0/2). Surgical coupling reflects position-level mean structure that hierarchical pooling correctly absorbs into `mu_position[Center]`; residual variance asymmetry vanishes. The 4-league surgical REB pattern is a position-mean structural finding, not a residual-class finding.

### Career-stage cells

**AST × deep-vet (pro context) — robust null.** 6/6 cells null across NBA cross-season Test 1 (3 seasons at 13+ years pro) and WNBA surgical 3-classifier matrix (3 seasons at 10+ years pro). Pro-league career-stage axis is process-only at every test season tested. CF refinement (Section 2.5) confirms process-only at full Fourier resolution: 0/4 higher moments significant, 0/201 CF grid points significant.

**NCAA AST × upperclassman — out of scope.** Couples in 8/8 cells at small magnitudes (variance ratios 0.91–0.98) at NCAA-scale cohorts (n_in ≈ 1300–2400). Mechanism is collegiate role-stabilization variance across class years (freshmen carry recruitment / rotation / transfer uncertainty that fourth-year seniors do not), distinct from the residual-class structural coupling tested in pro contexts where role stability is uniform across the cells. Flagged for further investigation under role-stability-matched cohort design; outside the scope of this paper.

### Pre-registered Tier-1 NULLs

**Probe B (multi-season contextual residual-class structure).** Pre-registered theme `top_record + early + home` failed to appear in any outlier cluster across 23-25 NBA pooled residuals. 0/18 testable cells beat Bonferroni; 1 nominal-p<0.05 hit on a different theme that does not survive correction. Locked language: "single-season null replicates at multi-season; contextual residual structure not detectable in NBA box-score-only contextual axes at the resolution tested."

**PBP score-margin × possession lever.** Pre-registered Tier-1 hypothesis (variance ratio σ_garbage / σ_clutch > 1 for PTS / REB / AST). 2024-25 result: 1/3 confirms (AST only). 2023-24 Tier-2 replication: 0/3 confirms — AST does not replicate. Cross-season aggregate: NULL. Pre-registration document at `audit_runs/pbp_garbage_clutch_pre_reg/PRE_REGISTRATION.md`, signed off 2026-05-07.

### Engineering ablations — diagnosed via the residual-class lens, not predicted by it

These are real improvements but they are *not* residual-class-specific predictions. Frame as standard hierarchical-Bayes phenomena that the residual-class lens prompted us to look for.

1. **Galton de-shrinkage** (γ ∈ [0.74, 0.88] across stats). v6.2 artifact applies `corrected = α + γ × proj`, drives league-wide bias to ~0, MAE reduction 1–7% per stat. Standard regression-to-the-mean correction. NOT deployed because vet PTS MAE 2.48 → 2.56 (Simpson's paradox: global γ over-corrects on vets that were already calibrated). v6.3 per-cohort γ also fit and held (vet γ ≈ 1.0 on every stat; applied to 25-26 gives marginal effects within sampling noise).

2. **Variance miscalibration** (calibration ratio 1.7–3.4× across all classes). Posterior-on-rate ≠ predictive-on-outcome — Stan's `proj_sd` measures uncertainty on the rate parameter, not predictive uncertainty about realized stat. v6.1's 50% intervals empirically cover 22–55% on the worst classes. **Paper material** — methodological category error in standard hierarchical Bayesian projection systems, exposed by the framework's coupling-test calibration ratios.

   **3PM-specific sharpening (pre-registered + replicated 2026-05-19).** Per-game 3PM variance is structurally over-dispersed by ~1.70× relative to the binomial floor `mean_3PA × p × (1−p)`. Pre-registered Tier-1 on 2017-18 + 2018-19 (untouched by exploratory probe) confirms Claim A both seasons at Wilcoxon p ~ 1e-45 to 1e-48; light shrinkage from exploratory 1.83 → replication mean 1.70. Claim B (3P% gradient ≥ 1.15 lower-CI) confirms 1/2 seasons; gradient is borderline at single-season cohort sizes (n≈300) but Guard-cell stratification (§7 conditional, fired) confirms 2/2. Pre-reg at [audit_runs/threept_dispersion_pre_reg/](audit_runs/threept_dispersion_pre_reg/), result at [audit_runs/threept_dispersion/summary.md](audit_runs/threept_dispersion/summary.md). Production-correction implication: Wonka audit-CSV `3PM_stddev_per_game` column inspected during write-up and found to sit at ~25% of per-game predictive SD on the highest-volume archetypes (Curry's 0.47 vs binomial-floor stddev ~1.55). Naive √1.7 multiplier insufficient — a contract-level rewrite from rate-SD to predictive-SD is the right fix. Open item, separate decision.

3. **Residual rank diagnostic.** PCA on the 12-stat residual matrix shows PC1 explains 62.9% of variance (top 4 PCs explain 87%). PC1 is a role-utilization axis (all loadings same sign, led by usage stats). Useful diagnostic about effective rank.

4. **Additive class structure saturation.** Layer-wise sd: pooled 6.61 → v6.1 per-stat 3.59 → +pos 3.58 → +ypb 3.54 → +pos×ypb 3.51. Adding additional class structure beyond the v4-lite per-stat projection contributes essentially nothing. Diagnostic showing where additive class layering exhausts.

## Paper outline (working)

> **Title (working):** Partial pooling of residual classes: theory, application to basketball projections, and measurable noise-floor reduction
>
> §1 Background — hierarchical Bayesian projections lose signal in cross-class interactions
> §2 Theory — partial pooling of residual classes, σ-shift invariance at the class level, characteristic-function characterization of process-only cells
> §2.5 Central NBA validation — same-class mean-variance coupling (Test 1) + CF refinement on career-stage class
> §3 Protocol — five rules: layer / SNR / LOO / single-class / additive-vs-mult
> §4 NBA application — v4-lite Stan + v6.1 LOCKED levers via the protocol
> §5 Validation — blind 25-26 forward projection, 567 players, vet PTS MAE 2.48; v6.3-A in-season update; head-to-head vs HashtagBasketball / FantasyPros; multi-season cross-season replication; cross-league replication on WNBA + NCAA D1 M + NCAA D1 W; Stan robustness for WNBA + NCAA D1 M + NCAA D1 W; PBP score-margin × possession Tier-1 pre-registered NULL **(complete and drafted at `paper_draft/section_5_empirical_validation.md`, 627 lines)**
> §6 Engineering ablations — de-shrinkage stretch, additive class saturation, cohort shrinkage gradient. Each labeled as "diagnosed via the residual-class lens, not predicted by it"
> §7 Coverage — z-MAE / scale-normalized residuals; variance miscalibration finding
> §8 Forward validation — 26-27 NBA forward Probe pre-registration locked; results gated by Oct 2026 season opener

§5 is the only currently-drafted section. §1–§4 and §6–§8 are outlined but not drafted.

## Open compute (priority order)

1. **Coverage / z-MAE table for §7** — empirical 50/80/95% interval coverage per stat × cohort across three seasons. ~30–60 min.
2. **Larger Stan training pool for soph/rookie γ** (optional) — current 200-player cap excludes early-career players from OOS residual pool. ~30–40 hours of Stan compute. Marginal value uncertain given vet γ at available data showed minimal effect.
3. **26-27 NBA forward Probe** — pre-registered, gated by October 2026 season opener. Pre-registration document at `audit_runs/probe_b_2627_pre_registration/PRE_REGISTRATION_2627_forward_probe.md`.

Closed since 2026-05-05:
- Multi-season Stan backtests (24-25, 23-24): shipped 2026-05-05
- BLK × Center cross-season: shipped 2026-05-06
- v6.3 per-cohort γ: fit, held
- WNBA surgical cross-league: shipped 2026-05-06
- WNBA Stan robustness: shipped 2026-05-06
- NCAA D1 M + W surgical cross-league: shipped 2026-05-07
- NCAA D1 M + W Stan robustness: shipped 2026-05-08
- NCAA AST × upperclassman scope-out: shipped 2026-05-08
- PBP score-margin × possession Tier-1 + Tier-2: shipped 2026-05-08

## Methodology footnote — stratified residual analysis (game prediction)

For Level 3 game prediction validation, the 8-season walk-forward (2018-19 through 2025-26, n=8,812 games) yields a 65.31% aggregate win pct matching Vegas closing-line accuracy. However, raw aggregates conceal residual structure. Three stratifications reveal a converging pattern:

> *"NBA stratified residual analysis: aggregate model matches Vegas closing-line accuracy (65.31% win pct on n=8,812 walk-forward games, 2018-19 through 2025-26), but residuals are structured. Three stratifications reveal a converging pattern: (a) per-margin-bucket miss rate is non-uniform with 64% wrong-direction calls on 15-20pt blowouts predicted as coin flips (|pred_margin| ≤ 2), (b) per-team error rate clusters by roster volatility with middling-volatile teams (DAL/SAC/ATL/MIA/LAL/CHI/IND/MIN) worst-predicted and extreme teams (WAS/DET/POR/BOS/OKC/CLE) best-predicted, (c) per-season big-miss rate spikes in 2023-24 (29.1% vs 15-20% typical) coinciding with documented roster volatility. All three stratifications point at roster-context lag in rolling efficiency as missing covariate. Prediction registered: an injury/depth-chart layer test should close the 2023-24 gap specifically and reduce the 15-20pt blowout coin-flip miss rate from 64% wrong-direction toward 50%, without significantly improving stable-season buckets (2022-23, 2025-26) where roster context is less load-bearing. Falsification criterion: if the injury layer closes the gap uniformly across volatile and stable seasons, the lag-dynamic hypothesis is wrong and the missing covariate is something else."*

Implementation result 1 (2026-05-17): a naive subtract-fresh-OUT-contribution layer (where "fresh" = OUT event within last 14 days, scaled by player's pre-injury 5-game rolling MPG × per-min PTS) hurts at every positive scale — win pct drops 65.31% → 62.36% → 60.00% as scale rises 0 → 0.5 → 1.0, and the drop is approximately uniform across volatile and stable seasons. Naive operationalization rejected — double-counts the player's absence which rolling team drtg has already partially absorbed.

Implementation result 2 (2026-05-18) — truly-fresh filter: filter restricted to players who participated in game N-1 with positive minutes AND have an OUT event dated in (N-1, N] AND do not appear in game N box (n=4,517 team-games with ≥1 truly-fresh OUT player, 23.7% of total team-games). This is the sharpest possible operationalization of fresh roster-lag. Layer still hurts at every positive scale — win pct drops 65.31% → 64.36% → 63.38% → 61.92% at scales 0.3 / 0.5 / 1.0. Drop is uniform across volatile and stable seasons; 2023-24 does not improve uniquely.

**Most diagnostic finding (closes the door):** the subset on which the layer should help — games WITH ≥1 truly-fresh OUT player (n=3,594) — has a baseline win pct of 64.77%. The complementary subset of games WITHOUT any fresh OUT player (n=5,218) has a baseline win pct of 65.68%. These differ by 0.9pp, which is well within sampling noise. **Presence of a truly-fresh injury does not make a game meaningfully harder to predict.** If roster-context lag were the missing covariate, the fresh-injury subset would show structurally worse baseline performance than the clean subset. It does not.

The pre-registered falsification criterion is now satisfied **cleanly** — both naive and sharp operationalizations of the roster-lag hypothesis fail the test, with the same falsification signature (uniform drop, no per-season differential). The 8-season residual structure (per-margin-bucket bias, per-team error clustering, 2023-24 anomaly) is real, but **roster-context lag is not the explanation**. Alternative hypotheses to test: (i) within-game stochastic variance dominated by 3PT shot luck; (ii) tactical/coaching adjustments not in box scores; (iii) scheduling artifacts (back-to-back density, road-trip length, travel mismatch).

This connects to a prior NBA player-projection result (per-player minutes redistribution after starter injury): minutes-weighted redistribution models REGRESS vs no-redistribution baseline by 15-36% MAE, because the empirical redistribution is concentrated in <30% of active players in ways that are hard to identify a priori, and natural game-to-game variance is larger than the redistribution signal. The same architectural lesson holds at the game-level: when a player goes OUT, backups absorb, opponents adjust, and pace shifts — the team's offense does not drop by the player's full pre-injury contribution. Both findings point to a deeper principle: **box-score-derived rolling efficiency already encodes most of the recoverable signal about team strength, and attempts to layer player-level deltas on top double-count rather than add information**.

## Methodology footnote — reproducibility infrastructure

For the §3 protocol and multi-season replication footprint, note in a methodology footnote (not as marketing — as a reviewer-question pre-empt):

> *"Multi-season Stan backtests are run via a defensive overnight runner (`cli/run_v4lite_overnight.py`) with: (1) a single-instance lockfile preventing concurrent runs against the same parquet store; (2) a pre-flight scan for residual `cmdstan` model binaries that halts the chain if any prior run's children survived; (3) verification after each fit that exit code == 0 AND a parseable `backtest_metrics.json` with non-null MAE was written, with failed stats marked failed and SKIPPED rather than retried; (4) no automatic retries — one fit per stat per season. Pre-fit calibration constants (aging curve coefficients, team-quality fitted parameters) are frozen at v4-lite values and not refit between seasons, ensuring cross-season comparisons reflect data differences only, not architectural drift. Script and CmdStan version IDs are logged per fit."*

This addresses the standard reviewer concern that long-running stochastic-MCMC chains in academic projections can be silently corrupted by stale child processes from prior runs, especially when the same compiled binary is reused.

## Important caveats

- **In-sample fit warning on v6.2 de-shrinkage**: γ values were fit on 25-26 actuals and applied to 25-26 projections. Honest out-of-sample γ requires multi-season backtests; v6.3 per-cohort γ is the proper out-of-sample fit and produced no meaningful improvement over v6.1 LOCKED.
- **PTS Stan posterior at WNBA scale**: 17–20% divergent transitions in WNBA Stan PTS chains; PTS Stan magnitudes are suggestive rather than calibrated. The qualitative null is consistent with surgical and with NBA Section 5.4.1 walk-back, so the qualitative finding is robust.
- **NCAA position labels** include `Athlete` and `Not Available` rows (~2–3% of cohort) that default to Forward under the inclusive classifier. Sensitivity test on dropping those rows is cheap if a reviewer pushes; sportsdataverse position labels do not contain hyphenated boundaries, so the WNBA classifier-sensitivity story does not carry over.
- **NCAA on-court approximation in PBP analysis**: per-player on-court windows in §5.8 use `[first_event_time, last_event_time]` rather than full lineup tracking. Documented in pre-reg Section 4.
- **Rookie metadata supplement** (`audit_runs/cohort_widening_v0_2025_26/rookie_metadata_supplement.parquet`) defaults 14 of 59 picks to "Forward" position because they're intl/G-League pathway players without combine matches. Eye-test override is the workflow when accuracy matters for those specific players.

## Repo

`https://github.com/mrnathanhumphrey-droid/NBAProjections`. Cross-league + Stan + PBP work since 2026-05-05 is uncommitted as of 2026-05-08. PAPER_STATE.md (this file) and `paper_draft/section_5_empirical_validation.md` + `.docx` also uncommitted.
