# Pre-Registration Redline Trail v1 → v2

This file tracks every documented deviation from the locked pre-registration
v1 (`notes/displacement_research_design.md` v1, committed at the initial
git commit `dd3f0ec`). Each entry has:

- The locked v1 specification being modified
- The reason for modification
- The replacement specification
- The commit hash at which the deviation is locked into v2
- The PI sign-off (or "automatic" for environment-forced deviations)

---

## Entry 001 — 2026-05-17 — ACLED replaced by GDELT for cross-source validation

**Locked v1 spec:** `notes/displacement_research_design.md` §3.3 + §5 (Axis 1)
+ §7 (Pre-cond 2 + Pre-cond 4) + §8 (data sources) named **ACLED** as the
cross-source conflict-event validator against UCDP-GED.

**Reason for modification:** ACLED access tightened post-2024 to require
institutional email + manual academic approval. Principal investigator
(Nathan Humphrey) is not institutionally affiliated; ACLED registration
returned access denial. The pre-cond 2 cross-source agreement check and
pre-cond 4 Yemen post-2022 coverage check both depended on ACLED.

**Replacement spec (locked at this commit):** **GDELT 2.0 Event Database**
substitutes for ACLED in:
  - §3.3 covariate `acled_event_count` → `gdelt_event_count` (event count
    from GDELT 2.0 ActionGeo-filtered to admin-2 × year)
  - §5 Robustness Axis 1: "Cross-source GDELT vs UCDP-GED" (was "Cross-source
    ACLED vs UCDP-GED")
  - §7 Pre-cond 2: Spearman ≥ 0.6 GDELT-vs-UCDP-GED per admin-2 × year
    (same threshold as locked v1; only the source substituted)
  - §7 Pre-cond 4: Yemen post-2022 coverage check uses GDELT
    ActionGeo_CountryCode = YM filtered to Houthi-controlled governorates
    (governorate list per the locked precond_4 script). Same ≥ 30%
    threshold as v1; only the source substituted.

**Rationale + tradeoffs:**

  - **GDELT is public + no auth + reproducible.** Free under Creative
    Commons. URL: https://www.gdeltproject.org/. Anyone can verify the
    fetched data without institutional access barriers — this is closer
    to the open-science discipline of the methodology corpus.
  - **GDELT is machine-coded from news, not human-coded.** Higher
    false-positive rate than ACLED's hand-coded data. Mitigated by the
    admin-2 × year aggregation (locked aggregation level is unchanged):
    noise smooths out at the aggregate scale used in pre-cond 2 + 4.
  - **GDELT event coding (CAMEO codes) differs from ACLED event types.**
    The shock indicator (UCDP-GED fatality 80th percentile within country)
    remains unchanged — GDELT is only the cross-source validator, not
    the primary shock indicator.
  - **Cross-source agreement threshold (Spearman ≥ 0.6) is unchanged.**
    The locked threshold is unchanged; the question is whether GDELT and
    UCDP-GED agree at the admin-2 × year aggregate, regardless of which
    source is "ground truth."
  - **Three-way cross-source possibility:** UCDP + GDELT + ICEWS (Harvard
    Dataverse, free, no auth) could be a tertiary check if GDELT alone
    is too noisy. Locked here: GDELT is the primary cross-source
    validator; ICEWS is reserved as Phase 1+ tertiary if Spearman corr
    is borderline (0.5-0.7 range).

**What stays unchanged from v1:**

  - All 4 hypotheses (H_SHOCK_AMPLIFICATION, H_HISTORICAL_INTENSITY,
    H_TERRAIN, H_CROSS_COUNTRY_PORTABILITY)
  - All 4 hypotheses' falsifier thresholds + confirmation CIs
  - Locked "associated with" framing in shock_amplification_specification.md
  - Stage-A historical polygon definitions (4 polygons unchanged)
  - UCDP-GED as primary shock indicator
  - DTM as primary outcome source
  - Stan model class + priors
  - 5 axes of pre-cond → 4 of which use GDELT now (axis 1 + pre-cond 2 + pre-cond 4)

**PI sign-off:** automatic — environment-forced deviation. ACLED access
denied to non-institutional PI; substrate-9 pre-reg cannot otherwise
proceed without dropping cross-source validation entirely. Documented in
this redline before any GDELT fetch is run.

**Files affected by this redline (to be updated in next commit):**

  - `_scripts/fetch_acled.py` — retained as FETCH_INSTRUCTIONS stub for
    future institutional access; not used in Phase 0+
  - `_scripts/fetch_gdelt.py` — NEW; replaces ACLED fetch
  - `_scripts/precond_2_conflict_source_agreement.py` — updated to read
    GDELT instead of ACLED
  - `_scripts/precond_4_yemen_post2022_coverage.py` — updated to use
    GDELT for the Yemen post-2022 coverage check
  - `notes/displacement_research_design.md` — v2 update reflecting the
    redline (header should reflect "v2" with link to this redline file)
  - `provenance/data_sources.md` — GDELT added; ACLED retained with
    note about access denial

---

## Entry 002 — 2026-05-17 — Stage-A polygon interpretations LOCKED + substrate framing clarified (long-term protracted displacement) + DRC source-list amendment

**PI confirmation (verbatim, 2026-05-17):**
> "modern IDP consists of long term displacement. look at Sudan and Congo
> and Palestine. that's why i picked those mainly"

This redline entry locks four things:
1. The 3 PI-confirmed polygon interpretations (Colombia / DRC / Yemen)
2. The substrate-9 framing clarification (long-term protracted displacement,
   not new-onset displacement)
3. The DRC source-list amendment (academic-history sources for Kasai
   1959-1965, since UCDP/EOSV both start at 1989)
4. Two procedural confirmations (DRC 2024 INS population denominator
   acceptance + Sudan 2003-2010 EOSV window confirmation) — these were
   already in the locked v1 spec; Entry 002 just confirms PI sign-off.

### 002-A: Colombia Stage-A polygon LOCKED
**v1 placeholder:** "CDO 1922" — unclear interpretation, 4 candidates
listed in §12 of design doc.
**Locked v2:** La Violencia 1948–1958 mortality concentration zones.
Geographic extent per Centro de Memoria Histórica *¡Basta Ya!* (2013)
Map 2 — Tolima, Caldas, Cundinamarca, Valle del Cauca, Antioquia, Boyacá,
Norte de Santander mortality zones.
**Rationale (PI):** La Violencia is Colombia's founding modern
displacement-atrocity event (~200-300k killed, ~2M displaced). Its
geography is *distinct* from modern FARC-era displacement geography
(Pacific coast / Caquetá / Norte de Santander), giving a clean
non-overlapping historical-vs-current contrast for the H_SHOCK_AMPLIFICATION
test. Rejected: 1922 Comisarías Especiales (administrative not atrocity)
and FARC pre-Caguán foothold (overlaps modern displacement, confounds
historical with current).
**Polygon directory renamed:** `historical_polygons/colombia_cdo_1922/`
→ `historical_polygons/colombia_la_violencia_1948_1958/`.

### 002-B: DRC Stage-A polygon LOCKED
**v1 placeholder:** "Kivu pre-1996" — author inference, flagged for PI.
**Locked v2:** Kasai 1959–1965 Luba expulsion zone.
Geographic extent: modern Kasai + Kasai-Central + Kasai-Oriental +
Lomami + Sankuru provinces (the 5 provinces that emerged from the
post-2015 administrative subdivision of historical Kasai-Occidental +
Kasai-Oriental).
**Rationale (PI):** the long-term protracted displacement framing
requires a *founding* historical-atrocity geography, not just any
prior-conflict geography. The 1959-1965 Luba expulsion + Lulua-Luba
ethnic violence created ~250,000 chronic IDPs whose geography was
reactivated by the 2016-2018 Kamuina Nsapu militia conflict that
displaced ~1.5M in the same provinces. Rejected: Eastern Kivu pre-1996
(too contemporary with the panel; well-covered by UCDP) and Ituri
pre-1999 Hema-Lendu (narrower geography).
**Polygon directory renamed:** `historical_polygons/drc_kivu_pre1996/`
→ `historical_polygons/drc_kasai_1959_1965/`.

### 002-C: DRC historical_atrocity_count source-list AMENDMENT
**v1 spec (§3.2):** "DRC: UCDP one-sided + EOSV 1996-2013."
**Problem identified post-PI-confirmation:** UCDP-GED and EOSV both
start at 1989. Kasai 1959-1965 is *pre-data-era* for both sources.
The locked v1 source list cannot extract atrocity counts for the
locked v2 polygon.

**Amended v2 spec (§3.2 DRC entry only):**
> DRC: manual coding from academic-history sources for the 1959-1965
> window. Primary sources:
>   - Young, C., & Turner, T. (1985). *The Rise and Decline of the
>     Zairian State.* University of Wisconsin Press.
>   - Lemarchand, R. (1964). *Political Awakening in the Belgian
>     Congo.* University of California Press.
>   - De Villers, G. (2002). *Tribu et État au Zaïre.* Cahiers
>     Africains 50.
>   - Stearns, J. (2011). *Dancing in the Glory of Monsters.*
>     PublicAffairs.
>   - CRDA UCL Louvain Belgian colonial archives.
> Output: `data/atrocity_counts/drc_kasai_atrocity_count.csv` with
> per-territoire event counts, manually coded.

**Methodological asymmetry caveat:** the DRC count is academic-secondary-
source coded; Colombia + Sudan + Yemen use primary-source event-database
extraction (UCDP-GED / CINEP / EOSV). The asymmetry is reported in the
§6 disposition reading as a per-country limitation. H_HISTORICAL_INTENSITY
for DRC has weaker primary-source provenance than the other three
countries; falsifier thresholds unchanged but DRC verdict is interpreted
with this caveat.

### 002-D: Yemen Stage-A polygon LOCKED
**v1 placeholder:** "pre-2014 Houthi / Zaydi" — narrow vs broad
interpretation flagged.
**Locked v2:** Six Wars (2004–2010) operational extent. Sa'dah
governorate entirety + Northern Hajjah + Western Amran + Northern Sana'a
governorate. EXCLUDES Sana'a city (Houthi capture occurred September 2014,
after locked pre-2014 cutoff).
**Rationale (PI):** narrow operational-conflict framing has cleaner
empirical contrast than the broader Zaydi-imamate heartland (which
would capture ~9 governorates and leave a thin tail of non-polygon
admin-2 units). The Six Wars also have well-defined data coverage in
UCDP-GED + ICG documentation at mudiriyah granularity.
**Polygon directory renamed:** `historical_polygons/yemen_houthi_zaydi/`
→ `historical_polygons/yemen_six_wars_2004_2010/`.

**Temporal-distance asymmetry note:** Yemen Six Wars (2004-2010) is the
youngest historical polygon across the 4 countries. Colombia La
Violencia is ~80 years pre-panel; Sudan Fur dar is pre-1994 (decades
pre-panel; centuries-old Sultanate); DRC Kasai is ~65 years pre-panel;
Yemen Six Wars is only ~4-10 years pre-panel. This asymmetry is locked
in §6 H_CROSS_COUNTRY_PORTABILITY interpretation — if the
shock-amplification signal holds only in the older-polygon countries
(Colombia / Sudan / DRC), that's a temporal-distance finding distinct
from the cross-country portability claim.

### 002-E: Substrate-9 framing clarification — long-term protracted displacement

**v1 framing (§1):** "long-duration armed conflict 1964-present"
(Colombia); "Darfur conflict 2003-present" (Sudan); etc. The
country-by-country descriptions emphasized conflict duration, not the
chronic-displacement-burden framing PI now articulates.

**v2 framing clarification:** the substrate-9 hypothesis tests
**long-term protracted displacement geography**, not new-onset
displacement geography. The Stage-A historical polygons mark where the
chronic IDP burden was first established by a founding atrocity event;
the contemporary conflict shock is the marginal stressor that compounds
on this chronic geography. This framing aligns substrate-9 with the
UNHCR / IDMC "protracted-displacement-situation" definition (≥ 25,000
IDPs displaced for ≥ 5 consecutive years in same country) — applicable
to all 4 substrate-9 countries.

H_SHOCK_AMPLIFICATION under v2 framing: "Conflict-shock-induced
displacement is associated with differential intensification in admin-2
units within a country's Stage-A historical-atrocity polygon —
geographies that have hosted protracted IDP populations since the
founding atrocity event — beyond what the shock itself predicts in
non-polygon units."

The locked "associated with" framing in
`shock_amplification_specification.md` is UNCHANGED; only the underlying
substrate motivation is clarified.

### 002-F: Two procedural confirmations
- **DRC 2024 INS population denominator + 1984 census staleness flag:**
  CONFIRMED by PI. No change to locked Phase 0 constraint; this entry
  records PI sign-off.
- **Sudan EOSV 2003-2010 atrocity-count window:** CONFIRMED by PI. No
  change to locked Phase 0 constraint; this entry records PI sign-off.

### Files affected by Entry 002 (this commit):
  - `historical_polygons/colombia_cdo_1922/` → renamed
    `historical_polygons/colombia_la_violencia_1948_1958/`
    (+ provenance.md rewritten)
  - `historical_polygons/drc_kivu_pre1996/` → renamed
    `historical_polygons/drc_kasai_1959_1965/`
    (+ provenance.md rewritten with academic-history source list)
  - `historical_polygons/yemen_houthi_zaydi/` → renamed
    `historical_polygons/yemen_six_wars_2004_2010/`
    (+ provenance.md rewritten)
  - `_scripts/precond_3_polygon_coverage.py` — path refs updated to
    new dir names
  - `notes/displacement_research_design.md` — §1 + §1.1 + §3.2 +
    §6 + §12 updated; "v2" header marker added with link to this redline
  - `notes/pre_reg_redline.md` — this entry

**PI sign-off:** explicit; questions 1-5 answered via AskUserQuestion
tool 2026-05-17. PI message verbatim: "modern IDP consists of long term
displacement. look at Sudan and Congo and Palestine. that's why i picked
those mainly" — recorded as the framing-clarification rationale.
