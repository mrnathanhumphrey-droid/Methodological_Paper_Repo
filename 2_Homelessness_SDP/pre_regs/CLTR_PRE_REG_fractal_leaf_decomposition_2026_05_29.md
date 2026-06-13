# CLTR PRE-REG — Fractal test: do the PRE_REG_039 discharge leaves recursively split into clean sub-leaves?

**Authored / LOCKED before (re-)fitting:** 2026-05-29. Owner: CLTR agent. Home: Paper 7 (SDP), seam work.
**Numbering:** CLTR-prefixed (no bare PRE_REG_NNN — 039/040 are contested by concurrent agents).

## Why this exists
PRE_REG_039 (CLOSED) showed displacement is ONE object that decomposes into two driver-distinct discharge leaves: **homelessness ← rent floor**, **food insecurity ← poverty**, sharing one upstream precarity. The RMD reading: a coarse cell that isn't single-ruled decomposes into clean leaves. The **fractal** claim is stronger — the "single rule fails → splits into clean sub-rules" motif must REPEAT one level down. This pre-reg tests recursion on each leaf.

- **Fractal-positive at a leaf:** the leaf's single parent rule fails to govern its internal split, a NEW (orthogonal) rule governs the split, and each sub-leaf is internally clean → self-similar.
- **Terminal leaf:** the same parent rule governs the children (no new structure) OR sub-leaves aren't cleaner → recursion bottoms out → finite hierarchy, not fractal.

## Integrity disclosures (pre-locked)
- **Leaf 1 is CONFIRMATORY, not blind.** The exploratory `paper7_structural_firstlook` already indicated climate dominates unsheltered SHARE (LOO 0.36; jan_temp std +0.11) with RTS secondary. So leaf-1's hypothesis is informed. What is locked-and-new here: the RMD decision rules applied to the SEPARATED street/sheltered RATES (firstlook used the ratio only), and the cleanness criteria below.
- **Leaf 2 is BLIND but DATA-LIMITED.** FEA food insecurity is state-resolved only (no within-state rural/urban outcome), so leaf 2 can only be a COARSE state-level interaction test; a clean split needs county food insecurity (Feeding America Map-the-Meal-Gap — not on disk). Verdict capped at "suggestive/inconclusive."
- **jan_temp is the project's approximate climate gradient** (`paper7_policy_block.py`, hand-coded first-look table); RTS={NY,MA,DC}, Medicaid/rent-control/min-wage are documented binaries (KFF/NMHC/DOL). Reused as-is for consistency with 029; flagged.

---

## LEAF 1 — Homelessness → {street (unsheltered), sheltered}
**Unit:** state, n≈50, year 2024 (matches 039). **Source:** `paper7_sdp_state_year_panel.csv` (unsheltered, overall_homeless, population, homeless_per_10k) + `paper7_policy_block.policy_frame()` (jan_temp, rts, medicaid_exp, rent_control, min_wage) + rent_floor (pop-weighted rent_coc CoC→state from metro_coc_panel).
**Outcomes:** `unsheltered_per_10k` (street); `sheltered_per_10k = homeless_per_10k − unsheltered_per_10k`. Also `unsheltered_share` (the split itself).
**Regressors (standardized):** jan_temp, rent_floor, rts (+ medicaid_exp, rent_control as controls).

**Decision rules (locked):**
- **L1-D1 — parent rule sets level, not split:** in `unsheltered_share ~ rent_floor + jan_temp + rts`, **rent_floor is NOT the dominant/sig driver of the split** (the rent rule governs the LEVEL, established 031/032, not the street/sheltered split). PASS if |rent_floor std β| < the climate/RTS drivers and/or rent_floor p≥0.05.
- **L1-D2 — distinct dominant rules:** the dominant (largest |std β|, p<0.05, correct sign) driver of `unsheltered_per_10k` ≠ that of `sheltered_per_10k`. Predicted: street dominant = **jan_temp (+)**; sheltered dominant = **rts (+)** or rent_floor.
- **L1-D3 — children clean:** each child model's dominant driver is significant (p<0.05, predicted sign) AND child R² ≥ 0.25.
- **LEAF-1 FRACTAL-POSITIVE ⇔ L1-D1 ∧ L1-D2 ∧ L1-D3.** Falsifier **F-L1**: L1-D2 fails (same dominant driver, e.g. rent rules both) → terminal leaf, NOT fractal.

---

## LEAF 2 — Food insecurity → {rural-access-limited, urban-income-limited}  (COARSE / data-limited)
**Unit:** state, n≈50. **Source:** FEA INSECURITY `FOODINSEC_21_23` (state) + `POVRATE21` (pop-weighted county→state) + FARA `food_floor` (Σ LAPOP1_10/Σ Pop2010) + `rural_share` (Σ Pop2010[Urban==0]/Σ Pop2010 from FARA). **Sentinel filter: FEA values <0 → NaN (the 039 bug).**
**Model:** `food_insec ~ poverty + food_floor + rural_share + food_floor×rural_share`.

**Decision rules (locked):**
- **L2-D1 — two channels present:** poverty p<0.05 positive (income channel) AND (food_floor OR food_floor×rural interaction) p<0.05 (access channel).
- **L2-D2 — access channel is rural-concentrated:** `food_floor×rural_share` interaction p<0.05 positive → the access sub-leaf is rural, distinct from the urban-income sub-leaf.
- **LEAF-2 FRACTAL-SUGGESTIVE ⇔ L2-D1 ∧ L2-D2** (suggestive only — resolution-limited). Falsifier **F-L2**: interaction n.s. → INCONCLUSIVE at state resolution; flag county-food-insecurity data need.

---

## Overall verdict
- **Self-similar (fractal earned at level 2)** if leaf 1 is fractal-positive (and leaf 2 at least suggestive). One clean self-similar split = the motif repeats once; full fractal needs further recursion (out of scope, noted).
- **Finite hierarchy** if leaves are terminal (parent rule governs children; no new orthogonal rule).

## Caveats (pre-locked)
- State resolution (n≈50), correlational, cross-sectional; low power for interactions (leaf 2).
- jan_temp approximate; swap to NOAA normals if leaf 1 hinges on climate precision.
- Sheltered rate is mechanically `homeless − unsheltered`; not an independent measurement.

## Artifacts (to be produced, CLTR namespace)
- `_scripts/CLTR_paper7_fire_fractal.py` → `analysis/CLTR_paper7_fractal_results_2026_05_29.json`
- dig `digs/CLTR_2026_05_29_fractal_leaf_decomposition.md`
