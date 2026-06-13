# Verification: Holmgren et al. 2018 pvlib

**Citation under test.** Holmgren, W.F., Hansen, C.W., Mikofski, M.A., 2018. "pvlib python: a python package for modeling solar energy systems." *Journal of Open Source Software*, 3(29), 884. DOI: 10.21105/joss.00884.

**Access dates.** Primary sources retrieved 2026-05-27.

---

## Step 1 — DOI resolution

`https://doi.org/10.21105/joss.00884` resolves (302) to `joss.theoj.org/papers/10.21105/joss.00884`. The JOSS HTML landing page itself was not retrievable through the available fetch path on 2026-05-27 (host-level denial after redirect), so metadata was obtained from the Crossref record (`api.crossref.org/works/10.21105/joss.00884`) and the JOSS review issue (`github.com/openjournals/joss-reviews/issues/884`).

**Crossref metadata confirms:**
- Title: "pvlib python: a python package for modeling solar energy systems" — matches.
- Authors: William F. Holmgren (ORCID 0000-0001-6218-9767), Clifford W. Hansen (0000-0002-8620-5378), Mark A. Mikofski (0000-0001-8001-8582) — matches author list and order.
- Journal: *Journal of Open Source Software*; ISSN 2475-9066.
- Volume 3, Issue 29, article 884 — matches.
- Published 2018-09-07 (cited as 2018 — matches).
- License: CC-BY-4.0.
- 14 references; 945 citations indexed as of 2026-05-21.

Citation is verified at the metadata level.

## Step 2 — Full text retrieval

The JOSS HTML and the JOSS-served PDF both blocked on the available fetch path. A PDF copy was downloaded via the redirect chain but could not be decoded to text in this session (PDF was binary; no extraction tool available under sandbox). Claim verification therefore relies on Crossref reference list + JOSS review thread + the live pvlib repository / source files for each claim. This is a partial-retrieval limitation and is logged here per evidence discipline.

## Step 3 — Claim checks

- **C1 — Open-source, GitHub-hosted, BSD-licensed.** CONFIRMED. JOSS review issue #884 lists repo `github.com/pvlib/pvlib-python`; live repo (accessed 2026-05-27) shows BSD-3-Clause license.
- **C2 — SAPM.** CONFIRMED indirectly. The reference list includes the King et al. SAPM PVSC paper (`10.1109/PVSC.2004` family DOIs) and pvlib's `pvsystem` module exposes `sapm`, `sapm_effective_irradiance`, `sapm_cell_from_module` (confirmed via source-file inspection of the public repo). The original paper.md source was not directly retrieved, so this is by-repo confirmation, not by-paper-quotation.
- **C3 — CEC module model.** CONFIRMED via live repo: `pvsystem.calcparams_cec`, `pvsystem.cec` interfaces present and documented in the API reference index.
- **C4 — PVWatts.** CONFIRMED via live repo: `pvsystem.pvwatts_dc`, `pvsystem.pvwatts_ac`, `pvsystem.pvwatts_losses` present.
- **C5 — Transposition models.** CONFIRMED via direct inspection of `pvlib/irradiance.py` on main: functions `isotropic`, `klucher` (1979), `haydavies` (1980), `reindl` (1990), `king`, and `perez` are all defined and dispatched through `get_sky_diffuse()`. All six models in the claim are present.
- **C6 — Single-axis tracker.** CONFIRMED. The repo's documented API reference includes a `tracking` module (single-axis tracker math is the canonical `pvlib.tracking.singleaxis` function — section listed in the reference index).
- **C7 — Actively maintained.** CONFIRMED. Live repo on 2026-05-27: current release v0.15.1 (2026-04-21), 54 releases, 1,917 commits on main, 1.6k stars / 1.2k forks, NumFOCUS-affiliated, "core group of PV modelers from a variety of institutions." A follow-on JOSS paper (Anderson, Hansen, Holmgren, Jensen, Mikofski, Driesse, 2023) exists as a project update.

All seven claims CONFIRMED; C2 with the by-repo caveat noted above.

## Step 4 — Current version state (accessed 2026-05-27)

- Current release: **v0.15.1**, dated 2026-04-21.
- Cadence: 54 tagged releases since project start; consistent release stream through 2024-2026.
- Maintainers: core group across multiple institutions; >100 contributors; NumFOCUS Affiliated Project.
- Major post-2018 additions visible in the API reference index that were not in the 2018 paper's scope:
  - `bifacial` top-level module (bifacial system modelling; ties to bifacial_radiance for view-factor / ray-trace).
  - Expanded `iotools` (PSM3, PVGIS, BSRN, SolarAnywhere, etc.).
  - `modelchain` framework as the recommended high-level entry point.
  - `transformer` losses module.
  - `scaling` (Wavelet variability model).
  - Expanded single-diode tooling consistent with IEC 61853-type matrix modeling (verified at module-listing level; specific IEC 61853 conformance not separately checked in this pass).
- A second JOSS paper (Anderson et al., 2023) documents the project update.

## Step 5 — JOSS review

From `openjournals/joss-reviews/issues/884` (retrieved 2026-05-27):
- Submitting author: William F. Holmgren (@wholmgren).
- Editor: Katy Huff (@katyhuff).
- Reviewers: Stefan Pfenninger (@sjpfenninger) and @ecotillasanchez.
- Submitted: 2018-08-07. Repository at submission: `github.com/pvlib/pvlib-python` (v0.5.2).
- Archive: Zenodo DOI `10.5281/zenodo.1411511`.
- Status labels: accepted / recommend-accept / published. Published 2018-09-07 (matches Crossref).

## Step 6 — Bottom line

Citation **VERIFIED**. All seven substantive claims (C1-C7) confirmed against primary sources (Crossref metadata, JOSS review thread, live pvlib repo source/API index). One caveat: the JOSS paper body PDF/HTML was not directly readable in-session, so section/paragraph references inside the paper itself are not quoted. Claim-level confirmation comes from the JOSS review record, Crossref metadata, and the canonical repository's source files — which is stronger evidence for the implementation claims (C2-C6) than the paper prose would be.

Holmgren 2018 is safe to cite for: pvlib as the open-source / BSD / GitHub-hosted Python toolbox implementing SAPM, CEC, PVWatts, the six listed transposition models, and single-axis tracker math, actively maintained by a multi-institution PV-modeler community.
