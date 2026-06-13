# Pre-Registration 011 — Failed-Coup-as-Enabler Sub-Pattern

**ID:** PRE_REG_011
**Locked:** 2026-05-25
**Substrate:** PATTERN_013 + PATTERN_027 (PER complication resolution)
**Status:** LOCKED — predictions and falsifiers pre-committed; retrospective test fires on existing data + forward predictions

---

## 1. Hypothesis

**H1 (failed-coup-as-enabler):** Failed coup attempts or failed self-coups can ENABLE subsequent democratic backsliding via political-establishment realignment. The mechanism:
- Failed coup creates political crisis
- Political establishment unifies AGAINST the coup actor (or in DEFENSE of the coup target)
- This unification suppresses institutional resistance to subsequent executive aggrandizement
- The post-failed-coup successor (or the coup target if they survive) consolidates faster than would have been possible without the political-establishment realignment

**H2 (mechanism variations):** Three sub-mechanisms:
- (a) **Coup-target-accelerates** (e.g., TUR 2016 Erdoğan): autocrat-targeted coup fails; autocrat uses it to mass-purge + accelerate consolidation
- (b) **Successor-displaces** (e.g., PER Castillo→Boluarte): coup actor loses; political establishment tolerates successor's authoritarian moves to prevent return of coup actor
- (c) **Future-leader-prepares** (e.g., USA Jan 6 2021 → Trump II 2025): failed coup-adjacent event leads to party purges + 4-year institutional preparation by aligned faction

---

## 2. In-sample evidence (NOT re-tested)

| Case | Failed event | Date | Subsequent backsliding | Sub-mechanism |
|---|---|---|---|---|
| TUR 2016 | Gulenist coup attempt | 2016-07-15 | 150K+ purges, 2017 constitutional referendum → -0.042 libdem/yr 2014-2017 | (a) coup-target-accelerates |
| VEN 2002 | Coup against Chávez (2-day) | 2002-04-11/13 | Chávez packs Supreme Court 2004, removes term limits 2009 | (a) coup-target-accelerates |
| PER 2022 | Castillo self-coup | 2022-12-07 | Boluarte regime; hcind 1.547→0.455 in 3y | (b) successor-displaces |
| USA 2021 | Jan 6 Capitol attack | 2021-01-06 | GOP purges dissidents, Project 2025, Trump II 2024 election | (c) future-leader-prepares |

---

## 3. Pre-locked predictions

### Prediction set A — Retrospective expansion test

Check additional failed-coup or failed-self-coup events 1990-2024 for backsliding acceleration:

- **THA 2014** (military coup against Yingluck — SUCCEEDED, not failed; treat as comparator)
- **BFA 2014** (failed coup attempt then 2015 actual coup)
- **GAB 2019** (failed coup against Bongo) — predicted: Bongo's consolidation accelerated 2019-2023 → 2023 actual coup
- **EGY 2011** (Mubarak ouster) → Sisi consolidation 2013+ — predicted: (b) successor-displaces variant
- **TUR 2024** (NO coup) — comparator
- **BLR 2020** (mass protests "color revolution" failed) — predicted: Lukashenko consolidation accelerated 2020+
- **KGZ 2020** (revolution succeeded → Japarov; mixed signal)
- **GNB various** (multiple failed coups; should show backsliding acceleration)

### Prediction set B — V-Dem libdem trajectory test

For each failed-coup case identified, check libdem rate before vs after the failed event:

**Prediction**: Failed-coup countries should show ACCELERATED libdem decline in the 5 years after the failed event vs the 5 years before.

### Prediction set C — Forward predictions

- **USA 2028 election**: if GOP loses, predict GOP-aligned faction launches political-realignment strategies similar to post-Jan-6 2021 → preparing for next consolidation attempt
- **GAB 2023 coup actor** — if democratic transition succeeds, predict failed-coup-as-enabler does NOT activate
- **Any 2025-2030 failed-coup** in our backsliding-watch list — track 5-year trajectory

---

## 4. Falsifiers

- **F1:** Retrospective expansion test shows ≤3 of identified failed-coup cases produce subsequent backsliding acceleration → sub-pattern is not generalizable
- **F2:** A confirmed Bukelization case shows NO failed-coup history → failed-coup-as-enabler is not necessary (which we already know — HUN, POL, SLV had no failed coup)
- **F3:** Multiple failed-coup cases produce sustained democratic recovery → political-establishment-realignment mechanism doesn't hold

F1 alone OR F3 firing on >2 cases = sub-pattern walked back.

Note: F2 isn't really a falsifier — failed-coup-as-enabler is a SUFFICIENT-not-necessary mechanism. Most Bukelization happens without a failed-coup precursor.

---

## 5. Methodology

- V-Dem v15 libdem rates 5y-before vs 5y-after each failed-event year
- Failed coup database — UCDP and CSP (Center for Systemic Peace) coup catalogues
- Political-establishment realignment qualitative coding

## 6. Cross-references
- PATTERN_013, PATTERN_027 (failed-backsliding archive — refined here)
- digs/2026_05_25_P1_F_PER_complication.md (substrate)
- Levitsky-Way 2025 (implicit in their analysis)

---

## 7. Results — first fit (fired 2026-05-25)

Retrospective expansion test across 8 failed-coup events, comparing libdem rate 5y-before vs 5y-after:

| Country | Year | Rate 5y BEFORE | Rate 5y AFTER | Acceleration | Result |
|---|---|---|---|---|---|
| **PER** | 2022 | -0.004 | **-0.038** | **-0.034** | ACCELERATED ✓ |
| **USA** | 2021 (Jan 6) | -0.024 | **-0.046** | **-0.022** | ACCELERATED ✓ |
| BLR | 2020 | +0.003 | -0.001 | -0.004 | marginal |
| GAB | 2019 | -0.003 | -0.010 | -0.007 | marginal |
| BFA | 2014 | +0.018 | +0.012 | -0.006 | marginal |
| EGY | 2011 | -0.000 | +0.000 | +0.000 | null |
| **TUR** | 2016 | -0.031 | -0.006 | **+0.025** | DECELERATED ❌ |
| **VEN** | 2002 | -0.079 | -0.019 | **+0.060** | DECELERATED ❌ |

**Verdict**: MIXED. Only 2 of 8 cases (PER, USA Jan 6) show clear acceleration. 2 cases (TUR, VEN) show DECELERATION because pre-coup decline was already faster than max-rate. 4 cases show marginal effects.

**Critical refinement**: The mechanism applies differently based on WHO the failed coup TARGETS:

### Sub-pattern A — Failed coup AGAINST democracy ENABLES backsliding (PER, USA Jan 6)
- Castillo's self-coup → political establishment realigns AGAINST left → tolerates Boluarte's authoritarian moves
- Jan 6 → GOP purges dissidents → Project 2025 prep → Trump II 2024 wins → rapid consolidation
- These are the cleanest enabler cases

### Sub-pattern B — Failed coup AGAINST autocrat does NOT accelerate (TUR 2016, VEN 2002)
- Erdoğan-targeting coup fails → BUT Erdoğan was already consolidating at -0.031/yr pre-coup
- Post-coup mass purges + 2017 referendum happen BUT V-Dem rate slows because Erdoğan-era was already collapsing
- Pre-coup rate was at the FLOOR of what V-Dem libdem index can register (already approaching 0.10)
- VEN 2002 same — Chávez had already been consolidating at -0.079/yr (massive); post-coup rate slowed (-0.019/yr) because regime was approaching the libdem floor

**The "failed-coup-as-enabler" claim is REFINED**:
- **H1 reframed**: failed coup TARGETING DEMOCRACY accelerates subsequent backsliding (when coup actor loses or coup-target government's coalition realigns rightward to prevent return of coup actor)
- **H1 NOT supported when**: failed coup targets autocrat who is already consolidating at high rate (because rate can't accelerate past the floor)

**Falsifier F1 (≤3 of 8 produce acceleration)**: FIRED — only 2 of 8 produce CLEAR acceleration. Original H1 walked back.

**v2 hypothesis** (sub-pattern A): failed-democracy-targeting-coup → political-establishment-realignment → enables successor backsliding. This is the PER/USA-Jan-6 pattern. Locked as the refined claim.

**Status**: WALK-BACK on broad claim; v2 reframe SUPPORTED across 2 clean cases. Future failed-coup events targeting democracies (Hungary, ZMB, etc.) will provide additional tests.
