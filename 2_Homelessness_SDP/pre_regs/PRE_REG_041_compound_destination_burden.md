# Pre-Registration 041 — Compound-Destination Burden & Temporal Co-Occurrence (Paper 8 mechanism frontier, Phase 4 / capstone)

**ID:** PRE_REG_041
**Locked:** 2026-05-29 (predictions + falsifiers committed before any burden/temporal computation)
**Substrate:** PRE_REG_040 (Phase 3 — coupling = displacement-DESTINATION convergence; SOM dest +0.41 / origin −0.10) + PRE_REG_033 (national temporal coupling) + PRE_REG_034 Set B (national contemporaneity, lag 0)
**Paper:** 8 (Compound-Crisis Coupling)
**Status:** LOCKED — fires on IDU destination parse (reuses PRE_REG_040 parser)

---

## 0. Why this test exists (capstone: quantify + close the loop)

Phase 3 established that conflict- and disaster-displaced converge on the same DESTINATION cells (SOM +0.41) from distinct origins. Two questions remain to fully specify and quantify the mechanism:
1. **Burden (policy):** how concentrated is this? What share of national displacement do the shared-destination cells absorb?
2. **Temporal loop-closure:** the national coupling (PRE_REG_033) is a country-*year* correlation. Do the shared-destination cells receive both flows in the SAME years (acute compound burden) — which would show the national temporal coupling LIVES in those destination cells, uniting the spatial (040) and temporal (033) findings?

---

## 1. Hypotheses

**H1 (concentration):** A small set of shared-destination cells (top tercile of BOTH conflict- and disaster-destination displacement) absorbs a disproportionate share of total national displacement.

**H2 (same-year compound):** Within shared-destination cells, conflict- and disaster-destination displacement co-occur in the SAME years (positive cell-year correlation; contemporaneous, matching PRE_REG_034 Set B) — and more so than in non-shared cells. The national temporal coupling is concentrated in the shared-destination cells.

---

## 2. Pre-locked metric + predictions

**Parse:** PRE_REG_040 destination parser (IDU `locations_type`/`locations_coordinates` → destination coords), per channel, per 0.5° cell, **per year**, figure-weighted.
**Shared-destination cells:** cells in the top tercile (≥66.7th pct) of cumulative conflict-destination-IDP AND top tercile of disaster-destination-IDP.
**Countries:** both-channel IDU cases (SOM decisive; COD/NGA/PHL as data permit).

### Set A — burden concentration (H1)
- **Predicted:** shared-destination cells absorb ≥ **40%** of total national destination-displacement (conflict + disaster pooled), despite being a small fraction of cells. Report Gini + top-decile share.

### Set B — same-year compound co-occurrence (H2)
- **Predicted:** within shared-destination cells, Spearman(conflict-dest-IDP, disaster-dest-IDP) across (cell, year) > 0 (same cell-years get both) AND exceeds the same correlation in non-shared cells.

### Set C — contemporaneity (matches 034)
- **Predicted:** the cell-year co-occurrence is strongest at lag 0 (same year), not lag ±1 — the compound burden is simultaneous, not sequential.

---

## 3. Falsifiers (pre-committed)

- **F1 (no concentration):** shared-destination cells absorb < 20% of national displacement → destination convergence is diffuse, not a concentrated burden locus → weakens the policy claim.
- **F2 (not same-year):** within shared-destination cells, conflict-dest and disaster-dest are temporally UNcorrelated or anti-correlated across years → destinations receive the two flows in DIFFERENT years (sequential burden) → the national temporal coupling does NOT live in the destination cells; spatial convergence and temporal coupling are separate phenomena.
- **F3 (sequential not simultaneous):** co-occurrence peaks at lag ±1 not lag 0 → compound burden is sequential (one flow then the other), reframing the policy implication.

F2 firing decouples the spatial mechanism (040) from the national temporal coupling (033) — they'd be independent facts rather than one unified phenomenon.

---

## 4. Methodology
- Reuse PRE_REG_040 destination parsing; add `year` dimension; figure-weighted per (cell, year, channel).
- Shared-destination cells via top-tercile-both rule (report sensitivity: top quartile/decile).
- H1: share of pooled destination-displacement in shared cells; Gini; top-decile share.
- H2: pool (cell, year) over shared cells; Spearman(conflict, disaster); compare to non-shared cells.
- H2/C: lag −1/0/+1 cross-correlation of cell-year series (pooled).
- Report IDU year coverage (recent-biased ~2016+) and n shared cells.

## 5. Acknowledgments at lock time
- IDU ~2016+ → short per-cell series; H2 is a pooled cell-year test, not per-cell time series.
- "Origin and destination" combined tag included as destination (per 040); sensitivity excluding.
- SOM is the decisive both-channel case; multi-country generalization limited (COD disaster-sparse, PHL conflict-sparse).
- Burden share is descriptive (policy-relevant), not a hypothesis test per se; falsifier F1 sets the bar.
- Co-occurrence ≠ causation.

## 6. Cross-references
- PRE_REG_040 (destination convergence — quantified here); PRE_REG_033 (national temporal coupling — loop closed here); PRE_REG_034 Set B (contemporaneity); PRE_REG_038/039 (arc).
- Data: `data/idmc_gidd/idu/`.

## 7. Provenance
Locked 2026-05-29 before any burden/temporal computation. Shared-cell rule, thresholds, predictions, falsifiers committed first.

---

## 8. Results — first fit (fired 2026-05-29, IDU destination parse)

Full dig: `papers/PAPER_8_COMPOUND_CRISIS/digs/2026_05_29_prereg041_compound_destination_burden.md`

**Set A + B + C all SUPPORTED. Mechanism quantified; loop with national coupling (033) closed.**

- **Set A (burden)**: SOM **8 shared-destination cells absorb 55.6%** of national displacement (top-decile 68.3%, Gini 0.794). Highly concentrated.
- **Set B (same-year)**: within shared cells, conflict-dest × disaster-dest over (cell,year) **ρ=+0.80 (p=0.0006)** vs +0.17 ns in non-shared → the national temporal coupling LIVES in the destination hubs.
- **Set C (contemporaneity)**: lag 0 = +0.80, lags ±1 negative → strictly same-year compound (matches PRE_REG_034 Set B).
- Cross-country: NGA burden only 18.6% (diffuse, non-coupling) — coupling signature = concentrated burden (56%) AND national coupling.
- Falsifiers F1/F2/F3 all NOT fired.

### Net — mechanism complete
Unifies the arc: the national year-coupling (033) is the aggregate signature of a few destination hubs absorbing both flows simultaneously. **Compound-crisis coupling = contemporaneous displacement-destination convergence of spatially-distinct, independently-driven hazards (no shared climate driver, no co-located hazards); burden concentrated on a few receiving hubs (SOM: 8 cells = 56%) that experience neither hazard directly.** Policy: target the destination hubs, not the hazard zones. Optional remaining: multi-country generalization (SOM decisive; most IDU countries single-channel), name the 8 SOM hubs for manuscript.
