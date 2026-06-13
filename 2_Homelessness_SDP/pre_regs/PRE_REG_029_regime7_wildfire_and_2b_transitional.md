# Pre-Registration 029 — Regime 7 (Wildfire-dominant) + Regime 2b (Flood-transitional)

**ID:** PRE_REG_029
**Locked:** 2026-05-27 (decision rules pre-committed in `_scripts/paper2_regime7_and_2b.py` header + session log BEFORE co-validation results read)
**Substrate:** PATTERN_029 (GRC wildfire candidate) + PATTERN_030 (ARG/KHM flood-transitional gap) + PRE_REG_017 Phase 2 expansion
**Status:** LOCKED + FIRED 2026-05-27. Thread 1 (Regime 7) SUPPORTED; Thread 2 (Regime 2b) WALKED BACK.

---

## 1. Hypotheses

**H1 (Regime 7 exists — Wildfire-dominant):** A 7th disaster-displacement regime exists, defined by wildfire as the dominant displacement channel, anchored in the Mediterranean fire-climate zone. PATTERN_029 surfaced GRC as a candidate (its "Other" channel turned out to be 82% wildfire under the full GIDD hazard taxonomy).

**H2 (Regime 2b exists — Flood-dominant transitional):** A flood-dominant-but-multi-mechanism sub-regime exists between Regime 1 (pure bimodal-mega-flood, storm <10%) and Regime 4 (mixed), populated by countries with flood ≥70% AND meaningful secondary storm exposure (10-30%). PATTERN_030 surfaced ARG + KHM as candidates.

---

## 2. Pre-locked decision rules (committed before reading results)

### Thread 1 — Regime 7
- **GRC confirmed wildfire-dominant** if wildfire-IDP ≥ 60% of GRC's total disaster-IDP
- **Regime 7 REAL** if ≥ 2 additional Mediterranean countries (from ESP/PRT/CYP/ITA/TUR/FRA/HRV) have wildfire share ≥ 30%
- **Regime 7 WALKS BACK to GRC-anomaly** if GRC is the only country with wildfire ≥ 30%

### Thread 2 — Regime 2b
- **ARG/KHM confirmed transitional** if both have flood ≥ 70% AND storm in [10%, 30%]
- **Regime 2b REAL** if ≥ 2 additional candidates (from COL/IRQ/VNM/BGD) also fall in the flood≥70% + storm 10-30% gap
- **Regime 2b WALKS BACK to boundary-documentation** if only ARG/KHM qualify

---

## 3. Falsifiers

- **F1 (Regime 7 fails):** GRC wildfire < 60%, OR fewer than 2 Mediterranean co-validators → wildfire is not a regime, GRC is an anomaly
- **F2 (Regime 2b fails):** fewer than 2 additional flood-transitional members → R2b is a boundary zone, not a regime

---

## 4. Results — fired 2026-05-27

Full dig: `D:/IDP/papers/PAPER_2_DISASTER_REGIMES/digs/2026_05_27_regime7_confirmed_2b_walkback.md`

### Thread 1 — Regime 7: **SUPPORTED (F1 NOT FIRED)**

| Country | Total IDP | Wildfire share | Top channel | Member? |
|---|---:|---:|---|:---:|
| CYP | 1,710 | 99.2% | Wildfire | ✓ |
| GRC | 290,731 | 82.1% | Wildfire | ✓ (anchor) |
| PRT | 15,968 | 80.3% | Wildfire | ✓ |
| ESP | 199,358 | 71.2% | Wildfire | ✓ |
| FRA | 126,413 | 61.1% | Wildfire | ✓ (weakest) |
| ITA | 198,802 | 5.2% | Earthquake (60%) | ✗ → R6 |
| TUR | 4,468,840 | 2.1% | Earthquake (97%) | ✗ → R6 |
| HRV | 61,175 | 0.7% | Earthquake (68%) | ✗ → R6 |

- GRC wildfire = 82.1% ≥ 60% → confirmed dominant ✓
- Co-validators ≥30%: ESP, PRT, CYP, FRA (4, all actually ≥60%) → **≥2 threshold met**
- **Regime 7 REAL.** 5 confirmed members: GRC, ESP, PRT, CYP, FRA
- **Clean discrimination**: ITA/TUR/HRV are in the Mediterranean basin but earthquake-dominant (Regime 6), correctly separated. The test distinguishes wildfire-Mediterranean from earthquake-Mediterranean.

### Thread 2 — Regime 2b: **WALKED BACK (F2 FIRED)**

| Country | Flood | Storm | flood max/med | In gap? |
|---|---:|---:|---:|:---:|
| ARG | 85.4% | 11.1% | 5.0× | ✓ |
| KHM | 75.7% | 23.8% | 10.6× | ✓ |
| COL | 92.9% | 2.9% | 82.8× | ✗ (storm <10% → R2-like) |
| THA | 94.3% | 5.7% | 130× | ✗ (R1 bimodal) |
| PAK | 95.0% | 0.6% | 65× | ✗ (R1 reference) |
| IRQ | 44.8% | 0.3% | — | ✗ (not flood-dominant) |
| VNM | 10.8% | 89.0% | — | ✗ (storm-dominant R3) |
| BGD | 36.1% | 63.5% | — | ✗ (storm-leaning R4b) |

- ARG + KHM both qualify (flood≥70% + storm 10-30%) ✓
- Additional candidates in gap: **none** → **< 2 threshold; F2 FIRES**
- **Regime 2b WALKS BACK to boundary-documentation.** ARG + KHM are a 2-country transition zone between R1 and R4, not a populated regime.

---

## 5. Net result

| Hypothesis | Verdict |
|---|---|
| H1 (Regime 7 Wildfire-dominant) | **SUPPORTED** — 5 Mediterranean members; F1 NOT FIRED |
| H2 (Regime 2b Flood-transitional) | **WALKED BACK** — only 2 members; F2 FIRED; documented as boundary zone |

Paper 2 typology expands from 6 to **7 regimes**. The R2b hypothesis is honestly retired to boundary-documentation. Refinement-rich pair: one new regime confirmed, one candidate-regime walked back on its own pre-committed falsifier.

---

## 6. Cross-references
- PATTERN_029 (Regime 7 — now confirmed)
- PATTERN_030 (Regime 2b — now walked back to boundary-doc)
- PATTERN_019 (master typology — extended to 7 regimes)
- PATTERN_020 (Regime 6 EQ-dominant — ITA/TUR/HRV correctly retained here, not R7)
- PRE_REG_003 (original 6-regime typology)
- PRE_REG_017 (Phase 2 expansion that surfaced both candidates)
- `analysis/paper2_regime7_2b_2026_05_27.json`
- `_scripts/paper2_regime7_and_2b.py`

## 7. Provenance
Decision rules pre-committed in script header + session log before co-validation results read. Fired 2026-05-27.
