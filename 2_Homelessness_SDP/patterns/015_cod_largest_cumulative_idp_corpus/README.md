# Pattern 015 — DRC (COD) is the world's largest cumulative conflict-displacement panel

- **ID:** PATTERN_015
- **Status:** noted
- **Type:** anomaly
- **Discovered:** 2026-05-21 via Central Africa cluster build
- **Severity / interest:** high

## One line
DRC cumulative conflict-displacement across our panel (1998-2024): ~29.8 million displacement events. The 2020-2024 acute period alone is 18.0M — larger than any other country's full-panel total.

## Numbers

COD conflict-displacement by period:

| Period | Conflict-displaced |
|---|---|
| pre_crisis 1998-2013 | 3,568,000 |
| early 2014-2019 | 8,224,000 |
| **acute 2020-2024** | **18,030,000** |
| **Cumulative** | **~29,822,000** |

Comparators (acute period, cumulative):
- ETH 10.0M
- SDN 10.7M
- SYR 3.4M
- BFA 2.7M
- COD 18.0M

COD acute fatalities by violence type:
- war_state_based: 5,957
- strife_non_state: 2,764
- one_sided_civilians: **14,322** (massive attacks-on-civilians signal)

## Why it stands out
COD's displacement scale is essentially unique in our corpus — it's an order of magnitude beyond most other countries. The one_sided_civilians fatality count (14,322 acute) suggests that DRC's conflict isn't dominated by inter-army battle deaths but by attacks on civilian populations — M23, ADF, CODECO, Mai-Mai factions targeting civilians. Displacement-per-fatality ratio for DRC is exceptionally high (18M displaced / 23K fatalities ≈ 783 displaced per fatality, vs BFA's 263 or SYR's ~50 over civil war years).

This also means COD's libdem stability (around 0.12 throughout) is *not* a story of "stable governance"; it's a story of *consistently failed governance with continuing violence*. The libdem-stable / displacement-massive combination is exactly the floor-saturated case in [[PATTERN_011]].

## Open questions
- How much of COD's displacement counting is single-individual repeated displacement events vs unique people? GIDD records events, not unique IDPs.
- Does the eastern DRC concentration (Ituri, North Kivu, South Kivu) show up as admin-1 hot-spots when we get to admin-1 panels?
- Is the 18M acute figure driven by a few catastrophic events (M23 advance 2022-23) or a steady stream?
- What's the funding-per-displaced for DRC vs ETH vs SYR? (FTS comparison)

## Related
- [[PATTERN_011]] DRC is the prime case of "floor-saturated libdem + massive scale" — the cluster-conditioning explains why libdem doesn't predict displacement here
- [[PATTERN_010]] DRC's strife level (2,764 acute) is meaningful but war + one-sided dominate; not strife-dominant per se
- [[PATTERN_001]] DRC has both massive flood (1.7M acute) and conflict (18M acute) — the channel orthogonality holds with the scale tripled

## Data sources
- `D:/IDP/analysis/central_africa_stratified_panel_2026_05_21.parquet`
- GIDD `1_Displacement_data` sheet, ISO3=COD
- UCDP-GED filtered for country=DR Congo (Zaire)

---

## Dig 2026-05-25 — actor decomp + eastern provinces confirmed

**COD acute (2020-2024) UCDP profile:**
- Events: 4,451
- Total fatalities: 23,043 (vs 18.03M displaced → ratio 783 displaced/fatality, extreme high)
- type_of_violence breakdown: state-based 5,957 / non-state 2,764 / **one-sided 14,322 (62%)**

**One-sided actor decomposition (top 15, side_a = initiator):**

| Actor | One-sided fatalities | Notes |
|---|---|---|
| **IS** (Islamic State Central Africa Province) | **7,731** | Successor to ADF; eastern DRC + Uganda border |
| **URDPC** | 2,576 | Union des Révolutionnaires pour la Défense du Peuple Congolais (Mai-Mai variant) |
| Government of DR Congo (Zaire) | 820 | Often Wazalendo-affiliated state ops |
| Zaire self-defense group | 469 | Ituri-based ethnic militia |
| **M23** | 438 | Rwanda-backed insurgency, eastern DRC |
| FDBC | 300 | |
| AFC (Alliance Fleuve Congo) | 268 | M23-aligned coalition |
| Mobondo | 267 | Western DRC ethnic militia (Mai-Ndombe) |
| FPIC Chambre noire sanduku | 256 | Ituri militia |
| Government of Rwanda | 187 | M23 enabler |
| VDP | 125 | |
| CODECO-BTD | 100 | |
| ALC | 98 | |
| CNPSC | 81 | |
| NDC-R | 79 | |

**The dominant one-sided killer is IS/ISCAP (7,731)**, more than 3× the next group. This refines the original PATTERN_015 narrative — it's not generic "M23/ADF/CODECO/Mai-Mai targeting civilians"; it's specifically the **ADF-turned-ISCAP campaign in North Kivu/Ituri** that drives the one-sided fatality count.

**Admin-1 acute fatalities (top 10):**

| Province | Fatalities | % of acute total |
|---|---|---|
| **Nord Kivu province** | **10,244** | 44% |
| **Ituri province** | **9,093** | 39% |
| Sud Kivu province | 1,549 | 7% |
| Mai-Ndombe province | 360 | 2% |
| Tshopo province | 201 | 1% |
| Tanganyika province | 187 | 1% |
| Kinshasa province | 148 | 1% |
| Haut-Katanga province | 83 | <1% |
| Kwilu province | 75 | <1% |
| Tshuapa province | 68 | <1% |

**83% of all DRC acute fatalities concentrated in Nord Kivu + Ituri** — the eastern frontier with Uganda/Rwanda. Sud Kivu is a distant third. This is a hyper-concentrated war geographically; the rest of DRC is comparatively quiet.

**Refined narrative:** DRC's massive displacement total (18M acute) is generated by a war in 2 of 26 provinces, fought primarily through one-sided attacks by ISCAP (and to a lesser extent M23, Mai-Mai factions, government counter-ops). The 783 displaced/fatality ratio reflects: (a) civilian populations fleeing repeated attacks rather than dying in them; (b) GIDD counting displacement *events* not unique IDPs (one person displaced 5 times = 5 events); (c) the war's diffusion across rural populations (small attacks → large flight responses).

**Status updated:** noted → **firmed-anomaly + candidate-hypothesis**. The DRC profile (high one-sided + geographic concentration + extreme displacement-per-fatality) is potentially a **distinct conflict-type** alongside formal-army war (ETH/UKR) and irregular insurgency (Sahel/Horn): **predator militia campaigns against civilian populations** where displacement is the primary outcome and fatalities are secondary.

**Cross-link:** [[PATTERN_017]]'s call for a conflict-type stratifier is sharpened by this dig — DRC needs its own category alongside interstate war and irregular insurgency.
