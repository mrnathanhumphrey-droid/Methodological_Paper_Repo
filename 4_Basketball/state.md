# NBA Projections — state.md

**Last audited: 2026-06-07.** Snapshot for future-agent handoff. README.md is the inbound doorway; this file is the working-state log.

## TL;DR

NBA projection engine at v6.1 production lock, with three major research extensions shipped in the last 7 days:

1. **Defensive metrics suite v1** (2026-06-05) — TADEC, DHA, PDS, RIM%
2. **Novel offensive metrics** (2026-06-05/06) — PSI, STD, FDQ, And1R, GAP, ADI + glossary
3. **Resolve Lottery 2026** (2026-06-07) — OUR-OWN top-14 pre-registered draft board

All read-only handoff artifacts are parquets + docs. No model is currently being trained.

## Production state (unchanged from prior session)

- **v6.1** LOCKED + paper-validated. Stan/NUTS hierarchical NB2/Gaussian, 18-stat full posteriors, joint structure preserved across categories.
- **Cohort widening** ships separately and concatenates into the unified ship chain (rookie path: NCAA-translation + draft-pick-log regression).
- **v6.2 de-shrinkage / v6.3 per-cohort γ** held as research artifacts (didn't beat v6.1 LOO MSE).
- **26-27 forward projection** still gated on summer roster turnover.

Audit CSV contract at `audit_runs/.../ship_per_player_projections.csv` carries per-game means + σ per cat. Inference orchestrator: `scripts/run_2025_26_ship_pipeline.py`.

## Today's session (2026-06-07) — Resolve Lottery 2026 SHIPPED

User: "we want our own lottery picks" → end-to-end pipeline from raw NCAA PBP → outcome-calibrated GBM → advanced metrics → synthesized Top 14 with bold contrarian calls pre-registered before late-June 2026 NBA Draft.

### Files added today

**Scripts (`scripts/`):**
- `decomp_01_build_rookies_master.py` — 501 drafted 2014-24 unified pre-NBA + combine + draft + Y1-Y3
- `decomp_02_translation_factors.py` — NCAA per-40 → NBA Y1 per-36 (blk R²=0.662, pts R²=0.077)
- `decomp_03_signal_source.py` — rookie reb from height-no-shoes R²=0.486; mpg ≈ draft_pick R²=0.264
- `decomp_04_archetype_clusters.py` — K=8 KMeans archetypes
- `decomp_05_rookie_priors_production.py` — `rookie_priors.parquet` (485 × 104 cols, drops into v6 EB anchor seat)
- `decomp_06_calibration_holdout.py` — 2022-23 holdout: 50% interval 45.6%, 80% 75.8%, 95% 91%
- `draft_prep_2026_v1_scrape_ncaa_2025_26.py` — sportsdataverse hoopR bulk parquet (196k game-rows, no auth)
- `draft_prep_2026_01_refresh_combine.py` — NBA combine invitees (measurements unpublished)
- `draft_prep_2026_02_build_candidate_pool.py` — 72 prospects
- `draft_prep_2026_03_project_class.py` — hand-composite v1
- `draft_prep_2026_v1_intl_supplement.py` — Kayil/Lopez/De Larrea/Suigo via DuckDuckGo→team-official sites
- `decomp_07_build_outcome_training_set.py` — outcome calibration setup
- `decomp_08_outcome_calibrated_gbm.py` — **Idea 2 PRIORS** (LightGBM w/ pre_nba_league_label categorical)
- `decomp_09_project_2026_outcome_calibrated.py` — v1 board
- `decomp_10_crossover_graph.py` — **Idea 1 CORRECTOR** (456 edges, league-strength ratios)
- `decomp_11_intl_label_refresh_from_wikipedia.py` — v2 (didn't move rankings — label refresh doesn't fix feature-level survivorship)
- `decomp_12_outcome_gbm_v2.py` / `decomp_13_project_2026_v2.py` — v2 with survivorship_signal column
- `decomp_14_historical_intl_supplement.py` — **v3 historical anchors** (LaMelo/Wemby/Hezonja/Vezenkov/Sarr/Risacher/Avdija via WebFetch Wikipedia)
- `decomp_15_outcome_gbm_v3.py` / `decomp_16_project_2026_v3.py` — v3 (Suigo +5.2 picks, real movement)
- `decomp_17_scrape_ncaa_pbp_2025_26.py` — **2,915,731 events bulk parquet**, single hoopR pull
- `decomp_18_teammate_context.py` — prospect_pts_share + best teammate per-40
- `decomp_19_outcome_gbm_v4_with_teammate.py` — **v4 BROKE forward projection** (honest finding; banked)
- `decomp_20_prospect_advanced_metrics.py` — STD/PSI/FT_rate/def_rate on 67 NCAA prospects
- `decomp_21_lottery_board_with_advanced.py` — joined board
- `decomp_22_resolve_lottery_synthesis.py` — **★ FINAL synthesizer** with auditable formula

**Parquets (`data/parquet/`):** rookies_master, rookie_translation_factors, rookie_archetypes, rookie_priors, draft_2026_candidate_pool, draft_2026_intl_supplement, draft_2026_projections, rookies_outcome_training_{v1,v2,v3,v4}, draft_2026_outcome_calibrated_{v1,v2,v3,v4}, crossover_edges, league_strength_multipliers, prospect_teammate_context, prospect_advanced_metrics_2026, draft_2026_lottery_board_final, **resolve_lottery_2026.parquet** (FINAL).

**Docs (`docs/`):** ROOKIE_DECOMP_SUITE_2026_06_07.md, ROOKIE_DECOMP_{TRANSLATION_FACTORS,SIGNAL_SOURCE,ARCHETYPES}.md, DRAFT_PREP_2026_v{0,1}.md, COMPETITION_NORMALIZATION{,_V2,_V3,_V4_HONEST}_2026_06_07.md, PROSPECT_ADVANCED_METRICS_2026_06_07.md, **RESOLVE_LOTTERY_2026_06_07.md** (FINAL).

### Resolve Score formula (deterministic + auditable)

```
resolve_score = (
      0.45 * v3_rank_pct         # outcome-calibrated GBM
    + 0.20 * hand_rank_pct       # production composite
    + 0.30 * advanced_signal_pct # PSI + STD + FT rate + def event rate
    + survivorship_penalty       # -0.03 * max(0, signal-5)
    + intl_low_n_penalty         # -0.12 for intl with league_n<10 + no NCAA PBP
)
```

### Resolve Top 14 (pre-registered 2026-06-07)

1. Cameron Boozer (Duke PF) | 2. Joshua Jefferson (Iowa St PF) | 3. AJ Dybantsa (BYU SF) | 4. Nate Ament (Louisville PF) | 5. Amari Allen (Alabama SF) | 6. Caleb Wilson (UNC PF) ★ UPGRADE | 7. **Aday Mara (UCLA C) ★★ BIGGEST BOLD CALL** | 8. Labaron Philon Jr (Alabama PG) | 9. Ebuka Okorie (Stanford PG) | 10. Hannes Steinbach (Washington C) ★ UPGRADE | 11. Darryn Peterson (Kansas SG) | 12. Jack Kayil (Alba Berlin PG) ⚠ LOW CONF | 13. Tyler Tanner (Vanderbilt PG) | 14. Christian Anderson (Texas Tech PG)

### Bold contrarian calls (locked for post-draft eval)

- **OUR HIGH, CONSENSUS LOW**: Mara top-10 (vs undrafted); Wilson top-15 (vs 15-25); Steinbach top-20 (vs 2nd round); Okorie top-25 (vs 2nd round)
- **OUR LOW, CONSENSUS HIGH**: Koa Peat NOT top-10 (vs top-5); Baba Miller NOT top-15 (vs top-5); Karim Lopez outside lottery (vs mid-1st)
- **LOCKS**: Boozer + Jefferson + Dybantsa as top-3 in some order

## Recent prior sessions

### 2026-06-05 — Defensive Metrics Suite v1
Folder: `defensive_metrics/`. README at `defensive_metrics/README.md`. Operators: **TADEC** (team-adjusted defensive event coverage), **DHA** (defensive heliocentric attribution), **PDS** (pick-side disruption), **RIM%** (rim deterrent rate).

### 2026-06-05/06 — Novel Offensive Metrics + Glossary
Docs: `docs/NOVEL_METRICS_SUITE_VERDICT_2026_06_05.md` + `docs/NOVEL_OFFENSIVE_METRICS_BRAINSTORM_2026_06_05.md` + `docs/RESOLVE_NBA_ADVANCED_METRICS_GLOSSARY_2026_06_06.md`. Operators: **PSI** (Pass Spread Index, Shannon entropy on assist destinations), **STD** (Shot Type Diversity), **FDQ** (Foul Drawn Quality), **And1R** (And-1 Rate), **GAP** (off-ball gravity), **ADI** (Action Diversity Index).

### 2026-06-07 — CP3 writer briefs (defensive_metrics/writer_briefs/)
8 briefs at `defensive_metrics/writer_briefs/` (01 comparison → 08 amplification proof). Verdict: CP3 #6 all-time PG, should have won 2007-08 MVP. Headline datum: Tyson Chandler 9.5→11.8 PPG instant lift moving CHI→NOH = cleanest CP3 amplification A/B test.

### 2026-06-07 — Centers deterrence study (centers_deterrence_study/)
Folder created today with data/docs/results/scripts subdirs. Status: in progress, see `centers_deterrence_study/docs/` for details.

## Architectural lessons banked this session (read before extending)

1. **sportsdataverse hoopR is canonical NCAA bulk source** (player_box + PBP, github raw, no auth)
2. **NBA combine API publishes invitee list weeks before measurements** — 2026 season has names + positions only as of audit date
3. **Label refresh doesn't move rankings** — survivorship bias is in features, not labels. Fix = scrape historical anchors, not relabel
4. **WebFetch via Wikipedia/scoutbasketball/team-official is the viable intl pipeline** (RealGM/ProBallers/EuroLeague-official 403 even via WebFetch)
5. **Outcome-calibration > stat-normalization** — load-bearing finding
6. **Bigs systematically under-valued by box-score-only hand composites** (drives Mara/Wilson/Steinbach upgrades)
7. **NCAA PBP gaps**: athlete_id_2 NaN for shots+fouls; assist credit lives in regex `(NAME assists)` text pattern. No play-type tags (no ADI), no tracking (no GAP), no defender attribution (no DCHS)
8. **Bigs dominate STD by construction** — varied shot inventory drives higher Shannon entropy than guards/shooters
9. **v4 teammate features broke forward projection** — Maliq Brown #10→#60, intl prospects NaN-imputed to identical preds. Banked: teammate context is diagnostic layer, not model input

## Cardinal rules held throughout

- "we don't project on other's projections ever. raw data only" — ZERO ESPN/Tankathon/Athletic mocks used as inputs
- "no fancy math / no formulas at all they're proprietary" — consumer glossaries only
- "i am 100% for posting and time stamping bold ass predictions IF we can justify them" — bold contrarian calls timestamped + pre-registered, NOT hedged

## Post-draft evaluation plan (locked, fires after late-June 2026 NBA Draft)

1. **Pick delta per prospect** — actual vs Resolve rank
2. **NBA Year-1 production check** — observed per-36 stats vs projected
3. **Method attribution** — which signal (v3 / hand / advanced / Resolve) called each pick most accurately
4. **Bold predictions scorecard** — each contrarian call evaluated

## Open items / parked for v2

- **Comp normalization v5**: scrape 20-30 more historical intl anchors per bucket; direction-of-move covariate for survivorship; per-season age progression
- **Advanced metrics v2**: Box +/- via substitution lineup tracking; And1R via FT-pairing; compute PSI for HISTORICAL 2023-24 NCAA prospects
- **Calibration**: 80% holdout interval at 75.8% — under-cover ~10%, widen v2

## Cross-references

- Memory: `[[project-resolve-lottery-2026-06-07]]`, `[[project-nba-prospect-advanced-metrics-2026-06-07]]`, `[[project-nba-competition-normalization-2026-06-07]]`, `[[project-nba-draft-prep-2026-2026-06-07]]`, `[[project-nba-rookie-decomp-suite-2026-06-07]]`, `[[project-cp3-writer-briefs-for-E-2026-06-07]]`
- Feedback: `[[feedback-raw-data-only-no-projecting-on-projections]]`, `[[feedback-bold-timestamped-predictions]]`, `[[feedback-ship-projections-not-papers]]`
- Sibling repos: `D:/NFL Projections`, `D:/NHL Projections`, `D:/MLB`, `D:/Golf`

## Production legacy artifacts (frozen, not modified this session)

- `models/stan/` — Stan files for v3+ skill projection
- `audit_runs/` — gitignored multi-GB per-fit outputs
- `paper_draft/` — Sloan paper sections (NBA + cross-domain)
- `PAPER_STATE.md` + `NBA_SUITE_2026_05_19.md` — pre-this-session VC pitch state
- `PRE_REGISTRATION_NBA_PLAYOFFS_25_26.md` — 2025-26 playoffs pre-reg (locked)

## Engineering log archive

Pre-2026-06-07 history lives in `PAPER_STATE.md` (Sloan paper progress) and `NBA_SUITE_2026_05_19.md` (VC pitch consolidation). Both kept for reference; this file is the forward log.
