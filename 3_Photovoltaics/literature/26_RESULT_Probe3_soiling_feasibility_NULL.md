# Result — Probe 3: Soiling × Climate FEASIBILITY-NULL

**Status:** COMPLETE. Disposition = **FEASIBILITY-NULL** — PVDAQ residential daily-energy data cannot support credible rdtools SRR soiling extraction. No full pre-reg locked; no fleet run. The diagnostic feasibility check stopped the probe before over-interpretation.
**Date:** 2026-05-28
**Type:** Pre-pre-reg feasibility diagnostic (per substrate discipline: confirm data can support the signal before locking a hypothesis test). Anchor: Ilse et al. 2019 (memo 11) — soiling aridity dependence.
**Code:** `code/probe3_soiling_feasibility.py`.

---

## 0. One-line result

rdtools Stochastic-Rate-and-Recovery (SRR) soiling extraction on PVDAQ daily-energy + NSRDB-modeled performance index returns **implausible soiling losses (13–19%)** with wide CIs and frequent hard failures, because the few-percent soiling sawtooth sits **below the ~32% measurement-noise floor** of the daily-energy normalization (quantified in Probe 2b memo 25 §4b). Combined with **zero analyzable systems in the truly-arid H1 zone** (Ilse's strongest prediction case), a credible soiling-aridity test is not achievable on PVDAQ. Probe 3 is shelved at feasibility, not run.

---

## 1. Feasibility check (6 systems, SRR with 200 bootstrap reps)

| Zone | System | SRR soiling loss | SR CI | Verdict |
|---|---|---|---|---|
| H2 semi-arid | 10068 | **18.98%** | [0.741, 0.871] | implausibly high |
| H2 semi-arid | 10112 | 4.30% | [0.935, 0.970] | plausible but isolated |
| H2 semi-arid | 10196 | **13.16%** | [0.814, 0.910] | implausibly high |
| H3 moderate | 10000 | — | — | **NoValidIntervalError (fail)** |
| H3 moderate | 10001 | — | — | **NoValidIntervalError (fail)** |
| H3 moderate | 10003 | 16.97% | [0.656, 0.952] | implausible + huge CI |

**Reference (Ilse 2019, memo 11 / CLM-ILSE-GLOBAL):** global aggregate soiling loss 3–4% current, 4–7% projected; site-specific arid up to ~1%/day transient but annual losses rarely exceed ~10%. The 13–19% SRR estimates here are 2–5× the plausible range — a clear signature of noise misattribution, not real soiling.

---

## 2. Why it fails (mechanism)

1. **Soiling signal < noise floor.** SRR detects soiling as a sawtooth: gradual PI decline (dust accumulation) punctuated by sharp recovery (rain/cleaning). The true signal depth is a few percent. The PVDAQ daily PI (measured daily AC energy ÷ PVWatts-NSRDB modeled energy) carries ~32% measurement-noise variance (Probe 2b §4b: measurement RMS 1.36 %/yr on the *trend*; the *daily* scatter is far larger). Daily PI scatter from cloud-model residual + meter noise + no on-site irradiance creates spurious decline-recovery patterns that SRR misattributes to soiling → inflated 13–19% estimates.
2. **NoValidIntervalError** on 2/3 moderate systems: SRR's internal quality gates reject the data outright when no clean soiling intervals can be isolated from the noise.
3. **No measured POA.** SRR is designed for systems with on-site irradiance (clean PI). The residential PVDAQ tier has daily AC energy only (memo 22 §3); modeled irradiance cannot resolve the day-to-day cleanliness needed for the sawtooth.

**Consistency with prior probes:** PLR (Probe 2) survived the same noise because the YoY *median over years* is robust to daily scatter. Soiling is a subtle *within-year* signal with no such robustness — so the same data supports PLR but not soiling. This is the expected signal-scale ordering.

---

## 3. Compounding limitation: no arid coverage

The Ilse 2019 prediction is specifically about **aridity** driving soiling. PVDAQ analyzable coverage:
- **H1 (truly arid, 0.7–3.0 g/kg): 0 systems** in the 668 PLR cohort.
- H2 (semi-arid): present but few, and SRR unreliable (above).
- The bulk (H3, 82%) is moderate-humidity where soiling is expected low and rain-cleaned.

Even if SRR worked, PVDAQ lacks the arid systems to test the aridity gradient. (Same coverage gap noted in memo 22 §2: no H5 tropical, sparse H1/H2.)

---

## 4. Disposition + what would be needed

**Probe 3 shelved at feasibility.** A credible soiling probe requires:
1. **Measured on-site POA** (clean daily PI) — the 64 PVDAQ rich-sensor systems have it, but (a) they need the expensive per-day long-format parquet extraction, and (b) they are concentrated in few climate zones with little arid coverage.
2. **Arid-site coverage** — external data (NREL Soiling stations, DEWA/Qatar/Atacama soiling testbeds, the Ilse 2019 underlying datasets) for the aridity gradient.
3. Higher temporal resolution than daily AC energy.

None of these are blocked-with-effort, but none are available in the PVDAQ residential tier already in hand.

---

## 5. CLM ledger additions

| ID | Claim | Status |
|---|---|---|
| CLM-079 | rdtools SRR soiling extraction on PVDAQ daily-energy+NSRDB PI returns implausible 13–19% losses (vs Ilse 3–7%) with wide CIs + frequent NoValidIntervalError; soiling signal below the daily-PI noise floor | VERIFIED-OWN |
| CLM-080 | Soiling (subtle within-year sawtooth) is NOT extractable from PVDAQ residential daily-energy data, though PLR (multi-year YoY-median trend) is — expected signal-scale ordering vs the 32% measurement-noise floor | VERIFIED-OWN |
| CLM-081 | PVDAQ has 0 analyzable H1 (truly-arid) systems → Ilse aridity-soiling prediction untestable on PVDAQ regardless of SRR feasibility | VERIFIED-OWN |

---

## 6. Substrate-discipline note

This is the **second time this session** the diagnostic-first / anti-over-interpretation discipline stopped a probe that the data could not support (first: the n=17 technology-controlled test, Probe 2b §1). In both cases the honest disposition (FEASIBILITY-NULL / pivot-to-detectability) is recorded rather than shipping a noisy point estimate as a finding. The meta-pre-reg evidence discipline is working as designed: **negative feasibility knowledge is logged so future sessions don't re-attempt, and no garbage enters the claims ledger as signal.**

---

**END RESULT — Probe 3 feasibility-null**
