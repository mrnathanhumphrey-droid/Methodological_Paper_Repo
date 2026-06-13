# 14 — Verification: IEA-PVPS T13-30:2025 — PV Failure Fact Sheets (PVFS) Review 2025

**Verification date:** 2026-05-27
**Verifier:** operator (local PDF read directly) + endorsement pending
**Target citation:** IEA-PVPS Task 13, 2025. "Photovoltaic Failure Fact Sheets (PVFS) — Review 2025." Report IEA-PVPS T13-30:2025. ISBN [verify, not on cover page].
**Purpose:** Investigate ERR-5 from `12_VERIFICATION_PASS_v1_summary.md`. T13-09:2017 found no strong climate-failure correlation at its N; does T13-30:2025 overturn or extend that finding?

## Retrieval status

- **Local PDF retrieved** at `D:/Renewables/Solar/data/raw/papers/Kontges2025_T13-30_PVFS.pdf` (8.1 MB, 83 pages)
- Source: operator pulled from `https://iea-pvps.org/wp-content/uploads/2025/02/IEA-PVPS-T13-30-2025-PVFS-ANNEX-Degradation-and-Failure.pdf`
- Read locally via pdfplumber — full text accessible.

## Citation header verdict — CONFIRMED with refinement

| Field | Verified value |
|---|---|
| Title | "Photovoltaic Failure Fact Sheets (PVFS) — Review 2025" |
| Report ID | IEA-PVPS T13-30:2025 |
| Year | 2025 |
| Page count | 83 |
| ISBN | Not visible on cover page; check PDF metadata or later page |
| Editors | Gabi Friesen (SUPSI Switzerland), Jay Lin (PV Guider), Ulrike Jahn (Fraunhofer CSP Germany) |
| Main contributors | Friesen, Köntges (ISFH Germany), Lin, Oreski (PCCL Austria), Eder (OFI Austria), Hacke (NREL USA), Gebhardt (Fraunhofer ISE Germany), Özkalay (SUPSI), Bucher (BFH Switzerland), Caccivio (SUPSI), Couderc (CEA France), Spataru (DTU Denmark) |

## Per-claim verdicts

### C1 — Is this the direct successor to T13-09:2017? **NO — different document type.**

T13-30:2025 is a **digest of 30 PV Failure Fact Sheets** organized by component, NOT a sample-N-based field-failure study. From page 6: *"The PVFS have been reviewed in 2024 to include latest PV module failures observed in the field and discussed in more detail in a technical IEA PVPS Task 13 report [Köntges25]."*

**The successor to T13-09:2017 is `[Köntges25]`** — a SEPARATE technical Task 13 report cited as: "M. Köntges, J. Lin, A. Virtuani, G. Eder, J. Zhu, G. Oreski, P. Hacke, J.S. Stein, L. Bruckman, P. Gebhardt, D. Barrit, M. Rasmussen, I. Martin, K.O. Davis, G. Cattaneo, B. Hoex, Z. Hameiri..." (citation truncated in T13-30 reference list page 13; need to retrieve full citation).

**ERR-5 status: NOT RESOLVED by T13-30 alone.** Requires Köntges25 retrieval.

### C2 — Updated failure-mode taxonomy. **VERIFIED — 30 fact sheets.**

Table 2 (page 12) lists 30 PVFS organized by component:

**PV module (20 fact sheets):** 1-1 Cell cracks · 1-2 Discolouration of encapsulant or backsheet · 1-3 Front delamination · 1-4 Backsheet delamination · 1-5 Backsheet cracking · 1-6 Backsheet chalking (whitening) · 1-7 Burn marks · 1-8 Glass breakage · 1-9 Cell interconnection failure · 1-10 Potential induced degradation · 1-11 Metallisation discolouration/corrosion · 1-12 Glass corrosion or abrasion · 1-13 Defect or detached junction box · 1-14 Junction box interconnection failure · 1-15 Missing or insufficient bypass diode protection · 1-16 Not conform power rating · 1-17 Light induced degradation in c-Si modules · 1-18 Insulation failure · 1-19 Hot spot (thermal patterns) · 1-20 Soiling

**Cables and interconnectors (4):** 2-1 DC connector mismatch · 2-2 Defect DC connector/cable · 2-3 Insulation failure · 2-4 Thermal damage in combiner box

**Mounting (3):** 3-1 Bad module clamping · 3-2 Inappropriate/defect mounting structure · 3-3 Module shading

**Inverter (3):** 4-1 Overheating (temperature derating) · 4-2 Incorrect installation · 4-3 Complete failure (not operating)

Page 12 notes: "The list does not pretend to be exhaustive or updated."

### C3 — New failure modes beyond T13-09 taxonomy. **PARTIAL.**

T13-30:2025 includes failure modes that were either absent from T13-09:2017 or covered in less detail:
- Backsheet chalking/whitening (1-6) — explicit fact sheet
- Glass corrosion / abrasion (1-12)
- Detached junction box (1-13) as distinct from junction box interconnection failure (1-14)
- Missing/insufficient bypass diode protection (1-15)
- "Not conform power rating" (1-16) — manufacturing-batch/bankability issue
- DC connector mismatch (2-1) — distinct from connector defect
- Thermal damage in combiner box (2-4)

**Not explicitly covered in T13-30 fact sheets:**
- LeTID (light + elevated temperature degradation in PERC) — referenced inside fact sheet 1-17 (LID) but no dedicated LeTID sheet
- TOPCon-specific UV-induced degradation — not as a standalone sheet
- HJT-specific failure modes — not as a standalone sheet
- Perovskite-tandem stability — not covered (this is a c-Si-fielded-fleet review)

### C4 — CRITICAL — climate-failure correlation. **NOT IN THIS DOCUMENT.**

T13-30:2025's structure is fact-sheet-per-failure-mode with severity ratings; it does NOT carry climate-failure correlation analysis. Such analysis would live in the technical companion `[Köntges25]`.

The PVFS does cite Köntges17 (T13-09:2017) directly + Köntges25 — when both are cited together, the T13-30 framing remains "summarize failure modes; field-data discussion deferred to companion." **No climate-correlation language quoted from T13-30 body.**

**ERR-5 status: requires Köntges25 retrieval.** The hypothesis that 2025 N changes the 2017 no-strong-correlation finding is testable in Köntges25, not in T13-30.

### C5 — Updated failure-impact ranking. **DIFFERENT-IN-DOCUMENT — new framework.**

T13-30:2025 introduces a 5-category performance severity scale (page 8) replacing T13-09's earlier ranking format:

| Performance category | Description | Expected power loss |
|---|---|---|
| 1 (low) | No direct effect on performance | 0% degradation |
| 2 | Minor impact | Below detection limit (<2-3%) |
| 3 | Moderate impact | Power degradation within warranty (<0.7-1%/year) |
| 4 | High impact | Power degradation out of warranty (>0.7-1%/year) |
| 5 (catastrophic) | Catastrophic impact | >3%/year |

Plus a 3-category safety scale (fire / electrical shock / physical danger).

**This is itself a useful claim for the substrate:** the 0.7-1%/year boundary is explicitly identified as the warranty threshold; the >3%/year boundary is catastrophic. v0's mention of "module manufacturer warranty curves" is now anchored to a concrete reference.

### C6 — AAA-backsheet recall cohort. **COVERED in PVFS 1-5 (Backsheet cracking) + 1-4 (Backsheet delamination).**

Visible at TOC level; fact sheet bodies have failure descriptions + severity. Specific peer-reviewed prevalence numbers not in PVFS-format; in companion Köntges25 if present.

### C7 — Bifacial reliability. **NOT EXPLICITLY listed in TOC.**

Bifacial-specific failure modes (rear-side soiling, non-uniform rear illumination thermal stress, hot-spot at rear) are not listed as standalone fact sheets. They may appear inside related sheets (1-19 Hot spot, 1-20 Soiling) but no dedicated bifacial fact sheet.

### C8 — Inverter vs module attribution. **NOT QUANTITATIVELY ADDRESSED.**

T13-30 covers inverter failure modes (4-1, 4-2, 4-3) but does NOT compute energy-loss attribution between inverter vs module. That analysis lives in companion technical reports + fleet-monitoring databases (RdTools, DNV, etc.).

## Climate methodology

Per page 6 reference list: T13-30:2025 cites Köntges17 (which used Köppen-Geiger), Schill21 (T13-21 Soiling), Herrmann21 (T13-24 PV Plant Qualification), Herz22 (T13-23 Technical Risks). The Task 13 documents index page hosts a **Köppen-Geiger geo-data translation tool** as a 2025-current artifact, indicating Köppen-Geiger remains the active climate framework for Task 13 field surveys.

## Datasets + access

T13-30:2025 itself does not release underlying field-data tables. Task 13 documents index continues to host:
- `fsurvey.xlsm` — Failure survey spreadsheet (template for data contribution)
- PV-System Survey sheet explanation (PDF)
- Köppen-Geiger geo-data translation tool

**No public row-level field-failure database** is released as supplementary to T13-30. Aggregated tables would be in Köntges25 if present.

## Cross-reference to T13-09

T13-30:2025 references T13-09 (Köntges17) directly as one of seven prior Task 13 reports used as source material. T13-30 does NOT explicitly compare its findings to T13-09 because T13-30's content is fact-sheet descriptive, not survey-statistical. Direct comparison must wait for Köntges25.

## Notes for substrate landscape revision

1. **30-failure-mode taxonomy** is the canonical 2025 reference; replace v0's ~10-mode list with this 30-mode list in `05_LANDSCAPE_RELIABILITY_v0.md`.
2. **5-category performance severity framework + 3-category safety framework** is the new severity standard from 2025; cite when discussing failure-mode severity.
3. **Warranty threshold concrete number:** **0.7-1%/year** is the conventional warranty boundary (T13-30 page 8); **>3%/year** is catastrophic. Use these for any "outperforms warranty" claims.
4. **ERR-5 still open.** The "climate-failure correlation" question requires Köntges25 — file a v3 verification pass.
5. **Bifacial / TOPCon / HJT / perovskite reliability** is NOT covered as standalone fact sheets in T13-30; these remain open for v3+ work even after Köntges25 is verified.

## Ledger impact (applies on operator endorsement)

- New entry: **CLM-T13-30-1** — 2025 PVFS taxonomy lists 30 failure modes across 4 component categories. VERIFIED.
- New entry: **CLM-T13-30-2** — Warranty threshold for module power degradation: 0.7-1%/year per T13-30:2025 severity framework. VERIFIED.
- New entry: **CLM-T13-30-3** — Catastrophic degradation threshold: >3%/year. VERIFIED.
- **CLM-005 (climate-specific aging)** — STAYS PARTIAL until Köntges25 is verified.

## Open follow-ups

- F1: **Retrieve Köntges25 — full citation needed.** The T13-30 reference list (page 13-14) truncated the citation at the page break. Read T13-30 pages 13-14 fully OR search IEA-PVPS for the post-T13-30 Task 13 report listing.
- F2: Verify the AAA-backsheet recall cohort with concrete prevalence numbers (likely in Köntges25 or referenced literature).
- F3: Verify the Jordan 2022 fleet paper (pip.3566) for climate-stratified field PLR (-0.48%/yr cool / -0.88%/yr hot).
- F4: Check whether bifacial / TOPCon / HJT / perovskite reliability gets fact-sheet coverage in newer T13-31:2026 or similar.

## Sources

- Local PDF: `D:/Renewables/Solar/data/raw/papers/Kontges2025_T13-30_PVFS.pdf`
- Original URL: https://iea-pvps.org/wp-content/uploads/2025/02/IEA-PVPS-T13-30-2025-PVFS-ANNEX-Degradation-and-Failure.pdf
- Task 13 documents index: https://iea-pvps.org/research-tasks/reliability-and-performance-of-pv-systems/task-13-documents/
