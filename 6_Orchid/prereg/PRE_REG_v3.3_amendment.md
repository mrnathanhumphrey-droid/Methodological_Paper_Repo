# Pre-Registration v3.3 — Amendment to RMD-SRC *Gymnadenia* v3.0 / v3.2

**Issued:** 2026-06-01.
**Type:** Diagnostic-driven amendment. Triggered by observation that PCs x4–x7 persistently fail Anderson–Darling under Huber across v3.0 and v3.2, while x2 + x3 pass. Hypothesis: the failing PCs are mixtures of well-behaved + heavy-tailed compounds; un-rotating to individual compounds may isolate which ones drive the failures.
**Status:** LOCKED v3.3, 2026-06-01.

## Single change vs v3.2

**v3.2 §2.5 (superseded):** d = 7, the seven PCs from `observable_scores_v11.parquet`.

**v3.3 §2.5 (operative):** d = 26, the individual z-standardized raw traits:
- 3 morphology: PlantHeight_cm, InflorescenceLength_cm, NrFlowers
- 22 scent compound log1p concentrations
- 1 ColourCode

Same per-trait z-standardization procedure as v1.1 rotation (pooled cohort fit-set means/sds). Plants with ColourCode NA scored on the 25 non-colour traits (ColourCode dropped from the regression for those rows; logged).

All other v3.2 decisions inherited: K=8 partition (Region × Pop), Huber RLM (env_PC1 + y2011), Anderson–Darling cleanness gate, locked joint-7D GMM labels for 4c, v3.2 §3.5 subcell-cleanness evaluation.

## Falsifier thresholds scale by d

F1: ≥ 80 % of K × d = 8 × 26 = 208 cells clean pre-decomp.
F2: < 50 % clean post-decomp.
F3, F4: same definitions.

## Pre-committed hypotheses

**H_v3.3A:** ≥ 8 of 26 raw observables pass global AD (vs v3.2's 2 of 7 PCs = 28.6%).

**H_v3.3B:** Post-decomp clean ≥ 25 % of 208 (vs v3.2's 19.6%).

**H_v3.3C:** Identify which 1-3 specific compounds are the heaviest-tailed AD-failers across cells — names the bio target for a future v3.4 transformation pre-reg.

## Audit chain

| Object | v3.3 status |
|---|---|
| `step3_response_function_v33.parquet` | NEW |
| `step3_cell_cleanness_v33.parquet`    | NEW |
| `step4_leaves_v33.parquet`            | NEW |
| `step_falsifier_report_v33.parquet`   | NEW |
| all v1/v2/v3.0/v3.1/v3.2 outputs       | preserved |
