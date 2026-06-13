# Pre-Registration v3.4 — Amendment to RMD-SRC *Gymnadenia* v3.2

**Issued:** 2026-06-01.
**Type:** Pre-named follow-up from RESULTS_FINAL.md §7 ("v3.4 — Pop random intercept; would directly handle the Remigen outlier and per-pop intercepts; likely +5-10 pp"). Tests whether mixed-effects with Pop random intercept clears the cleanness ceiling that operator-class-only refinements (v3.0–v3.3) hit at 19.6 %.
**Status:** LOCKED v3.4, 2026-06-01.

## Single change vs v3.2

**v3.2 §3.4 (superseded):** Huber RLM, x_j ~ env_PC1 + y2011, no random terms.

**v3.4 §3.4 (operative):** **OLS mixed-effects** with Population random intercept:
$$x_j(\text{plant}_i) = \alpha + u_{\mathrm{pop}(i)} + \beta_g \cdot \mathrm{env\_PC1}(\mathrm{pop}_i) + \beta_y \cdot \mathbb{1}[\mathrm{year}_i=2011] + \varepsilon_i$$
where $u_{\mathrm{pop}} \sim \mathcal{N}(0, \sigma_{\mathrm{pop}}^2)$ and $\varepsilon \sim \mathcal{N}(0, \sigma^2)$.

Fit via `statsmodels.formula.api.mixedlm("x ~ env_PC1 + y2011", df, groups=df['Population'])`.

**Structural note:** env_PC1 is a Pop-level constant. The random intercept $u_{\mathrm{pop}}$ and the fixed effect $\beta_g \cdot \mathrm{env\_PC1}$ both vary at the pop level. With only 8 pops, the model partitions between-pop variance into "env-PC1-explained" (fixed) and "residual" (random). If env-PC1 explains most between-pop variation, $\sigma_{\mathrm{pop}}$ shrinks toward zero. The Remigen outlier means env-PC1 does NOT explain all between-pop variation → $u_{\mathrm{pop}}^{Remigen}$ should be substantially non-zero.

## Cleanness gates

Inherited from v3.2 with one substitution: Huber → OLS-mixed pseudo-R² replaced by **conditional R²** (the fraction of variance explained by fixed + random effects together).

- Global per observable j: conditional R²_j ≥ 0.30 AND pooled residual AD p > 0.01 AND β_g sign consistent
- Per (cell, observable): within-cell AD p > 0.01 AND |μ̂_cell − μ_cell| < 0.5 · sd_cell AND regime check

Residuals computed against **fittedvalues including random effect contribution** — testing whether after pop random shifts are absorbed, the within-pop residuals are normal.

## Step 4c inherited from v3.2

Locked joint-7D GMM labels used as 4c subcell boundary. Subcell evaluation under v3.4 fit.

## Pre-committed hypotheses

**H_v3.4A:** σ_pop (estimated random-intercept SD) is non-trivial (≥ 0.3 on the standardized x_j scale) for at least 4 of 7 observables — confirms Pop-level intercept structure beyond env_PC1.

**H_v3.4B:** Post-decomp clean ≥ 25 % (vs v3.2's 19.6 %). +5-10 pp prior expectation per RESULTS_FINAL.

**H_v3.4C:** Remigen-specific and Corviglia-specific random intercepts $u_{\mathrm{pop}}^{Remi}, u_{\mathrm{pop}}^{Corv}$ are the most extreme (largest |u|) among the 8 pops on multiple observables — confirms the within-region outlier biological reading.

**H_v3.4D (collinearity check):** β_g remains identifiable (SE not exploded, |β_g/SE| > 2) for ≥ 4 of 7 observables. If β_g collapses to noise, the random intercepts absorbed the gradient signal entirely and ∇g is no longer identifiable in the model.

## Audit chain

| Object | v3.4 status |
|---|---|
| `step3_response_function_v34.parquet` | NEW |
| `step3_cell_cleanness_v34.parquet`    | NEW |
| `step4_leaves_v34.parquet`            | NEW |
| `step_random_intercepts_v34.parquet`  | NEW (the u_pop estimates per pop per observable) |
| all v1/v2/v3.0–v3.3 outputs            | preserved |
