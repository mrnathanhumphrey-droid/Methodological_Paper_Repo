# 04 — Degradation Research Landscape v0

> **🔴 SUPERSEDED FOR HEADLINE CITATIONS — see `02_CLAIMS_LEDGER.md` + verification memos `08_`, `13_`, `16_`.**
>
> **Corrections established by verification passes v1+v2 (2026-05-27):**
> - **ERR-1 (CLM-001):** v0 said "median c-Si degradation ≈ 0.5%/yr (Jordan-Kurtz 2013)." Correct: the 0.5%/yr is **all-technology median**, not c-Si specific (Jordan-Kurtz 2013 NREL preprint local PDF + verification memo `08_`). The c-Si-specific cut comes from Jordan 2016 Compendium.
> - **ERR-2 (CLM-002):** v0 said "c-Si mean 0.8-0.9%/yr (Jordan-Kurtz 2013)." Correct: this figure originates in **Jordan et al. 2016 Compendium** (DOI 10.1002/pip.2744), NOT 2013. Verification memo `13_`.
> - **Modern canonical citation:** For field PLR today, cite **Jordan et al. 2022** (pip.3566) at **-0.75%/yr system-level median**, n=4915 inverters / 1700 sites / 7.2 GW. Verification memo `16_`. The 2016 Compendium's 0.5-0.6%/yr is module-level historical; the 2022 system-level number is intrinsically higher by ~0.15-0.25%/yr by construction.
> - **Climate-failure correlation IS NOW ESTABLISHED:** Jordan 2022 finds p<0.001 temperature-PLR correlation in Al-BSF c-Si ground-mounted fleet (T3 cool -0.48 → T5 hot -0.88 %/yr). v0's framing of "climate-specific aging" is correct in direction but cite Jordan 2022 + Karin et al. 2019 PV-specific climate zones (NOT Köppen-Geiger). Verification memo `16_`.
> - **LeTID is now largely resolved at cell-tech level** per T13-30:2025 REPORT EX-SUMM (Boron→Gallium doping + thin wafers + lower-impurity wafers + standard test procedures available). Verification memo `15_`. v0 listed it as open question — downgrade to "active but largely solved."
> - **NEW open questions identified from T13-30:2025 EX-SUMM:** TOPCon + SHJ UVID (outdoor reversibility unclear); thin-glass (≤2 mm) glass/glass module breakage 5-10% in first 2 years; perovskite MHP stability (multiple solutions but no single-process resolution).
>
> All other v0 claims remain NEEDS-VERIFICATION until processed through meta-pre-reg §3.

> **STATUS:** NEEDS-VERIFICATION per `01_METAPREREG_v1.0` §8. LLM-surfaced citation
> leads from subagent run 2026-05-27. Every DOI / report ID requires independent
> retrieval before any claim moves to VERIFIED. UNVERIFIED-LEAD tags mark items
> with explicit lower confidence.

# Solar PV Module Degradation — Research-Landscape Inventory (NEEDS-VERIFICATION)

**Scope note:** All citations below are LLM-surfaced leads. Researcher must verify each DOI/URL before treating as primary source. "UNVERIFIED-LEAD" tags mark claims where I have lower confidence the exact citation resolves.

---

## 1. Research clusters

### 1a. NREL PV Reliability / Field Performance group
Lead figures: **Dirk Jordan, Sarah Kurtz (now UC Merced), Chris Deline, Michael Deceglie, Ingrid Repins**. Long-running degradation-rate meta-analysis lineage; PV Fleet Performance Data Initiative.
- Jordan, Deline, Kurtz et al., "Robust PV Degradation Methodology and Application," *IEEE J. Photovoltaics* (2018). DOI: 10.1109/JPHOTOV.2017.2779779
- Jordan et al., "PV Field Reliability Status — Analysis of 100,000 solar systems," *Prog. Photovolt.* (2020). DOI: 10.1002/pip.3262
- Deceglie, Jordan, Springer et al., "Quantifying soiling loss directly from PV yield," *IEEE J. Photovoltaics* (2018). DOI: 10.1109/JPHOTOV.2018.2784682 (older but canonical; newer PV Fleet papers 2022-2024 build on it — UNVERIFIED-LEAD for specific 2024 follow-ups)

### 1b. Fraunhofer ISE / Köntges (ISFH) / IEA-PVPS Task 13
Lead figures: **Marc Köntges (ISFH), Ulrike Jahn (formerly TÜV Rheinland/IEA-PVPS), Magnus Herz, Karl Berger (AIT)**. Failure-mode taxonomy and field-survey methodology.
- Köntges et al., "Review of Failures of Photovoltaic Modules," IEA-PVPS T13-01:2014 (foundational; report at iea-pvps.org). UNVERIFIED-LEAD for exact PDF URL stability.
- Jahn et al., "Assessment of Photovoltaic Module Failures in the Field," IEA-PVPS T13-09:2017.
- IEA-PVPS Task 13 ongoing reports 2021-2024 on bifacial degradation, PID, snail tracks — UNVERIFIED-LEAD for specific report numbers post-2022.

### 1c. DuraMAT consortium (DOE, US)
Lead figures: **Teresa Barnes (NREL, DuraMAT director), Laura Schelhas, Peter Hacke, Bill Marion**. Materials-level reliability, encapsulant browning, backsheet failures, accelerated-stress-to-field correlation.
- Hacke et al., "A status review of photovoltaic power conversion equipment reliability," *Renewable & Sustainable Energy Reviews* (2018). DOI: 10.1016/j.rser.2017.10.043
- Schelhas et al., on backsheet degradation chemistry — 2021-2023 *Solar Energy Materials and Solar Cells* run. UNVERIFIED-LEAD for exact DOI.

### 1d. CWRU SDLE (Solar Durability and Lifetime Extension)
Lead figure: **Roger French**. Data-science / ML approaches to outdoor-exposure datasets; Hadoop-style framework for large-N module monitoring.
- French et al., "Degradation pathways of photovoltaic systems: A multi-modal multi-scale data analytic perspective," recurring *Solar Energy* / *Prog. Photovolt.* papers 2020-2023. UNVERIFIED-LEAD for specific DOI.

### 1e. PID / LeTID / LID mechanism groups
Lead figures: **Skoczek (JRC-Ispra), Pingel (formerly SolarWorld), Luka (UL Ljubljana), Niewelt (Fraunhofer ISE), Hallam (UNSW)**. Cell-level recoverable-degradation mechanisms.
- Skoczek, Sample, Dunlop, "The results of performance measurements of field-aged crystalline silicon photovoltaic modules," *Prog. Photovolt.* (2009) — older but canonical baseline. DOI: 10.1002/pip.875
- Niewelt et al. on LeTID kinetics in *Solar Energy Materials and Solar Cells* 2021-2023. UNVERIFIED-LEAD.
- Hallam group (UNSW) on hydrogen-mediated LeTID — multiple 2020-2024 papers. UNVERIFIED-LEAD.

### 1f. Perovskite / tandem stability (emerging cluster, distinct from Si)
Lead figures: **Snaith (Oxford), McGehee (CU Boulder), Ginger (UW), Saliba (Stuttgart)**. ISOS protocols for perovskite-stability reporting.
- Khenkin et al., "Consensus statement for stability assessment and reporting for perovskite photovoltaics based on ISOS procedures," *Nature Energy* (2020). DOI: 10.1038/s41560-019-0529-5

---

## 2. Established findings (each NEEDS-VERIFICATION)

| Finding | Canonical citation | Notes |
|---|---|---|
| Median c-Si degradation ≈ 0.5–0.8 %/yr; mean ≈ 0.8–0.9 %/yr; distribution is long-tailed | Jordan & Kurtz, "Photovoltaic Degradation Rates — an Analytical Review," *Prog. Photovolt.* (2013). DOI: 10.1002/pip.1182 | Updated in Jordan et al. *Prog. Photovolt.* 2016 (DOI: 10.1002/pip.2744) and 2022 PV Fleet (UNVERIFIED-LEAD for exact 2022 DOI). |
| Thin-film (CdTe, CIGS) degradation rates broadly comparable to c-Si in modern modules, but with wider spread and stabilization transients | Jordan et al. 2016 (above); Strevel/Gostein on CdTe field behavior | UNVERIFIED-LEAD for Strevel specific DOI. |
| Hot/humid climates accelerate degradation roughly 2x vs. moderate climates | Jordan, Silverman, Sekulic, Kurtz, "PV Degradation Curves: Non-Linearities and Failure Modes," *Prog. Photovolt.* (2017). DOI: 10.1002/pip.2835 | Mechanism: encapsulant + backsheet hydrolysis. |
| Backsheet failures (PA, AAA) emerged as dominant field-failure mode for ~2010-2015 vintage modules | DuraMAT / Schelhas group, multiple papers 2019-2022 | UNVERIFIED-LEAD for specific DOI. |
| Module power-warranty curves underestimate real-world degradation tail (top decile >1.5 %/yr) | Jordan PV Fleet 2022 (UNVERIFIED-LEAD) | Bankability implication. |
| LID (boron-oxygen) typically saturates at ≈1-3 % within first weeks of operation in p-type c-Si | Bothe & Schmidt, *J. Appl. Phys.* (2006). DOI: 10.1063/1.2140584 | Older but canonical; mitigated in modern n-type / Ga-doped p-type. |
| LeTID in PERC modules: 1-6 % power loss over 1-3 years under field temperatures | Kersten et al., *Solar Energy Materials and Solar Cells* (2015) — DOI: 10.1016/j.solmat.2015.06.015 | Magnitude depends strongly on cell process; mechanism still debated. |

**Where sources disagree:** Magnitude of recent (post-2015) c-Si degradation rates — some PV Fleet analyses suggest improvement to ~0.4 %/yr median, others (commercial asset-management databases, e.g., kWh Analytics) report higher. This is an active disagreement.

---

## 3. Open research questions

1. **What fraction of "degradation" measured in field analytics is irreversible vs. seasonally / soiling-confounded?** Obstacle: separating soiling, spectral-mismatch seasonal artifacts, inverter clipping, and true module aging in production monitoring data. 2024-2026 efforts: NREL RdTools open-source toolkit refinements; PV Fleet methodology v2 (UNVERIFIED-LEAD for specific 2024 release).
2. **LeTID mechanism — is hydrogen the carrier or co-defect?** Obstacle: mechanism ambiguity; competing UNSW (hydrogen) vs. Fraunhofer (B-related) models. Recent: Hallam group hydrogen-injection studies 2021-2024 (UNVERIFIED-LEAD).
3. **Bifacial module degradation rates** — limited multi-year field data because deployment is recent (post-2018 scale). Obstacle: data scarcity. IEA-PVPS Task 13 surveys ongoing.
4. **Glass-glass vs. glass-backsheet long-term reliability difference** — vendors claim glass-glass advantage, field validation incomplete. Obstacle: vintage modules (>10yr) are predominantly glass-backsheet; G-G fleet too young.
5. **PID-s vs. PID-p vs. PID-c distinction in n-type TOPCon and HJT** — new cell architectures show new PID modes. Obstacle: industry-vintage modules entering field 2022-2024, no long-term data. JRC-Ispra and TÜV groups active.
6. **Perovskite / perovskite-Si tandem field stability vs. accelerated-test extrapolation** — ISOS protocols define lab tests but field-to-lab correlation unproven for perovskite. Obstacle: no multi-year fielded perovskite fleet. McGehee, Oxford PV groups.
7. **EVA vs. POE vs. TPO encapsulant aging under realistic UV doses** — accelerated UV tests do not reproduce field failure spectra. Obstacle: measurement (UV-dose dosimetry in field). DuraMAT and Fraunhofer ISE work ongoing.
8. **Inverter degradation contribution to system-level yield loss** — most degradation literature focuses on modules; inverter capacitor + IGBT aging less characterized. Obstacle: instrumentation; module and inverter losses confounded in DC-side data.

---

## 4. Datasets / public data resources

| Dataset | Owner | Access | Contents |
|---|---|---|---|
| **NREL PVDAQ** (PV Data Acquisition) | NREL / OEDI | Open; via OEDI portal (data.openei.org/submissions/4568) | Multi-year DC/AC + irradiance for ~50+ systems; mixed module technologies. UNVERIFIED-LEAD for exact site count post-2023. |
| **DuraMAT Data Hub** | LBNL / NREL | Open with registration; datahub.duramat.org | Module-level accelerated test results, materials characterization, fielded module imagery. |
| **IEA-PVPS Task 13 field-failure database** | IEA-PVPS | Reports public; underlying data partly restricted | Failure-mode incidence by climate/vintage. |
| **PV Fleet Performance Data Initiative** | NREL + industry partners | Aggregated results public; raw data restricted to consortium | >300 GW analyzed (UNVERIFIED-LEAD for current scale); degradation-rate distributions. |
| **CWRU SDLE outdoor exposure data** | CWRU | Partly public via SDLE Research Center | Multi-year I-V curves on test modules; EL/UV-F imagery. |
| **OEDI Solar repository** | DOE OEDI | Open | Umbrella for several DOE-funded datasets. openei.org/wiki/Solar_Energy_Data |
| **Sandia Regional Test Centers** | Sandia | Mixed access | Outdoor module test data across 5 US climates. UNVERIFIED-LEAD for current public-access status. |
| **PV Lifetime project (Fraunhofer CSE legacy)** | Now under DuraMAT | Partly archived | Outdoor I-V on commercial modules across US climates. |

**Gap:** No large open dataset of inverter-side telemetry paired with module I-V at multi-year scale. This is white-space.

---

## 5. Methodology trends

- **EL (electroluminescence) imaging** — moving from lab to drone-based field deployment. Key groups: ISFH (Köntges), CFV Labs. Automated crack/finger-break detection via CNNs. UNVERIFIED-LEAD for canonical 2023-2024 review.
- **UV fluorescence (UV-F)** imaging — encapsulant browning and crack detection in field; rapid drone surveys. Köntges and CFV Labs publications.
- **IV-curve fingerprinting / RdTools** — open-source Python toolkit from NREL (github.com/NREL/rdtools); year-on-year (YoY) degradation estimation with statistical CIs. Deceglie et al. canonical methodology.
- **Machine learning on production-monitoring data** — CWRU SDLE pipeline; PV Fleet aggregation. Active subfield: separating soiling from module aging via change-point models.
- **Daylight EL / outdoor EL** — emerging technique to image strings under sunlight without inverter shutdown. UNVERIFIED-LEAD for specific 2023-2024 papers (groups: ISFH, CFV Labs, BT Imaging).
- **Hyperspectral and PL (photoluminescence) imaging** — moving from cell-process QC to module-level field diagnostics.
- **Digital-twin / physics-informed degradation models** — coupling materials kinetics (Arrhenius + humidity factors) to field statistics. DuraMAT and CWRU active.
- **Drone-based aerial thermography at scale** — commercial (Raptor Maps, Heliolytics) outpacing academic literature; defect-classification taxonomies converging with IEA-PVPS T13.

**Underserved methodology areas (potential white-space):** (a) standardized cross-lab EL image benchmarks with ground-truth labels (analogous to ImageNet for defect classification); (b) inverter-side fingerprinting of module degradation modes; (c) open accelerated-to-field correlation datasets where the SAME modules are stressed in chamber and then deployed.

---

**Final caution to verifier:** roughly 30-40% of citations above are tagged or implicitly UNVERIFIED-LEAD because exact DOI resolution is not guaranteed. Treat the entire document as a search-prompt, not a bibliography. Recommended verification path: (1) Jordan/Kurtz/Deline NREL author pages; (2) IEA-PVPS Task 13 reports list at iea-pvps.org; (3) DuraMAT publications page; (4) Köntges Google Scholar; (5) DOI resolver checks on every citation before use in a pre-reg or paper.
