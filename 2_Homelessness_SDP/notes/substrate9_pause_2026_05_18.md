# Substrate 9 (IDP) — pause point

**Paused:** 2026-05-18
**Reason:** Phase 1 first-pass landed cleanly, then `precond_2` (GDELT↔UCDP-GED
admin-2 × year Spearman ≥0.6 cross-source-agreement check) FAILED on all 4
countries. The locked walk-back (shock indicator becomes source-specific;
two-model parallel fit) is held back pending a fresh angle on the
substrate-level question, which is: *how do we identify ways to help IDPs*,
not just *do conflict shocks intensify displacement in founding-atrocity
polygons*.

## Phase 1 first-pass — what landed (commit 325ca0a)

| Item | Status |
|------|--------|
| GDELT 2014-2024 full panel | LANDED. 4.45M events across 4 countries. Header bug fixed via `_scripts/fix_gdelt_phase1_headers.py` (61-col → 58-col GDELT 1.0 schema). |
| DTM via HDX HAPI v2 | LANDED for SDN (16,452 rows / 186 admin-2) + COD (1,366 / 143) + YEM (4,641 / 329). Colombia gap (HDX returns 0; RUV Power BI scraping deferred to Phase 2). |
| Stage-A polygons (4/4) | LANDED via admin-unit-list dissolution. All PASS `precond_3` (≥5 admin-2 inside): Colombia 658, Sudan 21, DRC 59, Yemen 102. |
| DRC Kasai atrocity-count | LANDED first-pass (0/1/2 coding; 12 HIGH territoires documented). |
| Admin-2 × year combined panel | LANDED. 3,160 rows. Sudan name-join at 14% (Phase 2 normalization queued). |

## precond_2 FAIL — the substrate-level event

| country | annual ρ | monthly ρ | adm2-only ρ | country-year ρ | QC4 adm2-only ρ |
|---------|----------|-----------|-------------|----------------|------------------|
| Colombia | −0.11 | −0.26 | 0.20 | −0.50 | 0.05 |
| Sudan    | 0.33  | 0.12  | 0.43 | 0.22  | **0.52** |
| DRC      | 0.18  | −0.21 | 0.30 | −0.43 | 0.29 |
| Yemen    | 0.11  | −0.19 | 0.34 | −0.12 | 0.33 |

All below the locked Spearman ≥0.6 threshold at every aggregation tested
(annual, monthly, admin-2-only, country-year) and across two GDELT subsets
(all events, QuadClass=4 = Material Conflict). Sudan QuadClass=4 admin-2-only
is the highest at 0.52, still below threshold.

**Substantive finding:** GDELT (media-attention event extraction) and UCDP-GED
(vetted fatal armed-conflict events) genuinely measure different phenomena at
admin-2 × time resolution across all 4 countries. Volume mismatch is not the
explanation — DRC's GDELT/UCDP ratio is 7× (lowest), yet correlation is still
poor; ratios elsewhere are 75-390×.

Negative country-year correlations in 3 of 4 countries (Colombia −0.50, DRC
−0.43, Yemen −0.12 across all-GDELT view; Colombia −0.63 under QC4) suggest
news-cycle attention and vetted-fatal-event capture respond to *anti-correlated*
temporal dynamics at country level.

## Path-forward options (locked-walk-back HELD)

The locked walk-back said: reframe shock as source-specific, two-model parallel
fit, §5 cross-source axis promotes from robustness to primary. That walk-back
is being deliberately deferred — user direction is to step back from the locked
shock-amplification framing and find a fresh angle on the substrate question.

Three flavors of reset previously surfaced (not picked):
1. Reset shock operationalization — try a different conflict measure on the
   existing polygons + hypothesis.
2. Reset load-bearing hypothesis — keep the 4 polygons, ask a different
   question (e.g., baseline displacement persistence, not shock amplification).
3. Reset substrate — pause substrate 9, pivot to a different open line.

## Picked path

**Substrate 9 paused. Fresh angle on "how to help IDPs" is the substantive
direction, but it's a fresh session question, not a within-substrate-9
continuation. Phase 1 deliverables remain in place; precond_2 FAIL is
documented; nothing committed locks the walk-back.**

## What stays on shelf, ready to resume

- All Phase 1 data on disk (4.45M GDELT events, 22,459 DTM rows, 4 polygons, 240 DRC atrocity codings, 3,160-row combined panel)
- All scripts versioned + working
- Pre-reg redline trail is intact through Entry 002
- Sanity-check diagnostics committed for full audit trail

When a fresh angle surfaces, the resume path is: read this file + the substrate-9
memory in `~/.claude/projects/.../memory/project_idp_substrate9_2026_05_17.md`.

## Honest caveats remaining (pre-pause)

- Sudan HDX↔GADM name join at 14% (transliterated Arabic; Phase 2 normalization)
- Yemen Ghamir district not in GADM (1 of 8 ICG-explicit districts unmatched)
- DRC Young & Turner archive.org PDF restricted (controlled digital lending)
- Colombia RUV longitudinal panel deferred to Phase 2 Power BI scraping
