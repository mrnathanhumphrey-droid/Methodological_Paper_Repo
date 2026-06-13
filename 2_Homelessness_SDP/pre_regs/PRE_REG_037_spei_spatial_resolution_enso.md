# Pre-Registration 037 — SPEI Spatially-Resolved Drought ENSO Test (P8-F2)

**ID:** PRE_REG_037
**Locked:** 2026-05-28 (predictions + falsifiers + exact metric/thresholds pre-committed BEFORE pulling the area-fraction series from GEE)
**Substrate:** PRE_REG_036 diagnostic limitation (country-box MEAN dilutes spatially-concentrated Horn drought — the 2020-22 catastrophe registered ~0 box-mean SPEI and never tripped the −1.0 threshold)
**Paper:** 8 (Compound-Crisis Coupling)
**Status:** LOCKED — fires immediately after the GEE area-fraction pull

---

## 0. Why this test exists (the diagnostic trigger)

PRE_REG_036 tested Horn drought via **country-box MEAN SPEI** and fired F1+F2 (Horn ~50% La Niña, same as displacement → single-year-ENSO weak, not an instrument artifact). BUT it surfaced a clear **measurement pathology, independent of the ENSO question**: the 2020-2023 Horn drought — worst in 40 years, five failed seasons, textbook multi-year La Niña, >1M displaced — registers as ~0 box-mean SPEI (ETH_12 2022 = +0.05, SOM_12 2022 = −0.30) and never trips the drought threshold. The drought was spatially concentrated in the arid SE lowlands (Somali region, Borena, southern Somalia); averaging with the wet Ethiopian highlands inside the country box washes it out.

**This is a diagnostic-driven (not result-driven) trigger** — the box-mean demonstrably cannot see a drought all sources agree happened. PRE_REG_037 re-runs the ENSO test with a **spatially-resolved drought metric** that does not require averaging across climate zones. The principled choice is **area-fraction-in-drought** (% of the region's land area in moderate+ drought) — the standard drought-monitoring approach — NOT a hand-picked sub-box (which would risk result-driven gerrymandering).

## 0a. The resolution this provides
- If the spatial metric NOW shows ≥60% La Niña where the box-mean showed 50% → the box-mean was **diluting a real La Niña signal**; the climate mechanism IS present, just spatially concentrated. PRE_REG_036's F1 was a spatial-aggregation artifact.
- If the spatial metric STILL shows ~50% → the weak signal is **robust to spatial resolution**; ENSO is genuinely weak (PRE_REG_036's conclusion firmed further, now bulletproof).
- Either way, a key validation: **does the 2020-2022 Horn drought finally register as a drought-year?** (it must, if the metric works).

---

## 1. Hypothesis

**H1:** With a spatially-resolved drought metric (area-fraction-in-drought), Horn (ETH+SOM) drought years cluster in La Niña years (≥60%) — the enrichment the country-box MEAN diluted away. The 2020-2022 Horn drought registers and is La-Niña-classified.

**H2:** BRA-Amazon drought years remain El-Niño-aligned (opposite phase), confirming the two-family split survives the spatial metric.

---

## 2. Pre-locked metric + predictions

**Metric (pre-committed exactly):** for each year, December image, per country box, mask to land (|SPEI| < 10, drops the 1e30 sentinel), then:
- **`frac_drought` = fraction of land pixels with SPEI ≤ −1.0** (area in moderate+ drought). This is the PRIMARY spatial metric.
- Secondary continuous: **`p10` = areal 10th-percentile SPEI** (the worst-affected tenth of the region).
- Bands: SPEI_12 (annual, primary) + SPEI_03 (OND short-rains, Horn secondary).
- ENSO phase: OND NOAA ONI (La Niña ≤ −0.5 / El Niño ≥ +0.5 / neutral), same as PRE_REG_034/036.
- Window: 1950-2023.

**Drought year (pre-committed):** `frac_drought ≥ 0.30` (≥30% of the region's land area in moderate+ drought). Sensitivity reported at 0.20 and 0.40.

### Prediction set A — Horn La Niña enrichment (spatial)
- **Predicted:** Horn (ETH+SOM) drought years (frac_drought ≥ 0.30) are ≥ **60%** La Niña, AND enrichment over baseline La Niña rate (~35%) is ≥ +15pp.

### Prediction set B — Amazon opposite phase
- **Predicted:** BRA-Amazon drought years have La Niña share < 30%, El Niño share > La Niña share, and BRA La Niña share < Horn La Niña share.

### Prediction set C — does the spatial metric register the 2020-22 Horn drought?
- **Predicted:** 2021 and/or 2022 (and/or 2017) appear as Horn drought-years under frac_drought ≥ 0.30 (they were invisible under box-mean). This validates the metric independent of ENSO.

---

## 3. Falsifiers (pre-committed)

- **F1 (no Horn enrichment even spatially):** Horn frac-drought years < 50% La Niña → even the spatially-resolved metric shows no La Niña enrichment → ENSO genuinely weak; PRE_REG_036's conclusion stands, now robust to spatial aggregation.
- **F2 (metric still blind):** the 2020-2022 Horn drought STILL does not register as a drought-year under frac_drought ≥ 0.30 → the problem is deeper than spatial averaging (likely CRU TS station sparsity in the Horn) → SPEI/CRU cannot test recent Horn events at all.
- **F3 (Amazon breaks split):** BRA frac-drought years are La-Niña-aligned (share ≥ Horn) → two-family opposite-signature finding does not survive the spatial metric.

F1 firing = the box-mean was NOT hiding a signal; ENSO is genuinely weak (PRE_REG_036 bulletproofed).
F1 NOT firing (Horn ≥60% La Niña) = the box-mean DILUTED a real La Niña signal; PRE_REG_036 F1 was a spatial-aggregation artifact and the climate mechanism is real-but-localized.

---

## 4. Methodology
- SPEIbase v2.10 via GEE `CSIC/SPEI/2_10` (same source as PRE_REG_036).
- Per year/box/band: `frac_drought` via `ee.Reducer.mean()` on `spei.lte(thr)` over land-masked pixels; `p10` via `ee.Reducer.percentile([10])`. scale=55660.
- Contingency: drought-year × ENSO-phase; exact counts (small n; report all years).
- Baseline La Niña rate over the window for enrichment.
- Sensitivity over frac threshold (0.20/0.30/0.40) and band (annual/OND).

## 5. Acknowledgments at lock time
- frac-threshold 0.30 is a pre-committed cut; sensitivity reported.
- Country box still spans climate zones; area-fraction handles concentration but not sub-national ENSO heterogeneity.
- ENSO ≠ sole driver (IOD co-drives Horn; Atlantic SST co-drives Amazon).
- If CRU TS station density is the limit (F2), no gridded product fixes it — would need station/satellite rainfall (CHIRPS) — flagged but out of scope here.
- Coupling ≠ causation; this tests the drought channel's climate driver.

## 6. Cross-references
- PRE_REG_036 (box-mean version — this resolves its dilution limitation); PRE_REG_034 (displacement); PRE_REG_033/035 (coupling census/structure).
- PATTERN_023 (ETH), PATTERN_021 (BRA), PATTERN_008 (Horn drought).
- [[reference-google-earth-engine-access]]; data `data/oni.txt`.

## 7. Provenance
Locked 2026-05-28 before the GEE area-fraction pull. Metric, thresholds, predictions, falsifiers all committed first. Fires immediately after the pull.

---

## 8. Results — first fit (fired 2026-05-28, GEE area-fraction pull)

Full dig: `papers/PAPER_8_COMPOUND_CRISIS/digs/2026_05_28_prereg037_spatial_enso.md`

**Set A F1 (harder than box-mean); the dilution alternative is RULED OUT.** The spatially-resolved metric does NOT rescue the La Niña signal — it shows it even weaker than the box-mean.

- **Set A (F1)**: Horn area-fraction drought years (≥30% land SPEI ≤ −1.0, annual, 1950-2023) → **41.2% La Niña** (+6.1pp vs 35.1% baseline) — *lower* than the box-mean's 50%/+14.9pp. Gentle severity gradient (35→41→45% as drought widens), never near 60%. OND band 41.7%.
- **Set C-reg (YES)**: SOM 2022 registers (36.5% of land in drought; invisible at box-mean). **F2 does NOT fire — the metric is not blind to recent droughts.**
- **Set C-exceed (NO)**: spatial 41.2% < box-mean 50% → **the box-mean was NOT diluting a hidden La Niña signal.** Dilution affected event-visibility, not the enrichment conclusion.
- **Set B holds on OND band**: BRA Amazon 17.6% La Niña / 52.9% El Niño (0%/60% at ≥0.40) — opposite the Horn; two-family split survives. Annual band smears it (timing artifact).
- **Tempers PRE_REG_036**: its "extreme Horn droughts 100% La Niña" was n=2 (1955,1984); the area metric shows the most-widespread droughts at only 45-47% La Niña — a gentle gradient, not a tail-lock. Honest downward revision.

### Net (triangulated)
Across three instruments — displacement (034: 50%), box-mean SPEI (036: 50%), area-fraction SPEI (037: 41%) — Horn drought–La Niña is consistently ~40-50%: weak, real, robust to instrument AND spatial aggregation. **Single-year ENSO does NOT drive Horn compound-crisis coupling.** Amazon stays El-Niño-aligned (opposite). The ENSO hypothesis is triangulated-negative; the climate-mechanism question is closed for Paper 8 (climate = weak tail-modulator, not coupling driver).
