# Pre-Registration v2.0 — GEO_F4 re-slice (classifier-noise vs substrate-noise)

**Type:** New analytical arm (additive). Does NOT amend or retract GEO_F4 firing on raw corridors (κ −0.06 div / 0.02 state). The original fire stands as the headline of §4.5 of the methodology paper; this arm reports as §4.6, asking *where* in the analytical hierarchy dynamic structure does transfer, if anywhere.
**Authored:** 2026-05-31
**Status:** LOCKED v2.0-final BEFORE re-fitting. Commit hash of last analytical state (no re-slice run yet): `b842b3e`. Locked-by-commit.

## Motivation (diagnostic-driven, the slope-edge-instability diagnostic)

The substrate evidence is mutually inconsistent under the "dynamic structure genuinely doesn't transfer" reading of GEO_F4:

| What transfers | Evidence | Interpretation |
|---|---|---|
| Gravity baseline (static O-D + mass + distance) | pseudo-R² 0.63 → 0.74 (div → state) | Static structure replicates |
| Latent corridor factors (PARAFAC rank-3 div) | Tucker split-half congruence 0.95 | Static loadings replicate |
| Corridor *regime labels* (Step-2 classifier on (μ, σ²) slope) | κ −0.06 div / 0.02 state | Discrete labels FAIL transfer |

The classifier discriminates regimes by slope-thresholding on (μ̇, σ̇²) with cuts at ±0.02/yr (mean) and ±0.05/yr (variance), where slope is fit on 6 training years and 4 holdout years. Three slope-edge sources of noise compound:
1. **Slope SE on 4–6 points** is large for any corridor with non-trivial year-to-year variance; most corridors have slopes statistically indistinguishable from zero.
2. **Discrete-label flipping at near-zero slope**: identical underlying dynamics can land in different label cells (Stationary / Concentrating / Diffusing / Fragmenting) under tiny shifts when the true slope sits near the threshold.
3. **Thin-corridor contribution**: low-volume corridors have noisy per-year μ̇, σ̇² that compound the slope noise.

The diagnostic is mathematical (slope-thresholding + finite-sample SE + nominal-category dimensionality) and the prediction is: classifier kappa will not transfer regardless of whether the underlying continuous regime positions do. **Two analytical objects are being conflated** in the original GEO_F4: the regime *positions* (where each corridor sits in (μ̇, σ̇²) space) and the regime *labels* (which of 4 cells they fall in). The labels are the noisy quantity; the positions need not be.

This arm cleanly separates the two and pre-registers tests for both, plus addresses the obvious sensitivity follow-ups (COVID-period structural break, sampling stability of the original κ, threshold sensitivity, period-split sensitivity).

## Scope: four parallel arms, run together as a package

All arms use the EXISTING corridor trajectory data (`results/geo_corridor_trajectories_state.parquet`, `..._division.parquet`) and the EXISTING tensor factors (`results/geo_tensor_factors.json`). No new data acquisition. No re-running of upstream pipeline.

### ARM A (PRIMARY) — Continuous-coordinate transfer on raw corridors

For each between-corridor `(orig, dest)` in `results/geo_corridor_trajectories_{division,state}.parquet`:
- Re-compute per-period slopes from annual μ_t and σ²_t:
  - μ̇_train = OLS slope of μ_t on year t for t ∈ {2012, …, 2017}
  - σ̇²_train = OLS slope of σ²_t on year t for t ∈ {2012, …, 2017}
  - μ̇_holdout, σ̇²_holdout: same on t ∈ {2018, 2019, 2020, 2021}
- A corridor enters the test if both periods have ≥ 4 annual points (per the original power floor).

**Falsifier GEO_F4_CONT (primary):**
Across the qualifying-corridor population, run two-sided Pearson r tests at each resolution:
- r_μ̇ = Pearson(μ̇_train, μ̇_holdout)
- r_σ̇² = Pearson(σ̇²_train, σ̇²_holdout)

PASS bar: **r_μ̇ ≥ 0.40 AND r_σ̇² ≥ 0.40**, each significant at Bonferroni-adjusted p < 0.025 (two tests per resolution). Both resolutions are tested separately; verdict is per-resolution and reported as a 2-cell box (div / state).

Substantive read:
- **PASS at both**: regime *positions* transfer; classifier noise is the source of original GEO_F4 fire. The original GEO_F4 fire remains permanent, but now lives in §4.6 as "the label-classifier overfits a stable underlying continuous structure."
- **PASS at state but FAIL at div** (or vice versa): regime positions transfer at one resolution only; report the asymmetry.
- **FAIL at both**: continuous coordinates also fail to transfer. Dynamic structure genuinely doesn't transfer at the raw-corridor granularity, and the GEO_F4 result is substantive — not classifier noise.

### ARM B (SECONDARY — exploratory with stated design) — Latent-corridor continuous coordinates

For each of the 3 PARAFAC latent factors at division-level (`results/geo_tensor_factors.json`):
- Reconstruct annual time-loading of each factor across t ∈ {2012, …, 2021}.
- OLS-fit μ̇^(k)_train, σ̇²^(k)_train on t ∈ {2012, …, 2017}; same on t ∈ {2018, …, 2021}.
- For each k ∈ {1, 2, 3}, classify the period's "slope sign with SE" into 3 cells per dimension:
  - μ̇ > +1.5 × SE(μ̇) → positive
  - μ̇ < −1.5 × SE(μ̇) → negative
  - else → near-zero
  - Same for σ̇².
- Each period × factor lands in one of 9 (3×3) cells.

**Falsifier GEO_F4_LATENT (secondary):**
PASS bar: **all 3 latent factors place in the same 3×3 cell or 1-cell-adjacent (differing by one cell in one dimension only) across periods.**

Chance probability under independence: roughly 9% (1 cell exact + 4 adjacent cells) per factor; (5/9)³ ≈ 17% — so a 3/3 pass is mild but not trivial evidence. Acknowledged honestly: with n=3 latent factors and an unavoidable per-factor power limit, this test is not pivotal on its own. It is reported as a **stated-design exploratory probe** of whether latent-space dynamics are stable. Status is secondary to ARM A precisely because of this power limit, not because it's an exotic test.

Substantive read:
- **PASS (3/3 in same-or-adjacent cell)**: dynamic structure transfers at the rank-3 latent granularity. Combined with ARM A's verdict, this localizes WHERE the structure lives.
- **FAIL**: latent-space dynamics also do not transfer cleanly at this design. Strengthens the "dynamics genuinely don't decompose" reading regardless of ARM A.

### ARM C (ROBUSTNESS) — Volume-thresholded original kappa

Restrict to the top-N corridors by total panel-mean annual volume:
- **State**: top N = 100 (pre-locked, ~20% of N=509 state corridors)
- **Division**: top N = 15 (pre-locked, ~17% of N≈85 division between-corridors)

Re-run the **ORIGINAL** Step-2 regime classifier (cuts at ±0.02/yr mean, ±0.05/yr variance) on the volume-restricted subset. Compute Cohen's κ between train-period labels and holdout-period labels.

**Falsifier GEO_F4_VOLUME (robustness):**
PASS bar: **κ ≥ 0.40 on the volume-restricted subset**, both resolutions reported.

Substantive read:
- **PASS**: classifier noise is dominated by thin corridors; high-volume corridors do transfer in the discrete-label space. Power-not-substance finding, but informative.
- **FAIL**: even after removing thin corridors, the classifier noise persists. Combined with ARM A passing, this confirms the threshold-edge instability is the issue, not corridor sparsity.

### ARM D (SENSITIVITY) — COVID-period structural break

2020 and 2021 cover the COVID-era migration anomaly (suburban exodus, remote-work-driven relocation, urban out-migration). The original holdout (2018–2021) includes 2 normal years + 2 COVID years. If dynamic structure transfers in normal periods but is disrupted by 2020–2021, the original GEO_F4 fire is partly a structural-break artifact, not pure classifier noise OR pure non-transfer.

**Replicate ARMs A, B, C on the pre-COVID holdout window {2018, 2019} only**, dropping {2020, 2021}. All bars and falsifiers as defined above, applied to this restricted holdout.

**Falsifier GEO_F4_PRECOVID:**
- If ARMs A/B/C PASS on pre-COVID holdout but FAIL on full holdout: **structural break confound named** — original GEO_F4 fire is driven by 2020–2021 regime disruption.
- If A/B/C FAIL on both: COVID is not the confound; original GEO_F4 fire is substrate-level on the slopes / labels.
- If A/B/C PASS on both: original GEO_F4 fire is classifier noise regardless of period (the cleanest single-source diagnosis).

Acknowledged: the pre-COVID holdout has only 2 years. Slope-fit power per corridor in ARM A is reduced; corridors need only ≥ 2 annual points in that window (relaxed from the ≥ 4 of the full-holdout ARM A). This is a sensitivity test, not a re-locking of ARM A — its result modifies INTERPRETATION of the primary, not its bar.

### ARM E (ROBUSTNESS — closes the "is the original κ even stable?" critique) — Bootstrap of original GEO_F4

Block-bootstrap the original Step-2 classifier kappa across corridors:
- 1,000 nonparametric bootstrap draws of corridors with replacement (preserving each corridor's full panel as a block).
- Recompute κ_train_holdout per draw at both resolutions.
- Report bootstrap mean, 95% CI, and the fraction of bootstrap draws with κ ≥ 0.40.

**No falsifier**; this is a diagnostic on the original GEO_F4 estimate.
- Bootstrap 95% CI excludes 0.40 by a wide margin → the original GEO_F4 fire is sampling-stable; the re-slice is what matters.
- Bootstrap 95% CI includes 0.40 → the original GEO_F4 fire is sampling-fragile; report this.

### ARM F (ROBUSTNESS — closes the "is the classifier knife-edge?" critique) — Threshold sensitivity

Re-run the original Step-2 classifier with the slope-thresholds scaled by × 0.5 (tighter "near-zero" zone) and × 2.0 (wider "near-zero" zone). The thresholds tested are not re-locked; the ORIGINAL (±0.02, ±0.05) remains the locked thresholds for the GEO_F4 fire. This arm is purely diagnostic of how knife-edged the discrete labels are.

Report κ_train_holdout at each threshold setting at both resolutions.

**No falsifier**; diagnostic only.
- κ monotonically passes 0.40 at some threshold setting → the threshold sits in a noise band; the original fire is threshold-sensitive.
- κ remains < 0.40 at all settings → the labels do not transfer regardless of where the thresholds are placed.

## Package-level verdict logic

| ARM A (primary) | ARM B (latent) | ARM C (volume) | ARM D (pre-COVID) | Reading |
|---|---|---|---|---|
| PASS both res | PASS or FAIL | any | PASS | **classifier-noise diagnosis confirmed**; dynamic structure lives in continuous coords and transfers; GEO_F4 fire = label-classifier overfit; §4.6 records this |
| PASS state only | any | any | PASS state | classifier-noise localized to state res; div is genuine non-transfer or under-powered; report asymmetry |
| FAIL both res | FAIL | FAIL | FAIL | **conservation-law reading reinforced**; dynamic structure genuinely doesn't decompose at ANY granularity tested; original GEO_F4 fire stands as substantive, not artifactual |
| PASS A, FAIL B | — | — | — | latent-space dynamics fail to transfer despite raw-coordinate transfer — latent reduction over-averages, OR n=3 power limit is real; report design limit honestly |
| FAIL A, PASS B | — | — | — | implausible but not impossible; would warrant a deeper look at whether the PARAFAC factors are over-smoothing |
| FAIL full holdout, PASS pre-COVID (ARM D) | — | — | PASS | **structural-break confound named**; original GEO_F4 fire is COVID-disrupted; report in §4.6 with the caveat |

The matrix is the verdict. Reporting commits to printing all four ARMs' outcomes regardless of which combination materializes, and to the verdict cell each combination indicates.

## Discipline guards (explicit pre-fit commitments)

1. **Original GEO_F4 fire is permanent.** Whatever the v2.0 outcome, §4.5 of the methodology paper continues to report the original κ −0.06 / 0.02 with the original ±0.02 / ±0.05 thresholds on the original 442/509-corridor population. The re-slice lives in §4.6, never replaces §4.5.
2. **Re-slice ≠ rescue.** No formulation in the manuscript or any future doc may use "re-slice recovers GEO_F4" or "v2.0 rescues the dynamic layer." The locked language is "v2.0 ARMs A/B/C/D locate where dynamic structure transfers, given that the raw-corridor regime-label classifier does not."
3. **No threshold tuning.** ARMs A/B/C/D fire with the bars locked in this document. ARM F's threshold scaling is diagnostic ONLY; it does not re-license a different threshold for the v1.0 fire.
4. **Abstract gate.** The methodology paper abstract reports GEO_F4 firing alongside whatever §4.6 v2.0 finds. Neither is omitted from the abstract.
5. **All-ARM reporting.** All four primary ARMs (A, B, C, D) plus the two robustness diagnostics (E, F) report regardless of pass/fail. No selective reporting.
6. **Bar-failure handling.** If ARM A PASSes at state res and FAILs at div, the paper reports that. If ARM B's chance probability turns out to mean the test is uninformative either way (which it might), the paper reports the design-limit honestly, not a "pass" claim.

## Acknowledgments at lock time

- **n=3 latent power limit (ARM B)**: real and stated. ARM B is designed to be stated-design exploratory regardless of outcome. The primary is ARM A.
- **2020 ACS sample disruption**: 2020 ACS 1-yr was not released; in the IPUMS 5-yr roll the 2020 year is the most-data-disrupted. ARM D's pre-COVID-only holdout is partly motivated by this.
- **Continuous coordinate definition**: ARM A uses raw OLS slope on the annual μ_t, σ²_t. Robust-regression alternatives (Theil-Sen, Siegel) would not change the bar — they would change the point estimates. We do NOT pre-reg an alternative-slope robustness sub-arm; if reviewers request one, it is a post-fit response, named as such.
- **Race / origin-MIGPUMA-clustering of SE**: ARM A's r_μ̇, r_σ̇² are computed across corridors as independent units; no further clustering (each corridor is a separate analytical unit by construction). Standard errors on r are computed via Fisher z-transform.
- **The two-mirrors caveat is unchanged**: the migration substrate is the observable-pull side of the displacement system. v2.0 is internal to the pull-side analysis and does not engage the SDP/homelessness push-side mirror.
- **No further amendments past v2.0**. If the re-slice's outcome warrants a v2.1, it gets locked AFTER v2.0 fires and reports honestly, never to re-litigate v2.0's bars.

## Files used (all pre-existing, no new data)

- `results/geo_corridor_trajectories_state.parquet` (7,359 corridor-years × 6 cols)
- `results/geo_corridor_trajectories_division.parquet`
- `results/geo_corridor_regimes_state.parquet` (509 state corridors with original (μ̇, σ̇²) slope fits)
- `results/geo_corridor_regimes_division.parquet`
- `results/geo_tensor_factors.json` (rank-3 PARAFAC at division, 9 units × 3 factors)

## Provenance

Locked 2026-05-31 BEFORE re-fitting. Commit hash of last analytical state on which all upstream parquets and JSONs were produced: `b842b3e`. The v2.0 results script(s) will write to `results/v2_geo_f4_reslice/` and will be the first script(s) to touch the v2.0 file tree.
