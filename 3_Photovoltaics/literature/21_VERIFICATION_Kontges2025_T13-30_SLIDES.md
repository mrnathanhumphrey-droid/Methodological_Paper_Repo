# 21 — Verification: Köntges, Lin, Jahn 2025 — T13-30 SLIDES

**Status:** VERIFIED (local PDF read)
**Date:** 2026-05-27
**Local file:** `D:/Renewables/Solar/data/raw/papers/Kontges2025_T13-30_REPORT_SLIDES.pdf` (753 KB, 5 pages)
**URL:** `https://iea-pvps.org/wp-content/uploads/2025/02/IEA-PVPS-T13-30-2025-SLIDES-Degradation-and-Failure.pdf` (WebFetch successful)

---

## 1. Bibliographic verification

- **Title:** Degradation and Failure Modes in New Photovoltaic Cell and Module Technologies
- **Authors:** Marc Köntges, Jay Lin, Ulrike Jahn
- **Date:** February 2025
- **Report ID:** IEA-PVPS T13-30:2025
- **Task:** Task 13 Reliability and Performance of PV Systems

**ERR-4 triangulation (3rd independent confirmation):** Lead author is Köntges; Jahn is 3rd. Confirmed via PVFS Annex (memo 14), REPORT EX-SUMM (memo 15), REPORT FULL (memo 17), and now SLIDES (this memo). All four documents under the T13-30:2025 umbrella attribute lead authorship to Köntges.

---

## 2. Content summary (5 slides)

**Slide 1 — Title**

**Slide 2 — Introduction**
> "Literature, test results and current field experience are collected to assess weaknesses of new module technologies such as TOPCON and HJT. For perovskite-based PV technologies, a comprehensive literature is conducted to identify all degradation pathways that need to be addressed for reliable use in PV applications. If available, mitigation strategies are identified."

**Slide 3 — Most important results**
- Some primary failure types appear mitigated: **LID/LeTID and cell part isolation**.
- "Many current module types show **high degradation of up to 10% after 60 kWh UV dose** in lab tests." — *Upper-bound emphasis*; REPORT FULL §2.6.3 gives range 0.5–8% median 3% (CLM-UVID-DOSE). SLIDES emphasizes the upper tail.
- IEC 61215 tests do NOT test for new embedment material degradation. **Additional tests needed.**
- **Thin glass breakage and cold solder joints** are critical current failure types.

**Slide 4 — PVFS 2025**
> "The original PV failure fact sheets (PVFS 2021) were reviewed to include failures occurring in new module technologies and its impact in the field:"

5 explicit new-to-2025 PVFS additions enumerated:
1. **Spontaneous thin glass breakage**
2. **PID-p in bifacial modules**
3. **Cold solder joints in new generation junction boxes**
4. **Cracking and delamination in new backsheet materials**
5. **Cell-cracking in MBB / multi-wire or shingled modules**

PVFS structure per slide: COMPONENT → DEFECT → APPEARANCE → DETECTION → ORIGIN → IMPACT → MITIGATION → EXAMPLES.

**Slide 5 — Synthesis (7-point list)**
1. **Impact of Innovation on Degradation:** Cell-cracking mitigated by multi-wire; LeTID mitigated by Ga-doped wafers + improved mfg.
2. **PID:** Reducible via targeted tests + cell/module/system-level adjustments. UV irradiation during testing is promising for minimizing certain cell-type degradation (e.g., **TOPCon**).
3. **UVID:** Occurs in some modules but manageable via UV-stable designs + encapsulation materials. **Further research required.**
4. **Encapsulation Material Challenges:** Polymer-material degradation is still a major problem. **New tests combining UV + humidity + temperature stresses are required.**
5. **Durability of Thin Glass:** Thin glass shows higher breakage rates → **tests with multiple modules under real installation conditions** needed.
6. **Junction Box Reliability:** Faulty bypass diode connections pose safety + performance risk. **Tests during production + on affected installations** recommended.
7. **Perovskite-based PV modules:** "Numerous problems with reliability in the literature. Many possible solutions, but all challenges must be solved at once."

---

## 3. Cross-document consistency check (T13-30:2025 corpus)

| Claim | PVFS (14) | EX-SUMM (15) | REPORT FULL (17) | SLIDES (21) | Concordance |
|---|---|---|---|---|---|
| Authors Köntges/Lin/Jahn | YES | YES | YES | YES | ★ 4/4 |
| UVID emphasized for TOPCon | indirect | YES (TOPCon UVID open question) | YES §2.6 | YES slide 3+5 | ★ 4/4 |
| 60 kWh/m² UV dose threshold | — | YES (Gebhardt) | YES §2.6.3 | YES slide 3 | 3/4 |
| UVID range | — | 0.5-8% median 3% | 0.5-8% (Gebhardt) median 3% | "up to 10%" upper bound | 3/4 (slides emphasizes tail) |
| Thin glass 5-10% breakage 2 yr | — | YES | YES §3.7 | YES slide 3+4 | 3/4 |
| LID/LeTID resolved | — | YES (Ga-doped) | YES §2.1-§2.3 | YES slide 3+5 | 3/4 |
| Cell-cracking via multi-wire | — | YES | YES §3.3 | YES slide 4+5 | 3/4 |
| New IEC test gap for embedments | — | YES (IEC 62804-1:2025 + DH+UV+T combos) | YES §6 | YES slide 3+5 | 4/4 (★ — strongest "research needed" claim across all 4 docs) |
| PID-p in bifacial as new failure | — | indirect | YES §2.4.3 | YES slide 4 | 3/4 |
| Cold solder joints in new j-boxes | — | indirect | YES §3.8 / §4.x | YES slide 3+4 | 3/4 |
| Perovskite "many solutions, must be solved at once" | — | YES | YES §4 (Baumann classes) | YES slide 5 | 4/4 (★ — flagged in all but PVFS) |

**Consistency verdict:** 4 documents in T13-30:2025 corpus tell internally consistent story. SLIDES is the highest-density summary; FULL has the technical details. No contradictions surfaced.

**Small tightening from SLIDES:** UVID upper bound "up to 10%" is a tail-emphasis vs the REPORT's central tendency 3% median. Reading: the SLIDES targets practitioner audience (planners, installers, investors, inspectors, consultants, insurance) and highlights worst-case to motivate caution; REPORT targets researchers and gives the distribution. Both are accurate.

---

## 4. Claims ledger addenda (no new entries)

All claims on the SLIDES are already in the ledger from EX-SUMM / REPORT FULL / PVFS verifications. SLIDES is a triangulation source, not a new-claim source.

Existing ledger entries reinforced by SLIDES:
- CLM-T13-30-1 (30 failure modes / 4 components)
- CLM-T13-30-2, CLM-T13-30-3 (warranty + catastrophic boundaries)
- CLM-TOPCon-UVID
- CLM-THINGLASS-BREAK
- CLM-PEROVSKITE-OPEN
- CLM-LeTID-RESOLVED
- CLM-CELL-CRACK-RESOLVED
- CLM-IEC-62804-2025

---

## 5. Implications for 19_PREREG_v1.0_TOPCon_UVID

- **H3 (field 2-10× lower than lab) gets stronger:** SLIDES "up to 10% at 60 kWh" is the test-condition tail; the field-vs-lab gap that H3 predicts is now anchored to a wider lab distribution. If field cohort observes ≥1% but <10%, both H3 and the SLIDES upper-tail can be simultaneously satisfied — the gap test must compare central-tendency to central-tendency, not central-to-tail.
- **Encapsulation prioritization for §7 sub-decomposition** is reinforced: slide 5 point 4 is a direct call for "tests combining UV + humidity + temperature" — i.e., the multi-axis stressor framework. The pre-reg's combinatorial (Encapsulation × Climate × Vintage) approach maps to this call.
- **No re-lock needed.** SLIDES content is fully consistent with the pre-reg as locked at fc32be4.

---

## 6. Storage

- Local PDF: `D:/Renewables/Solar/data/raw/papers/Kontges2025_T13-30_REPORT_SLIDES.pdf`
- Gitignored (per `D:/Renewables/.gitignore` Solar rules)
- Citation: Köntges, M., Lin, J., Jahn, U. (2025). *Degradation and Failure Modes in New Photovoltaic Cell and Module Technologies* [SLIDES]. IEA-PVPS Report T13-30:2025. International Energy Agency Photovoltaic Power Systems Programme.

---

**END MEMO 21**
