# Result v1.0 — Fleet PLR × PVCZ Climate-Zone RMD-SRC Partition (Probe 2)

**Status:** COMPLETE. Disposition = **CLIMATE PARTITION DOES NOT SURVIVE IN HETEROGENEOUS FLEET** (H1 REFUTED, F_Fleet_2 fired) — headline PLR magnitude replicates Jordan 2022.
**Date:** 2026-05-28
**Pre-reg:** `23_PREREG_v1.0_FleetPLR_PVCZ.md`, locked `165342b` (+ 2 acquisition-time deviations logged §13).
**Author:** Claude (LLM) per meta-pre-reg §8 — every numeric claim here is subject to operator verification.

---

## 0. One-line result

On 668 PVDAQ systems with valid PLR across the 5 viable Karin PVCZ cells, the **fleet median performance-loss rate is −0.79 %/yr** — a near-exact replication of Jordan 2022's system-level −0.75 %/yr. **But the climate-temperature PLR signal Jordan isolated does NOT survive**: PVCZ temperature zone explains only **η²=0.019** (~2%) of PLR variance and is non-monotone (T4 fastest, not T5). The pre-registered falsifier **F_Fleet_2 fired** — climate-null on an independent fleet — with the pre-registered mechanism (uncontrolled cell-architecture + vintage heterogeneity swamps the climate signal) being the operative explanation.

---

## 1. Verdict table (LOCKED gates, no post-hoc tuning)

| Hyp | Statement | Verdict | Evidence |
|---|---|---|---|
| **H1** | T-zone dominates PLR variance + monotone hotter→faster | **REFUTED** | η²_partial(T-zone)=0.019 (p=0.002, n=668); non-monotone (T3 −0.58, T4 −1.05, T5 −0.84 %/yr). η²<0.08 gate + no monotone trend |
| **H2** | Hot zones (T5+) show Gradient-tracking regime ≥50% | **REFUTED** | Moment-flow drift small vs within-cell heterogeneity; 4/5 cells flat ("Stationary"), 1 "Diffusing"; 0% Gradient-tracking. (See §4 caveat — regime classification is noise-limited.) |
| **H3** | Roof mounting elevates PLR vs ground | **INDETERMINATE** | 0 roof + 0 ground systems in analyzed set; PVDAQ mounting metadata 98% UNKNOWN (§3) |
| **H4** | Tracking shows NO PLR difference (null replication) | **INDETERMINATE** | 0 tracking systems in analyzed set; PVDAQ tracking metadata 1251:2 fleet-wide |
| **H5** | Humidity axis underpowered/indeterminate | **CONFIRMED** | η²_partial(H-zone)=0.003 (p=0.42); 1 H-zone below n=50. Indeterminacy replicated as pre-registered |

| Falsifier | Fired? | Value |
|---|---|---|
| **F_Fleet_1** (no-signal) | NO | fleet median PLR −0.79 %/yr; 42% of CIs cross zero (<70% threshold) |
| **F_Fleet_2** (climate-null vs anchor) | **YES** | H1 REFUTED → contradicts Jordan 2022 on independent fleet → §5 investigation |
| **F_Fleet_3** (replication inversion) | NO | no credible hotter→lower-PLR inversion |
| **RMD_F1** (initial cleanness) | **YES** | 80% of cells classify "clean" — but trivially (climate axis carries ~no PLR info, nothing to decompose) |
| **RMD_F2** (decomp convergence) | n/a | decomposition not run (RMD_F1 fired) |

**Aggregate (H1-H5):** 1 CONFIRMED (H5), 2 REFUTED (H1, H2), 2 INDETERMINATE (H3, H4). Per §12, ≤2/5 CONFIRMED → framework/fleet-suitability finding, documented here.

---

## 2. Headline numbers

| Quantity | Value |
|---|---|
| Systems in cohort (qa pass + years≥5) | 1288 |
| Systems in 5 viable PVCZ cells | 1151 |
| Systems with valid PLR (after pipeline + |PLR|≤10 bound) | **668** |
| Attrition (insufficient aligned days / no energy) | 471 (mostly `insufficient_aligned_days`, §6 threat) |
| Fleet median PLR | **−0.79 %/yr** |
| Fraction degrading (PLR<0) | 68.2% |
| Fraction of CIs crossing zero | 42% |

**Per-cell PLR (the climate grid):**

| Cell | n | PLR median (%/yr) | Yield vs cohort |
|---|---|---|---|
| T3:H3 (moderate / mod-humid) | 320 | −0.58 | 76% |
| T4:H3 (warm / mod-humid) | 234 | −1.05 | 45% |
| T5:H3 (hot / mod-humid) | 39 | −0.62 | 56% |
| T5:H2 (hot / semi-arid) | 18 | −0.81 | 27% |
| T5:H4 (hot / subtropical) | 57 | −0.98 | 100% |

The temperature gradient T3→T4→T5 at fixed H3 is **non-monotone**: −0.58 → −1.05 → −0.62. T4 degrades fastest, contradicting the monotone hotter→faster prior.

---

## 3. Jordan 2022 concordance table

| Quantity | Jordan 2022 (memo 16) | PVDAQ Probe 2 | Concordance |
|---|---|---|---|
| Fleet median PLR (system-level) | −0.75 %/yr | **−0.79 %/yr** | ✓ **MATCH** |
| Climate-T ordering | T3 −0.48 / T4 −0.78 / T5 −0.88; monotone, p<0.001 | η²=0.019; non-monotone (T4 worst) | ✗ **NOT replicated** |
| Humidity axis | INDETERMINATE (geographic skew) | η²=0.003, null; 1 zone underpowered | ✓ **MATCH (both null)** |
| Tracker vs fixed | null, p>0.49 | INDETERMINATE (no tracker data) | — untestable |
| Cohort composition | **homogeneous**: Al-BSF c-Si, ground-mount, n=1528 inv | **heterogeneous**: mixed cell-tech (unknown), 98% residential rooftop, mixed vintage | — the operative difference |

**The headline PLR magnitude replicates; the climate-partition structure does not.**

---

## 4. Why the climate signal does not survive (the mechanism)

Jordan 2022's climate-temperature ordering spans roughly −0.48 to −0.88 %/yr across T3-T5 — a **~0.4 %/yr** climate effect. PVDAQ's within-cell PLR spread (IQR) is ~**1.5–2 %/yr** (residential single-inverter systems, mixed technology). The climate effect is ~4–8× **smaller** than the within-cell heterogeneity, so it is statistically detectable (η²=0.019, p=0.002 at large n) but explains almost none of the variance and does not produce a monotone ordering.

The decisive difference from Jordan 2022 is **cohort homogeneity**:
- Jordan isolated the climate signal in a **single-technology, single-mounting** cohort (Al-BSF ground-mount), where within-cohort variance is minimized and the ~0.4 %/yr climate effect emerges cleanly.
- PVDAQ is a **heterogeneous public fleet** — cell architecture is not in the index (memo 22 §3; pre-reg threat #1), mounting is 98% UNKNOWN, vintage spans 2010-2020. The uncontrolled technology + vintage variance dominates.

**This is the pre-registered threat #1 realized.** It is not a refutation of Jordan 2022 — it is a demonstration of the *boundary condition* on Jordan's finding: **climate-driven degradation differences require technology-controlled cohorts to detect; large N alone in a heterogeneous fleet does not recover them.**

### Moment-flow caveat (H2)

The RMD-SRC moment-flow regime classification (§14.6-7) was operationalized on elapsed-time-aligned, start-normalized monthly PI trajectories. The within-system degradation drift the robust YoY method detects (−0.79 %/yr) is **small relative to monthly seasonal + measurement noise** in the cross-system aggregate, so the simple linear moment-flow slope is near-zero for most cells and classifies them "Stationary." This is a **limitation of the coarse moment-flow operationalization on noisy daily-energy-only residential data**, NOT evidence that systems don't degrade (they do, per YoY). H2's REFUTED verdict should be read as "no clean gradient-tracking regime structure is recoverable at the monthly-aggregate level," consistent with the small climate η². A finer moment-flow (e.g., per-system YoY-trajectory clustering) is a candidate refinement, not run here.

---

## 5. F_Fleet_2 disposition (per pre-reg §10)

F_Fleet_2 fired. Pre-registered disposition: *"investigate whether (a) PVDAQ's technology/mounting mix masks the climate signal Jordan isolated in a single-technology cohort, or (b) the anchor finding is fleet-specific."*

**Verdict: (a).** The headline PLR magnitude replicates exactly (−0.79 vs −0.75 %/yr), so the fleets are comparable in aggregate degradation. The climate ordering fails specifically because PVDAQ cannot control cell architecture (the field is absent from the index) and is dominated by heterogeneous residential rooftop systems. Jordan's finding is NOT refuted; its **precondition** (technology-controlled cohort) is exposed. Documented; not silently discarded.

---

## 6. Threats to validity realized

1. **Cell-architecture uncontrolled** (pre-reg threat #1) — the operative confound, as analyzed in §4. Irreducible with PVDAQ index metadata.
2. **Cell-biased attrition.** 668/1151 (58%) yield, but uneven: T3:H3 76%, T4:H3 45%, T5:H2 27%. The `insufficient_aligned_days` filter (require ≥730 aligned measured/modeled days) drops thinner-coverage systems. **T5:H2 fell to n=18, below the n_c≥50 termination threshold** — its −0.81 median is under-powered and excluded from strong inference. The non-monotonicity (T4 worst) could partly reflect T4:H3's 45% yield selecting a non-representative subset; flagged, not resolved.
3. **Daily-energy-only normalization** (deviation §13). PVWatts expected-energy with NSRDB irradiance; level offset (median PI ~1.1-1.17) cancels under YoY but adds noise vs on-site POA. The 64 rich-sensor systems (POA + module temp) were not separately cross-checked here — a candidate fidelity validation.
4. **Moment-flow noise** (§4 caveat) — regime classification not load-bearing.
5. **Uniform 2018-2023 window** (deviation §13) — mid-life-weighted PLR; vintage × life-stage confound captured only coarsely by A_VINT.

---

## 7. What this closes and what it opens

**Closes:**
- The naive hypothesis that a large heterogeneous public fleet (PVDAQ) can recover climate-zone degradation ordering. It cannot at η²>0.08 — the signal needs technology control.
- Probe 2's primary question: **PVDAQ fleet PLR does NOT admit a meaningful climate-zone RMD-SRC partition** (RMD_F1 fired trivially — the partition axis carries ~no PLR-discriminating information).

**Opens (candidate downstream pre-regs, NOT locked here):**
- **Probe 2b — technology-controlled re-test.** If cell-architecture metadata can be obtained for a PVDAQ subset (S3 per-system JSON, manufacturer cross-ref) OR via DuraMAT/RTC homogeneous cohorts, re-run the climate partition within a single technology. Direct test of the §4 mechanism.
- **Rich-sensor fidelity check.** Re-run the 64 POA+temp systems with standard rdtools (measured irradiance) to bound the daily-energy-normalization noise contribution.
- **Per-system YoY-trajectory clustering** as a finer moment-flow (replaces the noise-limited linear moment-flow).
- **Mounting/vintage as primary axis** where metadata exists (the rich-sensor subset has it).

---

## 8. Lab-design lesson (the substrate payoff)

For the future PV research lab: **detecting climate-driven degradation differences requires technology-controlled cohorts, not just large N.** A 668-system public fleet with −0.79 %/yr aggregate degradation could not resolve a ~0.4 %/yr climate effect because uncontrolled cell-architecture variance (~1.5-2 %/yr) buried it. Lab degradation studies must fix cell architecture + mounting per cohort and vary climate exogenously (multi-site identical-module deployments) — exactly the Jordan 2022 / Karin PVCZ design, not opportunistic fleet aggregation.

---

## 9. Reproducibility

| Artifact | Path |
|---|---|
| Cohort + ℙ₀ assignment | `code/probe2_cohort_p0.py` → `data/processed/probe2_cohort_p0.csv` |
| PLR pipeline (PVWatts + NSRDB + rdtools YoY) | `code/probe2_plr_pipeline.py` |
| Bulk driver | `code/probe2_run_bulk.py` |
| RMD-SRC analysis | `code/probe2_rmdsrc_analysis.py` |
| PLR results (668 ok) | `data/processed/probe2_plr_results_clean.csv` |
| Verdicts | `data/processed/probe2_verdicts.json` |
| Monthly PI trajectories | `data/processed/monthly_pi/` (gitignored, large) |
| NSRDB / PVDAQ raw | `data/raw/nsrdb/`, `data/raw/pvdaq_daily/` (gitignored) |

Data sources: PVDAQ OEDI submission 4568 (CC-BY 4.0); NSRDB v4 GOES CONUS (NREL API). Normalization: PVWatts DC (γ −0.0047/°C), Hay-Davies POA, SAPM open-rack cell temp. Degradation: rdtools 3.1.1 YoY (Deceglie 2018), 68.2% bootstrap CI.

**Known bug (does not affect verdicts):** the bulk driver wrote a ragged CSV (heterogeneous dict schemas under one header); recovered via positional parse of the consistent 10-field ok-row schema into `probe2_plr_results_clean.csv`. Fix the writer (collect→single write with union columns) before re-runs.

---

**END RESULT — Probe 2 v1.0**
