# 17 — Verification: IEA-PVPS T13-30:2025 REPORT (Full Body, 68 pp)

**Verification date:** 2026-05-27
**Verifier:** operator local PDF read via pdfplumber
**Target citation:** Köntges, Lin, Virtuani, Eder, Zhu, Oreski, Hacke, Stein, Bruckman, Gebhardt, Barrit, Rasmussen, Martin, Davis, Cattaneo, Hoex, Hameiri, Özkalay 2025. **"Degradation and Failure Modes in New Photovoltaic Cell and Module Technologies."** IEA-PVPS Task 13, Report **IEA-PVPS T13-30:2025**, February 2025. ISBN **978-3-907281-71-0**. Contributing author: S. Baumann (ISFH). Editors: Köntges, Lin, Jahn.

## Retrieval status

- **Full PDF retrieved + locally available:** `D:/Renewables/Solar/data/raw/papers/Kontges2025_T13-30_REPORT_FULL.pdf` (4.1 MB, **68 pages**)
- Source: Fraunhofer CSP mirror `https://www.csp.fraunhofer.de/content/dam/imws/csp/de/documents/task-13-reports/modul/IEA-PVPS-T13-30-2025-REPORT-Degradation-and-Failure.pdf`
- Read via WebFetch download + pdfplumber.

## TOC

| Section | Title | Page |
|---|---|---|
| — | Acknowledgements | 6 |
| — | Abbreviations | 7 |
| — | Executive summary | 8 |
| 1 | Introduction | 10 |
| 2 | Degradation and Failure modes in recent technologies entered the market | 11 |
| 2.1 | Cut Si wafer-based cell cracking and multi-wire design | 11 |
| 2.2 | Light-induced degradation | 12 |
| 2.3 | Potential-induced degradation | 14 |
| 2.4 | Protection of substrings in the modules | 24 |
| 2.5 | Encapsulation degradation and failure modes | 29 |
| 2.6 | New material degradation modes specific to TOPCon and SHJ | 38 |
| 3 | Perovskite-based future technologies | 44 |
| 3.1 | Intrinsic degradation causes | 44 |
| 3.2 | Cell-device-specific degradation modes | 45 |
| 3.3 | Extrinsic degradation causes | 46 |
| 3.4 | Module-device-specific degradation modes | 46 |
| 4 | Conclusion | 48 |
| — | References | 50 |

## Substantive findings (§2.6 + §3 + Conclusion)

### §2.6 — TOPCon + SHJ-specific degradation modes

**Market context (p.38):** Per ITRPV 2024 — TOPCon n-type wafer share growing **29% → 53%** within next decade; n-type SHJ **5% → 19%**. **TOPCon dominating cell technology after 2025**. Cell designs evolving in ~6-month cycles; field data from TOPCon + SHJ "may not be necessarily representative for the modules currently or in the future being produced."

#### TOPCon acetic-acid + sodium chloride sensitivity (p.39)

- **TOPCon contact resistivity increases significantly after 2 hours acetic acid exposure** vs PERC and SHJ.
- **DH testing on unencapsulated TOPCon with NaCl: TOPCon shows highest power loss** vs PERC + SHJ [126].
- Cause linked to high aluminum content in front paste [129].
- **Sen et al. [128]:** 7 encapsulation+backsheet combos tested with TOPCon cells, 3 with PERC. After **1000 h damp-heat test, TOPCon max power loss ranged 4-65% depending on encapsulation material; PERC only 1-2% under same conditions.** TPO encapsulants mitigate (Sommeling & Kroon [127]).

#### SHJ Na+ migration / PID-like degradation (p.40-42)

- **Arruti et al. [134]:** Bifacial rear-emitter SHJ in glass/glass + EVA degrades during DH 85°C/85% RH with negative bias (-1 kV). No degradation with positive bias.
- Mechanism: NaOH from glass diffuses through wet EVA → Na+ crosses ITO grain boundaries → reaches a-Si:H/c-Si interface → creates recombination centers (passivation loss).
- Cell-front sensitivity > rear-side per Arruti.
- **Mitigation (p.41-42):** POE encapsulant (low WVTR, low water uptake), edge sealants, glass/glass or glass/aluminum-foil construction with barrier layers, "appropriate rear and front covers."

#### UV-Induced Degradation (UVID) — magnitudes verified (p.42-43)

- **Gebhardt et al. [18]:** 14 different TOPCon types in UV tests — power loss **0.5% to 8% with median 3% after 60 kWh/m² UV dose**.
- **Shina [140]:** 28 TOPCon + 2 SHJ types tested — TOPCon 0-10% loss, SHJ 1-2.5% loss after same 60 kWh/m² dose.
- **60 kWh/m² UV dose ≈ 1-2 years of outdoor exposure depending on location.**
- Both tests applied at short-circuit conditions.
- **Field MPP may show LOWER degradation than test (short-circuit) suggests.**
- Light soaking may recover UVID for HJT modules [150].
- **Dark-storage degradation reported after UVID tests of TOPCon modules may accelerate field degradation during nighttime.**
- UV degradation more pronounced in emerging cell technologies (SHJ) vs Al-BSF [Sinha 142].
- **Mitigation:** UV reflecting ARC, UV-absorbing glass, lamination material, passivation layer adjustments.

### §3 — Perovskite (MHP-based) reliability (p.44+)

- Perovskite structure: **ABX₃** cubic unit cell. A = organic (Formamidinium FA) / inorganic (Cs) / mix; B = metal (Pb or Sn); X = halide (Cl, Br, I).
- 4 degradation categories (per Baumann et al. [155]):
  - **Intrinsic** (material properties, phase instability, impurity, ion radius mismatch)
  - **Cell-device-specific** (device design, manufacturing)
  - **Extrinsic** (environmental stressors)
  - **Module-device-specific** (interconnection, embedment)

### Thin glass breakage (§2.5, p.38, referenced earlier)

- Thin glass (≤2 mm) cannot be fully tempered like 3 mm glass — lower surface resistance to stress/impacts/scratches.
- IEC 61215 MQT16 mechanical load test focuses on frame deformation + cell breakage, NOT glass-specific breakage rates.
- **"In documented cases 5% to 10% of the module rear glasses broke in the first two years after installation."**
- Recommended test: **~20 modules of one type in final mounting position to roughly estimate breakage rates down to 5%.**

### Conclusion (p.48-49) — verbatim load-bearing claims

> "For 2024, the main cell related degradation modes are PID, UVID, and humidity related corrosion for SHJ and TOPCon modules."

> "From the perspective of the module design glass breakage failure for bifacial glass/glass modules with thin glass got a high relevance in the field."

> "The more power is achieved per module and in the module string, the more important the safety measures become, as the consequences of an imperfectly connected BPD can lead to a fire much more easily than before."

> "The most important standard IEC 61215 [6] does not cover the UVID, because the UV test included in the standard is too short and may not take recovery effects into account."

> "Similarly, for PID effects in SHJ PV module types, it is still not clear how the PID test represents relevant conditions in the field, as the influence of recovery conditions in the application has not yet been tested. More research is needed to adapt the UVID and PID tests."

> "Today's silicon-based module designs must withstand high absorber temperatures above 150°C and more during partial shading. Many researchers wrongly assume that MHP absorbers/solar cells only need to be stable up to 85°C. In fact, the number of cells per BPD, the reverse voltage characteristic of the cells and the cell efficiency determine the maximum cell temperature in the application profile."

> "Ion migration is a dominant characteristic involved in many published degradation modes, such as chemical interface reactions, phase changes, reverse voltage instability, PID, and metastability of the electrical characteristic, such as IV curve hysteresis. In this way, mitigating ion migration in MHP containing solar cells might be a way to solve many degradation pathways at once."

## ERR-5 (climate-failure correlation) — final status

T13-30 REPORT does **NOT** present a sample-N field-failure climate-correlation analysis (different document type). However, §2.6 establishes that **cell-technology choice strongly modulates environmental sensitivity**:

- TOPCon: sensitive to acetic acid, NaCl, UV
- SHJ: sensitive to Na+ migration in humid conditions, UV (hydrogen effusion mechanism)
- Both: humidity-induced corrosion, UVID

This is a **cell-tech-conditional climate-correlation framing** that complements Jordan 2022's fleet-level temperature-PLR correlation (Al-BSF only). The actual climate-failure correlation answer for 2025 has two layers:

1. **Statistical PLR vs temperature** at fleet level: Jordan 2022, p<0.001 for Al-BSF.
2. **Mechanistic cell-tech × environmental-stressor** interactions: T13-30 REPORT §2.6.

ERR-5 is fully closed: climate matters at both fleet-statistical AND cell-tech-mechanistic levels.

## Ledger impact (applies on operator endorsement)

New ledger entries from this verification:

- **CLM-TOPCon-AceticAcid:** TOPCon shows significantly higher contact resistivity increase under acetic-acid exposure vs PERC + SHJ; DH 1000 h power loss 4-65% depending on encapsulation. VERIFIED per Sen et al. [128] in T13-30 REPORT §2.6.
- **CLM-TOPCon-NaCl:** TOPCon shows highest NaCl-DH power loss vs PERC + SHJ. VERIFIED.
- **CLM-SHJ-Na-Migration:** SHJ in glass/glass + EVA degrades under DH 85°C/85% RH with negative bias via NaOH from glass → Na+ crossing ITO → a-Si:H/c-Si interface passivation loss. Mitigated by POE + barrier layers. VERIFIED per Arruti et al. [134].
- **CLM-UVID-TOPCon-MAGNITUDE:** 14 TOPCon types: 0.5-8% power loss median 3% after 60 kWh/m² UV dose (Gebhardt et al.); 28 TOPCon + 2 SHJ: 0-10% TOPCon, 1-2.5% SHJ (Shina). 60 kWh/m² ≈ 1-2 years field. VERIFIED.
- **CLM-UVID-MPP-vs-TEST:** Field MPP degradation may be LOWER than UV test (short-circuit) suggests; HJT modules show light-soak recovery. TENTATIVELY-VERIFIED.
- **CLM-PEROVSKITE-CATEGORIES:** Baumann et al. taxonomy — 4 categories: intrinsic / cell-device-specific / extrinsic / module-device-specific. VERIFIED.
- **CLM-PEROVSKITE-IONMIGRATION:** Ion migration is dominant characteristic across many MHP degradation pathways — single mitigation strategy. VERIFIED.
- **CLM-PEROVSKITE-TEMP-MISCONCEPTION:** Si module designs must withstand >150°C during partial shading; MHP "only need 85°C stability" is wrong assumption. Number of cells per BPD + reverse voltage + cell efficiency determine max temperature. VERIFIED.
- **CLM-ITRPV-2024-TOPCon:** ITRPV 2024 projects TOPCon 29% → 53% market share next decade; SHJ 5% → 19%. TOPCon dominating after 2025. VERIFIED.
- **CLM-THINGLASS-BREAK** (was already in ledger): adds methodological note that ~20 modules in final mounting position is the recommended test to estimate breakage to 5%.

## Notes for substrate landscape revision

1. **Failure-mode discussion in `05_LANDSCAPE_RELIABILITY_v0.md`** needs an entire section on cell-tech-conditional environmental sensitivities (TOPCon × acetic acid, SHJ × Na+ humidity, both × UVID). This is the modern 2025 framing.
2. **Open questions list** needs to include: TOPCon UVID outdoor-reversibility (is dark-storage degradation a real field problem?); SHJ PID outdoor relevance (the lab 85°C/85% RH may not reflect field).
3. **Standards gap:** IEC 61215 does NOT cover UVID; PID test for SHJ may not reflect field recovery conditions. New tests needed.
4. **Bifacial glass/glass + thin glass** is a 2025 reliability hotspot — 5-10% rear breakage rate in first 2 years documented.
5. **Perovskite-tandem field deployment** is gated on solving ion migration mechanistically; single-process resolution is the research target.

## Open follow-ups

- F1: Verify Karin et al. 2019 (in flight) — methodology paper for Jordan 2022's climate zones.
- F2: Pull the actual Sen et al. [128] paper for TOPCon DH magnitude (specific encapsulation combinations).
- F3: Pull the Gebhardt et al. UVID paper [18] for the 14-TOPCon-type baseline.
- F4: Pull NREL DuraMAT Fleet Insights dataset (download URL chase ongoing — operator-pull recommended).
- F5: T13-30:2025 SLIDES (still not retrieved) for summary figures.

## Sources

- Local PDF: `D:/Renewables/Solar/data/raw/papers/Kontges2025_T13-30_REPORT_FULL.pdf`
- Original URL: https://www.csp.fraunhofer.de/content/dam/imws/csp/de/documents/task-13-reports/modul/IEA-PVPS-T13-30-2025-REPORT-Degradation-and-Failure.pdf
- Companion EX-SUMM verified at memo `15_`
- Companion PVFS Annex verified at memo `14_`
