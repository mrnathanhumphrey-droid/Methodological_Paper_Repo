# RMD-SRC US Internal Migration — Results Record

**Factual results record (not a manuscript).** All numbers, methods, and verdicts from the 2026-05-27/28 build. Substrate: US internal migration, the named falsification target of RMD-SRC (Humphrey working draft).

---

## 0. Objective & data

Test whether RMD-SRC (Recursive Moment-flow Decomposition + Statistical-Rule Classification) holds on US internal migration.

**Data (all SHA256-manifested, ~1.12 GB):**
- IPUMS USA ACS 2012–2021, individual records, 30 vars (extract #1). *Not redistributable per IPUMS terms.*
- IRS SOI county-to-county migration 2011–12 → 2022–23 (public).
- Census TIGER PUMA shapefiles (2010 + 2020 vintage) + PUMA/MIGPUMA crosswalk (public).

**Pre-reg:** v1.0 + amendments v1.1–v1.7, all locked, all diagnostic-driven, literal-rule outputs preserved.

**Locked scope (v1.1–v1.3):** PUMA-to-PUMA events via MIGRATE1D ∈ {24,31,32}; single 2010-vintage geography (ACS 2012–2021); train 2012–2017 / holdout 2018–2021; observables at MIGPUMA resolution (origin only recorded at MIGPUMA).

---

## 1. Demographic arm (Steps 0–4)

**ℙ₀ (v1.2):** age × income × family × education cross-product (48 cells) → **38 species** after deterministic collapse of 10 sub-500-events/yr cells. 23,332,197 persons; **994,235 cross-PUMA migration events**. Partition hash frozen pre-outcome.

**Observables (v1.3):** opportunity-deficit (PCA-1 of median income, emp/pop 25–54, BA+ share, affordability; frozen on 2012–2017), log great-circle MIGPUMA-centroid distance, log destination MIGPUMA density.

**Step 1–2:** 1,140 moment trajectories (38×3×10). Under the v1.4-refined rule: log_distance and log_dest_density 38/38 **Stationary**; opp_deficit mostly Fragmenting (normalization-sensitive on a zero-centered variable).

**Step 3 (v1.4/v1.5 cleanness):** response function x = α + β_g·opp_deficit + β_s·ρ_s + β_x·ρ_x, origin-MIGPUMA-clustered SE. **Network sorting: 89/114 significant β_s — 48 boson (agglomeration), 41 fermion (dispersion).** Cleanness recalibrated to event scale (R²≥0.05, Shapiro n=300, residual dip).

**Falsifiers:**
- **F1 does not fire** — 0.9% clean ≪ 80% → substrate is not classical; decomposition warranted.
- **F3 does not fire** — 0 trajectory-vs-β_s contradictions (after fixing Stationary=inconclusive).
- **F2 FIRES** — Step-4 decomposition (rounds 1 & 2, order 4a→4b→4c): distance 1/57 + density 1/57 clean even after two rounds; only opp_deficit decomposes. **Geographic observables are decomposition-resistant under a demographic partition.**

**Verdict:** demographics organize *who sorts* (β_s) but cannot decompose migration's geography.

---

## 2. Geographic arm (v1.6, Stages 1–5)

Diagnosis: distance/density structure is geographic ("America as mini-countries"), not demographic. Additive arm; demographic result stands.

**Stage 1 — gravity baseline + 4-cube** (divisions 9, states 51; full 4-cube orig×dest×species×year, power-gated):
- Gravity pseudo-R² 0.63 (div) / 0.74 (state); mass elasticities ~0.85–0.98; distance friction γ −0.53/−0.66. **GEO_F1 does not fire** (residual structure exists). Within/between split 53/47.

**Stage 2 — corridor moment-flow** (observable = species-decomposed log gravity-residual; μ=mean over species, σ²=species-selectivity): **rich regime diversity across all four regimes** (div 11/22/13/26; state 41/167/109/192). Extreme corridors match known migration: MN→ND (Bakken) +2.51, AK→WA +2.69, WA↔HI, NH→ME; into Mid-Atlantic −1.3/−1.4 (NY-metro out-migration).

**Stage 3 — within-mini-country sorting:** density agglomeration near-universal (42/51 states boson); heterogeneity is state-level (β_s sd 0.032) not division-level (0.004) → "different physics" localized to state scale.

**Stage 4 — CP/PARAFAC rank-3 on division gravity-residual cube:** 3 interpretable latent corridors — (1) Sun Belt (Pacific/Midwest→S-Atlantic/Mountain, young-low-income), (2) Northeast→Southeast retiree (60+ species), (3) contrast. **GEO_F2 does not fire** — split-half Tucker congruence 0.95 (factors replicate).

**Stage 5 — falsifiers:**
- GEO_F1 no-fire; GEO_F2 no-fire (0.95); GEO_F3 div 33% fires (fragile n=3) / state 23% no-fire.
- **GEO_F4 FIRES both** — corridor *dynamic regimes* don't transfer (κ −0.06 div, 0.02 state; accuracy ≈ chance).

**Verdict:** static structure (gravity, latent corridors) is real and replicable; the *dynamic regime* layer overfits.

---

## 3. Opportunity-moment taxonomy (v1.7) — CONFIRMED

Diagnosis: migration sorts on the **moments** of the opportunity field, not on demographics.

**Upside index** (P90, P90/P50, top-income share, Gini; PCA frozen 2012–2017) — variance/ceiling of opportunity; correlation with the mean index only **0.37** (distinct dimension).

**Two pull-moments → four flows:**
| flow | def | young | kids | dest density |
|---|---|---|---|---|
| DREAMER | hi-σ, lo-μ | 42.7% | 27.0% | 991 |
| STABILITY | hi-μ, lo-σ | 40.2% | 31.6% | 356 |
| BOTH | up both | 44.0% | 27.6% | 984 |
| CLEARING | down both | 39.0% | 28.7% | 381 |

Upside instrument fixed the mean-index failure (dreamer young Δ +2.8 → +9.2 in the tails; family-sign flipped to correct). Separation is sharp on *where* (density ≈3×), modest on *who* (4–5pp) — opportunity generates the flow, demographics select within it.

**Held-out gate (PRE_REG v1.7):** signature-vector correlation train(2012–17) vs holdout(2018–21) = **0.999** (≥0.80). Both sanity contrasts preserved. **PASS** — the taxonomy transfers because it is *static*, unlike the dynamic corridor regimes.

---

## 4. Desperation = the seam (honest negative + cross-substrate bridge)

A fifth (push/displacement) flow was attempted: split the down-both quadrant by origin rent-burden. **Demographically null** (low-income Δ −1.2, wrong direction).

**Why:** ACS observes movers *post-move* (RENTGRS = destination, not origin) → the individual displacement push is structurally invisible; the truly desperate exit the mover sample entirely (eviction, doubling-up, homelessness).

**Two-mirrors synthesis:** this migration study (pull side, ACS) and the SDP/homelessness study (rent-displacement funnel, demand-led ~3× supply, n=302 CoC) are the same displacement object viewed from opposite sides. The same rent event is a "missing mover" in ACS and a "new homeless person" in the CoC count. Each study's blind spot is the other's domain.

---

## 5. Consolidated verdict

RMD-SRC **partially holds** for migration, precisely localized:
- ✅ **Static decomposition works** — demographic sorting (48 boson / 41 fermion), geographic gravity + replicable latent corridors, and the opportunity-moment pull taxonomy (held-out r=0.999).
- ❌ **Dynamic regime-classification fails** — F2 (decomposition-resistant geography under demographic partition) and GEO_F4 (corridor regimes don't transfer).

Mechanism: migration is an opportunity-clearing flow network. Opportunity is the generative field (endogenous, vacancy-chain-coupled); demographics are the selection/gearing; the field is read by people via its *moments* (μ = stability, σ = aspiration). Decomposition is the wrong mathematics for a conservation law, which is why the dynamic/decomposition layer breaks while the static-structure layer holds.

---

## 6. Next arc — stitch the seam (not started)

Conservation model: rent-displacement outflow = successful out-migration (ACS, clearing) + homelessness inflow (SDP/CoC), split by landing probability (destination availability). Requires the homelessness/SDP dataset (cross-project, D:/IDP) + a CoC↔county↔MIGPUMA crosswalk. Testable prediction: rent pushes the *split* between migration and homelessness as a function of landing capacity.

---

## Reproducibility

All scripts in `src/rmd_src/`. Pre-regs in `prereg/`. Aggregate results in `results/`. Individual-level and raw data (`data/`) are git-ignored (IPUMS non-redistribution). Env: `requirements.lock.txt`.
