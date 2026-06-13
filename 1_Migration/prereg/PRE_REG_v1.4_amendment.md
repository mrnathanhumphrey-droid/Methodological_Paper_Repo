# Pre-Registration v1.4 — Amendment to v1.0–v1.3 (RMD-SRC US Internal Migration)

**Amends:** §3.3 (Step-2 trajectory classification) and §3.4 (Step-3 validation, Fragmenting criterion).
**Authored:** 2026-05-28
**Status:** LOCKED v1.4-final, 2026-05-28. Refines two metric pathologies in the literal §3.3 operationalization. Earlier amendments unchanged.

## Why this amendment is honest (metric pathology, not result-tuning)

The literal §3.3 rule was implemented and run (Step 2). Output preserved at
`results/trajectory_classification_v1.3literal.parquet`:

| observable | Fragmenting | Gradient-tracking | Stationary |
|---|---|---|---|
| log_distance | 37 | 0 | 1 |
| log_dest_density | 38 | 0 | 0 |
| opp_deficit | 0 | 37 | 1 |

This output is **degenerate for mechanical reasons**, not because of a substantive
finding we wish to avoid:

1. **opp_deficit "Gradient-tracking" is self-referential.** §3.3 defines gradient-tracking as corr(μ(t), ∇g(t)) > 0.5, and ∇g *is* the opportunity-deficit. Correlating opp_deficit with itself gives corr ≈ 1 by construction → all 37 trivially classified. Mathematically degenerate.
2. **Raw-value dip test over-fires at ~100%.** Hartigan dip flagged 38/38 density and 37/38 distance as multimodal → Fragmenting. The near-universal rate is the tell: the test is detecting that **migration distance and destination-density are intrinsically multimodal** (short regional vs long cross-country moves; rural vs urban destinations) — a property of the observable, not evidence the demographic cell is a mixture. The §3.3 word is "**residual** distribution," but the dip was applied to **raw** observable values.

A genuine mixture-detection test would be selective across cells, not ~100%. These are data-distribution-exposed metric pathologies (cf. the battery CV-near-zero precedent), so refining is integrity-preserving, not result-driven. We are not changing the rule to obtain a preferred substantive answer.

## Amendment A (LOCKED) — refinement

**A1. Step-2 classifies on moment-slope dynamics only.** Remove the raw-value Hartigan dip as a Step-2 Fragmenting trigger. Step-2 precedence becomes:
1. r_var < −0.05 → Concentrating (boson-like)
2. r_var > +0.05 → Diffusing (fermion-like)
3. |r_var| ≤ 0.05 (flat variance):
   a. |r_mu| < 0.02 → Stationary
   b. (observable ≠ opp_deficit) AND grad_corr > 0.5 → Gradient-tracking
   c. else → Fragmenting (none-of-above: mean drifts without gradient-tracking or variance signal)

**A2. opp_deficit gradient-tracking branch skipped.** Because opp_deficit *is* ∇g, its trajectory regime is determined by variance dynamics + mean stability only (steps 1, 2, 3a, 3c). The self-referential gradient-tracking branch (3b) does not apply to it.

**A3. Multimodality (Hartigan dip) moves to Step 3, on response-function residuals.** This matches the spec's own Step-3 Fragmenting criterion ("Response function ill-fit — non-Gaussian residuals"). In Step 3, after fitting the response function per (cell, observable), run Hartigan dip on the residuals; dip p < 0.05 → residuals multimodal → cell not-clean / Fragmenting → Step-4 decomposition. Threshold p < 0.05 (unchanged from §3.3).

**A4. raw_dip_p retained as a stored diagnostic.** The raw-value dip p-value continues to be computed and stored in the Step-2 output as a non-classifier diagnostic, documenting the intrinsic multimodality of distance/density (a parallel substrate observation worth reporting, but not a decomposition trigger).

## Sections updated

| Section | prior | v1.4 |
|---|---|---|
| §3.3 Fragmenting trigger | raw-value Hartigan dip p<0.05 OR none-of-above | none-of-above only (dip removed from Step 2) |
| §3.3 gradient-tracking | all observables | all except opp_deficit (self-referential) |
| §3.4 Step-3 cleanness | R²≥0.30 AND Shapiro p>0.01 | + Hartigan dip on residuals p≥0.05 (multimodal residuals → not clean) |

Unchanged: falsifier thresholds (F1–F4), regime taxonomy, decomposition order 4a→4b→4c, ℙ₀ (v1.2), windows (v1.1), geography (v1.3), all numeric cutoffs (0.02 / 0.05 / 0.5 / 0.05-dip).
