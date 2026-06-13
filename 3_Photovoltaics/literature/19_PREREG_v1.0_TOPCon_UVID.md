# Pre-Registration v1.0 — TOPCon UVID Field-Cohort RMD-SRC Application

**Status:** First scientific pre-reg in the Solar substrate. **Once committed, no edits permitted; deviations logged in §10.**
**Locked at commit:** `fc32be4` on `main`.
**Builds on:**
- `01_METAPREREG_v1.0_evidence_discipline.md` (evidence rules)
- `03_RMDSRC_SOLAR_FRAMING_v0.md` (RMD-SRC × solar substrate mapping)
- `15_VERIFICATION_Kontges2025_T13-30_REPORT_ExSumm.md` + `17_VERIFICATION_Kontges2025_T13-30_REPORT_FULL.md` (TOPCon UVID established as live 2020s field question)
- `16_VERIFICATION_Jordan2022_PVFleet.md` (fleet-level field-PLR methodology + climate framework)
- `18_VERIFICATION_Karin2019_PVCZ.md` (PV-specific climate zones)
- RMD-SRC Algorithm Specification (`D:/Resolve Research/RMD SRC Algorithm Specification.docx`, Humphrey May 2026)

**Per user direction 2026-05-27 ("we go 1 first"):** TOPCon UVID is the highest-priority scientific question because it's the live 2020s open question with concrete measurable signal (lab-accelerated 0.5-8% power loss, median 3%, at 60 kWh/m² UV dose per Gebhardt et al. in T13-30 REPORT §2.6.3), AND because the outdoor reversibility question is the unresolved field-vs-lab gap (T13-30 REPORT EX-SUMM page 2).

---

## 0. What this pre-reg LOCKS

1. The **substrate scope** (§1): TOPCon-cell c-Si PV modules in outdoor field operation.
2. The **scientific question** (§2): does TOPCon UVID in field deployment cohorts admit RMD-SRC partition into clean trajectory regimes?
3. The **initial partition ℙ₀** (§3) — exogenous categoricals locked BEFORE outcome data is examined.
4. The **observable vector x_j** (§4) and time-binning convention.
5. The **response-function variables** (§5): ∇g, ρ_s, ρ_x definitions for TOPCon.
6. The **5 trajectory-classification regimes** (§6) — inherited from RMD-SRC.
7. The **sub-decomposition priority order** (§7).
8. The **pre-registered hypotheses** H1-H5 (§8) with falsification gates.
9. **RMD-SRC universal falsifiers F1-F4** (§9) inherited + substrate-specific F_T1-F_T3 (§10).
10. **Termination thresholds** (§11): minimum cell size n_c ≥ 50; residual-variance threshold.
11. **Verdict reporting protocol** (§12).
12. **Deviation log** (§13) — initially empty.

What this pre-reg does NOT lock:
- Specific modules / vendors / sites (will be selected per §3 ℙ₀ as substrate data accrues).
- Lab capex / opex (separate downstream pre-reg).
- Mechanism-level chemistry claims beyond T13-30 REPORT's published findings.
- Cross-substrate cohort comparisons (SHJ, perovskite-tandem) — separate downstream pre-regs.

---

## 1. Substrate scope (LOCKED)

**Object of study:** TOPCon-cell-architecture c-Si photovoltaic modules deployed in outdoor field operation.

**Inclusion criteria:**
- Cell architecture: Tunnel Oxide Passivated Contact (TOPCon) on n-type Si wafer (per T13-30 REPORT abbreviation, p.7)
- Module form factor: standard 60-cell to 78-cell c-Si module (mono-facial or bifacial)
- Field deployment: ≥6 months continuous outdoor exposure as of measurement window
- Manufacturer: commercial product with publicly disclosed cell architecture

**Exclusion criteria:**
- Lab-only modules without field deployment.
- Mixed-architecture modules (e.g., TOPCon-PERC bifacial hybrids — separate cohort).
- Pre-2022 vintage with disputed TOPCon labeling (TOPCon market scale-up was ~2022 per ITRPV 2024).
- Concentrator PV (CPV).

---

## 2. Scientific question (LOCKED)

**Primary question:** Does outdoor-field TOPCon UVID degradation, measured as power loss + IV-feature drift over 2+ years, admit an RMD-SRC partition into clean trajectory-classification regimes per the algorithm in `D:/Resolve Research/RMD SRC Algorithm Specification.docx`?

**Equivalently:** Are TOPCon field-degradation trajectories per (manufacturer × encapsulation × climate × vintage) cell either (a) clean under a single statistical-rule classification, or (b) decomposable into clean sub-cells via §7?

**Secondary questions (testable conditional on primary):**
- (a) Which categorical axis dominates UVID variance: manufacturer, encapsulation, climate, or vintage?
- (b) Does the lab-accelerated 60 kWh/m² UV dose / 0.5-8% power loss range (Gebhardt + Shina, T13-30 REPORT §2.6.3) translate to field rates predicted by Karin 2019 PVCZ?
- (c) Does outdoor exposure reverse UVID (T13-30 REPORT-flagged open question — light-soak recovery in HJT analog)?

---

## 3. Initial partition ℙ₀ (LOCKED before any outcome data is examined)

Exogenous categorical axes for ℙ₀, in tightest-grain ordering:

- **A_MFR** — Manufacturer (commercial brand, identifying string from datasheet metadata)
- **A_ENC** — Encapsulation material: {EVA, POE, TPO, EPE (EVA-POE-EVA), ionomer, OTHER}. Source: module BOM disclosure or destructive teardown.
- **A_VINT** — Installation vintage year: {2022, 2023, 2024, 2025, 2026+}. Source: install records.
- **A_PVCZ_T** — Karin 2019 PVCZ temperature zone: {T1 ... T10}. Source: site lat/lon → pvcz package lookup.
- **A_PVCZ_H** — Karin 2019 PVCZ humidity zone: {H1 ... H5}. Source: same.
- **A_MNT** — Mounting type: {open-rack ground-mount, fixed-tilt rack, single-axis tracker, dual-axis tracker, low-standoff rooftop, BIPV}. Source: site survey.

**ℙ₀ resolution:** Initial partition is the cross-product over all 6 axes. Combinatorial cap: maximum 10 × 6 × 5 × 10 × 5 × 6 = 18,000 cells theoretically; in practice ≤500 populated cells expected given fleet n.

**Pre-reg constraint per RMD-SRC §Step 0:** ℙ₀ is locked BEFORE any moment-flow statistic is computed on the outcomes. The pre-registration of ℙ₀ at this commit is the timestamp-anchor.

---

## 4. Observable vector x_j (LOCKED)

Per RMD-SRC §Step 1, the multi-dimensional event observable per module per time bin:

**Primary (required for VERIFIED status of any trajectory verdict):**
- x_1 = **Normalized DC yield** (kWh/kWp/year), per RdTools YoY methodology (Deceglie et al., adopted by Jordan 2022)
- x_2 = **I_sc** at module level, per IEC 61215 reference conditions (annual measurement)
- x_3 = **V_oc** at module level (same)
- x_4 = **Fill factor (FF)** = P_MPP / (V_oc × I_sc), dimensionless
- x_5 = **Series resistance R_s** extracted from IV-curve fitting

**Secondary (required for §8 H3 verification):**
- x_6 = **Front-side EL defect fraction** (dimensionless 0-1), per Köntges et al. 2017 PV EL imaging protocol
- x_7 = **UVID-specific spectral response loss** at 280-400 nm (relative units), measured via spectroradiometer if available

**Environmental gradient field components (per §5):**
- x_8 = **Cumulative UV dose** since installation (kWh/m²), modeled per pvlib + NSRDB
- x_9 = **Cumulative module temperature × time integral** (°C·days above 25°C)
- x_10 = **Cumulative water-vapor exposure** (g/kg·days, per Karin specific humidity)

**Time-binning convention:** Monthly aggregation for x_1, x_8, x_9, x_10. Annual aggregation for x_2-x_5, x_6 (matches typical EL imaging + IV measurement cadence).

---

## 5. Response-function variables for TOPCon (LOCKED)

Per RMD-SRC §Step 3, the response function:

```
x_j(e_i) = α + β_g · ∇g(e_i) + β_s · ρ_s(e_i) + β_x · ρ_x(e_i) + ε_i
```

**∇g (gradient field) for TOPCon UVID:**
∇g_i = β_g1 · UV_dose_i + β_g2 · T_module_i + β_g3 · humidity_i + β_g4 · UV × T interaction

where the UV × T interaction is pre-registered as a CANDIDATE mediator per T13-30 REPORT §2.6.3 finding that "light soaking may recover UVID for HJT modules" — suggesting reversible component governed by UV intensity × temperature.

**ρ_s (same-cell density) for TOPCon UVID:**
ρ_s_i = count of modules within 10-meter spatial neighborhood of e_i in the same (A_MFR × A_ENC × A_VINT) cell as e_i, divided by total local module count.

Tests **batch-cohort reinforcement** — whether modules from the same manufacturing batch deployed adjacently show correlated UVID timing.

**ρ_x (cross-cell density) for TOPCon UVID:**
ρ_x_i = count of modules within 10-meter neighborhood that are NOT in the same (A_MFR × A_ENC) cell.

Tests **substrate-cell interaction** — whether adjacent different-encapsulation modules affect each other (e.g., outgassing from EVA neighbors reaching POE-encapsulated modules).

---

## 6. Trajectory classification (LOCKED — inherited from RMD-SRC §Step 2)

The 5 regimes:

| Regime | μ̇ pattern | σ̇² pattern | Implied rule | TOPCon UVID interpretation candidate |
|---|---|---|---|---|
| Stationary | μ̇ ≈ 0 | σ̇² ≈ 0 | Equilibrium under gradient | Cell at post-LeTID-recovery plateau; UVID at saturation |
| Gradient-tracking | μ̇ matches gradient | σ̇² ≈ 0 | Classical / Maxwell-Boltzmann | Modules following expected UV-dose-driven loss |
| Concentrating (boson) | μ̇ toward equilibrium | σ̇² < 0 | Network attraction | Same-batch UVID propagating across spatial neighbors |
| Diffusing (fermion) | μ̇ away from gradient | σ̇² > 0 | Anti-clustering | Encapsulation-type mismatch creates dispersion (POE shields EVA neighbors?) |
| Fragmenting | irregular | σ̇² > 0, polymodal | Mixed cell; decompose | Cohort contains undocumented manufacturer-batch-process variation; trigger Step 4 |

Each (cell c, observable j) trajectory Γ_{c,j} is classified into one of these 5 regimes per RMD-SRC §Step 2.

---

## 7. Sub-decomposition priority order (LOCKED)

Per RMD-SRC §Step 4 cheapness order:

- **4a (categorical):** Split cell on additional observable categoricals from §3. Sequence: encapsulation (A_ENC) first, then vintage (A_VINT), then climate (A_PVCZ_T × A_PVCZ_H), then mounting (A_MNT). Priority justification: T13-30 REPORT Sen et al. §2.6.1 found encapsulation drives 4-65% DH variance in TOPCon — analogous mechanism predicted for UVID.
- **4b (time-phase):** Split on temporal windows. Pre-locked candidate phase boundaries: pre-2024 vs post-2024 (TOPCon cell-design evolves in ~6-month cycles per T13-30 REPORT p.38).
- **4c (mixture):** Latent-class analysis on response-function residuals.

**Pre-reg constraint:** One decomposition strategy per node. Choice rule = §Step 4 sequence (4a→4b→4c). Logged per decomposition.

---

## 8. Pre-registered hypotheses (LOCKED)

### H1 — Encapsulation material dominates UVID variance after manufacturer+climate+vintage controls

**Prior:** T13-30 REPORT §2.6.1 (Sen et al.) found encapsulation drives 4-65% power loss in TOPCon DH testing — variance dominance much larger than other within-cohort variance components.

**Test:** After §3 ℙ₀ partition is locked, regress per-cell UVID rate on encapsulation type, controlling for manufacturer + climate + vintage. Variance attributable to encapsulation should exceed 30% of total within-(MFR × climate × vintage) variance.

**Falsification gates:**
- **CONFIRMED:** η²_partial (encapsulation) > 0.30 after manufacturer+climate+vintage controls
- **PARTIAL:** η²_partial (encapsulation) ∈ [0.15, 0.30]
- **REFUTED:** η²_partial (encapsulation) < 0.15

### H2 — Climate × UV-dose interaction shows Concentrating-regime (boson-like) trajectories in hot zones

**Prior:** UVID accumulates with UV dose; in hot climates (T8-T10) cumulative UV dose × elevated module temperature × cell-stress accelerates degradation. RMD-SRC §Step 2 predicts σ̇² < 0 if same-batch modules show **correlated UVID timing** within spatial neighborhoods (ρ_s reinforcement).

**Test:** Within hot-climate Karin zones (T8-T10), classify trajectory regime per cell. Count fraction of cells classified as Concentrating.

**Falsification gates:**
- **CONFIRMED:** ≥40% of T8-T10 cells classified Concentrating
- **PARTIAL:** 20-40% Concentrating
- **REFUTED:** <20% Concentrating, OR Diffusing/Fragmenting dominates

### H3 — TOPCon field UVID rate is 2-10x lower than lab-accelerated 60 kWh/m² test predicts (outdoor MPP vs short-circuit gap)

**Prior:** T13-30 REPORT p.43: "the field degradation rate may be lower than the UV dose in the accelerated aging test suggests" because operating point in PV generator is MPP, not short-circuit. Light soaking may recover UVID for HJT modules. Dark-storage degradation accelerates field nighttime.

**Test:** Compute median field annual UVID rate from (x_1 normalized DC yield) attributed to UVID component (subtracted from other degradation modes). Compare to lab-accelerated rate scaled by UV dose actually delivered to field cohort (per x_8).

**Falsification gates:**
- **CONFIRMED:** field rate is 2-10× lower than lab-test prediction, AND signature is non-monotonic (consistent with light-soak recovery)
- **PARTIAL:** field rate is 0.5-2× lab prediction (test-to-field translation is OK at first order)
- **REFUTED:** field rate exceeds lab prediction (lab tests UNDER-predict field UVID — research-area-critical inversion)

### H4 — Manufacturer dominates 50%+ of variance after climate + vintage + encapsulation controlled

**Prior:** TOPCon cell-design evolution in ~6-month cycles (T13-30 REPORT p.38) implies manufacturer-batch process differences are large. Older Compendium analyses confirmed manufacturer is a major variance source.

**Test:** Variance decomposition with manufacturer entering AFTER climate + vintage + encapsulation are controlled. η²_partial (manufacturer) ≥ 0.50.

**Falsification gates:**
- **CONFIRMED:** η²_partial (manufacturer) ≥ 0.50 after other controls
- **PARTIAL:** ∈ [0.25, 0.50]
- **REFUTED:** < 0.25

### H5 — Cohort × manufacturer interaction is large; manufacturer-specific climate sensitivity exists

**Prior:** Per T13-30 REPORT §2.6.3, some TOPCon types show UV-stable behavior. Implication: manufacturer × climate interaction is non-zero — some manufacturers stable across climates, others sensitive.

**Test:** Test manufacturer × climate interaction term (manufacturer × PVCZ T-zone) in response-function fit. Compare main effects vs interaction.

**Falsification gates:**
- **CONFIRMED:** manufacturer × climate interaction Bayes factor > 10 vs additive
- **PARTIAL:** BF ∈ [3, 10]
- **REFUTED:** BF < 3 (interaction not credible)

---

## 9. RMD-SRC universal falsifiers (inherited)

Per RMD-SRC algorithm spec:

- **RMD_F1 (initial partition cleanness):** If ≥80% of ℙ₀ cells are clean at Step 3 without decomposition → TOPCon UVID doesn't need RMD; gradient response alone suffices.
- **RMD_F2 (decomposition convergence):** If decomposition produces leaves at minimum-cell-size limit without achieving cleanness on ≥50% of original cells → framework fails on TOPCon UVID.
- **RMD_F3 (validation agreement):** If trajectory classification and response-function fit disagree on ≥30% of leaves after decomposition → internal inconsistency.
- **RMD_F4 (predictive transfer):** Leaf classifications trained on [t1, t2] should predict leaf behavior on [t2, t3]. r < 0.4 in holdout → overfit.

---

## 10. Substrate-specific falsifiers (LOCKED)

- **F_TOPCon_1 (no-signal):** If median TOPCon annual UVID-attributable power loss < 0.5%/yr after 2+ years field exposure, the lab-accelerated UV tests (Gebhardt 0.5-8% at 60 kWh/m²) do not translate to field — substrate's TOPCon UVID research thesis is REFUTED at the field level. Report and stop. This is the "lab artifact" disposition.
- **F_TOPCon_2 (encapsulation null):** If H1 returns REFUTED (η²_partial encapsulation < 0.15), the T13-30 REPORT Sen et al. mechanism does NOT generalize from DH to UVID. Methodology gap exposed; downstream paper required to investigate.
- **F_TOPCon_3 (lab-field inversion):** If H3 returns REFUTED in the field-exceeds-lab direction, this is a research-area-critical finding requiring its own pre-reg + investigation. Substrate publishes immediately.

---

## 11. Termination thresholds (LOCKED)

Per RMD-SRC §Step 5:

- **Minimum cell size:** n_c ≥ 50 modules per leaf for VERIFIED trajectory classification.
- **Residual-variance threshold for "clean":** σ²_residual ≤ 0.25 · σ²_marginal at the leaf level.
- **Time-bin minimum:** ≥24 monthly bins (2 years) for trajectory classification; ≥3 annual bins for IV-feature trajectory.

Cells failing minimum cell size enter the "incompletely decomposed" state per RMD-SRC §Step 5 with a labeled residual.

---

## 12. Verdict reporting protocol (LOCKED)

Each hypothesis verdict reported as one of: **CONFIRMED**, **PARTIAL**, **REFUTED**, **INDETERMINATE** per §8 falsification gates.

Aggregate verdict over H1-H5:
- If ≥4/5 CONFIRMED: substrate's TOPCon UVID framework holds; methodology paper drafted.
- If ≤2/5 CONFIRMED: framework needs revision; deviation log + amendment.
- Mixed: report as-is, no umbrella verdict.

Falsifier verdicts (RMD_F1-F4 + F_TOPCon_1-3) reported independently; any single falsifier firing triggers the disposition specified.

Pre-reg discipline: results table reports H1-H5 + F1-F7 verdicts BEFORE any narrative interpretation, per `01_METAPREREG_v1.0` discipline.

---

## 13. Deviation log

| Date | Deviation | Rationale |
|---|---|---|
| 2026-05-27 | **Karin PVCZ axis-cardinality clarified:** §3 ℙ₀ axes correctly list `A_PVCZ_T` × `A_PVCZ_H` (T-zone × H-zone). §15 threat-of-validity #4 incorrectly listed "T-zone × H-zone × W-zone combinatorial sparsity" — W is an independent stressor in the pvcz package, NOT part of the canonical PVCZ label. Canonical PVCZ = T×H = 50 zones. Correcting §15 #4 to read T-zone × H-zone only. Substrate memory's "250" figure was the same error and is being corrected separately. | Direct extraction from `pvcz` v0.3.0 npz: `total_num_zones=50`, `zone_spec['pvcz']` enumerates 50 T:H labels. See memo `20_KARIN2019_THRESHOLDS_extracted.md` for full thresholds. Pre-reg ℙ₀ cardinality unchanged in substance (§3 was already correct); §15 wording corrected. No re-lock required (clarification of a stated axis, not amendment to scope). |

---

## 14. Operational protocol (LOCKED execution order)

1. **Lock this pre-reg at commit.**
2. **Cohort identification:** TOPCon-cell modules with ≥6 months field exposure, sourced from NREL DuraMAT, NREL PVDAQ, Sandia RTC partnerships, or substrate-specific lab outdoor arrays.
3. **ℙ₀ partition assignment:** Per §3, exogenous categoricals only. NO outcome inspection during partition assignment.
4. **Observable data acquisition:** Monthly x_1, x_8, x_9, x_10; annual x_2-x_5; opportunistic x_6, x_7 if EL/spectro available.
5. **Step 1 moment-flow:** Compute (μ, σ²) trajectories per (cell, observable).
6. **Step 2 trajectory classification:** Per RMD-SRC.
7. **Step 3 response-function fit:** Per §5.
8. **Step 4 sub-decomposition** if not-clean: per §7 priority.
9. **Step 5 termination:** Per §11 thresholds.
10. **Step 6 cross-cell mechanism inference.**
11. **Hypothesis verdicts:** H1-H5 + F_TOPCon_1-3 + RMD_F1-F4 per §12.
12. **Write up `result_v1.0_TOPCon_UVID_RMDSRC.md`.**

---

## 15. Threats to validity (acknowledged)

1. **TOPCon market scale-up is recent (~2022 per ITRPV);** field n at 2+ years exposure may be small in 2026-2027 measurement windows.
2. **Encapsulation BOM disclosure is incomplete** for many commercial TOPCon products. May require destructive sampling or NDA with manufacturer.
3. **UVID is one of multiple concurrent degradation modes** (PID, LeTID partial, thermal-cycling crack growth). Mode-decomposition error propagates to UVID attribution.
4. **Karin 2019 PVCZ T-zone × H-zone combinatorial sparsity** (50 canonical zones; W is independent stressor not multiplied into PVCZ label, per §13 DEVIATION 2026-05-27) may collapse some cells below n_c ≥ 50 minimum; cell aggregation rules may need amendment.
5. **DuraMAT fleet dataset access** is currently blocked by NREL SSL/TLS host issue (per session 2026-05-27); alternate data sources (OEDI, RTC partnerships, lab outdoor arrays) may have different ℙ₀ resolution.

---

## 16. Cross-pre-reg coordination

This pre-reg shares the meta-pre-reg + RMD-SRC framing with:
- Future SHJ UVID pre-reg (parallel substrate, separate cohort)
- Future perovskite-tandem stability pre-reg (further out; needs separate ℙ₀ axes)
- Future fleet-PLR PVCZ-stratified pre-reg (uses Jordan 2022 dataset; broader scope)

These downstream pre-regs may amend Karin 2019 PVCZ axes, the encapsulation taxonomy, or the gradient-field operationalization based on findings from this pre-reg.

---

## 17. Explicitly NOT covered

- SHJ, PERC, Al-BSF, perovskite-tandem cohorts (separate pre-regs)
- Manufacturer-batch tracing (NDA-gated, separate from this open scientific pre-reg)
- Bifacial-specific failure modes (separate cohort due to glass/glass distinction)
- Inverter-side energy-loss attribution (separate pre-reg, requires inverter-level monitoring infrastructure)
- LCOE / financial-cohort questions (downstream applied work)
- Manuscript-prose writing (user-authored, not in pre-reg scope)

---

**Locked at commit:** `fc32be4` on `main`.
**Repository scope:** D:/Renewables/Solar/.
**Author of v1.0 draft:** Claude (LLM) per meta-pre-reg §8 — every claim in this document is itself subject to operator endorsement and §3 verification when applied to field data.
