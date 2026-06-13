# Spec drift from Wonka — pinned 2026-04-25

The original `projection_model_spec.md` had stale references to Wonka's actual code. Captured here so we don't repeat the discovery work, and so future spec updates align to reality.

Wonka source-of-truth at pin time: `D:\Wonka Resolve\models\schemas.py` (`PlayerProjection`, `StatProjection`), `D:\Wonka Resolve\projections\ensemble.py` (`blend_player`), `D:\Wonka Resolve\projections\multi_source_csv.py` (audit-CSV ingester), `D:\Wonka Resolve\config\source_weights.py` (per-cat source weights).

| # | Drift item | Spec said | Wonka actually does | Resolution |
|---|---|---|---|---|
| 1 | Spec file path reference | "auction_tool_spec.md §2.1" | No such file at `D:\Wonka Resolve\docs\`; only `PROJECT_NOTES.md` exists | Update our spec to point at Wonka's `models/schemas.py` and `projections/ensemble.py` as the authoritative contract |
| 2 | Player ID type | `player_id: str` | `nba_api_id: int` | Use `nba_api_id` (int) everywhere |
| 3 | Category set | 18 granular stats | 10 categories + 4 support stats; treats A/T as a category, derives it from AST/TOV | **Project all 18 in Artifact B (standalone-first); adapter projects down to Wonka's subset in Artifact A.** A/T is never in our output — Wonka derives it. |
| 4 | TOV vs A/T | TOV first-class | A/T is a category in Wonka; TOV lives in `support_stats` | Ship `TOV` first-class in Artifact B; Wonka computes A/T downstream from `AST_proj / TOV_proj` |
| 5 | Ratio convention | Not specified | Wonka auto-detects 0-100 vs 0-1 (>1.5 → /100), normalizes internally to fractions | Always ship 0-1 fractions in both artifacts; document the convention |
| 6 | Joint posteriors | First-class output (1000 samples) | No consumer in current Wonka code; ensemble collapses to mean + stddev | Ship anyway — standalone-first. Phase 7 schedules a Wonka adapter (`bayes_internal_json.py`) to consume the joint samples properly. |
| 7 | Variance handover | Not addressed | Wonka recomputes `total_stddev² = structural² + inter_source²` per cell | Wonka's future Bayesian adapter must **skip structural-variance recomputation** on our cells. Documented in `projection_contract.md`. |
| 8 | 3PT stat naming | `threePM, threePA, threeP_pct` | Wonka category constant: `3PTM`. Audit CSV columns: `3PM_proj, 3PA_proj, 3P_pct_proj` | Standardize internally on `3PM, 3PA, 3P_pct`. JSON keys quoted (start with digit). Adapter writes `3PM_proj` etc. for the audit CSV. |
| 9 | Source registration | Not addressed | Wonka has `ENSEMBLE_SOURCES = (rotowire, fantasypros, hashtag, razzball)` and `SOURCE_WEIGHTS` table | One-time Wonka-side change at V1 ship: add `"bayes_internal"` to `ENSEMBLE_SOURCES` and assign per-cat weights |
| 10 | Name resolution | Spec assumes ID is direct | Wonka's CSV ingester uses 5-pass name cascade (`name_resolver.py`); single-source override file at `projections/overrides_<source>.json` | Publish `overrides_bayes_internal.json` mapping our names → IDs to bypass the cascade (we already know the IDs) |
| 11 | Support stats | Not addressed | Wonka tracks `FGA_per_game, FTA_per_game, FTM_per_game, TOV_per_game` for ratio math | These come for free in our 18-stat set (FGA, FTA, FTM, TOV are all there). The audit-CSV adapter writes them to `*_proj` columns; future Bayes-JSON adapter reads them from `cells[*].mean` |
| 12 | Variance double-counting | Not flagged | Wonka multiplies stddev by structural multipliers (rookie, traded, injured, age curve). Applied on top of source-level stddev. | Our posterior already encodes parameter + aleatoric variance. Wonka's existing CSV path strips our stddev anyway (only reads means). The future Bayes-JSON path must skip structural recomputation. |

User decision (2026-04-25): "standalone first, direct to Wonka second." Locks in resolution direction: when Wonka's expectations conflict with the standalone product's needs, **the standalone product wins**, and Wonka gets an adapter.

---

## Action items captured

- [ ] **Update `projection_model_spec.md`** to fix items 1, 2, 4, 5, 8 (path, ID, TOV/A-T, ratio convention, 3PT naming) — these are pure spec corrections
- [ ] **Phase 1 deliverable:** Artifact A formatter (CSV) + override file for Wonka name resolution
- [ ] **Phase 7 deliverable:** Artifact B formatter (JSON) + posterior serializer
- [ ] **Phase 7 Wonka coordination:** add `"bayes_internal"` to `ENSEMBLE_SOURCES`, assign weights, deploy `overrides_bayes_internal.json`
- [ ] **V1.1 stretch:** Wonka-side `bayes_internal_json.py` adapter to consume Artifact B with joint samples + skip structural-var recomputation
