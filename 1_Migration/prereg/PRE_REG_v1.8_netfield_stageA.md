# Pre-Registration v1.8 — Net-Livability Field, Stage A (does one field organize flows?)

**Type:** New arc (the seam, Stage A). Additive; all prior arms (demographic, geographic, v1.7 taxonomy) stand.
**Authored:** 2026-05-28
**Status:** LOCKED before fitting. Commit hash recorded at lock.

## Motivation

The demographic arm (F2) and the geographic *dynamic* regimes (GEO_F4) failed; the opportunity-moment **pull** taxonomy (v1.7) held statically (held-out r=0.999). The two pull-moments (μ = mean opportunity, σ = upside) plus the cost axis (rent burden) suggest a **single latent quantity** drives the flow: *net realizable life* = opportunity net of what the place extracts to live there. Pull sees the top of it, push (homelessness) sees the bottom, migration is its gradient.

Stage A tests one thing: do migration corridor flows align with the gradient of ONE constructed field **N** better than with its components entered separately? The push/desperation seam to the homelessness substrate (Stage B) is **not** in this pre-reg. Stage A must earn it.

## The field (LOCKED — chosen from mechanism, not from fit)

Per MIGPUMA-year (2010 vintage; HHWT-weighted medians from `migpuma_socioecon_2010`):

```
N(place, year) = med_hhinc − 12 · med_rent      [annual median household income net of annual median gross rent, in dollars]
```

- **Honest zero:** N < 0 ⇔ median household income below annual rent (subsistence-negative origin). This zero is load-bearing for Stage B's desperation definition; only a dollar-difference form provides it.
- **Why this form (form 3, realizable-income difference):** it deliberately **bypasses the opportunity PCA μ**. μ already contains `affordability` (= med_hhinc / 12·med_rent = **1/rent_burden**), so putting μ in the field would double-count cost. Income is the only opportunity dimension in dollar units commensurable with rent. Employment, education, μ, and σ are **LABELERS** (which level set a mover chooses), not field terms.
- **σ decision (2026-05-28):** σ (upside) stays a labeler, NOT a field term.

## Corridor quantity

Between-MIGPUMA corridors o→d.

```
ΔN = N(d) − N(o) = ΔINC − ΔRENT
  ΔINC  = med_hhinc_d − med_hhinc_o
  ΔRENT = 12 · (med_rent_d − med_rent_o)
```

Window-mean N per place. Flows built **separately** for train (2012–2017) and holdout (2018–2021). Mass = mean annual MIGPUMA population (`migpuma_population_2010`); distance = centroid haversine (`migpuma_geometry_2010`). ΔN entered in $10k units.

## Models (Poisson GLM, log link; origin-MIGPUMA-clustered SE; flow = PERWT-summed corridor count; between-MIGPUMA only; corridors with pooled flow ≥ 50)

- **M0 gravity:**    log E[flow] = a + b·log(mass_o) + c·log(mass_d) + g·log(dist)
- **M1 field:**      M0 + β_N·ΔN                     (single field)
- **M2 components:** M0 + β_I·ΔINC + β_R·ΔRENT       (income, rent free)
- **M3 (secondary):** M0 + β_μ·Δμ                    (prior opportunity-index gradient, Δμ = dest_opp − orig_opp)

## Falsifiers (pre-registered decision rules)

**FIELD_F1 — the field carries signal.** In M1: β_N significant (p < 0.01, clustered) AND β_N > 0 (higher destination net-livability → more inflow), in BOTH train and holdout. If it fails to fire correctly → the field does not organize flows → **arc FALSIFIED**.

**FIELD_F2 — it is ONE field, not two forces.** In M2 (train): require β_I > 0 AND β_R < 0 (income attracts, rent repels) AND magnitude ratio |β_I|/|β_R| ∈ [0.5, 2.0] (dollar-for-dollar within 2×). **FIRES (single-field falsified)** if coefficients are same-sign, or the ratio ∉ [0.5, 2.0]. On fire: report the empirical ratio as the discovered weight and downgrade to an explicit two-force model.

**FIELD_F3 — held-out parsimony.** Fit on train, predict holdout corridor flows. Single-field M1 holdout McFadden pseudo-R² ≥ (M2 holdout − 0.01). **FIRES (field is a lossy summary)** if M2 beats M1 by > 0.01 out-of-sample.

## Verdict logic

The field is **real and singular** ⇔ FIELD_F1 fires-correctly AND FIELD_F2 does-not-fire AND FIELD_F3 does-not-fire. Then Stage B (the homelessness seam) is licensed. Any other pattern → report exactly which clause broke; Stage B waits.

## Known limitations (logged pre-fit)

- `med_hhinc` is all-householder; `med_rent` is renter-only → N mixes owner income with renter rent. Acceptable for place-level net-livability (Stage A); Stage B (renter displacement) should refit on renter income.
- Pooled (window-mean) N suppresses year-to-year variation; chosen for power/parsimony and consistency with the Stage-1 gravity baseline.
- Corridors with no observed renter rent at origin or destination drop (coverage reported).

## Next (not this pre-reg)

Stage B — the seam: origins with N < 0 (or low N) discharge into the homelessness **terminus**; the split (successful out-migration : homelessness inflow) tilts toward homelessness as reachable positive-N destinations lose landing capacity. Requires a CoC↔county↔MIGPUMA crosswalk + the SDP/homelessness dataset (D:/IDP). Homelessness enters as terminus, not as a flow source.
