# Pattern 006 — Benin periphery: 350× less displaced than BFA, but fatalities climbing 0 → 147

- **ID:** PATTERN_006
- **Status:** noted
- **Type:** contrast
- **Discovered:** 2026-05-21 via `build_sahel_stratified.py` first look
- **Severity / interest:** medium

## One line
Benin sits on the southern edge of the Sahel violence; total conflict-displacement is 7,700 in 5 years (BFA: 2.7M = 350× more), but fatalities are climbing — 0 (pre) → 1 (early) → 147 (acute) — and that climb is monotonic year-by-year.

## Numbers

| Period | War fatalities | One-sided fatalities |
|---|---|---|
| pre-crisis 1998-2013 | 0 | 0 |
| early 2014-2019 | 0 | 1 |
| acute 2020-2024 | 147 | 26 |

Acute year-by-year war fatalities: 1 (2020), 11 (2021), 30 (2022), 28 (2023), **77 (2024)**.

V-Dem libdem trajectory is the *opposite* of its coup-affected neighbors: 0.472 (2018) → 0.284 (2020 dip) → 0.323 (2024 recovery). Benin did NOT have a coup.

## Why it stands out
Benin is geographically adjacent to Burkina Faso's southern conflict zones (Pendjari/W national parks region). If state-collapse-coups *cause* conflict-displacement, Benin should be the test case: no coup, no displacement. So far the data is consistent — Benin's 7,700 displacement is two orders of magnitude below its Sahel neighbors. But the slow fatality climb (especially 2024's 77 war-fatalities) is a real signal of spillover. It's still the cluster control case for now, but watching this trajectory matters.

## Open questions
- Is the fatality climb concentrated in Atacora / Alibori (the northern border departments with BFA)?
- When does Benin cross the "conflict country" threshold quantitatively? Some definitions use 25 battle-deaths/year (UCDP minimum); Benin crossed in 2022.
- Is there displacement that isn't being captured at the country level — internal Beninois movement from Atacora southward?

## Related
- [[PATTERN_002]] Benin = the no-coup control for the libdem-coup pattern
- [[PATTERN_003]] BFA is the upstream source of the spillover into Benin

## Data sources
- `D:/IDP/analysis/sahel_stratified_panel_2026_05_21.parquet` rows where iso3=BEN
- UCDP-GED filtered for country=Benin

---

## Dig 2026-05-25 — confirmed: northern departments + state-only-actor + BFA-Est mirror

**BEN UCDP profile (1998-2024):**
- Total events: 65 (all post-2019)
- **ZERO non-state-strife events** — Benin's entire UCDP record is state-based (gov-vs-JNIM) or one-sided
- Modern annual fatality climb: 2019 (1) → 2020 (1) → 2021 (11) → 2022 (30) → 2023 (46) → **2024 (85)** — perfectly monotonic, ~doubling per year

**BEN acute (2020-2024) admin-1 fatalities:**

| Department | Fatalities | % |
|---|---|---|
| **Alibori** | **102** | 59% |
| **Atacora** | **71** | 41% |
| (all other departments) | 0 | 0% |

**100% of BEN's conflict fatalities concentrated in the two northernmost departments** (Alibori + Atacora = the BFA border + Pendjari/W national parks region). The southern half of Benin is completely conflict-free in UCDP.

**Actor side_a (acute):** Government of Benin (147) vs JNIM (26). **Benin is doing counterinsurgency operations against JNIM**, which has crossed the border. Government is dominant initiator (same shape as BFA: state vs jihadist).

**Latitude band distribution of acute events:**

| Band | Events | Fatalities |
|---|---|---|
| mid (lat 9-11) | 15 | 32 |
| north_central (lat 11-11.5) | 23 | 66 |
| north_BF_border (lat 11.5-12.5) | 26 | 75 |

Spread across the entire northern half of Benin, with slight concentration at the BF border. Not just immediately at the border — there's southward bleed into the mid-latitudes already.

**Cross-border mirror — BFA Est region (directly adjacent to BEN's Alibori/Atacora):**

| Year | BFA Est events | BFA Est fatalities |
|---|---|---|
| 2018 | 6 | 23 |
| 2019 | 12 | 30 |
| 2020 | 18 | 40 |
| 2021 | 26 | 118 |
| 2022 | 30 | 339 |
| 2023 | 93 | **1,030** |
| 2024 | 64 | **1,476** |

**BFA Est region fatalities exploded 64× from 2018 to 2024.** This is the upstream pressure cooker. BFA Est is in collapse; Benin's northern departments are the downstream catchment for both fighters crossing and populations fleeing. BEN's monotonic climb (85 in 2024) is consistent with ~1-2 year lag from BFA Est's 2022 → 2023 jump.

**Status updated:** noted (contrast) → **firmed-contrast + active-spillover** (no longer a "control case"; Benin is in the early stages of becoming a conflict country).

**The trajectory question:** Benin crossed UCDP's 25-battle-deaths-per-year minor-armed-conflict threshold in **2022** (30 fatalities). 2023 was 46, 2024 was 85. At current doubling rate Benin will be at ~170 in 2025, ~340 in 2026 — comparable to NER's mid-2020s scale. **Watch Alibori + Atacora displacement figures going forward; GIDD may show step-change before UCDP fatalities catch up.**

**Implications for the corpus framework:**
- The "BEN = no-coup control for [[PATTERN_002]]" framing still holds for libdem-collapse (BEN didn't collapse), but BEN is no longer a clean control on conflict-displacement
- BEN proves spillover can occur in stable-libdem countries without coups — separates the libdem collapse mechanism from the conflict-spillover mechanism, which is methodologically useful

**Cross-link:** This strengthens the **meta-pattern of conflict-types** (see INDEX): BEN is becoming a "fragility-spillover state-counterinsurgency" type, distinct from the formal-army-war and predator-militia types.
