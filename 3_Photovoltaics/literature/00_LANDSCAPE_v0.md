# 00 — Solar Panel Research Landscape v0

> **⚠️ DEMOTED — 2026-05-27 per `01_METAPREREG_v1.0_evidence_discipline.md`.**
> **Every numeric and factual claim in this document is NEEDS-VERIFICATION** until processed
> through the meta-pre-reg §3 verification protocol. This document was written by an LLM
> (Claude) without primary-source citations and is treated as a HYPOTHESIS POOL, not a
> knowledge base. Do NOT cite anything here as evidence. Use `02_CLAIMS_LEDGER.md` to find
> verification status of individual claims.
>
> The document is retained in this state as a record of the starting hypothesis pool.

---

# 00 — Solar Panel Research Landscape v0

**Status:** v0 starter map, 2026-05-27. NOT authoritative. All numeric claims unverified.
**Purpose:** identify candidate facts and open questions across 3 axes, to be processed
through the meta-pre-reg's verification protocol.

This document does NOT contain verified claims — claims here are derived from LLM training
data (general field knowledge attribution to NREL Jordan-Kurtz, IEC standards, IEA-PVPS,
SAM, etc.) and require primary-source verification before any claim can be used in
downstream scientific pre-regs.

---

## Axis 1 — Degradation (yield loss over time)

### What's settled
- **Median degradation rate of crystalline Si modules in the field is ~0.5%/yr** (Jordan & Kurtz 2013, 2018). Thin-film is higher: ~0.8-1.0%/yr.
- **Year-1 LID (light-induced degradation, primarily boron-oxygen) is ~1-3%** then slows. This is a manufacturing-process issue, not aging.
- **PERC cell architectures introduced LeTID** (light + elevated temperature degradation) — initially under-modeled, now characterized.
- **Climate-specific aging is real:** hot/humid accelerates encapsulant + interconnect corrosion; arid + high-UV ages encapsulant (EVA browning); thermal cycling drives solder fatigue + cell cracks.
- **Module manufacturers publish ~25-year 80-85% power warranty curves**; field median outperforms warranty.

### Open questions a lab can address
1. **Mechanism decomposition per climate.** Given a field array showing X%/yr degradation, what fraction is encapsulant aging vs interconnect corrosion vs cell cracks vs other? Field studies report total degradation but rarely decompose. EL imaging + IR thermography + IV-curve fitting on the SAME modules over time can decompose, but few labs have multi-year cohorts.
2. **Accelerated-test-to-field translation.** IEC 61215 specifies damp-heat 1000 h, thermal cycling 200 cycles, humidity-freeze 10 cycles, UV 60 kWh/m². The translation factor to field years is contested (some claim ~25-yr-equivalent, real fields show otherwise). A lab co-located with both indoor chambers AND outdoor arrays of the same module batches can ground-truth this.
3. **Newer cell architectures (TOPCon, HJT, perovskite-Si tandem) field-degradation rates are largely unknown** — most field data is on Al-BSF or PERC. Perovskite-tandem stability under outdoor exposure is the largest open question.
4. **Non-linear / step degradation events.** Most analyses fit linear degradation; field data shows step-loss events (e.g., from extreme weather or a specific failure mode firing). A lab with high-frequency monitoring can characterize the non-linear distribution.

### Lab requirements for Axis 1
- **Outdoor test field with replicates** — minimum 5+ replicates per module type, multiple module types, ideally 3+ climate-class sites (hot-humid, arid-hot, temperate-cold).
- **Indoor accelerated chambers** — damp-heat, thermal-cycle, UV, humidity-freeze. Co-located with outdoor arrays for batched modules.
- **Diagnostic instruments** — EL imaging (electroluminescence camera), IR thermography (cooled microbolometer preferred), portable IV-curve tracer, hi-pot tester for PID detection.
- **Time horizon** — 5+ years minimum for actionable trend separation; 10+ for full-life envelope.
- **Manufacturer cooperation** — module-level metadata (cell type, batch, encapsulant material, backsheet material) often not in customer datasheets.

---

## Axis 2 — Field reliability (failure modes)

### What's settled
- **Inverter failure dominates O&M ticket volume** (~50-60% of service calls); module failure dominates **lifetime energy loss** because modules outlast inverters but lose energy continuously when degraded.
- **Cell cracking accumulates stochastically** from transport, installation, and thermal cycling. EL imaging post-installation reveals baseline crack distribution; cracks grow under thermo-mechanical stress.
- **PID (potential-induced degradation)** affects modules in high-voltage strings, particularly in humid environments without PV-grade encapsulants. Largely solved in modern modules via design changes; older fleet still exposed.
- **Backsheet failure** (PVDF browning, AAA backsheet recall era ~2015-2020) is a known cohort issue tied to specific manufacturer batches.
- **Junction box / connector failures** (MC4-type) are a non-trivial fraction of system-level outages; thermal IR scanning at scale detects these.

### Open questions a lab can address
1. **Failure-mode prior distribution as a function of installation age + climate + module vintage.** What's the conditional probability of (cell crack → measurable energy loss) given installation at year-T in climate-C? Current data is mostly cross-sectional manufacturer claims, not longitudinal field cohorts with controlled vintages.
2. **Early-warning signatures.** Can EL imaging at year 1 predict year-5 power loss? Can year-1 IV-curve features predict year-5 trajectory? This is the diagnostic-for-prognosis question; lab can build forecast models with controlled cohorts.
3. **Inverter MTBF in real climates vs datasheet MTBF.** Datasheets quote MTBF in lab conditions; real fleet failure rates often diverge 2-5x. Lab can co-monitor inverters + modules to attribute lost energy.
4. **Module-level vs string-level vs inverter-level optimizer economics.** Microinverters and DC optimizers cost more upfront but reduce shading + mismatch losses. The lifetime LCOE comparison under real failure modes is underexplored.

### Lab requirements for Axis 2
- **Drone-mounted thermal IR** for utility-scale field-wide fault detection.
- **String-level + module-level monitoring** capability (DC optimizers or microinverters on a subset of strings for hi-res failure attribution).
- **Component-level failure logging** (inverter event logs, ground-fault history, etc.) integrated into one database.
- **Forensic teardown capability** for failed modules — cross-section microscopy, IV-tracer post-failure, materials analysis (XRD / FTIR for encapsulant).
- **Standards-body access** — IEC working groups, IEEE 1547, NREL PVRW community. The reliability community is small and meets in person.

---

## Axis 3 — Siting / yield (geographic + meteorological yield drivers)

### What's settled
- **POA irradiance modeling** is mature (SAM, PVsyst, PlantPredict). DNI + DHI + ground-reflectance + albedo → plane-of-array irradiance.
- **Soiling losses** typically 1-3%/yr in temperate regions, 5-10%/yr in dust-prone (Middle East, Central Valley CA, Arizona, parts of India). Cleaning schedule + rainfall pattern govern this.
- **Module temperature loses ~0.3-0.45%/°C above STC (25°C)**. Hot climates lose more than cool ones at the same irradiance.
- **Bifacial gain** is 5-15% depending on albedo + height + row spacing. White gravel ground cover boosts substantially over grass.
- **Tracker gain** (single-axis) is ~15-25% over fixed-tilt at equivalent latitude; dual-axis trackers add another ~5-10% but cost more O&M.
- **Spectral effects** are small (~1-2% annual) but systematic in high-altitude or specific spectral-distribution climates.

### Open questions a lab can address
1. **Soiling characterization per region.** Soiling is the largest controllable yield loss and the most regional. Multi-site soiling-station network with passive deposition monitors + cleaning-vs-not controls produces actionable cleaning-schedule guidance per region. Underserved outside academic literature.
2. **Short-timescale (sub-hour) yield prediction under partly-cloudy conditions** for grid integration. Sky-imager networks + ML forecasting; performance bounded by cloud microphysics. Improving but unsolved.
3. **Bifacial yield modeling under real (non-ideal) ground covers** — albedo varies with surface moisture, vegetation, snow cover. Most models assume static albedo.
4. **Hail + extreme weather damage probability** as a function of module design (front-glass thickness, tempered vs heat-strengthened, frame design). Insurance industry has data but it's not publicly accessible at module-design granularity.
5. **Module-temperature models in dense urban or rooftop installations** (constrained airflow) systematically underestimate operating temperature vs open-rack standard.

### Lab requirements for Axis 3
- **On-site weather station** per outdoor test array — DNI (pyrheliometer with tracker), DHI (shaded pyranometer), GHI (pyranometer), wind speed, ambient T, module T (back-of-module thermocouples on multiple modules), spectroradiometer.
- **Soiling stations** — paired soiled/clean reference modules with automated IV traces. Multi-site replication for region-specific calibration.
- **Sky imager** for short-timescale cloud forecasting work.
- **Geographic diversity** — at least 3 climate classes (Köppen Bsh / Cfa / Dfb spans most of US PV deployment).
- **Modeling stack** — SAM + PVsyst licenses; pvlib-python for custom analysis; access to NSRDB and SURFRAD weather archive.

---

## Cross-axis observations (where the axes interact)

- **Degradation rate is climate-coupled** — hot-humid sites degrade faster (Axis 1 × Axis 3 interaction).
- **Failure mode distribution is climate-coupled** — PID concentrates in humid + high-voltage configurations; cracks concentrate in cold-cycle climates.
- **Yield model error compounds over time** — small soiling-estimate error grows as installations age beyond warranty.
- **The lab that can do all three is more valuable than three labs doing one each** — because the interactions are where the open questions live.

---

## Provisional lab spec (one-paragraph executive summary)

A solar-panel lab able to move the field forward needs: **(a)** an outdoor test field with ≥5 module-type replicates × ≥3 climate-class sites operating ≥5 years for degradation cohorts; **(b)** indoor accelerated-test chambers (damp-heat, thermal-cycle, UV, humidity-freeze) physically co-located with outdoor arrays for ground-truthing accelerated-to-field translation; **(c)** a diagnostic stack of EL imaging, IR thermography, IV-curve tracers, and forensic teardown capability for failure attribution; **(d)** per-site weather instrumentation (DNI pyrheliometer, DHI shaded pyranometer, ambient + module thermocouples, spectroradiometer) and soiling stations; **(e)** module-level + string-level + inverter-level monitoring infrastructure feeding into one database; **(f)** manufacturer relationships for module-batch metadata access; **(g)** standards-community participation for relevance + influence. Estimated lab capital: **mid-7-figure to low-8-figure** depending on site count and module-cohort size; estimated operating: **mid-6-figure / yr** for staff + cleaning + monitoring; estimated minimum time-to-first-result: **2 years for accelerated-test work, 5 years for outdoor degradation cohorts.**

---

## What this v0 doesn't yet address

- Specific module manufacturers + cell technologies to prioritize in the cohort
- Lab location selection (climate-class targeting vs partnership-of-convenience)
- Funding model (academic grant + industry consortium + DOE SETO + utility partnership)
- Specific accelerated tests to extend beyond IEC 61215 baseline
- IP / publication strategy
- Personnel structure (PhD scientists, technicians, software, analysts)

v0.1 should expand on at least one of these per user direction.

---

## Next-step options for v0.1

1. Lock the 3-axis scope into pre-registered hypotheses for the first 2 years of lab operation
2. Cost-out the lab capex + opex at 3 site-count tiers (1 / 3 / 5 sites)
3. Map specific NREL / Fraunhofer / IEA-PVPS existing capabilities to identify the white-space the lab fills
4. Identify the 5 most-impactful experiments the lab could run year-1
