# Pre-Registration v1.1 — Amendment to RMD-SRC *Gymnadenia* v1.0

**Issued:** 2026-06-01.
**Type:** Diagnostic-driven amendment. Triggered by Step 1 moment computation under v1.0 §2.5 d=7 observable choice. NOT result-driven.
**Status:** LOCKED v1.1, 2026-06-01.

## What triggered the amendment

Step 1 under v1.0 §2.5 (d=7 using SelectionAnalysis columns PC1–PC7) produced **μ ≈ 0 for every (cell, observable) pair** across all 12 ℙ₀ cells (output preserved at `results/moment_trajectories.parquet` v1.0, hash in `prereg/step1_log.txt` v1.0).

Diagnostic check (script `06_step1_moments.py` + ad-hoc probe):

- PC1–PC7 and PC1A–PC7A all have **global mean = 0.00000, global sd = 1.0000**.
- **Every population** also has mean PC1 = 0.0 (Albulapass 0.0, Corviglia −0.0, Doettingen 0.0, Linn −0.0, Muenstertal 0.0, Remigen 0.0, Rossweid 0.0, Schatzalp 0.0). Identical for PC2–PC7.
- **Every Region × Year** subset also has mean = 0.0.

This is consistent with the PCs being **residualized of Population (or (Population, Year))** by the Schiestl et al. 2016 phenotypic-selection-gradient pipeline — the paper computes selection gradients within each (population, year), so PCs in the deposited table are the within-(pop, year)-centered scores used for that within-cell regression.

The pre-reg v1.0 §2.5 default ("d=7 using paper-published PCs verbatim") rested on the assumption that these PCs preserve cross-cell μ structure. **They do not.** RMD-SRC Step 2 trajectory classification requires non-degenerate μ_{c,j}(t); the v1.0 observable choice yields μ_{c,j}(t) ≡ 0 by construction.

## Amendment to §2.5

**v1.0 §2.5 (superseded):** d=7 published PCs from SelectionAnalysis.

**v1.1 §2.5 (operative):** d=7, **re-derived PCs on the pooled-cohort z-standardized raw trait matrix**. Procedure:

1. Assemble raw trait matrix from `Data__SelectionAnalysis.xlsx` columns:
   `PlantHeight_cm, InflorescenceLength_cm, NrFlowers` (3 morphology)
   + 22 scent compound concentrations in ng/L (`Z3Hexen1Ol`, `Styrene`, `Heptanal`, `alphaPinene`, `Benzaldehyde`, `Sabinene`, `betaPinene`, `6Methyl5Hepten2One`, `Z3HexenylAcetate`, `HexylAcetate`, `Limonene`, `BenzylAlcohol`, `Phenylacetaldehyde`, `PhenylethylAlcohol`, `BenzylAcetate`, `1Phenyl12Propanedione`, `Phenylethylacetate`, `1Phenyl23Butanedione`, `Eugenol`, `MethylEugenol`, `GeranylAcetone`, `Benzylbenzoate`)
   + `ColourCode` (1 color)
   = **26 raw traits**.
2. Scent compound concentrations are log1p-transformed (right-skewed by construction, paper does the same with LN-versions).
3. Each of the 26 traits z-standardized to **global mean 0, global sd 1** across the full 1028-plant cohort (i.e., NOT within population). This is the key: standardize once on the pool, not per cell.
4. PCA on the 1028 × 26 z-matrix. Retain first **d = 7** PCs (≥ 70% variance per paper's d=7 choice; if cumulative variance differs, log it but keep d=7 for spec consistency).
5. Rotation matrix `W ∈ ℝ^{26 × 7}` is the locked rotation. Frozen after Step 1 rederivation; applied to all 1028 plants as observable vector x_i = W · z_i.
6. Rotation is fit on the FULL 1028-plant cohort, NOT on the 2010 training window only. Honest divergence from migration §2.5 (which fit PCA on a pre-window baseline). Rationale: orchid substrate has no pre-window data; fitting rotation on training year only (n=565) loses ~half the cohort variance information needed to stabilize the basis. F4 holdout test still uses 2011 plants applied to the rotation trained on the full cohort — the falsifier tests trajectory regime stability, not rotation stability.

ColourCode contains "NA" string values in 88/1028 rows. Per data-imputation policy: NA in `ColourCode` is dropped from the rotation fit; plants with NA are projected using all 25 non-NA traits scaled to the 7-PC space via least-squares projection of the available coordinates (standard PCA-imputation). Logged.

## Amendment to §3.2 (Step 1 freeze)

**v1.0 §3.2 unchanged in form.** Re-execute Step 1 under v1.1 §2.5 observable definition. Output file `results/moment_trajectories.parquet` is overwritten; the v1.0 output is preserved as `results/moment_trajectories_v10_DEGENERATE.parquet` for audit; both hashes recorded in `prereg/step1_log.txt` (appended).

## Other sections unchanged

All other §1, §2, §3, §4 commitments stand as written in v1.0. Specifically:
- ℙ₀ partition (K=12, hash in `prereg/P0_hash.txt`) is unchanged. The partition is over plants; the observable rotation is a separate map.
- §2.6 ∇g (env-PC1 of 10 env covariates) unchanged.
- §2.7 ρ_s / ρ_x Option A unchanged.
- §3.3 T=2 regime rules unchanged.
- §3.7 F4 protocol unchanged.
- §1 locked structural commitments unchanged.

## Audit chain

| Object | v1.0 hash | v1.1 status |
|---|---|---|
| P0_partition.parquet | bc7c6f682d3300a75a60ce8e7060ee7e2c4862814a037e13fb8003b062de5473 | unchanged |
| moment_trajectories.parquet (v1.0) | preserved as `..._v10_DEGENERATE.parquet`; new hash recorded post-rederivation | superseded |
| W rotation matrix (v1.1) | written to `derived/observable_rotation_W_v11.parquet`; hash recorded | new |

## Why this is not result-driven

A result-driven amendment would say "the trajectory classifications under v1.0 didn't show what we wanted, so we change the observables." That is not the case here. The amendment is triggered by a structural property of the observable definition — the published PCs are mean-zero in every cell *by construction* — which is detectable before any regime or response-function statistic. The diagnostic could have been caught in §2.5 pre-lock by inspecting the column distributions; it was not. This amendment corrects the missed pre-lock check.

The migration v1.0 amendment policy explicitly authorizes this category: "data-distribution-exposed metric pathologies are [honest amendments]."
