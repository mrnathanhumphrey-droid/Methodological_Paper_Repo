# Pattern 003 — Burkina Faso: industrial-scale conflict displacement, 22× fatality jump

- **ID:** PATTERN_003
- **Status:** noted
- **Type:** anomaly
- **Discovered:** 2026-05-21 via `build_sahel_stratified.py` first look
- **Severity / interest:** high

## One line
BFA went from zero conflict-displacement (1998-2013) and 459 war-fatalities (2014-2019) to 2,728,000 conflict-displaced and 10,403 war-fatalities in 2020-2024 — a 22× fatality jump in five years and a step-change in the displacement signal.

## Numbers

| Period | Conflict-displaced (cum.) | War fatalities (state-based) | Strife | One-sided |
|---|---|---|---|---|
| pre-crisis 1998-2013 | 0 | 0 | 0 | 0 |
| early Sahel 2014-2019 | 560,600 | 459 | 40 | 1,022 |
| acute Sahel 2020-2024 | **2,728,000** | **10,403** | 476 | 4,823 |

Year-by-year acute fatalities: 512 (2020), 991 (2021), 2,093 (2022), **4,608 (2023)**, 2,199 (2024). Annual conflict-displacement: 515K (2020), 682K (2021), 438K (2022), 713K (2023), 380K (2024).

## Why it stands out
The 2014-2019 → 2020-2024 transition is not gradual — it is an order-of-magnitude jump on both fatalities and displacement. Most of the conflict is state-vs-organized-group (war_state_based: 10,403 vs strife: 476). One-sided-on-civilians is also high (4,823). This is the largest country-level conflict-displacement signal in our Sahel cluster by far — for context, MLI's acute is 995K vs BFA's 2.7M; NER's conflict-displacement is 628K.

## Open questions
- How much of the BFA 2020 → 2023 ramp is correlated with the two 2022 coups vs the Wagner Group entry vs the Operation Barkhane withdrawal?
- Does the 2024 drop (from 713K → 380K conflict-displacement and from 4,608 → 2,199 fatalities) reflect a real ceasefire / military reversal, or just data lag / saturation effects?
- At admin-1 level, is the displacement concentrated in the Sahel/Nord/Est regions where ISGS+JNIM operate, or also in Centre-Nord/Boucle-du-Mouhoun?

## Related
- [[PATTERN_002]] BFA libdem collapse is the largest in the cluster; pattern timing matters
- [[PATTERN_006]] BEN sits adjacent to BFA on the south; spillover trajectory

## Data sources
- `D:/IDP/analysis/sahel_stratified_panel_2026_05_21.parquet` rows where iso3=BFA
- UCDP-GED filtered for country=Burkina Faso
- GIDD `1_Displacement_data` sheet, ISO3=BFA

---

## Dig 2026-05-25 — actor decomp + admin-1 + ramp-shape

**The jump shape:** UCDP fatality trajectory 2016-2024:

| Year | Events | Fatalities | YoY ratio |
|---|---|---|---|
| 2016 | 2 | 26 | — |
| 2017 | 27 | 54 | 2.1× |
| 2018 | 65 | 195 | 3.6× |
| 2019 | 222 | 1,246 | **6.4×** |
| 2020 | 166 | 1,167 | 0.94× |
| 2021 | 191 | 1,458 | 1.25× |
| 2022 | 237 | 2,704 | 1.85× |
| 2023 | 599 | **6,122** | 2.26× |
| 2024 | 307 | 4,251 | 0.69× |

The "22× fatality jump" originally cited was 2016 → 2019 (26 → 1,246 ≈ **48×** actually). The single steepest single-year was 2018 → 2019 (6.4×). 2023 is the fatality peak; 2024 is a partial pullback. Displacement ramps lagged fatalities by ~1 year early then decoupled (380K displaced in 2024 despite 4.2K fatalities, suggesting structural rather than event-driven displacement).

**Actor decomposition (2014-2024):** Government of Burkina Faso is the dominant *initiator* (12,675 fatalities-on-target), with JNIM as second-most-active initiator (2,792). On the target side, JNIM absorbs 9,611 and civilians 5,845 — meaning the kinetic profile is **state counterinsurgency operations against JNIM (with civilian collateral)**, not jihadist-on-state attacks. IS Sahel Province (1,367 initiated / 1,711 absorbed) is a secondary insurgent group. Koglweogo (Mossi self-defense / lynching militias) is a third actor type producing/absorbing ~330/56.

**Admin-1 acute (2020-2024) fatalities:**

| Region | Fatalities | Notes |
|---|---|---|
| Sahel region | 4,602 | Northern frontier with Mali/Niger — Liptako-Gourma triangle |
| Est region | 3,003 | Eastern frontier with Niger/Benin |
| Centre Nord | 2,541 | |
| Nord | 1,714 | |
| Boucle du Mouhoun | 1,542 | Western/central |
| Centre Est | 1,512 | |
| Hauts Bassins | 269 | |
| Cascades | 267 | |
| Sud-Ouest | 75 | |
| Centre Ouest | 64 | |

The signal is **concentrated in the northern/eastern frontier zones** (Sahel + Est + Centre Nord + Nord = 11,860 of total ~15,500 ≈ 76%). Capital Centre region is below the top-10 — Ouagadougou is largely insulated.

**Status updated:** noted → **firmed-anomaly** (mechanism understood: state counterinsurgency in Liptako-Gourma against JNIM; civilian displacement is largely collateral pressure from this campaign).
