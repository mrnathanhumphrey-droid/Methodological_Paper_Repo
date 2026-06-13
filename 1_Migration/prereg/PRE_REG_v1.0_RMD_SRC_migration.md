# Pre-Registration v1.0 — RMD-SRC Applied to US Internal Migration

**Substrate:** US internal migration
**Framework:** Recursive Moment-flow Decomposition with Statistical-Rule Classification (RMD-SRC), Humphrey working draft May 2026
**Role of this substrate:** Falsification target. Migration is the only entry in the RMD-SRC substrate ledger marked "not yet tested." A confirming run extends the cross-substrate generality claim; a failing run (F1, F2, F3, or F4 firing) is a published null on a pre-named target.
**Authored:** 2026-05-27
**Status:** LOCKED v1.0-final, 2026-05-27. All §2 `[CONFIRM]` items confirmed as drafted; §3.7 amended to add simple-accuracy sanity test alongside Cohen's κ.

**>> GOVERNING AMENDMENT: PRE_REG_v1.1_amendment.md (LOCKED 2026-05-27).** v1.1 supersedes the following sections of this document — read v1.1 for the operative values:
- §2.3 training window 2012–2019 → **2012–2017**
- §2.3 holdout window 2020–2023 → **2018–2021**
- §2.5/§2.6 PCA "2010 baseline" → **pooled 2012–2017 training panel, frozen, training-window-only**
- §2.2/§2.5 geography → **locked analysis restricted to 2010-vintage PUMAs (2012–2021); 2022–2023 is an optional cross-vintage extension, unlocked**
- §3.3 slope window 2012…2019 → **2012…2017**
- §3.7 holdout recompute 2020–2023 → **2018–2021**

All other sections of v1.0 remain operative. This v1.0 text is the immutable original anchor; do not edit below this line.

---

## 1. Locked structural commitments (from RMD-SRC spec)

These are inherited directly from the methodology spec and are not project-specific choices.

### 1.1 Pipeline
Steps 0 → 6 as specified. ℙ₀ is locked before any moment-flow statistic on outcomes is computed.

### 1.2 Five-regime trajectory taxonomy (Step 2)
Stationary / Gradient-tracking / Concentrating (boson-like) / Diffusing (fermion-like) / Fragmenting. No additional regimes; no relabeling.

### 1.3 Response function (Step 3)
$$x_j(e_i) = \alpha + \beta_g \cdot \nabla g(e_i) + \beta_s \cdot \rho_s(e_i) + \beta_x \cdot \rho_x(e_i) + \varepsilon_i$$

Predicted-sign agreement table per spec. Cell is **clean** iff trajectory regime and response-function βₛ sign agree, AND residual variance is below the threshold in §3.4.

### 1.4 Decomposition order (Step 4)
Strictly **4a (categorical) → 4b (time-phase) → 4c (mixture)**, one strategy per not-clean node. No skipping, no reordering.

### 1.5 Termination conditions (Step 5)
Clean / Resolution (min cell size hit) / Failure (no strategy reduces not-clean signature). Each not-clean cell exits via exactly one of these three.

### 1.6 Falsifier thresholds (verbatim from spec)
- **RMD_F1** (substrate doesn't need RMD): ≥ 80% of ℙ₀ cells clean at Step 3 without decomposition.
- **RMD_F2** (framework fails — decomposition-resistant): decomposition hits min-cell-size limit without achieving cleanness on ≥ 50% of original ℙ₀ cells.
- **RMD_F3** (framework internally inconsistent): trajectory vs response-function disagreement on ≥ 30% of leaves after decomposition.
- **RMD_F4** (overfit to training period): holdout regime-classification accuracy r < 0.4 between training window [t₁, t₂] and holdout window [t₂, t₃].

Any falsifier firing is reported as the result. No silent re-spec.

---

## 2. Migration-specific operationalizations — `[CONFIRM]` block

### 2.1 Data source `[CONFIRM]`

Default proposal: **primary = IPUMS USA ACS individual records 2006–2023, supplemented by IRS SOI county-to-county aggregates for flow validation.**

Rationale: IPUMS gives individual-level migration events with full demographics (age, income, family, education) needed to define ℙ₀; IRS SOI gives independent aggregate-flow check that doesn't share IPUMS sampling structure.

Alternatives considered:
- CPS-ASEC: richer annual cadence but smaller sample
- LEHD Origin-Destination: employment-based, no demographics — can't build species
- ACS migration flows tables: pre-aggregated, loses individual variation

### 2.2 Geographic unit `[CONFIRM]`

Default proposal: **PUMA-to-PUMA migration** (Public Use Microdata Areas; ~100K population per PUMA; available in IPUMS PUMS for 2012+).

Rationale: counties are too granular for IPUMS confidentiality (county only available for ~40% of cases); states are too coarse for opportunity-gradient meaning; PUMA is the natural unit in IPUMS individual records.

Tradeoff: PUMA boundaries change with decennial census redrawing (2010 → 2020 boundary shift). Pre-2012 records lose PUMA detail. Locks the time window in §2.3.

### 2.3 Time period and time-bin granularity `[CONFIRM]`

Default proposal: **2012–2023, annual time bins** (T = 12).

- Training window: 2012–2019 (8 years, pre-COVID)
- Holdout window: 2020–2023 (4 years, includes COVID + recovery — adversarial holdout for F4)

Rationale: 2012 = start of consistent post-2010 PUMA boundaries; 2023 = latest released ACS at draft date. COVID holdout is an aggressive F4 test — if regime classifications fit on 2012–2019 predict 2020–2023, that's strong evidence for substrate-level structure rather than period artifact.

### 2.4 Demographic species ℙ₀ `[CONFIRM]`

Spec specifies "K=12–16 demographic species." Two derivation methods:

**Option A (theoretical cross-product, collapsed):** age (4 bins: 18–29 / 30–44 / 45–59 / 60+) × income (3 bins: bottom-third / middle-third / top-third by household AGI) × family (2 bins: with-children / without-children) × education (2 bins: BA+ / less-than-BA) = 48 raw cells, collapsed to 12–16 by combining sparse cells.

**Option B (latent class analysis on demographics, K=12 or K=16 by BIC):** LCA on {age, income, family, education} with no migration-outcome leakage. Lock K via BIC on pre-2012 training data (separate from the 2012–2023 analysis window).

**Default proposal: Option A.** Reasons: (i) keeps ℙ₀ "from observable categorical variables" per spec; LCA already invokes Step 4c-style mixture machinery and risks circularity; (ii) cross-product cells are interpretable individually; (iii) sparse-cell collapse rule can be pre-registered (any cell with n < 500 events/year merged with nearest neighbor by age then income).

### 2.5 Observable vector x ∈ ℝᵈ `[CONFIRM]`

Spec lists "opportunity-deficit, distance, settlement-density" as the observables. Operationalizations:

1. **Opportunity-deficit** Δo(eᵢ) = origin-PUMA value − destination-PUMA value of the local opportunity index, computed as the first principal component of {median household income, employment-to-population ratio 25–54, BA+ share, housing affordability index (median income / median rent)}. PCA fit once on 2010 baseline PUMA-year panel, applied frozen to all (PUMA, year) cells. Positive values = origin worse than destination (the gradient the migrant moves with).

2. **Distance** d(eᵢ) = great-circle distance between PUMA centroids in km, log-transformed.

3. **Settlement-density** ρ_set(eᵢ) = destination-PUMA population density (persons/km²), log-transformed.

d = 3.

### 2.6 Gradient field ∇g `[CONFIRM]`

The opportunity-deficit Δo IS the gradient field per Step 3 response function. βₛ ρₛ is the same-species density at destination; βₓ ρₓ is the cross-species density at destination. Both density terms use the prior-year (t−1) PUMA composition to avoid simultaneity.

### 2.7 Event definition

An **event** eᵢ is a single individual recorded in the ACS PUMS as having migrated from PUMA π_origin to PUMA π_destination between t−1 and t. Within-PUMA moves are not events. Cross-border immigration in is not an event for v1.0 (separate substrate; flagged for v2).

### 2.8 Minimum cell size and termination

- Resolution termination threshold (Step 5): **n_c ≥ 50 events per (cell, time bin)**. Cell with any time bin below 50 cannot be further decomposed; lock as "incompletely decomposed" with labeled residual.
- Residual-variance threshold for cleanness (Step 3): **response-function R² ≥ 0.30 AND Shapiro-Wilk residual normality p > 0.01**. (Liberal R² floor — substrate is human behavior, not physics.)

---

## 3. Pre-registered analysis plan

### 3.1 Step 0 freeze
Compute ℙ₀ partition assignments on 2012–2023 panel using §2.4 method. Save as `data/derived/P0_partition.parquet`. Hash and timestamp before any outcome statistic is computed. Hash recorded in `prereg/P0_hash.txt`.

### 3.2 Step 1 freeze
For each (cell c, observable xⱼ, time bin t): compute μ_{c,j}(t) and σ²_{c,j}(t). Save trajectories as `results/moment_trajectories.parquet`. No regime classification yet.

### 3.3 Step 2 classification rule
Trajectory regime decided by the following deterministic rule on (μ̇, σ̇²) computed as OLS slopes across t = 2012,...,2019 (training window only):

| Rule | Condition |
|---|---|
| Stationary | |μ̇/μ̄| < 0.02 AND |σ̇²/σ̄²| < 0.05 per year |
| Gradient-tracking | μ̇ correlation with ∇g(t) > 0.5 AND |σ̇²/σ̄²| < 0.05 |
| Concentrating | σ̇²/σ̄² < −0.05 per year |
| Diffusing | σ̇²/σ̄² > +0.05 per year |
| Fragmenting | residual distribution Hartigan dip test p < 0.05 OR none of above |

Cutoffs locked in v1.0. Sensitivity sweep allowed in v1.1 ONLY as audit, not headline.

### 3.4 Step 3 validation
Fit response function per (cell, observable) with OLS, robust standard errors clustered at origin-PUMA. βₛ significance = |t| > 2.0 AND sign matches Step-2-implied prediction.

### 3.5 Step 4 logging
Every decomposition attempt writes one row to `results/decomposition_logs/decomp_tree.parquet`:
`{parent_cell_id, strategy (4a/4b/4c), split_variable, child_cell_ids, parent_cleanness, child_cleanness_mean, decision (locked/rejected)}`.

### 3.6 Step 6 mechanism inference
Cross-leaf classification pattern reported as a single contingency table with bootstrap CIs (1000 resamples at the leaf level). No NHST claims at the substrate-mechanism level; descriptive only.

### 3.7 RMD_F4 holdout protocol
1. Run Steps 0–5 on training window 2012–2019, locking terminal partition ℙ*_train.
2. Apply ℙ*_train cell definitions to 2020–2023 data.
3. For each leaf, recompute trajectory regime on holdout window using §3.3 rule.
4. **Primary RMD_F4 metric:** Cohen's κ between training-period and holdout-period regime labels across leaves. Threshold for non-failure: **κ ≥ 0.4** (mapping spec's "r < 0.4" to a categorical-agreement statistic, the appropriate metric for regime labels; κ corrects for chance agreement given the 5-regime taxonomy and any imbalance in regime frequencies).
5. **Sanity-test metric (locked alongside primary):** simple accuracy = fraction of leaves with identical training and holdout regime labels. Reported with no fixed threshold — used to detect pathological κ behavior (e.g., near-zero κ driven by one dominant regime, or high κ with low raw agreement). If κ and accuracy disagree directionally (one passes, one signals concern), report both and flag for investigation rather than auto-resolving either way.

### 3.8 What is NOT pre-registered
- Choice of decomposition split variable inside 4a (the spec leaves this open; logged but not pre-committed).
- v2 extensions: immigration, intra-PUMA moves, multi-year migration sequences.
- Cross-substrate comparison of leaf-classification patterns vs prior substrates (Collatz, NBA, DNC, physics_detector, cancer). Filed as separate document if produced.

---

## 4. Reporting commitments

- Result document published regardless of outcome (clean / resolution / failure / F1 / F2 / F3 / F4).
- If F1 fires: report "migration substrate is well-described by classical gradient response; RMD-SRC machinery not required" — this is a meaningful negative result for the cross-substrate universality claim.
- If F2 or F3 fires: report as documented framework failure on a named substrate.
- If F4 fires: report as period-specific overfit; substrate may still be analyzable with shorter windows but not at this configuration.
- All falsifier outcomes update the RMD-SRC substrate ledger.

---

## 5. Confirmed lock decisions (2026-05-27)

All six `[CONFIRM]` items confirmed as drafted. Alternatives considered are retained in §2 for audit trail.

| # | Item | Locked choice | Alternatives rejected |
|---|---|---|---|
| 2.1 | Data source | IPUMS USA ACS 2006–2023 individual + IRS SOI county aggregates | CPS-ASEC (sample too small), LEHD (no demographics), ACS flow tables (no individual variation) |
| 2.2 | Geographic unit | PUMA-to-PUMA | County (IPUMS coverage gap), state (too coarse for gradient) |
| 2.3 | Window / bin | 2012–2023 annual; train 2012–2019, holdout 2020–2023 (COVID = adversarial F4) | Pre-2012 (PUMA boundary shift), 5-year bins (loses time resolution) |
| 2.4 | ℙ₀ method | Option A (theoretical cross-product, 48 cells → 12–16 via sparse-cell collapse n<500/yr) | Option B LCA (risks 4c circularity) |
| 2.5 | Observables | PCA-1 opportunity index (income, emp/pop 25–54, BA+, affordability) frozen on 2010 baseline; log great-circle distance; log destination density | Individual indicator regressors (collinearity), road distance (computational cost) |
| 2.6 | Gradient ID | Δo (origin − destination opportunity) = ∇g; prior-year (t−1) densities for ρₛ ρₓ | Contemporaneous densities (simultaneity) |
| 3.7 | F4 metric | Cohen's κ ≥ 0.4 primary + simple accuracy as sanity test (no threshold; flag if directional disagreement) | κ alone (loses raw-agreement check) |

Amendment policy: subsequent changes follow the diagnostic-driven-amendment standard. Result-driven amendments are not honest; data-distribution-exposed metric pathologies are.

Next step: data sourcing per §2.1, then ℙ₀ computation and hash freeze.
