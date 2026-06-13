# Pre-Registration v1.0 — RMD-SRC Applied to *Gymnadenia odoratissima* Floral Phenotype Across an Alpine Environmental Gradient

**Substrate:** Plant floral phenotype × environmental gradient. *Gymnadenia odoratissima* (Orchidaceae), 8 Swiss populations spanning lowland (500–650 m) and mountain (1800–2250 m) regions, 1028 individually measured plants 2010–2011 (Schiestl et al. 2016, *PLOS ONE* 11:e0147975, Dryad doi:10.5061/dryad.dj40r).

**Framework:** Recursive Moment-flow Decomposition with Statistical-Rule Classification (RMD-SRC), Humphrey working draft May 2026, methodology snapshot locked 2026-05-12 (Paper 6).

**Role of this substrate:** First biological-substrate entry in the RMD-SRC ledger. Cross-substrate generality claim previously rests on quantitative/social substrates (Collatz, NBA, DNC, SP500, FkCancer, hydrology, MOFA-FLEX, migration). Plant trait variation along environmental gradients is the "no decision-making" biological substrate per [DIAGNOSTIC_LAYER_RESEARCH_DESIGN](file in C:/Users/Nate/OneDrive/Documents/methodology), a load-bearing test of whether RMD-SRC machinery generalizes outside human/quantitative substrates.

A confirming run (≤ F1 or "Clean" terminations across ≥ 50% of ℙ₀ cells with all four falsifiers silent) extends the universality claim to plant phenotype. A failing run on a named falsifier is a published null on a pre-named target. Either outcome is a result, not a setback.

**Authored:** 2026-06-01.
**Status:** **LOCKED v1.0-final, 2026-06-01.** All §2 and §3.3/3.7 `[CONFIRM]` items confirmed as drafted. Step 0 ℙ₀ partition computed and hashed before any phenotype statistic; hash recorded in `prereg/P0_hash.txt`. Subsequent changes follow diagnostic-driven amendment policy per migration v1.0 §5.

---

## 1. Locked structural commitments (inherited from RMD-SRC spec — not substrate-specific)

Identical to PRE_REG_v1.0_RMD_SRC_migration §1. Reproduced for self-containment; not re-litigated here.

### 1.1 Pipeline
Steps 0 → 6 as specified. ℙ₀ is locked before any moment-flow statistic on outcomes is computed.

### 1.2 Five-regime trajectory taxonomy (Step 2)
Stationary / Gradient-tracking / Concentrating (boson-like) / Diffusing (fermion-like) / Fragmenting. No additional regimes; no relabeling.

### 1.3 Response function (Step 3)
$$x_j(e_i) = \alpha + \beta_g \cdot \nabla g(e_i) + \beta_s \cdot \rho_s(e_i) + \beta_x \cdot \rho_x(e_i) + \varepsilon_i$$

Cell is **clean** iff trajectory regime and response-function βₛ sign agree AND residual variance is below the §2.8 threshold.

### 1.4 Decomposition order (Step 4)
Strictly **4a (categorical) → 4b (time-phase) → 4c (mixture)**, one strategy per not-clean node. No skipping, no reordering.

### 1.5 Termination conditions (Step 5)
Clean / Resolution (min cell size hit) / Failure. Each not-clean cell exits via exactly one.

### 1.6 Falsifier thresholds (verbatim from spec)
- **RMD_F1**: ≥ 80% of ℙ₀ cells clean at Step 3 without decomposition.
- **RMD_F2**: decomposition hits min-cell-size limit without ≥ 50% cleanness on original ℙ₀ cells.
- **RMD_F3**: trajectory vs response-function disagreement on ≥ 30% of leaves after decomposition.
- **RMD_F4**: holdout regime-classification accuracy (Cohen's κ) < 0.4 between train and holdout windows.

Any falsifier firing is reported as the result. No silent re-spec.

---

## 2. Orchid-specific operationalizations — `[CONFIRM]` block

### 2.1 Data source `[CONFIRM]`

**Default proposal:** Schiestl et al. 2016 dataset, Dryad doi:10.5061/dryad.dj40r, raw at `D:/Phenotype_Research/data/orchids/gymnadenia/raw/`. Primary phenotype table = `Data__SelectionAnalysis.xlsx` (1028 plants × 72 cols, 2010–2011). Auxiliary tables (FloralTrait, Reproductive, Herbivory, PollinatorLimitation) referenced by the response function but not used to expand ℙ₀.

Environmental covariates from `D:/Phenotype_Research/data/{climate,soil,elevation,ecoregions}/` already overlaid in `data/orchids/gymnadenia/derived/gymnadenia_pop_env_v2.csv` (138 cols / population).

Alternatives considered:
- Multi-species *Gymnadenia* ladder (G. conopsea + G. rhellicani sister-clade): would require separate data collection; not in deposit. Filed for v2.
- *Prosthechea karwinskii* substitute: population-mean only, no per-individual. Vetted, rejected.
- *Drakaea concolor*: no orchid floral measurements in deposit. Vetted, rejected.

### 2.2 Sampling unit `[CONFIRM]`

**Default proposal:** Plant. Each row of SelectionAnalysis is one plant measured in situ at one of 8 populations in one of 2 (or 3–4) years. No within-plant repeated measures across years (PlantIDs are year-unique).

This is a substantive divergence from the migration template: in migration the event is an *action* (a move). Here the event is an *organism's lifetime phenotype at one location*. The response-function reinterpretation:

- ∇g(eᵢ) becomes the **env vector AT the plant's location** (not a vector field traversed by the event). The plant did not move; its phenotype is the outcome of selection at one env coordinate.
- The "moment-trajectory" axis is *time* (year-to-year shift within a population) rather than *gradient progression*.

This is the same operator-form equation but a different physical interpretation. Flagged so v2 can reconsider if this maps cleanly to the spec.

### 2.3 Time period and time-bin granularity `[CONFIRM]`

**Default proposal:** Annual bins, **T = 2** (2010, 2011 — both years measured at ≥ 7 of 8 populations).

- Training window: **2010** (single year).
- Holdout window: **2011** (single year).

This is a one-year-train / one-year-holdout F4 test. Severely stringent compared to migration's 8-year/4-year split. Honest tradeoff: only year with broad-pop coverage. With T = 2 the moment-trajectory slope (μ̇, σ̇²) is a single-year difference, not an OLS regression over multiple time points. §3.3 rule definitions are adjusted accordingly.

**Alternative (if F4 power is judged inadequate):** **Population holdout** — train on 3 lowland + 3 mountain pops, holdout 1 each. Trades within-cell n loss against F4 statistical power. Decision deferred to user lock.

A FloralTraitDifferences table includes 2012 and 2013 for a subset of pops; if user prefers to extend, T = 4 with train 2010–2011 / holdout 2012–2013 is offered as a third option. Sample size shrinks per cell.

### 2.4 Structural partition ℙ₀ `[CONFIRM]`

Spec specifies "K = 12–16 species" derived from observable categorical variables before the outcome is measured. Plant-substrate analogs of demographics are sparse — we have **where the plant grew (population, region)** and **when it was measured (year)** as the pre-phenotype structural variables. The natural cross-product:

**Option A (default):** Region × Population × Year. K_max = 2 × 8 × 2 = 32; observed cells = 15 (1 pop-year is missing). Collapse rule: any cell with n < 50 plants merged with the nearest neighbor (within-region, same year, nearest-elevation population). Expected post-collapse K ≈ 12–14.

**Option B:** Env-binned ℙ₀: pH-class (3) × elev-class (3) × precip-class (2) = 18 raw cells, collapsed. Pro: env-defined; con: env values are pop-level constants so cells collapse to populations anyway.

**Option C:** Latent class on env + plant_pre_phenotype (year, region): risks 4c circularity per migration §2.4.

**Default = Option A.** Reasons: (i) the structural variables are unambiguously pre-outcome; (ii) Pop captures the env gradient by proxy (each pop is one env-coordinate); (iii) Year is the legitimate "time bin" axis; (iv) Region is the validated lowland/mountain split that drives the largest known phenotype contrast.

Collapse rule locked: cells with n < 50 plants merged with within-region same-year nearest-elevation neighbor. Order of merges deterministic by population code.

### 2.5 Observables x ∈ ℝᵈ `[CONFIRM]`

Schiestl et al. supply 7 pre-published PCs of the phenotype space (PC1–PC7 in SelectionAnalysis: aromatic compounds, terpenoids, fatty acid derivatives, display size, color groupings). Each PC has a biological interpretation in the paper.

**Default proposal:** **d = 7, using the published PCs verbatim.** Avoids re-deriving rotations on the data (which would invoke Step-4c-style mixture machinery before Step 0 freeze).

**Alternative (d = 4):** condensed observables — `morphology_PC` (single PC from PlantHeight + InflorescenceLength + NrFlowers) + `scent_PC1` + `scent_PC2` + `ColourCode`. Sparser per-cell-per-observable workload.

**Alternative (d = 3, migration-parallel):** `display_size_index` + `scent_composition_index` + `fruit_set` — closest to migration's d = 3.

**Default = d = 7.** Reasons: (i) the rotation is paper-published and pre-data-collection; (ii) finer-grained regime classification per chemical class; (iii) 1028 plants / 14 ℙ₀ cells × 2 years × 7 observables ≈ 36 plants per (cell, year, observable) — adequate for cell-level statistics.

### 2.6 Gradient field ∇g `[CONFIRM]`

**Default proposal:** **First principal component of population-level env vector** computed on `gymnadenia_pop_env_v2.csv` columns: `bio_1, bio_6, bio_12, bio_15, phh2o_0-5cm, clay_0-5cm, sand_0-5cm, soc_0-5cm, elev_wc5m, altitude_paper_m`.

PCA fit once on the 8-pop env matrix, frozen, applied to assign each plant the env-PC1 score of its population. ∇g(eᵢ) := env_PC1(pop(eᵢ)).

Expected loadings: low BIO1 + low Tmin + high elev → high PC1 (mountain); reverse → low PC1 (lowland). Sign convention locked: high PC1 = mountain.

**Alternative:** raw elevation (m a.s.l., paper-reported). Simpler, single-axis; loses soil + precipitation info but transparent.

**Default = env-PC1.** Reason: combines climate + soil + elevation into the operator the spec asks for (single gradient field that the response function regresses against). Sensitivity sweep using raw elev is logged as audit.

### 2.7 Same- / cross-species density (ρ_s, ρ_x) `[CONFIRM]`

Migration substrate uses conspecific/heterospecific density at destination. **Direct port to plants is ill-defined**: plants don't move; "density at destination" is just env at the plant's site. Two adaptation options:

**Option A (default):** community-composition operationalization.
- ρ_s(eᵢ) := *Gymnadenia odoratissima* incidence in sPlotOpen 50 km neighborhood of pop(eᵢ). (Note: the orchid may be sub-detection in sPlotOpen; if neighborhood incidence is uniformly 0 or 1 across pops, treat ρ_s as a constant and drop the βₛ term — log this as a substrate-honest reduction.)
- ρ_x(eᵢ) := dominant non-orchid cover at pop(eᵢ), operationalized as mean Picea abies relative cover in 50-km neighborhood (chosen because Picea dominates mountain pops and is sub-dominant or absent in lowland pops — large between-region variance, the variable RMD-SRC needs).

**Option B:** Drop the density terms entirely. Response function reduces to x_j(eᵢ) = α + β_g · ∇g(eᵢ) + εᵢ. Cleanest interpretation for sessile organisms.

**Default = Option A.** Reason: maintain spec form; Picea covariate is real biological context and orthogonal to env-PC1 only partially, which is itself informative. If Option A's |β_x| is dominated by env-PC1 collinearity (VIF > 5), report and fall back to Option B post-hoc only with explicit log entry.

### 2.8 Cell-size and cleanness thresholds

Migration spec values are **carried verbatim** for the orchid run, with one substrate-specific note:

- **Min cell size** (Step 5 resolution): n_c ≥ 50 plants per (cell, year). Drives the collapse rule in §2.4.
- **Cleanness** (Step 3): response-function R² ≥ 0.30 AND Shapiro-Wilk residual normality p > 0.01.
- Substrate note: 1028 plants / 14 cells / 2 years / 7 observables ≈ 36 plants per (cell, year, observable) — falls below the 50 threshold for moment computation at (cell, year, observable) granularity but is acceptable for (cell, year) moment averaging across observables. Per-observable moment series uses (cell, year) aggregation with n_c-year ≥ 50; per-observable R² in §3.4 fits across all years in cell.

---

## 3. Pre-registered analysis plan

### 3.1 Step 0 freeze
Compute ℙ₀ partition assignment per plant using §2.4 method. Save `data/orchids/gymnadenia/derived/P0_partition.parquet`. Hash + timestamp before any phenotype statistic. Hash → `prereg/P0_hash.txt`.

### 3.2 Step 1 freeze
For each (cell c, observable xⱼ ∈ §2.5 set, year t): compute μ_{c,j}(t), σ²_{c,j}(t). Save `results/moment_trajectories.parquet`. No regime classification yet.

### 3.3 Step 2 classification rule (adapted for T = 2)

With T = 2 the slope-based rule in the migration spec is undefined (one-year difference is not an OLS slope). **Locked rule for T = 2:**

| Rule | Condition |
|---|---|
| Stationary | \|Δμ/μ̄\| < 0.05 AND \|Δσ²/σ̄²\| < 0.10 |
| Gradient-tracking | sign(Δμ_{c,j}) matches sign(env_PC1 trend in cell c across years) AND magnitude \|Δμ/μ̄\| > 0.05 |
| Concentrating | Δσ²/σ̄² < −0.15 |
| Diffusing | Δσ²/σ̄² > +0.15 |
| Fragmenting | residual distribution Hartigan dip test p < 0.05 (across plants in cell, pooled over 2 years) OR none of above |

Cutoffs locked in v1.0. Sensitivity sweep allowed in v1.1 ONLY as audit, not headline. **If T = 3 or 4 is locked in §2.3, the migration-spec OLS-slope rule replaces this one verbatim.**

### 3.4 Step 3 validation
Fit response function per (cell, observable) with OLS, robust standard errors clustered at population (since within-population env-PC1 is constant, this clustering captures the actual independence structure). βₛ significance = \|t\| > 2.0 AND sign matches Step-2-implied prediction.

If §2.7 Option B is locked, drop ρ_s and ρ_x terms; cleanness criterion becomes regression of x_j on ∇g alone.

### 3.5 Step 4 logging
Every decomposition attempt writes one row to `results/decomposition_logs/decomp_tree.parquet`:
`{parent_cell_id, strategy (4a/4b/4c), split_variable, child_cell_ids, parent_cleanness, child_cleanness_mean, decision (locked/rejected)}`.

Step 4a split-variable candidates (logged but not pre-committed): year, plant_height_quintile, NrFlowers_quintile, plot-level sPlotOpen community PC1.

### 3.6 Step 6 mechanism inference
Cross-leaf classification pattern reported as a contingency table with bootstrap CIs (1000 resamples at the leaf level). No NHST claims at substrate-mechanism level; descriptive only.

### 3.7 RMD_F4 holdout protocol (year holdout)
1. Run Steps 0–5 on train year (locked in §2.3), producing terminal partition ℙ*_train and per-leaf trajectory regimes.
2. Apply ℙ*_train cell definitions to holdout-year plants.
3. For each leaf with ≥ 50 plants in the holdout year, recompute trajectory regime via §3.3 rule on holdout data.
4. **Primary F4 metric:** Cohen's κ between train and holdout regime labels across leaves. Non-failure: κ ≥ 0.4.
5. **Sanity-test metric:** simple accuracy (fraction identical labels); no fixed threshold; flag if directional disagreement with κ.

Substrate note: with only one train year and one holdout year, the trajectory regime in Step 2 is computed on *between-year* shift in each window. The "training-window trajectory" with one year is undefined. **Operational fallback:** for T = 2, the F4 test is computed as "do the same Step 2 rules applied to (train-pop μ, holdout-pop μ) at the leaf level reproduce the same regime classifications?" — i.e., between-population regime stability rather than between-time-bin stability. If user prefers strict spec adherence, lock §2.3 alternative to T = 4 (FloralTraitDifferences-extended).

### 3.8 What is NOT pre-registered
- Step 4a split-variable choice (per spec).
- v2: sister-clade (G. conopsea, G. rhellicani) cross-species comparison; multi-species ladder.
- v2: pollination-treatment arm (PollinatorLimitation supplementation vs OpenPollination as Step-4b time-phase split).
- v2: scent compounds as 22 individual observables (currently aggregated into PC1–PC7).
- Cross-substrate comparison of leaf-classification patterns vs prior RMD-SRC substrates.

---

## 4. Reporting commitments

- Result document published regardless of outcome (Clean / Resolution / Failure / F1 / F2 / F3 / F4). Written to `D:/Phenotype_Research/notes/RESULTS_RMD_SRC_gymnadenia_v1.md`.
- F1 fires → "*Gymnadenia odoratissima* phenotype variation is well-described by a single env-gradient response function; RMD-SRC decomposition machinery not required for this substrate." Meaningful negative for the cross-substrate universality claim.
- F2 / F3 → documented framework failure on a named biological substrate.
- F4 → period-specific overfit; substrate analyzable with longer time series only.
- All outcomes update the RMD-SRC substrate ledger and the methodology corpus tally.

---

## 5. Confirmed lock decisions (2026-06-01)

All eight `[CONFIRM]` items confirmed as drafted. Alternatives retained in §2 / §3 for audit trail.

| # | Item | Locked choice | Alternatives rejected |
|---|---|---|---|
| 2.1 | Data source | Schiestl 2016 dataset, Dryad doi:10.5061/dryad.dj40r, `Data__SelectionAnalysis.xlsx` as primary phenotype table | Multi-species ladder (no deposit), Prosthechea (summary-only), Drakaea (no orchid morphology) |
| 2.2 | Sampling unit | Plant (single-shot per plant; no within-plant repeated measures); ∇g reinterpreted as env-at-site for sessile substrate | Move-style event (not applicable) |
| 2.3 | Time window | T = 2 — train 2010 / holdout 2011 (single-year holdout F4) | T = 4 (2010–2013, FloralTrait-extended; per-cell n insufficient) |
| 2.4 | ℙ₀ method | Region × Population × Year; cells with n < 50 collapsed with within-region same-year nearest-elevation neighbor (deterministic by population code) | Env-binned ℙ₀ (collapses to pops anyway), LCA (4c circularity) |
| 2.5 | Observables | d = 7 (published PC1–PC7 from SelectionAnalysis; paper-rotated, pre-data-collection) | d = 4 (condensed), d = 3 (migration-parallel) |
| 2.6 | Gradient field | ∇g = env-PC1, fit once on 8-pop matrix of {bio_1, bio_6, bio_12, bio_15, phh2o_0-5cm, clay_0-5cm, sand_0-5cm, soc_0-5cm, elev_wc5m, altitude_paper_m}; frozen at Step 0; high PC1 = mountain | Raw elevation (loses soil + precip info) |
| 2.7 | ρ_s / ρ_x | Option A — ρ_s = G. odoratissima sPlotOpen 50 km incidence; ρ_x = mean Picea abies relative cover in 50 km neighborhood; if ρ_s degenerate, drop βₛ with explicit log entry | Option B (drop both terms) |
| 3.3 / 3.7 | T = 2 regime rules and F4 fallback | Δ-based regime cutoffs (§3.3 table); F4 = between-population regime stability at leaf level using train→holdout pop partitioning | Strict OLS-slope rule (undefined at T = 2) |

Amendment policy: diagnostic-driven, not result-driven. Data-distribution-exposed metric pathologies count; outcome-driven re-spec does not.

Next step: Step 0 partition + hash freeze, then Step 1 moment trajectories.

---

## Appendix A. Operative deltas vs migration v1.0

For audit. RMD-SRC migration v1.0 = template; this document = substrate-adapted clone.

| Element | Migration v1.0 | Gymnadenia v1.0 |
|---|---|---|
| Event | Migration move (individual, t−1 → t) | Plant (organism × site × year) |
| ℙ₀ axes | age × inc × fam × edu | Region × Pop × Year |
| K cells | 12–16 (collapsed cross-product) | ≈ 12–14 (post-collapse) |
| Time bins T | 12 (2012–2023) | 2 (2010, 2011) |
| Train / holdout | 2012–2017 / 2018–2021 | 2010 / 2011 |
| Observables d | 3 (Δo, distance, density) | 7 (paper PCs) |
| ∇g | opportunity-deficit | env-PC1 (climate + soil + elev) |
| ρ_s, ρ_x | conspecific / heterospecific density at destination | sPlotOpen-derived community covariates (Option A) or dropped (Option B) |
| Step 2 rule | OLS slope over 8 train years | Δ between 2 train years (§3.3 T=2 adaptation) |
| F4 axis | between-year-window stability | between-year stability (single-year windows) |

The largest structural divergence is T=2. If F4 is judged structurally underpowered, the T=4 alternative in §2.3 brings the substrate closer to spec at the cost of cell sample size.
