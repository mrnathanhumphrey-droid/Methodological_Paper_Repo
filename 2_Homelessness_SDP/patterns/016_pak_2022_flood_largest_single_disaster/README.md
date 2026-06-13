# Pattern 016 — PAK 2022 floods: largest single-channel disaster displacement in corpus

- **ID:** PATTERN_016
- **Status:** noted
- **Type:** anomaly (magnitude)
- **Discovered:** 2026-05-25 via South Asia cluster build
- **Severity / interest:** high

## One line
Pakistan acute-period (2020-2024) disaster-displacement is **9,968,000**, of which **9,791,671 is flood alone** — the largest single-hazard-channel displacement total in our 19-country corpus. Driven primarily by the 2022 monsoon floods (~33M affected, ~8M displaced per IDMC).

## Numbers

PAK by period and channel:

| Period | Conflict-disp | Disaster-disp | Flood (share of disaster) |
|---|---|---|---|
| pre_crisis 1998-2013 | 4,142,000 | 13,797,000 | (not yet broken out) |
| early 2014-2019 | 1,001,100 | 1,889,700 | — |
| **acute 2020-2024** | **7,140** | **9,968,000** | **9,791,671 (98%)** |

Comparators (acute disaster-displacement total):
- PAK 9.97M
- NER 1.92M (was the previous flood-dominance flag, PATTERN_004)
- AFG 1.73M
- MMR 1.74M
- SOM (Horn drought-era) lower

PAK 2020-2024 conflict-disp is **7,140** — essentially zero, three orders of magnitude below disaster. PAK is functionally a pure-disaster country in the acute period (despite ongoing TTP / Balochistan insurgency, scale is negligible compared to flood).

## Why it stands out
- **Scale**: 9.79M flood-displacement acute is bigger than every country's full-panel conflict total except DRC and UKR. Flood as a displacement channel can dominate everything else.
- **Inverts conflict-as-primary frame**: For PAK, the corpus framework's main attractor (conflict→displacement) is the wrong story. Disaster is the story.
- **Pattern echo from NER**: Same shape as PATTERN_004 (NER 2024 flood > entire war period), at ~9× the scale. Suggests this isn't a Sahel-specific quirk — it's a general feature of climate-vulnerable mid-population countries.
- **Tests PATTERN_001's 3-channel hypothesis at upper tail**: Flood channel alone can be larger than conflict + drought combined.

## Open questions
- Is PAK 2022 a one-off or part of a rising trend in monsoon-flood displacement? (CHIRPS + ERA5 will say.)
- How does PAK's acute flood:fatality ratio compare to conflict? Disaster fatalities (EM-DAT) needed.
- Does the climate-attribution literature on the 2022 Pakistan floods (WWA studies) feed into a "conflict-attributable vs climate-attributable displacement" decomposition?

## Related
- [[PATTERN_001]] 3-channel displacement — PAK is the extreme flood-channel case
- [[PATTERN_004]] NER 2024 flood>war — same shape, smaller scale
- [[PATTERN_015]] DRC 30M cumulative — comparator for "one country dominates the corpus" framing, but DRC's is conflict-side

## Data sources
- `D:/IDP/analysis/south_asia_stratified_panel_2026_05_21.parquet`
- GIDD Disasters sheet, ISO3=PAK, hazard_type=Flood

---

## Dig 2026-05-25 — EM-DAT confirm + history + non-stationarity

**EM-DAT 2022 flood event (single record):**

| Field | Value |
|---|---|
| Disaster Type | Flood (General) |
| Start - End Month | June - September 2022 |
| Locations | Balochistan (Lasbela, Jhal Magsi, Killa Saifullah, Pishin, Noshki, Kachhi, Khuzdar, Kalat, Chaman); Sindh; Punjab; KP; Azad Jammu; Gilgit Baltistan; Kashmir |
| Total Deaths | 1,739 |
| Total Affected | **33,012,865** |

This is the 2022 Pakistan "monster monsoon" — a single seasonal event spanning June-September. EM-DAT counts 33M affected; GIDD logs 8.16M flood-displaced (~25% of affected, vs NER 2024's 77%). The ratio is lower because most affected populations stayed (homes/livelihoods damaged but not destroyed) rather than displaced — but the absolute displacement is still 5× anything else in the corpus.

**PAK GIDD disaster-displacement history 2008-2024 (flood-only):**

| Year | Flood-displaced | Notes |
|---|---|---|
| 2008 | 82,200 | |
| 2009 | 84,000 | |
| **2010** | **11,000,000** | Indus mega-flood (Sindh/Punjab) — previous record |
| 2011 | 300,000 | Sindh flooding |
| 2012 | 1,857,000 | |
| 2013 | 124,000 | |
| 2014 | 758,636 | |
| 2015 | 331,200 | |
| 2016 | 12,700 | |
| 2017 | 1,630 | |
| 2018 | 760 | (drought year) |
| 2019 | 33,082 | |
| 2020 | 810,170 | |
| 2021 | 2,028 | |
| **2022** | **8,163,375** | **The monster monsoon** |
| 2023 | 647,034 | |
| 2024 | 169,064 | |

**Two mega-events in 12 years** (2010: 11M, 2022: 8.16M) with intermittent moderate years and several near-zero years. This is **NOT a non-stationary upward trend** — it's a bimodal distribution where most years are sub-million and a small number are mega-events. The 2022 event was *bigger than 2010 in per-capita-affected terms* (because Pakistan's population grew) but *smaller in raw displacement* than 2010.

**Climate attribution:** The 2022 floods have been attributed in part to climate change (WWA study Sep 2022: 50-75% increase in rainfall over Sindh/Balochistan vs preindustrial baseline; mixed signal). Glacial melt in northern PAK contributed alongside La Niña-amplified monsoon.

**Status updated:** noted → **firmed-anomaly**. PAK is a bimodal mega-flood regime, not a steady upward trend. The 2010 and 2022 events define the upper tail; 2024 (169K) is back to mid-range.

**Open thread:** Are there other bimodal-mega-flood countries in the corpus? PHL, BGD, IND, VNM, MOZ are candidates. If yes, PAK isn't unique — it's an instance of a class. If no, PAK is structurally distinctive (Indus geography + monsoon + glaciers).

**2026-05-25 bimodal test result — PAK IS UNIQUE:**

| Country | Total acute flood-IDP | Flood max year | Flood max | Flood median | **Max/median ratio** | Mega-years (>1M) |
|---|---|---|---|---|---|---|
| **PAK** | 24.4M | 2010 | **11M** | 169K | **65.1×** | 3 (2010, 2012, 2022) |
| VNM | 0.6M | 2011 | 230K | 14K | 15.9× | 0 |
| MOZ | 0.6M | 2013 | 186K | 24K | 7.9× | 0 |
| BGD | 7.7M | 2020 | 1.9M | 400K | 4.8× | 2 |
| IND | 45.8M | 2012 | 8.9M | 2.4M | 3.8× | **14 of 17 years** |
| PHL | 10.2M | 2012 | 1.6M | 626K | 2.5× | 3 |

PAK's max/median of **65×** is an order of magnitude higher than any peer. India is the polar opposite — 14 of 17 years exceed 1M flood-displaced, **steady annual high-flood regime**. PHL is steady-moderate. BGD has frequent moderate floods. VNM and MOZ are low-flood (storm-dominant — see [[PATTERN_019]]).

**Conclusion:** PAK's bimodal-mega-flood pattern is **NOT a class** of countries — it's structurally distinctive to PAK's Indus river geography (steep Himalayan gradient + glacial melt + monsoon belt + flat Indus plain). The class-of-countries hypothesis is falsified; the structural-uniqueness hypothesis is supported.

This is a clean honest-test result: we predicted PAK might be one of a class, ran the test, the data said no.

**Cross-link strengthening:** Combined with [[PATTERN_004]] (NER 2024 monsoon flood: single event, 5 regions, 1.17M), the [[PATTERN_001]] 3-channel hypothesis has now firmly shown that **single-monsoon events can dominate a country's entire decade of displacement** in flood-vulnerable regimes. The flood channel is not background noise; it's intermittent catastrophe.
