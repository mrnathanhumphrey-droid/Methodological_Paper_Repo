# Pre-Registration — NCAA D1 Men's Adjudicated-Position Test 1 Re-Validation

## Center-Subset Extraction on the NCAA Men's Cells of the Cross-League Variance-Asymmetry Test

**Date filed:** 2026-06-01
**Filed before:** any inspection of variance ratio, Levene's p, bootstrap CI, or any per-cell statistic on NCAA D1 Men's residuals computed under adjudicated position bucketing. The metadata-bucketed NCAA M Test 1 results (cross-league paper §5.7, Table 5.11; §5.7.3, Table 5.15) are visible and locked at their existing reported values; the adjudicated-bucket-derived per-cell statistics have not been computed at any cell level.
**Status:** Sloan-grade Tier-1 pre-registration. Companion to the WNBA and NCAA W pre-regs filed in the same session. Locks via git commit. Single-test α = 0.05 per cell per existing cross-league protocol.
**Sloan paper:** *Partial pooling of residual classes: theory, application to basketball projections, and measurable noise-floor reduction* (working title), draft state at `paper_draft/section_5_empirical_validation.md`. Extends §5.7 / §5.7.3 with an adjudicated NCAA M arm.
**Cross-paper anchor:** companion to the NBA Sloan adjudicated pre-reg at `e52505f` and the WNBA Sloan adjudicated pre-reg filed in this same session. Together the three cross-league pre-regs cover the WNBA + NCAA contribution to the 11/11 BLK × Center claim and the cross-league §5.4.1 REB walk-back validation.

---

## 1. Why this exists — and why NCAA's adjudication question differs from NBA / WNBA

The cross-league paper §5.7 reports NCAA D1 Men's Test 1 results under a 3-way classifier sensitivity matrix (inclusive / strict / primary). For NCAA M, **all three classifiers produce identical per-cell statistics** (Table 5.11: inclusive ≡ strict ≡ primary at n_in = 221/215 for 2024/2025). This is structural: NCAA D1 metadata uses single-letter position labels (G / F / C) with only 4 hyphenated cases out of 8,458 players (0.05%). The classifier sensitivity question that motivates WNBA adjudication is null at NCAA M scale.

A different question is open at NCAA M: **is the F (Forward) metadata bucket harboring on-court Centers that would tighten the Center cohort and either strengthen the BLK × Center claim or break the REB × Center Stan walk-back?**

NCAA M's F bucket contains 2,933 players. Among these, **1,714 have height ≥ 80" (6'8" or taller), the modern NBA-derived stretch-big threshold**. At NCAA cohort scale (n_in ≈ 220), even a small extraction of true on-court Centers from this 1,714-player pool would materially change the Center sample. The existing Test 1 protocol's metadata bucket does not capture this extraction; it bins all F-labeled players as non-Center regardless of height or on-court archetype.

The cross-league paper §5.7.3 reports NCAA M Stan robustness:
- BLK confirmed under Stan: 2/2 cells coupling at p < 10⁻¹⁵.
- REB walked back under Stan: 0/2 cells null (parallel to WNBA Stan walk-back).
- PTS upgraded to 2/2 coupling at p < 0.05 (NCAA cohort scale resolves the small effect).

Independent NBA work (committed at `e52505f`, results at `RMD_SRC_PIPELINE/results/sloan_adjudicated/`) showed that the NBA REB × Center Stan walk-back was a **power problem hidden by metadata mis-bucketing**: 46 modern bigs (Anthony Davis, Giannis Antetokounmpo, Kevin Love, Mason Plumlee, Kristaps Porziņģis, etc.) were metadata-Forward but on-court-Center, and adjudication revealed REB × Center 3/3 WALK-BACK FALSIFIED under the corrected bucket.

This NCAA M pre-registration tests whether the same power-problem-hidden-by-mis-bucketing dynamic governs the NCAA M REB walk-back. The adjudication question for NCAA M is **Center-subset extraction from the F bucket** — not boundary re-bucketing like NBA / WNBA had with hyphenated labels.

The adjudicated Center bucket includes the metadata Center bucket (417 players) as a strict superset plus any F-labeled tall players the adjudicator assigns to Center, minus any metadata Centers reclassified to Forward.

## 2. Locked operationalizations

### 2.1 Substrate scope

- **Seasons:** 2024, 2025 NCAA D1 Men's regular season. Two seasons, exactly matching the existing NCAA M cross-season Test 1 design (cross-league paper §5.7, Tables 5.11 / 5.15). The 2023 row is empty in the existing tables (cohort not yet populated at that lock); we do not retroactively backfill.
- **Source:** `C:/NCAA D1 Mens/data/processed/player_game_logs.csv`, restricted to regular-season rows for 2024 and 2025.
- **Cohort selection:** per the existing NCAA M Test 1 protocol (qualifying union with GP ≥ 10 per season), exactly matching the cohort used to produce Table 5.11. Cohort definition is read from the existing audit run at `C:/NCAA D1 Mens/audit_runs/test_1_replication/ncaa_mbb_3way_sensitivity.csv`; no cohort re-derivation.
- **Observable space:** BLK, PTS, REB — per-game, exactly matching existing Test 1 protocol.

### 2.2 Residual baselines (two, one per existing arm)

**Surgical arm:**
- Residual = actual_S(p, g) − career_mean_S(p) computed under the same surgical projection method as §5.7 / Table 5.11.

**Stan arm (load-bearing for walk-back validation):**
- Residual = actual_S(p, g) − E_stan(p, g, S) under the existing NCAA M hierarchical NB2 Stan posterior fit reported in §5.7.3 (Table 5.15). Read-only at `C:/NCAA D1 Mens/audit_runs/stan_robustness/ncaa_mens_stan_3_cell.csv`. No re-fit. No re-conditioning on adjudicated positions.

### 2.3 Position classifier — locked

**Metadata bucket (control, matching existing §5.7 inclusive classifier):**
- **Center:** `position` string == `C` OR contains the substring `C` as the primary token in a hyphenated label (e.g., `C-F`).
- **Non-Center:** all other position strings (G, F, G-F, F-G, F-C).

For NCAA M with 4 hyphenated cases total, the inclusive/strict/primary classifiers are equivalent.

**Adjudicated bucket (load-bearing, NEW):**

The adjudication scope is the **Center-candidate pool**, defined as:
- All metadata `F` players with `height_inches ≥ 80` (6'8" or taller): **1,714 candidates**.
- All metadata `C` players (no height filter): **417 candidates** (re-judged for possible mis-classification toward Forward).
- All hyphenated players (`G-F`, `F-G`, `C-F`, `F-C`): **4 candidates**.
- All metadata `F` players with `height_inches < 80`: **NOT in scope** (default to non-Center under both metadata and adjudicated). The pre-filter is principled by the modern stretch-big height threshold and locks the scope before adjudication.

**Total NCAA M adjudication scope: 2,135 candidates.**

Counts verified against the metadata snapshot at lock time. Adjudication scope is locked at this SHA.

The ~6,323 non-adjudicated players (metadata-G + metadata-F with height < 80") keep their metadata-bucket assignment in the adjudicated arm.

### 2.4 Adjudication method — INDEPENDENT SUBAGENT FLEET

The 2,135 adjudication verdicts are produced by **2,135 independent Sonnet subagents**, one per candidate. No batching, no inter-agent communication. Mirrors NBA v1.2 fleet methodology.

**Locked agent prompt template (NCAA M-adapted, fixed at this SHA):**

```
You are adjudicating a single NCAA D1 Men's college basketball player's
best-fit position bucket for a methodology paper substrate. The bucket
choices are:
  Center, Forward, Guard, or no_fit.

You will NOT be told what the methodology paper concludes about position.
Your only job is to pick the bucket that best reflects this player's
on-court archetype across the 2024 and 2025 NCAA D1 Men's seasons, using
ONLY the data provided in this prompt.

Decision criteria (in priority order):
  1. On-court archetype in the 2024-2025 window: defense and offense role.
  2. Height: >= 82" (6'10") strongly leans Center; 80-81" can be either
     Forward or Center depending on role; < 80" defaults to Forward at
     this label tier. NCAA D1 Men's center height range is typically
     6'8"-7'0", lower than NBA. Be calibrated to the NCAA scale.
  3. Career counting-stat profile: high REB / BLK with low AST and low
     FG3M attempts -> Center archetype; balanced REB / AST with moderate
     BLK and modest 3PT activity -> stretch-Forward archetype; high AST
     with low REB -> Guard archetype.
  4. Class year: a senior with a defined role gives stronger signal than
     a freshman whose role is unsettled. Weight the most recent season's
     archetype heavily for upperclassmen; use multi-season averaging
     more for underclassmen.
  5. Default to the LOWER-COMMITMENT bucket (Forward over Center) when
     the on-court archetype is genuinely ambiguous. The Center bucket is
     for paint-bound 5s; do not assign stretch-4s to Center.

The `no_fit` disposition: choose `no_fit` ONLY if the player's archetype
is genuinely positionless (truly straddles 2+ buckets without a primary
one). `no_fit` is a real disposition, not a fallback when uncertain.

Output exactly this JSON shape (no other text):
{
  "assignment": "Center" | "Forward" | "Guard" | "no_fit",
  "confidence": "high" | "medium" | "low",
  "rationale": "<one paragraph, 2-4 sentences>",
  "no_fit_reason": "<populated only if assignment is no_fit>"
}

The player to adjudicate:
  name: <full_name>
  player_slug: <slug>
  metadata_position: <metadata position string>
  metadata_bucket_inclusive: <Center | non-Center>
  height_inches: <height>
  class_year_2024: <Fr | So | Jr | Sr | Gr | null>
  class_year_2025: <Fr | So | Jr | Sr | Gr | null>
  career_avg_PTS_per_game: <number>
  career_avg_REB_per_game: <number>
  career_avg_AST_per_game: <number>
  career_avg_BLK_per_game: <number>
  career_avg_FG3M_per_game: <number>
  career_avg_FG3A_per_game: <number>
```

**Structured output schema:** identical to NBA v1.2 / WNBA pre-reg.

### 2.5 Test statistic — Levene's variance ratio (load-bearing)

Per (season, observable, arm), under each bucketing arm:
- σ_Center = sample SD of residuals across qualifying (Center player, game) records.
- σ_non-Center = sample SD of residuals across qualifying (non-Center player, game) records.
- Variance ratio = σ_Center / σ_non-Center.
- Bootstrap 95% CI on the ratio: B = 1,000 resamples, cluster on player, seed = 20260601.
- Levene's test (median-centered) on residual² — load-bearing.
- p_F (two-sided F-test) and p_Bartlett supplementary.

### 2.6 Power gate (pre-committed)

Per cell: `n_in_adjudicated / n_in_metadata ≥ 1.10`.

The NCAA gate is tighter (1.10) than WNBA's (1.20) because NCAA's metadata Center cohort is already large (n_in ≈ 220). A 10% lift is the minimum that materially changes the variance estimate at NCAA scale. If any cell fails the gate, that cell is POWER-LIMITED.

## 3. Tier-1 Hypotheses

Three hypotheses, each tested per season × per arm (surgical, Stan). Two seasons (2024, 2025) × three observables × two arms = 12 per-cell statistics per bucket × 2 buckets = 24 statistics total.

### 3.1 H1 — BLK × Center under adjudicated bucketing

Existing NCAA M claim (Table 5.11 inclusive): 2024 ratio 1.84 (p<10⁻³²), 2025 ratio 1.73 (p<10⁻¹⁹). Both formally significant at NCAA cohort scale.

Per-cell decision rule under adjudicated Stan REB residuals — same as WNBA H1 §3.1 (PERSISTS / PERSISTS-DIRECTIONAL / ATTENUATES / REGIME-NULL / INVERTED / INCONCLUSIVE) referenced to the [1.26, 2.03] cross-league band.

### 3.2 H2 — PTS × Center

Existing NCAA M (Table 5.11): 2024 ratio 0.89 (p=0.04), 2025 ratio 0.82 (p<0.001). Both directional-coupling at NCAA cohort scale.

Per-cell decision rule: DIRECTIONAL-PERSISTS / NULL / INVERTED / INCONCLUSIVE per WNBA H2 §3.2 framework, referenced to [0.76, 1.02].

### 3.3 H3 — REB × Center walk-back validation

Existing NCAA M (Table 5.11 surgical): 2024 ratio 1.23 (p<0.001), 2025 ratio 1.14 (p<0.01). Both couple under surgical.

Existing NCAA M (Table 5.15 Stan): 0/2 cells coupling. Walk-back framed in §5.7.3 / §5.4.1 as method-driven (Stan absorbs position mean).

**Alternative reading (the test):** the Stan walk-back is power-problem-hidden-by-mis-bucketing — F-labeled tall players whose REB profiles cluster with Centers would resurrect REB × Center coupling under adjudication.

Per-cell decision rule under adjudicated Stan REB residuals: WALK-BACK UPHELD / WALK-BACK FALSIFIED / WALK-BACK FALSIFIED-INVERTED / INCONCLUSIVE per WNBA H3 §3.3 framework.

Aggregate H3:
- 2/2 WALK-BACK UPHELD → walk-back robust at NCAA M scale; reinforces §5.4.1.
- ≥ 1 WALK-BACK FALSIFIED → walk-back overturned at NCAA M layer. Combined with NBA's already-FALSIFIED 3/3 (and possibly WNBA's outcome), the cross-league §5.4.1 retraction is reopened across multiple leagues.

### 3.4 H4 — power gate sanity

Per cell, report `n_in_meta`, `n_in_adj`, lift, gate (≥ 1.10) disposition. All 6 cells (2 seasons × 3 observables) reported regardless of outcome.

## 4. Aggregate report framework

3 × 2 disposition table (hypotheses × seasons) under each arm (surgical, Stan), with the Stan arm load-bearing for H3.

Cross-league paper revision targets: §5.7 (Table 5.11 surgical), §5.7.3 (Table 5.15 Stan), and §5.4.1 (REB walk-back). The aggregate framework mirrors the NBA Sloan adjudicated pre-reg §4 and the WNBA pre-reg §4.

## 5. Discipline guards

1. Threshold adjustment after firing — forbidden. [1.26, 2.03], [0.76, 1.02], 1.10 power gate, all decision-rule conditions locked.
2. Classifier redefinition — forbidden. Adjudicated bucket read verbatim from `ncaa_m_position_adjudication_v10.json`.
3. NCAA M Stan re-fit — forbidden. The Stan posterior is read-only.
4. Statistical-test substitution — forbidden. Levene's is load-bearing.
5. Selective reporting — all 12 per-cell statistics × 2 buckets = 24 numbers reported regardless of disposition.
6. Walk-back rescue — forbidden. If H3 returns FALSIFIED, §5.4.1 is honestly reopened.
7. Adding observables — forbidden.
8. Fleet independence — each of the 2,135 subagents adjudicates independently.
9. Lower-commitment default — agent prompt §2.4 instructs the adjudicator to default to LOWER-COMMITMENT bucket (Forward over Center) when ambiguous.
10. Pre-filter scope locked — the 2,135-candidate scope is fixed at this SHA. Adding or removing candidates after seeing residuals is a violation. Players with metadata `F` and height < 80" are NOT in scope; they remain non-Center under the adjudicated arm.

## 6. Output artifacts

Under `C:/NCAA D1 Mens/audit_runs/test_1_replication/sloan_adjudicated/`:

- `ncaa_m_position_adjudication_v10.json` — the 2,135-verdict adjudication output.
- `n_in_lift_table.parquet` — per cell.
- `variance_ratios_metadata_surgical.parquet`, `variance_ratios_metadata_stan.parquet`.
- `variance_ratios_adjudicated_surgical.parquet`, `variance_ratios_adjudicated_stan.parquet`.
- `dispositions.json`.
- `aggregate_verdict.md`.
- `SLOAN_ADJUDICATED_NCAA_M_RESULTS.md`.

## 7. Timing and commitment

- **Lock event:** git commit to NBAProjections `main`; SHA in `SHA_LOCK.txt`.
- **Adjudication fires:** once, after sign-off. 2,135-Sonnet-subagent fleet via Workflow tool.
- **Analysis fires:** once after adjudication artifact written. Single batch.
- **No re-runs.**

## 8. Sign-off

- **Filed by:** Claude Code (claude-opus-4-7[1m])
- **Sign-off requested from:** mr.nathanhumphrey@gmail.com
- **Repo:** https://github.com/mrnathanhumphrey-droid/NBAProjections
- **Cross-paper anchor SHAs:** NBA Sloan adjudicated `e52505f`; WNBA Sloan adjudicated (this session); NCAA W Sloan adjudicated (this session).

---

**End of draft v1.0.**
