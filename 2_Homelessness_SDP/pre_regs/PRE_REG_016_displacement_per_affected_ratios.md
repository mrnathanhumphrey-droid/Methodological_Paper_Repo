# Pre-Registration 016 — Displacement-per-Affected Ratios by Regime

**ID:** PRE_REG_016
**Locked:** 2026-05-25
**Substrate:** PATTERN_019 (6-regime typology) + EM-DAT affected counts
**Status:** LOCKED — predictions and falsifiers pre-committed; first fit fires on existing GIDD + EM-DAT data

---

## 1. Hypothesis

**H1 (mechanism-distinct ratios):** The ratio of internal-displacement to total-affected differs systematically by hazard-type because the physical mechanism of damage differs:

- **Earthquakes**: building collapse / structural damage → immediate, permanent displacement → HIGH ratio (≥ 30%)
- **Floods**: water inundation → temporary displacement → MEDIUM ratio (10-25%)
- **Storms/Cyclones**: variable — depends on wind damage (high displacement) vs storm surge / rain (medium) → MEDIUM ratio (10-30%)

**H2 (state-capacity moderation):** Within Regime 3 (storm-dominant) and Regime 6 (EQ-dominant), high-capacity states show LOWER displacement-per-affected than low-capacity states because evacuation infrastructure + construction codes reduce per-affected displacement.

- USA (Regime 3) < PHL (Regime 3) for storm-driven events
- JPN (Regime 4 / mixed but high EQ exposure) < HTI (Regime 6) for EQ-driven events
- ITA (Regime 6) < NPL (Regime 6) for EQ-driven events

**H3 (Regime 1 anomaly):** Bimodal-mega-flood (PAK) shows HIGHER ratio than steady-high-flood (IND) because mega-events outstrip evacuation capacity and produce surge-displacement.

---

## 2. In-sample reference (not formally tested)

Known anchor cases (qualitative):
- HTI 2010 EQ: ~1.5M displaced / ~3M affected ≈ 50% (high)
- PAK 2022 flood: ~8M displaced / ~33M affected ≈ 24% (medium-high — mega-flood)
- USA Helene+Milton 2024: ~10.24M displaced / unclear affected baseline (likely 15-30M affected) ≈ 35-65%

---

## 3. Pre-locked predictions

### Prediction set A — Hazard-type ratios (cross-country medians)

For each hazard type with sufficient events (n ≥ 20 country-event observations), compute median (IDP / total-affected) ratio using EM-DAT for affected and GIDD for IDP, joined on Country × Year × Hazard.

**Predicted medians**:
- Earthquake: ≥ 30% (95% CI lower bound > 20%)
- Flood: 10-25%
- Storm: 10-30%
- Drought: < 5% (very low — long onset, less displacement per affected)
- Mass movement: variable; not formally predicted

### Prediction set B — Regime-by-regime ratios

For each confirmed regime member (22 countries from PATTERN_019/020/025), compute country-level displacement-per-affected:

| Regime | Predicted ratio (median) | Reasoning |
|---|---|---|
| 1 (Bimodal-mega-flood: PAK) | 20-30% | Mega-flood overwhelms evacuation |
| 2 (Steady-high-flood: IND) | 8-15% | Annual baseline, adapted |
| 3 (Storm-dominant) | 15-25% | Cyclone-belt; variable state capacity |
| 3a (USA, CUB) | 10-20% | Bimodal mega-storm with state capacity (USA) or extensive evacuation (CUB) |
| 3b (PHL) | 20-30% | Chronic exposure but high per-event displacement |
| 4 (Mixed) | 10-20% | Average of constituent channels |
| 6 (EQ-dominant) | 30-50% | EQ building-collapse mechanism |

### Prediction set C — State-capacity moderation

Compare displacement-per-affected within Regime 3 + Regime 6:
- USA (Regime 3, high-capacity) < PHL (Regime 3, mid-capacity) — predicted difference ≥ 10 pp
- ITA (Regime 6, high-capacity) < NPL (Regime 6, low-capacity) — predicted difference ≥ 10 pp
- JPN (Regime 4, mixed but high EQ exposure & capacity) < HTI (Regime 6, low-capacity) — predicted difference ≥ 15 pp

---

## 4. Falsifiers

- **F1**: Earthquake median ratio < 20% → EQ-specific mechanism wrong (building-collapse logic fails empirically)
- **F2**: Storm median > Flood median by more than 15pp OR Flood median > Storm median by more than 15pp → channels indistinguishable
- **F3**: State-capacity contrast (H2) does NOT show predicted direction in ≥ 2 of 3 contrasts (USA-PHL, ITA-NPL, JPN-HTI) → state-capacity moderation walked back
- **F4**: Regime-by-regime ratios don't separate (all regimes within 10pp of each other) → ratios not mechanism-distinct; ratios are noise

F1 firing alone = H1 walked back.
F3 firing alone = H2 walked back; H1 may still hold.
F2 + F4 firing = ratios are not mechanism-distinct, regimes are not separable by ratio.

---

## 5. Methodology

- **GIDD**: Disaster Internal Displacements 2008-2024, joined on ISO3 × Year × Hazard Type
- **EM-DAT**: Total Affected, joined on ISO × Start Year × Disaster Type
- **Join**: country-year-hazard. Drop rows where either side is null.
- **Ratio**: GIDD_IDP / EMDAT_total_affected. Reject ratios > 1 (data error) or = 0 (data error).
- **Aggregate**: median per country, per hazard, per regime.
- **Sufficient-evidence threshold**: n ≥ 20 country-event observations per hazard type for H1; n ≥ 3 per country for H3.

### State-capacity proxy
Use World Bank GDP-per-capita 2020 as state-capacity proxy. Pre-locked thresholds:
- High-capacity: GDP/capita > $25,000 (USA, ITA, JPN)
- Mid-capacity: GDP/capita $5,000-25,000 (CUB, MEX, BRA, TUR, CHL)
- Low-capacity: GDP/capita < $5,000 (PHL, HTI, NPL, IND, PAK, IDN, BGD, ECU, MOZ, VNM, FJI, VUT)

---

## 6. Cross-references
- PATTERN_019 / 020 / 025 (parent typology)
- PRE_REG_003 (regime classification anchor)
- PRE_REG_013 (within-regime sub-typing; runs in parallel)

---

## 7. Provenance
Locked 2026-05-25 before Phase 1 P2-I test fires.

---

## 8. Results — first fit (fired 2026-05-25)

Pre-reg fired immediately after lock. Dig: `D:/IDP/papers/PAPER_2_DISASTER_REGIMES/digs/2026_05_25_P2_I_displacement_per_affected_ratios.md`. Data: GIDD + EM-DAT joined on ISO3 × Year × Hazard (1,680 records).

### Prediction set A — Hazard-type ratios
| Hazard | N | Median % | Predicted | Verdict |
|---|---|---|---|---|
| Earthquake | 166 | **33.6** | ≥30% | ✓ matches |
| Flood | 921 | **31.5** | 10-25% | ABOVE band |
| Storm | 396 | **28.8** | 10-30% | ✓ matches |
| Drought | 22 | **1.3** | <5% | ✓ matches |

**F1 (EQ < 20%)**: NOT FIRED ✓
**F2 (|Storm − Flood| > 15pp)**: NOT FIRED (diff = 2.7pp) ✓

H1 supported qualitatively (EQ ≥ flood ≥ storm >> drought), but flood ratio band was too narrow — floods drive higher displacement than predicted.

### Prediction set B — Regime-by-regime ratios
| Regime | N | Median % | Predicted | Verdict |
|---|---|---|---|---|
| 1 (PAK) | 25 | 30.5 | 20-30% | ✓ |
| 2 (IND) | 35 | **45.1** | 8-15% | WAY ABOVE — predicted PAK > IND, **FALSIFIED** (IND > PAK) |
| 3 (mixed) | 85 | 26.5 | 15-25% | close ✓ |
| **3a** | 33 | **85.1** | 10-20% | WAY ABOVE — predicted 3b > 3a, **FALSIFIED** (3a >> 3b) |
| 3b (PHL) | 53 | 37.1 | 20-30% | above |
| 4 | 169 | 27.3 | 10-20% | above |
| 6 | 108 | 31.0 | 30-50% | ✓ |

**F4 (regimes within 10pp)**: NOT FIRED (spread = 58.6pp) ✓ — regimes ARE ratio-separable.

### Prediction set C — State-capacity moderation
| Contrast | High | Low | Predicted | Actual | Meets threshold? |
|---|---|---|---|---|---|
| Regime 3 Storm USA vs PHL | 33.5% | 37.1% | USA < PHL | +3.6pp ✓ dir | NO (need ≥10pp) |
| Regime 6 EQ ITA vs NPL | 97.2% | 29.9% | ITA < NPL | −67.3pp INVERTED | NO |
| Mixed EQ JPN vs HTI | 37.8% | 31.3% | JPN < HTI | −6.5pp INVERTED | NO |

**F3 (< 2 of 3 meet)**: **FIRED → H2 WALKED BACK**

### Falsifier summary
| Falsifier | Fired? |
|---|---|
| F1 (EQ < 20%) | NO |
| F2 (Storm-Flood > 15pp diff) | NO |
| F3 (state-capacity contrasts < 2/3) | **YES** |
| F4 (regimes within 10pp) | NO |

### Net result
- **H1 supported** qualitatively; specific flood band prediction wrong
- **H2 walked back** — state capacity does not moderate displacement-per-affected as predicted
- **H3 (PAK > IND, 3a < 3b) falsified** — both directional predictions inverted in data
- **New post-hoc finding**: Regime 3a (85%) >>> Regime 3b (37%) — bimodal mega-storms drive HIGHER displacement-per-affected than perpetual storms. Mechanism candidate: forced-evacuation counting vs in-place-shelter populations
- **Reporting heterogeneity** is the dominant signal — EM-DAT "affected" definitions vary by country, confounding state-capacity tests

**Refined claim for Paper 2**: hazard-types separate qualitatively; regimes are ratio-separable; state-capacity-moderation drops out as a claim; new 3a-vs-3b reporting hypothesis added (needs forward pre-reg if to be formally tested).

**Status**: PARTIAL SUPPORT + 1 WALK-BACK (H2) + 1 FALSIFICATION (H3 directional) + 1 NEW POST-HOC FINDING (3a >> 3b).
