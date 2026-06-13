# Pre-Registration v1.7 — Opportunity-Moment Flow Taxonomy (pull flows)

**Type:** New discovery arm, post-RMD-SRC. Additive; prior arms stand.
**Authored:** 2026-05-28
**Status:** LOCKED v1.7, held-out test PASSED 2026-05-28. Signature-vector corr train(2012-17) vs holdout(2018-21) = **0.999** (≥0.80 gate); both sanity contrasts (density dreamer>stability; kids stability>dreamer) preserved out-of-sample; flow shares stable. The opportunity-moment pull taxonomy is a CONFIRMED, transferable finding — it transfers because it is STATIC (which moment is chosen), unlike the dynamic corridor regimes (GEO_F4 failed). Secular note: BA+ rose ~4pp in all flows (education trend, level shift, structure preserved).

## Motivation

The demographic ℙ₀ failed (F2); the geographic re-slice worked statically but its dynamic regimes didn't transfer (GEO_F4). Diagnosis: migration sorts on the **moments of the opportunity field**, not on demographics. Discovery confirmed (in-sample): splitting moves by mean-gradient (Δμ) and upside-gradient (Δσ) yields demographically distinct **pull flows**. The push/desperation flow is NOT estimable in ACS (post-move blindness) — it exits to the homelessness substrate; excluded here.

## Taxonomy (locked definitions)

Per move, with opportunity MEAN index (μ) and UPSIDE index (σ):
- `tmean` = opp_deficit<0 (toward higher μ); `tup` = upside_deficit<0 (toward higher σ)
- **DREAMER** = tup & ¬tmean (chase ceiling, accept lower mean)
- **STABILITY** = tmean & ¬tup (chase thick middle, accept lower ceiling)
- **BOTH** = tmean & tup
- **CLEARING** = ¬tmean & ¬tup (down both; the agency half of old Q4)
- (DESPERATION = push axis, cross-substrate, not in this arm)

## Discovered signatures (in-sample, full window) — the predictions to replicate

| flow | young | kids | BA+ | dest density |
|---|---|---|---|---|
| DREAMER | 42.7% | 27.0% | 37.7% | 991 |
| STABILITY | 40.2% | 31.6% | 37.4% | 356 |
| BOTH | 44.0% | 27.6% | 40.7% | 984 |
| CLEARING | 39.0% | 28.7% | 36.8% | 381 |

Key qualitative contrasts: **dreamer dest-density ≫ stability** (≈3×); **stability kids > dreamer kids**.

## Held-out falsification (GATE)

Compute each flow's signature SEPARATELY on TRAIN (2012–2017) and HOLDOUT (2018–2021).
- **Primary:** Pearson correlation of the 16-value signature vector (4 flows × 4 features), train vs holdout. **Pass if r ≥ 0.80.**
- **Sanity:** the two key contrasts (density dreamer>stability; kids stability>dreamer) preserve sign in the holdout.
- Flow shares stable across windows (report; no hard threshold).

Pass → the moment-sorting taxonomy is a confirmed, transferable finding (clears the discovery→confirmation gate). Fail → in-sample artifact; report as such.

## Next arc (not this pre-reg)

Stitch the seam: a conservation model where rent-displacement outflow = successful-migration (ACS, clearing) + homelessness-inflow (SDP), split by landing probability. Requires the homelessness/SDP dataset (cross-project).
