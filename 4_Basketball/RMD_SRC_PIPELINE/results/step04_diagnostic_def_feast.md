# Step 4 — decomposition disposition (arm = def_feast)

Locked v1.0 SHA: `cd40b46`
(v1.1 amendment not in scope)

## Headline
- Step 2 non-Stationary cells (any of 4 regimes): **34**
- Of those, response-validated at Step 3 (clean): **0**
- Step 4 input cardinality: **0**
- Disposition: **vacuous**

## Reading
Per pre-reg v1.0 section 5, Step 4 applies only to cells that are BOTH (a) response-validated at Step 3 AND (b) classified as one of {Concentrating, Diffusing, Contracting, Drifting} at Step 2. Under the locked spec, Step 3's Hartigan-dip-on-raw-values check over-fires at 100% on this substrate (per-game per-36 distributions are intrinsically multimodal at the (player x game) level due to within-cell role heterogeneity). Every non-Stationary cell is therefore flagged at Step 3, leaving Step 4 with an empty input set across all 4 arms.

This mirrors Migration's v1.4 amendment diagnosis of the same dip-over-fire pattern on raw observable values. Under Path A (discipline-pure, no spec modification), the over-fire is reported as a substrate-shape finding and Step 4 proceeds vacuously.

## Consequences for downstream falsifiers
- **F2** numerator = Stationary count (Step 4 produces zero additional clean cells under the vacuous case).
- **F3** vacuously does not fire — there are no sub-partitions to be thin.
- **F1** and **F4** are independent of Step 3/4 and are computed in Step 5.

## Per-cell outcomes

*(none — Step 4 input is empty under Path A)*
