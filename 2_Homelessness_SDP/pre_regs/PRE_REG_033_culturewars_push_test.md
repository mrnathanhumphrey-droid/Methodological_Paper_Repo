# Pre-Registration 033 — Culture-Wars / Social-Change Push Test

**ID:** PRE_REG_033
**Locked:** 2026-05-28
**Substrate:** PRE_REG_029/031 (rent is the displacement funnel; structure explains the push net of climate) + pull/push system frame
**Status:** LOCKED — design + thresholds + falsifiers pre-committed BEFORE building the culture block and BEFORE any coefficient inspection.

**PI prior (stated):** the culture-wars / changing-culture explanation of the homelessness push **does NOT exist** — the push is economic (rent), not cultural. This pre-reg builds the FALSIFIABLE test so the data can confirm OR overturn that prior. Neither the null nor the positive is assumed; both are reported verbatim.

---

## 0. The claim under test

Culture-war framings of homelessness assert the "push" is driven by a **changing landscape/society/culture**, not housing economics:
- **CW1 (political permissiveness):** homelessness is higher where the *political culture* is progressive/permissive ("blue cities enable/tolerate it; red states criminalize it").
- **CW2 (fraying social fabric):** homelessness is higher where family structure has frayed (single-person households, low marriage), social capital is low, and religiosity/charity has declined.
- **CW3 (dynamic — "changing culture pushes"):** places whose culture *changed* (became more progressive / more socially fragmented / more secular) over 2012–2024 saw homelessness *rise*.

The discriminating test against the economic explanation: **does a culture block explain homelessness NET OF RENT?** If rent already explains it and culture adds ~nothing, the culture-wars push is an artifact of culture correlating with high-cost metros.

---

## 1. Hypotheses

**H1 (cross-sectional, culture net of rent):** A culture/politics/social-fabric block explains CoC homelessness *after* rent (+ income) is partialled out.

**H2 (dynamic, changing culture pushes):** Within CoCs over 2012–2024, *change* in culture (Δ partisan lean, Δ family structure, Δ religiosity) predicts *change* in homelessness, net of Δrent.

**H3 (which culture sub-axis, if any):** if culture matters, is it political-permissiveness (CW1), social-fabric (CW2), or neither?

---

## 2. Pre-locked thresholds + FALSIFIERS

| Hyp | "Culture-wars push EXISTS" (would surprise PI) | FALSIFIED (confirms PI prior) |
|---|---|---|
| **H1** | culture block ΔLOO-R² over (rent+income) ≥ 0.10, ≥1 culture var p<0.05 correct sign | **F1**: ΔR² < 0.05 → culture adds nothing over rent; push is economic not cultural |
| **H2** | ≥1 Δculture coef p<0.05 correct sign in within-CoC FE | **F2**: Δculture coefs null → changing culture does NOT push |
| **H3** | a coherent culture sub-axis carries it | (descriptive) |

"Correct sign" per culture-war claim: more-Democratic → more homeless; more single-person-HH → more; lower social capital → more; lower religiosity → more. Bootstrap/clustered SE. Thresholds not movable post-fit.

---

## 3. Culture block (the test variables)

- **Political culture (CW1):** county presidential Democratic vote share (MIT Election Lab), level (2020) + change (2012→2020). → CoC pop-weighted.
- **Family/social structure (CW2):** ACS — % single-person households (B11001/B11016), % never-married, % living alone; level + 2012→2024 change.
- **Social capital (CW2):** county social capital index (Rupasingha/Goetz or JEC Social Capital Project). Level.
- **Religiosity (CW2):** US Religion Census (ARDA) county adherence rate, 2010 + 2020 (change).
- **Deaths-of-despair context:** CDC drug-death rate (already have) — the "disorder/addiction culture" proxy.

**Controls (the economic funnel, partialled first):** median rent (ACS), median income. Climate excluded (noise for level, per 029 retest).

**Outcome:** homeless_per_10k (CoC); robustness unsheltered_per_10k.

---

## 4. Pre-conditions
1. Culture block coverage ≥150 CoCs (election + ACS family + ≥1 of social-capital/religiosity).
2. Dynamic panel: ≥120 CoCs with culture-change + rent-change + homelessness-change 2012→2024.
3. Multicollinearity check: partisan-lean vs rent |ρ|<0.85 (else they can't be separated — report).
Failures redlined.

## 5. Robustness (ROBUST n/4)
1. Cross-section vs within-CoC dynamic
2. Outcome per-10k vs unsheltered-per-10k
3. With vs without top metros (NYC/LA/SF — Dem + high-rent + high-homeless)
4. Political-culture-only vs full culture block (does politics survive social-fabric controls?)

## 6. Causal / honesty guards
- Correlational; "consistent with / not" the culture-wars claim, never proof.
- **The key confound IS the test:** progressive politics correlates with high-cost coastal metros. Partialling rent is precisely what separates "it's the politics/culture" from "it's the cost." If the political coefficient vanishes net of rent, the culture-war claim was a rent artifact.
- Report the null verbatim if it falsifies (it likely will, per PI prior) — do NOT manufacture a culture effect; equally, do NOT suppress one if it survives.
- Reverse causality: homelessness could shift local politics/social fabric; dynamic + lagged mitigates; flagged.

## 7. Cross-references
PRE_REG_029/031 (rent funnel), pull/push system frame, P7 SDP. Food-scarcity edge handled separately by PI.

## 8. Provenance
Locked 2026-05-28 before culture block built + before coefficient inspection. First fit after §4 pre-conditions.
