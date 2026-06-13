# H_SHOCK_AMPLIFICATION — Isolated Pre-Commit Specification

**Substrate:** 9 of Paper 6 methodology corpus (IDP cross-country study).
**Pre-reg parent doc:** `notes/displacement_research_design.md` v1.
**This file:** Isolated pre-commit for the load-bearing hypothesis,
H_SHOCK_AMPLIFICATION. Locked here separately from the parent design
doc to make the framing-language constraint immutable.

---

## Framing language (LOCKED, verbatim)

The hypothesis statement uses the phrase:

> **"associated with differential displacement intensification under conflict shock"**

NOT "causes." This study does NOT make a causal claim. The mechanism by
which historical-atrocity-polygon membership might produce modern
displacement amplification is not identified here; observed association
is what the model tests.

This framing constraint applies to:

- The hypothesis statement (§6 of `displacement_research_design.md`)
- The README headline (post-Phase 4)
- The disposition reading verdicts (§6 of design doc)
- Any abstract, summary, or external communication of the substrate-9 finding

Any deviation from this language — substituting "causes," "produces,"
"leads to," "explains," or other causal connectors in their place — is a
pre-reg deviation and must be redlined into `notes/pre_reg_redline.md`
v1→v2 before publication.

---

## Operationalization

The load-bearing coefficient is `beta_interaction` in the v0_2 / v0_3 /
v0_4 Stan models (specified in §4.1 of `displacement_research_design.md`):

```
beta_interaction * (shock_indicator * in_historical_polygon)
```

Where:

- `shock_indicator` is a binary indicator: did admin-2 × year exceed the
  within-country 80th percentile of fatality count? (Threshold LOCKED;
  not data-tuned.)
- `in_historical_polygon` is a binary indicator: is the admin-2 (geometrically)
  within the country's Stage-A historical-atrocity polygon? (Computed by
  spatial intersection on the digitized polygon vs GADM admin-2 boundary.)
- `beta_interaction` is the differential amplification of displacement
  rate when both conditions are met, beyond the additive shock effect
  and beyond the additive polygon effect.

The coefficient is interpreted on the natural log scale (negative binomial
link). A positive `beta_interaction` means: under conflict shock, admin-2
units within the historical-atrocity polygon experience displacement at
a *multiplicatively higher* rate than admin-2 units outside the polygon
experience under the same shock conditions.

This is an INTERACTION coefficient, not a main effect. The main-effect
shock coefficient (`beta_shock`) and the main-effect polygon coefficient
(`alpha_polygon`) are simultaneously estimated and are reported alongside
`beta_interaction`. Interpretation of the interaction requires reading
all three.

---

## Confirmation / falsification thresholds (LOCKED)

- **Confirmation:** 95% posterior CI on `beta_interaction` excludes zero
  on the POSITIVE side in v0_2 (after polygon inclusion). Replicates in
  v0_3 AND v0_4. ROBUST on ≥ 3 of 4 §5 robustness axes.

- **Falsification:** 95% CI spans zero in v0_2. OR, replicating in v0_2
  but failing on fewer than 3 of 4 §5 axes.

- **Mixed:** Replicates in v0_2 but not v0_3 or v0_4. OR, robust on 2 of
  4 axes. Report verbatim per pre-reg discipline; do NOT pick the
  prettiest narrative.

The 95% CI threshold is the locked decision rule. It is not movable
post-fit. The 3-of-4 axes rule is the locked robustness rule and is not
movable post-fit.

---

## Cross-country portability sub-test

A SUPPORTED H_SHOCK_AMPLIFICATION at the cross-country pooled level
requires a separate check: does the direction hold per country?

H_CROSS_COUNTRY_PORTABILITY (§6 of design doc): all 4 country-specific
`beta_interaction` estimates land on the positive side of zero.

If H_SHOCK_AMPLIFICATION is SUPPORTED at pooled level but
H_CROSS_COUNTRY_PORTABILITY fails (e.g., sign reversal in DRC), the
substrate-9 finding is reported as **country-specific**, not
cross-country. The locked language for that case:

> "Historical-atrocity-polygon membership is associated with differential
> displacement intensification under conflict shock in [country list],
> but not in [country list]. Cross-country portability of the substrate-9
> finding is not supported."

---

## Pre-reg discipline statement

This specification is committed at the initial git commit alongside the
parent design doc. Both files together constitute the pre-registration of
the load-bearing hypothesis.

The locked framing-language constraint exists because the alternative —
publishing a "causes" claim after a SUPPORTED interaction in observational
panel data — would constitute a stronger inferential claim than the
study design supports. Pre-registering the language NOW makes it
unmodifiable post-hoc without leaving a public redline trail.

This is the substrate-9 equivalent of gun-violence's "This is statistical
evidence of systemic racism" README headline (cite: gun_violence README
under "§6 disposition reading"). That headline language was pre-registered
in the gun-violence design doc PRIOR to v0_4 fit landing. The IDP
substrate locks "associated with" similarly, before any fit lands.

---

## Sign-off

- **Author:** Nathan Humphrey
- **Date locked:** 2026-05-17
- **Initial commit hash:** TBD (set at first git commit)
- **Spec hash:** TBD (SHA-256 of this file at commit time)
