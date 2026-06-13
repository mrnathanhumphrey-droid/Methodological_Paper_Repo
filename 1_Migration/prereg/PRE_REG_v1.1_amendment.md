# Pre-Registration v1.1 — Amendment to v1.0 (RMD-SRC US Internal Migration)

**Amends:** PRE_REG_v1.0_RMD_SRC_migration.md (locked 2026-05-27)
**Authored:** 2026-05-27
**Status:** LOCKED v1.1-final, 2026-05-27. A1 and A2 both accepted as drafted. Supersedes the named sections of v1.0 (see "Sections updated" table). v1.0 remains the immutable original anchor; this doc is the governing amendment. Further changes require a v1.2 amendment under the same diagnostic-driven standard.

## Why this amendment is honest (not result-driven)

Both ambiguities were exposed by **tracing the data's structure**, before any moment-flow statistic on outcomes was computed (the ℙ₀ partition isn't even built yet):

- **A1** surfaced while reasoning through implementation: §2.5's phrase "PCA fit once on 2010 baseline PUMA-year panel" has no clean referent, because 2010-vintage PUMAs only exist in ACS 2012+. There is no 2010 PUMA-year panel in our extract.
- **A2** surfaced when we pulled both TIGER vintages: the analysis window straddles the decennial PUMA boundary redraw. ACS 2012–2021 uses 2010-vintage PUMAs; ACS 2022–2023 uses 2020-vintage. The v1.0 train/holdout boundary (2019|2020) sits inside the 2010-vintage era, but the holdout (2020–2023) crosses into 2020-vintage at 2022.

Neither trigger involved inspecting an outcome. This is the data-distribution-exposed class of amendment, logged per the project's amendment-integrity standard.

---

## Amendment A1 — PCA opportunity-index baseline (supersedes §2.5 ¶1 and §2.6)

**v1.0 text (ambiguous):** "PCA fit once on 2010 baseline PUMA-year panel, applied frozen to all (PUMA, year) cells."

**v1.1 resolution (LOCKED choice):** Fit the opportunity-index PCA **once on the pooled training-window PUMA-year panel** (years per A2 below), freeze the loadings, and apply them unchanged to every (PUMA, year) cell in both training and holdout windows.

Rationale:
- The original intent of "2010 baseline" was a *fixed reference independent of per-event computation*. A pooled training-window fit achieves that intent and is well-powered (~2,300 PUMAs × N training years ≈ 1.4×10⁴ PUMA-year observations for a 4-variable PCA).
- Fitting on the **training window only** keeps the gradient-field definition out of the holdout, so RMD_F4 (predictive transfer) is not contaminated by holdout information leaking into the opportunity index.
- PCA loadings are on the four socioeconomic **variables** (median household income, emp/pop ratio 25–54, BA+ share, affordability = median income / median rent), not on geography. They therefore transfer across the PUMA vintage redraw without modification — each year's PUMA aggregates are projected onto the frozen loadings regardless of boundary vintage.

Rejected:
- Pool PCA across *all* years incl. holdout → F4 contamination.
- Separate external 2010 baseline (ACS 5-yr 2008–2012) → mixed PUMA vintage (2008–2011 are 2000-vintage), defeats the clean design.

---

## Amendment A2 — PUMA vintage crossing and the train/holdout split (supersedes §2.3, and §3.7 windows)

**The constraint:** 2010-vintage PUMAs cover ACS 2012–2021 (10 yrs); 2020-vintage cover ACS 2022–2023 (2 yrs). No off-the-shelf Census puma10↔puma20 crosswalk exists (only tract-level 2010↔2020 relationship files, from which a PUMA crosswalk would need population-weighted allocation — itself an error source).

**v1.1 resolution (RECOMMENDED — confirm before lock):** Restrict the **locked v1.0 pipeline to a single PUMA vintage** (2010-vintage, ACS 2012–2021), and shift the split:

- **Training window: 2012–2017** (6 years, 2010-vintage)
- **Holdout window: 2018–2021** (4 years, 2010-vintage)
- **2022–2023 (2020-vintage): reserved as an OPTIONAL cross-vintage extension test**, reported separately and NOT part of the v1.0/v1.1 locked falsifiers.

Why this split:
1. **Single geographic vintage** across the entire locked analysis → distance and density observables are computed on one consistent PUMA universe; no boundary-redraw/behavior confound; no crosswalk allocation error.
2. **4 holdout years** preserves enough time points for the §3.3 OLS-slope regime classification and the §3.7 κ agreement test. (A 2012–2019 / 2020–2021 split would leave only 2 holdout points — a single difference — too thin to classify a holdout trajectory regime.)
3. **Generalization test is arguably richer:** the 2018–2021 holdout spans normal continuation (2018–2019) plus the COVID shock (2020–2021), testing whether training-period leaf classifications survive both a calm extrapolation and a shock — a stronger F4 than a pure-COVID holdout.
4. **2022–2023 is not wasted:** it becomes a bonus "does structure transfer across a geography redraw?" test, outside the locked claims.

Cost acknowledged: loses the crisp "pre-COVID train / COVID-era holdout" framing of v1.0 §2.3; loses the 2 most-recent years from the locked falsifiers.

### Alternatives considered and rejected

- **Option X — harmonize geography via puma10↔puma20 crosswalk, keep 2012–2019/2020–2023.** Rejected: no direct Census crosswalk; building one from tract relationship files injects population-allocation measurement error into exactly the holdout years that F4 evaluates, confounding the overfit test with crosswalk noise.
- **Option Z — keep v1.0 windows, compute observables on each year's native vintage, add a structural-break diagnostic at 2021→2022.** Rejected: places a known geographic discontinuity at a single seam inside the holdout; the break-diagnostic cannot cleanly separate redraw-induced jumps from genuine behavioral regime change at that seam.
- **Option (2012–2019 train / 2020–2021 holdout, single vintage, drop 2022–2023).** Rejected: 2-year holdout = 1 difference per leaf, insufficient for trajectory-regime classification and κ.

---

## Sections updated by this amendment

| Section | v1.0 | v1.1 |
|---|---|---|
| §2.3 training window | 2012–2019 | 2012–2017 |
| §2.3 holdout window | 2020–2023 | 2018–2021 |
| §2.3 / §2.5 PCA fit window | "2010 baseline" (undefined) | pooled 2012–2017 training panel, frozen |
| §2.5 / §2.2 geography scope | 2012–2023, vintage unaddressed | locked analysis = 2010-vintage only (2012–2021); 2022–2023 optional extension |
| §3.3 slope window | t = 2012…2019 | t = 2012…2017 |
| §3.7 holdout recompute | 2020–2023 | 2018–2021 |

Unchanged: all structural commitments (§1), falsifier thresholds (F1=80/F2=50/F3=30/F4 κ≥0.4 + accuracy sanity), regime taxonomy, decomposition order 4a→4b→4c, ℙ₀ method (Option A cross-product), observable operationalizations (PCA index / log-distance / log-density), event definition, min cell size n_c≥50, reporting commitments.

---

## Sign-off needed

1. **A1** — PCA on pooled training-window panel, frozen, training-window-only. (Recommended; low controversy.)
2. **A2** — single-vintage restriction + 2012–2017 train / 2018–2021 holdout + 2022–2023 as optional extension. (The real fork — confirm or pick X/Z/other.)

Reply "lock v1.1" to accept both as drafted, or call out changes. On lock I update the v1.0 header to reference v1.1 as the governing amendment and we proceed to Step 0.
