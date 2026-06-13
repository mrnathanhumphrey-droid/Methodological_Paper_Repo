# Pre-Registration v2.0 — RMD-SRC Applied to *Gymnadenia odoratissima* (re-partitioned)

**Type:** **NEW pre-registration**, not an amendment. v2.0 changes the structural partition (§2.4) from v1.0's (Region × Pop × Year) → (Region × Pop), turning Year into the t-bin axis per spec §1.1 instead of an in-ℙ₀ stratum. This is the structural translation v1.0 results doc flagged as the natural F2-mode-attribution test: *did the v1 partition choice drive F2 or did the framework genuinely fail on this substrate?*

**Substrate:** Same as v1 (Schiestl et al. 2016, Dryad dj40r, 1028 plants × 8 Swiss pops × 2010–2011). All raw data and env overlays unchanged.

**Framework:** RMD-SRC, Humphrey working draft May 2026 (Paper 6 snapshot).

**Authored:** 2026-06-01.
**Status:** LOCKED v2.0-final, 2026-06-01. Eight `[CONFIRM]` items defaulted as v1.0 + amendments inherited operative form, with the §2.4 partition change as the sole structural delta.

---

## 1. Locked structural commitments (unchanged from v1.0)

Verbatim inheritance of v1.0 §1.1–§1.6. Five-regime taxonomy; response-function form; 4a→4b→4c decomp order; F1/F2/F3/F4 thresholds.

## 2. Substrate operationalizations

### 2.1 Data source — inherited
Schiestl et al. 2016 / Dryad dj40r. Phenotype = `Data__SelectionAnalysis.xlsx`. Env overlays in `derived/gymnadenia_pop_env_v2.csv`.

### 2.2 Sampling unit — inherited
Plant (single-shot per plant, no within-plant repeated measures). ∇g reinterpreted as env-at-site for sessile substrate (carry-over from v1.0 §2.2).

### 2.3 Time period — inherited (T = 2, 2010 + 2011)
Default T = 2 retained. T = 4 (FloralTrait 2010–2013) remains a v2.1 / v3 option, not used in v2.0.

### 2.4 Structural partition ℙ₀ — **CHANGED**

**v1.0 §2.4 (superseded):** Region × Population × Year, K=12.

**v2.0 §2.4 (operative):** **Region × Population, K=8.** Year is removed from ℙ₀ and becomes the t-bin axis per spec §1.1.

Pop-level n across years (no Year stratification): D=165, R=144, L=184, RW=72, S=122, M=190, A=69, C=82. All ≥ 50. **No collapses required.** K=8 cells, all single-population, time-invariant cell identity.

Of 8 cells: **5 span both years** (D, R, L, M, S) — these have within-cell Year trajectories. **3 are single-year** (RW=2011-only, A=2010-only, C=2011-only) — these have no within-cell year trajectory; spec Step-2 regime is `Insufficient_T` per v1.0 §3.7 fallback rules (carried over).

### 2.5 Observables x ∈ ℝ⁷ — inherited v1.1
d = 7 re-derived PCs on pooled cohort z-standardized 26-trait raw matrix (3 morphology + 22 scent log1p + 1 ColourCode). Rotation matrix `observable_rotation_W_v11.parquet` reused — **rotation hash unchanged.** Plant scores `observable_scores_v11.parquet` reused.

### 2.6 Gradient field ∇g — inherited
env_PC1 frozen from `step2_env_PC1.parquet` (69.8 % variance, sign-corrected high = mountain). Reused verbatim.

### 2.7 ρ_s / ρ_x — inherited v1.3
Option B operative: drop ρ_s and ρ_x per v1.3 (VIF blow-up + sign flip). Response function:
$$x_j(\text{plant}_i) = \alpha + \beta_{g,j} \cdot \mathrm{env\_PC1}(\mathrm{pop}_i) + \beta_{y,j} \cdot \mathbb{1}[\mathrm{year}_i = 2011] + \varepsilon_i$$

### 2.8 Cell-size and cleanness thresholds — inherited
MIN_CELL_N = 50, R² ≥ 0.30, Shapiro p > 0.01, |μ̂_cell − μ_cell| < 0.5 · sd_cell.

## 3. Pre-registered analysis plan

### 3.1 Step 0 freeze
Recompute ℙ₀ assignment per plant using v2.0 §2.4. Save `derived/P0_partition_v20.parquet`. Hash to `prereg/P0_hash_v20.txt`.

### 3.2 Step 1
Moments μ_{c,j}(t), σ²_{c,j}(t) per (cell c ∈ K=8, observable j ∈ 7, year t ∈ {2010, 2011}). For cells with only one year, only that year's moment is populated; the other is NA. Save `results/moment_trajectories_v20.parquet`. Total max 8 × 7 × 2 = 112 (cell, obs, year) rows; expected 5×7×2 + 3×7×1 = 91 populated.

### 3.3 Step 2 regime classification — **NOW PROPERLY DEFINED**
For each (cell c, observable j) with both years populated: apply v1.0 §3.3 T=2 Δ-based rules.
For cells with single year: regime = `Insufficient_T`.
Single-year pops contribute 21 such cells (3 pops × 7 observables).

### 3.4 Step 3 response function — inherited v1.3 form
Pooled-plant regression per observable d=7. Cluster-robust SE at Pop. Cleanness gates per v1.2 (global Shapiro/R² + per-cell pred-error/Shapiro).

### 3.5 Step 4 — **4b NOW ALIVE**
- **4a (categorical):** No pre-outcome categorical structure available (Region, Pop in cell ID). Logged as `no_valid_split` per all cells, proceed to 4b.
- **4b (time-phase):** **For the 5 multi-year cells**, attempt Year split → 2 subcells (year=2010 plants vs year=2011 plants). Each subcell evaluated for cleanness. Subcells with n < 50 (e.g. Schatzalp 2010 with n=47) → resolution termination on that child.
- **4c (mixture):** GMM k=1..3 on remaining not-clean leaves.

### 3.6 Step 6 mechanism inference — inherited

### 3.7 F4 holdout — inherited v1.0 §3.7 T=2 fallback (between-pop κ within region)

### 3.8 Hypotheses about v2.0 outcome vs v1.0

This pre-reg makes one structural prediction worth recording before execution:

**H_v2:** If F2 in v1 was driven by partition choice (Year inside ℙ₀ killing 4b), v2.0 will recover cells via 4b time-phase splits and reduce post-decomp cleanness gap. If F2 still fires at < 50 % in v2.0, the framework failure is substrate-structural, not partition-driven.

Both outcomes are reported regardless of direction.

---

## 4. Reporting commitments

Same as v1.0 §4. Result doc → `notes/RESULTS_RMD_SRC_gymnadenia_v2.md`. Outcome updates the RMD-SRC substrate ledger as a second-run-on-same-substrate entry.

---

## 5. Audit chain inheritance

| Object | v2.0 status |
|---|---|
| `observable_rotation_W_v11.parquet` | inherited unchanged |
| `observable_scores_v11.parquet`      | inherited unchanged |
| `step2_env_PC1.parquet`              | inherited unchanged |
| `P0_partition.parquet` (v1.0)        | preserved; not touched |
| `P0_partition_v20.parquet`           | NEW, v2.0 lock |
| all other v1 outputs                 | preserved |
