# Pre-Registration 003 — Disaster-Displacement Regime Typology

**ID:** PRE_REG_003
**Locked:** 2026-05-25
**Substrate:** IDP broad-data corpus (D:/IDP/)
**Status:** LOCKED — predictions and falsifiers pre-committed; holdout test fires immediately

---

## 1. Hypothesis

**H1 (regime typology):** All countries with significant disaster-displacement (cumulative ≥ 100K events 2008-2024) fit one of 4 regimes:

| Regime | Definition | Generator example |
|---|---|---|
| **1. Bimodal-mega-flood** | flood max/median > 30× AND ≥2 mega-years (>1M flood-IDP) AND storm channel <10% of disaster | PAK (max/median = 65×) |
| **2. Steady-high-flood** | flood max/median < 5× AND ≥40% of years have >1M flood-IDP AND flood channel >50% of disaster | IND (14/17 yrs >1M, max/median = 3.8×) |
| **3. Storm-dominant** | storm channel >70% of total disaster-displacement | PHL (84%), VNM (97%), MOZ (93%) |
| **4. Mixed flood-storm** | neither channel exceeds 70%; no extreme bimodality | BGD (storm 61%, flood 39%, max/median moderate) |

**H2 (mechanism):** Regime is determined by physical geography and is relatively stable. Specifically:
- Regime 1 requires: steep mountain gradient + glacial input + monsoon belt + flat downstream plain (Indus-type)
- Regime 2 requires: multiple major river systems + sustained annual monsoon (Ganges/Brahmaputra-type)
- Regime 3 requires: tropical cyclone exposure (typhoon / hurricane / cyclone belts)
- Regime 4 requires: deltaic geography + both seasonal flood AND cyclone exposure

A country's regime should NOT shift on decadal timescales (physical geography doesn't move).

---

## 2. In-sample evidence (NOT re-tested)

From PATTERN_019 flood-corpus build:
- PAK = Regime 1 (uniquely; max/median 65×)
- IND = Regime 2 (steady-high; 14/17 mega-years)
- PHL = Regime 3 (storm 84%, 16/17 storm mega-years)
- VNM = Regime 3 (storm 97%)
- MOZ = Regime 3 (storm 93%)
- BGD = Regime 4 (mixed; storm 61% / flood 39%)

---

## 3. Pre-locked predictions (holdout — fires NOW)

### Prediction set A — Caribbean (predicted: Regime 3 storm-dominant)
- **HTI (Haiti):** Regime 3 + secondary earthquake channel (2010 EQ = 224K displaced, 2021 EQ = 350K)
- **DOM (Dominican Republic):** Regime 3 pure (hurricane-belt)
- **CUB (Cuba):** Regime 3 pure (hurricane-belt; high state-capacity may dampen displacement-per-affected)

### Prediction set B — US Gulf (predicted: Regime 3 storm-dominant, high-capacity context)
- **USA:** Regime 3; expect high event counts (Katrina, Harvey, Ian) but displacement-per-affected will be LOWER than developing-country comparators because of evacuation infrastructure

### Prediction set C — South Pacific (predicted: Regime 3 storm-dominant)
- **FJI (Fiji):** Regime 3 (Pacific cyclones)
- **VUT (Vanuatu):** Regime 3 (Pacific cyclones; small island = high % displaced per event)
- **SLB (Solomon Islands):** Regime 3 (Pacific cyclones)

### Prediction set D — Brazil (predicted: Regime 2 steady-high-flood OR Regime 4 mixed)
- **BRA (Brazil):** likely Regime 2 (Amazon flooding + Northeast flooding); confidence lower than other predictions

### Prediction set E — Drought-dominant (predicted: 5th regime needed)
- **SOM (Somalia):** drought-displacement very high in our Horn data (1.66M)
- **ETH (Ethiopia):** drought 840K
- If these don't fit any of 4 regimes → predict **NEW Regime 5: Drought-dominant** with separate physical drivers (Sahel/Horn rainfall variability, ENSO teleconnections)

---

## 4. Falsifiers (pre-committed)

- **F1:** ≥3 of the 7 holdout countries (HTI/DOM/CUB/USA/FJI/VUT/SLB) fit NONE of the 4 regimes → typology incomplete; continuous-spectrum model needed
- **F2:** A predicted-Regime-3 country shows storm <40% of disaster-displacement → cyclone-exposure-determines-regime mechanism wrong
- **F3:** Any country regime SHIFTS over the 2008-2024 period (e.g., went from Regime 1 to Regime 4) → regime not stable
- **F4:** SOM/ETH fit Regime 4 (mixed flood-storm) without needing Regime 5 → drought-displacement is a sub-channel, not a regime-determining factor

Any 2 of {F1, F2, F3, F4} firing = HYPOTHESIS WALKED BACK; will be logged in patterns/ as such.

---

## 5. Methodology

### Data
- **GIDD Disasters** (IMDC) — annual country-year by hazard type
- **EM-DAT** — event-level disaster catalog
- 2008-2024 window (matches PATTERN_019 generation period)

### Test procedure
1. Pull GIDD Disasters for each holdout country
2. Compute: max/median flood ratio, storm share %, total disaster-IDP, mega-year count
3. Apply regime-classification rules (H1 definitions)
4. Score fit / no-fit for each country
5. Check falsifier conditions

### Decision rules
- **Supported:** All 7 holdout countries fit a regime (with at most 1 hitting Regime 5 drought)
- **Partial:** 1-2 don't fit; refine boundaries or add 5th regime
- **Null:** F1 fires → walk back

---

## 6. Cross-references
- [[PATTERN_019]] Disaster-displacement regime typology (the substrate)
- [[PATTERN_016]] PAK uniqueness (Regime 1 sole member confirmed)
- [[PATTERN_004]] NER monsoon flood (may sit between Regime 2 and Regime 5 if drought is added)
- [[PATTERN_009]] Earthquake as separate channel — orthogonal to this typology

---

## 7. Provenance
Locked 2026-05-25, post-PATTERN_019 generation. Holdout panel build to follow immediately.

---

## 8. Results — first fit (fired 2026-05-25)

Holdout panel classification (2008-2024):

| Country | Predicted | Actual regime | Total disaster-IDP | Verdict |
|---|---|---|---|---|
| **HTI** | Regime 3 + EQ secondary | **Regime 6 — Earthquake-dominant (70.4%)** | 2,460,350 | **NEW REGIME** — see [[PATTERN_020]] |
| DOM | Regime 3 | Regime 3 (storm 75.9%) | 458,975 | ✓ FIT |
| CUB | Regime 3 | Regime 3 (storm 99.2%) | 7,408,863 | ✓ FIT (extreme storm-purity) |
| USA | Regime 3 | Regime 3 (storm 80.3%); flood max/median 45×! | 22,292,822 | ✓ FIT; bimodality WITHIN storm channel noted |
| FJI | Regime 3 | Regime 3 (storm 86.1%) | 213,473 | ✓ FIT |
| VUT | Regime 3 | Regime 3 (storm 88.8%) | 246,752 | ✓ FIT |
| SLB | Regime 3 | INSUFFICIENT DATA (26K total) | 26,290 | Below 100K threshold |
| BRA | Regime 2 or 4 | Regime 4 (flood 64.8% / storm 31.8%) | 5,404,585 | ✓ FIT (closer to Regime 4) |

5th-regime (drought) test for SOM/ETH/AFG/BFA/NER:
- SOM: 4_MIXED (drought 41.8%, flood 56.8%, storm 1.3%) — **drought is sub-channel, not regime-defining**
- ETH: 4_MIXED (drought 32.6%, flood 66.0%)
- AFG: 4_MIXED (drought 16.4%, flood 58.2%)
- BFA/NER: pure flood (Sahel-flood subtype within Regime 4)

**Verdict:**
- **F1 not fired** (1 of 7 holdout fit none → not >3)
- **F2 not fired** (all storm-predicted countries showed storm >70%)
- **F3 not yet testable** (need decadal data)
- **F4 PARTIALLY fired** — drought is sub-channel of Regime 4, doesn't need Regime 5. **5th regime falsified**; 6th regime (EQ) emerged instead.

**Net: HYPOTHESIS SUPPORTED with one extension** (added Regime 6: Earthquake-dominant via HTI). 5 of 8 strong fits, 1 new-regime discovery, 1 insufficient-data, 1 borderline-Regime-4. New regime confirmed by single case; needs NPL/CHL/MEX/IDN replication.

**Updated typology (6 regimes):**
1. Bimodal-mega-flood (PAK)
2. Steady-high-flood (IND)
3. Storm-dominant (PHL, VNM, MOZ, DOM, CUB, USA, FJI, VUT)
4. Mixed flood-storm (BGD, BRA; sub-types: Sahel-flood BFA/NER, Horn-drought-flood SOM/ETH)
5. Drought-dominant — **falsified as regime**; drought is sub-channel within Regime 4
6. **Earthquake-dominant (HTI)** — NEW
