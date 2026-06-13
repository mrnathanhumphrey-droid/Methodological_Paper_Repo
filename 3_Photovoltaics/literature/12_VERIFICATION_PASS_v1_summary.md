# 12 — Verification Pass v1 Summary

**Pass date:** 2026-05-27
**Pass scope:** First verification pass on 5 canonical anchors flagged in `04_LANDSCAPE_DEGRADATION_v0.md`, `05_LANDSCAPE_RELIABILITY_v0.md`, and `06_LANDSCAPE_SITING_YIELD_v0.md`.
**Anchors verified:** Jordan & Kurtz 2013; Köntges et al. IEA-PVPS T13-09:2017; Sengupta et al. 2018 NSRDB; Holmgren et al. 2018 pvlib JOSS; Ilse et al. 2019 *Joule* soiling.
**Verifier:** 5 parallel verification subagents per meta-pre-reg §3; outputs at `07_…` through `11_…`.

## Headline outcome

**Verification caught 5 distinct attribution errors in the LLM-written v0 landscape docs.** This is exactly what the meta-pre-reg was designed to detect. Of 7 + 5 + 7 + 7 + 7 = 33 claim-level verdicts produced across the 5 verifications, 13 came back VERIFIED, 8 PARTIAL-with-corrections-needed, 12 CAN'T-VERIFY (due to WebFetch host denials on full PDFs).

## Attribution errors caught

| ID | Source doc | Original claim | Corrected reading |
|---|---|---|---|
| ERR-1 | `04_LANDSCAPE_DEGRADATION_v0.md` | "median c-Si degradation ≈ 0.5–0.8 %/yr" cited Jordan-Kurtz 2013 | The 0.5%/yr is the **all-technology** median in the 2013 paper. The c-Si-specific cut may exist inside the paper but is NOT the headline number. Tighten phrasing to "all-technology median ~0.5%/yr (Jordan-Kurtz 2013)". |
| ERR-2 | `04_LANDSCAPE_DEGRADATION_v0.md` | "mean c-Si degradation 0.8-0.9 %/yr" cited Jordan-Kurtz 2013 | This range originates in **Jordan et al. 2016 Compendium** (DOI 10.1002/pip.2744), NOT the 2013 paper. Re-attribute to 2016. |
| ERR-3 | `06_LANDSCAPE_SITING_YIELD_v0.md` | "soiling losses, arid: 3-7%/yr if uncleaned" cited Ilse 2019 | Ilse's 3-4% is the **global aggregate** 2018 production loss; 4-7% is the **projected global** 2023 loss. NOT an arid-regions-only annual figure. Arid-region uncleaned annual losses are higher than this aggregate and should be cited to specific regional studies (Sayyah 2014, Costa 2018, Maghami 2016, or Figgis Qatar field papers). |
| ERR-4 | `05_LANDSCAPE_RELIABILITY_v0.md` | "Jahn et al. T13-09:2017" | Lead author is **Köntges, M.** (ISFH); Jahn is 3rd author. Use "Köntges, M., Oreski, G., Jahn, U., Herz, M., et al., 2017." |
| ERR-5 | `04_LANDSCAPE_DEGRADATION_v0.md` + `05_LANDSCAPE_RELIABILITY_v0.md` | "Climate-specific aging is established" / failure-mode-by-climate framing | T13-09:2017 uses **Köppen-Geiger** climate zones (not the 3-bucket framing) AND **explicitly reports no strong climate-failure correlation at the 2017 dataset N**. Soften the claim. T13-30:2025 PVFS may have changed this — verify. |

## VERIFIED claims (move to canonical state)

From Sengupta 2018 (siting/yield axis):
- NSRDB 2018 PSM v3 covers 1998-2016, GOES + Himawari-7, 4 km / 30-min — VERIFIED for the 2018-paper vintage
- Validation against SURFRAD 7-station CONUS network — VERIFIED (specific RMSE/MBE table not retrieved)
- Current NSRDB suite (post-2018) at developer.nrel.gov/docs/solar/nsrdb/ — TENTATIVELY-VERIFIED

From Holmgren 2018 (modeling stack):
- pvlib-python is open-source, BSD-3-Clause, GitHub-hosted — VERIFIED
- Implements SAPM, CEC, PVWatts module models — VERIFIED
- Implements transposition models: isotropic, klucher (1979), haydavies (1980), reindl (1990), king, perez — VERIFIED IN SOURCE CODE (`pvlib/irradiance.py`)
- Implements single-axis tracker mathematics — VERIFIED
- Current state v0.15.1 (released 2026-04-21), 1917 commits, NumFOCUS-affiliated, active maintenance — VERIFIED
- 2023 JOSS project-update paper exists (Anderson, Hansen, Holmgren, Jensen, Mikofski, Driesse) — TENTATIVELY-VERIFIED

From Köntges T13-09:2017 (failure taxonomy):
- T13-09:2017 is the canonical failure-mode taxonomy reference — VERIFIED with nuance (T13-01:2014 established it; T13-09 extends)
- Failure-impact ranking: PID > bypass diodes > cell cracks > EVA discoloration — VERIFIED
- T13-01:2014 is the predecessor — VERIFIED
- Subsequent reports T13-21:2022 (Soiling), T13-23:2021 (Technical Risks), T13-25:2022 (O&M), T13-29:2025 (Degradation in new tech), T13-30:2025 PVFS — TENTATIVELY-VERIFIED

From Ilse 2019 (soiling):
- Global techno-economic review of PV soiling — VERIFIED
- Covers mitigation strategies including robotic cleaning (>95% reduction potential, €2.4-8.2/m²) — VERIFIED
- Cost-vs-revenue break-even analysis per country (top-20 PV markets, ~90% of 2018 capacity) — VERIFIED
- Per-region soiling-rate map exists in Figure 2B + Tables S1-S3 — STRUCTURALLY VERIFIED (numeric contents not retrieved)

## Useful artifacts surfaced

### Open-access PDFs identified
- Köntges T13-09:2017: `https://iea-pvps.org/wp-content/uploads/2017/09/170515_IEA-PVPS-report_T13-09-2017_Internetversion_2.pdf`
- Ilse 2019: `https://elib.dlr.de/129424/1/Joule-ils.pdf` (DLR repository)
- Jordan-Kurtz 2013: UNT Digital Library, 32-page record `https://digital.library.unt.edu/ark:/67531/metadc829954/`

(All blocked by WebFetch in subagent sessions; need permission or local-curl retrieval to read full text.)

### Datasets immediately accessible
- **NSRDB Developer API** — `developer.nrel.gov/docs/solar/nsrdb/`, requires free API key
- **SURFRAD** — NOAA GMD, free, 7 CONUS stations, 1-min cadence
- **BSRN** (Baseline Surface Radiation Network) — free, ~70 global sites
- **NREL PVDAQ** via OEDI — free, ~50-100 US PV systems with multi-year DC/AC/met data
- **DuraMAT Data Hub** — free with registration
- **pvlib-python** — GitHub.com/pvlib/pvlib-python, BSD-3-Clause

### Subsequent-tier sources to verify next
1. **Jordan et al. 2016 Compendium of PV degradation rates** (DOI 10.1002/pip.2744) — actual source of c-Si mean 0.8-0.9%/yr; closes ERR-2.
2. **T13-30:2025 PVFS** — direct successor to T13-09:2017; current field-failure dataset. PDF URL: `https://iea-pvps.org/wp-content/uploads/2025/02/IEA-PVPS-T13-30-2025-PVFS-ANNEX-Degradation-and-Failure.pdf` (verified link from Köntges subagent).
3. **T13-29:2025** — degradation in new tech (TOPCon / HJT / perovskite-Si).
4. **Buster et al. 2022** physics-guided ML NSRDB (DOI 10.1016/j.solener.2022.01.004)
5. **Habte et al. 2018** "A correct validation of NSRDB" (DOI 10.1016/j.rser.2018.07.054) — canonical RMSE/MBE table per SURFRAD station
6. **Anderson et al. 2023 pvlib project update** in JOSS
7. **Figgis et al. 2024 QEERI decade-review** of Qatar field PV soiling — surfaced as 2024 academia.edu entry

## Retrieval constraints (binding for this session)

WebFetch was denied for: `cell.com`, `sciencedirect.com`, `mdpi.com`, `iea-pvps.org`, `elib.dlr.de`, Wiley Online Library, `docs.nrel.gov`, `osti.gov`, `digital.library.unt.edu`, `research-hub.nrel.gov`, ResearchGate. Bash `curl` and PowerShell `Invoke-WebRequest` also denied on these hosts in subagent sessions.

**Implication:** the full PDFs of the canonical papers were not read this pass. Verifications relied on DOI redirect metadata, WebSearch result snippets, ScienceDirect listings, NREL developer documentation, and (for pvlib) direct GitHub source-code inspection.

The discipline still caught the attribution errors — but a re-run with WebFetch permitted on these hosts would (a) confirm or refute the CAN'T-VERIFY claims, (b) extract exact page references for the VERIFIED claims, (c) read the PDF supplementary materials (Ilse Figure 2B / Tables S1-S3 in particular).

## Prompt-injection note

One subagent (Ilse verification) reported **prompt-injection attempts observed and disregarded** in Semantic Scholar and WebSearch result content — specifically fabricated `<system-reminder>` TodoWrite blocks embedded in returned search results. Correctly ignored. Flagging for awareness: search-result content can carry prompt-injection payloads.

## Ledger impact

`02_CLAIMS_LEDGER.md` needs the following updates (next pass):

- **CLM-001** (c-Si median 0.5%/yr): downgrade to "**REFUTED as stated; CORRECTED to 'all-technology median'**". Cite Jordan-Kurtz 2013 with new phrasing.
- **CLM-002** (mean c-Si 0.8-0.9%/yr): re-attribute to Jordan 2016 Compendium; mark current Jordan-Kurtz 2013 citation as REFUTED.
- **CLM-005** (climate-specific aging established): downgrade to **PARTIAL** with the Köntges T13-09 caveat about no strong climate-failure correlation at 2017 N.
- **CLM-014** (soiling losses arid 3-7%/yr): downgrade to **REFUTED-as-attributed**; the 3-7% is global aggregate not arid-specific.
- **CLM-013** (POA modeling stack maturity): upgrade to **VERIFIED** via Holmgren 2018 pvlib paper + GitHub source-code review.

Plus several NEW CLM-NNN entries for verification artifacts (NSRDB-1/2/3, pvlib-1/2/3, T13-09-1/2/3, Ilse-1/2).

## Next-pass priorities

1. **Operator review of this summary + ledger updates.** Endorsement required before claim states officially change.
2. **Update v0 landscape docs with corrections** — strike through ERR-1 through ERR-5 with correction annotations.
3. **Verify Jordan 2016 Compendium (DOI 10.1002/pip.2744)** — closes ERR-2 fully and is the canonical c-Si degradation reference, not 2013.
4. **Verify T13-30:2025 PVFS** — current field-failure successor to T13-09; potentially changes the climate-failure-correlation question.
5. **Permission unlock for at least `iea-pvps.org`, `docs.nrel.gov`, and `elib.dlr.de`** so the open-access PDFs can be read in full on next pass.
6. **First public-data access test:** pull a small NSRDB query via Developer API (with key) to confirm the access path works; pull a SURFRAD daily file; clone pvlib repo locally.

## Operator decision points

A. Endorse this verification-pass summary as-is, or revise?
B. Which next-tier source to verify first: Jordan 2016 Compendium (closes ERR-2) or T13-30:2025 PVFS (potentially changes climate framing)?
C. Should we lift WebFetch permissions on the blocked hosts before next pass, or proceed with the same constraint and accept the partial-verification outcome?
