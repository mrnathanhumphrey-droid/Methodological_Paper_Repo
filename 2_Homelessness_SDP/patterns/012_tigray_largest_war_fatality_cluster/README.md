# Pattern 012 — Tigray war is the single largest war-fatality cluster in our entire corpus

- **ID:** PATTERN_012
- **Status:** noted
- **Type:** anomaly
- **Discovered:** 2026-05-21 via Horn of Africa first-look
- **Severity / interest:** high

## One line
ETH war_state_based fatalities 2020-2024: **313,201** — the largest *single-period* war-fatality cluster in our corpus. Syria's full-civil-war total (2011-2024) is comparable at ~343,000 across three periods but no single period reaches Tigray's magnitude.

## Numbers

Acute period (2020-2024) war_state_based fatalities by country:

| Country | War fatalities |
|---|---|
| **ETH** | **313,201** |
| SOM | 13,312 |
| BFA | 10,403 |
| SDN | 10,166 |
| MLI | 4,995 |
| LBN | 4,482 |
| IRQ | 3,632 |
| NER | 2,801 |
| Others | various lower |

## Why it stands out
The Tigray war (Nov 2020 - Nov 2022) and subsequent Amhara conflict make Ethiopia by far the largest war-fatality crisis in our corpus, larger than any single conflict from MENA or West Africa. Yet international attention and humanitarian funding have not been proportional to scale (FTS data may surface this — pending Sahel-vs-Horn funding-per-fatality comparison). This isn't a "structural pattern" in the residue-class sense, but it's a magnitude finding that should constrain any "Sahel is the worst crisis" framing in our writeups.

## Open questions
- What's the funding-per-fatality ratio for ETH vs SAH vs SYR? (FTS data already on disk)
- Does the Tigray war timing (Nov 2020 - Nov 2022) match a GIDD displacement spike? (need to look at quarter-level not annual)
- How much of the 313K is concentrated in 2021 alone vs spread across the war years?

## Related
- [[PATTERN_001]] Conflict channel
- [[PATTERN_002]] ETH had a coup in 2018-2020? (Abiy's reform period collapsed into the Tigray war) — libdem trajectory in ETH

## Data sources
- `D:/IDP/analysis/horn_of_africa_stratified_panel_2026_05_21.parquet`
- UCDP-GED filtered for country=Ethiopia

---

## Dig 2026-05-25 — conflict_name + admin-1 decomp + time profile

**313K confirmed.** The 2020-2024 ETH war fatalities decompose as:

| Year | Ethiopia: Government (TPLF-Federal) | Ethiopia: Government/Amhara (Fano) | Ethiopia: Oromiya | Total |
|---|---|---|---|---|
| 2020 | 20,888 | — | 28 | **20,916** |
| 2021 | 124,269 | — | 283 | **124,552** |
| 2022 | 162,442 | — | 766 | **163,210** |
| 2023 | — | 1,218 | 464 | **1,682** |
| 2024 | 10 | 2,139 | 685 | **2,834** |

The war IS concentrated: **307,599 of 313K (98%) come from the Federal-TPLF war (2020-2022).** The 2023-2024 residual is the post-Tigray Fano (Amhara nationalist) insurgency plus the ongoing OLA (Oromia) low-level insurgency. The narrative "ETH largest war fatality cluster" is really "ETH Federal-TPLF war 2020-2022" with a much smaller continuation conflict.

**The single deadliest month:** November 2020 (war opening) — 22,917 fatalities in the Tigray admin-1 zone alone, including the Mai Kadra massacre. The war was an order of magnitude deadlier in the first month than typical wars achieve.

**Geographic spillover (Tigray admin-1 dig):** Tigray-tagged events = 51,403 total fatalities (39,604 in war window 2020-2022). The remaining ~268K war-window fatalities are coded to **Eritrea province (43K), Wollo province (13K), Amhara state (9K), Shewa province (9K)** — i.e., the war extended deep into the Federal-controlled Amhara highland and across the Eritrean front. **This is a conflict where admin-1 geography under-represents the war: UCDP's "Ethiopia: Government" dyad killed people across 6+ admin-1 zones plus Eritrea.**

**Tigray itself, monthly profile:**
- Nov 2020: 22,917 fatalities (war opening / Mai Kadra)
- Dec 2020 - Mar 2021: 1.0K-3.2K/month (early occupation phase)
- Jun 2021: 2,613 (TPLF counter-offensive)
- Aug 2022 - Nov 2022: spike again (final TPLF offensive + Federal counter, before Pretoria ceasefire Nov 2022)
- Post-Nov 2022: drops to ~1/month — ceasefire holds

**Actor side_a in Tigray admin-1:** Government of Ethiopia (45,070), Government of Eritrea (4,257), joint operations (1,713), TPLF (361). TPLF is dramatically under-represented as initiator — they were the targeted side throughout. **The war was a Federal-Eritrean joint kinetic operation against TPLF/Tigrayan forces and civilian populations, not a symmetric inter-state conflict.**

**ETH GIDD conflict-displacement matches the timing:** 2018 (2.9M, Oromia/Somali pre-Abiy-collapse) → 2019 (1.05M) → 2020 (1.69M) → **2021 (5.14M peak)** → 2022 (2.03M) → 2023 (0.79M) → 2024 (0.39M). The 5.14M displacement peak in 2021 matches the war's deadliest year. Displacement-per-fatality for ETH acute = ~32 (low end of corpus, similar to UKR; consistent with high-intensity formal-army conflict).

**Status updated:** noted → **firmed-anomaly + candidate-hypothesis**. The "single concentrated formal-army conflict produces extreme fatality density" pattern may transfer (compare UKR which also has 235K in ~3 years with similar mechanism). Possible Tier-A promotion: **conflict-type-x-intensity decomposition** as a meta-pattern (high-intensity formal-army war = high fatality / low displacement-per-fatality / spatial concentration; vs irregular conflict = lower fatality / higher displacement-per-fatality / spatial diffusion).

**Cross-link:** ETH libdem 2020 = 0.130 (already floor); the Federal-TPLF war happened in a floor-saturated libdem environment, supporting [[PATTERN_011]]'s observation that mass political violence is uncoupled from libdem trajectory in floor-locked countries.
