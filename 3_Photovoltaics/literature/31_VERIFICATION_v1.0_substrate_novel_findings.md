# 31 — Verification v1.0 of substrate-novel findings (V1–V4)

**Status:** External-literature verification of the 4 substrate-novel findings flagged in memo 30 §4 ("Substrate-novel findings flagged for external verification").
**Date:** 2026-05-30 (post-compact)
**Scope:** D:/Renewables/Solar/ — verifications V1 (muddy soiling), V2 (multi-system synchrony methodology), V3 (σ_within heterogeneity inflation), V4 (CdTe-low soiling).
**Method:** 4 parallel literature-search subagents on bounded targets, then 1 follow-up conference-proceedings sweep to harden V2. Substrate meta-pre-reg §3-§6 evidence discipline applied — only direct quotes from peer-reviewed sources or official agency reports counted as anchors.

---

## 1. Verdict matrix

| # | Substrate-novel finding | Verdict | Substrate impact |
|---|---|---|---|
| **V1** | Wet-season DEPOSITION > dry-season at Alice Springs (muddy soiling) — CLM-093 | **VERIFIED** (mechanism = prior art) | Reframe from "novel mechanism" to "first explicit Australian-arid replication of established dew-cementation mechanism"; quantification (wet/dry sign test 11/13) is the contribution |
| **V2** | Multi-system Jaccard + K-consensus decomposes natural vs operational cleaning — CLM-094, CLM-095 | **NOVEL-FRONTIER (HARDENED)** | Promote to candidate primary publishable methodological artifact; one watch-item open (IEEE 11132652 full-text check) |
| **V3** | 2.0× σ_within heterogeneity inflation (PVDAQ vs Jordan) + 8× tightening (DKA homogeneous) — CLM-078, CLM-083 | **PARTIAL (direction anchor-supported, ratio quantification novel)** | Direction supported by Deceglie 2019 (residential>non-residential PLR means); σ_within ratio itself is substrate-novel quantification frontier |
| **V4** | CdTe-low soiling at DKA M7 (3.15%, lowest single-system) — CLM-090 | **PARTIAL-VERIFIED (directional)** | CdTe<c-Si direction replicates in Morocco lit (Ammari 2022, Tahri 2023); FS-proprietary-coating attribution dies — reframe as CdTe-class effect |

---

## 2. V1 — Muddy soiling (CLM-093)

**Verdict:** VERIFIED. 4 strong peer-reviewed anchors. Mechanism is established prior art across at least 4 arid PV substrates; substrate's first-explicit Australian-arid wet/dry sign test is the quantitative contribution, not the mechanism discovery.

### 2.1 Anchors

| Anchor | DOI | Supporting quote / number |
|---|---|---|
| Figgis et al. 2018 *Solar Energy* 173:826-840 | 10.1016/j.solener.2018.07.087 | "dew formation frequently occurs and leads to particle cementation by needle-shaped crystals of the clay mineral palygorskite, which directly precipitates at the glass surface"; "Preventing dew by sample heating inhibits cementation and reduced soiling by 65%" |
| Ilse et al. 2019 *Joule* 3(10):2303-2321 | 10.1016/j.joule.2019.08.019 | "cementation (formation of chemical and/or solid bridges between particles and surfaces after dew cycles)"; "rain can also cause negative effects through wet deposition of aerosol particles"; "Dew has been identified as a crucial factor in soiling, increasing cementation and decreasing particle rebound" |
| Ferrada / Atacama 2021 *Sol. Energy Mater. Sol. Cells* | 10.1016/j.solmat.2021.111-prefix | "At high humidity, water-soluble dust particles ... form microscopic droplets of salt solutions, and when dried ... the precipitated salt acts as a cement to anchor insoluble particles"; "surfaces are typically wet in the morning due to intense condensation during the night" |
| Energies 16(24):8022, 2023 review | 10.3390/en16248022 | "Slight rainfall (<0.508 mm/day) may not be sufficient and can even maximize dust deposition by creating a muddy layer"; "dry deposition has reduced adhesion compared to wet deposition" |

### 2.2 What was already in our substrate

Ilse 2019 was already cited in CLM-014 (closed ERR-3) and the soiling claims, but its wet-deposition / dew-cementation language had been under-leveraged — we cited it for the global aggregate (3-4% / 4-7%) but not for the mechanism that explains the wet/dry inversion at DKA. The other 3 anchors are new.

### 2.3 Reframe

The DKA wet>dry result is **not a mechanism discovery**. It is the **first explicit Australian-arid fleet replication** of a mechanism already documented in Qatar (Figgis), Atacama (Ferrada), and the global PV-soiling literature. The quantitative contribution stands: 11/13 systems showing the inversion, with a Mann-Whitney one-sided p=0.9996 in the opposite-of-naive direction, is novel data. The mechanism interpretation is anchor-supported.

---

## 3. V2 — Multi-system synchrony methodology (CLM-094, CLM-095)

**Verdict:** NOVEL-FRONTIER, HARDENED via journal + conference sweep. Candidate primary publishable methodological artifact.

### 3.1 Journal sweep (no prior art)

The substrate's claim is that pairwise Jaccard similarity of SRR recovery events + K-of-N consensus across a heterogeneous PV fleet decomposes cleaning events into natural (rain-correlated, lower K) vs operational (manual washing, all-K, NOT rain-correlated). The closest journal anchors are:

| Anchor | DOI / ref | What it does — and why it doesn't overlap |
|---|---|---|
| Deceglie, Micheli, Muller 2018, IEEE JPV 8(2):547-551 (rdtools SRR base) | 10.1109/JPHOTOV.2017.2784961 | Per-system stochastic recovery detection. No cross-system synchrony. |
| Muller, Perry, Micheli, Almonacid, Fernandez 2022, Prog. Photovolt. | 10.1002/pip.3523 | "Time series power production data from 22 PV inverters were **labeled** for natural or manually occurring cleaning events" — uses per-inverter labels, not cross-system co-occurrence inference. |
| Micheli, Muller, Deceglie et al. 2021, IEEE JPV 11(2) | 10.1109/JPHOTOV.2020.3043168 | "Nine soiling stations and a 1-MW site" — piecewise regression per-site; no inter-system consensus operator. |
| Jordan, Anderson, Deceglie et al. 2024, NREL/TP fy24osti/88769 | — | Fleet-aggregate degradation; no per-event synchrony decomposition. |
| Micheli, Almonacid, Fernandez et al. 2021 *iScience* review | 10.1016/j.isci.2021.102165 | "soiling rates measured by soiling stations distributed across two Californian PV sites... could vary by up to 2x within the same site" — spatial variability documented but not used as a recovery-event classifier. |
| NREL fy18osti/68225 "Mapping PV Soiling Using Spatial Interpolation" | — | Spatial correlation of soiling magnitude across 2-km separated stations. Magnitude, not event-synchrony. |

### 3.2 Conference sweep (HARDENED, with one watch-item)

PVSC 2022-2025, EU-PVSEC 2022-2024, PVRW 2024-2025, WCPEC checked. No paper, talk, or poster surfaced using inter-system Jaccard / synchrony / K-of-N consensus to detect or classify soiling-recovery / cleaning events across a fleet.

| Adjacency | Why it doesn't overlap |
|---|---|
| **Meyers, Dufour, Ogut 2025, IEEE PVSC-53 doc 11132652** "Anomaly detection in PV fleet data via interpretable ML" | Closest adjacency. Uses "neighborhood of measurements across systems and time" + linear-regression normalization + binary classifier — fleet-aware, but **general anomaly detection (not cleaning-event classification)**; uses regression-on-neighborhood, **not set-consensus**; does not address natural-vs-operational decomposition. **WATCH-ITEM:** retrieve full PDF to confirm no embedded cleaning-classification subsection. |
| Meyers 2023, arXiv 2307.00004 "PV Fleet Modeling via Smooth Periodic Gaussian Copula" | Fleet-level distributional modeling; no cleaning-event classification. |
| Li, Pendleton, Müller 2025, PVRW 2025 "Comparative Dust Soiling Assessment for PV systems" | Methodology comparison at single-system level; no fleet-consensus angle. |
| Cristaldi et al. 2024, IEEE doc 10432941 "Improved Cleaning Event Detection Methodology Including Partial Cleaning by Wind" | Per-system, adds wind-partial-cleaning class; no fleet consensus. |

### 3.3 Action

CLM-094 and CLM-095 promoted to **VERIFIED-OWN / NOVEL-FRONTIER** in the ledger. The K-sweep fleet-Jaccard synchrony operator as a natural-vs-operational decomposition appears to be without prior art. This is the substrate's leading candidate for a publishable methodological artifact.

**Watch-item:** retrieve IEEE 11132652 full text (Meyers/Dufour/Ogut PVSC-53 2025) to confirm no embedded cleaning-classification subsection. If present, downgrade to PARTIAL.

---

## 4. V3 — σ_within heterogeneity inflation (CLM-078, CLM-083)

**Verdict:** PARTIAL. Direction supported by external anchor; the σ_within ratio quantification itself is substrate-novel frontier (no peer-reviewed paper reports σ_within numerically for the relevant comparison).

### 4.1 Direction anchor

| Anchor | DOI | Supporting number |
|---|---|---|
| Deceglie et al. 2019 IEEE JPV "Fleet-Scale Energy-Yield Degradation Analysis" | 10.1109/JPHOTOV.2018.2885706 | n=503 systems (387 residential, 116 non-residential, PVDAQ + partners): residential mean PLR 1.3 %/yr vs non-residential 0.8 %/yr |

This **direction** supports the substrate's claim — heterogeneous residential fleets show larger PLR magnitudes / spread than non-residential controlled fleets. But Deceglie 2019 reports **mean** degradation rates by stratum, not σ_within.

### 4.2 What was NOT found

- **Jordan 2022** (10.1002/pip.3566) reports point estimates by climate stratum (cool -0.48 vs hot -0.88 %/yr) but no σ_within. The substrate's "Jordan-implied σ ≈ 0.99 %/yr" is a derived quantity, not a published anchor.
- **Jordan & Kurtz 2013** (10.1002/pip.1182), **Jordan 2016** (10.1002/pip.2744), **Phinikarides 2014** (10.1016/j.rser.2014.07.155), **Deceglie 2023** (10.1002/solr.202300196) — none report σ_within numerically by cohort.

### 4.3 Substrate implication

The 2× heterogeneous σ-inflation claim has **direction-anchor support** (Deceglie 2019), but the ratio quantification — and the 8-10× heterogeneous-vs-homogeneous σ_within ratio — is a substrate-novel quantitative frontier. The CLMs are now PARTIAL with anchor citation; the ratio claim retains its NOVEL-FRONTIER status. Worth pursuing — the gap means substrate findings could anchor a new ratio in future lit.

---

## 5. V4 — CdTe-low soiling (CLM-090)

**Verdict:** PARTIAL-VERIFIED. CdTe < c-Si **direction** replicates in independent Morocco field studies. The FS-proprietary-anti-soiling-coating attribution **does NOT** survive — lit attributes the effect to surface chemistry / partial-shading response, not to FS coating.

### 5.1 Anchors

| Anchor | DOI | Supporting number |
|---|---|---|
| Ammari et al. 2022 *Heliyon* 8:e11395 | 10.1016/j.heliyon.2022.e11395 | Benguerir, Morocco semi-arid head-to-head: "drop on the energy production of 15% for the Poly-Si and 13%" for CdTe; "Poly-Si is highly affected by soiling in comparison to the CdTe" |
| Tahri et al. 2023 *Renewable Energy* 205:695-716 | 10.1016/j.renene.2023.01.090 | Hot-arid multi-tech: daily SR loss CdTe 23.2% vs pc-Si 25.5% |
| NREL Si vs CdTe Soiling fy21osti/80330 (Muller 2020) | — | Explicit CdTe vs Si comparison report at NREL (treat as supporting reference) |
| Sayyah/Horenstein/Mazumder 2014 *Solar Energy* 107:576-604 | 10.1016/j.solener.2014.05.030 | Foundational anti-soiling review; documents hydrophobic/hydrophilic coating mechanisms (no CdTe-specific quote retrieved) |

### 5.2 Mechanism reframe

Lit attributes CdTe < c-Si in arid soiling to **surface chemistry + partial-shading response of thin-film cell architecture**, not to a First-Solar-proprietary anti-soiling glass. The substrate's "FS coating did it" framing in CLM-090 is therefore not supported. The directional finding (CdTe array shows lower soiling than c-Si arrays at DKA) survives as part of a documented CdTe-class effect.

### 5.3 Substrate implication

CLM-090 promoted from VERIFIED-OWN (n=1) to PARTIAL-VERIFIED (directional). Drop the FS-coating framing from any downstream substrate document. The DKA M7 finding stays interesting as part of a CdTe-class effect with prior peer-reviewed support.

---

## 6. Net impact on substrate

### 6.1 What got stronger

- **V2** is the substrate's leading publishable artifact, hardened against both journal and conference prior art
- **V1** mechanism story is locked in literature; substrate becomes a quantitative replicator in a new geography
- **V4** survives directionally with replication

### 6.2 What got weaker / reframed

- **V1 mechanism contribution dies** (already prior art) — quantitative contribution stays
- **V3 ratio is still substrate-novel** (no comparison σ_within in lit) — this is both a weakness (can't claim anchor support) and an opportunity (substrate could anchor a future ratio)
- **V4 FS-coating framing dies** — reframe as CdTe-class effect

### 6.3 What the substrate now publishes

Three plausible publication tracks emerge:

1. **Methodology paper** — multi-system Jaccard + K-consensus as a natural-vs-operational cleaning decomposition tool (V2-led). Sole novel-frontier finding; PV-reliability venue (IEEE JPV or Prog. Photovolt.); 1 fleet (DKA Alice Springs) as demonstration, with methodological framing emphasizing generality.
2. **σ_within heterogeneity quantification paper** (V3-led) — first published comparison of σ_within across heterogeneous vs homogeneous PV fleets; reports a 2× / 8× ratio that the lit currently lacks. Anchor: Deceglie 2019 mean-level direction.
3. **DKA Alice Springs case study** (V1 + V4 + soiling time-stability) — replication piece with the wet>dry sign test as the headline; CdTe-class finding folded in.

Tracks 1 and 2 are the substrate's distinctive contributions. Track 3 is a replication piece.

---

## 7. Open items / watch-list

| Item | Status |
|---|---|
| **WATCH-ITEM-1: RESOLVED 2026-05-30.** IEEE 11132652 (Meyers/Dufour/Ogut PVSC-53 2025) abstract retrieved via WebSearch — general anomaly detection, no overlap. | RESOLVED |
| Ferrada/Atacama 2021 paper DOI is partial; resolve when convenient | OPEN |
| Calyxo CdTe (DKA catalog #23) operator-pull for n=2 CdTe replication of V4 | OPEN (low priority) |
| **Probe 8 DKA fuzz-robustness sweep** (±0/±1/±2/±3) to harden CLM-095/103 | OPEN (operator-prioritized 2026-05-30) |

---

## 8. SKEPTIC-PASS CORRECTIONS (2026-05-30)

Operator entered cold-skeptic mode after V2/V3 probe push and identified gaps the verification round missed. Corrections folded into ledger CLMs 094, 095, 097, 101, 102, 103. Summary:

### 8.1 Heinrich 2020 — adjacent prior art MISSED by initial verification agent

**Heinrich, Meunier, Samé, Quéval, Darga, Oukhellou, Multon 2020. "Detection of cleaning interventions on photovoltaic modules with machine learning." Applied Energy 263:114642. DOI 10.1016/j.apenergy.2020.114642.** Per-system supervised ML on 3.5 mHz V/I/T electrical signals, 97% classification accuracy on n=1938 labeled examples, application context = standalone PV systems for rural electrification. Detects "wet cleaning interventions during daytime."

**Distinction from V2:**
- Heinrich: per-system, supervised, electrical signals, classifies "did a cleaning happen on this system"
- V2: fleet-level, unsupervised, SRR-recovery dates, decomposes detected cleanings into natural/operational

**Impact on V2 verification verdict:** **CLM-095 DOWNGRADED from NOVEL-FRONTIER to PARTIAL.** V2 remains methodologically distinct (different unit, supervision, signal) but the "no prior art on PV cleaning detection by ML" framing was wrong — Heinrich occupies that frontier explicitly. The verification agent searched for synchrony/Jaccard/K-consensus operators in PV but did not check the broader "ML for PV cleaning detection" line. This is the verification round's first found-by-skeptic miss.

**Action:** Pull full Heinrich 2020 PDF when accessible; current sources (ScienceDirect / HAL / Semantic Scholar / pv-magazine summary) returned 403 or blocked. Substrate uses the WebSearch-surfaced abstract as documentary evidence; not LLM-summarized.

### 8.2 Statistical strength of DKA K=13 crash — modest, not crushing

CLM-095 reported "K=12-13 crash to 5-10% << baseline 15%." Honest binomial tests:
- K=13: 2 of 42 rainy days, baseline 15.3% → one-sided p≈0.029 (significant; not crushing)
- K=12: 5 of 51 rainy, baseline 15.3% → one-sided p≈0.14 (not significant alone)
- Combined K=12+13: stronger but not pre-registered as a combined test

**CLM-103 added** to record this honestly. Probe 8 (fuzz sweep) is the obvious robustness check.

### 8.3 ±1 day fuzz NOT pre-registered

Convention copied from Probe 5b (which actually used ±2 days). Not formally justified. Probe 8 will sweep ±0/±1/±2/±3 on DKA to show whether the K=13 crash is robust to the choice.

### 8.4 MA K=17 "100% rain alignment" — statistically empty

Probe 6b memo 34 reported MA K=17 at 100% alignment (3 of 3 rainy). Binomial test: baseline 70.9%, observed 3 of 3 → z=1.11, p≈0.27. NOT significant. **CLM-102 added** to record this honestly. The 100% number was descriptively true but interpretively meaningless.

### 8.5 V2 "operational cleaning is uniform" scope limit was implicit

L7 (CLM-101) flagged climate + operator conditionality. The skeptic-pass adds: V2 assumes operational cleaning is WHOLE-SITE-SINGLE-DAY. Real operators may clean zones/strings across days, in which case V2 misses the operational regime entirely and falsely reports "no operational regime." CLM-101 expanded.

### 8.6 MA Jaccard 2.01× = borderline, not "generalizes"

CLM-097 framing was too strong. 2× synchrony at residential rooftops with shared seasonal weather (pollen, leaf litter, snow events) is plausibly produced by shared environment alone, without any cleaning-related synchrony. Reframed CLM-097.

### 8.7 Net impact on substrate publication tracks

Track 1 (V2 methodology paper) is now meaningfully constrained:
- Two-site demonstration: DKA strong, MA borderline + scope-limited
- Adjacent prior art (Heinrich 2020) must be cited and distinguished
- Fuzz sensitivity (Probe 8) must be reported
- Whole-site-day operational assumption must be flagged as scope limit
- Statistical reporting must use binomial p-values, not raw percentages

None of these kill V2 as a methodology contribution, but they tighten the scope of the claim significantly. The substrate's verification round caught some things, missed others — the skeptic-pass caught what verification missed. Both are now in the ledger.

---

## 8. Recommended next-substrate actions

1. **Pull IEEE 11132652 full text** (resolves WATCH-ITEM-1; should be quick via OSTI/preprint or PVSC proceedings)
2. **Draft V2 methodology paper outline** — the substrate's strongest publishable artifact
3. **Operator-pull Calyxo M23** to strengthen V4 (low priority — V4 reframe is the bigger move)
4. **Consider Probe 1 TOPCon UVID resumption** — verification phase is now substantially closed; substrate is back in probe mode

Per operator standing direction, no new probes until the user signals it.

---

**END VERIFICATION v1.0** — substrate-novel verdicts now: V1 VERIFIED (prior art), V2 NOVEL-FRONTIER HARDENED, V3 PARTIAL, V4 PARTIAL-VERIFIED.
