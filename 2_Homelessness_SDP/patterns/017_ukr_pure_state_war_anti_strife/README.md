# Pattern 017 — UKR is the pure-interstate-war signature, anti-PATTERN_010

- **ID:** PATTERN_017
- **Status:** candidate-hypothesis (contrast)
- **Type:** mechanism (boundary case)
- **Discovered:** 2026-05-25 via Eastern Europe cluster build
- **Severity / interest:** high (defines the boundary of the framework)

## One line
UKR acute 2020-2024 = **17.89M conflict-displacement / 235K war fatalities / 0 strife fatalities / 5.4K disaster**. Pure state-based interstate war. The polar opposite of [[PATTERN_010]] (strife-dominant) and a near-degenerate case of [[PATTERN_001]] (only 1 channel fires meaningfully).

## Numbers

UKR acute period (2020-2024):

| Metric | Value | Comparator |
|---|---|---|
| Conflict-displacement | 17,890,114 | DRC 18.0M (full panel) |
| Disaster-displacement | 5,361 | PAK 9.97M, NER 1.92M |
| War (state-based) fatalities | **235,068** | next: ETH 313K (Tigray, but mixed); SDN 50K+ |
| Strife (non-state) fatalities | **0** | MLI 2,144; SSD 2,866; HTI 2,000+; CAF 1,500+ |
| One-sided (civilian) fatalities | 1,460 | DRC 14,322 |
| Displacement / fatality ratio | ~76 | DRC 783; BFA 263; SYR ~50 |

V-Dem libdem trajectory:
- 2018: 0.244
- 2020: 0.325 (peak — Maidan/EU-accession reforms)
- 2024: 0.230 (wartime suspension, martial law, no elections)

## Why it stands out
1. **Pure conflict-type signature**: strife = 0 is a structural finding. Russia-Ukraine isn't an insurgency with civilian-targeting irregulars dominating; it's two state militaries. The corpus's strife channel collapses to zero by mechanism, not by under-reporting.
2. **Low displacement-per-fatality**: 76 is at the bottom of the corpus. Interstate war with organized evacuation, NATO/EU border corridors, and external host capacity converts fatalities to displacement at a lower rate than civilian-targeted irregular conflict. (Contrast DRC's 783: civilians fleeing communal attacks displace at high ratios with low body counts; UKR's military deaths don't directly drive evacuation of those same units.)
3. **Different libdem trajectory**: UKR libdem went UP (2018→2020) then DOWN (2020→2024). Not the collapse-from-range shape of [[PATTERN_011]]. Wartime suspension is a distinct mechanism — elections postponed, mobilization, martial law — not authoritarian capture from within.
4. **3-channel hypothesis ([[PATTERN_001]]) breaks**: UKR is 1-channel. Flood/drought/disaster channels are present at <0.03% of conflict channel. Either the 3-channel framework is wrong, or it's conditioned on conflict-type-not-being-interstate-war.

## Boundary lesson for the framework
The corpus framework's patterns (strife-dominant, range-conditioning, 3-channel) emerged from civil-conflict and fragility contexts. UKR shows the framework has a **conflict-type boundary**: interstate war is a different generative process, and patterns don't auto-apply. This is methodologically useful — pre-reg should specify "civil/intrastate conflict regimes" not "all conflict-displacement."

Compare to fluid-dynamics: laminar vs turbulent flow have different governing equations. Interstate war and irregular conflict may need different displacement-mechanism models.

## Open questions
- Where else in the corpus does conflict-type matter? IRQ 2003-2011 had interstate phase + insurgency phase; can we decompose?
- Is UKR's low displacement/fatality ratio a function of conflict-type alone, or of receiving-country capacity (EU)? Compare with hypothetical interstate war in a low-capacity region.
- Does the framework need a "conflict-type stratifier" alongside the range stratifier?

## Related
- [[PATTERN_010]] strife-dominant — UKR is the anti-case (strife=0)
- [[PATTERN_001]] 3-channel displacement — UKR breaks the multichannel assumption
- [[PATTERN_011]] range-conditioning — UKR's libdem doesn't follow the collapse pattern (wartime suspension is different mech)

## Data sources
- `D:/IDP/analysis/eastern_europe_stratified_panel_2026_05_21.parquet`
- UCDP-GED for state-based vs non-state breakdown
