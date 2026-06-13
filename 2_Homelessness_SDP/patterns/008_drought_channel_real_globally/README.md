# Pattern 008 — Drought-displacement is real globally; the "invisible drought" finding was Sahel-specific

- **ID:** PATTERN_008
- **Status:** noted
- **Type:** data-quality-flag (revises [[PATTERN_007]])
- **Discovered:** 2026-05-21 via Horn of Africa cross-cluster comparison
- **Severity / interest:** high (it changes the channel taxonomy)

## One line
GIDD captures drought-displacement massively for Somalia (1.66M acute) and Ethiopia (840K acute) — the channel is real, the IDMC methodology does pick it up, just not for Sahel countries.

## Numbers

GIDD disaster_drought, acute 2020-2024:

| Cluster | Country | Drought-displaced |
|---|---|---|
| Sahel | all 4 | 0 |
| Horn | SOM | **1,659,627** |
| Horn | ETH | **840,590** |
| Horn | SSD | 2,600 |
| Horn | SDN | 0 |
| MENA | IRQ | 129,200 |
| MENA | YEM | 30 |
| LatAm | COL | 7,864 |

## Why it stands out
Revises [[PATTERN_007]] substantially. Drought-displacement is captured by IDMC when there's a documented displacement event attributable to drought conditions (e.g., the 2022 SOM drought-displacement crisis). The Sahel countries don't have this captured probably because: (a) drought displacement is more diffuse / less attributed to specific events; (b) IOM DTM in the Sahel hasn't been instrumented for slow-onset displacement to the degree it has in the Horn; (c) Sahel drought displacement may be routed through "food insecurity" reporting via IPC rather than IDMC events.

## Open questions
- Why specifically is the Sahel data drought-blind? Is it methodology, infrastructure, or actual absence?
- Do FEWS NET / IPC shapefiles for Sahel show drought-displacement that GIDD misses?
- If we add a "drought channel" via IPC pop-in-crisis-3+ as a proxy, does the Sahel picture change?

## Related
- [[PATTERN_001]] Becomes three-channel (conflict / flood / drought) given Horn data
- [[PATTERN_007]] Downgraded: the gap is Sahel-specific, not global

## Data sources
- `D:/IDP/analysis/horn_of_africa_stratified_panel_2026_05_21.parquet`
- GIDD Disasters file with Hazard Type = "Drought"
