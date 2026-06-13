# v6.1 Post-Mortem (Session 2 — locked spec)

**Date:** 2026-05-02
**Scope:** All work from session 2 (post-compact 2026-05-01 evening through 2026-05-02) that took v6.1 from its initial 2-season-validated form to its locked 3-season-validated form. This is the document the 26-27 refit cycle should read first.

---

## Summary

v6.1 went through three states this session:

| State | Mean offsets | Variance multipliers | PTS MAE | AST MAE |
|---|---|---|---|---|
| Initial (2-season-validated) | 5 | 12 | 1.8120 (-2.97%) | 0.6381 (-4.23%) |
| 3-season post-cleanup intermediate | 3 | 4 | 1.8203 (-2.52%) | 0.6431 (-3.47%) |
| **LOCKED** | **3** | **3** | **1.8203 (-2.52%)** | **0.6428 (-3.52%)** |

The locked spec is smaller and softer than the initial ship. We gave up apparent MAE gains to ship something defensible across 3 cross-validated seasons with clean classes. Initial gains on REB and TOV were false positives that didn't replicate at 24-25.

**Locked spec:**

```python
VALIDATED_OFFSETS = {
    "PTS": {"position": {"Center": -0.587}},        # ADDITIVE, 3-season alpha
}
VALIDATED_MULTIPLIERS = {
    "PTS": {"mid_season_change": {True: 0.9382}},   # MULT -6.18%
    "AST": {"years_pro_bucket": {"13+": 0.9278}},   # MULT -7.22%
}
```

```python
VARIANCE_MULTIPLIERS = {  # all TIGHTEN
    ("REB", "position", "Guard"): 0.723,
    ("AST", "position", "Forward"): 0.819,
    ("BLK", "position", "Guard"): 0.662,
}
```

---

## Timeline

| Time | Event |
|---|---|
| ~22:00 EDT 5/1 | Resume post-compact; 5-stat 22-23 chain in flight (`bbcczit4w`) |
| 22:00 | Audit availability map: 24-25 audits fireable now, older seasons need box-score backfill |
| ~22:30 | Wrote brief `fetcher_brief_historical_box_scores_backfill.md` (14-15 to 18-19 backfill) |
| 23:00–01:54 | Fetcher landed (`130,406 new rows`, 11 seasons total, 1529 unique players, 461 metadata backfilled) |
| ~01:55 | Cross-season validation at 2-season pool: 35 mean candidates surfaced, 12 variance candidates |
| ~02:30 | Add-vs-mult tests on REB×mid_season, AST×years_pro 13+, TOV×years_pro 13+ — picked forms |
| ~03:00 | Initial v6.1 shipped (5 offsets, 12 variance multipliers) |
| 03:00–05:48 | 6-stat 24-25 chain (`bqkjv1stk` first try bailed at STL via `set -e`; `box1henb0` patched script finished BLK + TOV at 05:48) |
| 06:00 | Cross-season validation at 3-season pool — REB×mid_season and TOV×years_pro 13+ DROPPED; magnitudes softened |
| ~06:30 | Found smoke-test audit pollution; patched `find_audits` tiebreak from mtime → file size |
| ~07:00 | Found pre-2014 draft data "ghost class" contamination; centralized `_class_features.py` with `debut_year` + metadata `draft_pick` fixes |
| ~07:30 | Re-validated; refit magnitudes |
| ~08:00 | Hierarchical Stan fit (138 cells × 3 years × 21,546 obs, ~20 min wall) |
| ~08:30 | Tested top-3 Stan-flagged candidates — all rejected; spec locked |

---

## Methodology evolution

The protocol gained five rules this session (now 11 total). Each was learned the hard way.

### Rule 6 — single-season LOO necessary but not sufficient (carried over from prior session)

The initial 23-24 LOO surfaced 8 strong-SNR candidates. Forward validation at 22-23 → 23-24 rejected most. 3-season cross-season validation rejected even more.

### Rule 7 — NaN buckets are real classes, BUT verify they're not data-quality artifacts

In session 1, the protocol said "ship NaN buckets if they pass cross-season." This session showed `years_pro_bucket=nan` was actually pre-2014-drafted vets whose `draft_year` was missing because `nba_draft_data.parquet` only covered 2014+. Same condition for `draft_pick_tier=undrafted`. **The fix was data-layer**: use metadata's own `draft_pick` (CommonPlayerInfo populated, with 0 = nba_api's "undrafted" sentinel) and `debut_year` for years_pro.

### Rule 8 — trajectory check on top of cross-season sign-replication

Three real examples this session:
- PTS × mid_season: -1.896 → -1.207 → -0.301 (fading hard, but signs all negative — passed sign-replication)
- TOV × mid_season: -0.212 → -0.130 → -0.008 (essentially extinguished)
- PTS × draft_pick_tier=late_first: -0.104 → -0.345 → +0.093 (sign FLIPPED in 24-25)

Cross-season sign-replication only checks "all signs the same." Doesn't catch monotonic fade or single-season flip. Per-season trajectory is now a required gate.

### Rule 9 — Stan stability_fraction is a ranking lens, not a ship gate

`stability_fraction[c] = sigma²[c] / (sigma²[c] + tau²[c])`. High value = year-to-year mean variance is small relative to within-year noise. **Not** the same as "the offset replicates predictably."

PTS × draft_pick_tier=late_first hit stability **0.94** (highest of all 138 cells) but had a 24-25 sign flip. Stan can't see year ordering — years are exchangeable in the model.

Use Stan to *prioritize* candidates for trajectory + magnitude/SD checks. Do not ship Stan-shrunk values directly.

### Rule 10 — operational threshold |alpha| / cohort_residual_SD ≥ ~20%

Calibration anchors:
- PTS × Center: -0.587 / 2.41 = 24% → ships
- AST × years_pro 13+: -0.257 / 0.94 = 27% → ships
- REB × draft_pick_tier=lottery: -0.123 / 0.91 = 14% → **rejected** (signs all negative across 3 seasons, but signal too weak to move MAE)

Below ~20%, applying a uniform shift to a high-SD cohort improves MAE for some players, worsens for others, with net near zero.

### Rule 11 — pipeline-mismatch: derive on the same model you ship to

AST × draft_pick_tier=lottery cleared cross_season_full_validation with seasonal means [+0.104, +0.247, +0.086] using v4-lite tq_g audit residuals. On the v6 ship CSV, the same cohort had means [-0.005, +0.098, -0.006] — the signal lived in v4-lite but v6's age curves already absorbed it.

When the spec applies to model B, run candidate tests on B's residuals, not the audit pipeline's residuals on the same cohort.

---

## Data infrastructure changes

### Box-score backfill 14-15 to 18-19

`fetcher_brief_historical_box_scores_backfill.md` shipped, fetcher delivered ~1.5 hr later:
- 130,406 new rows (~26K per season, target band ✓)
- 11 seasons total (14-15 to 24-25)
- 1529 unique players (was 1068; +461 metadata backfilled via `CommonPlayerInfo`)
- All 461 added players got `draft_year`, `draft_pick`, `debut_year` populated

Output: `data/parquet/historical_box_scores.parquet` (extended in place; backup at `.backup_20260501`).

### `scripts/_class_features.py` — canonical class-feature module

Created to centralize what was duplicated in 8 scripts. Key fixes:
1. `years_pro = target_year - debut_year` (was `- draft_year`, which broke for undrafted players whose draft_year=0)
2. `draft_pick` taken from metadata (which has `CommonPlayerInfo`-populated values for all players including 0=undrafted), not from `nba_draft_data.parquet` (2014+ only)
3. `_pick_bucket(0)` returns "undrafted" explicitly

Refactored callers: `cross_season_full_validation.py`, `hierarchical_multi_year_runner.py`, `refit_offsets_3season.py`, `test_candidate_3season.py`, `apply_v61_validated_offsets.py`, `apply_v61_variance_multipliers.py`.

### `find_audits` tiebreak: mtime → file size

A 15-row smoke-test audit at 23-24 PTS (max_players=15, n_iter=20) was being preferred over the 195-row canonical audit because it was newer. New tiebreak: largest `per_player_projections.csv` wins. Future-proofs against the same class of bug.

### `fire_v6_24_25_chain.sh` patch — `set -e` removed

STL on 24-25 finished cleanly with `Exception: normal_lpdf: ...` Stan diagnostic warnings → python returned exit 1 → `set -e` killed the chain before BLK/TOV could fire. Replaced with explicit per-stat exit handling that checks `per_player_projections.csv` artifact presence. Diagnostic-warning exits no longer kill the loop.

### Stan model: array syntax + RTools toolchain init

Two patches to `hierarchical_multi_year_runner.py` and `hierarchical_multi_year_offsets.stan`:
1. `int x[N]` → `array[N] int x` (cmdstan 2.36 deprecated old syntax)
2. Added `cmdstanpy.set_cmdstan_path()` + `cxx_toolchain_path()` initialization mirroring `models/skill/fit.py` (Windows env-var inheritance through bash subshells is unreliable)

---

## Spec evolution: how we got from 5 offsets to 3

### Initial v6.1 ship (2-season pool, 22-23 + 23-24)

| Offset | Status at 3-season |
|---|---|
| PTS × Center additive -0.70 | ✓ confirmed (softened to -0.587) |
| PTS × mid_season multiplicative -8.4% | ✓ confirmed (softened to -6.18%) |
| **REB × mid_season additive -0.543** | ✗ **DROPPED** — sign/magnitude didn't replicate at 24-25 |
| AST × years_pro 13+ multiplicative -9.1% | ✓ confirmed (softened to -7.22%) |
| **TOV × years_pro 13+ multiplicative -10.0%** | ✗ **DROPPED** — sign/magnitude didn't replicate at 24-25 |

Two of five offsets failed the 3-season test. Both were the smaller-magnitude additions from session 1's expansion.

### 3-season magnitude softening

Across ALL surviving offsets, 24-25 magnitudes were ~half of 22-23/23-24 magnitudes:

- PTS × Center: -0.722 → -0.684 → **-0.292**
- PTS × mid_season: -1.896 → -1.207 → **-0.301**
- AST × years_pro 13+: -0.146 → -0.562 → **-0.120**

The base v6 model is improving over time at predicting the previously-biased subgroups. Two non-mutually-exclusive explanations:
1. v6's training data accumulates; later test seasons get more training data, making predictions better.
2. League-level changes (rule changes, role changes for the player cohorts) are washing out the historical biases.

The locked spec uses 3-season combined regression alpha/c, which gives shrinkage-toward-zero relative to early seasons — closer to where 24-25 actually lands.

### Variance multiplier prune from 12 → 3

8 of 12 variance multipliers from 2-season pool failed 3-season test. Most were BLK-related (high-noise stat, easily flips). The 3 survivors are all TIGHTEN signals on position-class:

- REB × position=Guard ×0.723
- AST × position=Forward ×0.819
- BLK × position=Guard ×0.662

WIDEN signals (BLK × Center, AST × traded=True, BLK × top5) all dropped. After class-feature cleanup, BLK × draft_pick_tier=late_first also dropped (cohort changed enough that 3-season agreement was lost).

---

## Hierarchical Stan: what we learned

138 cells × 3 years × 21,546 obs. Convergence diagnostics:
- 6/400 divergent transitions (1.5% — mild, not catastrophic)
- ESS satisfactory across all params
- R-hat > 1.01 on ~150 of 414 mu/tau/sigma params (low-data cells; doesn't impact top-stability rankings)

**Stan validates our 3 shipping offsets at high stability:**

| Offset | Our 3-season refit | Stan shrunk | Stan stability |
|---|---|---|---|
| PTS × Center | -0.587 | -0.562 | 0.91 |
| PTS × mid_season | combined alpha -1.005 | -0.863 | 0.83 |
| AST × years_pro 13+ | -0.257 | -0.202 | 0.80 |

**Stan surfaced ~25 high-stability candidates not currently shipping.** Tested top 3:

| Candidate | Stan stability | Verdict | Why rejected |
|---|---|---|---|
| PTS × draft_pick_tier=late_first | 0.94 | ✗ | 24-25 sign flip (-0.345 → +0.093) |
| REB × draft_pick_tier=lottery | 0.91 | ✗ | trajectory clean but magnitude/SD = 14% (below 20% gate) |
| AST × draft_pick_tier=lottery | 0.90 | ✗ | pipeline mismatch (signal in v4-lite audits, absent on v6 ship) |

Three distinct failure modes from the top three candidates. Each surfaced one of rules 9, 10, 11.

---

## What's locked vs what's open

### Locked

- **Spec**: 3 mean offsets + 3 variance TIGHTEN multipliers
- **Methodology**: 11-rule Collatz protocol with cross-season + trajectory + magnitude/SD + pipeline gates
- **Data infrastructure**: 11-season box-score parquet (14-15 to 24-25), centralized class features, find_audits-by-size, set-e-safe chain runner

### Parked until more data

- **Forward validation against 25-26**: true out-of-sample test of the locked spec. Not possible until 25-26 audits exist (presumably after 25-26 season ends or partway through).
- **Multi-year audit campaign for 19-20/20-21/21-22**: data is now available (post-backfill), 24 fits ~12-18 hr sequential. Would extend pool from 3 → 6 seasons of audits per stat. Not fired this session — incremental gain probably small, and 25-26 forward validation should come first.

### Open questions for 26-27 refit cycle

1. **Should Center / mid_season / years_pro 13+ become FEATURES of the base v6 model rather than post-hoc offsets?** The fact that magnitudes are fading season-over-season suggests v6 is learning these patterns; pulling them into v6 directly would be cleaner than patches.
2. **Why is the 24-25 audit cohort ~60% the size of 22-23 / 23-24 (~833 obs vs ~1393)?** Worth investigating before 25-26 lands. Could be max-players filtering, metadata-coverage, or training-data ceiling.
3. **Should we refit v6 with the expanded box-score history (14-15 to 18-19)?** Currently v6 trains on 19-20 onward. The pre-2014 backfill enables 4-5 more training seasons.
4. **Is the locked spec robust to a v6.0 → v6.x base-model upgrade?** Pipeline-mismatch (rule 11) means changing the base model can invalidate offsets. Locked spec assumes v6 baseline.

---

## File / output reference

### Scripts (all at `D:\NBA Projections\scripts\`)

- `_class_features.py` — canonical class-feature attachment (use this everywhere)
- `apply_v61_validated_offsets.py` — applies VALIDATED_OFFSETS + VALIDATED_MULTIPLIERS dicts
- `apply_v61_variance_multipliers.py` — applies SD scaling + builds Wonka v2 table
- `cross_season_full_validation.py` — sign-replication + variance ratio across all available season audits
- `refit_offsets_3season.py` — recomputes alpha and c on 3-season combined cohort
- `test_candidate_3season.py STAT CLASS VALUE` — full diagnostic gate on one candidate
- `hierarchical_multi_year_runner.py [--dry-run | --fit]` — Stan model runner
- `hierarchical_multi_year_offsets.stan` — Stan model file
- `fire_multi_year_audits.sh [--fire]` — orchestrator for older-season backfit campaign
- `fire_v6_24_25_chain.sh` — sequential 6-stat fit at 24-25 (set-e-safe version)

### Outputs

- `audit_runs/unified_ship_v6_1/per_player_projections_2023-24.csv` — locked v6.1 ship
- `audit_runs/unified_ship_v6_1/metadata.json` — provenance for each shipped offset
- `data/parquet/cross_season_validated_offsets.parquet` — current cross-season-validated mean offsets
- `data/parquet/cross_season_validated_variances.parquet` — current cross-season-validated variance multipliers
- `data/parquet/wonka_variance_multiplier_v2.parquet` — Wonka v2 per-player-per-stat SD multipliers (270 rows)
- `data/parquet/hierarchical_validated_offsets.parquet` — Stan output (138 cells × posterior summaries + stability_fraction + shrunk_offset)

### Memory entries (for future sessions)

- `memory/feedback_collatz_protocol_for_projections.md` — 11-rule discipline (read first)
- `memory/project_nba_proj_v61_locked_2026_05_02.md` — this snapshot, indexed in MEMORY.md

### Audit dirs (24-25 chain that finished overnight)

- PTS: `audit_runs/20260502T040204Z/skill_backtest_PTS_phase4_v4_quadratic_tq_g_2019-20-2020-21-2021-22-2022-23-2023-24__2024-25/`
- REB: `audit_runs/20260502T051745Z/...`
- AST: `audit_runs/20260502T062901Z/...`
- STL: `audit_runs/20260502T071900Z/...`
- BLK: `audit_runs/20260502T085540Z/...`
- TOV: `audit_runs/20260502T094826Z/...`

---

## What the 26-27 refit cycle should do first

1. **Read this document** and `feedback_collatz_protocol_for_projections.md` to load the 11 rules.
2. **Verify v6 baseline still applies** — if v6 was upgraded between sessions, locked spec may need re-derivation per Rule 11.
3. **Fire 25-26 audits when available** for all 6 main stats (4-prior-season train, ~3-5 hr).
4. **Run forward validation**: apply locked spec to 25-26 audit residuals; check whether each offset still produces MAE improvement on the new cohort. Any that fail → drop or refit.
5. **Re-run cross-season validation at 4-season pool** (22-23 + 23-24 + 24-25 + 25-26) — new pool, stricter test, will refresh both surviving offsets and any new candidates.
6. **Re-run hierarchical Stan** with 4 years; the model gains real shrinkage power (stability_fraction estimates are tighter; `n_years >= 4` is well above the threshold).
7. **Re-investigate top-stability candidates** with the trajectory + magnitude/SD + pipeline gates from rules 8-11. Don't trust Stan alone.

The goal of the 26-27 cycle is not "more offsets." It's "the offsets we ship are operationally honest under the strongest test we can run with the data we have." This session showed the methodology works — it caught and pruned false positives between session 1 and session 2.
