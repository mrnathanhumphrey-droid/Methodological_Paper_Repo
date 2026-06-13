# Internal Displacement Cross-Country Study — Research Design

**Working title:** Historical Atrocity Geography and Differential Displacement Response to Contemporary Conflict Shocks Across Four IDP Substrates

**Author:** Nathan Humphrey

**Status:** Pre-registration v2 (effective 2026-05-17). Entry 001 (ACLED → GDELT cross-source substitution) + Entry 002 (Stage-A polygon interpretation locks + substrate framing clarification + DRC source-list amendment) both committed to `notes/pre_reg_redline.md`. Original v1 committed at `dd3f0ec`. No Stan fits yet. No rate-level outcome inspection.

**Pipeline position:** Substrate 9 of the Paper 6 methodology corpus. Mirrors gun-violence (substrate 6) and food-deserts (substrate 8) discipline: commit-hash + content-hash pre-reg lock, locked falsifier + walk-back protocol, public commit chain, honest negative reporting.

---

## §0. Pre-registration commitments

This document is the pre-registration. Changes to anything below after data
analysis begins must be (a) explicitly noted as post-hoc, (b) justified, (c)
reported in `notes/pre_reg_redline.md` alongside the original specification.

The design specifies:

- Substrate definition (§1)
- Unit of analysis (§2)
- Levers / covariates (§3)
- Model class + prior structure (§4)
- Robustness axes (§5)
- Pre-registered hypotheses with quantitative falsification criteria (§6)
- Pre-conditions that must pass before fitting (§7)
- Data sources (§8)
- Walk-back protocol per disposition (§9)
- Phased execution timeline (§10)
- Repository structure (§11)

No looking at displacement outcome data (DTM rates) until all of the above is
locked AND the four pre-conditions have run. Pre-cond results documented in
`notes/precond_*_report.md`; failures redlined in `notes/pre_reg_redline.md`
v1→v2.

---

## §1. Substrate definition

The substrate is **internal displacement geography across four cross-country IDP
contexts**:

- **Colombia** — long-duration armed conflict 1964–present; FARC, ELN, paramilitary,
  cocaine-economy linkages.
- **Sudan** — Darfur conflict 2003–present; pre-2011 South Sudan separation;
  post-2023 RSF–SAF war.
- **Democratic Republic of the Congo** — eastern DRC ethnic conflict 1996–present;
  Rwandan-genocide spillover; M23 cycles.
- **Yemen** — civil war 2014–present; Houthi vs Saudi-coalition / Hadi govt;
  pre-2014 Houthi conflicts 2004–2010.

Each context has:

1. A **Stage A historical-atrocity polygon** documented from archival sources
   (specified per country in §1.1) — defines historically-targeted geography.
2. A **Stage B contemporary-conflict-shock series** from UCDP + ACLED event
   data — defines the current shock.
3. A **DTM displacement-rate time series** at admin-unit level — defines the
   outcome.

**Substantive question (v2 framing, per redline Entry 002-E):**

The substrate-9 hypothesis tests **long-term protracted displacement
geography**, not new-onset displacement geography. Per PI clarification
(2026-05-17): modern IDP is multi-generational protracted displacement
(Sudan, DRC, Colombia, Palestine all exemplify this) — the chronic IDP
burden geography was established by founding atrocity events decades
ago, and is periodically compounded by contemporary conflict shocks. The
Stage-A polygons mark where the chronic burden lives; the contemporary
shock is the marginal event compounding on that geography. This framing
aligns substrate-9 with the UNHCR/IDMC "protracted-displacement-situation"
definition (≥ 25,000 IDPs displaced for ≥ 5 consecutive years).

Under this framing, the substantive question is: do conflict shocks
produce differentially-intensified displacement response in admin-2
units within a country's founding-atrocity polygon — geographies that
have hosted protracted IDP populations since the historical event —
beyond what the shock predicts in non-polygon units? The framing is
correlational. Per Phase 0 locked language: **"associated with
differential displacement intensification under conflict shock"** — NOT
"causes." The shock-amplification specification is isolated in
`notes/shock_amplification_specification.md`.

### §1.1 Stage A historical polygons (4, LOCKED at redline Entry 002)

| Country | Polygon | Historical period | Source materials |
|---|---|---|---|
| Colombia | La Violencia mortality concentration zones | 1948–1958 (Bogotazo to National Front; extends to 1964) | CNMH *¡Basta Ya!* (2013) Map 2; CINEP Noche y Niebla; Guzmán Campos et al. (1962); Sánchez & Meertens (2001); Roldán (2002) |
| Sudan | Fur dar (pre-1994) | Pre-1994 historical Fur Sultanate / Dar Fur dar boundary | Daly 2007 *Darfur's Sorrow* plates II + III; De Waal 2005 Map A1; Sudan Open Archive; Anglo-Egyptian Sudan Survey 1928 |
| DRC | Kasai Luba expulsion zone | 1959–1965 (Katangan secession era + Lulua-Luba ethnic violence) | Young & Turner (1985); Lemarchand (1964); De Villers (2002); Stearns (2011); CRDA UCL Louvain colonial archives |
| Yemen | Six Wars operational extent | 2004–2010 (Six Wars Houthi insurgency) | ICG MER N°86 (2009) + N°114 (2011); Salisbury 2015 Chatham House; Yemen Polling Center 2012; UCDP-GED 2004-2010 |

All four polygon interpretations are PI-confirmed per redline Entry 002
(2026-05-17). The Sudan polygon is the same as v1 (unambiguous from the
start). The Colombia, DRC, and Yemen polygons were locked from
placeholder interpretations to PI-confirmed ones.

The Colombia La Violencia polygon and pre-1994 Fur dar polygon are the
slowest-to-digitize components (2-3 days each). The DRC Kasai 1959-1965
polygon also requires manual academic-history coding for its
`historical_atrocity_count` covariate per §3.2 amendment (UCDP and EOSV
data both begin at 1989, so neither covers the Kasai 1959-1965 window;
manual coding from Young & Turner + Lemarchand + Stearns + CRDA replaces
the event-database extraction). Provenance.md files in
`historical_polygons/*/` document the digitization plan + source archive
citations BEFORE the polygons are drawn.

---

## §2. Unit of analysis

**Primary unit:** GADM admin-2 polygon (county / municipality / governorate)
within each country. Each row of the analytic panel is one admin-2 × year.

| Country | GADM admin-2 equivalent | N admin-2 units (approx) |
|---|---|---|
| Colombia | Municipio | ~1,120 |
| Sudan | Locality (mahaliya) | ~190 |
| DRC | Territoire | ~145 |
| Yemen | Mudīriyah (district) | ~333 |

**Time unit:** annual; panel runs 2014–2024 (10 years) for the contemporary
shock window. Stage A historical events are NOT annualized — they enter the
model as a polygon-level binary or atrocity-count covariate.

**Outcome:** DTM-reported IDPs per admin-2 per year, normalized by admin-2
population (per-1k-pop displacement rate). Population denominators from the
most recent national census, INS estimates, or DTM-internal population frames;
specific source per country flagged in `data/dtm/_population_provenance.md`.

**Outcome inspection rule:** the outcome variable is NOT loaded, summarized,
or plotted before pre-cond scripts pass AND the v1 commit timestamp is
established. Only metadata-level row counts and structural checks (column
schema, year coverage, admin-2 coverage) are inspected.

---

## §3. Levers / covariates

### §3.1 Outcome
- `idps_per_1k_pop_year` — DTM-reported IDPs per admin-2 × year, normalized
  by population.

### §3.2 Historical atrocity geography (Stage A)
- `historical_atrocity_polygon` — binary indicator: is the admin-2 (geometrically)
  within the country's Stage A polygon? Computed by spatial intersection on
  the digitized polygon vs GADM admin-2 boundary.
- `historical_atrocity_count` — total documented atrocity events within the
  admin-2's historical window per country (PER COUNTRY SOURCE, LOCKED at
  redline Entry 002-C):
  - Colombia: CINEP Noche y Niebla per-municipio counts, 1948–1965 window
    (La Violencia core + 7-year trailing per CNMH ¡Basta Ya! documentation)
  - Sudan: EOSV 2003–2010 (LIMITED to within EOSV coverage; EOSV ends 2013;
    post-2013 ethnic-targeting events fold into `current_conflict_intensity`,
    NOT into atrocity-count). PI-confirmed at redline Entry 002-F.
  - **DRC (redline Entry 002-C amendment):** manual academic-history coding
    for the 1959-1965 Kasai Luba expulsion window. Primary sources: Young
    & Turner (1985) *Rise and Decline of the Zairian State*; Lemarchand
    (1964) *Political Awakening in the Belgian Congo*; De Villers (2002)
    *Tribu et État au Zaïre*; Stearns (2011) *Dancing in the Glory of
    Monsters*; CRDA UCL Louvain Belgian colonial archives. UCDP/EOSV do
    NOT cover this window (both start at 1989). Output:
    `data/atrocity_counts/drc_kasai_atrocity_count.csv`. Methodological
    asymmetry caveat reported in §6 disposition reading: DRC's
    historical_atrocity_count is academic-secondary-source coded;
    Colombia/Sudan/Yemen use primary-source event-database extraction.
  - Yemen: UCDP-GED filtered to Yemen events 2004-2010, side_a/side_b
    contains Houthi or Government, type_of_violence ∈ {1, 3}. Per
    mudiriyah via ActionGeo spatial join to GADM admin-2.

### §3.3 Contemporary conflict shock (Stage B)
- `current_conflict_intensity` — UCDP-GED fatality count within admin-2 × year
- `acled_event_count` — ACLED battle + violence-against-civilians count within
  admin-2 × year (cross-source validation of conflict intensity)
- `shock_indicator` — binary: did admin-2 × year exceed within-country 80th
  percentile of fatality count? (locked threshold; not data-tuned)

### §3.4 Demographic + structural covariates
- `population_admin2` — population, from country's most recent national
  census or INS estimates
- `pct_indigenous` (Colombia, DRC), `pct_ethnic_group_X` (Sudan, Yemen) —
  proxies for current ethnic composition where data permits
- `terrain_ruggedness` — Nunn–Puga terrain ruggedness index per admin-2
  (GADM-joined)
- `urban_rural` — binary: admin-2 contains ≥1 city of 50k+ from Africapolis /
  GHS-SMOD
- `distance_to_border_km` — for cross-border-displacement context

### §3.5 Country fixed effects
- `country_id` — categorical {Colombia, Sudan, DRC, Yemen}.

### §3.6 Pre-reg lock on lever inclusion
Any covariate not listed above cannot be added in Phase 1+ without a
pre-reg redline entry. Added covariates must be (a) noted post-hoc, (b)
justified, (c) reported alongside the locked specification.

---

## §4. Model class + prior structure

### §4.1 Model

Hierarchical Bayesian negative-binomial regression with partial pooling across
country × historical-polygon-status cells:

```
idps_count ~ NegBinom(mean = exp(eta), phi)
eta = log(population_admin2)
    + alpha_country
    + alpha_polygon[country, in_historical_polygon]
    + beta_shock * shock_indicator
    + beta_interaction * (shock_indicator * in_historical_polygon)
    + beta_atrocity_count * log1p(historical_atrocity_count)
    + beta_terrain * terrain_ruggedness
    + beta_urban * urban_rural
    + beta_pct_ethnic_group * pct_ethnic_group_X
    + beta_distance_border * distance_to_border_km / 100
```

`alpha_polygon` has the hierarchical structure: nested within country, with
the partial-pool prior shrinking each country × polygon-status combination
toward the country-level mean.

**The load-bearing coefficient is `beta_interaction`** — the differential
amplification of displacement under shock IF the admin-2 is within the
historical-atrocity polygon, after controlling for shock intensity, history
count, and structural covariates.

Phi (negbin dispersion) is fit as a free hyperparameter per country (4 phi
values).

### §4.2 Priors

- `alpha_country` ~ Normal(0, 2)
- `alpha_polygon[c, in]` ~ Normal(alpha_country[c], sigma_alpha_polygon)
- `sigma_alpha_polygon` ~ Half-Normal(0, 1)
- `beta_shock` ~ Normal(0, 1)
- `beta_interaction` ~ Normal(0, 0.5)  -- tighter prior on the load-bearing
  interaction to encode genuine skepticism
- All other slopes ~ Normal(0, 1)
- `phi` ~ Half-Normal(0, 10) per country

### §4.3 Estimation

Stan / CmdStan via PyStan or cmdstanpy. Default sampler (NUTS, adapt_delta
0.95 to handle hierarchical funnel). 4 chains × 2000 warmup × 2000 sampling.
R-hat convergence threshold < 1.01.

### §4.4 Stan model files

- `analysis/v0_1_baseline.stan` — country FE + shock + interaction, no
  historical polygon
- `analysis/v0_2_polygon.stan` — adds historical-atrocity polygon binary +
  interaction
- `analysis/v0_3_atrocity_count.stan` — adds log1p(atrocity_count)
- `analysis/v0_4_full.stan` — adds all §3.4 covariates

Phase 0 produces NO Stan fits. Phase 1 builds and fits v0_1; Phase 2 v0_2;
Phase 3 v0_3; Phase 4 v0_4 + robustness sensitivities.

---

## §5. Robustness axes (4 axes, mirrors gun-violence v0.5 self-replication structure)

The gun-violence study used 3 axes (5-fold sample, Tier-3 source swap, BG
geography refinement). IDP adds a 4th given its cross-country structure:

1. **Axis 1 — Cross-source ACLED vs UCDP-GED.** Re-fit using ACLED event counts
   substituted for UCDP-GED fatality counts in the shock indicator. Same
   80th-percentile threshold rule.
2. **Axis 2 — 5-fold admin-2 cross-validation.** SEED 20260517. Five random
   admin-2 folds per country. Refit on 4/5 train per fold. Per-finding pass
   rule: ≥4 of 5 folds CI clean on the correct side of zero.
3. **Axis 3 — Pre-2020 vs Post-2020 temporal split.** Pre-2020 (2014-2019)
   vs Post-2020 (2020-2024) panel splits. Tests whether the historical-
   amplification signal is stable across pre-COVID vs post-COVID conflict
   regimes.
4. **Axis 4 — Polygon-boundary sensitivity.** For each Stage-A polygon, fit
   under the original boundary + a ±10km buffer expansion + a ±10km erosion.
   Tests robustness to digitization choices.

A finding is reported as ROBUST n/4 axes where n is the number of axes on
which the CI remains on the correct side of zero.

---

## §6. Pre-registered hypotheses with quantitative falsification criteria

Four primary hypotheses; falsification thresholds locked here.

### H_SHOCK_AMPLIFICATION (load-bearing)
**Statement:** Conflict-shock-induced displacement is associated with
differential intensification in admin-2 units within a country's
Stage-A historical-atrocity polygon, beyond what the shock itself
predicts in non-polygon units.

**Operationalization:** `beta_interaction` in §4.1.

**Confirmation:** 95% posterior CI on `beta_interaction` excludes zero on
the positive side in v0_2 (after polygon inclusion) AND replicates in v0_3 +
v0_4. Robust on ≥ 3 of 4 §5 axes.

**Falsification:** 95% CI spans zero in v0_2 OR fewer than 3 of 4 §5 axes
clean.

**Locked language ("associated with"):** the framing is correlational; this
study does NOT make a causal claim about the historical polygon causing
modern displacement amplification. The polygon is a marker of geography that
historically experienced atrocity; modern displacement geography is the
outcome. Mechanisms (institutional continuity, social-network depletion,
demographic remnant) are NOT identified here.

### H_HISTORICAL_INTENSITY
**Statement:** Admin-2 units with more documented historical atrocity
events show higher baseline displacement rates, independent of polygon
membership.

**Operationalization:** `beta_atrocity_count` in §4.1 of v0_3.

**Confirmation:** 95% CI excludes zero positive in v0_3 + v0_4. Robust
≥ 3 of 4.

**Falsification:** CI spans zero in v0_3 OR fewer than 3 of 4 axes clean.

### H_TERRAIN
**Statement:** Terrain ruggedness independently predicts displacement
geography. (Rugged terrain shelters insurgency, alters refugee routes,
constrains escape.)

**Operationalization:** `beta_terrain` in §4.1 of v0_4.

**Confirmation:** 95% CI excludes zero in v0_4. Robust ≥ 3 of 4.

**Falsification:** CI spans zero OR fewer than 3 of 4 axes clean.

### H_CROSS_COUNTRY_PORTABILITY
**Statement:** The shock-amplification interaction effect (`beta_interaction`)
holds in the same direction across all 4 countries (Colombia, Sudan, DRC,
Yemen) when fit separately per country.

**Operationalization:** Per-country single-model fits estimating
`beta_interaction` for each country. Same direction (positive) in 4/4
countries → cross-country portability supported.

**Confirmation:** All 4 country-specific `beta_interaction` CIs on the
positive side of zero (does not require CI excluding zero — direction-only
robustness given smaller per-country samples).

**Falsification:** Sign reversal in any country, OR CIs flat-line through
zero in ≥2 countries.

### §6 disposition reading table (template; populated post-Phase 4)

| Hypothesis | v0_2 | v0_3 | v0_4 | n/4 axes | Verdict |
|---|---|---|---|---|---|
| H_SHOCK_AMPLIFICATION | TBD | TBD | TBD | TBD | TBD |
| H_HISTORICAL_INTENSITY | n/a | TBD | TBD | TBD | TBD |
| H_TERRAIN | n/a | n/a | TBD | TBD | TBD |
| H_CROSS_COUNTRY_PORTABILITY | TBD | TBD | TBD | TBD | TBD |

---

## §7. Pre-conditions that must pass BEFORE Stan fitting

Four pre-condition checks, each shipped as a script in
`_scripts/precond_N_*.py` with results documented in
`notes/precond_N_report.md`. Any FAIL is redlined into
`notes/pre_reg_redline.md` v1→v2 before fitting.

### Pre-cond 1 — Country sample availability
**Check:** Each of the 4 countries has ≥ 5 years of DTM data with ≥ 50
admin-2 units present per year. Counts only.

**Pass:** All 4 countries clear.
**Fail:** Drop the failing country from primary panel; rerun with 3 countries
or pivot to Stage-B-only for the failing country.

### Pre-cond 2 — Conflict-source agreement
**Check:** ACLED and UCDP-GED event counts per admin-2 × year correlate
≥ 0.6 across the panel (Spearman). Cross-source validity check.

**Pass:** All countries clear.
**Fail:** Reframe shock indicator as source-specific; rerun §5 Axis 1 as
primary instead of robustness.

### Pre-cond 3 — Historical polygon coverage
**Check:** Each Stage-A polygon contains ≥ 5 admin-2 units to support
within-polygon variance. Pure coverage count; no outcome inspection.

**Pass:** All 4 polygons clear.
**Fail:** Aggregate polygon-internal admin-2s to a single binary indicator
without within-polygon partial pooling; document downgrade.

### Pre-cond 4 — Yemen post-2022 coverage
**Check:** ACLED post-2022 events in Houthi-controlled governorates as a
fraction of pre-2022 coverage. Drop threshold: < 30% of pre-2022 level →
Yemen post-2022 Stage A is unreliable.

**Pass:** Coverage ≥ 30% → Yemen panel intact.
**Fail:** Drop Yemen post-2022 from Stage B; keep Stage A historical
polygon analysis only. Document in §6 sensitivity. **Per locked
constraints language: "document, don't fight it."**

---

## §8. Data sources

| Source | URL | Use |
|---|---|---|
| UCDP-GED | https://ucdp.uu.se/downloads/ | Conflict fatalities + events 1989–present |
| ACLED | https://acleddata.com/data-export-tool/ | Cross-source event validation; Yemen pre-cond |
| IOM DTM | https://dtm.iom.int/ | IDP rates per admin-2 × year (the outcome) |
| GADM | https://gadm.org/download_country.html | Admin-2 polygons (all 4 countries) |
| EOSV | https://www.pcr.uu.se/research/ucdp/datasets/eosv/ | Historical one-sided violence (ends 2013) |
| Nunn-Puga ruggedness | https://diegopuga.org/data/rugged/ | Terrain ruggedness per admin-2 |
| Africapolis / GHS-SMOD | https://africapolis.org/ ; https://human-settlement.emergency.copernicus.eu/ | Urban/rural admin-2 classification |
| CINEP | https://www.nocheyniebla.org/ | Colombia historical violence archive |
| Sudan Open Archive | https://www.sudanarchive.net/ | Sudan colonial-era historical sources |
| ICG / Salisbury 2015 | https://www.crisisgroup.org/ | Yemen Six Wars timeline |

All fetched files SHA-256 hashed and recorded in `manifest.json`.

---

## §9. Walk-back protocol (LOCKED)

The walk-back protocol specifies the disposition reading per cross-hypothesis
pattern. **Locked here before any fit.**

### Per-hypothesis verdicts

- **H_SHOCK_AMPLIFICATION SUPPORTED + H_HISTORICAL_INTENSITY SUPPORTED + H_CROSS_COUNTRY_PORTABILITY SUPPORTED:**
  Substrate-9 load-bearing finding. Historical atrocity geography
  ASSOCIATED WITH differential displacement amplification under
  contemporary shocks, cross-country portable, robust across robustness
  axes. Methodology-corpus contribution: corpus's hierarchical structural-
  prior framework extends to 4-country cross-substrate IDP geography.

- **H_SHOCK_AMPLIFICATION SUPPORTED + H_CROSS_COUNTRY_PORTABILITY FAILED:**
  The shock-amplification finding is country-specific. Report which
  country(ies) carry the signal. Do not claim cross-country portability.

- **H_SHOCK_AMPLIFICATION FALSIFIED:**
  Historical atrocity polygon does not amplify displacement response to
  contemporary shocks at the locked CI threshold. Honest negative for the
  H_SHOCK_AMPLIFICATION hypothesis. Substrate-9 closes with this finding;
  follow-ups (mechanism-disaggregated framings) deferred to substrate
  extensions.

- **H_HISTORICAL_INTENSITY SUPPORTED but H_SHOCK_AMPLIFICATION FALSIFIED:**
  Historical atrocity-count predicts baseline displacement rates but does
  NOT differentially amplify under shock. Report the baseline finding;
  flag the shock-interaction null as honest negative.

- **H_TERRAIN SUPPORTED ALONE:**
  Terrain ruggedness is the load-bearing geographic predictor of
  displacement. The historical-atrocity-polygon framing is not what's
  doing the work in this substrate. Frame as "displacement geography is
  primarily terrain-shaped, not atrocity-history-shaped."

- **ALL HYPOTHESES FALSIFIED:**
  The corpus's structural-prior framework does NOT cleanly transfer to
  IDP geography at this scale. Honest negative for the substrate-9
  extension. Document fully; do not retrofit hypotheses.

### Cross-substrate methodology touch

The IDP study tests whether the partial-pooling + structural-prior
methodology that identified race × inequity (gun violence) and
dollar-store / pct_Hispanic residual couplings (food deserts) transfers
to cross-country humanitarian-data geography. The methodology corpus
contribution is independent of the specific findings: it's the discipline
of pre-reg + commit-hash + content-hash + walk-back applied to a new
substrate.

---

## §10. Phased execution timeline

### Phase 0 — Data + pre-conditions (current phase)
1. Repo skeleton + initial commit (lock timestamp)
2. Fetch UCDP + ACLED (execute now)
3. Scaffold DTM + GADM fetches (Stage B execution Phase 2)
4. Stage-A historical polygon provenance.md per country
5. `build_longitudinal_panel.py` defensive harmonization
6. Pre-cond 1-4 scripts + execute
7. Pre-cond results documented; failures redlined into v2

### Phase 1 — Country panel build + v0_1 fit
- Execute DTM + GADM fetches (Stage B)
- Build country-level analytic panels via build_longitudinal_panel.py
- Fit v0_1 (no historical polygon, country FE + shock + interaction)
- Diagnostics

### Phase 2 — Polygon overlay + v0_2 fit
- Digitize 4 Stage-A historical polygons (with provenance docs)
- Spatial-join polygons to GADM admin-2
- Fit v0_2 (adds polygon binary + shock × polygon interaction)
- Diagnostics; H_SHOCK_AMPLIFICATION first read

### Phase 3 — Historical atrocity count + v0_3
- Extract historical atrocity counts per admin-2 (CINEP / EOSV / UCDP / Six Wars)
- Fit v0_3 with log1p(atrocity_count)
- H_HISTORICAL_INTENSITY read

### Phase 4 — Full covariates + v0_4 + robustness axes
- Add terrain ruggedness + urban/rural + ethnic-composition where available
- Fit v0_4
- Run 4 robustness axes (§5)
- Final §6 disposition reading

---

## §11. Repository structure

```
IDP/
├── README.md                  — populated post-Phase 4 with headline table
├── manifest.json              — SHA-256 of every fetched file
├── _scripts/
│   ├── fetch_ucdp.py          — UCDP-GED + EOSV downloads
│   ├── fetch_acled.py         — ACLED export
│   ├── fetch_dtm.py           — IOM DTM (scaffold; per-country)
│   ├── fetch_gadm.py          — GADM admin-2 polygons
│   ├── fetch_eosv.py          — Ethnic One-Sided Violence (Eck & Hultman)
│   ├── build_longitudinal_panel.py  — defensive harmonization
│   ├── precond_1_country_sample_availability.py
│   ├── precond_2_conflict_source_agreement.py
│   ├── precond_3_polygon_coverage.py
│   └── precond_4_yemen_post2022_coverage.py
├── data/                      — fetched data (gitignored beyond manifest)
│   ├── ucdp/
│   ├── acled/
│   ├── dtm/                   — _harmonization_log.json per country
│   ├── gadm/
│   ├── eosv/
│   ├── polygons/              — digitized historical polygons (Stage A)
│   └── (population denominators)
├── analysis/
│   ├── v0_1_baseline.stan
│   ├── v0_2_polygon.stan
│   ├── v0_3_atrocity_count.stan
│   ├── v0_4_full.stan
│   └── precond/               — pre-cond output artifacts
├── historical_polygons/
│   ├── colombia_la_violencia_1948_1958/provenance.md
│   ├── sudan_fur_dar_pre1994/provenance.md
│   ├── drc_kasai_1959_1965/provenance.md
│   └── yemen_six_wars_2004_2010/provenance.md
├── notes/
│   ├── displacement_research_design.md     — this file (v1)
│   ├── shock_amplification_specification.md
│   ├── pre_reg_redline.md                  — v1→v2 deviations
│   ├── precond_1_report.md
│   ├── precond_2_report.md
│   ├── precond_3_report.md
│   └── precond_4_report.md
└── provenance/
    ├── data_sources.md                     — fetch URLs + dates
    └── chain_of_custody.md                 — file hash chain
```

---

## §12. Author flags — RESOLVED at redline Entry 002 (2026-05-17)

All 5 flagged items have been PI-confirmed and locked. See
`notes/pre_reg_redline.md` Entry 002 for details. Summary:

1. **Colombia Stage-A polygon naming:** RESOLVED — La Violencia 1948–1958
   mortality concentration zones (option b). PI rationale: La Violencia
   is Colombia's founding modern displacement-atrocity event; geographically
   distinct from modern FARC-era displacement (clean non-overlap
   contrast for H_SHOCK_AMPLIFICATION). Directory renamed:
   `historical_polygons/colombia_la_violencia_1948_1958/`.
2. **DRC Stage-A polygon:** RESOLVED — Kasai 1959–1965 Luba expulsion zone
   (NOT the placeholder Kivu pre-1996). PI rationale: founding
   protracted-displacement geography reactivated by 2016-2018 Kamuina
   Nsapu conflict; deeper historical layer than the eastern Kivu
   alternative. Directory renamed:
   `historical_polygons/drc_kasai_1959_1965/`. Additional source-list
   amendment (Entry 002-C) for `historical_atrocity_count` since
   UCDP/EOSV don't cover pre-1989 events.
3. **Yemen Stage-A polygon:** RESOLVED — Six Wars (2004-2010) operational
   extent (narrow framing; Sa'dah + N. Hajjah + W. Amran + N. Sana'a gov,
   EXCLUDES Sana'a city). PI rationale: cleaner empirical contrast than
   the broader Zaydi-imamate heartland. Directory renamed:
   `historical_polygons/yemen_six_wars_2004_2010/`.
4. **DRC 1984 census staleness:** CONFIRMED. 2024 INS estimates with
   staleness flagged per Phase 0 locked constraint.
5. **EOSV cutoff 2003–2010 for Sudan atrocity-count:** CONFIRMED. Post-2013
   ethnic-targeting events fold into `current_conflict_intensity`, not
   `historical_atrocity_count`, per Phase 0 locked constraint.

Phase 1 unblocked: Stage-A polygon digitization can proceed for all 4
polygons. DRC additionally requires manual academic-history coding
(Entry 002-C amendment) for the historical_atrocity_count covariate.
