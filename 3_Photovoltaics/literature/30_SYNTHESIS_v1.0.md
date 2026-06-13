# 30 — Solar Substrate Synthesis v1.0

**Status:** First substrate-level synthesis. Consolidates 10 probe results into one coherent map. Identifies substrate-novel findings flagged for next-session external verification.
**Date:** 2026-05-30
**Scope:** D:/Renewables/Solar/ — 2026-05-27 through 2026-05-30 work (~30 literature memos, 10 numbered probe results).

---

## 1. The arc in one paragraph

The substrate began with a meta-pre-reg locking LLM outputs out of the primary-evidence layer; verified 9 anchor papers (catching 5 attribution errors in the v0 LLM-written landscape); identified PVDAQ + NSRDB as the reachable public data; **executed Probe 2** (climate-PLR partition on 668 PVDAQ systems → replicates Jordan 2022's −0.79 %/yr magnitude but **REFUTED the climate-zone partition by underpower**); **executed Probe 2b** (quantified the mechanism — heterogeneity inflates σ_within 2× over Jordan's homogeneous cohort, costing ~6× more N); **executed Probe 3** (soiling on PVDAQ → FEASIBILITY-NULL: signal below the daily-energy noise floor); pivoted to DKA Alice Springs (arid + measured POA + multi-tech, operator-pulled 5.4 GB); **executed Probe 4** (DKA tech-controlled PLR → σ_within drops 8×, technology ordering visible — directly validates Probe 2b's lab-design prescription); **executed Probe 5** (DKA soiling → 3.87 %/yr, Ilse 2019 confirmed, PVDAQ-null vindicated); then **4 follow-up sub-probes** on the soiling result (5b rain alignment validated; 5c surprise inversion = wet > dry deposition; 5d synchrony separates natural vs operational cleaning; 5e null = soiling regime stable 12 years). End-state: a complete, internally consistent quantitative story about PV degradation + soiling at heterogeneous public fleets vs controlled arid single-site, with hard lab-design constraints quantified.

---

## 2. Findings matrix (10 probes + anchors)

### Probes (own work)

| # | Probe | Result | Key number |
|---|---|---|---|
| **2** | PVDAQ Fleet PLR × PVCZ | Magnitude replicated, climate partition REFUTED-by-underpower | −0.79 %/yr; η²=0.019 |
| **2b** | Detectability addendum | Heterogeneity quantified | σ inflation 2.0×; power 0.49; N needed ~1938 |
| **3** | PVDAQ soiling SRR | FEASIBILITY-NULL (data quality, not method) | 13–19% garbage / 2-of-3 fail |
| **4** | DKA tech-controlled PLR | Vindicates 2b prediction (8× σ tightening) | DKA σ 0.23 %/yr vs PVDAQ 1.99 |
| **4 (bonus)** | Per-phase artifact | Methodological flag | M2_A −1.39 vs M2_C −0.17 same system |
| **5** | DKA soiling | Ilse 2019 confirmed at canonical arid site | 3.87 %/yr median; 3.62 fixed |
| **5b** | Rain-event validation | 13/13 above baseline, modest lift | binomial p≈0.00012; 1.3× |
| **5c** | Seasonal pattern | **SURPRISE INVERSION**: wet > dry deposition | 0.74× ratio dry/wet; 11/13 (p=0.998) |
| **5d** | Inter-system synchrony | **NEW METHODOLOGY**: separates natural from operational cleaning | Jaccard 4.78× random; K=8 peak 25% / K=13 → 5% |
| **5e** | 12-yr temporal drift | NULL — regime stable | All p > 0.10; sign-test p = 1.0 |

### Anchors (verified literature)

| Anchor | Verified via | What it locks |
|---|---|---|
| Jordan & Kurtz 2013 | memo 08 + JK preprint | All-tech median 0.5 %/yr (closes ERR-1) |
| Jordan 2016 Compendium | memo 13 | c-Si mean 0.8–0.9 %/yr (closes ERR-2) |
| Köntges T13-09:2017 | memo 09 | Failure-mode taxonomy; lead author Köntges (closes ERR-4) |
| Köntges T13-30:2025 (PVFS + EX-SUMM + REPORT + SLIDES) | memos 14/15/17/21 | 30 failure modes; TOPCon UVID; thin glass break; IEC 62804-1 |
| Jordan 2022 PV Fleet | memo 16 | Climate-T p<0.001 at n=1528 (closes ERR-5); Karin PVCZ adoption; tracker-null |
| Karin 2019 PVCZ | memos 18 + 20 (npz extracted) | T-zone × H-zone = 50 (closes substrate memory's "250"); literal °C / g/kg cutoffs |
| Sengupta 2018 NSRDB | memo 07 | 4 km / 30-min PSM v3; v4 GOES CONUS 2018+ at 2 km / 60-min |
| Holmgren 2018 pvlib | memo 10 | Transposition models verified in source |
| Ilse 2019 soiling | memo 11 (closes ERR-3) | Global aggregate 3-4% / 4-7% (NOT arid-specific) |

---

## 3. Methodological lessons established (the substrate's main payoff)

### L1. Daily-energy + modeled-irradiance PI has a measurement-noise floor that buries fine signals

PVDAQ residential daily AC-energy data, normalized by PVWatts-NSRDB modeled expected energy, carries ~32% measurement variance (Probe 2b §4b). This is fine for **multi-year YoY-median trends** (PLR) but **insufficient for within-year sawtooth signals** (soiling). Evidence: Probes 2/2b succeed on PLR; Probe 3 fails on soiling; Probe 5 succeeds on soiling using DKA's measured-POA-on-site PI.

→ **Lab/fleet design rule:** measured on-site POA + ≤daily cadence is required for fine-grained PV signal extraction.

### L2. Heterogeneity inflates within-cell variance and kills climate-effect detectability

PVDAQ's heterogeneous fleet (uncontrolled cell-tech, mixed mounting, mixed vintage) has σ_within = 1.99 %/yr — 2.0× Jordan 2022's homogeneous-cohort σ ~0.99 %/yr (Probe 2b §4b). Jordan's 0.40 %/yr climate-T effect at PVDAQ's σ corresponds to Cohen f=0.071 → power 0.49 at n=668. **Required N scales ~quadratically with σ inflation.** DKA's homogeneous σ=0.23 (8× tighter than PVDAQ) recovers detectability at small N — Probe 4 validates this with the technology ordering visible at n=6 fixed-mount.

→ **Rule:** for climate-driven effects, σ_within ≤ ~1 %/yr (homogeneous cohort) or 6× more N. Confirmed twice: predicted (2b), validated (4).

### L3. Pre-registration discipline catches non-feasibility before it becomes garbage

The substrate has now **3 cases** where the diagnostic-first / anti-over-interpretation discipline correctly stopped a probe that the data couldn't support:
- Probe 2b technology-controlled climate test: n=17 → pivoted to detectability analysis (rigorous mechanism quantification instead of underpowered η² estimate)
- Probe 3 PVDAQ soiling: 13–19% garbage + frequent failures → FEASIBILITY-NULL logged, no pre-reg locked
- Probe 4 per-phase tracker artifact: discovered mid-execution → flagged and carried forward as caveat, not over-interpreted

→ **Substrate convention:** feasibility-check before pre-reg-lock; report FEASIBILITY-NULL as a result type; never ship noise as signal.

### L4. Inter-system synchrony is a powerful tool for fleet-of-replicates soiling analytics (substrate-novel)

Probe 5d demonstrates that pairwise Jaccard + K-threshold consensus-day analysis on SRR recovery dates **separates natural environmental cleaning from operational/manual cleaning** in a multi-system single-site fleet. SRR alone conflates them in the `soiling_interval_summary`. This is methodologically novel as far as the substrate is aware (verification queued §6).

→ **Tool:** apply to any multi-system single-site soiling work where common-cause vs per-system cleaning is unresolved.

---

## 4. Substrate-novel findings — VERIFICATION COMPLETE (2026-05-30)

External-literature verification round-1 closed. See memo `31_VERIFICATION_v1.0_substrate_novel_findings.md` for full per-finding detail (anchors, quotes, DOIs).

| Finding | Memo / CLM | **Verdict** | Substrate impact |
|---|---|---|---|
| **V1** Wet-season DEPOSITION > dry-season at Alice Springs (muddy soiling) | 29 §6c / CLM-093 | **VERIFIED** (mechanism = prior art) | Reframe to "first explicit Australian-arid replication of established dew-cementation"; anchors: Figgis 2018 (Qatar palygorskite), Ilse 2019 (cementation after dew), Ferrada Atacama (salt cementation), Energies 2023 (light rain → muddy layer) |
| **V2** Multi-system synchrony decomposes natural vs operational cleaning | 29 §6d / CLM-094, CLM-095 | **NOVEL-FRONTIER (HARDENED)** | Candidate primary publishable methodological artifact. Journal + conference sweep (PVSC 2022-25, EU-PVSEC, PVRW) found no prior art. Watch-item: IEEE 11132652 Meyers PVSC-53 2025 full-text check |
| **V3** 2.0× σ_within heterogeneity inflation + 8× DKA homogeneous tightening | 25 §4b, 28 §2 / CLM-078, CLM-083 | **PARTIAL** (direction anchored, ratio novel) | Direction supported by Deceglie 2019 (residential 1.3 vs non-residential 0.8 %/yr mean PLR, n=503); no peer-reviewed σ_within numerical anchor — ratio itself is substrate-novel quantification frontier |
| **V4** CdTe-low soiling at DKA M7 (3.15%) | 29 §3 / CLM-090 | **PARTIAL-VERIFIED** (directional) | CdTe<c-Si replicates in Morocco — Ammari 2022 (13% vs 15%), Tahri 2023 (23.2% vs 25.5%). **FS-proprietary-coating attribution dies** — lit attributes to surface chemistry / partial-shading response, not coating. Reframe as CdTe-class effect |

**Three publication tracks emerge from verification:**
1. **Methodology paper** (V2-led) — multi-system Jaccard + K-consensus as natural-vs-operational cleaning decomposition; PV-reliability venue
2. **σ_within quantification paper** (V3-led) — first published heterogeneous vs homogeneous PV σ_within ratio; Deceglie 2019 direction anchor
3. **DKA Alice Springs replication case study** (V1 + V4 + 5e time-stability) — wet>dry as headline

---

## 5. Lab-design implications (consolidated for the future PV lab)

The substrate exists to inform a future PV research lab. Quantitative constraints established:

1. **For climate-driven degradation:** use **homogeneous cohorts** (single cell-tech, single mounting class) — heterogeneous public fleet aggregation fails (Probe 2). Target σ_within ≤ ~1 %/yr (DKA demonstrates 0.23 achievable).
2. **For soiling work:** **on-site measured POA + ≤daily cadence** is required (Probe 3 fails on daily-energy; Probe 5 succeeds on measured POA). Arid sites recommended for soiling — Alice Springs 3.87 %/yr is in the Ilse global aggregate range and is time-stable (Probe 5e).
3. **For cleaning ROI at arid sites:** **post-WET-season cleaning** may capture bulk of annual losses (Probe 5c surprise inversion: wet-season deposition is faster despite rain) — inverts the naive dry-season prescription. Verify per §4 before committing.
4. **For multi-system soiling analytics:** inter-system synchrony decomposition (Probe 5d) separates natural cleaning from operational interventions — apply before deriving annual rates.
5. **For PLR estimation:** PVWatts-DC normalization + rdtools YoY YoY + bootstrap CI is sufficient for fleet-aggregate magnitudes (Probe 2 replicated Jordan; Probe 4 reproduced expected ranges). Per-phase data for 3-phase systems is unreliable per-system (Probes 4/5 artifact); use phase-combined files.
6. **Sample-size targeting:** for a ~0.4 %/yr climate effect, need either σ_within ≤ ~1 %/yr or n ≥ ~2000 per zone. Pre-compute power before any partition design.
7. **Data acquisition order:** start with anchor verification → cohort identification → ℙ₀ assignment (no outcome inspection) → run → report. Never invert.

---

## 6. Open questions / candidate next probes

| Probe candidate | What it would close | Feasibility |
|---|---|---|
| Mount-effect clean test (DKA fixed vs tracker with phase-combined) | Mount confound in Probe 4 | Needs missing phase files (downloadable) |
| Orientation-effect (DKA 16A/B/C/D 4-orientation BP poly) | Tilt/azimuth confound | Needs operator-pull of 16A/B/C/D |
| CdTe-low-soiling replication | n=1 → n=≥3 | Needs catalog #23 Calyxo (operator-pull); + external CdTe datasets |
| External homogeneous-cohort climate test | Direct technology-controlled climate replication | DuraMAT blocked (network + confidentiality); needs alternate source (NREL RTC, manufacturer partnership) |
| Encapsulation × climate (T13-30 Sen et al. mechanism) | TOPCon UVID Probe 1 still blocked on cohort ID | Needs PVDAQ S3 per-system JSON metadata pull (≤1 day work if metadata exists) |
| LCOE / cleaning-interval ROI sketch | Applied-economics layer for lab vision | All inputs in hand (PLR, soiling, time-stability) |

---

## 7. State summary

- **30 literature memos** (00–30); **10 numbered probe results** (Probes 1/2/2b/3/4/5/5b/5c/5d/5e)
- **96 CLMs in ledger** (CLM-001 to CLM-096), all with VERIFIED / VERIFIED-OWN / NEEDS-VERIFICATION / REFUTED status per meta-pre-reg discipline
- **Reusable infrastructure**: PVDAQ S3 puller, NSRDB v4 puller (cached), rdtools+pvlib PLR pipeline, DKA per-array loader (5-min POA-normalized PR), SRR soiling pipeline, multi-system synchrony tool, temporal-drift analyzer
- **Code:** Solar/code/probe2_*.py, probe2b_*.py, probe3_*.py, probe4_*.py, probe5_*.py, probe5b/c/d/e_*.py
- **Data:** Solar/data/raw/{pvdaq_daily,nsrdb,dka,papers}/ (gitignored, 5.4 GB DKA + caches); Solar/data/processed/probe{2,2b,3,4,5,5b,5c,5d,5e}_*.csv|json (whitelisted small artifacts)
- **Repo:** github.com/mrnathanhumphrey-droid/Renewables HEAD `fe8629d` (pre-compact lock target)

The substrate has reached a natural checkpoint — story is internally consistent, every probe has a clean disposition, no garbage in the claims ledger, methodology lessons are quantified. Verification of substrate-novel findings (§4) is the next-session priority per operator direction.

---

**END SYNTHESIS v1.0**
