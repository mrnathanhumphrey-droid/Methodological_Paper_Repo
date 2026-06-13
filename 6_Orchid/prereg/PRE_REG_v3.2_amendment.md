# Pre-Registration v3.2 — Amendment to RMD-SRC *Gymnadenia* v3.0

**Issued:** 2026-06-01.
**Type:** Diagnostic-driven amendment. Triggered by v3.1 result (chemotype dummy confirmed real signal at p<0.01 on 6/7 obs but worsened cleanness via residual-spike artifact). v3.2 swaps the v3.1 additive-dummy operationalization for **subcell-level cleanness evaluation** using the locked within-cell joint 7-D GMM labels.
**Status:** LOCKED v3.2, 2026-06-01.

## Trigger and v3.1 lesson

v3.1 added a single binary `Corv_monomorph` dummy to the Huber response function. β_m was significant at p<0.01 on 6/7 observables (chemotype is real signal). But cleanness REGRESSED from 12.5% → 5.4% pre-decomp because the dummy created a residual-spike at zero for the 23 corrected plants → Anderson–Darling penalized the pooled residual distribution → x2 lost AD-clean status.

The diagnostic: **additive dummy correction is the wrong operationalization for latent classes.** What's needed is to honor the latent-class structure at the **cleanness-evaluation** layer, not at the model-fit layer.

## Amendment to §3.5 (Step 4c)

**v3.0 §3.5 (operative for non-v3.2 use):** 4c GMM k=1..3 per (cell, observable) on the single observable's plant scores. BIC-select.

**v3.2 §3.5 (operative):** 4c uses the **locked joint 7-D GMM labels** from the within-cell-noise analysis (`results/within_cell/<cell>_gmm_labels.parquet`) instead of re-fitting per-observable. This honors the joint phenotype-space cluster structure already identified.

Operationally:
- Cells with locked `best_k_gmm_7d` = 1 (per `results/within_cell/summary.parquet`): no 4c split. Carry through.
- Cells with locked `best_k_gmm_7d` ≥ 2: subdivide using the locked plant→cluster mapping. Evaluate v3.0 cleanness gates per subcell.
- A subcell is clean iff it has n ≥ 50 AND all v3.0 §2.9 gates pass on subcell residuals from the global v3.0 Huber fit (which is NOT re-fitted; same fit as v3.0).

## Response function unchanged

v3.2 §3.4 is identical to v3.0: Huber RLM, env_PC1 + y2011, no morph dummies. **The v3.1 dummy is REMOVED.** Single difference vs v3.0: §3.5 4c uses locked joint GMM labels rather than per-observable 1-D BIC.

## Pre-committed hypotheses

**H_v3.2A:** Post-decomp clean rises above v3.0's 16.1 %.

**H_v3.2B:** Corviglia subcells stratified by chemotype achieve cleanness on ≥ 3 of 7 observables for the non-morph subgroup.

**H_v3.2C:** L_Ross MethylEugenol subcell + M_Muen benzoid subcell additional clean recoveries beyond Corviglia.

## Audit chain

| Object | v3.2 status |
|---|---|
| `step3_response_function_v30.parquet` | inherited unchanged (same fit) |
| `step3_cell_cleanness_v30.parquet`    | inherited unchanged |
| `step4_leaves_v32.parquet`            | NEW |
| within-cell GMM labels                  | inherited locked (no re-cluster) |

## What this tests

If H_v3.2A confirms: the chemotype latent classes ARE the right decomposition layer; honoring them at cleanness time recovers the cells the additive dummy could not. The Mode C diagnosis was about cell-evaluation granularity, not model-fit form.

If H_v3.2A fails: the locked 7-D GMM clusters do not align with the within-cell residual structure under Huber. Says the chemotype hypothesis needs sharper operationalization (mixture-of-regressions, v3.3 not pre-named).
