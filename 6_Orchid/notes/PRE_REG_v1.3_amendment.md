# Pre-Registration v1.3 — Amendment to RMD-SRC *Gymnadenia* v1.0 / v1.1 / v1.2

**Issued:** 2026-06-01.
**Type:** Diagnostic-driven amendment. Triggered by VIF / sign-flip diagnostic at Step 3 inspection. Pre-authorized by v1.0 §2.7 ("If Option A's |β_x| is dominated by env-PC1 collinearity (VIF > 5), report and fall back to Option B post-hoc only with explicit log entry").
**Status:** LOCKED v1.3, 2026-06-01.

## Trigger

Inspection of Step 3 v1.2 output (`scripts/orchids/09_inspect_step3.py`) revealed:

- **Pop-level Pearson correlations** (n=8):
  - env_PC1 × ρ_x = **0.975**
  - env_PC1 × ρ_s = 0.910
  - ρ_s × ρ_x = 0.916
- **Plant-level VIF** (n=1028):
  - env_PC1 = **27.0**
  - ρ_x = **27.9**
  - ρ_s = 6.5
  - y2011 = 1.0
- **β_g sign flip in x2:**
  - Full model (env_PC1 + ρ_s + ρ_x + y2011): β_env = **+1.488** (positive)
  - Option B (env_PC1 + y2011 only): β_env = **−0.322** (negative — matches the Step-1 pooled region means: lowland x2 ≈ 0, mountain x2 ≈ −1.97, slope ≈ −0.40)

All three substantive predictors have plant-level VIF > 5, triggering the v1.0 §2.7 fall-back gate verbatim. The full-model β_env is collinearity-driven; the partial slope of env_PC1 after conditioning on ρ_x (which is ~95% the same variable) inverts.

## Amendment to §2.7

**v1.0 §2.7 (superseded):** Option A — ρ_s + ρ_x community covariates retained in the response function.

**v1.3 §2.7 (operative):** **Option B — drop ρ_s and ρ_x terms.** The response function reduces to:

$$x_j(\text{plant}_i) = \alpha_j + \beta_{g,j} \cdot \mathrm{env\_PC1}(\mathrm{pop}_i) + \beta_{y,j} \cdot \mathbb{1}[\mathrm{year}_i = 2011] + \varepsilon_i$$

Cleanness gates from v1.2 §3.4 amendment carry over identically with one simplification: the regime-consistency check (iii) for Gradient-tracking cells uses β_g sign vs pop's env_PC1 sign (unchanged); the β_s sign-agreement check (which appeared in v1.0 §3.4 via the original spec equation) is dropped because β_s is not estimated.

## v1.0 §2.7 audit-trail justification

v1.0 §2.7 explicitly pre-authorized this fall-back: *"If Option A's |β_x| is dominated by env-PC1 collinearity (VIF > 5), report and fall back to Option B post-hoc only with explicit log entry."*

VIF threshold (5) is exceeded by all three Option-A predictors with margin > 1.3× (ρ_s) to > 5× (ρ_x). The β_g sign flip in x2 between the two specifications is the canonical signature of the collinearity-driven regression pathology v1.0 §2.7 anticipated. The pre-reg therefore licenses v1.3 without an extended amendment defense — it is the documented contingency.

## Other sections unchanged

- §1 spec-locked commitments unchanged.
- §2.4 K=12 partition unchanged.
- §2.5 v1.1 re-derived rotation unchanged.
- §2.6 env_PC1 freeze unchanged.
- §3.3 Step 2 regimes unchanged.
- §3.7 F4 protocol unchanged.
- v1.2 cleanness gates carry over (with β_s removed).

## Re-run scope

Step 3 only. Step 0, Step 1, Step 2 do not depend on §2.7.

## Audit chain

| Object | Status |
|---|---|
| `step3_response_function.parquet` (v1.2) | preserved as `..._v12.parquet` |
| `step3_cell_cleanness.parquet` (v1.2)    | preserved as `..._v12.parquet` |
| `step3_response_function.parquet` (v1.3) | re-written; new hash logged |
| `step3_cell_cleanness.parquet` (v1.3)    | re-written; new hash logged |
| all other artifacts                       | unchanged |
