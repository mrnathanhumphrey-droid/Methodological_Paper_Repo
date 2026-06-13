# 35 — Probe 8: DKA fuzz-robustness sweep (V2 K-crash and Jaccard)

**Status:** Skeptic-pass robustness test on V2's two load-bearing claims at DKA (memo 29). Tests whether the ±1 day fuzz parameter — which was NOT formally pre-registered — was load-bearing for either the K-consensus rain-alignment "crash" (CLM-095) or the inter-system Jaccard synchrony detection (CLM-094).
**Date:** 2026-05-30 (skeptic pass)
**Substrate:** D:/Renewables/Solar/

---

## 1. Why this probe

Operator entered cold-skeptic mode after V2/V3 push and noted (memo 31 §8.3) that the ±1 day fuzz used in Probes 5d/6 was copied from Probe 5b convention (which actually used ±2 days) without formal justification. If the K=13 crash signature depends on the specific fuzz choice, the "operational regime detection" claim is p-hacked.

Probe 8 sweeps fuzz ∈ {0, 1, 2, 3} days on cached DKA recovery dates and reports K-consensus rain-alignment + Jaccard synchrony for each.

---

## 2. K=13 crash — NOT robust to fuzz

| fuzz | K=13 n_days | n_rainy | pct | baseline | p_one_sided_low | verdict |
|---|---|---|---|---|---|---|
| **0** | 14 | 0 | 0.0% | 8.0% | 0.31 | below not sig |
| **1** | 42 | 2 | 4.8% | 15.3% | **0.034** | **BELOW + sig** ← what we reported |
| **2** | 62 | 10 | 16.1% | 21.1% | 0.21 | below not sig |
| **3** | 86 | 21 | 24.4% | 26.2% | 0.41 | below not sig |

K=12:

| fuzz | pct | baseline | verdict |
|---|---|---|---|
| 0 | 0.0% | 8.0% | below not sig |
| 1 | 9.8% | 15.3% | below not sig |
| **2** | 29.0% | 21.1% | **ABOVE baseline** |
| **3** | 40.3% | 26.2% | **ABOVE baseline** |

**The crash signature exists ONLY at fuzz=1.** At fuzz=0 the crash direction holds but the sample is too small (n=14) to be significant. At fuzz=2/3, K=12 events actually look *natural-cleaning-like* (rain alignment ABOVE baseline). At fuzz=2/3 K=13 events drift back to baseline.

### 2.1 Interpretation

The events at K=12-13 (≥12 of 13 systems agreeing on a recovery date) **tend to occur 2-3 days after rain, not within 1 day of rain**. At fuzz=1 we miss the rain attribution and the events look operational (no rain link). At fuzz=2/3 we catch the rain attribution and the events look natural (with a multi-day lag).

This is consistent with either:
- **(a) Operational cleanings ARE happening at DKA, scheduled a few days after rain events** (e.g., "after the weekend rain, send the crew Monday"). The K=13 crash at fuzz=1 then partially detects operational signal that's not coincident with rain but is causally downstream of it.
- **(b) The K=13 "crash" at fuzz=1 is a tuning artifact** — a window narrow enough to exclude valid natural cleanings happening with a multi-day delay between rain and SRR-detected recovery.

The substrate cannot distinguish (a) from (b) without an operational log from DKA.

### 2.2 Effect on CLM-095

The original claim was: "K=12-13 alignment CRASHES to 5-10% << baseline 15%, ~42 site-wide events over 12yr ~3.5/yr — substrate-novel methodology separates natural from operational cleaning."

The honest revised claim is: **at fuzz=1 specifically, K=13 events show statistically significant under-alignment with rain (p≈0.03). This signature does not persist at fuzz=0/2/3, suggesting the operational events (if any) occur with a multi-day lag from rain, not strictly within ±1 day.** The "separates natural from operational" framing requires either pre-registered fuzz justification or a more nuanced model of operational-event timing.

---

## 3. Jaccard synchrony — IS fuzz-robust

| fuzz | observed median Jaccard | random null | ratio |
|---|---|---|---|
| 0 | 0.161 | 0.023 | **6.87×** |
| 1 | 0.259 | 0.074 | 3.51× (probe5d reported 4.78× — span-denominator difference, see §3.1) |
| 2 | 0.320 | 0.129 | 2.48× |
| 3 | 0.365 | 0.191 | 1.91× |

**Synchrony detection is robust across all fuzz values** — observed Jaccard always above random null. Ratio monotonically decreases as fuzz widens (more permissive matching → both observed and null Jaccard rise, but null rises faster proportionally).

The fuzz=1 choice was CONSERVATIVE for the synchrony claim — at fuzz=0 the ratio is actually stronger (6.87×). This was not p-hacked in the synchrony direction.

### 3.1 Note on the probe5d 4.78× vs probe8 3.51× discrepancy

Probe 5d used `rain.index.min/max` for the span denominator (6189 days), giving null Jaccard 0.054 and ratio 4.78×. Probe 8 used `max(dates) - min(dates)` across recovery sets (4635 days), giving null 0.074 and ratio 3.51×. Both are valid; the rain-span denominator is preferable because it matches the K-consensus analysis denominator. Either way the synchrony detection survives.

---

## 4. Net effect on V2 status

| V2 claim | Status |
|---|---|
| **Fleet-level synchrony detection** (Jaccard >> random) | **ROBUST** to fuzz; survives skeptic pass |
| **Natural cleaning regime** (alignment elevated above baseline at moderate K) | **ROBUST** at fuzz=1,2,3 (K=8 lift 1.65× / 1.61× / 1.58× respectively) |
| **Operational cleaning decomposition** (K=12-13 crash below baseline) | **FUZZ-FRAGILE** — only fires at fuzz=1; could be a tuning artifact OR could be a real lagged-operational signature requiring different model |

### 4.1 What V2 still publishes

Memo 31 §6.3 Track 1 (methodology paper) needs to be reframed:

- **Was:** "V2 = multi-system synchrony decomposition that separates natural from operational cleaning"
- **Is:** "V2 = fleet-level synchrony detection of cleaning events via inter-system Jaccard + K-consensus, with an observed asymmetry at high K that suggests but does not establish an operational-cleaning sub-mode"

This is a much weaker contribution than the original framing — but it's still novel (no journal/conference paper does fleet-level Jaccard / K-consensus on PV cleaning events; Heinrich 2020 and Muller 2022 operate per-system). And it's substrate-defensible.

### 4.2 What V2 doesn't publish (yet)

The "natural vs operational decomposition" claim. To establish that:
1. **Pre-register the fuzz choice** with physical justification (daily aggregation aliasing → fuzz=1; weekend-scheduling lag → fuzz=2/3; specify which)
2. **OR** find a fleet with operational logs to ground-truth which K-events were manual cleanings
3. **OR** model operational events with a lag distribution rather than a hard ±fuzz window

---

## 5. Recommendations to substrate

1. **CLM-095 downgraded** in ledger from PARTIAL → record fuzz-fragility (CLM-104 added)
2. **Memo 31 §8 corrections** extended with fuzz finding
3. **Probe 6/6b at MA** also fuzz-fragile by extension — was already weakened in §8.6. Probe 6 Jaccard 2.01× at MA was fuzz=1; at fuzz=0 would presumably be higher, at fuzz=2/3 lower (deferred sweep)
4. **Methodology paper Track 1 should report Probe 8 results as primary methodology robustness section** — the substrate caught its own fuzz-fragility, which is exactly the kind of falsification discipline reviewers reward

---

## 6. Artifacts

- `code/probe8_v2_fuzz_robustness.py` — fuzz sweep pipeline
- `data/processed/probe8_dka_recovery_dates_cache.csv` — per-system recovery dates (SRR-stochastic; cached for reproducibility within this probe)
- `data/processed/probe8_fuzz_robustness.csv` — full K × fuzz table

---

**END Probe 8** — V2 synchrony detection robust; V2 operational decomposition fuzz-fragile. Substrate's earlier "novel methodology that separates natural from operational" framing was too strong. What survives: novel fleet-level synchrony detection (no prior art at fleet level); observed high-K asymmetry suggesting but not proving operational sub-regime.
