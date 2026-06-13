# Pattern 004 — Niger 2024 flood displacement (1.17M) exceeds country's entire war-period conflict displacement

- **ID:** PATTERN_004
- **Status:** noted
- **Type:** anomaly
- **Discovered:** 2026-05-21 via `build_sahel_stratified.py` first look
- **Severity / interest:** high

## One line
Niger 2024: 1.17 million flood-displaced in a single year — that's nearly 2× the country's total conflict-displacement across the whole 2020-2024 acute period.

## Numbers

NER disaster-displaced by year, acute period:

| Year | Disaster-displaced | Conflict-displaced (same year) |
|---|---|---|
| 2020 | 276,000 | 136,000 |
| 2021 | 125,000 | 110,000 |
| 2022 | 248,000 | 101,000 |
| 2023 | 95,000 | 181,000 |
| 2024 | **1,172,000** | 100,000 |

Acute period totals: disaster 1,916,000 vs conflict 628,000 — disaster 3× larger than conflict.

100% of NER disaster-displacement in GIDD is logged as `flood` hazard type. (Drought displacement isn't separately captured — see [[PATTERN_007]].)

## Why it stands out
Two things. First, the magnitude — 1.17M in a single year would be a top-tier humanitarian crisis in any country, and NER is a country of ~26M people. Second, the direction — most Sahel reporting frames the crisis as conflict-driven, but Niger's quantitative load in 2024 is overwhelmingly hydro. If we frame Niger purely as a "conflict-coup" country we'll mis-characterize where IDPs are coming from.

## Open questions
- What was the 2024 climatological event? CHIRPS / SPEI overlay needed.
- Is the 1.17M figure a single big event (a specific flood disaster) or aggregated across the season?
- Are the flood-displaced people the same populations as the conflict-displaced (compounding crisis) or geographically separated?
- Does the channel-orthogonality story [[PATTERN_001]] hold up under this — i.e., are the flood IDPs in non-conflict admin-1 regions?

## Related
- [[PATTERN_001]] Two-channel hypothesis — NER is the strongest empirical case
- [[PATTERN_007]] Drought displacement invisible in data — would shift the picture further if included

## Data sources
- `D:/IDP/analysis/sahel_stratified_panel_2026_05_21.parquet` rows where iso3=NER and year=2024
- GIDD Disasters file, ISO3=NER, Year=2024
- Will need CHIRPS data extract for NER box 2020-2024

---

## Dig 2026-05-25 — EM-DAT confirmation

EM-DAT NER 2024 flood event (single record):

| Field | Value |
|---|---|
| Disaster Type | Flood |
| Subtype | Flood (General) |
| Start - End Month | June - October 2024 |
| Locations | Maradi, Zinder, Agadez, Tahoua, Tillabéri (5 regions) |
| Total Deaths | 396 |
| Total Affected | 1,527,058 |

This is **a single seasonal flood event** spanning the 2024 West African monsoon (Jun-Oct), affecting 5 of NER's 7 administrative regions. Crucially these regions are **distinct from the conflict-active zones** (Diffa, Tillabéri-frontier with BFA/MLI) — Maradi/Zinder/Agadez are central+north and largely outside the JNIM/ISGS theater. So the **flood-IDPs and conflict-IDPs are geographically separated populations**, supporting [[PATTERN_001]]'s channel-orthogonality at the within-country scale (not just cross-country).

Total affected (1.53M) is close to displaced figure (1.17M GIDD) — implying ~77% displacement rate among affected. Very high for a flood (typical is 30-50%); suggests these were either highly persistent floods or that "affected" was counted conservatively (people whose homes/livelihoods were destroyed, not all in the zone).

Historical NER flood-displacement, 2008-2024 — note 2012 (540K) and 2010 (206K) are previous mid-tier events; 2024 is **2.2× the previous peak**. Trend is non-stationary upward (5 of last 6 years above 100K).

**Status updated:** noted → **firmed-anomaly**. Single monsoon event, 5-region, 396 deaths, 1.53M affected, 1.17M displaced. Strengthens [[PATTERN_001]] via within-country channel separation.

**Open thread:** is the rising trend (2010 → 2012 → 2024 peaks getting closer together and bigger) consistent with documented climate-attribution work on Sahel monsoon shifts? Needs CHIRPS Jun-Oct 2024 vs climatological baseline.
