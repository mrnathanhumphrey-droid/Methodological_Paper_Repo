# 15 — Verification: IEA-PVPS T13-30:2025 REPORT Executive Summary

**Verification date:** 2026-05-27
**Verifier:** operator local PDF read (downloaded via WebFetch to tool-results, copied to substrate)
**Target citation:** Köntges, M., Lin, J., Virtuani, A., Eder, G.C., Oreski, G., Hacke, P., Stein, J.S., Bruckman, L., Gebhardt, P., Barrit, D., Rasmussen, M., Martin, I., Davis, K.O., Cattaneo, G., Hoex, B., Hameiri, Z., Özkalay, E. 2025. **"Degradation and Failure Modes in New Photovoltaic Cell and Module Technologies."** IEA-PVPS Task 13, Report **IEA-PVPS T13-30:2025**, February 2025. ISBN **978-3-907281-71-0**. Editors: Köntges, Lin, Jahn.

**Importance:** This is the technical companion to the PVFS annex (verified at `14_`). It's the actual successor to T13-09:2017 "Assessment of PV Module Failures in the Field" — the document needed to resolve ERR-5. The PVFS bibliography mis-labeled this as `[Köntges25] T13-29:2025` — verified correction: it is T13-30:2025 REPORT.

## Retrieval status

- **EX-SUMM** (3 pages, executive summary): **retrieved locally** at `D:/Renewables/Solar/data/raw/papers/Kontges2025_T13-30_REPORT_ExSumm.pdf` via WebFetch from `https://www.iea-pvps.org/wp-content/uploads/2025/02/IEA-PVPS-T13-30-2025-EX-SUMM-Degradation-and-Failure.pdf`. **Full text accessible.**
- **Full REPORT PDF:** at Fraunhofer CSP mirror `https://www.csp.fraunhofer.de/content/dam/imws/csp/de/documents/task-13-reports/modul/IEA-PVPS-T13-30-2025-REPORT-Degradation-and-Failure.pdf`. Fraunhofer.de host not currently in WebFetch allowlist — operator action needed for full retrieval.
- **SLIDES:** at `https://iea-pvps.org/wp-content/uploads/2025/02/IEA-PVPS-T13-30-2025-SLIDES-Degradation-and-Failure.pdf`. Not yet retrieved.

## Citation header — CONFIRMED

| Field | Verified value |
|---|---|
| Title | "Degradation and Failure Modes in New Photovoltaic Cell and Module Technologies" |
| Report ID | IEA-PVPS T13-30:2025 |
| Publication date | February 2025 |
| ISBN | 978-3-907281-71-0 |
| Main author count | 17 |
| Lead author | M. Köntges (ISFH, Germany) |
| Editors | M. Köntges (ISFH), J. Lin (PV Guider), U. Jahn (Fraunhofer CSP Germany) |
| Task 13 managers | Ulrike Jahn (Fraunhofer CSP) + Laura Bruckman (CWRU) |

Affiliations: ISFH, PV Guider, CSEM Switzerland, OFI Austria, PCCL Austria, NREL USA, Sandia USA, CWRU USA, Fraunhofer ISE Germany, TotalEnergies France, UCF USA, UNSW Australia, SUPSI Switzerland.

## Key findings from EX-SUMM (verbatim and paraphrased)

### 1. Innovation impact on degradation
- **Cell cracking** — "the impact of cell cracking has been mostly overcome by the innovation of multi-wire technology" (page 1).
- **LID/LeTID** — "well understood and solved by switching from Boron to Gallium as a dopant for Si-wafers, by using adjusted processes in the cell production together with the use of thin wafers, and lowering the number of impurities in the wafer production. Furthermore, standard test procedures are available, so that the LID/LeTID impact on long-term performance can be tested even for innovation" (page 1).

### 2. Potential-Induced Degradation (PID)
- PID mechanisms triggerable/mitigable at cell, module, and system level.
- **Upcoming IEC TS 62804-1 (2025)** offers combined potential + light test procedure (page 2).

### 3. UV-Induced Degradation (UVID) — NEW MODE in TOPCon + SHJ cohorts
- "In some solar modules with TOPCon and SHJ cells, UVID is pronounced after accelerated aging tests" (page 2).
- "It is still unclear whether the degradation can be reversed by outdoor exposure and how the test can be transferred from laboratory to field" (page 2).
- Mitigation: reflection or absorption of UV before reaching c-Si/passivation interfaces (encapsulation strategy).
- **This is the live 2020s open research question for TOPCon/SHJ fielded cohorts.**

### 4. Encapsulant material degradation
- IEC 61215-series + safety standards focus on electrical performance, NOT polymer material stability.
- "Many PV modules are found in the field with damaged lamination material" (page 2).
- Recommendation: new combined-stress tests covering temperature + humidity + UV simultaneously (T13 sister report on combined-stress aging tests is forthcoming).

### 5. Thin glass durability (NEW finding for glass/glass cohort)
- "In practice, thin glass (thickness ≤ 2 mm) used in new glass/glass modules sometimes results in unpredictable high glass breakage rates" (page 2).
- **"In documented cases 5% to 10% of the module rear glasses broke in the first two years after installation"** (page 2).
- IEC 61215 mechanical load test cannot reveal this — requires parallel testing of tens of modules instead of one.

### 6. Junction box / bypass diode (BPD) contact failures
- "More frequently than before, it happens that electrical contacts in the junction boxes are not soldered correctly" (page 2).
- Faults can cause fires + power losses in entire module strings.
- "Unconnected BPDs are difficult to detect in PV systems that have already been installed" — recommendation: 100% BPD function check during production.

### 7. Perovskite (Metal Halide Perovskite, MHP) modules
- "Still plenty of reliability issues for perovskite-based PV module technologies in literature" (page 2).
- "There are many possible solutions, but they have not yet been evaluated in literature when combined in a single process solving all challenges at once" (page 2).
- Perovskite stability remains the central open question.

## Critical for ERR-5 (climate-failure correlation)

**The EX-SUMM does NOT directly address climate-failure correlation.** It's organized by failure mode + cell technology, not by climate. The full REPORT body (at Fraunhofer CSP, fraunhofer.de — not currently in WebFetch allowlist) may contain climate-stratified discussion in its body chapters. The EX-SUMM addresses:
- Cell-technology-specific degradation (TOPCon UVID, SHJ UVID, perovskite MHP stability)
- Innovation-driven mitigation (Boron→Gallium for LID, multi-wire for cracking, UV-stable encapsulants for UVID)
- Standards gap (IEC 61215 not catching encapsulant aging, thin-glass breakage, BPD wiring)

**ERR-5 cannot be closed by T13-30 alone**. The cleaner resolution is Jordan et al. 2022 fleet paper (pip.3566) which explicitly reports climate-stratified PLR (cool -0.48%/yr vs hot -0.88%/yr) at much larger N — that's the direct climate-correlation evidence that T13-09:2017 didn't have. In-flight subagent verifying Jordan 2022.

## Ledger impact (applies on operator endorsement)

New ledger entries from this verification:

- **CLM-TOPCon-UVID:** TOPCon + SHJ cells exhibit UVID after accelerated tests; outdoor reversibility unclear. NEEDS-LAB-WORK (no field consensus). VERIFIED-AS-OPEN-QUESTION via Köntges T13-30:2025 EX-SUMM.
- **CLM-THINGLASS-BREAK:** Thin glass (≤2 mm) in glass/glass modules — 5-10% rear breakage in first 2 years documented. VERIFIED via Köntges T13-30:2025 EX-SUMM page 2.
- **CLM-PEROVSKITE-OPEN:** MHP perovskite stability has multiple candidate solutions but none combined in single process. VERIFIED-AS-OPEN-QUESTION.
- **CLM-LeTID-RESOLVED:** LID/LeTID mitigation via Boron→Gallium doping + thin wafers + lower impurity wafers. Standard test procedures exist. VERIFIED via T13-30:2025 EX-SUMM page 1.
- **CLM-CELL-CRACK-RESOLVED:** Cell cracking impact mostly overcome by multi-wire technology innovation. VERIFIED.
- **CLM-IEC-62804-2025:** New PID test standard IEC TS 62804-1 (2025) combines potential + light procedure. VERIFIED via T13-30:2025 EX-SUMM page 2.

## Notes for substrate landscape revision

1. Update `05_LANDSCAPE_RELIABILITY_v0.md` open-questions list with TOPCon UVID + thin-glass breakage as 2020s-cohort open questions backed by Köntges T13-30:2025.
2. Update LID/LeTID open-question status from "active research" to "largely resolved at cell-tech level; standard tests available."
3. Note that perovskite stability is treated by the field as MULTI-component open problem (no single-process solution claimed yet).
4. New standard pending: IEC TS 62804-1 (2025) — add to standards inventory.

## Open follow-ups

- F1: **Get the full T13-30:2025 REPORT body PDF from Fraunhofer CSP** — needs fraunhofer.de added to WebFetch allowlist, OR operator pull. This carries the chapter-level climate analysis (if present) that closes ERR-5.
- F2: T13-30:2025 SLIDES — pull from iea-pvps.org (allowlisted) — may have summary figures (e.g., "Figure 1: Overview of test availability and impact of currently relevant degradation modes of TOPCon and SHJ module designs" referenced in EX-SUMM but not visible in EX-SUMM as a separate figure).
- F3: IEC TS 62804-1 (2025) — verify standard exists, retrieve scope, add to standards inventory.

## Sources

- Local PDF: `D:/Renewables/Solar/data/raw/papers/Kontges2025_T13-30_REPORT_ExSumm.pdf`
- Original URL: https://www.iea-pvps.org/wp-content/uploads/2025/02/IEA-PVPS-T13-30-2025-EX-SUMM-Degradation-and-Failure.pdf
- Full REPORT URL (not yet retrieved): https://www.csp.fraunhofer.de/content/dam/imws/csp/de/documents/task-13-reports/modul/IEA-PVPS-T13-30-2025-REPORT-Degradation-and-Failure.pdf
- SLIDES URL: https://iea-pvps.org/wp-content/uploads/2025/02/IEA-PVPS-T13-30-2025-SLIDES-Degradation-and-Failure.pdf
