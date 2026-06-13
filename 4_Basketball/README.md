# NBA Projections

Pure-Bayesian per-game NBA projection engine. Stan/NUTS hierarchical model producing 18-stat full posteriors with preserved joint structure across categories, designed for fantasy auction valuation, predictive-interval calibration, and combo-prop research.

## Architecture

- **Skill layer**: hierarchical NB2 / Gaussian rate model per stat with quadratic age curves, position-stratified peak-and-decline slopes, team-quality covariate (prior-season win pct), and teammate-gravity covariate (top-4 returners' usage). Stan v3+ models in `models/stan/`.
- **Joint posteriors**: per-stat fits expose draws via cmdstanpy, allowing downstream consumers to construct combo distributions natively without Gaussian-copula assumptions on the marginals.
- **Cohort widening**: separate projection path for sophomores, unfit vets, and rookies (`scripts/cohort_widening_2025_26.py`). Rookie path uses hybrid NCAA-translation + draft-pick-log regression with per-stat method preference (volume stats from pick log, rate stats from NCAA translation).
- **Audit-CSV contract**: shipped output at `audit_runs/.../ship_per_player_projections.csv` carries per-game means + standard deviations per cat. v1.1 schema adds rookie-aware metadata columns (`projection_method`, `years_in_league`, draft details, pre-NBA league/team, `cohort_size_n`, `auction_value_seed` via closed-form Z-score-over-replacement).
- **Ship chain**: orchestrated via `scripts/run_2025_26_ship_pipeline.py` — v1 unified → v2 mpg-blend → v3 3pct → v4 3pa → v5 PTS-authoritative → v6 full consistency → v6.1 LOCKED offsets → v6.2 de-shrinkage (research) → Wonka writer.

## Latest validation results

Held-out validation fit on 2025-26 regular season (train 2019-20 through 2024-25, test 2025-26, `max_players=200` cohort, `iter_warmup=400`, `iter_sampling=400`, 4 chains):

| Stat | MAE    | Convergence                       |
|------|--------|-----------------------------------|
| PTS  | 2.2477 | warnings (R-hat > 1.01 on subset) |
| REB  | 0.6573 | clean                             |
| AST  | 0.6178 | clean                             |
| FG3M | 0.3667 | clean                             |
| STL  | 0.1971 | clean                             |
| BLK  | 0.1703 | clean                             |
| TOV  | 0.3757 | warnings                          |
| FGM  | 0.7738 | clean                             |
| FTM  | 0.8290 | warnings                          |
| FGA  | 1.6262 | warnings                          |
| FTA  | 0.9902 | warnings                          |
| FG3A | 0.9147 | clean                             |

Cohort: top-200 players by historical GP, intersected with `min_test_minutes=400` filter on 2025-26, yields n=124 evaluation cohort for PTS. Cohort and methodology caveats apply when comparing across systems.

Run total wallclock: 15.3 hours (sequential per-stat fit, 4 chains × 1 thread per stat).

## Reproducing

Requires Python 3.12, `cmdstanpy` with RTools40 (Windows), and the parquet data layer under `data/parquet/`.

```
python -m cli.run_v4lite_overnight \
    --train-seasons 2019-20 2020-21 2021-22 2022-23 2023-24 2024-25 \
    --test-season 2025-26
```

Audit dirs land at `audit_runs/<timestamp>/skill_backtest_<STAT>_phase4_v4_quadratic_tq_g_<train>__<test>/` with `per_player_projections.csv` + `backtest_metrics.json`.

Forward-mode fits (no test-season actuals available) use `--forward-mode`, which augments the box-score parquet in-place with prior-season rows relabeled as the target season, then restores the original parquet on exit.

The runner is defensive: lockfile at `audit_runs/.runner.lock`, pre-flight zombie-process scan, per-stat metrics-file verification, 3h per-stat timeout, no retries.

## Repository layout

```
NBA Projections/
├── cli/                 # entry points (backtest, fit, exports, runners)
├── models/skill/        # Stan model wrappers + post-fit logic
├── models/stan/         # .stan model files
├── scripts/             # data builders, validation harnesses, ship-chain orchestrators
├── data/parquet/        # ingested data (box scores, lineups, draft, transactions, ...)
├── audit_runs/          # per-fit outputs (gitignored, multi-GB)
├── paper_draft/         # Sloan paper sections
└── config/              # paths, IDs, fetcher state
```

## Status

- **Production model**: v6.1 LOCKED, paper-validated.
- **Research artifacts**: v6.2 de-shrinkage and v6.3 per-cohort γ held (didn't improve LOO MSE).
- **Cohort widening**: ships separately and concatenates into the unified ship chain.
- **26-27 forward projection**: gated on roster turnover (summer transactions, draft, free agency) before next forward fit.

## License

Private research repository.
