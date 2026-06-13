# Results — RMD-SRC v2.0 Applied to *Gymnadenia odoratissima* (K=8 partition)

**Pre-registration:** `prereg/PRE_REG_v2.0_RMD_SRC_gymnadenia.md` (LOCKED 2026-06-01).
**Inherits:** v1.1 rotation, v1.2 regression form, v1.3 Option B predictor set.
**Single structural delta vs v1:** §2.4 partition Region × Pop × Year (K=12) → Region × Pop (K=8). Year demoted from ℙ₀ to t-bin axis, activating Step 4b time-phase splits.
**Execution date:** 2026-06-01.

---

## Headline outcome

**v2.0 reproduces v1's F2 + F4 failure pattern with no improvement from the partition change.**

| Falsifier | v1.0 | v2.0 | Direction |
|---|---|:---:|---|
| F1 (substrate doesn't need RMD)    | 6.0 % silent  | 5.4 % silent  | no change |
| **F2 (decomposition-resistant)**   | 6.0 % **FIRES** | 5.4 % **FIRES** | no change |
| F3 (regime vs response mismatch)   | 4.8 % silent  | 3.6 % silent  | no change |
| **F4 (between-pop κ instability)** | 0.216 **FIRES** | 0.216 **FIRES** | identical |

**§3.8's pre-registered hypothesis H_v2 is DISCONFIRMED.** v2.0 explicitly pre-committed: *"If F2 in v1 was driven by partition choice, v2.0 will recover cells via 4b time-phase splits."* 4b was alive — 35 Year-split attempts logged across 5 multi-year cells × 7 observables — and recovered **zero** cells. The 4abc-exhaustion rate is 53/56 = 94.6 %.

**Substrate-honest read:** F2 failure is **substrate-structural at this T**, not partition-driven. The framework cannot decompose *Gymnadenia* phenotype at T=2 regardless of where Year sits in the structural partition.

F4 is unaffected by partition (regime classifications are at Pop level; partition only changes which plants belong to which "cell"). κ = 0.216 identical to v1.

---

## What changed and what didn't

### Step 0 — partition
v2.0: K=8 (D, R, L, RW, S, M, A, C), n range 69–190, no collapses. Compare v1.0: K=12, 1 collapse (Schatzalp 2010 → Muenstertal 2010), n range 56–143. P0 hash `bc7c6f68…` (v1.0) ≠ new v2.0 hash; both preserved on disk.

### Step 1 — moments
v2.0 produces 112 (cell, obs, year) slots; 91 populated (5 cells × 7 obs × 2 years + 3 cells × 7 obs × 1 year). v1.0 had 84 (cell, obs) entries.

### Step 2 — regimes
**Identical pop-level regime classifications.** Both versions classify regimes per (Pop, observable); the partition change re-labels cell IDs but the underlying Δμ between 2010 and 2011 within each pop is the same. The 5 multi-year pops get the same regime labels; the 3 single-year pops get `Insufficient_T` in both versions.

### Step 3 — response function
**Identical** Option B form (env_PC1 + y2011). The OLS fit operates on plant-level data; partition affects only per-cell cleanness aggregation. Global β_g, β_y, R², Shapiro p, global_clean labels per observable all match v1.3 within rounding.

Per-cell cleanness counts:
- v1.0: 5/84 clean (6.0 %)
- v2.0: 3/56 clean (5.4 %)

The drop is partition-mechanical: the 5 v1 clean cells (Remi_2010, Remi_2011, Ross_2011, Corv_2011, Muen_2011) under v2 collapse into 5 v2 cells (L_Remi, L_Ross, M_Corv, M_Muen, plus M_Scha as a separate one). Pooled multi-year cells (L_Remi, M_Muen) now have larger within-cell residual spread driven by year-shift, pushing pred-err and within-cell Shapiro across thresholds.

3 v2 clean cells = L_Ross, M_Corv (both single-year + Insufficient_T), and M_Scha (the only multi-year cell that survived).

### Step 4 — decomposition
**4b was alive but produced zero recoveries.** 35 4b Year-split attempts across 5 multi-year cells × 7 observables — for each one of those cells the year subcells either failed cleanness or failed min-cell-size (Schatzalp 2010 child = n=47 < MIN_CELL_N = 50). 4c GMM produced no further recoveries.

Why 4b didn't help: the year dummy y2011 in the global response function already captures the within-cell year shift. Splitting the cell on year produces subcells where the global ŷ is closer to subcell μ (pred-err improves marginally), but **within-cell Shapiro doesn't improve** with smaller subcell size — residual non-normality is intrinsic per observable (skewed scent compounds, heavy tails), not a year-mixture artifact.

The conclusion the framework is structurally telling us: the cleanness threshold's Shapiro gate is the binding constraint, not the year confound. 4b is the wrong decomposition tool because the failure mode is *distribution shape*, not *time-phase mixture*.

### Step 5 / §3.7 F4 — identical to v1
4 within-region pop pairs, average κ = 0.216, Doettingen-Linn dominates the agreement (κ = 0.696), Remigen the outlier. Same result.

---

## Substrate × framework structural diagnosis

Combining v1 and v2 results:

- **F2 fires under both partitions** ⇒ partition was not the cause.
- **4b time-phase alive in v2** ⇒ year-phase confound is not the cause either.
- **4c GMM produces no splits in either run** ⇒ within-cell distribution is not a hidden mixture of well-separated components.
- **The dominant cleanness failure mode is within-cell Shapiro** ⇒ residuals against the linear-additive response function are systematically non-normal within most cells.

This points at a substrate ↔ response-function-form mismatch: the v1.0 §1.3 response function form (additive linear in env_PC1 + densities) underspecifies *Gymnadenia* phenotype variance. The within-cell residuals carry biology that linear-additive can't model — likely:

- Heavy-tailed scent compound distributions (right-skewed by chemistry, log1p preserves some skew).
- Pop-specific intercept shifts beyond what env_PC1 captures (the Remigen outlier from F4 — Remigen sits at 600 m, intermediate elevation, may have unmeasured local selection regime; F4 already flagged this).
- Interaction structure (env_PC1 × y2011 or env_PC1²) not in the locked spec equation.

These are **substrate-class hypotheses** in L2 retro Mode C territory (non-additive interaction). A v3 pre-reg with a non-additive operator class — quadratic terms, env × year interaction, or a robust regression family — would be the next natural test of whether the substrate is decomposable by RMD-SRC at all.

---

## Updated L2 Mode classification

| v1 retro (single run) | v2 update (both runs combined) |
|---|---|
| Mode A + B (partition exhausted decomp substrate, regime non-generalization) | **Mode C added**: locked spec's additive operator-class is the binding mismatch with substrate distribution shape. v2 disconfirmed partition as the cause; remaining structural mismatch is operator form. |

The substrate has clear per-unit signal (x2 axis, regime asymmetry, env_PC1 → x2 β = −0.32). The RMD-SRC framework at the locked operator-class formulation can't decompose it. A non-additive operator class is the v3 candidate; not pursued in v2.

---

## RMD-SRC substrate ledger update (v2)

| Substrate | v1 outcome | v2 outcome | Net |
|---|---|---|---|
| Gymnadenia | F2 + F4 fire | F2 + F4 fire | Substrate failure confirmed across partitions; cause = operator-class mismatch, not partition or T-axis |

The cross-substrate universality claim for RMD-SRC is **negatively updated** for biological substrates at this configuration: a structural-prior partition + additive single-operator response function does not decompose a sessile plant substrate with multi-trait scent phenotype at T=2. A non-additive operator-class re-pre-registration is the v3 candidate; multi-year extension (T=4) is a v2.1 candidate.

---

---

## Addendum — Post-hoc within-region stratification (Reading B)

**NOT pre-registered.** Slices the v2.0 substrate into lowland (4 pops, n=565) and mountain (4 pops, n=463) blocks, re-fits env-PC1 within each region, re-runs steps 1-5 inside each stratum. Reported with explicit exploratory tag.

| Stratum | n | env-PC1 var % | pre-decomp clean | F4 avg κ | F1 | F2 | F3 | F4 |
|---|---:|---:|---|---:|---|---|---|---|
| lowland | 565 | 47.8 % | 1/28 = 3.6 % | 0.163 | silent | **FIRES** | silent | **FIRES** |
| mountain | 463 | 58.0 % | 3/28 = 10.7 % | −0.037 | silent | **FIRES** | silent | **FIRES** |

**B findings:**

1. **Within-lowland env-PC1 puts Remigen at the high extreme** (D −2.80, RW −0.16, L +0.44, **R +2.51**). Within-region gradient is essentially a "distance from Doettingen-Linn" axis with Remigen at the far end. Confirms Remigen as the structurally-distinct lowland pop driving F4.

2. **Within-lowland D–R κ = −0.077** (vs global D–R κ = +0.054). Stratification sharpens the Remigen anti-correlation. Linn–Remigen κ = 0.125 also remains low.

3. **Mountain stratum: only M–S κ pair available** (A and C single-year, drop from F4). κ = −0.037 → essentially zero agreement. Mountain trajectory pops do not share regime structure.

4. **x2 is the only globally-clean observable in both strata** (lowland Shapiro 0.49, R² 0.36; mountain Shapiro 0.09, R² 0.31). All other observables fail Shapiro at the within-stratum pooled level. The residual non-normality is **invariant to stratification**.

5. **Mountain cleans modestly more cells than lowland** (10.7 % vs 3.6 %) — suggests mountain phenotype within-region is slightly more linear-additive on x2, but neither stratum approaches F1's 80 %.

**Triangulated conclusion across v1 + v2 + B:**

| Diagnostic | v1 outcome | v2 outcome | B outcome |
|---|---|---|---|
| F2 fires | ✓ | ✓ | ✓ both strata |
| F4 fires | ✓ | ✓ | ✓ both strata, worse κ |
| 4b alive | (locked-out) | ✓ but 0 recoveries | ✓ but 0 recoveries |
| Cleanness failure mode | within-cell Shapiro | within-cell Shapiro | within-cell Shapiro |
| Stratification effect on cleanness % | n/a | unchanged | unchanged |
| Stratification effect on F4 | n/a | unchanged | **worse** (Remigen sharpens) |

**Mode classification (final, post-B):** L2 Mode A + B + C. The spec's additive-linear single-operator response function is the binding mismatch; stratification confirms it's operator-class, not partition, not T-axis, not within-region noise. Substrate-honest. Non-additive response-function form (env_PC1² + env_PC1·y2011, or robust regression family) is the clean v3 candidate, not pursued here.

**Remigen's outlier biology — possible mechanisms (speculative):** intermediate elevation 600 m vs lowland mean 575 m; geographic separation east of Aare river vs western lowland cluster; possible mid-elevation pollinator community; possible local soil chemistry not captured by 5 km SoilGrids. Would require pop-specific micro-environmental measurement to disentangle; not pursued here.

### Files (B addendum)

```
results/
  step2_regimes_lowland.parquet         step2_regimes_mountain.parquet
  step3_response_function_lowland.parquet   step3_response_function_mountain.parquet
  step3_cell_cleanness_lowland.parquet  step3_cell_cleanness_mountain.parquet
  step4_leaves_lowland.parquet          step4_leaves_mountain.parquet
  step5_F4_pairs_lowland.parquet        step5_F4_pairs_mountain.parquet
  B_within_region_summary.parquet
scripts/orchids/
  14_B_within_region.py
prereg/
  B_within_region_log.txt    (NOT a pre-reg; exploratory log)
```

---

## Files (v2)

```
prereg/
  PRE_REG_v2.0_RMD_SRC_gymnadenia.md
  P0_hash_v20.txt
  v20_log.txt
data/orchids/gymnadenia/derived/
  P0_partition_v20.parquet
results/
  moment_trajectories_v20.parquet
  step2_regimes_v20.parquet
  step3_response_function_v20.parquet
  step3_cell_cleanness_v20.parquet
  decomposition_logs_v20/decomp_tree.parquet
  step4_leaves_v20.parquet
  step5_F4_pairs_v20.parquet
  step_falsifier_report_v20.parquet
scripts/orchids/
  12_v20_step0_partition.py
  13_v20_pipeline.py
notes/
  RESULTS_RMD_SRC_gymnadenia_v2.md     (this file)
```

All v1 artifacts preserved.
