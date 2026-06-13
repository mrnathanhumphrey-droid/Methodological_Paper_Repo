# Pattern 025 — Regime 3 sub-typology: bimodal-mega-storm vs perpetual-storm

- **ID:** PATTERN_025
- **Status:** candidate-hypothesis (typology refinement)
- **Type:** mechanism (sub-typology within Regime 3)
- **Discovered:** 2026-05-25 via deep PRE_REG_003 within-regime dig
- **Severity / interest:** medium-high (refines PATTERN_019 typology)

## One line
Within disaster-displacement Regime 3 (storm-dominant), countries split into two sub-types: **Regime 3a — bimodal-mega-storm** (USA, CUB) where storm-displacement is concentrated in 3-4 catastrophic years; and **Regime 3b — perpetual-mega-storm** (PHL) where 16 of 17 years exceed 1M storm-displaced.

## Numbers — Storm channel year-by-year

### Regime 3a: bimodal-mega-storm
USA storm-displacement 2008-2024:
- Mega-years (>1M): 2008 (1.96M Gustav/Ike), 2017 (1.05M Harvey/Irma/Maria), **2024 (10.24M — Helene/Milton)**
- Median: 471K; max/median = **21.7×**
- Most years: <1M; few catastrophic spikes

CUB storm-displacement 2008-2024:
- Mega-years (>1M): 2008 (2.71M Gustav/Ike), 2016 (1.08M), 2017 (1.74M Irma)
- Many quiet years (e.g. 2019 9.9K, 2023 13K)
- Max/median = 7.7×

### Regime 3b: perpetual-mega-storm
PHL storm-displacement 2008-2024:
- Mega-years (>1M): **16 of 17 years** (only 2010 missed)
- Range: 287K (2010) to 7.74M (2024)
- Max/median = 2.5× (steady-high distribution)
- Cumulative: **71.17M displaced** — largest single-channel total in entire 50-country corpus

## Why it stands out
- **Within-regime heterogeneity matters for policy.** USA needs catastrophic-event preparedness (FEMA surge capacity, evacuation infra); PHL needs annual baseline preparedness (continuous IDP camp infrastructure)
- **Bimodal-mega-storm (3a) parallels bimodal-mega-flood (Regime 1, PAK)** — same statistical structure, different physical mechanism (cyclones vs glacial monsoon)
- **2024 was a US watershed year**: 10.24M storm-displaced in a single year is the largest single-year storm signal in the corpus, driven by Helene + Milton consecutive Atlantic hurricane season. May indicate climate-attribution-driven regime intensification in US Gulf coast.

## Implications for PATTERN_019 typology
The 6-regime typology now has sub-typing within at least 2 regimes:
- Regime 1 (bimodal-mega-flood) — PAK; structurally unique
- **Regime 3a (bimodal-mega-storm) — USA, CUB**
- **Regime 3b (perpetual-mega-storm) — PHL** (potentially: VNM, MOZ at smaller absolute scale)
- Other regimes need within-regime sub-typing tests

## Open questions
- Where do DOM, FJI, VUT fit on the 3a vs 3b spectrum? Need same year-by-year analysis.
- Does Bangladesh fit 3b (perpetual) at smaller scale? (BGD storm-mega-years: 6 of 17)
- Climate-attribution: is USA shifting from 3a to 3b as Atlantic hurricane intensification continues? 2024 alone is 5× the previous USA single-year peak.
- Is PHL a "first-mover" of what other tropical-cyclone countries will become under continued ocean warming?

## Related
- [[PATTERN_019]] disaster regime typology — this refines Regime 3
- [[PATTERN_016]] PAK bimodal-mega-flood — Regime 1 analog
- [[PATTERN_020]] HTI EQ-dominant — Regime 6 (orthogonal to 3a/3b distinction)
- [[PRE_REG_003]] disaster typology pre-reg — this is a within-pre-reg refinement

## Data sources
- GIDD Disasters storm hazard 2008-2024 for USA, PHL, CUB, DOM, FJI, VUT, BGD
- Year-by-year output from deep_dig_pre_regs.py 2026-05-25

---

## Dig 2026-05-25 — 3a expanded to 5 members; 3b remains single-member (P2-A first fit)

PRE_REG_013 prediction set C extended sub-typing test to DOM, FJI, VUT, BGD year-by-year.

| ISO | Years>1M storm | Total yrs | Storm max/median | Sub-type |
|---|---|---|---|---|
| DOM | 0 | 15 | 6.43× | 3a-leaning |
| FJI | 0 | 12 | 10.28× | **3a bimodal-mega-storm** |
| VUT | 0 | 10 | 94.12× | **3a bimodal-mega-storm** (small-state extreme variance) |
| BGD | 6 | 15 | 7.61× | between 3a and 3b (40% mega-year frequency) |

**3a confirmed members now: USA, CUB, DOM, FJI, VUT (5 cases).**
**3b confirmed members: PHL only (1 case).**

**PHL-first-mover hypothesis gains support**: PHL is the only country in the corpus with 16/17 mega-storm-years AND chronic exposure pattern. If climate-attribution shifts other tropical-cyclone countries toward chronic exposure, they would transition from 3a → 3b. This is the testable forward prediction in PRE_REG_015 (climate-attribution regime-shift).

**BGD is interesting**: at 6 of 15 mega-years (40%), BGD sits between 3a (sparse mega-events) and 3b (chronic mega-events). Could be a third sub-type "mid-density mega-storm" or a transitional state.

---

## Dig 2026-05-25 — Displacement-per-affected: 3a >> 3b (post-hoc P2-I finding)

PRE_REG_016 first fit revealed an unpredicted finding:

| Sub-regime | Median ratio % | N |
|---|---|---|
| 3a (USA, CUB) | **85.1** | 33 |
| 3b (PHL) | **37.1** | 53 |

**Bimodal mega-storms drive HIGHER displacement-per-affected than perpetual storms** — opposite to the pre-locked prediction.

**Mechanism hypothesis (post-hoc)**: Mega-event response triggers **mandatory evacuation** (USA Helene/Milton, CUB cyclone evacuations) which is counted as displacement. PHL chronic exposure populations stay in place between typhoons — they're not counted as IDPs unless permanently displaced.

This is a **reporting/evacuation-counting** finding, not a physical-mechanism finding. Needs forward pre-reg if to be formally claimed in Paper 2.

**Cross-ref**: `papers/PAPER_2_DISASTER_REGIMES/digs/2026_05_25_P2_I_displacement_per_affected_ratios.md`
