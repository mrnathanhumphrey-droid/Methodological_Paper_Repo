# Pre-Registration v1.2 — Amendment to RMD-SRC *Gymnadenia* v1.0 / v1.1

**Issued:** 2026-06-01.
**Type:** Diagnostic-driven amendment. Triggered at Step 3 setup by a structural property of the K=12 partition encoding. NOT result-driven.
**Status:** LOCKED v1.2, 2026-06-01.

## Trigger

v1.0 §3.4 says: *"Fit response function per (cell, observable) with OLS, robust standard errors clustered at origin-PUMA."* The migration substrate has within-cell variation in ∇g, ρ_s, ρ_x (one cell = one demographic species spanning many origin-destination pairs across many years; predictors vary at the event level inside the cell).

The *Gymnadenia* K=12 partition encodes (Region, Pop, Year) inside each cell. **All three predictors are constants within a cell:**

- ∇g = env_PC1 is a Pop-level fixed value (climate + soil + elevation at the site).
- ρ_s = G. odoratissima sPlotOpen 50 km incidence is a Pop-level fixed value (orchid was found / not found in the broad neighborhood, fixed per site).
- ρ_x = mean Picea abies cover in 50 km neighborhood is a Pop-level fixed value.

Within (Pop, Year), env_PC1 / ρ_s / ρ_x have zero variance ⇒ OLS β_g, β_s, β_x are unidentifiable per the v1.0 §3.4 wording. The migration template's "per-cell" granularity is inapplicable for sessile-organism substrates where predictors live at population level.

## Amendment to §3.4

**v1.0 §3.4 (superseded):**
> Fit response function per (cell, observable) with OLS, robust standard errors clustered at origin-PUMA.

**v1.2 §3.4 (operative):**

Response function is fit **once per observable** (d=7 regressions total), pooled across all 1028 plants, with the following equation:
$$x_j(\text{plant}_i) = \alpha_j + \beta_{g,j} \cdot \mathrm{env\_PC1}(\mathrm{pop}_i) + \beta_{s,j} \cdot \rho_s(\mathrm{pop}_i) + \beta_{x,j} \cdot \rho_x(\mathrm{pop}_i) + \beta_{y,j} \cdot \mathbb{1}[\mathrm{year}_i=2011] + \varepsilon_i$$

Notes on operative form:

1. **Pooled-plant regression**, not per-cell. The cell structure is preserved via the year dummy (`year=2011`) and via Pop (entering through env_PC1 / ρ_s / ρ_x). β_g / β_s / β_x are *between-pop* effects; β_y is the *between-year* effect; the regression has 1028 rows.

2. **Robust standard errors clustered at Pop.** Pop is the natural independence level — within-pop residuals share the env-PC1 / ρ_s / ρ_x values and any site-level unmeasured covariate. (Spec analog: migration v1.0 clusters at origin-PUMA; pop is the orchid analog.)

3. **Year dummy added** to absorb between-year intercept shift (no equivalent in migration spec because migration regression already varies t within cell). Without it, residual structure carries year effect into the cluster.

4. ρ_s operationalization confirmed per v1.0 §2.7 Option A: ρ_s(pop) := n_plots_with_G_odoratissima / n_plots_total in sPlotOpen 50 km neighborhood (range 0.008-0.041 across pops; mountain > lowland). Non-degenerate; βₛ retained.

5. ρ_x confirmed per v1.0 §2.7 Option A: ρ_x(pop) := mean Picea abies relative cover in sPlotOpen 50 km neighborhood (range 0.089-0.214; mountain > lowland).

## Amendment to §3.4 cleanness gate

**v1.0 cleanness criterion** (§3.4 last sentence + §2.8): *"response-function R² ≥ 0.30 AND Shapiro-Wilk residual normality p > 0.01"* at the per-(cell, observable) granularity, AND *βₛ sign agreement* with Step-2-implied prediction.

**v1.2 cleanness criterion**, decomposed by inevitability under pooled-plant regression:

- **Global cleanness** per observable j (the regression-level statistic):
  - Pooled R²_j ≥ 0.30 AND
  - Pooled-residual Shapiro p_j > 0.01 AND
  - sign(β_g,j) consistent with Step-2 regime (Gradient-tracking cells should have β_g sign matching the pop's env_PC1 sign).

- **Per-(cell, observable) cleanness** (one row per K=12 × 7 = 84 cells):
  - Within-cell Shapiro p > 0.01 on the pooled regression's residuals restricted to the cell, AND
  - |predicted cell mean − observed cell mean| < 0.5 × cell_sd (the pooled regression's predicted μ for that cell is within half a within-cell SD of the actual μ).

A (cell, observable) is **clean** iff:
  (i) the pooled regression for j is globally clean (R², Shapiro, β-sign),
  AND
  (ii) the per-cell residual diagnostic passes (Shapiro p > 0.01 within cell AND predicted-vs-actual within tolerance),
  AND
  (iii) the Step-2 regime classification for that (Pop, observable) is consistent with the response-function direction (e.g., Concentrating cells should have residual variance shrinking with env_PC1 in the expected direction; Gradient-tracking already requires sign match in Step 2).

For Insufficient_T cells (single-year pops × all observables = 21 cells): the regime-direction check (iii) is replaced with "regime undetermined; cell is clean iff (i) and (ii) pass."

## Falsifier accounting

F1 (substrate doesn't need RMD): unchanged. Threshold ≥ 80% of K=12 × 7 = **84 cells clean at Step 3 without decomposition**.

F2 / F3 / F4: unchanged. v1.2 only affects how cleanness is computed at Step 3; falsifier thresholds remain the v1.0 numbers.

## Other sections unchanged

- §1 locked structural commitments unchanged.
- §2.4 K=12 partition unchanged. ℙ₀_hash unchanged.
- §2.5 v1.1 re-derived rotation unchanged. observable_scores_v11 unchanged.
- §2.6 env_PC1 freeze (locked at Step 2) unchanged. step2_env_PC1.parquet unchanged.
- §2.7 ρ_s / ρ_x Option A confirmed non-degenerate; retained.
- §3.3 Step 2 regimes unchanged. step2_regimes.parquet unchanged.
- §3.7 F4 protocol unchanged.

## Why this is not result-driven

The amendment is triggered by the *predictor variance structure*, not by the regression outcome. Within-cell zero-variance of (∇g, ρ_s, ρ_x) under the K=12 partition is detectable from the partition definition alone — no x_j(plant) statistic enters. The amendment could have been written before Step 0 with full pre-knowledge of §2.4 + §2.6 + §2.7 if the operational consequence had been noticed. It was not noticed at v1.0 lock; v1.2 corrects.

This is the same class of amendment as v1.1 (data-distribution-exposed metric pathology authorized by migration v1.0 §5).

## Audit chain (cumulative)

| Object | Status |
|---|---|
| `P0_partition.parquet`            | v1.0 locked, sha256 = bc7c6f68… |
| `observable_rotation_W_v11.parquet` | v1.1 locked |
| `observable_scores_v11.parquet`     | v1.1 locked |
| `moment_trajectories.parquet`       | v1.1 locked |
| `step2_env_PC1.parquet`             | v1.0 §2.6 frozen at Step 2 |
| `step2_regimes.parquet`             | v1.0 §3.3 locked |
| `step3_*.parquet`                   | v1.2 operative; written next |
