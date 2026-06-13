# 05 — Field Reliability Research Landscape v0

> **🔴 SUPERSEDED FOR HEADLINE CITATIONS — see `02_CLAIMS_LEDGER.md` + verification memos `09_`, `14_`, `15_`.**
>
> **Corrections established by verification passes v1+v2 (2026-05-27):**
> - **ERR-4:** v0 cited "Jahn et al. T13-09:2017." Correct: **Köntges, M.** is lead author; Jahn is 3rd author. Use Köntges, Oreski, Jahn, Herz, Hacke, Weiß, Razongles, Paggi, Parlevliet, Tanahashi, French 2017. ISBN 978-3-906042-54-1. Verification memo `09_`.
> - **ERR-5 (was OPEN, NOW CLOSED):** v0 said "climate-specific aging is established." T13-09:2017 itself found **no strong climate-failure correlation at 2017 N** using Köppen-Geiger zones. **However, Jordan et al. 2022 fleet paper at much larger N (4915 inverters / 1700 sites) DOES find statistically significant temperature-PLR correlation at p<0.001** in Al-BSF c-Si ground-mounted fleet. So climate correlation IS established — but cite Jordan 2022 + Karin et al. 2019 PV-specific climate zones (NOT Köppen-Geiger), NOT T13-09:2017. Verification memos `09_` + `16_`.
> - **Updated 2025 failure-mode taxonomy:** T13-30:2025 PVFS lists **30 failure modes** across 4 component categories (PV module 20, cables 4, mounting 3, inverter 3). Replace v0's ~10-mode partial list with this canonical 30-mode list. Verification memo `14_`.
> - **New 5-category performance + 3-category safety severity framework** from T13-30:2025 PVFS. Concrete warranty boundary = **0.7-1%/year**; catastrophic threshold = **>3%/year**.
> - **NEW failure modes surfaced for 2020s cohorts** (from T13-30:2025 REPORT EX-SUMM): **TOPCon + SHJ UVID** (live open question on outdoor reversibility); **thin glass (≤2 mm) breakage 5-10% in first 2 years** in glass/glass modules (IEC 61215 mechanical test cannot reveal); **junction box bypass-diode contact failures** more frequent (recommendation: 100% production BPD test); **perovskite MHP stability** unresolved.
> - **NEW PID standard pending:** IEC TS 62804-1 (2025) — combined potential + light test procedure.
> - **AAA-backsheet recall cohort** confirmed in T13-30:2025 PVFS Fact Sheets 1-5 (backsheet cracking) + 1-4 (backsheet delamination).
> - **Cell cracking** mostly resolved by multi-wire technology innovation per T13-30:2025 REPORT EX-SUMM.
>
> All other v0 claims remain NEEDS-VERIFICATION until processed through meta-pre-reg §3.

> **STATUS:** NEEDS-VERIFICATION per `01_METAPREREG_v1.0` §8. LLM-surfaced citation
> leads from subagent run 2026-05-27. UNVERIFIED-LEAD tags mark items with
> explicit lower confidence.

# Solar PV Field Reliability — Research Landscape Inventory

---

## 1. Research clusters (active groups, 2020-2026)

**Sandia National Laboratories — PV Reliability & Performance Group**
Lead names: Bruce King, Joshua Stein, Laurie Burnham, Olga Lavrova.
- Stein et al., "PV Performance Modeling Collaborative (PVPMC)" — Sandia Reports series, e.g. SAND2020-3877 (**UNVERIFIED-LEAD** — report ID likely but verify on OSTI).
- Hartley et al., "PV Module Reliability Scorecard" methodology contributions — **UNVERIFIED-LEAD**.

**NREL — PV Reliability, Durability & Module Materials**
Lead names: Ingrid Repins, Michael Deceglie, Dirk Jordan, Peter Hacke, Sarah Kurtz (now UC Merced), Laura Schelhas.
- Jordan, Deceglie, Kurtz, "PV Degradation Rates — an Analytical Review," *Progress in Photovoltaics* (canonical 2013, updated 2022 cohort). DOI 10.1002/pip.2744 for original; 2022 update DOI **UNVERIFIED-LEAD**.
- Jordan et al., "Robust PV Degradation Methodology," *Progress in Photovoltaics* 2022 — DOI **UNVERIFIED-LEAD** (likely 10.1002/pip.355x range).
- Hacke et al., on PID + accelerated stress, *IEEE Journal of Photovoltaics* — **UNVERIFIED-LEAD** specific paper.

**Fraunhofer ISE / Fraunhofer CSP (Halle)**
Lead names: Harry Wirth, Karl-Anders Weiß, Daniel Philipp (ISE); Marko Turek, Matthias Pander (CSP).
- Köntges et al., "Review of Failures of PV Modules," IEA-PVPS Task 13 report T13-09:2017 (canonical pre-2020 reference still cited).
- Annual Fraunhofer ISE "Photovoltaics Report" (updated 2024/2025) — public PDF, no DOI.
- Weiß et al. on encapsulant/backsheet aging — *Solar Energy Materials and Solar Cells* — **UNVERIFIED-LEAD**.

**TÜV Rheinland**
Lead names: Werner Herrmann, Florian Reil, Willi Vaaßen.
- Contributions to IEC TC82 WG2 (module qualification). Public papers limited; conference proceedings (EU PVSEC, PVSC). **UNVERIFIED-LEAD** specific DOIs.

**IEA PVPS Task 13 — "Performance, Operation and Reliability of PV Systems"**
- "Assessment of Photovoltaic Module Failures in the Field," Report IEA-PVPS T13-09:2017 (still primary taxonomy reference).
- Task 13 subsequent reports 2020-2024 on bifacial, snail tracks, soiling — IDs in T13-xx:202x format, verify on iea-pvps.org.

**RdTools / kWh Analytics / DNV — fleet-level field analytics**
- Deceglie et al., "RdTools open-source PV degradation analysis," *IEEE PVSC* 2018 proceedings; software at github.com/NREL/rdtools.
- DNV "Solar Risk Assessment" reports (annual, 2022/2023/2024) — public PDFs, no DOI.
- kWh Analytics "Solar Generation Index" — industry report.

**Australian groups — UNSW SPREE, ANU**
Lead names: Bram Hoex, Renate Egan (UNSW); Andrew Blakers (ANU).
- LeTID mechanism work — Niewelt, Schubert et al. (Fraunhofer ISE + UNSW collaborations). **UNVERIFIED-LEAD** specific DOIs.

---

## 2. Established failure-mode taxonomy

Canonical taxonomy reference: **Köntges et al., IEA-PVPS T13-09:2017**, "Assessment of Photovoltaic Module Failures in the Field." This is the field's reference frame; cite directly rather than via LLM.

| Failure mode | Mechanism (short) | Canonical reference | Notes |
|---|---|---|---|
| Cell cracks / microcracks | Mechanical stress from handling, transport, snow load; propagate under thermal cycling | Köntges et al. T13-01:2014 "Review of Failures of PV Modules" | Prevalence figures vary widely; verify on cohort basis |
| Potential-Induced Degradation (PID) | Na+ ion migration under high system voltage; shunting at cell-glass interface | Pingel et al., *Proc. 25th EU PVSEC* 2010; Hacke et al. *IEEE JPV* — **UNVERIFIED-LEAD** DOI | IEC 62804 standardizes test |
| LeTID (Light & elevated Temperature Induced Degradation) | Hydrogen-related defect state in PERC cells | Ramspeck et al., *EU PVSEC* 2012; Niewelt et al. — **UNVERIFIED-LEAD** | Post-2017 PERC fleet issue |
| Backsheet failure (AAA / polyamide cracking) | UV + hydrolysis embrittlement of polyamide backsheets | Lyu et al. NREL; Gambogi et al. DuPont — **UNVERIFIED-LEAD** specific DOI | Major 2018-2024 field cohort issue; class-action litigation cohort |
| Junction box / connector failure | Solder joint fatigue, water ingress, arc faults | IEA-PVPS T13 reports | Fire-risk driver |
| EVA discoloration / browning | UV-induced acetic acid release; transmittance loss | Pern, Czanderna 1990s canonical | Older module cohorts |
| Snail trails | Silver paste + moisture + microcrack interaction | Köntges et al. cited above | Cosmetic + sometimes performance |
| Hotspots | Cell mismatch or partial shading + bypass diode failure | Standard textbook (Wenham, Green) | EL/IR diagnostic target |
| Inverter failure | Capacitor aging, IGBT failure, firmware faults | Sandia inverter reliability reports — **UNVERIFIED-LEAD** | Dominates O&M cost share per multiple fleet studies |
| Bypass diode failure | Thermal stress, lightning | IEC 62979 (bypass diode thermal runaway test) | |
| Glass breakage / delamination | Mechanical / thermal cycling | Köntges T13-09:2017 | |

**Post-2020 shifts (verify all):**
- **AAA-backsheet recall cohort** — polyamide-based backsheets (multiple vendors) showing accelerated cracking; warranty / litigation cohort 2019-2024. **UNVERIFIED-LEAD** for specific peer-reviewed prevalence number.
- **TOPCon-specific degradation modes** — emerging concerns about UV-induced degradation in n-type TOPCon; recent 2023-2024 papers. **UNVERIFIED-LEAD**.
- **HJT (heterojunction)** — reportedly lower temperature coefficient, but field reliability data thin. **UNVERIFIED-LEAD**.
- **Perovskite tandem stability** — moisture, thermal, light-soak instability is the central open question; IEC 61215 not yet validated for perovskites. Active area: Snaith group (Oxford), Sargent group (Toronto/Northwestern), McGehee (CU Boulder).

---

## 3. Open research questions

1. **Accelerated-test-to-field-life translation factor.** IEC 61215 sequences (TC200, DH1000, UV) do not map cleanly to 25-year field life. Quantitative translation factors per failure mode remain disputed.
2. **Early-warning signatures from EL / I-V / thermal imaging.** Which features in baseline EL images predict 5-year degradation? Open; AI/CV methods proliferating but cross-fleet validation thin.
3. **Inverter-vs-module energy-loss attribution at fleet scale.** Several fleet studies suggest inverter availability dominates lifetime loss budget, but per-mode attribution is still inconsistent across DNV, kWh Analytics, RdTools.
4. **TOPCon UV-induced degradation magnitude.** Multiple 2023-2024 manufacturer + lab reports, no converged consensus on UV0 cohort.
5. **Perovskite-silicon tandem outdoor stability.** Lab T80 vs outdoor T80, encapsulation requirements, IEC standardization. Wide-open.
6. **Bifacial reliability under non-uniform rear illumination.** Increased thermal gradients, hotspot risk under bifacial soiling patterns. **UNVERIFIED-LEAD** as to whether this is settled.
7. **Soiling-degradation interaction.** Cementation/cementing soiling and abrasive cleaning effects on AR coatings + glass.
8. **Repowering vs replacement decision frameworks.** As 2010-2015 cohort fleets cross 10-15 years, when does module replacement pay off vs inverter-only repowering? Mostly industry whitepapers, limited peer-reviewed.

---

## 4. Standards landscape

All revision dates **NEEDS-VERIFICATION** against IEC webstore / IEEE Xplore / UL.

| Standard | Scope | Latest revision (verify) |
|---|---|---|
| IEC 61215-1 / -1-1 / -1-2 / -1-3 / -1-4 / -2 | Terrestrial PV module design qualification — crystalline Si, thin-film, etc. | 61215-1:2021, -2:2021 (verify) |
| IEC 61730-1 / -2 | PV module safety qualification | 61730-1:2016+AMD1:2023, 61730-2:2016+AMD1:2023 (verify) |
| IEC 60904 series | PV cell/module measurement (spectral response, I-V, reference cells) | Multiple parts, various revision years; -1:2020, -3:2019 (verify) |
| IEC 61853 series | PV module performance / energy rating | -1:2011, -2:2016, -3:2018, -4:2018 (verify) |
| IEC 62804-1 | PID test method (crystalline Si) | 62804-1:2015+AMD1:2020 (verify) |
| IEC 62788 series | Encapsulant / backsheet materials | Multiple parts 2016-2022 (verify) |
| IEC 62941 | Quality system for PV module manufacturing | 62941:2019 (verify) |
| IEC 63209-1 / -2 | Extended-stress testing for module reliability | -1:2021 (verify); newer additions in progress |
| IEC TS 63126 | High-temperature climate qualification beyond 61215 | TS 63126:2020 (verify) |
| IEC 62979 | Bypass diode thermal runaway | 62979:2017 (verify) |
| IEEE 1547 / IEEE 1547.1 | Distributed-resource interconnection (inverter-side) | 1547-2018 (verify) |
| UL 61730 / UL 1703 (legacy) | US module safety; UL 1703 superseded by UL 61730 | UL 61730 harmonization 2017-2018 |
| UL 3703 | Tracker safety | (verify revision) |

**Working-group activity** (all **UNVERIFIED-LEAD**, confirm at iec.ch TC82):
- IEC TC82 WG2 — module standards; revisions to 61215 sequences under discussion.
- IEC TC82 WG7 — concentrator PV (less relevant for reliability lab unless CPV in scope).
- Perovskite stability standardization — early-stage WG activity; no published IEC standard for perovskite-specific qualification as of mid-2024 to my knowledge — verify.
- IEC 63209 extended-stress series — explicit response to the gap between 61215 and field-observed degradation.

---

## 5. Methodology / instrumentation trends

- **Drone-based aerial thermal IR + RGB inspection.** Commercial (Heliolytics, Above, Raptor Maps) + academic. Standardized via IEC TS 62446-3:2017 (outdoor IR inspection). Aerial EL emerging (night-time, forward-bias). **UNVERIFIED-LEAD** on canonical aerial-EL paper.
- **Daylight / outdoor EL imaging.** Bhoopathy, Kunz et al. (Fraunhofer / UNSW collaborations). **UNVERIFIED-LEAD** DOI.
- **String- and module-level monitoring.** Module-level power electronics (MLPE) data streams enable per-module degradation tracking at fleet scale; data ownership + standardization open.
- **AI-driven anomaly detection.** Numerous 2021-2024 papers on CNN classifiers for EL defect detection; cross-fleet generalization is the open problem (parallels physics_detector cross-corpus issues — relevant lab capability).
- **PL (photoluminescence) imaging in-line.** Manufacturing QC; field application emerging.
- **UV fluorescence imaging.** Detects encapsulant degradation pre-power-loss. Fraunhofer ISE / CSP work. **UNVERIFIED-LEAD**.
- **Hyperspectral / multispectral aerial.** Soiling characterization + backsheet condition. Emerging.
- **Acoustic emission + lock-in thermography.** Lab-side crack detection; less field-deployed.
- **Digital twins / physics-informed degradation models.** RdTools + commercial (DNV, kWh Analytics) trend toward Bayesian fleet-level degradation inference.

---

## Recommended verification path

1. Pull IEA-PVPS T13-09:2017 directly from iea-pvps.org — anchors taxonomy.
2. Pull Jordan/Deceglie *Progress in Photovoltaics* degradation-rate review series via Wiley — anchors field degradation distribution.
3. Pull IEC TC82 WG2 current work-item list from iec.ch — anchors standards-revision white-space.
4. Cross-check every **UNVERIFIED-LEAD** above against Google Scholar / Web of Science before citing.
5. Consider a focused literature pull of post-2022 TOPCon / HJT / perovskite-tandem reliability papers — this is the live white-space where a new lab can stake unique ground.
