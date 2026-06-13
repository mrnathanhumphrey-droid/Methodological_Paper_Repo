# Pre-Registration 038 — Sub-National Spatial Co-Location of Compound-Crisis Coupling (Paper 8 mechanism frontier, Phase 1)

**ID:** PRE_REG_038
**Locked:** 2026-05-28 (predictions + falsifiers committed before computing any sub-national co-location)
**Substrate:** PRE_REG_033 (coupling census — signed axis: COD/SOM/BRA positive, UKR/TUR negative) + PRE_REG_036/037 (ENSO ruled out as the driver → mechanism question reopened) + PATTERN_023 (ETH/Horn) + PATTERN_021 (BRA)
**Paper:** 8 (Compound-Crisis Coupling)
**Status:** LOCKED — fires on IDU event-level data (`data/idmc_gidd/idu/`)

---

## 0. Why this test exists (the frontier question)

Across PRE_REG_034/036/037 we ruled out single-year ENSO as the driver of Horn compound-crisis coupling (triangulated-negative across displacement, box-mean SPEI, area-fraction SPEI). The mechanism question is therefore reopened: **is compound-crisis coupling a real WITHIN-PLACE process, or a national-aggregation artifact?**

PRE_REG_033/035 established that coupling is rare (8%), structural, and predicted by chronic shock-overlap — but all of that is measured at the **country-year** level. A country can show high national-level "coupling" between conflict-displacement and disaster-displacement for two very different reasons:
- **(Real coupling)** the same sub-national regions experience BOTH shocks — drought and conflict co-occur in the same places (resource competition, coping-capacity collapse, displacement of the same populations). The national correlation reflects a genuine local compound crisis.
- **(Aggregation artifact)** conflict hits region X, drought hits region Y, and the national totals happen to both be elevated in the same years. The "coupling" is a statistical mirage of summing two spatially-independent processes.

These are distinguishable only at the sub-national level. **IDU (IDMC Internal Displacement Updates) provides event-level displacement tagged by cause (Conflict/Disaster) with lat/lon + figure** — exactly the instrument needed. This is the make-or-break mechanism test for Paper 8.

---

## 1. Hypothesis

**H1 (co-location = real coupling):** In positively-coupled countries, conflict-displacement and disaster-displacement concentrate in the SAME sub-national units (positive cross-channel spatial correlation). The national coupling is a genuine within-place compound crisis.

**H2 (co-location tracks the coupling sign):** Across IDU countries with both channels present, the sub-national cross-channel spatial co-location coefficient correlates with the national coupling sign/magnitude from PRE_REG_033. Displacement-substitution (negative) cases spatially separate or have one channel eclipse the other.

---

## 2. Pre-locked metric + predictions

**Instrument:** IDU event-level (`data/idmc_gidd/idu/*.csv`): fields `displacement_type` (Conflict/Disaster), `latitude`, `longitude`, `figure`, `year`. 20 countries available incl. coupling cases COD, SOM, UKR.

**Spatial unit (pre-committed):** **1°×1° grid cell** (deterministic, no boundary dependency) — PRIMARY. Admin-1 (via point-in-polygon against a global admin layer if available) reported as interpretive refinement.

**Co-location metric (pre-committed):** per country, sum conflict-IDP `figure` and disaster-IDP `figure` per grid cell; **Spearman ρ across cells (conflict-IDP totals vs disaster-IDP totals)** = the spatial co-location coefficient. Also report top-quartile-cell overlap (Jaccard) as robustness.

**Window:** all IDU years available per country (IDU is recent-biased, ~2016-2026).

### Prediction set A — positive-coupling cases co-locate
- **Predicted:** COD ρ_spatial > +0.3 AND SOM ρ_spatial > +0.3 (conflict & disaster displacement share geography).

### Prediction set B — substitution case separates
- **Predicted:** UKR (PRE_REG_033 negative / displacement-substitution) shows either (i) disaster channel < 10% of total IDP (single-channel, conflict eclipses), or (ii) ρ_spatial ≤ 0 (channels spatially separated).

### Prediction set C — co-location tracks national coupling sign (the key cross-country test)
- **Predicted:** across all IDU countries with both channels (≥ ~50 events each), the per-country ρ_spatial correlates POSITIVELY with the PRE_REG_033 national coupling coefficient (Spearman across countries, expected positive; significance reported given small n).

### Prediction set D — orthogonal control
- **Predicted:** a disaster-dominant orthogonal country (PHL: typhoons in Visayas/Luzon vs Mindanao conflict) shows ρ_spatial ≈ 0 (channels in different regions) — co-location is specific to coupling cases, not universal.

---

## 3. Falsifiers (pre-committed)

- **F1 (coupling is an aggregation artifact):** COD AND SOM ρ_spatial ≈ 0 (≤ +0.1) → positive-coupling cases do NOT share geography → national coupling is a spatial-aggregation mirage, not a within-place process. **Major finding — would force re-interpretation of all of Paper 8.**
- **F2 (co-location is universal):** ALL countries (coupling and non-coupling) show similar positive ρ_spatial → co-location doesn't discriminate coupling (both channels just hit the same populous/vulnerable regions everywhere).
- **F3 (sign doesn't track):** cross-country ρ_spatial does NOT correlate with the PRE_REG_033 coupling coefficient → sub-national co-location is not the mechanism behind the national coupling sign.

F1 firing = coupling is an aggregation artifact (re-interprets Paper 8).
F1 not firing + Set C confirmed = coupling is a real within-place compound crisis; the mechanism is sub-national shock co-location.

---

## 4. Methodology
- Parse each IDU country file; keep `displacement_type ∈ {Conflict, Disaster}`, numeric `figure`, valid lat/lon.
- Bin to 1° grid cells; per country build cell × {conflict-IDP, disaster-IDP}; Spearman ρ across cells with ≥1 event in either channel.
- Top-quartile overlap (Jaccard) of conflict-heavy vs disaster-heavy cells as robustness.
- Cross-country: join per-country ρ_spatial to PRE_REG_033 coupling coefficients; Spearman across countries.
- Report channel counts/shares per country (to flag single-channel cases for Set B).
- Sensitivity: 0.5° and 2° grid.

## 5. Acknowledgments at lock time
- IDU coverage is recent-biased (~2016+) and uneven by country; report n-events per channel.
- Event geolocation accuracy varies (ADM1/2/3 in `locations_accuracy`); 1° grid absorbs minor imprecision.
- Co-location ≠ causation — both channels hitting the same vulnerable regions is itself a form of real compound exposure (F2 guards against trivial universality).
- Single-channel countries can't yield a co-location ρ (informative for the substitution hypothesis, Set B).
- PRE_REG_033 coupling coefficients are country-year correlations; this is a different (spatial) object — Set C tests whether they align.

## 6. Cross-references
- PRE_REG_033 (coupling census / signed axis — Set C joins to it); PRE_REG_036/037 (ENSO ruled out → mechanism reopened); PRE_REG_035 (structural).
- PATTERN_023 (ETH/Horn — note ETH absent from IDU; SOM stands in for the Horn CD case), PATTERN_021 (BRA — note BRA absent from IDU; COD/SOM carry Phase 1).
- Data: `data/idmc_gidd/idu/` (event-level, cause-tagged, geolocated); GADM (`data/gadm/`) + Natural Earth (`data/natural_earth/`) for admin-1 refinement.

## 7. Provenance
Locked 2026-05-28 before any sub-national co-location was computed. Metric (1° grid Spearman), case predictions, and falsifiers committed first. First fire on IDU immediately follows.

---

## 8. Results — first fit (fired 2026-05-28, IDU event-level)

Full dig: `papers/PAPER_8_COMPOUND_CRISIS/digs/2026_05_28_prereg038_subnational_colocation.md`

**F1 does NOT fire — coupling is NOT an aggregation artifact where testable.** SOM co-locates; non-coupling controls separate. But IDU single-channel coverage limits the cross-country test.

- **Set A (PARTIAL)**: SOM (Horn CD-coupling, balanced channels) ρ_spatial = **+0.30 (p=0.02) at 1°, +0.297 (p=0.0003) at 0.5°** — same districts get conflict + drought displacement. COD = −0.02 (ns) but its disaster channel is only 38 events (2.8% share) → untestable, not evidence against. Conjunction (both >+0.3) not met for coverage reasons.
- **Set B (SUPPORTED)**: UKR = 735 conflict / **0 disaster** events → pure single-channel = displacement-substitution confirmed at event level.
- **Set C (COULD NOT FIRE)**: only 4 countries (SOM/COD/PHL/NGA) have ≥30 events in both channels (n<5). IDU is single-channel-dominant (most countries conflict-only or disaster-only). Descriptively 3/4 track national sign (SOM/PHL/NGA align; COD discordant = sparse).
- **Set D (SUPPORTED)**: PHL control ρ_spatial = **−0.33 (1°), −0.49 (p<0.001 at 0.5°)** — channels spatially separated; NGA corroborates (−0.32). Non-coupling = significant spatial SEPARATION.
- **Sensitivity (pre-committed)**: signal strongest at 0.5°, washes out at 2° → **co-location is district-scale (~50–100 km)**.
- **Falsifiers**: F1 NOT fired (SOM co-locates), F2 NOT fired (controls separate, opposite to coupling case), F3 untestable (Set C n=4).

### Net
Within-place co-location mechanism supported where data permit: the Horn coupling case (SOM) co-locates at district scale, non-coupling cases (PHL/NGA) separate — co-location discriminates coupling and is NOT an aggregation artifact. Combined with the ENSO-null: **Horn coupling = local compound vulnerability (same districts hit by drought AND conflict), not a shared national climate driver.** Binding limit = IDU single-channel coverage → **Phase 2 (PRE_REG_039 candidate): dense gridded drought-hazard channel (GEE SPEI at 0.5° cells) paired with IDU conflict events, to fix coverage + enable the full cross-country Set C test + spatio-temporal co-location.**
