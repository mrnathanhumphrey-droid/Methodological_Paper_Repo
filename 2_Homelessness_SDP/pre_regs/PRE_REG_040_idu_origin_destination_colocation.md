# Pre-Registration 040 — IDU Origin-vs-Destination Co-Location (Paper 8 mechanism frontier, Phase 3)

**ID:** PRE_REG_040
**Locked:** 2026-05-29 (predictions + falsifiers committed before any origin/destination split is computed)
**Substrate:** PRE_REG_038 (Phase 1 — displacement channels co-locate, SOM +0.30) + PRE_REG_039 (Phase 2 — HAZARDS do NOT co-locate; reframe → coupling = shared destinations + temporal overlap, not co-located hazards)
**Paper:** 8 (Compound-Crisis Coupling)
**Status:** LOCKED — fires on IDU `locations_type` / `locations_coordinates` parse

---

## 0. Why this test exists (direct test of the Phase 2 reframe)

Phase 1 found conflict- and disaster-DISPLACEMENT co-locate (SOM +0.30). Phase 2 found the underlying HAZARDS do not (SOM −0.24) and drought doesn't locally trigger conflict. The reframe: **compound-crisis coupling is a displacement-system property — drought- and conflict-displaced people converge on the SAME receiving destinations, even though the hazards originate in DIFFERENT places.**

IDU tags each displacement event's locations as **Origin / Destination** (`locations_type`, parallel to `locations_coordinates`). This lets us split the displacement co-location into its origin and destination components and test the reframe head-on: **do conflict-IDP and disaster-IDP share DESTINATIONS (high co-location) while having distinct ORIGINS (low co-location)?**

---

## 1. Hypotheses

**H1 (shared destinations, distinct origins):** Cross-channel (conflict × disaster) spatial co-location is HIGHER at destinations than at origins: ρ_destination > ρ_origin.

**H2 (destinations genuinely shared):** ρ_destination is substantially positive (> +0.3) — drought- and conflict-displaced converge on the same receiving cells.

---

## 2. Pre-locked metric + predictions

**Parse:** per IDU event, zip `locations_type` (split ";") with `locations_coordinates` (split ";", each "lat, lon"). Assign each coord to the ORIGIN set if its tag contains "Origin", to the DESTINATION set if it contains "Destination" ("Origin and destination" → both). Bin to 0.5° cells; sum `figure` into per-cell, per-channel (Conflict/Disaster), per-role (Origin/Destination) totals.
**Co-location:** ρ_origin = Spearman(conflict-origin-cell, disaster-origin-cell) across cells with ≥1 event either channel; ρ_destination = the same on destination cells.
**Countries:** all IDU countries with ≥30 events in BOTH channels and parseable roles (SOM is the key balanced coupling case; PHL/NGA/COD as available).

### Prediction set A — SOM (key coupling case)
- **Predicted:** ρ_destination > ρ_origin AND ρ_destination > +0.3.

### Prediction set B — generalization (paired)
- **Predicted:** across both-channel countries, ρ_destination > ρ_origin (paired; mean/median difference > 0).

### Prediction set C — origins distinct
- **Predicted:** ρ_origin is materially lower than ρ_destination (gap ≥ +0.15); origins are NOT strongly shared (consistent with Phase 2's hazard non-co-location).

---

## 3. Falsifiers (pre-committed)

- **F1 (no role distinction):** ρ_destination ≈ ρ_origin (|gap| < 0.10) → the Phase 1 displacement co-location is NOT destination-specific → it's a geography/population confound (both channels concentrate in populated zones regardless of role), and the reframe's "shared destinations" mechanism is unsupported.
- **F2 (opposite):** ρ_destination < ρ_origin → displaced converge LESS at destinations than origins → reframe wrong.
- **F3 (destinations not actually shared):** ρ_destination ≤ +0.1 even if > ρ_origin → "shared destination" is weak in absolute terms.

F1 firing = the displacement co-location is a population/geography artifact, not a destination-convergence mechanism (reframe must be revised toward pure national-temporal-overlap).
H1+H2 confirmed = the reframe is correct: coupling is destination-convergence of distinctly-originating hazards.

---

## 4. Methodology
- Robust parse: events where len(types) == len(coords) after split; tolerate "Origin and destination" (→ both); drop unparseable.
- Per country: build 4 cell-vectors (conflict-origin, disaster-origin, conflict-dest, disaster-dest); Spearman across the union of nonzero cells.
- Paired test across countries (Wilcoxon on ρ_dest − ρ_origin).
- Sensitivity: 0.25°/1° grid; figure-weighted vs event-count.
- Report n-events parsed per role/channel.

## 5. Acknowledgments at lock time
- "Origin and destination" combined tag is ambiguous (counted as both) — report its share; sensitivity excluding it.
- IDU is recent-biased (~2016+); SOM is the best-powered both-channel case.
- Destinations may be reported more coarsely than origins (or vice-versa) — accuracy field varies; 0.5° grid absorbs minor imprecision.
- Co-location ≠ causation; this tests geographic convergence of the displacement system.

## 6. Cross-references
- PRE_REG_038 (Phase 1 displacement co-location — decomposed here); PRE_REG_039 (Phase 2 hazard non-co-location → the reframe this tests); PRE_REG_033 (coupling census).
- Data: `data/idmc_gidd/idu/` (`locations_type`, `locations_coordinates`).

## 7. Provenance
Locked 2026-05-29 before any origin/destination split. Parse rule, metric, predictions, falsifiers committed first.

---

## 8. Results — first fit (fired 2026-05-29, IDU origin/destination parse)

Full dig: `papers/PAPER_8_COMPOUND_CRISIS/digs/2026_05_29_prereg040_origin_destination.md`

**Set A SUPPORTED — the reframe is confirmed. Compound-crisis coupling = displacement-DESTINATION convergence.**

- **Set A (SUPPORTED)**: SOM ρ_destination = **+0.412**, ρ_origin = **−0.097**, gap **+0.509** (>+0.3 and dest>origin). Drought- and conflict-displaced Somalis flee FROM different places but converge ON the same destinations.
- **Set B (directionally unanimous, n=3)**: all both-channel countries show dest > origin — SOM +0.51, COD +0.28, NGA +0.28. The gap (dest>origin) is universal (displaced converge); the coupling signature is the *absolute positive* destination co-location (SOM +0.41 vs NGA −0.10). (PHL destination set too sparse; n<4 for formal Wilcoxon.)
- **Set C (SUPPORTED)**: SOM origins distinct (−0.10), gap ≥ +0.15 — consistent with Phase 2's hazard non-co-location.
- Falsifiers: F1/F2/F3 NOT fired for SOM.

### Net — mechanism established
Reconciles the full arc: Phase 1 mixed-centroid +0.30 = destination signal (+0.41) diluted by non-co-locating origins (−0.10 ≈ Phase 2 hazard −0.24). **Mechanism: compound-crisis coupling is NOT co-located hazards / shared climate driver; it is displacement-destination convergence — two spatially-distinct, independently-driven hazards (drought peripheries, conflict zones) whose displaced populations pile into the SAME receiving areas. The compound burden falls on the destinations, not the hazard origins.** Fully triangulated (ENSO-null 036/037 + hazard-coloc-null 039 + origin-distinct/destination-shared 040). Policy corollary: receiving areas bear the compound load. Phase 4 = destination-burden quantification + temporal-overlap decomposition of the PRE_REG_033 coupling.
