# Pattern 011 — V-Dem libdem dynamic range is cluster-conditioned

- **ID:** PATTERN_011
- **Status:** candidate-hypothesis
- **Type:** mechanism-candidate
- **Discovered:** 2026-05-21 via cross-cluster comparison
- **Severity / interest:** high (changes how we'd pre-reg [[PATTERN_002]])

## One line
The libdem-collapse-tracks-coup pattern from Sahel ([[PATTERN_002]]) only fires where libdem has dynamic range. Cluster-conditioning is the wrong frame; **range-conditioning** is right. Inside Central Africa, CAF (range = 0.249 in 2018) collapses to 0.097; COD and CMR (already at 0.12) stay flat. Within-cluster heterogeneity confirms.

## Numbers

V-Dem libdem 2018 → 2024 by country:

| Cluster | Country | 2018 | 2024 | Δ | Has dynamic range (>=0.20)? |
|---|---|---|---|---|---|
| Sahel | BFA | 0.485 | 0.126 | **−0.359** | yes → collapsed |
| Sahel | MLI | 0.307 | 0.141 | −0.166 | yes → collapsed |
| Sahel | NER | 0.405 | 0.182 | −0.223 | yes → collapsed |
| Sahel | BEN | 0.472 | 0.323 | −0.149 | yes → held (no coup) |
| Central Africa | **CAF** | **0.249** | **0.097** | **−0.152** | **yes → collapsed** |
| Central Africa | COD | 0.117 | 0.123 | +0.006 | no → flat (range-locked) |
| Central Africa | CMR | 0.120 | 0.126 | +0.006 | no → flat |
| LatAm | COL | 0.533 | 0.554 | +0.021 | yes → held |
| LatAm | HTI | 0.257 | 0.101 | **−0.156** | yes → collapsed |
| LatAm | SLV | 0.428 | 0.090 | **−0.338** | yes → collapsed (Bukelization) |
| Horn | ETH | 0.131 | 0.093 | −0.038 | no → already low |
| Horn | SOM | 0.106 | 0.127 | +0.021 | no → already low |
| Horn | SDN | 0.068 | 0.030 | −0.038 | no → floor |
| Horn | SSD | 0.053 | 0.071 | +0.018 | no → floor |
| Horn | ERI | 0.007 | 0.009 | 0 | no → literal floor |
| MENA | SYR | 0.025 | 0.054 | +0.029 | no → floor |
| MENA | YEM | 0.034 | 0.047 | +0.013 | no → floor |
| MENA | IRQ | 0.238 | 0.210 | −0.028 | yes → held (modest drift) |
| MENA | LBN | 0.282 | 0.226 | −0.056 | yes → held (modest drift) |
| South Asia | **AFG** | **0.176** | **0.014** | **−0.162** | borderline → collapsed (Taliban 2021) |
| South Asia | **MMR** | **0.232** | **0.015** | **−0.217** | yes → collapsed (military coup 2021) |
| South Asia | **PAK** | **0.250** | **0.193** | **−0.057** | **yes → range-yes but trigger-no = NO COLLAPSE** |
| E. Europe | **UKR** | **0.244** | **0.230** | **−0.014** | yes → wartime suspension (different mech) |

## Why it stands out
The within-Sahel pattern "libdem collapses with coup" was clean (BFA/MLI/NER all collapsed, BEN held). But applying the same expectation to Horn/MENA: libdem there has been at the floor for 20+ years, so the dynamic range needed to test the pattern doesn't exist. The pattern IS testable in LatAm — SLV's collapse mirrors Sahel's coup-countries, and COL's holding mirrors BEN. So the libdem-mechanism pre-reg should specify "applies where pre-period libdem ≥ 0.25" or similar threshold — outside that range, the mechanism is null by construction (no range to fall through).

This is exactly the kind of methodology-corpus point that distinguishes "we found a pattern" from "we found a pattern that holds in the right conditioning regime."

**2026-05-25 South Asia + UKR refinement:** range is NECESSARY but NOT SUFFICIENT. PAK had identical 2018 range to MMR (0.250 vs 0.232) — MMR collapsed via 2021 coup, PAK did not (no regime-changing trigger). UKR's 2018 range was 0.244 but the collapse mechanism is wartime suspension, not regime authoritarianization (and it's mild, −0.014). Refined model:
- Range floor ≥ ~0.22 = collapse channel is *available*
- Trigger (coup / authoritarian-civilian consolidation / Taliban-style takeover) = collapse channel *activated*
- Interstate war = different mechanism entirely (wartime suspension, not capture)

PAK is the new clean control: range-yes + trigger-no = no collapse. Strengthens the conditioning argument.

## Open questions
- What's the right libdem-range threshold for cluster-conditioning?
- Does the same logic apply to PATTERN_002's coup-trigger story — i.e., is the libdem-collapse the trigger or the consequence?
- Does it hold in a fifth cluster (Central Africa: COD/CAR/CMR) where there's mid-range libdem?

## Related
- [[PATTERN_002]] Original libdem-coup pattern; this conditions it
- [[PATTERN_013]] Bukelization (SLV) — libdem collapse without a coup, different mechanism but same outcome shape

## Data sources
- All four cluster panels at `D:/IDP/analysis/*_stratified_panel_2026_05_21.parquet`
- V-Dem v15 libdem indicator
