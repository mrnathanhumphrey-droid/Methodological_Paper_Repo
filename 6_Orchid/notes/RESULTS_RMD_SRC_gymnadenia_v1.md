# Results — RMD-SRC Applied to *Gymnadenia odoratissima* Floral Phenotype Across an Alpine Environmental Gradient

**Pre-registration:** `prereg/PRE_REG_v1.0_RMD_SRC_gymnadenia.md` + amendments v1.1 / v1.2 / v1.3.
**Substrate:** *Gymnadenia odoratissima* (Orchidaceae), 8 Swiss populations (lowland 4 + mountain 4), 1028 plants, 2010–2011, Schiestl et al. 2016 *PLOS ONE* 11:e0147975 (Dryad doi:10.5061/dryad.dj40r).
**Framework:** RMD-SRC, Humphrey working draft May 2026 (Paper 6 methodology snapshot, locked 2026-05-12).
**Execution date:** 2026-06-01.
**Status:** First biological-substrate entry in the RMD-SRC ledger.

---

## Headline outcome

**Two falsifiers fired. Substrate is a documented framework-failure on a named biological target.**

| Falsifier | Statistic | Threshold | Result |
|---|---|---|:---:|
| F1 (substrate doesn't need RMD) | 6.0 % cells clean pre-decomp | ≥ 80 % | **silent** |
| F2 (decomposition-resistant)    | 6.0 % cells clean post-decomp | < 50 % | **FIRES** |
| F3 (trajectory vs response mismatch) | 4.8 % of 84 leaves disagree | ≥ 30 % | silent |
| F4 (cross-population κ instability)  | 0.216 average within-region κ | < 0.40 | **FIRES** |

Per pre-reg §4: *"F2 or F3 fires → report as documented framework failure on a named substrate."* F2 + F4 firing is the published outcome of this run. Substrate is the first biological-substrate entry in the RMD-SRC ledger; outcome updates the substrate ledger and the methodology corpus tally per §4.

The result is **not** "the substrate has no signal." Significant per-population phenotype variation and a sharp lowland-mountain axis exist (see §x2 below). The result is that this particular substrate × locked-spec × K=12 partition combination cannot be decomposed by the spec's 4a→4b→4c machinery and cannot produce regime labels that generalize across populations.

---

## What was built and run

| Step | Artifact | What it is |
|---|---|---|
| Step 0 | `data/orchids/gymnadenia/derived/P0_partition.parquet` (sha bc7c6f68…) | K=12 cells, 1 collapse (Schatzalp 2010 → Muenstertal 2010), n range 56–143 |
| Step 1 v1.1 | `data/orchids/gymnadenia/derived/observable_rotation_W_v11.parquet` + `observable_scores_v11.parquet` + `results/moment_trajectories.parquet` | d=7 PCs re-derived on pooled cohort z-standardized raw trait matrix (26 traits = 3 morphology + 22 scent log1p + 1 colour), 80.4 % cum variance |
| Step 2 | `results/step2_env_PC1.parquet` + `results/step2_regimes.parquet` | env_PC1 (69.8 % var); 56 cell-observable regime classifications |
| Step 3 v1.3 | `results/step3_response_function.parquet` + `results/step3_cell_cleanness.parquet` | Option B response function (env_PC1 + y2011), 7 pooled regressions, 5/84 cells clean |
| Step 4 | `results/decomposition_logs/decomp_tree.parquet` + `results/step4_leaves.parquet` + `results/step4_falsifier_report.parquet` | 237 decomp attempts (3 strategies × 79 not-clean cells); 0 recoveries; F2 fires |
| Step 5 / §3.7 | `results/step5_F4_holdout.parquet` + `results/step5_F4_pairs.parquet` | 4 within-region pop pairs; avg κ = 0.216; F4 fires |

---

## Per-step record

### Step 0 — ℙ₀ freeze

Partition: Region × Population × Year. Of 16 possible cells, 13 non-empty (RW-2010, A-2011, C-2010 absent per S1 Table coverage). One collapse: Schatzalp 2010 (n=47, below n<50 threshold) merged into Muenstertal 2010 (within-region same-year nearest-elevation, Δalt = 0 m). Final K=12 cells, n range 56–143, all ≥ 50.

### Step 1 v1.1 — observable rotation re-derived

The v1.0 spec called for d=7 using `PC1`–`PC7` columns from `Data__SelectionAnalysis.xlsx`. Step 1 v1.0 produced **μ ≈ 0 for every (cell, observable)** because those PCs are within-(Pop, Year)-centered (Schiestl et al.'s phenotypic-selection-gradient pipeline). Diagnostic-driven amendment v1.1: re-derive rotation on the pooled cohort z-standardized 26-trait raw matrix; d=7, 80.4 % cumulative variance explained.

ColourCode NA on 465/1028 plants (paper measured colour from 2011); imputed via partial projection. All 1028 plants scored on x1–x7.

### Step 2 — trajectory regime classification

env_PC1 frozen per §2.6: PCA on 8-pop × 10-covariate env matrix, sign so high PC1 = mountain. Loadings on elevation, low BIO1 (mean annual T), low BIO6 (Tmin). 69.8 % variance explained. Rossweid 0–5cm soil cells column-mean imputed (3/8 missing).

Trajectory rules per §3.3 T=2 adapted (Δ-based replacement for OLS slopes). 56 (Pop, observable) classifications:

| Region | C | D | F | G | S | Insuff_T |
|---|---:|---:|---:|---:|---:|---:|
| lowland (D,L,R,RW) | **11** | 4 | 6 | 0 | 0 | 7 |
| mountain (S,M,A,C) | 1 | **9** | 2 | 2 | 0 | 14 |

**Asymmetric region pattern is the substrate-honest finding** (lowland concentrates, mountain diffuses). Zero Stationary cells; only 2 Gradient-tracking (both Muenstertal x6 + x7). 21 Insufficient_T cells from 3 single-year pops (RW 7 + A 7 + C 7).

### Step 3 — response function

v1.0 §3.4 specified "fit response function per (cell, observable) with OLS, robust SE clustered at origin-PUMA." Under K=12 orchid partition, ∇g = env_PC1 is constant within (Pop, Year) cells; per-cell β_g is unidentifiable. Diagnostic-driven amendment **v1.2**: pooled-plant regression per observable (d=7 fits), cluster-robust SE at Pop level, year dummy added.

Diagnostic at Step 3 inspection revealed **VIF blow-up**: env_PC1 = 27.0, ρ_x = 27.9, ρ_s = 6.5; pop-level correlations env_PC1 × ρ_x = 0.975. β_g sign flipped for x2 between full model and Option B. Diagnostic-driven amendment **v1.3** pre-authorized by v1.0 §2.7 (VIF > 5 trigger): switch §2.7 from Option A to Option B (drop ρ_s, ρ_x). Cleanness result preserved at 5/84 (6.0 %) under Option B, but with biologically-correct β_g sign for x2.

### Step 4 — decomposition

237 decomp attempts across 79 not-clean cells, strictly ordered 4a → 4b → 4c per §1.4:

- **4a (categorical):** Only one cell (M_Muen_2010) had within-cell pop variation (Schatzalp + Muenstertal collapse). Split rejected: Schatzalp child n=47 < min_cell_size=50 → resolution termination on that subcell; Muenstertal child n=96 did not become clean. All other cells logged `no_valid_categorical_split` because (Region, Pop, Year) is fully exhausted by the cell ID — orchid K=12 partition has no pre-outcome categorical structure left to split on.
- **4b (time-phase):** Every cell is single-year by construction. No within-cell t-bins. All 79 cells logged `single_year_cell`. Inapplicable across the substrate.
- **4c (mixture):** Gaussian Mixture k=1..3 by BIC on each (cell, observable) plant score vector. 0 of 79 cells improved cleanness via a k>1 split.

**0 cells recovered. F2 fires at 6.0 % < 50 %.**

### Step 5 / §3.7 — F4 holdout

Under v1.0 §3.7 T=2 fallback ("between-population regime stability at the leaf level"): pairwise Cohen's κ on 7-observable regime vectors within region, across the 5 trajectory-classifiable pops (D, L, R, M, S):

| pair | region | κ | raw agreement |
|---|---|---:|---:|
| Doettingen–Linn      | lowland  | **0.696** | 86 % |
| Doettingen–Remigen   | lowland  | 0.054 | 29 % |
| Linn–Remigen         | lowland  | 0.079 | 29 % |
| Muenstertal–Schatzalp | mountain | 0.034 | 43 % |

Average κ = 0.216, 95% threshold 0.40. **F4 fires.** Remigen's regime pattern diverges sharply from Doettingen/Linn despite similar climate and ecoregion. Mountain pair (M, S) also shows near-random agreement. Regime labels are population-specific, not region-specific.

---

## Diagnostic narrative — three amendments, all pre-result

The pre-reg locked v1.0 with 8 `[CONFIRM]` items defaulted as drafted. Three diagnostic-driven amendments followed during execution; **all three triggered before any cleanness statistic was computed against falsifier thresholds**. None was result-driven:

**v1.1 (Step 1, observable choice).** Trigger: μ ≈ 0 for every (cell, observable) under v1.0 §2.5 d=7 published PCs. Diagnostic: PCs are within-(Pop, Year)-centered by Schiestl et al.'s phenotypic-selection-gradient pipeline. Remedy: re-derive rotation on pooled z-standardized raw trait matrix.

**v1.2 (Step 3, regression granularity).** Trigger: predictors (env_PC1, ρ_s, ρ_x) constant within K=12 cells ⇒ per-cell β_g unidentifiable. Remedy: pooled-plant regression per observable; cluster-robust SE at Pop; year dummy added; cleanness gates decomposed into global + per-cell.

**v1.3 (Step 3, predictor multicollinearity).** Trigger: VIF blow-up (env_PC1 = 27, ρ_x = 28, ρ_s = 6.5) and β_g sign flip in x2. v1.0 §2.7 pre-authorized this contingency. Remedy: drop ρ_s, ρ_x.

The amendment cascade is itself a finding: **the locked spec's transfer from migration substrate to sessile-biological substrate required three structural adjustments before falsifier accounting could be done.** The spec generalizes formally but not operationally without these structural translations.

---

## Substrate-honest biological findings

Independent of the framework's falsifier outcome, the run produced real biology:

1. **x2 is the cross-region phenotype axis** (R² = 0.45 under v1.2, 0.30 under v1.3 Option B). x2 positively loads PlantHeight + NrFlowers + Eugenol + BenzylAcetate + Phenylacetaldehyde + ColourCode; negatively loads β-pinene + Limonene + α-pinene. Mountain orchids are smaller, fewer-flowered, monoterpene-dominant; lowland orchids are taller, benzoid-dominant, more colour-vivid. Matches published *Gymnadenia odoratissima* pollination-ecology literature.

2. **Lowland concentrates, mountain diffuses.** Step 2 regime distribution shows 11/21 lowland trajectory-cells Concentrating vs 9/14 mountain Diffusing. Asymmetric variance dynamics consistent with stronger between-year selection in lowland; higher environmental stochasticity or weaker selection in mountain.

3. **Large 2011 > 2010 year effect** on all 7 observables across all 5 trajectory pops. Cohort-wide upward year shift not separable from sampling protocol effects at this T.

4. **Density predictors (ρ_s, ρ_x) are not independent of env_PC1**. At the orchid 8-pop scale, the sPlotOpen-derived community covariates carry essentially the same lowland-mountain signal as the climate-soil-elevation PC1. The v1.0 §2.7 Option A model is misspecified for sessile organisms at this geographic scale; Option B is the substrate-honest model.

5. **Remigen's regime pattern is the within-region outlier** that drove F4. Remigen 7-observable regime classification looks like a mountain pop (Concentrating in x1, Diffusing in x4-x7), not a lowland pop. Possible biological mechanisms: site is intermediate-elevation (600 m, second-highest lowland), shadier substrate, or unmeasured local selection regime. Worth a follow-up note in any future Gymnadenia substrate work; not pursued here.

---

## Failure-mode classification (per L2 corpus retro)

The L2 update to METHODOLOGY_NOTES.md (2026-05-11) defines four NULL-disposition modes:

- **Mode A** (operationalization mismatch): substrate has per-unit signal; spec tests wrong relationship.
- **Mode B** (substrate-uniform redundancy): per-unit dominates spec dimensions.
- **Mode C** (non-additive interaction): substrate × operator-class mismatch.
- **Mode D** (clean substrate boundary): no per-unit signal anywhere.

This run's F2 + F4 firing combination matches **Mode A with Mode-B contamination**:

- The substrate has clear per-population signal (x2 region split, regime asymmetry, real β_g on env_PC1) — not Mode D.
- The spec's 4a/4b/4c decomposition machinery is structurally inapplicable under the K=12 partition the spec's ℙ₀ defaulted to: (Region, Pop, Year) eats all pre-outcome categorical structure. **The partition choice exhausted the decomposition substrate.** A different partition (e.g., Region × Pop with Year handled as a t-bin axis spanning multi-year cells) would have left 4b alive and could plausibly have lifted F2.
- F4 firing on average κ = 0.216 says regime labels are pop-specific, not region-specific. That's a per-pop signal swamping the regime classification system — Mode B's "specs hit all units the same way" inverted: regimes don't generalize across units within a category.

**Substrate boundary:** *Gymnadenia odoratissima* at T=2, K=12 partition is decomposition-resistant under the locked spec. A re-pre-registration with a different partition (ℙ₀ = Region × Pop, K=8) and/or T = 4 (extended via FloralTraitDifferences 2010–2013) could revisit. Filed as v2 candidate, not pursued in v1.

---

## Update to RMD-SRC substrate ledger

| Substrate | Outcome | Mode |
|---|---|---|
| Collatz, NBA, DNC, SP500, FkCancer, hydrology, MOFA-FLEX, migration | (prior corpus, see methodology snapshot) | see L2 retro |
| **Gymnadenia (this run)** | **F2 + F4 fire; documented framework failure on first biological substrate** | **Mode A + B (partition exhausted decomp substrate; regime non-generalization across pops)** |

Net of this run: the cross-substrate universality claim for RMD-SRC does **not** extend to the locked T=2 K=12 *Gymnadenia* configuration. A T=4 / K=8 re-pre-registration is an open question, not a resolved one. Methodology snapshot is unchanged; this entry sits in the substrate ledger as a published null on a pre-named target with a fully audited amendment trail.

---

## Files

```
prereg/
  PRE_REG_v1.0_RMD_SRC_gymnadenia.md   (locked)
  PRE_REG_v1.1_amendment.md            (locked)
  PRE_REG_v1.2_amendment.md            (locked)
  PRE_REG_v1.3_amendment.md            (locked)
  P0_hash.txt
  step1_log.txt   step2_log.txt   step3_log.txt
  step4_log.txt   step5_log.txt
data/orchids/gymnadenia/derived/
  P0_partition.parquet
  observable_rotation_W_v11.parquet
  observable_scores_v11.parquet
results/
  moment_trajectories.parquet
  moment_trajectories_v10_DEGENERATE.parquet     (v1.0 audit)
  step2_env_PC1.parquet
  step2_regimes.parquet
  step3_response_function.parquet         (v1.3 operative)
  step3_response_function_v12.parquet     (v1.2 audit)
  step3_cell_cleanness.parquet            (v1.3 operative)
  step3_cell_cleanness_v12.parquet        (v1.2 audit)
  decomposition_logs/decomp_tree.parquet
  step4_leaves.parquet
  step4_falsifier_report.parquet
  step5_F4_holdout.parquet
  step5_F4_pairs.parquet
scripts/orchids/
  01_overlay_gymnadenia_env.py            (substrate build, v1)
  02_overlay_gymnadenia_env_v2.py         (substrate build, v2)
  03_join_per_plant.py
  04_splotopen_neighborhood.py
  05_step0_P0_freeze.py
  06_step1_moments.py                     (v1.0; produced degenerate output)
  06b_step1_moments_v11.py                (v1.1; primary)
  07_step2_regimes.py
  08_step3_response_function.py           (v1.2)
  08b_step3_response_function_v13.py      (v1.3; primary)
  09_inspect_step3.py                     (diagnostic, query-only)
  10_step4_decomposition.py
  11_step5_F4_holdout.py
notes/
  ORCHID_SUBSTRATE_v1.md
  RESULTS_RMD_SRC_gymnadenia_v1.md        (this file)
```

All amendment artifacts preserved with audit hashes. P0 hash unchanged across all amendments — partition was never re-locked.
