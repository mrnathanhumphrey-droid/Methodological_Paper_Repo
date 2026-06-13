# 03 — RMD-SRC × Solar Substrate Framing v0

> **STATUS:** NEEDS-VERIFICATION per `01_METAPREREG_v1.0` §8 — this doc was LLM-written
> from operator-supplied source documents (`D:/Resolve Research/founding ethos.docx` +
> `D:/Resolve Research/RMD SRC Algorithm Specification.docx`, both 2026-05-27).
> Operator endorsement required before any claim here moves out of NEEDS-VERIFICATION.

**Purpose:** map the RMD-SRC algorithm's input requirements onto solar field-data sources, and re-frame the solar substrate work in this folder as an RMD-SRC application (not a generic solar lab).

**References (operator-supplied):**
- `D:/Resolve Research/founding ethos.docx` (Resolve Research)
- `D:/Resolve Research/RMD SRC Algorithm Specification.docx` — Humphrey, May 2026 working draft

---

## 1. What the solar substrate is FOR

The solar lab is the next-substrate application of RMD-SRC after the existing ledger (Collatz / NBA / DNC / physics detector / cancer subtypes / migration). Solar provides:

- **Large event N:** O(10⁸) installed PV modules globally (~1 TW capacity at ~400 W/module). Field-monitoring data exists for sub-fractions of this.
- **Long temporal panel:** 10-30 year operating windows; sufficient T for moment-trajectory computation.
- **Multi-dimensional observable vector x_i per event:** electrical (IV-curve features, DC + AC output), optical (EL imaging, IR thermography), environmental (irradiance, temperature, soiling), discrete-event (failure mode tags).
- **Natural exogenous categorical structure for ℙ₀:** cell technology × manufacturer × vintage × climate-class × mounting-style. Each axis is observable before any outcome is measured.
- **Cross-cell density structure:** spatially co-located installations enable ρ_x computation; per-installation neighborhoods enable ρ_s.

Solar therefore satisfies the substrate requirements RMD-SRC needs to either succeed or be falsified.

## 2. RMD-SRC step mapping to solar

### Step 0 — Initial partition ℙ₀

Candidate exogenous partition axes for solar, in order of expected importance per the v0 landscape pool (all currently NEEDS-VERIFICATION):

- **Cell technology:** Al-BSF / PERC / TOPCon / HJT / perovskite-Si tandem / CdTe / a-Si / CIGS
- **Manufacturer batch:** specific manufacturer × production-year cohort (recall cohorts in particular: AAA-backsheet 2015-2020 vintage is one such)
- **Climate class:** Köppen classification, or simplified to {hot-humid / hot-arid / temperate / cold-cold-snowy}
- **Mounting configuration:** fixed-tilt / single-axis tracker / dual-axis tracker / rooftop-constrained-airflow / bifacial
- **Installation vintage:** install year (degradation envelope shifts as cell technology evolves)

Operator decision required: which axes enter ℙ₀ vs which are observables x_j. Pre-reg constraint: this is locked BEFORE any outcome moment is computed.

### Step 1 — Per-cell moment-flow computation

For each (cell c ∈ ℙ₀, observable j) pair, compute trajectory (μ_{c,j}(t), σ²_{c,j}(t)) across time bins.

Candidate observables x_j for solar:
- **Normalized DC yield** (kWh/kWp/yr or %-of-nameplate); the primary degradation observable
- **IV-curve fingerprint features:** I_sc, V_oc, fill factor, series resistance, shunt resistance — extracted on a periodic schedule
- **EL signature:** binary fault indicators or continuous defect-fraction metrics from electroluminescence imaging
- **Module operating temperature** (back-of-module thermocouple): captures climate × mounting interaction
- **Soiling ratio:** ratio of soiled to clean reference panel
- **Discrete failure events:** time-to-event for known failure modes (inverter failure, junction box fault, cell-crack-induced power loss, backsheet failure)

Time-bin granularity: monthly or annual depending on the observable. Annual aligns with degradation literature convention.

### Step 2 — Trajectory classification

The 5 regimes from RMD-SRC Step 2 map to candidate solar phenomena (all NEEDS-VERIFICATION):

| Regime | Solar interpretation candidate |
|---|---|
| Stationary | Steady-state operation; cell is at performance plateau (post-LID stabilization) |
| Gradient-tracking | Modules following expected degradation gradient (climate × cell-tech) without surprise |
| Concentrating (boson-like) | Same-cohort failures clustering — installation-batch defects propagating across spatially close modules |
| Diffusing (fermion-like) | Anti-clustering — modules in same string with shading-mismatch effects (one weak module displaces neighbors' operating point); thermal-mismatch dispersion |
| Fragmenting | Cell contains mixed sub-populations (e.g., a manufacturer cohort actually contains two production batches with different failure modes) → triggers Step 4 sub-decomposition |

The boson/fermion language is from RMD-SRC's statistical-rule terminology; physical interpretation is what's mapped above.

### Step 3 — Response-function validation

Solar-specific response function:
```
x_j(e_i) = α + β_g · ∇g(e_i) + β_s · ρ_s(e_i) + β_x · ρ_x(e_i) + ε_i
```

Where:
- **∇g** = the climate/operating gradient acting on the module — irradiance dose, temperature dose, humidity exposure, UV dose accumulated over the time bin
- **ρ_s** = same-cell density at module location — count of same-(cell-tech × manufacturer × vintage) modules within a defined spatial neighborhood; tests whether batch-cohort reinforcement is present
- **ρ_x** = cross-cell density — count of OTHER-cell modules within same neighborhood; tests whether substrate-cell interactions exist (e.g., one cell type accelerating failure in adjacent different-cell modules through shading or thermal coupling)

The validation question: does fitted β_s on the response function agree with the Step 2 trajectory classification?

### Step 4 — Sub-decomposition strategies for solar

Following RMD-SRC §4 cheapness order:

- **4a (categorical):** Split a cell on additional categoricals (e.g., split "PERC 2018-2020 vintage" into specific manufacturers + production months when batch metadata is available).
- **4b (time-phase):** Split on temporal windows (e.g., pre-2018 / post-2018 if a manufacturing-process change creates a phase boundary).
- **4c (mixture):** Latent class on observable residuals when batch metadata is unavailable but the cell still fragments.

Operator pre-reg decision: which decomposition axes are in scope before running.

### Step 5 — Termination thresholds (operator-pre-reg)

- Minimum cell size n_c: candidate 50-100 events per leaf depending on observable noise level (operator decides).
- Residual variance threshold for "clean": operator-decided; convention to be borrowed from existing RMD-SRC substrate applications.

### Step 6 — Cross-cell mechanism inference

What we'd expect to learn from solar:
- If most leaves are classical: solar degradation is well-explained by gradient response alone; the field's existing modeling stack (SAM, PVsyst, climate-physics-based degradation models) is sufficient.
- If a coherent subset of leaves is boson-like: manufacturing-batch defects + spatial clustering of failures matter materially; lab should focus on batch-tracing diagnostics.
- If a coherent subset is fermion-like: string-level / inverter-level interactions matter more than module-level alone.
- If many leaves are time-phase-fragmenting: cell-technology generational transitions (Al-BSF → PERC → TOPCon → HJT → perovskite-Si tandem) create non-stationarity that gradient models miss.

## 3. RMD-SRC pre-registered falsifiers as applied to solar

- **F1 (initial partition cleanness):** If ≥80% of ℙ₀ cells are clean at Step 3 without decomposition, solar doesn't need RMD-SRC; gradient response alone suffices. Reports as the classical-substrate disposition.
- **F2 (decomposition convergence):** If decomposition hits minimum-cell-size without cleanness on ≥50%, framework fails on solar. Substrate "decomposition-resistant"; methodology reported as not applicable.
- **F3 (validation agreement):** If trajectory classification and response-function fit disagree on ≥30% of leaves after decomposition, internal inconsistency.
- **F4 (predictive transfer):** Leaf classifications trained on [t₁, t₂] should predict leaf behavior on [t₂, t₃]; r < 0.4 in holdout falsifies.

These are inherited from RMD-SRC; the solar substrate adds the substrate-specific data definitions but does not modify the falsifiers themselves.

## 4. Solar lab spec — re-framed under RMD-SRC requirements

The v0 landscape's lab requirements **were already RMD-SRC compatible**, but the framing changes:

| Lab requirement | RMD-SRC role |
|---|---|
| Multi-climate sites (≥3 climate classes) | ℙ₀ climate axis with sufficient cell counts per class |
| ≥5 replicates per cell type | minimum cell size n_c per leaf |
| 5+ year time horizon | sufficient T for moment-trajectory computation |
| EL + IR + IV diagnostic stack | multi-dimensional observable vector x_j per event |
| Per-site weather instrumentation | gradient field ∇g for response-function fitting |
| Module-level + string-level monitoring | enables ρ_s + ρ_x density computation at module + string scale |
| Manufacturer batch metadata access | enables Step 4a categorical sub-decomposition |
| Indoor accelerated test chambers | controls on the gradient field for response-function calibration |
| Forensic teardown capability | post-hoc verification of failure-mode classifications (regime → physical mechanism mapping) |

What needs sharpening that v0 missed:
- **Per-module spatial coordinates** matter — RMD-SRC's ρ_s + ρ_x are spatial densities. Standard system-level monitoring often doesn't preserve module-position metadata. Lab spec must require this from day one.
- **Time-binning convention** must be pre-locked at lab inception — annual bins for degradation, monthly for short-cycle observables. RMD-SRC's trajectory classification depends on this choice.
- **ℙ₀ axes must be lockable from EXOGENOUS metadata** (install records) without consulting any outcome data. This is enforceable at the data-architecture level (audit trail for partition-axis selection).

## 5. Public datasets that already provide RMD-SRC-shaped inputs (candidates)

The subagent landscape reports (in flight) will surface specific datasets and their access requirements. Candidates from the v0 landscape pool — all NEEDS-VERIFICATION:

- **NREL PVDAQ** (PV Data Acquisition) — public field-monitoring data from multiple sites; spatial granularity unknown until access
- **NSRDB** (National Solar Radiation Database) — gradient field ∇g component
- **DuraMAT** consortium data — module reliability with metadata
- **IEA-PVPS Task 13 field surveys** — failure-mode tagged event data
- **EU JRC PVMD** — European field-monitoring repository
- **CFV Solar Test Laboratory data** — accelerated-test + outdoor cohort data

Access-verification pass needed before any of these enters the substrate as a primary data source.

## 6. Open framing questions for operator

1. **ℙ₀ axis selection.** Which categoricals enter the initial partition for solar's RMD-SRC application? Cell-tech × climate × manufacturer is the obvious triple but creates ~50-100 cells immediately; minimum cell size constraint will collapse some.
2. **Primary observable x_j.** Is normalized DC yield the headline observable, with everything else as secondary? Or are EL-derived defect fractions primary because they're more mechanistically interpretable?
3. **Time-binning convention.** Annual / monthly / daily?
4. **Migration substrate status.** RMD-SRC spec lists migration as next falsification target; solar is the substrate I'm scoping. Are these parallel substrates (different teams), or is solar replacing migration in the queue, or both are queued?
5. **Lab capex constraint.** v0 sketch quoted mid-7 to low-8 figures; this drives ℙ₀ resolution (more cells × replicates × sites = more capex). Operator constraint here shapes Step 5 minimum-cell-size feasibility.

---

## 7. What this re-framing doesn't yet do

- Replace `00_LANDSCAPE_v0.md` claims with verified primary citations (separate verification passes per meta-pre-reg §3).
- Lock the solar scientific pre-reg (this is FRAMING, not a pre-reg — the scientific pre-reg is downstream).
- Define ℙ₀ axes or thresholds (requires operator decision per §6.1, §6.2, §6.3).
- Audit the lab spec capex / opex under RMD-SRC's specific data requirements (per-module spatial metadata may add cost not in v0 estimate).

These move into v0.1+ work as operator direction lands.

---

**Next concrete steps**

1. Operator endorsement (or revision) of the framing in this doc.
2. Subagent landscape reports (3 in flight) return; their primary-source citations get logged into `02_CLAIMS_LEDGER.md`.
3. Operator selects ℙ₀ axis set + primary observable + time-binning convention → these become the FIRST scientific pre-reg (`04_PREREG_v1.0_solar_initial_partition.md`).
4. Public-dataset access verification (NREL PVDAQ first, since it's the closest match to RMD-SRC's data shape).
