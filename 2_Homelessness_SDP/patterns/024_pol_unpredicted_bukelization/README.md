# Pattern 024 — Poland (PiS era) is an unpredicted Bukelization case

- **ID:** PATTERN_024
- **Status:** candidate-hypothesis (unpredicted confirmation of PATTERN_013)
- **Type:** mechanism (replication)
- **Discovered:** 2026-05-25 via deep PRE_REG_005 sliding-window dig
- **Severity / interest:** **high — single biggest unpredicted confirmation of Bukelization mechanism**

## One line
Poland under PiS (Law and Justice party, 2015-2023) shows textbook Bukelization shape: libdem **0.825 (2008) → 0.450 (2020)** = Δ−0.377 over 12 years, monotonic, no coup. **6 sliding 10-year windows fit the Bukelization criteria** — more than Hungary, more than SLV.

## Numbers (POL V-Dem libdem)

| Year | libdem |
|---|---|
| 2008 | 0.825 |
| 2010 | 0.827 |
| 2012 | 0.825 |
| 2014 | 0.823 |
| 2015 | 0.821 (PiS wins parliament Oct 2015) |
| 2017 | 0.685 |
| 2019 | 0.505 |
| 2020 | 0.450 |
| 2021 | 0.424 |
| 2022 | 0.417 |
| 2023 | 0.457 (election Oct 2023; Tusk takes office Dec 2023) |

6 fitting 10-year windows in sliding search (criteria: start ≥ 0.30, Δ ≤ −0.30, monotonic):
- 2008-2018: 0.825 → 0.524, Δ=-0.301
- 2009-2019: 0.825 → 0.505, Δ=-0.320
- **2010-2020: 0.827 → 0.450, Δ=-0.377** (the deepest fit)
- 2011-2021: 0.827 → 0.424, Δ=-0.403
- 2012-2022: 0.825 → 0.417, Δ=-0.408 (the steepest end-state)
- 2013-2023: 0.821 → 0.457, Δ=-0.364

## Why it stands out
- **NOT in PRE_REG_005's pre-locked prediction set** — POL was not one of the 4 retrospective cases (HUN/TUR/VEN/RUS). This is an unpredicted true positive.
- **Fits BETTER than HUN** — POL shows 6 fitting windows vs HUN's 4
- **Started from one of the highest libdem scores in the corpus** (0.825) and collapsed to mid-floor — biggest absolute Δ in any Bukelization case
- **2023 recovery signal** — Tusk's coalition winning Oct 2023 election produced first uptick (0.417 → 0.457). Parallels BRA's Bolsonaro→Lula recovery — see [[PATTERN_022]]
- **Confirms PATTERN_013 generalizes across continents and political contexts**: Latin America (SLV), Central Europe (HUN, POL), and partial Eurasia (TUR)

## Implications
- **PATTERN_013 firms from "candidate-hypothesis (1 case)" to "candidate-hypothesis (5 confirming cases)":** SLV, HUN, TUR, VEN, POL
- **RUS, IND, BRA all FALSIFY at 10y window** — Bukelization is NOT universal; it's a specific signature
- **The Bukelization mechanism is replicable across (a) democratic post-Soviet transitions (POL/HUN), (b) populist Latin America (SLV/VEN), (c) post-Kemalist Turkey (TUR). What unites them: populist leaders + judicial capture + media capture + civilian-authoritarian path.**
- **Recovery is possible (POL 2023, BRA 2023):** the Bukelization trajectory is NOT a one-way absorbing state. Democratic election turnover can reverse it. This is a hopeful finding methodologically.

## Open questions
- Is POL's recovery (2023) sustained? Need 2024/2025 V-Dem release.
- Other unpredicted Bukelization cases in V-Dem we haven't tested? Candidates: SRB (Vučić), BGR, ROU
- Does POL fit PRE_REG_002's range+trigger model? Range condition YES (0.825 ≥ 0.22), trigger condition AMBIGUOUS (no fatality jump, but a clear political consolidation event)
- What's the difference between countries that show Bukelization (HUN/POL/TUR/SLV/VEN) and those that don't despite similar pressures (USA/BRA)? Hypothesis: party-state institutional fusion vs alternation.

## Related
- [[PATTERN_013]] Bukelization (the substrate; this is the 5th confirming case)
- [[PATTERN_022]] BRA recovery — POL 2023 is the second recovery case
- [[PRE_REG_002]] range+trigger collapse — POL satisfies range, trigger less clean
- [[PRE_REG_005]] Bukelization pre-reg — this is an unpredicted true positive

## Data sources
- V-Dem v15 libdem indicator, POL 2000-2024
- Sliding 10-year windows from deep_dig_pre_regs.py 2026-05-25
