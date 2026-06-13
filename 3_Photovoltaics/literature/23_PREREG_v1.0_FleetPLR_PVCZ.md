# Pre-Registration v1.0 — Fleet PLR × PVCZ Climate-Zone RMD-SRC Partition (Probe 2)

**Status:** Second scientific pre-reg in the Solar substrate. **Once committed, no edits permitted; deviations logged in §13.**
**Locked at commit:** `165342b` on `main`.
**Builds on:**
- `01_METAPREREG_v1.0_evidence_discipline.md` (evidence rules)
- `03_RMDSRC_SOLAR_FRAMING_v0.md` (RMD-SRC × solar substrate mapping)
- `16_VERIFICATION_Jordan2022_PVFleet.md` (fleet-level field-PLR methodology + climate framework — **this probe is a pre-registered replication+extension of Jordan 2022 on an independent fleet**)
- `18_VERIFICATION_Karin2019_PVCZ.md` + `20_KARIN2019_THRESHOLDS_extracted.md` (PV-specific climate zones + literal thresholds)
- `22_PVDAQ_alternate_path_and_rdtools.md` (data source: PVDAQ 1862-system index + rdtools)
- RMD-SRC Algorithm Specification (`D:/Resolve Research/RMD SRC Algorithm Specification.docx`, Humphrey May 2026)

**Why this probe now (per user direction 2026-05-27 "go probe 2"):** Unlike Probe 1 (`19_PREREG` TOPCon UVID, blocked on cell-architecture cohort identification), this probe is **unblocked**: it requires only (a) per-system performance-loss rate and (b) exogenous siting categoricals — both fully provided by the PVDAQ public lake already in hand (memo 22). It is the natural next crunch: real field data, no acquisition blocker, and it tests the substrate's most important anchor finding (Jordan 2022's p<0.001 climate-temperature PLR correlation) on a fleet that overlaps but is not identical to Jordan's.

---

## 0. What this pre-reg LOCKS

1. The **substrate scope** (§1): all-technology PVDAQ field systems with sufficient longitudinal coverage.
2. The **scientific question** (§2): does field PLR partition cleanly on Karin PVCZ climate zones under RMD-SRC?
3. The **initial partition ℙ₀** (§3) — exogenous siting categoricals locked BEFORE any PLR (outcome) is computed.
4. The **observable vector x_j** (§4) and time-binning.
5. The **response-function variables** (§5).
6. The **5 trajectory-classification regimes** (§6) — inherited from RMD-SRC.
7. The **sub-decomposition priority order** (§7).
8. The **pre-registered hypotheses** H1-H5 (§8) with falsification gates.
9. **RMD-SRC universal falsifiers F1-F4** (§9) + substrate-specific F_Fleet_1-3 (§10).
10. **Termination thresholds** (§11).
11. **Verdict reporting protocol** (§12).
12. **Deviation log** (§13) — initially empty.

**Pre-reg integrity note:** As of this lock, the only PVDAQ quantities inspected are **exogenous coverage statistics** (T-zone / H-zone / mounting / tracking / years / qa_status counts — memo 22 §2). These are ℙ₀-side. **No performance / yield / PLR (outcome) quantity has been computed.** The ℙ₀ partition below is therefore locked blind to outcomes, satisfying RMD-SRC §Step 0.

What this pre-reg does NOT lock:
- Specific systems (selected per §3 ℙ₀ inclusion rule from PVDAQ index).
- Cell-architecture stratification (PVDAQ index lacks this field — it is an *uncontrolled within-cell nuisance* here, §15).
- Cross-fleet meta-analysis with Jordan 2022's actual systems (separate downstream work).
- Manuscript prose (user-authored).

---

## 1. Substrate scope (LOCKED)

**Object of study:** Photovoltaic systems in the NREL PVDAQ public data lake (OEDI submission 4568, DOI 10.25984/1846021, CC-BY 4.0) with sufficient longitudinal field coverage to estimate a performance-loss rate.

**Inclusion criteria:**
- Present in `PVDAQ_systems_20250729.csv` (1862 systems).
- `qa_status == "pass"` (1564 systems).
- `years ≥ 5.0` (longitudinal coverage sufficient for YoY PLR per rdtools/Deceglie 2018) — 1288 systems meet QA+years jointly.
- Has the sensor channels required for rdtools normalization (`available_sensor_channels` sufficient for at least clearsky-index or measured-POA normalization). Exact channel requirement resolved at acquisition; systems lacking minimum channels are excluded and counted.
- Assigned to a populated Karin PVCZ T-zone and H-zone (all PVDAQ systems are, via the pre-computed columns).

**Exclusion criteria:**
- `qa_status == "fail"` (298 systems).
- `years < 5.0`.
- Systems whose `years` is inflated by gaps (resolved at acquisition via `number_records` density check; thin-coverage systems excluded and counted).
- Systems with PVCZ zone assignment missing (none expected).

**All-technology by design:** This is a climate/siting probe, NOT a cell-technology probe. Cell architecture (Al-BSF / PERC / TOPCon / thin-film) is NOT in the PVDAQ index and is therefore an **uncontrolled within-cell nuisance variable**, addressed as residual variance (§15) and as a candidate Step-4 split only if architecture metadata is later acquired.

---

## 2. Scientific question (LOCKED)

**Primary question:** Does outdoor-field performance-loss rate (PLR), measured per the RdTools year-on-year methodology (Deceglie et al. 2018, as adopted by Jordan 2022), admit an RMD-SRC partition into clean trajectory-classification regimes when the initial partition ℙ₀ is the Karin 2019 PV-specific climate zone (T-zone × H-zone) crossed with siting categoricals?

**Equivalently:** Are field PLR trajectories per (PVCZ-T × PVCZ-H × mounting × tracking × tilt × azimuth × capacity-class × vintage) cell either (a) clean under a single statistical-rule classification, or (b) decomposable into clean sub-cells via §7?

**Secondary questions (testable conditional on primary):**
- (a) Does PVDAQ replicate Jordan 2022's credibly-higher PLR in hotter PVCZ T-zones at p<0.001 (T3 −0.48 / T4 −0.78 / T5 −0.88 %/yr, Al-BSF ground-mount, memo 16)?
- (b) Does PVDAQ replicate Jordan 2022's tracker-vs-fixed PLR null (p>0.49)?
- (c) Is the humidity (H-zone) axis underpowered in PVDAQ as it was in Jordan 2022 (geographic skew → INDETERMINATE)?

---

## 3. Initial partition ℙ₀ (LOCKED before any outcome data is computed)

Exogenous categorical axes, all derived from install-time / geometric metadata in the PVDAQ index (none derivable from outcomes):

- **A_PVCZ_T** — Karin PVCZ temperature zone, from PVDAQ column `pvcz_t_rack` (roof systems may instead use `pvcz_t_roof`; rule fixed at §3.1). Levels present in PVDAQ: {T1, T2, T3, T4, T5, T6}.
- **A_PVCZ_H** — Karin PVCZ humidity zone, from `pvcz_humidity`. Levels present: {H1, H2, H3, H4}.
- **A_MOUNT** — mounting type, from `type`: {roof, ground, carport}. (`unknown`/NaN systems → A_MOUNT = UNKNOWN, retained as own level.)
- **A_TRACK** — tracking, from `tracking`: {fixed, tracking}.
- **A_TILT** — tilt bin, from `tilt`: {low [0-15°), mid [15-35°), high [35°+)}.
- **A_AZ** — azimuth bin, from `azimuth`: {south-facing [135-225°), east [45-135°), west [225-315°), north [other]}.
- **A_CAP** — DC capacity class, from `dc_capacity_kW`: {residential [<20], commercial [20-1000), utility [≥1000]}.
- **A_VINT** — commissioning vintage, from `first_timestamp` year, binned: {pre-2010, 2010-2014, 2015-2019, 2020+}.

**§3.1 Mounting-coherent temperature-zone rule (LOCKED):** A system's A_PVCZ_T uses `pvcz_t_roof` if `A_MOUNT == roof`, else `pvcz_t_rack`. This respects Karin 2019's distinct roof/rack equivalent-temperature surfaces (roof runs hotter; memo 20 §2). Locked before outcome inspection.

**ℙ₀ resolution:** Initial partition is the cross-product over all 8 axes. Theoretical cap 6×4×4×2×3×4×3×4 = 27,648 cells; in practice ≤30 populated cells with n≥20 expected, concentrated in T3:H3 and T4:H3 (memo 22 §2). Sparse cells handled per §7 + §11.

**Primary partition for H1/H4 replication tests:** A_PVCZ_T × A_PVCZ_H (the 2D Karin grid), marginalizing the siting axes, is the direct analog of Jordan 2022's climate-zone analysis and is the headline replication partition.

---

## 4. Observable vector x_j (LOCKED)

Per RMD-SRC §Step 1, per system per time bin:

**Primary (required for VERIFIED status of any trajectory verdict):**
- x_1 = **Normalized performance index** (energy yield normalized to modeled clear-sky-or-POA expectation), per `rdtools.normalization`. Dimensionless, ~1.0 at install.
- x_2 = **Temperature-corrected performance ratio**, per `rdtools` temperature-correction (cell-temp from sensor or modeled per pvlib).

**Derived scalar (headline outcome):**
- PLR (%/yr) = central YoY degradation rate per `rdtools.degradation.degradation_year_on_year`, with bootstrap CI per `rdtools.bootstrap` (Deceglie 2018; identical methodology family to Jordan 2022).

**Environmental gradient-field components (per §5; from PVDAQ sensor channels where present, else modeled):**
- x_3 = **Cumulative plane-of-array insolation** (kWh/m²) — measured irradiance channel or NSRDB-modeled (Sengupta 2018, memo 07).
- x_4 = **Cumulative module-temperature × time** (°C·days above 25 °C) — sensor or pvlib-modeled; the Karin Arrhenius driver.
- x_5 = **Cumulative specific-humidity exposure** (g/kg·days) — from the system's Karin H-zone mean specific humidity × elapsed time (memo 20 §3 boundaries).

**Time-binning convention:** Monthly aggregation for x_1, x_2, x_3, x_4, x_5 (≥24 monthly bins required per §11). PLR computed over the full per-system monthly series.

**Soiling separation (opportunistic):** Where sensor cadence permits, `rdtools.soiling` (Deceglie soiling SRR) extracts a soiling component so that x_1 trajectory degradation is intrinsic-degradation-dominant, not soiling-dominant. Flagged per-system; not required for primary verdict.

---

## 5. Response-function variables (LOCKED)

Per RMD-SRC §Step 3:

```
x_j(e_i) = α + β_g · ∇g(e_i) + β_s · ρ_s(e_i) + β_x · ρ_x(e_i) + ε_i
```

**∇g (gradient field) for fleet PLR:**
∇g_i = β_g1 · insolation_i + β_g2 · T_module×time_i + β_g3 · humidity_i + β_g4 · (T_module × humidity) interaction

The T×humidity interaction is pre-registered as a CANDIDATE mediator: hydrolytic + thermal degradation modes (backsheet, encapsulant, PID) are jointly accelerated by heat AND moisture (T13-30 mechanisms, memo 17).

**ρ_s (same-cell density):** ρ_s_i = fraction of systems in the same ℙ₀ cell as e_i within the same `site_location` cluster — tests **fleet/portfolio reinforcement** (systems from the same developer/portfolio in the same zone aging coherently, e.g., shared O&M, shared module batch).

**ρ_x (cross-cell density):** ρ_x_i = fraction of co-located (`site_location`-shared) systems NOT in the same ℙ₀ cell — tests whether mixed-design co-located portfolios show interaction.

---

## 6. Trajectory classification (LOCKED — inherited from RMD-SRC §Step 2)

| Regime | μ̇ pattern | σ̇² pattern | Implied rule | Fleet-PLR interpretation candidate |
|---|---|---|---|---|
| Stationary | μ̇ ≈ 0 | σ̇² ≈ 0 | Equilibrium | No measurable degradation; PLR ≈ 0 within noise |
| Gradient-tracking | μ̇ matches gradient | σ̇² ≈ 0 | Classical / Maxwell-Boltzmann | PLR follows climate-stress gradient — **the Jordan 2022 expectation** |
| Concentrating (boson) | μ̇ toward equilibrium | σ̇² < 0 | Network attraction | Same-zone/same-portfolio systems converging in PLR |
| Diffusing (fermion) | μ̇ away from gradient | σ̇² > 0 | Anti-clustering | PLR dispersing within a zone (heterogeneous module/BOM mix) |
| Fragmenting | irregular | σ̇² > 0, polymodal | Mixed cell; decompose | Cell mixes cell-architectures / vintages; trigger Step 4 |

Each (cell c, observable j) trajectory Γ_{c,j} classified into one regime.

**Substrate prior:** Because cell-architecture is uncontrolled (§1), the **Fragmenting** regime is expected to be common in coarse ℙ₀ cells that mix module technologies — Step 4 decomposition on the *available* siting axes is the test of whether siting alone cleans them, or whether the residual fragmentation is architecture-driven (irreducible without architecture metadata).

---

## 7. Sub-decomposition priority order (LOCKED)

Per RMD-SRC §Step 4 cheapness order:

- **4a (categorical):** Split cell on additional §3 categoricals. Sequence: **mounting (A_MOUNT) first** (roof-vs-ground is the largest known PLR modifier via operating temperature, memo 20 roof/rack split), then **tracking (A_TRACK)**, then **capacity class (A_CAP)**, then **tilt/azimuth (A_TILT, A_AZ)**, then **vintage (A_VINT)**.
- **4b (time-phase):** Split on temporal windows. Pre-locked candidate boundary: year-1 (LID/break-in) vs steady-state (post-year-1), per the well-known break-in + stabilization PLR phases.
- **4c (mixture):** Latent-class analysis on response-function residuals — the *de facto* test for uncontrolled cell-architecture clustering.

**Pre-reg constraint:** One decomposition strategy per node; choice rule = 4a→4b→4c sequence; logged per decomposition.

---

## 8. Pre-registered hypotheses (LOCKED)

### H1 — PVCZ temperature zone dominates PLR variance; hotter zones degrade faster (REPLICATION of Jordan 2022)

**Prior:** Jordan 2022 (memo 16) found credibly-higher PLR in hotter PVCZ T-zones at p<0.001: T3 −0.48 / T4 −0.78 / T5 −0.88 %/yr (Al-BSF ground-mount, n=1528 inv). PVDAQ overlaps but is not identical (mixed technology, mixed mounting).

**Test:** On the A_PVCZ_T × A_PVCZ_H primary partition, regress per-system PLR on T-zone, controlling H-zone + mounting + tracking. Test (a) variance attributable to T-zone and (b) monotone hotter→faster ordering T2≥T3≥T4≥T5≥T6 (more negative PLR).

**Falsification gates:**
- **CONFIRMED:** η²_partial(T-zone) > 0.20 AND monotone hotter→faster holds across ≥4 adjacent T-zones at p<0.01
- **PARTIAL:** η²_partial(T-zone) ∈ [0.08, 0.20] OR monotone trend holds but η² weak
- **REFUTED:** η²_partial(T-zone) < 0.08 AND no monotone trend

### H2 — Hot zones (T5-T6) exhibit Gradient-tracking regime dominance

**Prior:** If PLR tracks the thermal/insolation gradient (Jordan 2022 mechanism), hot-zone systems should classify as Gradient-tracking (μ̇ matches ∇g, σ̇²≈0), not Stationary or Diffusing.

**Test:** Within T5-T6 cells, classify trajectory regime per system. Count fraction Gradient-tracking.

**Falsification gates:**
- **CONFIRMED:** ≥50% of T5-T6 systems classified Gradient-tracking
- **PARTIAL:** 25-50% Gradient-tracking
- **REFUTED:** <25% Gradient-tracking OR Fragmenting dominates (→ architecture confound swamps climate signal)

### H3 — Roof mounting elevates PLR vs ground at matched T-zone (operating-temperature mechanism)

**Prior:** Karin 2019 distinguishes roof vs rack equivalent temperature (roof ~10 °C hotter; memo 20 §2). Per the §3.1 mounting-coherent rule, roof systems sit in hotter effective T-surfaces. Within a matched *ambient* T-zone, roof-mount should degrade faster than ground.

**Test:** Pair roof vs ground systems within matched A_PVCZ_T (rack-basis ambient), compare median PLR.

**Falsification gates:**
- **CONFIRMED:** roof PLR more negative than ground by ≥0.15 %/yr at matched zone, p<0.05
- **PARTIAL:** roof more negative by 0.05-0.15 %/yr OR p∈[0.05,0.15]
- **REFUTED:** no difference or ground degrades faster

### H4 — Tracking shows NO PLR difference vs fixed (PRE-REGISTERED NULL REPLICATION of Jordan 2022)

**Prior:** Jordan 2022 found tracked Si + CdTe show no statistical PLR difference vs fixed-tilt (p>0.49; memo 16, CLM-FLEET-TRACKER-NULL). This is a pre-registered NULL — we expect to *fail to reject*.

**Test:** Compare PLR distribution fixed vs tracking, controlling T-zone.

**Falsification gates:**
- **CONFIRMED (null replicated):** no credible PLR difference, p>0.05, |Δmedian| < 0.10 %/yr
- **PARTIAL:** marginal difference 0.10-0.20 %/yr OR p∈[0.01,0.05]
- **REFUTED (null broken):** credible PLR difference |Δ|>0.20 %/yr at p<0.01 — a *departure* from Jordan 2022 worth reporting

### H5 — Humidity (H-zone) axis is underpowered/INDETERMINATE at PVDAQ N (REPLICATION of Jordan 2022 humidity-null)

**Prior:** Jordan 2022 found the humidity axis trend UNCONFIRMED due to geographic skew (memo 16, CLM-FLEET-CLIMATE-H). PVDAQ is worse: H3 holds 82% of systems, H5=0, H1/H2/H4 sparse (memo 22 §2). We pre-register that H-zone will be underpowered.

**Test:** Regress PLR on H-zone controlling T-zone; assess power (achieved cell counts) + effect credibility.

**Falsification gates:**
- **CONFIRMED (indeterminacy replicated):** H-zone η²_partial < 0.05 OR ≥2 H-zones below n_c=50 (underpowered as predicted)
- **PARTIAL:** weak credible H-zone effect emerges (η² ∈ [0.05,0.12])
- **REFUTED (surprise signal):** strong credible H-zone effect η²>0.12 despite skew — a *positive surprise* worth reporting (PVDAQ humidity coverage better-resolved than expected)

---

## 9. RMD-SRC universal falsifiers (inherited)

- **RMD_F1 (initial partition cleanness):** If ≥80% of ℙ₀ cells are clean at Step 3 without decomposition → fleet PLR doesn't need RMD; a flat climate-zone regression suffices (and Jordan 2022's GLM framing is sufficient — no RMD value-add).
- **RMD_F2 (decomposition convergence):** If decomposition produces leaves at minimum-cell-size limit without cleanness on ≥50% of original cells → RMD framework fails on fleet PLR (likely architecture-confound-limited).
- **RMD_F3 (validation agreement):** If trajectory classification and response-function fit disagree on ≥30% of leaves → internal inconsistency.
- **RMD_F4 (predictive transfer):** Leaf classifications trained on early monthly window should predict later window; r<0.4 in holdout → overfit.

---

## 10. Substrate-specific falsifiers (LOCKED)

- **F_Fleet_1 (no-signal):** If fleet median |PLR| < 0.1 %/yr OR bootstrap CIs are so wide that >70% of systems have PLR CI crossing zero → PVDAQ data quality / normalization insufficient for a PLR partition. Report as a data-quality finding and stop; revisit normalization choices in a follow-up pre-reg.
- **F_Fleet_2 (climate-null vs anchor):** If H1 returns REFUTED (T-zone η²<0.08, no monotone trend), this *contradicts* Jordan 2022 on an independent fleet. Disposition: investigate whether (a) PVDAQ's technology/mounting mix masks the climate signal Jordan isolated in a single-technology cohort, or (b) the anchor finding is fleet-specific. Either way → notable, document fully (do NOT silently discard).
- **F_Fleet_3 (replication inversion):** If hotter T-zones show credibly *lower* PLR (opposite of Jordan 2022) at p<0.01 → research-critical inversion. Substrate publishes immediately with its own follow-up pre-reg.

---

## 11. Termination thresholds (LOCKED)

Per RMD-SRC §Step 5:

- **Minimum cell size:** n_c ≥ 50 systems per leaf for VERIFIED trajectory classification. (Memo 22 §2: only ~4-6 PVCZ cells individually clear this; aggregation per §7 expected.)
- **Residual-variance threshold for "clean":** σ²_residual ≤ 0.25 · σ²_marginal at the leaf.
- **Time-bin minimum:** ≥24 monthly bins per system (the years≥5 inclusion gives ≥60 bins for qualifying systems).

Cells failing minimum size enter "incompletely decomposed" with a labeled residual; not silently dropped.

---

## 12. Verdict reporting protocol (LOCKED)

Each hypothesis verdict reported as **CONFIRMED / PARTIAL / REFUTED / INDETERMINATE** per §8 gates.

Aggregate over H1-H5:
- ≥4/5 CONFIRMED: PVDAQ replicates+extends Jordan 2022 under RMD-SRC; methodology note drafted.
- ≤2/5 CONFIRMED: framework or fleet-suitability needs revision; deviation log + amendment.
- Mixed: report as-is, no umbrella verdict.

Falsifiers (RMD_F1-4 + F_Fleet_1-3) reported independently; any firing triggers its disposition.

Pre-reg discipline: results table reports H1-H5 + all falsifier verdicts BEFORE narrative interpretation, per `01_METAPREREG_v1.0`.

**Replication framing (LOCKED):** H1 and H4 are explicit replication tests of Jordan 2022 (climate-temperature signal + tracker null). H5 is a replication of Jordan's humidity indeterminacy. The result write-up reports concordance/discordance with Jordan 2022 per-hypothesis.

---

## 13. Deviation log

| Date | Deviation | Rationale |
|---|---|---|
| 2026-05-27 | **Observation window fixed to 2018-2023 (NSRDB v4 GOES CONUS coverage).** §4 x_3 specified "NSRDB-modeled" irradiance for normalization. At acquisition: NSRDB **v4 GOES CONUS** covers 2018-2023 only (GOES-16/17 era); legacy PSM **v3** (1998-2020) is a different irradiance product. Splicing v3+v4 within a single system's PI series would inject a product-discontinuity step that corrupts YoY degradation. Chose v4-only → a **uniform 2018-2023 window across the whole fleet**. All 1288 cohort systems retain ≥2 yr in-window (1253 ≥3 yr); all 1151 systems in the 5 viable PVCZ cells fully retained. | (a) Single consistent irradiance product avoids version-seam bias. (b) Uniform calendar window controls for climate-year confounds across the fleet. (c) **Noted consequence:** a fixed calendar window observes different-vintage systems at different life-stages (a 2012-vintage system contributes its years 6-11; a 2019-vintage system its years 0-4 incl. LID break-in). The A_VINT ℙ₀ axis (§3) captures this; §7 4b year-1-vs-steady-state split is the decomposition lever if life-stage confounds a leaf. PLR estimated here is therefore a **mid-life-weighted steady-state PLR**, not a lifetime-from-install PLR. |
| 2026-05-27 | **Normalization model fixed (per §15 #6 acquisition-time choice):** measured PVDAQ daily AC energy ÷ pvlib PVWatts DC expected energy, NSRDB irradiance → Hay-Davies POA transposition → SAPM open-rack cell temp → PVWatts DC (gamma_pdc −0.0047/°C, Pdc0 = dc_capacity_kW). | Residential PVDAQ tier has daily AC energy only (no on-site irradiance/temp — memo 22 §3 / acquisition finding). PVWatts expected-energy normalization with satellite irradiance is the standard fleet-PLR approach when on-site sensors are absent. Constant inverter efficiency + level offset cancel under YoY differencing; clipping (DC/AC>1) acknowledged residual (§17). |

(v1.0 lock SHA `165342b` unchanged; these are acquisition-time operationalizations logged per discipline, not scope amendments.)

---

## 14. Operational protocol (LOCKED execution order)

1. **Lock this pre-reg at commit.**
2. **Cohort assembly:** Filter PVDAQ index per §1 inclusion (qa pass + years≥5 + channel-sufficient). Count retained N.
3. **ℙ₀ partition assignment:** Per §3 + §3.1, exogenous metadata only. NO outcome inspection during assignment.
4. **Observable acquisition:** Pull per-system time series from PVDAQ S3 (`s3://oedi-data-lake/pvdaq/`); build monthly x_1, x_2 + env gradient x_3-x_5.
5. **PLR computation:** `rdtools` YoY per system with bootstrap CI.
6. **Step 1 moment-flow:** (μ, σ²) trajectories per (cell, observable).
7. **Step 2 trajectory classification:** Per §6.
8. **Step 3 response-function fit:** Per §5.
9. **Step 4 sub-decomposition** if not-clean: per §7.
10. **Step 5 termination:** Per §11.
11. **Step 6 cross-cell mechanism inference.**
12. **Hypothesis verdicts:** H1-H5 + F_Fleet_1-3 + RMD_F1-4 per §12, with Jordan 2022 concordance table.
13. **Write up `result_v1.0_FleetPLR_PVCZ_RMDSRC.md`.**

---

## 15. Threats to validity (acknowledged)

1. **Cell-architecture is uncontrolled** (PVDAQ index lacks it, memo 22 §3). Climate signal is estimated *across* a technology mix; architecture variance enters as residual / Fragmenting. This is the central confound — H2/RMD_F2 are partly tests of whether it swamps the climate signal.
2. **System-level vs module-level PLR** (Jordan 2022 framing, CLM-FLEET-MEDIAN-FRAMING): PVDAQ meter/inverter data is system-level; system PLR composites module degradation + BOS + availability. PLR magnitudes are not directly comparable to module-level lab rates.
3. **Coverage gaps:** PVDAQ has zero T7-T10 (very hot) and zero H5 (tropical) coverage (memo 22 §2). H1's hot-tail and any tropical-humidity test are out of reach; H5 indeterminacy is partly structural.
4. **Soiling/availability confound:** Intrinsic degradation can be conflated with soiling trend or inverter-downtime. `rdtools.soiling` + `rdtools.availability` partially separate; residual conflation possible.
5. **PVCZ cell sparsity:** Only ~4-6 PVCZ cells clear n_c=50 individually; most inference rides on T3:H3 + T4:H3 (78% of data). Hotter/drier/wetter zones are thin → wide CIs.
6. **Normalization model dependence:** rdtools normalization choice (clearsky vs measured POA vs PVWatts expected) affects PLR; the choice is fixed at acquisition and logged, but is a researcher degree of freedom acknowledged here.

---

## 16. Cross-pre-reg coordination

Shares the meta-pre-reg + RMD-SRC framing with:
- `19_PREREG_v1.0_TOPCon_UVID` (Probe 1) — sibling; if TOPCon cohort is later identified *within* PVDAQ, Probe 1 and Probe 2 partition the same data lake on different axes (cell-tech vs climate).
- Future soiling × GHI/climate pre-reg (Probe 3 candidate; Ilse 2019 anchor).
- Future encapsulation-degradation pre-reg (Probe 4 candidate; T13-30 Sen et al.).

This probe may surface PVCZ cell-aggregation rules that downstream pre-regs reuse.

---

## 17. Explicitly NOT covered

- Cell-architecture attribution (PVDAQ lacks the field; separate cohort-identification work).
- The DuraMAT/Jordan 2022 *exact* systems (this is an independent-fleet replication, not a re-analysis of Jordan's data).
- Inverter-clipping / DC-AC ratio effects on apparent PLR (acknowledged residual).
- LCOE / financial questions (downstream applied work).
- Manuscript-prose writing (user-authored).

---

**Locked at commit:** `165342b` on `main`.
**Repository scope:** D:/Renewables/Solar/.
**Author of v1.0 draft:** Claude (LLM) per meta-pre-reg §8 — every claim is subject to operator endorsement and §3 verification when applied to field data.
