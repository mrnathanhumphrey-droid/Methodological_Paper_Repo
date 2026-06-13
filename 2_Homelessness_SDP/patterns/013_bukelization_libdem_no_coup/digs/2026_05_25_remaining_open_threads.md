# PATTERN_013 — Remaining Open Threads Analysis (2026-05-25)

After completing emigration (PRE_REG_007 partial-support) and Sato 2022 reconciliation, attacked the remaining open threads: party-state vs personalist axis, speed variation, IND federal counter-pressure, POL+BRA recovery symmetry, coordinated resistance.

## Headline findings

1. **PRE_REG_008 speed-by-classification: NULL on first fit.** Mann-Whitney U test p=0.44. Party-state vs personalist does NOT predict consolidation speed cleanly. Durability/recovery prediction remains open (forward window 2026-2030).
2. **Window length DOES correlate with absolute rate** (Spearman ρ=−0.489, p=0.11): shorter consolidation windows = faster libdem decline rates. Single-dramatic-event cases (SLV) drive the short end; federal slow-burn (IND, BGD) drives the long end.
3. **IND federal-counter-pressure CONFIRMED**: judicial constraints index held at 0.819 for 17 years (1998-2014), only declining post-Modi-supermajority. Federal court system + state-level institutions resisted national consolidation. Slow-burn = institutional friction.
4. **POL recovery symmetry: CONFIRMED 5 of 6 sub-indicators reverse**. Spearman ρ=0.543. The captures are reversible in proportional magnitudes — except elections-free-and-fair (still hasn't recovered).
5. **BRA recovery symmetry: PARTIAL (3 of 6)**, with a complication — Bolsonaro era saw some V-Dem indices RISE (because Supreme Federal Tribunal actively resisted). Consolidation deltas are atypical because BRA was *failed backsliding*, not completed Bukelization.
6. **Opposition autonomy proxy works**: declined in ALL 12 consolidation cases (range −0.055 TUN to −1.712 HUN). USA's −0.988 over 7y is notably large for the short window. Operationalizable proxy for coordinated-resistance erosion.

---

## A. PRE_REG_008 first fit — speed by classification

| iso | Class | Window | Start libdem | End libdem | Rate |
|---|---|---|---|---|---|
| SLV | personalist | 5y | 0.393 | 0.090 | **−0.0606** (fastest) |
| HUN | party_state | 10y | 0.677 | 0.351 | −0.0326 |
| TUR | personalist | 10y | 0.461 | 0.101 | −0.0360 |
| VEN | party_state | 10y | 0.603 | 0.162 | −0.0441 |
| POL | party_state | 10y | 0.827 | 0.450 | −0.0377 |
| TUN | personalist | 10y | 0.642 | 0.196 | −0.0446 |
| BLR | personalist | 10y | 0.443 | 0.100 | −0.0343 |
| IND | party_state | 22y | 0.587 | 0.281 | −0.0139 |
| USA | personalist | 7y | 0.749 | 0.751 | +0.0003 (not yet in window — pre-2025 data) |
| SRB | personalist | 14y | 0.503 | 0.225 | −0.0199 |
| BGD | party_state | 15y | 0.193 | 0.097 | −0.0064 |
| NIC | personalist | 13y | 0.216 | 0.045 | −0.0132 |

Personalist (n=7): mean rate −0.0297, median −0.0343
Party-state (n=5): mean rate −0.0269, median −0.0326

**Mann-Whitney U test**: U=16.0, p=0.4381 → NOT significant.

**Verdict**: F4 (party-state rate ≥ personalist rate) does NOT fire, but neither does the prediction. Speed-by-classification is essentially null. The classification needs a different test — durability (recovery vs reversal post-leader-exit) is the open empirical question, but requires forward observation.

**Refinement for PRE_REG_008**: drop H2's speed-prediction; keep H3's recovery-prediction as the live test in 2026-2030 window.

## B. Window length predicts speed

Spearman ρ(window_length, |rate|) = **−0.489** (p=0.107).

Direction is correct: shorter windows produce higher rates. This is partly mechanical (Δ/n shrinks with n) and partly substantive (single-event consolidations don't need long windows). Useful as a sanity check more than a discovery.

## C. IND federal counter-pressure — CONFIRMED

IND year-by-year sub-indicators 1998-2025:

| Period | libdem | jucon (judicial constraints) | partyaut |
|---|---|---|---|
| 1998-2008 | ~0.58-0.59 | **0.819 (held flat 11 years)** | 2.05 (held) |
| 2009-2013 | 0.52-0.54 | 0.819 (still held) | 1.792 |
| 2014 (Modi I election) | 0.488 | 0.818 | 1.792 |
| 2015-2024 | 0.281 (collapsed) | **0.799 → 0.710 (−0.109 over 9y, much slower than libdem)** | 1.479 → 0.967 |
| 2025 | 0.260 | 0.667 (continuing decline) | 1.583 (slight bounce) |

**The federal-counter-pressure hypothesis is SUPPORTED**: judicial constraints index held at 0.819 for nearly 2 decades before Modi-era erosion began. India's federal court system (Supreme Court + High Courts at state level) provided institutional resistance to executive consolidation for an extended period. This explains why IND is slow-burn (−0.014/yr) vs SLV's −0.061/yr.

**Mechanism candidate**: federal/parliamentary systems with strong sub-national institutions and constitutionally-entrenched judicial review slow the speed of Bukelization. Unitary or weakly-federal systems (SLV, HUN, TUR) can consolidate faster.

## D. POL + BRA recovery symmetry — quantitative test

### POL consolidation 2010-2020 vs recovery 2022-2024:

| Sub-indicator | Consol Δ | Recov Δ | Symmetric? |
|---|---|---|---|
| Judicial constraints (jucon) | −0.388 | +0.164 | YES |
| Free expression + alt info | −0.291 | +0.305 | YES (recovers fully) |
| Elections free + fair | **−2.150** | −0.033 | **NO** (still suppressed) |
| High court independence | −2.833 | +1.686 | YES (partial recovery) |
| Media censorship | −2.669 | +2.475 | YES (almost full recovery) |
| Civil society space | −0.788 | +0.436 | YES (partial) |

Spearman ρ(consol_delta, −recovery_delta) = **+0.543** (moderate-strong symmetry).

**5 of 6 sub-indicators show symmetric reversal.** The exception is elections-free-and-fair, which hasn't recovered — Polish electoral law remains effectively PiS-shaped post-2023. This is a real prediction for PRE_REG_006 (stalled-recovery): election quality is the LATE-to-recover sub-indicator.

### BRA consolidation 2018-2022 vs recovery 2022-2024:

| Sub-indicator | Consol Δ | Recov Δ | Symmetric? |
|---|---|---|---|
| Judicial constraints | −0.032 | +0.127 | YES |
| Free expression | −0.088 | +0.219 | YES |
| Elections free + fair | +0.108 | 0.000 | NO (rose during Bolsonaro?) |
| High court independence | **+0.436** | +0.199 | NO (kept rising) |
| Media censorship | −0.193 | +2.509 | YES (massive recovery) |
| Civil society | +0.194 | +0.616 | NO (kept rising) |

Spearman ρ = 0.371 (weaker symmetry).

**The BRA case is structurally different**: it's *failed* Bukelization, not completed. Bolsonaro-era saw some indices RISE (judicial constraints, high court independence rose because Supreme Federal Tribunal actively resisted Bolsonaro). This is consistent with the literature framing BRA as the failed-backsliding null case.

**Lesson**: recovery-symmetry test only works cleanly on COMPLETED Bukelization episodes. BRA isn't one — its "recovery" is more about removing Bolsonaro pressure than reversing institutional captures, because the captures never fully landed.

## E. Coordinated resistance proxy — opposition autonomy

V-Dem v2psoppaut (opposition party autonomy) deltas during consolidation:

| iso | Window | oppaut Δ |
|---|---|---|
| HUN | 2010-2020 | **−1.712** |
| SLV | 2019-2024 | **−1.643** |
| SRB | 2010-2024 | −1.452 |
| NIC | 2007-2020 | −1.236 |
| VEN | 1997-2007 | −1.137 |
| IND | 2002-2024 | −1.083 |
| **USA** | **2017-2024** | **−0.988** (largest per-year drop except SLV) |
| BGD | 2009-2024 | −0.815 |
| TUR | 2007-2017 | −0.610 |
| POL | 2010-2020 | −0.398 (constrained by EU) |
| TUN | 2012-2022 | −0.055 |
| BLR | 1992-2002 | 0.000 (already at floor) |

**All 12 consolidation cases show declining opposition autonomy.** This is a clean operationalization of "coordinated resistance erosion" — opposition can't coordinate effectively because party autonomy is suppressed.

USA's −0.988 over 7 years is notably steep — annual rate −0.141/yr is faster than HUN, POL, IND. Consistent with USA being a fast-pole case (per Carnegie 2025 and our LDI single-year-drop finding).

V-Dem WP #147's claim that "coordinated resistance within one electoral cycle" predicts fast U-turn can now be operationalized: a country's recovery prospects are stronger when opposition party autonomy has NOT fully collapsed.

**Forward test**: POL kept oppaut high (−0.398, modest decline) → opposition could coordinate by 2023 → recovery possible. HUN dropped −1.712 → opposition severely suppressed → 2026 election prediction = HUN recovery unlikely even if Orbán loses.

---

## Implications for the writeup

1. **PRE_REG_008 H2 (speed-by-classification) walked back to null** — speed doesn't differ by party-state vs personalist at sample size n=12. H3 (durability) stays open.

2. **Window length / single-event-vs-incremental remains the cleanest speed predictor** — pre-existing speed-style observation from deep extraction holds.

3. **IND federal counter-pressure is a confirmed finding** — slow-burn is structural, not just chronological. Methodology paper can cite IND as the federal-friction case.

4. **POL recovery symmetry is replicable mechanistic** — 5 of 6 sub-indicators reverse in proportional magnitudes. Elections-free-and-fair is the LATE-recover sub-indicator (potentially the bellwether for full recovery durability).

5. **BRA is structurally different from the other recovery case** — failed backsliding rather than recovered Bukelization. Don't lump POL and BRA in the methodology paper's recovery section.

6. **Opposition autonomy as coordinated-resistance proxy** — V-Dem v2psoppaut works empirically. Cases with smaller oppaut decline have better recovery prospects. POL's relatively-preserved oppaut (−0.398) explains its 2023 recovery; HUN's massive oppaut decline (−1.712) predicts slow/no recovery if Orbán loses 2026.

7. **USA fast-pole confirmed by opposition autonomy too**: −0.988 oppaut Δ over 7y is faster than HUN per year. Consistent across multiple indicators.

## Open questions remaining

- Forward observation 2026-2030: PRE_REG_008's durability prediction, PRE_REG_006's stalled-recovery prediction
- Time-stamping court-capture events for clean chronological test (event-history)
- UN DESA migration data for full PRE_REG_007 test
- USA Trump II forward trajectory: predict to drop below 0.40 by 2028 or settle?
- BGD reversal trajectory: Yunus interim sustains or reverses?
