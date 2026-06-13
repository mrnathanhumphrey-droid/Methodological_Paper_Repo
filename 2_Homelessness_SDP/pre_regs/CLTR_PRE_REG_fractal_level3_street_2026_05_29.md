# CLTR PRE-REG — Fractal level 3: does the STREET (unsheltered) sub-leaf split again?

**LOCKED before fit:** 2026-05-29. Owner: CLTR. Extends `CLTR_PRE_REG_fractal_leaf_decomposition_2026_05_29.md` (level-2 found homelessness→{street←climate, sheltered←RTS} fractal-positive).

## Question
"Fractal" requires the "single rule fails → clean driver-distinct sub-leaves" motif to REPEAT. Level 2 gave street←climate. Level 3 asks: within the **street** leaf, does a NEW orthogonal rule govern the magnitude, or is street terminally climate-ruled?

**Hypothesis (blind — not seen at CoC resolution):** climate *gates* whether street homelessness is survivable; among climate-permitting places, **housing-supply tightness** sets the magnitude. So street splits into a climate-gate × supply-magnitude structure.

## Unit & data
CoC, year 2024, n≈302 (`paper7_metro_coc_panel_2024.csv`: unsheltered_per_10k, saiz_elasticity, rent_coc). Drivers: **jan_temp** (state→CoC broadcast via prefix, `paper7_policy_block`), **supply_tight = −saiz_elasticity** (higher = more supply-constrained), **rent_coc**, **rts** (CoCs in NY/MA/DC, control), **jan_temp×supply_tight**. All standardized.

## Decision rules (locked)
- **L3-D1 — a NEW rule emerges beyond climate:** in `unsheltered_per_10k ~ jan_temp + supply_tight + rent_coc + rts + jan_temp×supply_tight`, supply_tight OR rent_coc is significant (p<0.05, positive) — i.e. the street leaf is not governed by climate alone.
- **L3-D2 — self-similar gate×magnitude split:** the **jan_temp×supply_tight interaction is significant positive** (p<0.05) — street is worst where warm AND supply-constrained (climate gates possibility, supply scales magnitude).
- **FRACTAL-REPEATS (level 3) ⇔ L3-D1 ∧ L3-D2.** Genuinely fractal (motif at ≥3 levels).
- **Falsifier F-L3:** interaction n.s. AND no new significant main effect → street is climate-terminal → recursion bottoms out → FINITE hierarchy (two-level), not fractal.

## Caveats (pre-locked)
- jan_temp is state-broadcast to CoC (loses within-state climate variation, esp. CA/TX) — coarse climate; caveat.
- Correlational, cross-sectional, CoC resolution.
- Saiz elasticity covers 302 of 408 CoCs (metro-based; rural CoCs absent).

## Artifacts (CLTR namespace)
- `_scripts/CLTR_paper7_fire_fractal_level3.py` → `analysis/CLTR_paper7_fractal_level3_results_2026_05_29.json`
- dig `digs/CLTR_2026_05_29_fractal_level3_street.md`
