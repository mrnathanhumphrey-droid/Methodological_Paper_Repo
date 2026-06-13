# Projection Contract — V1

Pinned 2026-04-25. The NBA Projections project ships **two output artifacts** per refresh.

- **Artifact B** (`output/projections_full.json`) is canonical. All 18 fantasy-relevant stats with full Bayesian posterior samples + joint samples. This is the standalone product.
- **Artifact A** (`output/projections_audit.csv`) is a Wonka-compat adapter. Posterior means only, in Wonka's existing audit-CSV column schema. Drops into Wonka's ingest pipeline with zero new code on Wonka's side.

The orientation: standalone-first, Wonka-second. Artifact B is the source of truth; Artifact A is generated from it.

---

## Categories (canonical 18-stat set)

Volume / counting:
`PTS, REB, OREB, DREB, AST, STL, BLK, TOV, FGM, FGA, FTM, FTA, 3PM, 3PA, MIN`

Ratio:
`FG_pct, FT_pct, 3P_pct`

Conventions:
- **Ratio cats are stored as fractions in [0, 1]** (e.g., `0.474`, never `47.4` or `47`). Wonka's audit-CSV ingester auto-detects scale (>1.5 → /100), but we ship fractions consistently to remove ambiguity.
- **Player ID is `nba_api_id` (int)** — the NBA API's `person_id`. Never a string.
- **A/T is NOT a first-class category in Artifact B.** Wonka derives it downstream from `AST / TOV`. Artifact A also omits it.

---

## Artifact B — Full posterior JSON (canonical)

Path: `output/projections_full.json`

```jsonc
{
  "schema_version": "2.0",
  "model_version": "<semver>",         // e.g., "1.0.0"
  "generated_at": "<ISO8601 UTC>",
  "prior_specification": "<id>",       // e.g., "v1.2_aging_2026q1"
  "n_posterior_samples": 1000,         // N for cells[*].posterior_samples and joint_samples
  "players": [
    {
      "nba_api_id": 12345,
      "player_name": "First Last",
      "team": "ABC",
      "position": "PG",
      "age": 27,
      "experience_years": 5,
      "role": "starter",               // starter | rotation | bench | inactive
      "injury_status": null,           // string or null
      "confidence_tier": "high",       // high | medium | low
      "notes": "",

      "expected_games_played": {
        "mean": 75.0,
        "median": 76.0,
        "stddev": 5.0,
        "quantiles": {"p10": 68, "p25": 73, "p50": 76, "p75": 79, "p90": 81},
        "posterior_samples": [/* N floats */]
      },

      "cells": {
        "PTS":     {"mean": ..., "median": ..., "mode": ..., "stddev": ..., "quantiles": {...}, "distribution_family": "normal", "posterior_samples": [/* N */]},
        "REB":     {/* same shape */},
        "OREB":    {/* ... */},
        "DREB":    {/* ... */},
        "AST":     {/* ... */},
        "STL":     {/* ... */},
        "BLK":     {/* ... */},
        "TOV":     {/* ... */},
        "FGM":     {/* ... */},
        "FGA":     {/* ... */},
        "FG_pct":  {/* ... */},
        "FTM":     {/* ... */},
        "FTA":     {/* ... */},
        "FT_pct":  {/* ... */},
        "3PM":     {/* ... */},
        "3PA":     {/* ... */},
        "3P_pct":  {/* ... */},
        "MIN":     {/* ... */}
      },

      "joint_samples": [
        {"PTS": 22.1, "REB": 4.3, "OREB": 0.6, /* ...all 18 stats... */},
        /* N rows; each row is one plausible "season" preserving inter-stat correlations */
      ]
    }
  ]
}
```

`distribution_family` values: `"normal"`, `"skewed_right"`, `"skewed_left"`, `"bimodal"`, `"heavy_tailed"`. Set by the model per cell based on posterior shape; downstream consumers can fast-path Gaussian assumptions when family == `"normal"`.

---

## Artifact A — Audit CSV (Wonka-compat adapter)

Path: `output/projections_audit.csv`

Column schema matches Wonka's existing audit format at `D:\Wonka Resolve\audit\data\parsed\*_projections.csv`:

```
source, player_name, team, position, games_proj, minutes_proj,
PTS_proj, REB_proj, AST_proj, STL_proj, BLK_proj, TOV_proj,
FGM_proj, FGA_proj, FG_pct_proj,
FTM_proj, FTA_proj, FT_pct_proj,
3PM_proj, 3PA_proj, 3P_pct_proj
```

Adapter rules (`Artifact B → Artifact A`):

| CSV column      | Source in Artifact B                              |
|-----------------|---------------------------------------------------|
| `source`        | literal `"bayes_internal"` for every row          |
| `player_name`   | `players[i].player_name`                          |
| `team`          | `players[i].team`                                 |
| `position`      | `players[i].position`                             |
| `games_proj`    | `players[i].expected_games_played.mean`           |
| `minutes_proj`  | `players[i].cells.MIN.mean`                       |
| `PTS_proj`      | `players[i].cells.PTS.mean`                       |
| `REB_proj`      | `players[i].cells.REB.mean` (combined OREB+DREB)  |
| `AST_proj`      | `players[i].cells.AST.mean`                       |
| `STL_proj`      | `players[i].cells.STL.mean`                       |
| `BLK_proj`      | `players[i].cells.BLK.mean`                       |
| `TOV_proj`      | `players[i].cells.TOV.mean`                       |
| `FGM_proj`      | `players[i].cells.FGM.mean`                       |
| `FGA_proj`      | `players[i].cells.FGA.mean`                       |
| `FG_pct_proj`   | `players[i].cells.FG_pct.mean` (fraction, 0-1)    |
| `FTM_proj`      | `players[i].cells.FTM.mean`                       |
| `FTA_proj`      | `players[i].cells.FTA.mean`                       |
| `FT_pct_proj`   | `players[i].cells.FT_pct.mean` (fraction, 0-1)    |
| `3PM_proj`      | `players[i].cells["3PM"].mean`                    |
| `3PA_proj`      | `players[i].cells["3PA"].mean`                    |
| `3P_pct_proj`   | `players[i].cells["3P_pct"].mean` (fraction, 0-1) |

Stats present in Artifact B but dropped in Artifact A (Wonka doesn't read them today): `OREB`, `DREB`. They're aggregated into `REB_proj` for the CSV. Internally we keep OREB/DREB separate because future consumers (waiver/trade analyzer, shot-chart correlations) want them.

`nba_api_id` is **not** a column in Artifact A. Wonka resolves names back to IDs via its own `name_resolver.py` cascade. To improve resolution reliability for our internal source, we'll publish an override file at `D:\Wonka Resolve\projections\overrides_bayes_internal.json` mapping our exact `player_name` strings to `nba_api_id`s — bypassing the cascade for our CSV.

### Wiring into Wonka (one-time setup)

1. Add `"bayes_internal"` to `ENSEMBLE_SOURCES` in `D:\Wonka Resolve\config\source_weights.py`
2. Add per-category weights to `SOURCE_WEIGHTS` (start with uniform; tune from audit results)
3. Drop `output/projections_audit.csv` next to the four existing audit CSVs at `D:\Wonka Resolve\audit\data\parsed\`
4. Re-run `cli/build_player_pool.py`

These four steps are Wonka-side changes, made when V1 ships.

---

## Future: Wonka consuming Artifact B directly

Wonka's current ingest path collapses our posteriors to mean+stddev and re-applies its own structural-variance multipliers on top. That double-counts uncertainty. To consume Artifact B properly, Wonka needs a new adapter:

- New file: `D:\Wonka Resolve\projections\bayes_internal_json.py`
- Reads `cells[c].mean` and `cells[c].stddev` directly into a `PlayerProjection`
- **Skips structural-variance recomputation** for our cells (our stddev already encodes parameter + aleatoric variance)
- Optionally reads `joint_samples` for correlation-aware ratio math (would replace Wonka's current per-cat-marginal aggregation with proper joint sampling)

Out of scope for V1 ship. Coordinate when adding.

---

## Refresh cadence

- **Pre-season**: Sept-Oct, both artifacts published before draft window
- **Mid-season**: weekly refresh, both artifacts
- **In-game / live**: out of scope for V1

---

## Schema versioning

Both artifacts carry `schema_version`. Rules:

- **MAJOR** (e.g., 2.0 → 3.0): rename or remove a field; change ID type; change ratio convention. Requires Wonka coordination before ship.
- **MINOR** (e.g., 2.0 → 2.1): add a field; add a category to `cells`; expand `notes`. Backwards-compatible.
- **PATCH** (e.g., 2.0.0 → 2.0.1): fix a bug in a value. No schema change.

V1 ships at `2.0`. The bump from Wonka's `1.0` PlayerProjection reflects the addition of `posterior_samples`, `joint_samples`, `expected_games_played` distribution, `confidence_tier`, and the 18-category set vs Wonka's 10.

---

## Test fixtures

- `tests/fixtures/sample_projection_full.json` — one player, all 18 cells, N=5 samples (real output: N=1000)
- `tests/fixtures/sample_projections_audit.csv` — header + one row, derived from the same player

Phase 7 output formatters validate against these fixtures.
