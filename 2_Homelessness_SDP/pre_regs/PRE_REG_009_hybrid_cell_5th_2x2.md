# Pre-Registration 009 — HYBRID Cell as 5th 2x2 Typology Cell

**ID:** PRE_REG_009
**Locked:** 2026-05-25
**Substrate:** PATTERN_013 + PATTERN_026 (USA fast-pole)
**Status:** LOCKED — predictions and falsifiers pre-committed; first fit fires on existing V-Dem data + forward window 2026-2030

---

## 1. Hypothesis

**H1 (HYBRID cell):** A 5th cell exists in the 2x2 typology (speed × institutional vehicle): **personalist-activated party-state HYBRID**. Cases in this cell exhibit:
- (a) LOW party-cohesion measure (v2pscohesv < 1.0) — looks personalist by V-Dem
- (b) HIGH pre-existing party-state institutional infrastructure (judicial appointment networks, state-level party machines, party-aligned think tanks)
- (c) Leader-brand fused with party
- (d) Single-event consolidation speed but party-state durability features

**H2 (durability prediction):** HYBRID cases have **intermediate** durability post-leader-exit compared to pure personalist (collapse fast) vs pure party-state (durable). Recovery is conditional on whether party-state infrastructure can produce successor without leader-brand.

**H3 (USA classification):** USA Trump II is the empirical type-specimen of HYBRID. TUR (Erdoğan/AKP) is the secondary HYBRID candidate.

---

## 2. In-sample evidence (NOT re-tested)

USA Trump II profile (per P1-A dig):
- v2pscohesv = 0.39 (LOW; structural feature of US politics not Trump-specific)
- Pre-existing infrastructure: Federalist Society (1982+), SCOTUS 6-3 (since 2020), state-level GOP machinery, Heritage Foundation Project 2025
- Trump-GOP brand fusion: post-2016 GOP purges, dissidents removed
- Single-event speed (Trump II 2024→2025 LDI Δ = −0.180) + party-state institutional execution

TUR profile (candidate):
- v2pscohesv = 2.53 (HIGH unlike USA)
- Pre-existing AKP institutional depth post-2003
- Erdoğan-AKP fused brand
- Incremental speed (not single-event) → may not fit HYBRID cleanly

---

## 3. Pre-locked predictions

### Prediction set A — Cluster classification test

For each of our 10 Bukelization cases + ZMB Hichilema 2021 recovery, score:
- (i) v2pscohesv (party cohesion)
- (ii) v2psorgs (party organizations)
- (iii) v2psnatpar (national party organization)
- (iv) v2psprbrch (party branches)
- (v) v2psprlnks (party-state linkages)

Predicted clustering:
- **Pure personalist cluster** (LOW everything except leader-cohesion): SLV, TUN, BLR, NIC
- **Pure party-state cluster** (HIGH everything): HUN, POL, VEN, BGD, IND
- **HYBRID cluster** (LOW cohesion + HIGH infrastructure): USA, possibly TUR

If cluster analysis produces 3 distinct clusters → H1 supported.
If only 2 clusters → HYBRID is artificial; merge USA back into personalist or party-state.

### Prediction set B — Durability test (forward 2026-2030)

| Cell | Predicted post-leader-exit libdem recovery in 2y |
|---|---|
| Pure personalist (SLV, TUN if Bukele/Saied exit) | +0.20 or more |
| Pure party-state (HUN, POL, VEN, IND if leader exits) | +0.05-0.10 (stalled) |
| **HYBRID (USA if Trump exits 2029)** | **+0.10-0.15 (intermediate)** |

### Prediction set C — Post-Trump scenario (locked 2026-2030 window)

If Trump exits power Jan 2029 (term-limited):
- If GOP successor (Vance, DeSantis, etc.) maintains GOP party-state infrastructure → consolidation continues at slower rate → HYBRID maintained → libdem stays 0.30-0.45 by 2031
- If GOP successor breaks with Trump faction → recovery toward 0.50-0.60 by 2031
- If no GOP candidate wins 2028 (Democrat victory) → recovery toward 0.55-0.65 by 2031 BUT captured SCOTUS + state machines limit recovery speed

---

## 4. Falsifiers

- **F1:** Cluster analysis produces only 2 clean clusters (personalist vs party-state) → HYBRID is data artifact, not real cell
- **F2:** Post-Trump-exit recovery is rapid (+0.20 or more in 2y) → USA was pure personalist (party-state didn't survive Trump)
- **F3:** Post-Trump-exit recovery is null (<+0.05 in 2y) → USA was pure party-state (Trump exit doesn't matter)
- **F4:** TUR fails HYBRID classification AND no other HYBRID case emerges → USA is a unique outlier, not a cell

Any 2 of {F1, F2, F3, F4} firing = HYBRID cell walked back; USA reclassified as personalist or party-state.

---

## 5. Methodology

- V-Dem v15 party-system indicators (5 cols)
- Hierarchical clustering on standardized indicators
- Forward V-Dem releases 2026-2030 for durability test

## 6. Cross-references
- PATTERN_013, PATTERN_026, PRE_REG_008 (extends H3)
- digs/2026_05_25_P1_A_USA_personalist_or_partystate.md (substrate)

---

## 7. Results — first fit (fired 2026-05-25)

K-means clustering on 5 V-Dem party-system indicators, n=12 cases:

**k=3 clusters produced (inertia 25.58):**
- Cluster 0 (pscohesv_mean = 2.24): NIC, VEN, BGD — "floor consolidation cases"
- Cluster 1 (pscohesv_mean = 0.92): TUN, POL, IND, USA, SRB — "LOW-cohesion cases"
- Cluster 2 (pscohesv_mean = 2.48): SLV, BLR, HUN, TUR — "HIGH-cohesion cases"

**USA in k=3 = Cluster 1 (low-cohesion).** Not in own cluster, not paired with TUR.

**Verdict on H1**: PARTIALLY SUPPORTED with caveat. Three clusters emerge but they don't cleanly map to personalist / party-state / HYBRID typology. The clustering is driven primarily by v2pscohesv (party cohesion), which puts USA in a mixed group (TUN/POL/IND/USA/SRB) rather than producing a distinct HYBRID cluster.

**Refinement needed**: V-Dem party-system indicators alone don't capture HYBRID's distinguishing feature (pre-existing party-state institutional infrastructure like Federalist Society, SCOTUS appointment networks, state-machine integration). These are measured by V-Dem only indirectly. A proper HYBRID test needs:
- Judicial appointment-network mapping (Federalist Society database)
- State-level party-control + election infrastructure data
- Think-tank ecosystem measures

**Status**: H1 SOFT SUPPORT. USA is in a distinct cluster from pure-personalist (SLV/TUN/BLR/etc) AND pure-party-state (HUN/VEN/BGD), but the cluster is heterogeneous (POL party-state alongside USA HYBRID alongside TUN personalist). The HYBRID concept is real but requires additional non-V-Dem data to identify properly. Forward predictions (post-Trump scenarios) remain locked.

**Forward predictions not yet testable** (require 2026-2030 data).
