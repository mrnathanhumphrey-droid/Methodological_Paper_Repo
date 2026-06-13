# 20 — Karin 2019 PVCZ: Literal Zone Thresholds (extracted)

**Status:** VERIFIED (direct extraction from pvcz package binary)
**Date:** 2026-05-27
**Source:** `pvcz` Python package v0.3.0 (MIT license), file `PVCZ-2019_ver0p2_zones.npz`, key `limits` (dict)
**Extraction script:** `pip install pvcz` → `np.load(<pkg>/PVCZ-2019_ver0p2_zones.npz, allow_pickle=True)['limits'].item()`
**Companion paper:** Karin 2019, IEEE PVSC-46, DOI 10.1109/PVSC40753.2019.8980831 (verified in `18_VERIFICATION_Karin2019_PVCZ.md`)

---

## 1. Correction to substrate memory: canonical scheme is T×H = 50 zones, NOT 250

Project memory `project_solar_substrate.md` and `19_PREREG_v1.0_TOPCon_UVID.md` previously stated PVCZ = "T1-T10 × H1-H5 × W1-W5 = 250 combined zones." **The npz `total_num_zones` is `50`, and `zone_spec['pvcz']` enumerates only T1:H1 through T10:H5.** W (wind) is a separate stressor with its own 5-zone bin scheme but is NOT multiplied into the canonical `pvcz` label string. Same for V (temperature velocity, 4 zones) and GHI (3 zones) — independent stressor scales, not part of `pvcz` label.

**Source of confusion:** Karin 2019 paper §III lists T, H, W, V as four hazard axes — but the canonical "PV climate zone" label combines T and H only. W/V/GHI are queryable per-site stressors, not part of the bivariate zone string.

**Action:** Will correct `19_PREREG` Manufacturer × Encapsulation × Vintage × **T-zone × H-zone** × Mounting (drop "W-zone" — was based on incorrect 250-zone reading).

---

## 2. T-zone boundaries (Equivalent Temperature, Rack, 1.1 eV Arrhenius-weighted, °C)

| Zone | Lower (°C) | Upper (°C) | Width (°C) |
|---|---|---|---|
| T1 | −10.3 | 14.0 | 24.3 |
| T2 | 14.0 | 19.0 | 5.0 |
| T3 | 19.0 | 24.0 | 5.0 |
| T4 | 24.0 | 29.0 | 5.0 |
| T5 | 29.0 | 34.0 | 5.0 |
| T6 | 34.0 | 39.0 | 5.0 |
| T7 | 39.0 | 44.0 | 5.0 |
| T8 | 44.0 | 49.0 | 5.0 |
| T9 | 49.0 | 54.0 | 5.0 |
| T10 | 54.0 | 67.0 | 13.0 |

**Width interpretation:** Inner zones T2–T9 are uniform 5 °C wide; T1 (cold tail) and T10 (hot tail) span the longer tails of the global cumulative distribution. Boundaries calibrated to global land surface (~230k 0.25°×0.25° GLDAS-NOAH cells), approximately decile-balanced over inner zones.

**`T_equiv_rack_1p1eV` definition:** Site equivalent temperature for rack-mounted modules under Arrhenius kinetics with activation energy 1.1 eV (Boltzmann-weighted average of hourly module-back temperature time series). Drives Arrhenius-driven degradation (LeTID, encapsulant browning, junction box thermal aging, etc.).

**Roof-mount variant:** `T_equiv_roof_1p1eV` uses identical boundary set (insulated mounting raises operating temperature ~10 °C vs rack; zone assignment shifts hotter).

---

## 3. H-zone boundaries (Specific Humidity, mean, g/kg)

| Zone | Lower (g/kg) | Upper (g/kg) | Width (g/kg) |
|---|---|---|---|
| H1 | 0.7 | 3.0 | 2.3 |
| H2 | 3.0 | 4.1 | 1.1 |
| H3 | 4.1 | 5.9 | 1.8 |
| H4 | 5.9 | 10.5 | 4.6 |
| H5 | 10.5 | 18.3 | 7.8 |

**Width interpretation:** Non-uniform — H2/H3 are tightly binned (1–2 g/kg) around the temperate-mid-humidity transition; H4 spans broad subtropical band; H5 is tropical (5+ g/kg above H4). Boundaries empirically chosen to separate failure-relevant regimes (e.g., backsheet hydrolysis kinetics, PID-s susceptibility, junction-box water ingress).

**`specific_humidity_mean` definition:** Time-averaged absolute humidity (mass water / mass dry air) at module-relevant air column, derived from GLDAS-NOAH 3-hour reanalysis. Chosen over relative humidity because RH is temperature-coupled (an Arrhenius confounder); specific humidity is thermodynamically independent of T.

---

## 4. W-zone boundaries (ASCE 7-16 MRI 25-Year wind, mph)

| Zone | Lower (mph) | Upper (mph) |
|---|---|---|
| W1 | −6 | 1 |
| W2 | 1 | 33 |
| W3 | 33 | 36 |
| W4 | 36 | 39 |
| W5 | 39 | 60 |

**Note:** `W1 = [-6, 1]` reflects an integer sentinel for missing/inland-low-wind cells (no positive wind hazard). W2/W3/W4 are tightly clustered (1–39 mph design wind); W5 catches hurricane/cyclone-exposed coastlines.

**Source:** ASCE 7-16 MRI (Mean Recurrence Interval) 25-year design wind speed, gridded onto 0.25° land cells. Drives static + uplift loading analysis for racking/clamping.

**Standalone axis:** Not part of canonical T:H pvcz label. Tracked as independent site stressor.

---

## 5. Auxiliary stressor scales (not zone-binned for canonical pvcz label)

### Temperature velocity, rack (`T_velocity_rack`, °C/hr)

4 zones, boundaries: `[0.328, 1.1, 1.7, 2.3, 3.280]`. Captures thermal cycling fatigue rate (relevant to cell crack propagation, solder fatigue, EVA delamination).

### GHI mean (kWh/m²/day)

3 zones, boundaries: `[1.39, 3.5, 5.0, 7.32]`. Total irradiance driver; drives UV dose, soiling rates (in interaction with W), yield ceiling.

---

## 6. World stressor dataframe coverage

- File: `PVCZ-2019_ver0p2_world_PV_climate_stressors_and_zones.pkl`
- Shape: **230,742 land cells × 49 columns**
- Grid: 0.25° × 0.25° (~28 km at equator)
- Columns include: lat/lon, full Arrhenius series `T_equiv_rack_{0p1...2p1}eV` (11 activation energies sampled), specific humidity mean/rms, GHI mean, wind metrics, ASCE 7-16 hazard, Köppen-Geiger zone & class, plus all four zone-label strings + composite `pvcz_labeled` (e.g., `T4:H3`).
- Köppen-Geiger comparison fields present (`KG_zone`, `KG_class_0/1/2/02`, `KG_numeric_zone`) — supports the explicit Karin 2019 vs Köppen comparison work that motivated PVCZ.

---

## 7. Application to `19_PREREG_v1.0_TOPCon_UVID`

**Operational consequence:** For any TOPCon field cohort site (lat/lon known), assignment to (T-zone, H-zone) is a single lookup in the world stressors dataframe:

```python
import pvcz
df = pvcz.get_pvcz_data()  # returns the world stressors dataframe
site = df.iloc[((df.lat - target_lat)**2 + (df.lon - target_lon)**2).idxmin()]
T_zone = site['T_equiv_rack_1p1eV_zone']        # 'T1' ... 'T10'
H_zone = site['specific_humidity_mean_zone']     # 'H1' ... 'H5'
label  = site['pvcz_labeled']                    # 'T4:H3'
```

(Pseudocode — to be wrapped into `Solar/code/zone_lookup.py` when cohort sites land.)

**Pre-reg axis update needed:** `19_PREREG` ℙ₀ should read **Manufacturer × Encapsulation × Vintage × T-zone (10 levels) × H-zone (5 levels) × Mounting (rack/roof)** — total ℙ₀ cardinality |M| × |E| × |V| × 50 × 2. W is a covariate not a partitioning axis.

---

## 8. Claims ledger entries to add

| CLM ID | Claim | Status | Evidence |
|---|---|---|---|
| CLM-051 | PVCZ canonical scheme is T×H = 50 zones, not 250 | VERIFIED | npz `total_num_zones` = 50; `zone_spec['pvcz']` lists 50 labels |
| CLM-052 | T-zone boundaries: [−10.3, 14, 19, 24, 29, 34, 39, 44, 49, 54, 67] °C | VERIFIED | npz `limits['T_equiv_rack_1p1eV']` |
| CLM-053 | H-zone boundaries: [0.7, 3.0, 4.1, 5.9, 10.5, 18.3] g/kg | VERIFIED | npz `limits['specific_humidity_mean']` |
| CLM-054 | PVCZ activation energy = 1.1 eV (canonical) | VERIFIED | variable name `T_equiv_rack_1p1eV`; package default |
| CLM-055 | World coverage 230,742 land cells at 0.25° resolution | VERIFIED | pkl df.shape = (230742, 49) |
| CLM-056 | T-zone inner zones (T2-T9) uniform 5 °C wide | VERIFIED | derived from boundaries |
| CLM-057 | H-zones non-uniform; H4 (5.9-10.5 g/kg) widest temperate-subtropical band | VERIFIED | derived from boundaries |

---

## 9. Memo of follow-up

- Update `19_PREREG_v1.0_TOPCon_UVID.md` §ℙ₀ axes to read T×H = 50 zones (not 250 combined). Memo this as an amendment, not a re-lock (the pre-reg LOCK SHA fc32be4 is immutable; corrections go in DEVIATION log).
- Update `02_CLAIMS_LEDGER.md` with CLM-051 through CLM-057.
- Update memory `project_solar_substrate.md` to correct the 250→50 figure.
- Add `Solar/code/zone_lookup.py` skeleton when TOPCon cohort sites land.

---

**END MEMO 20**
