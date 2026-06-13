# PRE-REG 039 — Seam closure: two discharge axes of one displacement system

**Authored:** 2026-05-29
**Status:** LOCKED before fitting. Commit hash recorded at lock.
**Home:** Paper 7 (SDP framework). Closes the migration↔homelessness seam.

## Why this exists

The migration substrate (D:/Migration) nulled the displacement *push* five independent ways: net-livability field (Stage A), desperation axis, four flow-bridges, and food-apartheid on both instruments (FARA food-access inert for all races; HOLC redline NH-White-only, racial differential inverted). Conclusion: **migration flows cannot instrument the push — it is a vertical status-drop, not a horizontal move.** The prior conservation/bifurcation seam test also failed (income does not route an out-migration vs homelessness split; `paper7_conservation_seam_2026_05_28.json`).

This pre-reg tests the remaining, positive form of the unified frame: the **terminus is a multi-axis gated system**. The same precarity discharges as a vertical status-drop on whichever axis has the weakest local floor:
- **rent floor hard** → discharge as **homelessness** (no cheap unit to fall to; coasts).
- **rent floor soft + food-access floor weak** → discharge as **food insecurity** (cheap housing absorbs the housing fall, but the deprivation surfaces in nutrition; South).

If the two discharge axes **dissociate** geographically and share the **same precarity input**, the seam closes: one system, a rent-floor switch between two axes, with migration as the blind horizontal complement.

## Unit and data (state level, n≈51 — the resolution of the dissociation and of the precarity/Colburn–Aldern evidence)

FEA food insecurity is state-resolved (verified: 50/51 states single-valued), so the test is at state level. All on-disk:
- **food_insec** = FEA `FOODINSEC_21_23` (state household food-insecurity %, Food Environment Atlas).
- **homeless_per_10k** = `paper7_coc_timepanel` CoC `homeless_per_10k` aggregated to state (population-weighted, latest year).
- **rent_floor** = CoC `rent_coc` aggregated to state (population-weighted).
- **precarity** = Pulse `behind_on_rent_share` (and `eviction_risk_share`), state mean over periods (`paper7_pulse_housing_precarity`).
- **poverty** = FEA `POVRATE21`, state (population-weighted county→state).
- **food_floor** = FARA low-access population share at state = Σ`LAPOP1_10` / Σ`Pop2010` over tracts in state (income-free distance measure; same instrument family as the migration arm).

## Pre-registered predictions (decision rules)

- **CLOSE_D1 (precarity → food insecurity):** corr(precarity, food_insec) > 0, p < 0.05. The precarity that does NOT become homelessness must surface somewhere — predict food insecurity.
- **CLOSE_D2 (precarity ↛ homelessness):** corr(precarity, homeless_per_10k) NOT significantly positive (replicates the Pulse rent-gating: behind-on-rent ↔ homeless r≈0, eviction-risk ↔ homeless r<0).
- **CLOSE_D3 (axes dissociate):** corr(food_insec, homeless_per_10k) ≤ 0 (NOT significantly positive). The two discharge axes do not co-rise; high-food-insecurity states are not high-homelessness states.
- **CLOSE_D4 (the switch is the rent floor):** in `homeless ~ rent_floor + poverty`, rent_floor positive & significant; in `food_insec ~ poverty + food_floor (+ rent_floor)`, poverty and/or food_floor positive & significant AND rent_floor NOT significant. Rent gates homelessness, not food insecurity.

**SEAM_CLOSED ⇔ D1 ∧ D2 ∧ D3 ∧ D4.** Reading: one displacement system, precarity is the shared input, the rent floor is the switch, food insecurity and homelessness are the two dissociated discharge axes, and migration is the structurally-blind horizontal axis (established in D:/Migration).

**Falsification:** if D3 is significantly POSITIVE (food insecurity and homelessness rise together) the "two-axis" model is wrong — they're one severity gradient, not dissociated axes, and the seam does NOT close this way. If D1 is null, precarity does not surface as food insecurity and the discharge framing fails.

## Known limitations (logged pre-fit)

- State resolution (n≈51); coarse, low power for interactions — hence correlational + simple-regression decision rules, not fine interactions. The CoC-level rent→homelessness gate mechanism itself was already established at finer resolution (PRE_REG_031).
- Cross-sectional / correlational; no person-linkage; this is geographic dissociation, not individual mediation.
- food_insec (FEA, ~CPS-FSS state) and homeless (PIT/CoC→state) and precarity (Pulse) come from different instruments at different vintages; aligned at state, latest-available.
- "Food insecurity as a discharge axis" is the *terminus* reading; the migration arm already proved food access is NOT a migration push, so this is correctly placed on the terminus side, not as a flow.
