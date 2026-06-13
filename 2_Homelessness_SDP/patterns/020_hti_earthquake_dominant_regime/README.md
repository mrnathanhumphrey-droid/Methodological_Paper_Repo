# Pattern 020 — Haiti is earthquake-dominant; surfaces new Regime 6 in disaster typology

- **ID:** PATTERN_020
- **Status:** candidate-hypothesis (single case)
- **Type:** mechanism (typology extension)
- **Discovered:** 2026-05-25 via PRE_REG_003 holdout fit
- **Severity / interest:** high — extends PATTERN_019 typology

## One line
Haiti is the first country in the corpus where **earthquake (70.4%) > storm (27.5%) > flood (1.9%)** in cumulative disaster-displacement. Adds a 6th regime to [[PATTERN_019]]: earthquake-dominant. Total 2.46M disaster-IDP, dominated by the 2010 and 2021 quakes.

## Numbers (2008-2024, GIDD Disasters)

| Hazard | Total IDP | Share |
|---|---|---|
| Earthquake | 1,732,000 (est) | **70.4%** |
| Storm | 676,000 | 27.5% |
| Flood | 47,000 | 1.9% |
| **Total disaster-IDP** | 2,460,350 | 100% |

The 2010 Port-au-Prince earthquake (Mw 7.0, ~316K deaths, ~1.5M displaced) and the 2021 Tiburon Peninsula earthquake (Mw 7.2, ~650 deaths, ~224K displaced) dominate.

## Why it stands out
Predicted Regime 3 (Caribbean cyclone-dominant) for HTI based on geography — wrong. Earthquake risk on the Enriquillo-Plantain Garden fault zone produces a fundamentally different disaster-displacement regime than the storm-belt islands around it (DOM 76% storm, CUB 99% storm). Two countries on the SAME island (Hispaniola) have different disaster regimes — HTI earthquake-dominant, DOM storm-dominant. **Regime is determined by geophysical exposure at sub-national scale, not nominal climatic zone.**

## Implications for PATTERN_019 and PRE_REG_003
- **Regime 6 (Earthquake-dominant)** is added to the typology
- Likely future Regime 6 members: NPL (Nepal — Himalayan front, 2015 Gorkha quake displaced 2.6M), MEX (mid-Pacific subduction zone), CHL, NZL, PHL (Luzon zones — though PHL is storm-dominant overall, EQ is a notable secondary channel), IDN
- **Test:** pull NPL, CHL, MEX, IDN to see if Regime 6 has multiple members

## Open questions
- Is Regime 6 a robust class or a 1-2 country oddity? Need NPL test to confirm.
- Does HTI's earthquake-dominant displacement pattern interact with its political-collapse trajectory (libdem 0.257 → 0.101)? HTI is on PATTERN_011 / PATTERN_018 as a gang-state-collapse case.
- Does the displacement-per-affected ratio differ for earthquakes vs storms vs floods? HTI 2010 = ~1.5M displaced from ~3M affected = 50%, vs floods typically 20-40%.

## Related
- [[PATTERN_019]] disaster regime typology — this adds Regime 6
- [[PATTERN_009]] earthquake as 4th displacement channel — confirmed here as a regime-determining factor in some countries
- [[PRE_REG_003]] disaster typology pre-reg — this holdout result triggered the new regime

## Data sources
- `D:/IDP/analysis/prereg_holdout_stratified_panel_2026_05_21.parquet` rows iso3=HTI
- GIDD Disasters file, ISO3=HTI
- Cross-referenced with USGS earthquake catalog (2010-01-12 Mw 7.0; 2021-08-14 Mw 7.2)

---

## Dig 2026-05-25 — Regime 6 firmed with 6 confirming countries

Expansion test on candidate Regime 6 countries:

| Country | EQ % | Storm % | Flood % | Total disaster-IDP | Regime classification |
|---|---|---|---|---|---|
| **HTI** | **70.4%** | 27.5% | 1.9% | 2,460,350 | Regime 6 ✓ |
| **NPL** | **71.1%** | 0.6% | 26.9% | 3,913,016 | Regime 6 ✓ |
| **CHL** | **95.4%** | 0.9% | 1.3% | 4,185,661 | Regime 6 ✓ (extreme purity) |
| **ECU** | **77.8%** | 0.1% | 20.1% | 361,244 | Regime 6 ✓ |
| **TUR** | **97.1%** | 0.0% | 0.7% | 4,468,840 | Regime 6 ✓ (2023 Türkiye-Syria EQ Mw 7.8) |
| **ITA** | **60.0%** | 21.9% | 12.0% | 198,802 | Regime 6 ✓ |
| MEX | 7.4% | 42.1% | 50.0% | 2,734,205 | Regime 4 (mixed) |
| IDN | 27.6% | 2.2% | 58.7% | 8,582,905 | Regime 4 (mixed, EQ significant) |
| JPN | 16.2% | 64.5% | 10.8% | 4,778,142 | Regime 4 (storm-leaning) |
| PER | 3.3% | 4.8% | 88.3% | 928,259 | Regime 4 (flood-leaning) |

**Result: Regime 6 (Earthquake-dominant) is FIRMED with 6 confirming countries** across 3 continents. The geographic distribution traces the major subduction-zone + collision-zone fault systems:
- HTI: Caribbean plate (Enriquillo-Plantain Garden fault)
- NPL: Indian plate / Himalayan front
- CHL: Nazca plate / Andean subduction
- ECU: Nazca plate / Andean subduction
- TUR: Anatolian-African-Arabian plate junction (East Anatolian Fault)
- ITA: Adriatic-Eurasian plate boundary (Apennines)

**Notable non-fits:** MEX, IDN, JPN, PER all have significant earthquake activity but are classified Regime 4 because their disaster-displacement portfolios are MIXED. JPN especially: 64% storm-dominant despite multiple major EQ events (Tohoku 2011 displaced 470K — large in absolute terms but smaller as % of cumulative).

**Status updated:** candidate-hypothesis (single case) → **candidate-hypothesis FIRMED (6 cases across 3 continents)**. PATTERN_019 typology now has 6 confirmed regimes (Regime 5 drought-dominant remains falsified — drought is sub-channel within Regime 4).

---

## Dig 2026-05-25 — Regime 6 is uniformly single-event-driven (PRE_REG_013 first fit)

P2-A sub-typing test (PRE_REG_013) attempted to split Regime 6 into 6a single-quake-driven (≥50% from one event) vs 6b multi-quake-distributed (<50%). Result: **ALL 6 confirmed Regime-6 countries show ≥50% single-event share** (range 50.1% to 94.3%).

| ISO | EQ total IDP | Max event | Max share % | Sub-type |
|---|---|---|---|---|
| HTI | 1,732,360 | 1,500,000 | 86.6 | single-event |
| NPL | 2,782,155 | 2,623,000 | 94.3 | single-event |
| TUR | 4,339,796 | 4,047,000 | 93.3 | single-event |
| CHL | 3,994,868 | 2,000,000 | 50.1 | single-event (borderline) |
| ECU | 281,026 | 259,000 | 92.2 | single-event |
| ITA | 119,220 | 70,000 | 58.7 | single-event |

**Refined Regime 6 definition**: EQ-dominant (≥60% of total disaster-IDP) AND single-event-driven (single largest event ≥ 50% of EQ-IDP). The original predicted "6b multi-quake-distributed" sub-type doesn't exist in the data window.

**Mechanism**: Reaching the EQ ≥ 60%-share threshold within 17 years requires at least one major (Mw ≥ 7.0) event. Multi-quake countries with high EQ exposure (MEX, IDN, JPN) don't qualify as Regime 6 because their distributed EQ-IDP doesn't dominate their other channels — they fall into Regime 4.

**Status**: Regime 6 refined into a sharper class — not "EQ-dominant + sub-typed" but "EQ-dominant single-event-driven, uniform within-class". Sub-typing applies to Regimes 3 and 4, NOT to Regime 6. See `papers/PAPER_2_DISASTER_REGIMES/digs/2026_05_25_P2_A_within_regime_sub_typing.md`.

---

## Dig 2026-05-25 — Regime 6 is EVENT-LATENT (PRE_REG_014 first fit)

Phase 3 stability test revealed that **4 of 6 Regime-6 countries gained R6 status only after 2007** via single major quake events:

| Country | 1980-2007 classification | 2008-2024 classification | Driving event |
|---|---|---|---|
| HTI | 3a (Bimodal-mega-storm) | 6 (EQ-dominant) | 2010 Port-au-Prince Mw 7.0 |
| NPL | UNCLASSIFIED | 6 (EQ-dominant) | 2015 Gorkha Mw 7.8 |
| CHL | 4c (Balanced mixed) | 6 (EQ-dominant) | 2010 Maule Mw 8.8 + 2014 Iquique |
| ECU | 4a (Flood-leaning mixed) | 6 (EQ-dominant) | 2016 Pedernales Mw 7.8 |
| TUR | 6 (EQ-dominant) | 6 (EQ-dominant) | stable — pre-existing R6 status |
| ITA | 6 (EQ-dominant) | 6 (EQ-dominant) | stable — L'Aquila + Irpinia |

**Refined Regime 6 definition (post-Phase 3)**:
Regime 6 status is the **JOINT product** of:
1. **Geophysical exposure** (subduction-zone, collision-zone, or major-fault tectonics) — necessary but not sufficient
2. **Major-event occurrence within observation window** — necessary

A country's R6 classification is **window-sensitive**: it can be "latent R6" (subduction-zone exposed but no major event in window) and "activated R6" (event occurs, displacement registers, classification triggers).

**Implications**:
- 4 of 6 current R6 members were classified differently pre-2007 — R6 "arrived"
- "Latent R6" candidates that could activate in future: IRN (2017/2022 quakes building), GRC (1981, 1995 historical R6), NZL (Christchurch 2011), MEX/IDN (multi-event but other channels dominate)
- Paper 2 must report R6 classification with observation window caveat

**Cross-ref**: `papers/PAPER_2_DISASTER_REGIMES/digs/2026_05_25_P2_H_F_phase3_stability_USA.md`
