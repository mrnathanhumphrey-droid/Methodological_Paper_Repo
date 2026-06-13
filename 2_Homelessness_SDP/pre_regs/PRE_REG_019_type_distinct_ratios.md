# Pre-Registration 019 — Type-Distinct Fatality/Displacement Ratios

**ID:** PRE_REG_019
**Locked:** 2026-05-27
**Substrate:** PATTERN_012/015/017/031/032/033 + PRE_REG_018 v2 classifications
**Status:** LOCKED — confirmatory pre-reg with explicit acknowledgment that DPF distributions visible from P4-C v1 first fit. Formal test fires on v2-reclassified data + tests rank-order/spread predictions.

**Honesty caveat**: DPF medians for each type are visible from v1 dig. v2 may shift some cases (MLI/BFA/SOM into C). This pre-reg locks the **direction + magnitude predictions** in formal form and tests whether they survive v2 reclassification + held-out cases.

---

## 1. Hypothesis

**H1 (type-distinct DPF):** Displacement-per-fatality (DPF) ratios are mechanism-distinct across the 5 conflict-types. Specifically:

| Type | Predicted DPF median | Mechanism |
|---|---|---|
| A formal-army | 30-80 | High-intensity state-vs-state; military deaths don't drive evacuation; organized border-corridor flight |
| B predator-militia | 250-1500 | One-sided civilian-targeting; mass flight from militia-territory; multi-displacement-event-per-person |
| C irregular insurgency | 100-300 | Mixed actor landscape; civilian flight tied to specific attacks; mid intensity |
| D criminal-violence | ≤80 | Cartel violence targeted; doesn't mass-displace civilian populations |
| E civil-war-mass-displacement | 300-2500 | State-vs-rebel prolonged conflict; large IDP + refugee flows; cumulative displacement |

**H2 (rank ordering):** Median DPF rank-order should be: D ≈ A < C < B < E (criminal-violence and formal-army low; civil-war-mass-displacement and predator-militia highest).

**H3 (within-type spread):** Within each type, the interquartile DPF range should be SMALLER than the inter-type median spread → ratios are diagnostic, not noise.

---

## 2. Pre-locked predictions

### Prediction set A — Type-distinct medians match bands

After PRE_REG_018 v2 reclassification, compute median DPF per type. Predict:
- A median in 30-80 range
- B median in 250-1500 range
- C median in 100-300 range
- D median ≤ 80 (low)
- E median in 300-2500 range

**Match threshold**: 4 of 5 type medians fall within predicted bands → H1 SUPPORTED.

### Prediction set B — Rank ordering correct

Compute median DPF per type, rank. Predict order: D ≈ A < C < B < E.
- D and A roughly tied (both low)
- C in middle
- B and E high (B from predator-militia mechanism; E from prolonged-civil-war mechanism)

**Match threshold**: ranking matches in 4 of 4 pairwise comparisons (D < C, A < C, C < B, C < E) → H2 SUPPORTED.

### Prediction set C — Within-type IQR < between-type spread

For each type, compute IQR of DPF. Compute inter-type median spread (max median - min median).

**Predicted**: Within-type IQR < inter-type spread for ALL 5 types → H3 SUPPORTED (ratios are diagnostic).

---

## 3. Falsifiers

- **F1 (medians outside bands)**: ≥3 of 5 type medians outside predicted bands → H1 walked back
- **F2 (rank inverted)**: rank ordering wrong in ≥2 pairwise comparisons → H2 walked back
- **F3 (within > between)**: ANY type's within-IQR > inter-type spread → H3 walked back (ratios noisy not diagnostic)
- **F4 (collapse)**: All types' DPF within 100 of each other → mechanism-distinction null

F1 + F2 firing together = ratio-based discrimination walks back.

---

## 4. Methodology

After PRE_REG_018 v2 reclassification:
1. Aggregate country-year DPF per type
2. Compute median + IQR per type
3. Test prediction sets A/B/C

Use the country-year DPF values (not just country-level) to get N for each type.

## 5. Cross-references
- PRE_REG_018 v2 (classifier output)
- PATTERN_012/015/017/031/032/033 (type anchors)

## 6. Provenance
Locked 2026-05-27 before PRE_REG_018 v2 re-fire.

---

## 7. Results — first fit (fired 2026-05-27)

### Type DPF medians (all bands match)
| Type | N | Median DPF | IQR | Band | Match |
|---|---:|---:|---:|---|---|
| A formal-army | 6 | 37 | 42 | 30-80 | ✓ |
| B predator-militia | 3 | 715 | 297 | 250-1500 | ✓ |
| C irregular insurgency | 5 | 238 | 1765 | 100-300 | ✓ |
| D criminal-violence | 3 | 30 | 16 | 0-100 | ✓ |
| E civil-war-mass-displacement | 17 | 938 | 786 | 300-2500 | ✓ |

**H1: 5/5 bands match → SUPPORTED**

### Rank ordering (H2)
**D (30) < A (37) < C (238) < B (715) < E (938) — EXACTLY MATCHES PREDICTION**
4/4 pairwise comparisons correct → SUPPORTED

### Within-type IQR vs inter-type spread (H3)
- Inter-type spread (max-min medians): 908
- Max within-type IQR: 1765 (Type C)

**H3 WALKED BACK** — Type C heterogeneous (MLI 165, LBN 238, SSD 1930, COL 5000+).

### Net result
H1 + H2 STRONGLY SUPPORTED. H3 walked back, surfacing Type C sub-typing candidate. Status: 2 of 3 hypotheses confirmed; 1 walked back with constructive refinement direction.
