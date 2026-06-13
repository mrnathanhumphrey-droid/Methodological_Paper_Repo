# Verification: IEA-PVPS T13-09:2017

**Status:** Primary-source verified via WebSearch retrieval of IEA-PVPS official pages and PDF cover/abstract content. The full PDF (`170515_IEA-PVPS-report_T13-09-2017_Internetversion_2.pdf`) was located but local Bash/PowerShell download was sandbox-blocked this session — verification rests on the publisher landing page and indexed PDF content (TUV mirror, IEA-PVPS direct link, Korean translation cover sheet, Sandia/PVPMC catalog), all of which agree on identifiers.

**Operating discipline:** Per `01_METAPREREG_v1.0_evidence_discipline.md`, claims below are flagged by what is directly visible in retrieved publisher metadata/abstract vs. what would require page-level PDF reads. PDF download to `literature/pdfs/T13-09-2017.pdf` is recommended as a follow-up to firm up CAN'T-VERIFY rows.

---

## DOI / Access

- **Title (verbatim):** *Assessment of Photovoltaic Module Failures in the Field*
- **Report ID:** IEA-PVPS T13-09:2017
- **Publication:** May 2017 (PDF filename `170515_...` = 2017-05-15)
- **ISBN:** 978-3-906042-54-1
- **DOI:** none listed on IEA-PVPS page (Task 13 reports were not DOI-registered in 2017)
- **Open access:** YES — freely downloadable PDF, no paywall, no registration
- **Direct PDF:** https://iea-pvps.org/wp-content/uploads/2017/09/170515_IEA-PVPS-report_T13-09-2017_Internetversion_2.pdf
- **Landing page:** https://iea-pvps.org/key-topics/report-assessment-of-photovoltaic-module-failures-in-the-field-2017/
- **Mirror:** TUV (https://www.tuv.com/content-media-files/master-content/services/products/p06-solar/solar-downloadpage/report-iea-pvps-t13-09_2017_assessment-of-pv-module-failures-in-the-field.pdf); Korean translation hosted by IEA-PVPS (2021-03)

## Authorship — CORRECTION TO TARGET CITATION

The target citation lists **Jahn, U.** as lead. **The actual lead author is Marc Köntges** (Institute for Solar Energy Research Hamelin, ISFH, Emmerthal, Germany). Jahn is the third-listed author. The "commonly attributed to Köntges et al." parenthetical in the prompt is the correct attribution.

**Author list as printed (publisher metadata):**
- Marc Köntges (ISFH, Germany) — **lead**
- Gernot Oreski (Polymer Competence Center Leoben GmbH, Austria)
- Ulrike Jahn (TÜV Rheinland Energy GmbH, Cologne, Germany)
- Magnus Herz (TÜV Rheinland Energy GmbH, Cologne, Germany)
- Peter Hacke (NREL, Golden, CO, USA)
- Karl-Anders Weiss (Fraunhofer ISE, Freiburg, Germany)
- Guillaume Razongles (CEA-INES, France)
- Marco Paggi (IMT School for Advanced Studies Lucca, Italy)
- David Parlevliet (Murdoch University, Australia)
- Tadanori Tanahashi (AIST, Japan)
- Roger H. French (Case Western Reserve University, USA)

Recommended in-text cite: **Köntges, M., Oreski, G., Jahn, U., Herz, M., et al., 2017.**

---

## Per-Claim Verdicts

### C1 — Canonical failure-mode taxonomy
**VERIFIED-IN-REPORT (with nuance).** Together with predecessor T13-01:2014, T13-09:2017 is the canonical IEA-PVPS field-failure reference and is cited as such by the 2023 and 2025 PVFS follow-ons and by T13-30:2025. Strictly, T13-01:2014 *established* the taxonomy and the formal failure definition; T13-09:2017 *extends* it with field-observation impact rankings. Phrase as "extends the IEA-PVPS canonical taxonomy" rather than "establishes."

### C2 — Failure modes covered
**MOSTLY VERIFIED.** Publisher abstract and indexed content explicitly list: delamination, backsheet adhesion loss, junction-box failure, frame breakage, EVA discolouration, cell cracks, snail tracks/trails, burn marks, potential-induced degradation (PID), disconnected cell and string interconnect ribbons, defective bypass diodes, plus thin-film-specific failures (micro-arcs at glued connectors, shunt hot spots, front-glass breakage, back-contact degradation).

Per-item:
- cell cracks — VERIFIED
- PID — VERIFIED (PID-s discussed with temperature-dependent precursors)
- backsheet failure — VERIFIED (adhesion loss); polyamide/AAA-specific failure mode **NOT-CONFIRMED in abstract** (PA-backsheet field-failure crisis became prominent post-2017; likely treated generally not by polymer chemistry — CAN'T-VERIFY without PDF page check)
- junction box failure — VERIFIED
- EVA browning/discolouration — VERIFIED
- snail trails — VERIFIED
- hotspots — VERIFIED (shunt hot spots, thin-film section)
- glass breakage — VERIFIED (front-glass breakage)
- delamination — VERIFIED
- bypass diode failure — VERIFIED
- **LeTID — NOT-FOUND in retrieved metadata.** LeTID was newly named in 2015–2016; whether T13-09 covers it explicitly is **CAN'T-VERIFY without PDF**. Treat as likely absent or only briefly mentioned.

### C3 — Prevalence data, methodology, sample size, geographic scope
**PARTIALLY VERIFIED.** Report ranks failures by impact (power loss when present) rather than pure prevalence. Stated headline rank (independent of climate): **PID > bypass-diode failure > cell cracks > encapsulant discolouration.** Methodology = aggregated field observations contributed by Task 13 expert participants across member countries (≥10 countries via author affiliations: DE, AT, US, FR, IT, AU, JP). **Exact sample size (modules / plants / MW inspected) — CAN'T-VERIFY without PDF page-level read.** Geographic scope = international IEA-PVPS member set; per-country counts not visible in metadata.

### C4 — Climate-zone classification
**DIFFERENT-IN-REPORT.** Report does attempt climate stratification using **Köppen–Geiger** zones (not the simpler hot/humid–arid–temperate trichotomy in the prompt). Key finding: **"the results do not show a strong correlation of the observed failure occurrences and impacts with the Köppen and Geiger climatic zones"** — authors flag dataset size as limiting and call for larger future datasets. Cite this as "Köppen–Geiger stratification attempted; no strong climate–failure correlation at 2017 dataset size."

### C5 — Predecessor T13-01:2014 and what T13-09 adds
**VERIFIED.** Predecessor: **IEA-PVPS T13-01:2014, *Review of Failures of Photovoltaic Modules*** (https://iea-pvps.org/wp-content/uploads/2020/01/IEA-PVPS_T13-01_2014_Review_of_Failures_of_Photovoltaic_Modules_Final.pdf). T13-09:2017 explicitly carries forward T13-01's formal definition of PV-module failure (power-degrading or safety-creating; cosmetic excluded) and extends with: (a) field-observed impact rankings, (b) Köppen–Geiger climate-zone analysis, (c) expanded thin-film section, (d) updated treatment of PID, snail tracks, and bypass-diode failure.

---

## Subsequent Task 13 Reports (post-2017, failure-relevant)

- **T13-21:2022** — *Soiling Losses in PV Plants* (adjacent; loss mechanism not failure)
- **T13-23:2021** — *Quantification of Technical Risks in PV Power Systems* (risk-framework follow-on)
- **T13-25:2022** — *Guidelines for Operation and Maintenance of PV Power Plants in Different Climates*
- **T13-26:2024** — *Best Practices for the Optimization of Bifacial PV Tracking Systems*
- **T13-27:2024** — *Performance of Partially Shaded PV Generators*
- **T13-29:2025** — *Degradation and Failure Modes in PV Cell and Module Technologies* (ISBN 978-3-907281-71-0) — explicit successor on degradation/failure
- **T13-30:2025** — *Photovoltaic Failure Fact Sheets (PVFS) 2025* — direct field-failure successor; supersedes T13-09 for current-generation tech
- **PVFS 2023** (pre-print at `pvlab.solar/.../DB_PV-Failure-Fact-Sheets-2023.pdf`) — interim fact-sheet update referencing T13-09:2017

**Operational implication:** for any 2026 deployment-side claims, cross-cite T13-09:2017 (canonical) **with T13-29:2025 / T13-30:2025 (current)**. T13-09 alone is now 9 years old; mainstream cell/module tech (PERC ubiquity, TOPCon, HJT, large-format wafers, glass-glass) has shifted the failure profile.

## Datasets / Field-Failure Databases

- **No public IEA-PVPS field-failure dataset.** Task 13 contributions are member-confidential; only aggregated rankings/figures appear in reports.
- **No DOI dataset deposit** referenced in publisher metadata.
- **PVFS (2023, 2025)** are the only public-facing structured per-failure-mode artifacts and they are document fact sheets, not row-level datasets.
- External datasets that pair with T13-09 framing (not endorsed by it, but commonly cross-referenced): NREL PV Module Reliability Workshop proceedings, Sandia PV Lifetime Project, DuraMAT data hub. **None of these are claimed by T13-09:2017 itself** — flag as separate sources if cited.

## Disagreements with Target Citation

1. **Lead author:** target says Jahn; actual is **Köntges**. Use Köntges as lead in any reference list.
2. **C4 climate trichotomy:** target asks hot/humid vs arid vs temperate; report uses **Köppen–Geiger** and reports **no significant correlation** — frame carefully.
3. **C2 specifics:** **PA/AAA backsheet** chemistry and **LeTID** are NOT visibly confirmed from indexed metadata. Treat as CAN'T-VERIFY until PDF page read; do NOT cite T13-09 as the primary source for either.

## Follow-Ups (pre-cite-locking actions)

1. **Local PDF retrieval** to `D:/Renewables/Solar/literature/pdfs/T13-09-2017.pdf` (sandbox blocked this session — re-attempt with permission).
2. **Page-level verification** of: (a) LeTID coverage, (b) PA-backsheet treatment, (c) exact sample size N for the prevalence/impact tables, (d) the Köppen–Geiger-stratified figures.
3. **Always pair-cite** T13-09:2017 with **T13-29:2025** and/or **T13-30:2025 (PVFS)** for any current-tech claim.
4. **Predecessor in-line cite** T13-01:2014 (Köntges et al.) whenever invoking the definitional framing of "module failure."

---

**Memo file:** `D:/Renewables/Solar/literature/02_VERIFICATION_T13-09-2017_IEA-PVPS.md`
**Verification status:** publisher-metadata level; PDF page-level pass pending.
