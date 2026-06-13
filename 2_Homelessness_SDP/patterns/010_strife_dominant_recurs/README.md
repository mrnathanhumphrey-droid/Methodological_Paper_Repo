# Pattern 010 — Strife-dominant violence pattern recurs across clusters

- **ID:** PATTERN_010
- **Status:** candidate-hypothesis
- **Type:** mechanism-candidate
- **Discovered:** 2026-05-21 via cross-cluster comparison
- **Severity / interest:** high

## One line
Non-state communal violence dominates in at least four countries across four different regional clusters: MLI (Sahel: 30% strife), SSD (Horn: strife 2742 / war 302 — strife DOMINATES), HTI (LatAm: gang violence as strife + one-sided), **CAF (Central Africa: early-period strife 3,219 vs war 432 = 7.5× ratio).** The cross-cluster cross-continent pooling firms up.

## Numbers

| Country | Cluster | Period | War fatal | Strife fatal | Strife/War ratio |
|---|---|---|---|---|---|
| MLI | Sahel | acute | 4,995 | 2,197 | 0.44 |
| **SSD** | **Horn** | acute | **302** | **2,742** | **9.1** |
| HTI | LatAm | acute | 193 | 422 | 2.2 |
| **CAF** | **Central Africa** | **early** | **432** | **3,219** | **7.5** |
| SDN | Horn | acute | 10,166 | 3,322 | 0.33 |
| SYR | MENA | early | 207,948 | 48,531 | 0.23 |
| ETH | Horn | acute | 313,201 | 1,158 | 0.004 |
| BFA | Sahel | acute | 10,403 | 476 | 0.05 |
| IRQ | MENA | early | 45,218 | 90 | 0.002 |
| COL | LatAm | acute | 628 | 448 | 0.71 |

## Why it stands out
The peer countries in each cluster (BFA, SDN, IRQ) are dominated by state-based armed conflict — government fighting organized rebel groups. But MLI, SSD, and HTI show the opposite: NON-state communal violence is the main fatality driver. South Sudan especially: 9× more communal-violence fatalities than war-fatalities. These countries also have meaningful displacement, but the mechanism is different from a JNIM/ISGS or state-army-vs-rebels picture. If we model displacement with country fixed effects, we'd miss that MLI / SSD / HTI behave more like each other (across continents) than like their cluster peers.

This is the cleanest cross-cluster pooling-finding so far: a residue class that ignores geography.

## Open questions
- Are the strife-dominant countries also weaker-state countries? (V-Dem rule_of_law check)
- Do strife-dominant countries have higher displacement-per-fatality ratios (because communal violence drives displacement more efficiently per fatality than state-based war)?
- Is the mechanism the same — inter-ethnic / inter-communal — or does the LatAm gang-violence version operate differently from African inter-pastoralist conflict?

## Related
- [[PATTERN_005]] Original MLI strife observation; this generalizes it cross-cluster
- [[PATTERN_001]] Adds a "strife" sub-channel to conflict in the channel taxonomy

## Data sources
- `D:/IDP/analysis/{sahel,horn_of_africa,middle_east,latin_america}_stratified_panel_2026_05_21.parquet`
- UCDP-GED type_of_violence stratification across 4 clusters
