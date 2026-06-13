# DRAFT Amendment v1.3 — Diagnostic dip-on-residuals localization

**Type:** Queued diagnostic-amendment (additive). UNLOCKED — staged for review after Path A results land. Mirrors the paper's §3.4 discipline of "diagnostic-amendment without falsifier rescue" (Migration v1.10 precedent).

**Status:** DRAFT — not committed, not SHA-locked. The user reviews Path A's results first and decides whether to lock this and run the extension.

**Filed before:** any inspection of dip-on-residual p-values on this substrate. The raw-value dip results from Step 3 are visible (universally fail) but no residual-level dip has been computed yet.

## 1. Why this exists (post-Path-A motivation)

Path A executed Steps 0-6 + F1-F4 + comparative arm under the locked v1.0 + v1.1 + v1.2 spec with no rescue. Three findings warrant a diagnostic localization arm:

1. **Step 3 dip-on-raw-values fails 0/all across every arm.** Per the v1.0 spec §4, the Hartigan dip test is applied to the within-cell observable distribution pooled across training seasons. Every cell × observable returns `p_dip = 0.000`. Per-game per-36 distributions are intrinsically multimodal at the (player × game) level due to within-cell role / minutes heterogeneity (a 32-MPG starter and a 14-MPG rotation guy within the same cell produce a pooled bimodal distribution).
2. **F4 fires on all 16 (arm × observable) cells**, with mean κ ≈ 0 across train→holdout. Regime labels do not transfer. The framework's dynamic-classification layer carries no signal at this resolution.
3. **The static decomposition transfers well.** σ_within transfers at r ≈ 0.99 across windows; β_role-cohort at r ≈ 0.61–0.93. The static cell-signature is robust; only the regime label is noisy.

The v1.3 diagnostic asks a single localized question: **does the dip-over-fire reflect a raw-value measurement artifact or a substrate property?**

If dip on the residuals of an additive within-cell regression (cell-mean baseline) returns p ≥ 0.05 for a non-trivial fraction of cells, then the raw-value over-fire is a measurement artifact — the substrate IS unimodal at the residual level, and the locked Step 3 dip check is testing the wrong target. This mirrors Migration's v1.4 amendment diagnosis exactly.

If dip on residuals also over-fires, the substrate has genuine within-cell multimodality even after removing cell-mean effects — i.e., role-cohort heterogeneity is structural and the partition under-resolves it.

## 2. Locked operationalizations (proposed)

### 2.1 Scope

Identical to v1.0 + v1.1 + v1.2: same qualifying player-season set (2,798), same 4 observables, same training window, same 4 arms (`usg`, `mpg`, `usg_adj`, `mpg_adj`). No new data acquisition.

### 2.2 The new check (Check D — dip on residuals)

For each (cell, observable):
1. Compute the within-cell residual per (player, game): `r_pg = y_pg - μ_cell`, where `μ_cell` is the cell's training-window pooled mean of the observable.
2. Apply Hartigan dip test to the pooled residuals across the training window.
3. **PASS if `p_dip_residual ≥ 0.05`.**

### 2.3 Step 3 amended (additive)

The locked v1.0 Step 3 dip-on-raw-values check (Check A) **remains in place and continues to fire as documented under Path A**. Check D is an ADDITIONAL check, reported separately. Neither check's threshold is modified.

The v1.0 "clean" definition (Check A AND Check B AND Check C) is preserved unchanged. Check D produces a SEPARATE downstream disposition called `residual_clean`:
- `residual_clean = (Check D PASS) AND (Check B PASS) AND (Check C PASS)`

This `residual_clean` quantity feeds an alternative F2 / F3 / Step 4 / comparative arm pipeline reported alongside the v1.0 pipeline. The original Path A reports are NOT modified.

### 2.4 Localization disposition (pre-committed)

After Check D runs across all 4 arms:

- **Frac(Check D PASS) ≥ 0.50** across (cell, observable) pairs: **localization confirmed.** The raw-value dip-over-fire is a measurement artifact; the substrate IS unimodal at the residual level. Path A's Step 3 over-fire is documented as measurement-on-wrong-target. Path B's `residual_clean` pipeline produces a parallel F2 / Step 4 / comparative arm that lifts the framework's machinery off the dip-over-fire bottleneck. Both pipelines are reported.
- **0.20 ≤ Frac(Check D PASS) < 0.50**: **partial localization.** Some cells have unimodal residuals, others remain multimodal even after cell-mean adjustment. Substrate has mixed within-cell structure; report the cell-by-cell breakdown without claiming full localization.
- **Frac(Check D PASS) < 0.20**: **substrate-level multimodality confirmed.** Even after cell-mean adjustment, within-cell distributions are multimodal — the partition under-resolves role-cohort heterogeneity at NBA scale. Path A's dip-over-fire is reframed as a substrate-shape finding, not a measurement artifact. The static-transfers-but-dynamic-doesn't pattern from Path A is structurally locked in.

All three dispositions are publishable.

## 3. Cross-arm comparison expansion (post-v1.3)

Path B introduces a second pipeline per arm. The substrate ledger expands:
- 4 arms × 2 pipelines (v1.0 + v1.3) × 4 observables = 32 F2 values, 32 F4 values, 32 comparative dispositions.
- Cross-arm κ matrix grows to compare Path A vs Path B regime labels.

This is a substantial reporting expansion. The amendment commits to printing all 32+32+32 values regardless of which fire / pass / TIE.

## 4. Discipline guards

- **Path A reports are NOT modified.** SUBSTRATE_LEDGER.md retains v1.0 + v1.1 + v1.2 results verbatim. v1.3 results are reported in a separate section.
- **v1.0 Check A threshold (`p_dip ≥ 0.05`) is NOT modified.** Check D's threshold is the same value but applied to a different target (residuals vs raw).
- **No retroactive de-firing of F4.** F4 firing per the locked spec stands. Path B does not modify Step 5 transfer or F4 computation.
- **No re-running of v1.0 / v1.1 / v1.2 pipelines.** v1.3 adds a parallel pipeline; the original artifacts at SHAs `db0ed9a` / `4d0602d` / `1bfdb4c` remain authoritative for what they cover.

## 5. Outputs (v1.3 artifacts)

- `step03_dip_residual_{arm}.parquet` — per (cell, observable): residual_p, residual_pass, residual_clean.
- `step03b_diagnostic_{arm}.md` — Check D pass rates + localization disposition.
- `step04b_decomposition_{arm}.json` — Path B Step 4 outcomes (4a/4b/4c) on residual_clean cells.
- `step05b_falsifiers_{arm}.json` — Path B F2 / F3 / Step 5 / comparative outcomes.
- `crossarm_kappa_matrix_path_b.json` — Path A vs Path B regime κ.
- `SUBSTRATE_LEDGER.md` (appended) — new section under "Path B results."

## 6. Sign-off (not yet executed)

This amendment is queued. The user reviews Path A's substrate ledger and decides whether to lock v1.3 and run the extension. Sign-off path:
1. User says "lock v1.3" → I rename this file to `AMENDMENT_v1.3_DIP_ON_RESIDUALS_LOCKED.md`, git add, git commit, record SHA in `SHA_LOCK.txt`.
2. Then build `step03b_validate_residuals.py` + `step05b_falsifiers_path_b.py`.
3. Run on all 4 arms.
4. Update SUBSTRATE_LEDGER.md with Path B section.

If the user does NOT lock v1.3, this draft sits as documentation of the methodological extension that COULD be run, preserving the discipline trail.

---

**End of draft v1.3.**
