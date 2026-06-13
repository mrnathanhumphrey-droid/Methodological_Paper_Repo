# Pre-Registration v3.1 — Amendment to RMD-SRC *Gymnadenia* v3.0

**Issued:** 2026-06-01.
**Type:** Diagnostic-driven amendment + pre-named follow-up. v3.0 §3.8 pre-named v3.1 as "mixture-of-regressions just for Corviglia (k=2 latent class)" contingent on H3 confirming. H3 confirmed strongly (Corviglia 0/7 clean under v3.0). v3.1 operationalizes the v3.0-promised follow-up.
**Status:** LOCKED v3.1, 2026-06-01.

## Trigger

v3.0 §3.7 H3: "Corviglia 2011 cells fail cleanness on monoterpene-related observables (x1, x4, x5)" — confirmed at **3/3** mono-obs failing AND **7/7 ALL Corviglia observables failing** (Corviglia is the only pop with 0 clean cells across v3.0). The within-cell-noise analysis (`scripts/orchids/15_within_cell_noise.py`) identified a 23-plant monoterpene-rich minority within Corviglia 2011 via joint 7-D GMM (k=2 selected by BIC, ΔBIC = −57.5 vs k=1).

## Amendment to §3.4

**v3.0 §3.4 (operative):** Huber RLM, x_j ~ env_PC1 + y2011, no per-pop interaction.

**v3.1 §3.4 (operative for Corviglia, additive correction elsewhere):**

$$x_j(\text{plant}_i) = \alpha + \beta_g \cdot \mathrm{env\_PC1}(\mathrm{pop}_i) + \beta_y \cdot \mathbb{1}[\mathrm{year}_i=2011] + \beta_{m} \cdot \mathbb{1}[\mathrm{Corv\_monomorph}_i] + \varepsilon_i$$

Where `Corv_monomorph_i = 1` if and only if plant i ∈ Corviglia AND plant i is assigned to the high-monoterpene GMM cluster from `results/within_cell/M_Corv_gmm_labels.parquet` (cluster 1; n=23 plants). Else 0.

All non-Corviglia plants get `Corv_monomorph = 0`. Corviglia plants in the low-monoterpene cluster (cluster 0; n=59) also get 0.

This is a **single binary dummy added to the v3.0 model**, anchored on the pre-existing GMM clustering. No new clustering done at v3.1 — the cluster assignment is locked from the within-cell-noise analysis hash chain.

## Pre-committed hypotheses

**H_v3.1A:** β_m is significant at p < 0.01 for at least 3 of 7 observables (especially the monoterpene-loading ones: x1, x4, x5).

**H_v3.1B:** Corviglia cleanness rises from 0/7 to ≥ 4/7.

**H_v3.1C:** Substrate-wide post-decomp cleanness rises above v3.0's 16.1 %.

## Operational

Re-fit Huber RLM per observable with the 4-predictor model. Re-evaluate cleanness gates per v3.0 §2.9 (Anderson–Darling p > 0.01, pseudo-R² ≥ 0.30, β_g sign, per-cell AD, pred-err).

If H_v3.1A confirms: chemotype identification is real, the v3.0 H3 reading is biologically substantiated.

If H_v3.1A confirms but H_v3.1B fails: Corviglia has structural residual variance even after monomorph adjustment; v3.2 (quantile) becomes the next test.

If H_v3.1A fails: chemotype morph is not the right covariate; the within-cell GMM finding is a 1-D-cluster artifact not a structural latent class.

## Audit chain

| Object | v3.1 status |
|---|---|
| `M_Corv_gmm_labels.parquet` | locked from within-cell noise analysis (no re-cluster) |
| `step3_response_function_v31.parquet` | NEW |
| `step3_cell_cleanness_v31.parquet` | NEW |
| `step4_leaves_v31.parquet` | NEW |
| all other v1/v2/v3.0 outputs | preserved |
