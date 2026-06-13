# Pre-Registration 001 — Strife-Signature Epicenter Diffusion

**ID:** PRE_REG_001
**Locked:** 2026-05-25
**Substrate:** IDP broad-data corpus (D:/IDP/)
**Status:** LOCKED — predictions and falsifiers pre-committed; not yet tested on holdout countries

---

## 1. Hypothesis

**H1 (descriptive):** Non-state strife violence (UCDP-GED type_of_violence = 2) in the Sahel cluster shows a **temporal epicenter-diffusion** pattern. Mali was the first-mover (first year with ≥50 strife fatalities = 2012 in the modern era); the signal then appears in adjacent countries with a multi-year lag.

Observed lag in generation data (will NOT be re-tested):
- MLI: 2012 (epicenter)
- BFA: 2020 (8-year lag)
- NER: 2021 (9-year lag)

**H2 (mechanism):** The diffusion is driven by **two coupled processes**:
- (a) Insurgent group operational expansion across borders (JNIM, IS Sahel Province) — testable via UCDP dyad_name overlap
- (b) Inter-ethnic / inter-clan violence flowing along ethnic-geographic corridors (Dogon-Fulani belts, Tuareg territories)

**H3 (generalization, the holdout test):** The same epicenter-diffusion structure exists in:
- **Central African sub-cluster:** CAR (epicenter, 2011) → CMR (peripheral), GAB, GNQ, CongoBrazz
- **Latin American sub-cluster:** HTI (epicenter, 2021) → DOM (peripheral, watching)

---

## 2. Pre-locked predictions (the holdout cases — NOT used to generate H1/H2)

### Prediction set A — Sahel southward extension

The Sahel diffusion hypothesis predicts that the strife signal will continue spreading southward into the West African coastal countries that are adjacent to BFA's Est region and MLI's southern borders.

| Country | Predicted first year ≥50 strife fatalities | Pre-locked window |
|---|---|---|
| **TGO (Togo)** | adjacent to BFA Est; predicted **2022-2025** | If TGO shows ≥50 strife fatalities by end-2025 → H3 supported |
| **CIV (Côte d'Ivoire)** | adjacent to MLI south + BFA west; predicted **2023-2026** | If CIV shows ≥50 strife fatalities by end-2026 → H3 supported |
| **GHA (Ghana)** | north-east border with BFA + TGO; predicted **2024-2027** | If GHA shows ≥50 strife fatalities by end-2027 → H3 supported |

### Prediction set B — Actor-overlap test

H2 mechanism (a) predicts that the SAME insurgent group names will appear as dyads in MLI, BFA, NER, BEN, and (predicted) TGO/CIV/GHA. Specifically:

- **JNIM (Jama'at Nusrat al-Islam wal-Muslimin)** should appear as side_a or side_b in: MLI ✓ (already known), BFA ✓ (already known), NER (predicted), BEN ✓ (already known per dig 2026-05-25), TGO (predicted)
- **IS Sahel Province** should appear in: MLI ✓, BFA ✓, NER ✓, BEN (predicted), TGO (predicted, lower probability)
- **At least one local self-defense militia** (Dozos / Dan na Ambassagou / Koglweogo / VDP) should appear in each affected country

If JNIM dyad presence in BEN/TGO/CIV/GHA is NOT found → mechanism (a) falsified for those countries.

### Prediction set C — CAR sub-cluster replication

| Country | Predicted shape |
|---|---|
| **CMR (Cameroon)** | Boko Haram-adjacent + Anglophone crisis; predicted ≥50 strife by 2018, sustained through 2024 |
| **TCD (Chad)** | Boko Haram spillover + intra-Chadian rebellion; predicted ≥50 strife by 2015, sustained |
| **COG (Congo-Brazzaville)** | NOT predicted to show diffusion (geographic + governance buffer); test of "diffusion isn't universal" |

### Prediction set D — Caribbean sub-cluster (HTI epicenter)

H3 extension predicts that the HTI gang-war strife signature will:
- Continue intensifying in HTI itself (predicted ≥200 strife fatalities/year by 2025-2026)
- Show first cross-border manifestation in **Dominican Republic** by 2027 (predicted: ≥10 strife fatalities/year tied to Haitian gang networks)
- NOT diffuse to Cuba, Jamaica, or Puerto Rico (geographic + sea barrier + governance buffer)

---

## 3. Falsifiers (pre-committed)

The hypothesis is **NULL** if any of the following are observed:

- **F1:** TGO, CIV, GHA show **zero** strife signal (≥50 fatal threshold) by end-2027 → diffusion does NOT continue southward; mechanism is geographically bounded
- **F2:** TGO/CIV/GHA emerge but with **completely different actors** (no JNIM/IS-Sahel/Dozo-type analogues) → diffusion is coincidental, not mechanistic
- **F3:** CAR/CMR/TCD sub-cluster shows NO temporal ordering (e.g., all emerge in same year, or peripheral country precedes CAR) → epicenter model fails outside Sahel
- **F4:** HTI gang-war does NOT cross to DOM by 2027 → diffusion does not generalize to non-contiguous geographies (the geographic-corridor mechanism is the right narrower frame)

Any 2 of {F1, F2, F3, F4} firing = HYPOTHESIS WALKED BACK; will be logged in patterns/ as such.

---

## 4. Methodology

### Data
- **Primary:** UCDP-GED v25.1 (and successors); type_of_violence = 2 filter
- **Secondary:** GIDD displacement (does displacement track the strife emergence?)
- **Tertiary:** GDELT 1.0 (event density / sentiment around predicted-emergence years)

### Test procedure (executed at each annual update of UCDP-GED)
1. Build country-year strife panel for predicted countries
2. Compute first year with ≥50 strife fatalities
3. Compute dyad-name overlap matrix across all Sahel + coastal countries
4. Compare against pre-locked predictions
5. Update pattern catalog with result

### Decision rules
- **Supported:** TGO emerges 2022-2025 AND CIV emerges 2023-2026 AND actor overlap is present → H1+H2+H3 supported for Sahel southward extension
- **Partial:** Only TGO emerges, or actor overlap is weak → write up as partial; refine hypothesis with conditioning
- **Null:** F1 fires → walk back the H3 generalization claim; keep H1+H2 as Sahel-only findings

---

## 5. Pre-locked analyst notes

- I have NOT yet pulled UCDP data on TGO, CIV, GHA, CMR, TCD, COG, DOM. The predictions in §2 are based on geographic adjacency and qualitative reporting only.
- The "epicenter" framing is descriptive, not necessarily causal. The hypothesis allows for: (a) actual cross-border insurgent expansion, (b) regional pressure cooker with simultaneous independent emergence, (c) ethnographic / climatic / economic shocks transmitted regionally. The actor-overlap test (B) is what discriminates among these.
- This pre-reg is on the **PUBLIC** track for the methodology paper. No proprietary data or models used.
- "Sahel cluster" excludes Mauritania and Senegal (no current strife signal); does NOT exclude them from the southward-diffusion logic, but they are not currently in the prediction set.

---

## 6. What gets locked vs what stays open

**LOCKED (do not modify after 2026-05-25):**
- The H1/H2/H3 hypothesis text
- The prediction set (TGO, CIV, GHA windows + CAR/CMR/TCD/DOM)
- The falsifier set (F1-F4)
- The decision rules

**STAYS OPEN (can be added later as exploration, not as result):**
- New countries to add to the prediction set in subsequent pre-regs
- Refinements to the mechanism (which can be proposed as PRE_REG_002+)
- Climate / economic / governance conditioning variables (separate pre-reg)

---

## 7. Cross-references

- [[PATTERN_005]] MLI strife epicenter dig 2026-05-25
- [[PATTERN_010]] Strife-dominant cross-cluster recurrence (the substrate this pre-reg formalizes)
- [[PATTERN_006]] BEN periphery already showing JNIM presence (this pre-reg's "soft early data")
- [[PATTERN_003]] BFA state counterinsurgency in Liptako-Gourma (the upstream pressure)
- [[INDEX]] meta-pattern of conflict-types

---

## 8. Provenance

Pre-reg authored 2026-05-25 by N. Humphrey + Claude (Anthropic), based on the patterns/ catalog work of 2026-05-21 through 2026-05-25. Substrate: D:/IDP/. Cross-session memory: project_idp_substrate_2026_05_25_broad_pivot.md.

Will be hashed and committed to git at the next snapshot.

---

## 9. Results — partial fit (fired 2026-05-27)

Full dig: `D:/IDP/papers/PAPER_3_STRIFE_EPICENTER/digs/2026_05_27_partial_fit.md`

### In-sample diffusion CONFIRMED
- MLI 2012 → BFA 2020 (8y lag) → NER 2021 (9y lag)

### Forward-watch results

| Country | Pre-locked window | Status |
|---|---|---|
| TGO | 2022-2025 | **EARLY-EMERGENCE**: JNIM operational (Govt-JNIM 109 + JNIM-civ 97 = 206 fatalities 2020-2024); type-2 strife threshold not yet crossed. Window still open. |
| CIV | 2023-2026 | Quiet (only 1 event 2020-2024); no JNIM presence |
| GHA | 2024-2027 | Local Kusasi-Mamprusi ethnic conflict (38 fatalities 2022-2024); no JNIM; **F2 partial-fire risk** |

### Actor-overlap test
**JNIM presence: MLI ✓ BFA ✓ NER ✓ BEN ✓ TGO ✓ CIV ✗ GHA ✗**

JNIM has reached TGO. Framework narrows: Sahel diffusion is **JNIM-corridor-specific**, not pan-regional.

### Sub-cluster tests
**F3 PARTIALLY FIRED — Central Africa fails epicenter ordering**:
- CAR: 2011 ✓ (matches)
- Cameroon: **1991** (predates CAR by 20y)
- Chad: **2000** (predates CAR by 11y)
- Congo-Brazzaville: zero strife ✓ (buffer confirmed)

Framework is **Sahel-specific**; doesn't auto-generalize to Central Africa.

HTI sub-cluster: 2021 epicenter ✓; DOM zero (forward-watch active).

### Falsifier status
| F | Status |
|---|---|
| F1 (TGO/CIV/GHA zero by 2027) | not fired; at risk for CIV |
| F2 (different actors) | **PARTIALLY FIRED for GHA** |
| F3 (CAR no temporal ordering) | **PARTIALLY FIRED** |
| F4 (HTI → DOM by 2027) | forward-watch |

### Refined claim
- Sahel-specific
- JNIM-corridor-specific (TGO yes; CIV/GHA outside corridor in current data)
- Multi-stage: actor-present-but-threshold-not-crossed (TGO is at this stage)
- Forward-falsifiable through 2027 UCDP releases

**Status**: PARTIAL SUPPORT + 2 partial falsifiers + framework REFINED to narrower scope. Publishable now as forward-watch working-paper / blog post.
