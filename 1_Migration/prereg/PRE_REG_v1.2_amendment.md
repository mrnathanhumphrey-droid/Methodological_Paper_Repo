# Pre-Registration v1.2 — Amendment to v1.0/v1.1 (RMD-SRC US Internal Migration)

**Amends:** §2.4 (ℙ₀ species count and collapse mechanics) of v1.0, as governed by v1.1.
**Authored:** 2026-05-27
**Status:** LOCKED v1.2-final, 2026-05-27. Supersedes the "K=12–16" target and specifies the deterministic collapse algorithm. v1.0/v1.1 otherwise unchanged.

## Why this amendment is honest (not result-driven)

Triggered by the Step-0 **event-count distribution**, which is not an outcome of the study. The outcomes are the moment-flow statistics of the observables (distance, settlement-density, opportunity-deficit) — none of which have been computed. Partition granularity decided on event counts is pre-outcome and pre-registration-legitimate, consistent with the project's diagnostic-driven-amendment standard.

## What changed

**v1.0 §2.4 text:** "48 raw cells, collapsed to **12–16** by combining sparse cells" + "any cell with n<500 events/yr merged with nearest neighbor by age then income."

**Observed (Step-0 diagnose, 994,235 cross-PUMA events, 2012–2021):** only **10 of 48** cells fall below 500 events in their worst year; the other **38 are well-powered every year**. All 10 sparse cells are "with-children" cells in off-peak migration strata (60+ with kids; 18–29 with kids; low-income BA+ with kids). Applying the n<500 rule literally lands near **~38 species, not 12–16**.

The "12–16" was a pre-data estimate carried from the RMD-SRC spec's prior substrates. The operational rule (merge n<500) is retained; the **K=12–16 target is removed** as superseded by the observed distribution.

**v1.2 resolution (LOCKED):** Retain all cells meeting the floor; merge only sub-floor cells via the deterministic algorithm below. Final species count is whatever the algorithm yields (expected ~36–40). Rationale: RMD-SRC is a recursive *decomposition* framework — a finer well-powered initial partition gives Step-4 decomposition room to operate; pre-collapsing to 16 would pre-empt decompositions the data may warrant.

## Locked collapse algorithm (deterministic, reproducible)

Operates **only along age then income**, within each fixed (family, educ) block — family and education are never merged (per the original "by age then income" rule). Each cell carries an age-span (subset of {18–29,30–44,45–59,60+}) and income-span (subset of {lo,mid,hi}); initially singletons.

Within each (family, educ) block, repeat until every cell has min-over-years event count ≥ 500:
1. Select the sparse cell with the **smallest min-year event count**. Tie-break: lowest age-span min index, then lowest income-span min index.
2. Choose its merge partner:
   a. Among cells **age-adjacent** at the same income-span (spans touching on the age axis), pick the one with the smallest min-year count.
   b. If no age-adjacent cell exists (cell already spans the full age range), among cells **income-adjacent** at the same age-span, pick the smallest min-year count.
3. Merge: union the two cells' event sets, age-spans, and income-spans. Recompute min-year count.

The final partition ℙ₀ is the union of all blocks' resulting cells. Merged cells are labeled by their spans, e.g. `45-59∪60+ | inc_lo | kids | BA+`.

Floor (n_c ≥ 50 per cell-bin from v1.0 §2.8) is unchanged and far below the 500-event collapse trigger — the 500 trigger is the partition-construction threshold; the 50 floor is the analysis-estimation minimum.

## Sections updated

| Section | prior | v1.2 |
|---|---|---|
| §2.4 target K | 12–16 | removed; K = algorithm output (~36–40) |
| §2.4 collapse | "nearest neighbor by age then income" (informal) | deterministic algorithm above |

Unchanged: scope, geography, windows, observables, falsifier thresholds, decomposition order, event definition, reporting commitments.
