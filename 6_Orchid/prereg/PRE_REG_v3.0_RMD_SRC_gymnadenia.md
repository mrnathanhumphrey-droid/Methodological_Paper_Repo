# Pre-Registration v3.0 — RMD-SRC Applied to *Gymnadenia odoratissima* (robust-regression operator class)

**Type:** NEW pre-registration. Sequel to v1.0, v2.0, and the post-hoc B within-region exploratory + within-cell-noise diagnostic. v3.0 changes §3.4 response-function fit from OLS to **Huber robust regression** and changes the residual-normality cleanness gate from Shapiro–Wilk to **Anderson–Darling**. Locked operator-class change targets the diagnosed binding constraint (heavy-tailed residuals + year-cohort spread), per the within-cell-noise analysis surfaced at `scripts/orchids/15_within_cell_noise.py`.

**Substrate:** Same as v1 / v2. Schiestl et al. 2016, Dryad dj40r, 1028 plants × 8 Swiss pops × 2010–2011.
**Framework:** RMD-SRC, Humphrey working draft May 2026.
**Authored:** 2026-06-01.
**Status:** **LOCKED v3.0-final, 2026-06-01.** All §2 / §3 confirmations locked as drafted.

**Supersedes:** the earlier v3.0 draft from this date that proposed quadratic + env × year interaction (candidate A). That draft was shelved after within-cell-noise diagnostic showed the residual non-normality is not interaction-form but heavy-tail / year-cohort / single-chemotype-morph (Corviglia 2011 monoterpene). v3.0 lock = Huber (B), not quadratic (A).

---

## 1. Locked structural commitments (inherited from v1.0)

§1.1–§1.6 verbatim from v1.0 spec. Five-regime taxonomy, response-function form (now under robust fit), 4a → 4b → 4c order, F1/F2/F3/F4 thresholds.

## 2. Substrate operationalizations

### 2.1 Data source — inherited
Schiestl 2016 / Dryad dj40r, `Data__SelectionAnalysis.xlsx`.

### 2.2 Sampling unit — inherited
Plant. Sessile interpretation of ∇g.

### 2.3 T window — inherited from v2.0
T = 2 (2010 / 2011). T = 4 extension out of scope.

### 2.4 ℙ₀ partition — inherited from v2.0
Region × Pop, K = 8. Hash `P0_hash_v20.txt` reused.

### 2.5 Observables — inherited v1.1
d = 7, `observable_scores_v11.parquet`.

### 2.6 ∇g — inherited
env_PC1 frozen from `step2_env_PC1.parquet`.

### 2.7 ρ_s / ρ_x — inherited v1.3
Dropped. Response function has only env_PC1 + y2011.

### 2.8 Response function — **CHANGED**

v2.0 §3.4 (superseded): OLS, x_j ~ env_PC1 + y2011, cluster-robust SE at Pop.

**v3.0 §3.4 (operative):** **Huber-loss robust regression**, same equation form:
$$x_j(\text{plant}_i) = \alpha + \beta_g \cdot \mathrm{env\_PC1}(\mathrm{pop}_i) + \beta_y \cdot \mathbb{1}[\mathrm{year}_i = 2011] + \varepsilon_i$$

Fit via `statsmodels.RLM(y, X, M=HuberT()).fit()`. Default Huber-T tuning constant 1.345 (covers 95% of normal data at full efficiency, downweights past).

Standard errors are heteroskedasticity-consistent from the IRLS fit (H1-type). Cluster-robust SE at Pop is **not** carried over because Huber RLM does not natively support it; this is a logged honest divergence. Falsifier F3 uses β_g_p from H1 SE.

### 2.9 Cleanness gates — **CHANGED**

v1.2 / v1.3 gates (superseded for residual-normality clause): Shapiro-Wilk p > 0.01.

**v3.0 cleanness criteria:**

**Global per observable j:**
- Pseudo-R²_j ≥ 0.30, where pseudo-R² = 1 − Σ(y − ŷ)² / Σ(y − ȳ)² computed on the Huber fit.
- **Anderson–Darling test** on pooled residuals: AD statistic < critical value at 1% significance (i.e., p > 0.01). Anderson–Darling is more robust to heavy tails than Shapiro and is the standard normality test in the corpus discipline note when Shapiro is over-rejecting.
- β_g sign consistency unchanged.

**Per (cell, observable):**
- Within-cell Anderson–Darling on residuals: AD p > 0.01 (or AD statistic below the cell's n-adjusted 1% critical value).
- |μ̂_cell − μ_cell| < 0.5 · sd_cell (unchanged).
- Regime-consistency (iii) unchanged.

A cell is **clean** iff global Anderson–Darling passes, pseudo-R² ≥ 0.30, β_g sign consistent, within-cell AD passes, pred-error passes, regime check passes. Same conjunction structure as v1.2 / v1.3 — only the normality test changes.

For small cells where AD requires n ≥ 8 sample size: cells with 50 ≤ n < 8 (not possible at MIN_CELL_N = 50) — trivially satisfied; AD computable for all v3 cells.

---

## 3. Pre-registered analysis plan

### 3.1–3.3 — inherited unchanged
P0 hash, moment trajectories, regimes all reused from v2.0 outputs.

### 3.4 Step 3 — Huber fit per observable
1028 plants × 7 observables = 7 RLM fits. H1 robust SE.

### 3.5 Step 4 decomposition — **inherited from v2.0**
4a logged as `no_valid_categorical_split` per cell, 4b alive on multi-year cells (split by Year), 4c GMM k=1..3 BIC. All subcells re-evaluated against v3.0 cleanness gates.

### 3.6 Step 5 / §3.7 F4 — inherited
Same between-pop κ within region; F4 result is invariant to response-function form. Will be re-emitted from v2's regime classifications for completeness.

### 3.7 Pre-committed hypotheses for the v3-B dig

**H1 — Anderson–Darling improvement:** ≥ 4 of 7 observables pass AD at p > 0.01 globally (vs OLS-Shapiro v2.0 having only 1 observable, x2, pass).

**H2 — F2 mitigation:** post-decomp cleanness rises above v2.0's 5.4 %. If F2 silences (≥ 50 % clean), substrate is decomposable under robust-regression operator class.

**H3 — Corviglia chemotype isolation:** Corviglia 2011 cells fail cleanness on monoterpene-related observables (x1 + x4 + x5 by rotation loading), identifying the one real chemotype morph found in the within-cell-noise analysis. **If H3 confirms while H1+H2 also confirm**, that's the publishable result: substrate decomposes via robust regression *except* for one identified local chemotype.

All three hypotheses tested per published numbers. Outcomes reported regardless of direction.

### 3.8 What is NOT pre-registered
- v3.1 mixture-of-regressions (latent class) — pre-named follow-up if H1+H2 fail.
- v3.2 quantile regression — pre-named alt to Huber if both fail.
- T = 4 FloralTrait extension — orthogonal.

---

## 4. Reporting commitments

Same as v1.0 §4. Results doc → `notes/RESULTS_RMD_SRC_gymnadenia_v3.md`.

If H1+H2 confirm AND H3 confirms: substrate decomposes via Huber operator class with one isolated chemotype as the published-named residual finding. Cross-substrate universality claim updated positively for biological substrates with robust regression as the operator class.

If H1+H2 fail: residual non-normality is not heavy-tail-fixable; mixture-of-regressions (v3.1) becomes the next test.

If H1 confirms but H2 still fires F2: AD normality test is the right diagnostic but residuals still fail per-cell cleanness for non-normality reasons (likely the Corviglia chemotype manifesting more broadly than H3 expects). v3.1 narrows.

---

## 5. Lock decisions

All locked at draft values:

| # | Item | Locked |
|---|---|---|
| 2.3 | T window | T = 2 (inherited) |
| 2.4 | Partition | K = 8 from v2.0 |
| 2.5 | Observables | d = 7 from v1.1 |
| 2.6 | ∇g | env_PC1 from step2 |
| 2.7 | Densities | dropped (v1.3 Option B) |
| 2.8 | Response function | **Huber-T RLM** |
| 2.9 | Normality gate | **Anderson–Darling p > 0.01** |
| 3.4 | SE type | H1 heteroskedasticity-consistent (Huber default), NOT cluster-robust |

Amendment policy: data-distribution-exposed only.

---

## 6. Audit chain

| Object | v3.0 status |
|---|---|
| `P0_partition_v20.parquet`              | inherited unchanged |
| `observable_scores_v11.parquet`            | inherited unchanged |
| `step2_env_PC1.parquet`                    | inherited unchanged |
| `step2_regimes_v20.parquet`                | inherited unchanged |
| `moment_trajectories_v20.parquet`          | inherited unchanged |
| `step3_response_function_v30.parquet`      | **NEW** |
| `step3_cell_cleanness_v30.parquet`         | **NEW** |
| `step4_leaves_v30.parquet`                 | **NEW** |
| `step_falsifier_report_v30.parquet`        | **NEW** |
