# CLTR PRE-REG — Fractal leaf 2 at COUNTY resolution: does food insecurity split into rural-access vs urban-income?

**LOCKED before fit:** 2026-05-29. Owner: CLTR. Resolves the leaf-2 split that was INCONCLUSIVE at state resolution (state-level food insecurity was poverty-dominated; access n.s.). County Map-the-Meal-Gap data now on disk gives a within-state food-insecurity outcome.

## Question
PRE_REG_039 / the fractal test: food insecurity is a level-1 leaf (poverty-ruled). Does it recursively split into **rural-access-limited** vs **urban-income-limited** sub-leaves with DISTINCT dominant rules → fractal? Or is food insecurity "just poverty" everywhere (terminal)?

## Unit & data (county, n≈3,000+)
- **Outcome:** county **Overall Food Insecurity Rate** — `MMG2025_2019-2023_Data_To_Share.xlsx` (County sheet). Primary year **2023**; 2021–2023 for validation + stability.
- **poverty:** FEA `POVRATE21` (county, sentinel <0 → NaN).
- **access floor:** FARA `LAPOP1_10` / `Pop2010` aggregated tract→county (Σ/Σ) = low-access population share.
- **rural:** **RUCC 2023** (built into MMG). `rural = RUCC ≥ 4` (USDA nonmetro); continuous RUCC as robustness.
- Join on 5-digit county FIPS (zero-padded). Rate aligned to percent if stored as fraction.

## Validation (integrity, before the split)
Aggregate county FI 2021–2023 → state (Σ #FI persons / Σ population) and confirm it reproduces FEA `FOODINSEC_21_23` (the state value the seam used). Expect r≈0.99 (FEA sources from MMG). Report; a low r means a linkage/vintage error — halt and fix.

## Decision rules (locked) — n is large so judge by EFFECT SIZE (std β), not just p
- **F2-D1 — income channel is universal:** poverty std β > 0, p<0.05 in BOTH metro and nonmetro subsamples.
- **F2-D2 — access is a RURAL-specific channel:** the **access×rural interaction std β > 0, p<0.05** AND access std β is meaningfully larger in the nonmetro subsample than metro. (Physical access drives rural food insecurity beyond poverty; not urban.)
- **FRACTAL-SPLIT ⇔ F2-D1 ∧ F2-D2** (food insecurity decomposes into urban-income + rural-access sub-leaves with distinct rules).
- **Falsifier F-F2 (TERMINAL):** access×rural n.s. OR access negligible in both subsamples → food insecurity is poverty-ruled everywhere; the leaf does NOT split → terminal (food = a poverty axis, full stop). The state-level result makes this a live outcome.

## Models
1. Full: `food_insec ~ poverty + access + rural + poverty×rural + access×rural` (standardized, HC1).
2. Subsamples: metro (RUCC 1–3) and nonmetro (RUCC ≥4) separately: `food_insec ~ poverty + access`; report std β + which dominates.
3. Stability: rerun full model for 2021, 2022, 2023.

## Caveats (pre-locked)
- Correlational, cross-sectional; ecological (county).
- FARA access is 2019 vintage; poverty 2021; FI 2023 — vintages differ, aligned at county, flagged.
- LAPOP1_10 = low-access at 1 mi (urban) / 10 mi (rural) — the standard combined measure, appropriate for both.
- Large n inflates significance → effect-size emphasis is built into the rules.

## Artifacts (CLTR namespace)
- `_scripts/CLTR_paper7_fire_leaf2_county.py` → `analysis/CLTR_paper7_leaf2_county_results_2026_05_29.json`
- dig `digs/CLTR_2026_05_29_fractal_leaf2_county.md`
- raw `data/paper7/mmg/MMG2025_2019-2023_Data_To_Share.xlsx`
