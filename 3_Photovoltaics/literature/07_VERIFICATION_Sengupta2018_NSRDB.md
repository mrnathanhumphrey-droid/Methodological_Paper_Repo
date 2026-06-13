# 07 — Verification: Sengupta et al. 2018 NSRDB

**Verification date:** 2026-05-27
**Verifier:** subagent + operator endorsement pending
**Target citation:** Sengupta, M., Xie, Y., Lopez, A., Habte, A., Maclaurin, G., Shelby, J., 2018. "The National Solar Radiation Data Base (NSRDB)." *Renewable and Sustainable Energy Reviews*, 89, 51-60. DOI: 10.1016/j.rser.2018.03.003.

## Retrieval status

- DOI **resolves** (302 → linkinghub.elsevier.com/retrieve/pii/S136403211830087X).
- Publisher full text + NREL/OSTI mirrors (osti.gov 1872976, docs.nrel.gov fy21osti/80439, fy22osti/82063, fy17osti/67722) **blocked under WebFetch permission policy** in this session.
- Metadata, abstract fragments, and downstream NREL documentation accessed via WebSearch result snippets + Semantic Scholar listing.
- Per-section page references inside the 2018 paper itself are **not directly verified** — flagged as retrieval limitation. Downstream NREL technical reports corroborate the engineering claims.

## Citation header verdict — CONFIRMED in full

| Field | Our citation | Verified | Verdict |
|---|---|---|---|
| Authors (order) | Sengupta, Xie, Lopez, Habte, Maclaurin, Shelby | Same 6, same order | CONFIRMED |
| Year | 2018 | 2018 | CONFIRMED |
| Title | "The National Solar Radiation Data Base (NSRDB)" | Same (note: "Data Base" two words per publisher; some NREL refs render "Database") | CONFIRMED w/ spelling note |
| Journal | Renewable and Sustainable Energy Reviews | Same | CONFIRMED |
| Volume / pages | 89, 51-60 | 89, 51-60 | CONFIRMED |
| DOI | 10.1016/j.rser.2018.03.003 | Resolves to S136403211830087X | CONFIRMED |

## Per-claim verdicts

- **C1 — NSRDB is the dataset described in this paper.** **VERIFIED.** Abstract confirms.
- **C2 — Coverage: CONUS + Americas + India + Asia/Africa.** **PARTIAL.** 2018 paper covered (a) GOES-based CONUS + surrounding Americas and (b) Himawari-7-based Asia-Pacific 2011–2015. **India via Meteosat-IODC came post-2018.** Soften any "India in 2018" claim accordingly.
- **C3 — Spatial resolution ~4 km.** **VERIFIED for 2018-era PSM v3.** Current Himawari-8 product is 2 km, Meteosat is 4 km — vintage-specific.
- **C4 — Temporal resolution 30-minute.** **VERIFIED for 2018-era.** Current Himawari-8 is 10-min, Meteosat is 15-min.
- **C5 — Temporal range starts 1998.** **VERIFIED.** PSM v3 GOES record covers 1998–2016 at time of paper.
- **C6 — Satellite-derived, which satellites.** **VERIFIED.** Primary: NOAA GOES via NREL Physical Solar Model (PSM). Secondary: Himawari-7 for Asia-Pacific. Meteosat NOT in 2018 paper as primary input.
- **C7 — GHI, DNI, DHI + auxiliary meteorology.** **VERIFIED for GHI/DNI/DHI.** Auxiliary list (air temp, dew point, RH, surface pressure, wind speed/direction, precipitable water, aerosol optical depth, surface albedo, cloud type, solar zenith angle) **corroborated via NREL developer documentation, not directly extracted from 2018 paper PDF.**

## Validation against ground truth

- **SURFRAD validation: VERIFIED.** 7 stations in CONUS. Reported abstract claim: GHI / DNI mean percentage biases within 5% / 10% respectively; per-station hourly GHI bias range 2.7–15.9% per downstream summary.
- **BSRN status in 2018 paper specifically: UNVERIFIED in this session** — broader NSRDB validation literature uses BSRN but its use in the 2018 paper requires PDF retrieval.

## Datasets referenced (usable for substrate)

- **NSRDB GOES PSM v3 1998–2016 (4 km, 30-min)** — paper subject; accessible via NREL Developer API (developer.nrel.gov/docs/solar/nsrdb/)
- **Himawari-7 PSM 2011–2015 (4 km, 30-min)** — paper subject; same access
- **SURFRAD 7-station validation network** — paper validation source; free at NOAA GMD
- Post-2018: **Himawari-8 2016–2020 (2 km, 10-min); Meteosat Prime + IODC ~2017–2019 (4 km, 15-min)** — current NSRDB suite

## Follow-up citations worth verifying next

- **F1:** Habte et al. 2018 "A correct validation of NSRDB" (DOI 10.1016/j.rser.2018.07.054) — canonical RMSE/MBE table per SURFRAD station
- **F2:** Buster et al. 2022 — physics-guided ML accuracy work (DOI 10.1016/j.solener.2022.01.004)
- **F3:** NREL FY22 Final Report 82063 — covers post-2018 NSRDB updates; cite alongside Sengupta 2018 for current capability

## Notes / disagreements with our attribution

1. **India coverage in 2018 — softened.** Our v0 doc said "India + parts of Asia/Africa" for 2018 NSRDB; correct framing is "Americas + Asia-Pacific via Himawari-7 in 2018; India via Meteosat-IODC added later."
2. **Resolutions are vintage-specific.** When citing current NSRDB capability, use 2-km / 10-min Himawari-8 figures, not the 4-km / 30-min 2018-paper figures.

## Open follow-ups for next pass

- Retrieve full PDF via osti.gov 1872976 or docs.nrel.gov fy21osti/80439 to verify per-section page refs + explicit BSRN status.
- For citing *current* NSRDB capabilities, cite the post-2018 update set (FY22 Final Report 82063 + Buster et al. 2022) alongside Sengupta 2018.

## Sources consulted

- ScienceDirect listing: https://www.sciencedirect.com/science/article/pii/S136403211830087X
- DOI 10.1016/j.rser.2018.03.003
- ADS: 2018RSERv..89...51S
- OSTI.GOV 1490905 (journal article record)
- NREL Developer API: https://developer.nrel.gov/docs/solar/nsrdb/
- NREL fy17osti/67722, fy22osti/82063 (referenced; full PDFs WebFetch-blocked)
- Habte et al. 2018 DOI 10.1016/j.rser.2018.07.054 (referenced; not retrieved)
- Semantic Scholar paper page

## Ledger impact

Move the following claims out of NEEDS-VERIFICATION:

- **CLM-013 (POA modeling stack maturity)** — not directly verified by this paper; needs pvlib + SAM verification first.
- New CLMs added per this verification:
  - **CLM-NSRDB-1:** NSRDB 2018 PSM v3 has 4 km spatial / 30-min temporal / 1998-2016 GOES coverage. **VERIFIED.** (Sengupta 2018, abstract corroborated)
  - **CLM-NSRDB-2:** NSRDB validation against SURFRAD 7 CONUS stations shows GHI bias <5%, DNI bias <10%. **TENTATIVELY-VERIFIED** (per snippet; full table not retrieved).
  - **CLM-NSRDB-3:** Current NSRDB (post-2018) includes Himawari-8 at 2 km / 10-min and Meteosat IODC for India. **TENTATIVELY-VERIFIED** (via NREL Developer API docs).
