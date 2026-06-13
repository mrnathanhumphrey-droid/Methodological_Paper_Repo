# CLTR PRE-REG — Fractal level 3 (b): does the SHELTERED sub-leaf split again?

**LOCKED before fit:** 2026-05-29. Owner: CLTR. Sibling of `CLTR_PRE_REG_fractal_level3_street_2026_05_29.md`. Extends level-2 (homelessness→{street←climate, sheltered←RTS}).

## Question
The sheltered leaf was RTS-ruled at level 2 (rts dominant; climate n.s. there). Does it split AGAIN, or is it terminal (RTS rules everything)? Two recursion tests:
1. **Need × capacity (user framing):** does sheltered split into a COLD-need component (cold winters → must shelter to survive) and a CAPACITY/provision component (RTS legal duty → beds)?
2. **Structural sub-types:** does the sheltered population decompose into **emergency shelter (ES)** vs **transitional housing (TH)** governed by DIFFERENT rules?

## Unit & data
State, year 2024, n≈51. `paper7_sdp_state_year_panel.csv` (unsheltered, overall_homeless, shelt_es, shelt_th, population) → sheltered_per_10k, shelt_es_per_10k, shelt_th_per_10k. Drivers: **jan_temp** (AUTHENTIC NOAA climdiv 1991–2020; HI/DC filled from policy_block, flagged), **rts** (capacity/provision), **rent_floor** (pop-weighted CoC→state), **medicaid_exp** (safety-net/funding proxy for programmatic TH). All standardized.

## Decision rules (locked)
- **SH-D1 — need + capacity both matter:** in `sheltered_per_10k ~ jan_temp + rts + rent_floor`, BOTH a cold-need driver (**jan_temp negative, p<0.05** — colder → more sheltered) AND **rts positive, p<0.05** are significant → sheltered splits into cold-need × RTS-capacity (two distinct rules), not RTS alone.
- **SH-D2 — sub-type split:** the dominant (largest |std β|, p<0.05) driver of `shelt_es_per_10k` ≠ that of `shelt_th_per_10k` (ES and TH governed by different rules), each child clean (dominant sig, R²≥0.25).
- **SHELTERED FRACTAL-CONTINUES ⇔ SH-D1 ∨ SH-D2.**
- **Falsifier F-SH (TERMINAL):** neither fires — RTS/rent dominates both sub-types and cold is n.s. → the sheltered branch bottoms out. (This would be an informative ASYMMETRY: the street branch recurses [climate-gate × supply], the sheltered branch is terminal.)

## Priors / honesty
- Level-2 already showed climate n.s. for sheltered (−0.95, p=0.54) — so SH-D1's cold component may well FAIL; tested honestly. Not blind to that.
- RTS and cold are confounded (RTS states NY/MA/DC are cold) — separation is low-powered at n≈51; flagged. The ES/TH structural split (SH-D2) is the cleaner test.

## Caveats (pre-locked)
- State n≈51, correlational, cross-sectional, low power for the need/capacity separation.
- Sheltered sub-types are administrative (ES/TH) HUD categories; no direct shelter-capacity/funding variable on disk (medicaid_exp is a weak proxy).
- jan_temp authentic state-level (climdiv); DC/HI filled from policy_block.

## Artifacts (CLTR namespace)
- `_scripts/CLTR_paper7_fire_fractal_sheltered.py` → `analysis/CLTR_paper7_fractal_sheltered_results_2026_05_29.json`
- dig `digs/CLTR_2026_05_29_fractal_sheltered_recursion.md`
