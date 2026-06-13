# Pre-Registration v1.3 — Amendment to v1.0/v1.1/v1.2 (RMD-SRC US Internal Migration)

**Amends:** §2.5 (observable geography) and §2.2 (geographic unit) of v1.0.
**Authored:** 2026-05-27
**Status:** LOCKED v1.3-final, 2026-05-27. Resolves the origin-geography resolution left open at end of Step 0. v1.0/v1.1/v1.2 otherwise unchanged.

## Why this amendment is honest (not result-driven)

Forced by **data structure**, exposed during Step-0 coding: ACS public-use microdata records current residence at PUMA resolution but **prior-year residence only at MIGPUMA** (Migration PUMA — a confidentiality aggregation, ~100K-pop floor → 1,039 units in scope vs 2,351 PUMAs). Since two of the three observables are origin→destination quantities, the origin's resolution binds them. No outcome was inspected; this is a geography-feasibility constraint, not a result.

## What changed

**v1.0 §2.5 text:**
- distance = "great-circle distance between PUMA centroids"
- settlement-density = "destination-PUMA population density"
- opportunity-deficit = origin − destination opportunity index "per PUMA-year"

**v1.3 resolution (LOCKED): all three observables computed at MIGPUMA resolution (symmetric).**
- **distance** d(eᵢ) = log great-circle km between **origin-MIGPUMA centroid** and **destination-MIGPUMA centroid** (destination PUMA mapped to its MIGPUMA via the PUMA→MIGPUMA crosswalk).
- **settlement-density** ρ_set(eᵢ) = log **destination-MIGPUMA** population density (persons/km²).
- **opportunity-deficit** Δo(eᵢ) = PCA-1 opportunity index on **MIGPUMA-year** aggregates, origin-MIGPUMA minus destination-MIGPUMA. PCA still fit on the pooled 2012–2017 training panel (v1.1 A1), now at MIGPUMA aggregation, frozen.

**Event detection is unchanged** — still PUMA-level via MIGRATE1D ∈ {24,31,32} (v1.0 §2.7). Only the *observable* geography drops to MIGPUMA. A cross-PUMA move that is within-MIGPUMA (origin and destination share a MIGPUMA) still counts as an event but contributes distance≈within-MIGPUMA internal scale; these are a minority and flagged in Step-1 QA.

## Rejected alternative

- **Asymmetric: origin-MIGPUMA centroid → destination-PUMA centroid, destination-density at PUMA.** Rejected: mixes resolutions on the two endpoints of a single distance, making the gradient field Δo and the distance d interpretation inconsistent (origin "blob" vs destination "point"). Symmetric MIGPUMA is cleaner for the moment-flow trajectories. The minor resolution gain on destination-only density does not justify the asymmetry.

## Build implications (Step 1)

- Need a **PUMA→MIGPUMA crosswalk** (IPUMS publishes PUMA↔MIGPUMA correspondence; alternatively derive from the MIGPUMA definitions). 
- **MIGPUMA geometry** (centroids + land area): no direct TIGER MIGPUMA shapefile — dissolve the 2010-vintage PUMA polygons up to MIGPUMA using the crosswalk, then compute centroids and km² areas from the dissolved polygons.
- MIGPUMA-year socioeconomic aggregates (income, emp/pop 25–54, BA+ share, affordability) built from the IPUMS person records aggregated to MIGPUMA × year.

## Sections updated

| Section | prior | v1.3 |
|---|---|---|
| §2.2 geographic unit | PUMA-to-PUMA | event detection PUMA-level; observables MIGPUMA-level |
| §2.5 distance | between PUMA centroids | between MIGPUMA centroids (log km) |
| §2.5 density | destination-PUMA | destination-MIGPUMA |
| §2.5/§2.6 opportunity index | per PUMA-year | per MIGPUMA-year, origin−destination |

Unchanged: event definition codes, ℙ₀ (v1.2, K=38), windows (v1.1), PCA training-window fit (v1.1 A1), falsifier thresholds, decomposition order, reporting.
