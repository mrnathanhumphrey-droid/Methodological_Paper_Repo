# Internal Displacement Cross-Country Study

**Working title:** Historical Atrocity Geography and Differential Displacement Response to Contemporary Conflict Shocks Across Four IDP Substrates

**Author:** Nathan Humphrey

**Status:** Phase 0 — Pre-registration v1 LOCKED at initial commit. No Stan fits yet. No rate-level outcome inspection. Data + pre-conditions only.

**Pipeline position:** Substrate 9 of the Paper 6 methodology corpus. Mirrors gun-violence (substrate 6) and food-deserts (substrate 8) discipline.

**Pre-registration timestamp:** This repository's initial commit is the pre-registration timestamp. `notes/displacement_research_design.md` v1 (this commit) and `notes/shock_amplification_specification.md` (this commit) together constitute the locked pre-registration.

---

## What this will be

A pre-registered observational study testing whether historical atrocity geography is *associated with* differential displacement intensification under contemporary conflict shocks, across four cross-country IDP substrates: Colombia, Sudan, DRC, Yemen.

The framing is correlational, not causal — per `notes/shock_amplification_specification.md`, the locked language is "associated with," not "causes." This is the substrate-9 methodology-corpus contribution: extending pre-reg + commit-hash + content-hash + walk-back discipline to cross-country humanitarian-data geography.

## Pre-registered hypotheses (§6 of design doc)

- **H_SHOCK_AMPLIFICATION (load-bearing)** — Historical-atrocity-polygon admin-2 units show differential displacement intensification under conflict shock (locked framing: "associated with," not "causes").
- **H_HISTORICAL_INTENSITY** — Admin-2 historical-atrocity-event count predicts baseline displacement rate.
- **H_TERRAIN** — Terrain ruggedness predicts displacement geography.
- **H_CROSS_COUNTRY_PORTABILITY** — H_SHOCK_AMPLIFICATION direction holds in all 4 countries.

Quantitative falsification thresholds locked in §6.

## Pre-conditions (§7 of design doc)

Four pre-conditions must pass before fitting:

1. Country sample availability (≥5 years × ≥50 admin-2 per year per country)
2. Conflict-source agreement (Spearman ≥0.6 ACLED vs UCDP-GED per admin-2 × year)
3. Polygon coverage (≥5 admin-2 in each Stage-A polygon)
4. Yemen post-2022 coverage (≥30% of pre-2022 in Houthi-controlled govs)

## Robustness axes (§5 of design doc)

Four robustness axes per finding:

1. Cross-source ACLED ↔ UCDP-GED substitution
2. 5-fold admin-2 cross-validation (SEED 20260517)
3. Pre-2020 vs Post-2020 temporal split
4. Polygon-boundary ±10km sensitivity

ROBUST n/4 reporting per finding.

## Phase 0 deliverables (this commit)

- [x] Repo skeleton + manifest.json
- [x] `_scripts/fetch_ucdp.py` (executable)
- [x] `_scripts/fetch_acled.py` (executable if `ACLED_EMAIL` + `ACLED_API_KEY` env vars set; scaffolds manual fetch instructions otherwise)
- [x] `_scripts/fetch_dtm.py` (scaffold — Phase 2 executes per locked constraint)
- [x] `_scripts/fetch_gadm.py` (executable)
- [x] `_scripts/fetch_eosv.py` (executable)
- [x] `_scripts/build_longitudinal_panel.py` (defensive harmonization with per-country `_harmonization_log.json`; rule book locked at Phase 0)
- [x] `_scripts/precond_1_country_sample_availability.py`
- [x] `_scripts/precond_2_conflict_source_agreement.py`
- [x] `_scripts/precond_3_polygon_coverage.py`
- [x] `_scripts/precond_4_yemen_post2022_coverage.py`
- [x] `notes/displacement_research_design.md` v1
- [x] `notes/shock_amplification_specification.md`
- [x] `historical_polygons/{colombia,sudan,drc,yemen}/provenance.md` scaffolds
- [x] Initial git commit (this commit) — pre-reg timestamp

## What's NOT in Phase 0 (per locked constraints)

- No Stan fits
- No rate-level outcome inspection
- No Stage-B fetch beyond stubs (Phase 2)
- No README headline result table (post-Phase 4)
- No actual digitized Stage-A polygons (multi-day budget per polygon)

## Phased execution (§10 of design doc)

- **Phase 0** (current) — data + pre-cond infrastructure + pre-reg lock
- **Phase 1** — DTM + GADM fetch + country panel build + v0_1 fit
- **Phase 2** — Stage-A polygon digitization + v0_2 fit (H_SHOCK_AMPLIFICATION first read)
- **Phase 3** — Atrocity-count covariate + v0_3 fit (H_HISTORICAL_INTENSITY)
- **Phase 4** — Full covariates + v0_4 fit + 4 robustness axes + §6 disposition reading

## Cross-substrate methodology context

Substrate 9 of the Paper 6 methodology corpus. Related substrates:

- **Substrate 6:** Gun violence (github.com/mrnathanhumphrey-droid/gun_violence). 3 CI-clean structural findings replicated across 3 robustness axes.
- **Substrate 7:** Bird song (github.com/mrnathanhumphrey-droid/birdcalls). Spectral + structural dialect findings replicated.
- **Substrate 8:** Food deserts (github.com/mrnathanhumphrey-droid/Food-Deserts). Sociology branch closed (5 probes); supply-chain branch first probe landed.

The IDP substrate is the FOURTH cross-domain test of the corpus's pre-reg + walk-back + ROBUST-n/4 discipline.

## v2 redline pending (per §12 of design doc)

PI confirmation required before Stage-A polygon digitization begins on three of four polygons (Colombia "CDO 1922" interpretation, DRC "Kivu pre-1996" interpretation, Yemen "pre-2014 Houthi" interpretation). Sudan Fur dar polygon is unambiguous and can proceed.

## Repository structure (§11 of design doc)

See `notes/displacement_research_design.md` §11 for the full structure.

## License + data ethics

Raw UCDP, ACLED, DTM, and EOSV data are NOT redistributed in this repo (gitignored under `data/`). The `manifest.json` records SHA-256 hashes for chain-of-custody auditing without redistributing the data itself.

ACLED data requires user registration per ACLED terms of use. Researchers must obtain their own ACLED API key.

This study is observational and uses publicly-available conflict + displacement datasets. No new human subjects data is collected. The "associated with" framing language in `notes/shock_amplification_specification.md` is the locked epistemic constraint.
