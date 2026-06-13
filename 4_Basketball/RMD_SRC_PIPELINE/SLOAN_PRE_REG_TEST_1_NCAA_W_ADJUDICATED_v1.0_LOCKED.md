# Pre-Registration — NCAA D1 Women's Adjudicated-Position Test 1 Re-Validation

## Center-Subset Extraction on the NCAA Women's Cells of the Cross-League Variance-Asymmetry Test

**Date filed:** 2026-06-01
**Filed before:** any inspection of variance ratio, Levene's p, bootstrap CI, or any per-cell statistic on NCAA D1 Women's residuals computed under adjudicated position bucketing. The metadata-bucketed NCAA W Test 1 results (cross-league paper §5.7, Table 5.12; §5.7.3, Table 5.16) are visible and locked at their existing reported values; the adjudicated-bucket-derived per-cell statistics have not been computed at any cell level.
**Status:** Sloan-grade Tier-1 pre-registration. Companion to the WNBA and NCAA M pre-regs filed in the same session.
**Sloan paper:** *Partial pooling of residual classes: theory, application to basketball projections, and measurable noise-floor reduction* (working title), draft state at `paper_draft/section_5_empirical_validation.md`. Extends §5.7 / §5.7.3 with an adjudicated NCAA W arm.
**Cross-paper anchor:** companion to NBA `e52505f`, WNBA pre-reg, and NCAA M pre-reg in this session.

---

## 1. Why this exists

The cross-league paper §5.7 reports NCAA D1 Women's Test 1 results under the same 3-way classifier sensitivity matrix. For NCAA W, classifier sensitivity matters less than at NBA / WNBA scale: the hyphenated cohort is 298 of 7,668 players (3.9%), and inclusive ≡ strict ≡ primary at the per-cell statistic level (Table 5.12 shows n_in = 224/210 identical across all three classifiers for 2024/2025).

The adjudication question for NCAA W is **Center-subset extraction from the F bucket**, mirroring NCAA M's question: are there F-labeled tall players whose on-court archetype is Center, whose extraction would either strengthen the BLK × Center claim or break the REB × Center Stan walk-back?

NCAA W's F bucket contains 2,272 players. Among these:
- **453 have height ≥ 75"** (6'3" or taller — the WNBA-derived modern stretch-big threshold scaled to NCAA W).
- **298 hyphenated players** (G-F, F-C, etc.) also enter the candidate pool.

Existing NCAA W §5.7.3 Stan robustness:
- BLK confirmed under Stan: 2/2 cells coupling at p < 10⁻³⁷.
- REB walked back under Stan: 0/2 cells null (parallel to NBA / WNBA Stan walk-back).
- PTS upgraded to 1/2 coupling at p < 0.05 plus 1 directional at p = 0.056.

The NBA Sloan adjudicated result (committed `e52505f`) showed REB × Center 3/3 WALK-BACK FALSIFIED under adjudicated bucketing — the metadata mis-bucketing of modern NBA bigs hid a real REB × Center coupling. This NCAA W pre-registration tests whether the same dynamic governs NCAA W.

The adjudicated Center bucket includes the metadata Center bucket (398 players) as a strict superset plus F-labeled tall players assigned to Center by the adjudicator, minus any metadata Centers reclassified to Forward.

## 2. Locked operationalizations

### 2.1 Substrate scope

- **Seasons:** 2024, 2025 NCAA D1 Women's regular season. Matches §5.7 (Table 5.12) and §5.7.3 (Table 5.16). The 2023 row is empty in the existing tables; not retroactively backfilled.
- **Source:** `C:/NCAA D1 Womens/data/processed/player_game_logs.csv`, regular-season rows for 2024 and 2025.
- **Cohort selection:** per existing NCAA W Test 1 protocol (GP ≥ 10). Cohort read from existing audit `ncaa_wbb_3way_sensitivity.csv`; no re-derivation.
- **Observable space:** BLK, PTS, REB per-game.

### 2.2 Residual baselines

**Surgical arm:** residual = actual − career_mean, matching §5.7 / Table 5.12.

**Stan arm (load-bearing):** residual = actual − E_stan under the existing NCAA W hierarchical NB2 Stan posterior at `C:/NCAA D1 Womens/audit_runs/stan_robustness/ncaa_womens_stan_3_cell.csv`. Read-only.

### 2.3 Position classifier — locked

**Metadata bucket (control):**
- **Center:** `position` string == `C` OR has `C` as the primary token (e.g., `C-F`).
- **Non-Center:** all other position strings.

**Adjudicated bucket (load-bearing, NEW):**

Center-candidate pool:
- All metadata `F` players with `height_inches ≥ 75`: **453 candidates**.
- All metadata `C` players (no height filter, re-judged): **398 candidates**.
- All hyphenated players (`G-F`, `F-C`, `F-G`, `C-F`): **298 candidates**.

**Total NCAA W adjudication scope: 1,149 candidates.**

Counts verified at lock time. Locked at this SHA.

The ~6,519 non-adjudicated players (metadata-G + metadata-F with height < 75") keep their metadata-bucket assignment in the adjudicated arm.

### 2.4 Adjudication method — INDEPENDENT SUBAGENT FLEET

The 1,149 adjudication verdicts are produced by **1,149 independent Sonnet subagents**. Mirrors NBA v1.2 fleet methodology.

**Locked agent prompt template (NCAA W-adapted, fixed at this SHA):**

```
You are adjudicating a single NCAA D1 Women's college basketball player's
best-fit position bucket for a methodology paper substrate. The bucket
choices are:
  Center, Forward, Guard, or no_fit.

You will NOT be told what the methodology paper concludes about position.
Your only job is to pick the bucket that best reflects this player's
on-court archetype across the 2024 and 2025 NCAA D1 Women's seasons,
using ONLY the data provided in this prompt.

Decision criteria (in priority order):
  1. On-court archetype in the 2024-2025 window.
  2. Height: >= 76" (6'4") strongly leans Center; 74-75" can be either
     Forward or Center depending on role; < 74" defaults to Forward at
     this label tier. NCAA D1 Women's center height range is typically
     6'2"-6'8", lower than NCAA Men's. Be calibrated to NCAA W scale.
  3. Career counting-stat profile: high REB / BLK with low AST and low
     FG3M attempts -> Center archetype; balanced REB / AST with moderate
     BLK and modest 3PT activity -> stretch-Forward archetype; high AST
     with low REB -> Guard archetype.
  4. Class year: weight the most recent season heavily for upperclassmen
     (Jr / Sr / Gr); use multi-season averaging for underclassmen.
  5. Hyphenated metadata position string carries information: G-F leans
     Forward, F-C leans Center, F-G leans Forward.
  6. Default to the LOWER-COMMITMENT bucket (Forward over Center) when
     the on-court archetype is genuinely ambiguous.

The `no_fit` disposition: choose `no_fit` ONLY if the player's archetype
is genuinely positionless. Not a fallback when uncertain.

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

Structured output schema: identical to NBA v1.2 / WNBA / NCAA M pre-regs.

### 2.5 Test statistic

Identical to NCAA M pre-reg §2.5: Levene's variance ratio, B=1,000 bootstrap CI, cluster on player, seed 20260601.

### 2.6 Power gate

Per cell: `n_in_adjudicated / n_in_metadata ≥ 1.10`. Same threshold and rationale as NCAA M.

## 3. Tier-1 Hypotheses

Per-cell decision rules identical to NCAA M pre-reg §3. Two seasons (2024, 2025) × three observables × two arms = 12 per-cell × 2 buckets = 24 statistics.

Existing NCAA W metadata cells (Table 5.12 inclusive):
- BLK 2024 ratio 2.03 (p<10⁻³⁷); 2025 ratio 1.76 (p<10⁻²³).
- PTS 2024 ratio 0.98 (p=0.24); 2025 ratio 0.89 (p=0.05 directional).
- REB 2024 ratio 1.20 (p=0.03); 2025 ratio 1.21 (p<0.001).
- REB under Stan (§5.7.3): 0/2 cells couple (walk-back).

H1 BLK × Center: persists / persists-directional / attenuates / regime-null / inverted / inconclusive per [1.26, 2.03] band.
H2 PTS × Center: directional-persists / null / inverted / inconclusive per [0.76, 1.02] band.
H3 REB × Center walk-back: upheld / falsified / falsified-inverted / inconclusive.
H4 power gate sanity: report all 6 cells regardless.

Aggregate H3:
- 2/2 UPHELD → walk-back robust at NCAA W scale.
- ≥ 1 FALSIFIED → walk-back overturned at NCAA W layer. Combined with NBA's already-FALSIFIED 3/3 (and possibly WNBA / NCAA M outcomes), the cross-league §5.4.1 retraction is reopened across multiple leagues.

## 4. Aggregate report framework

Same as NCAA M §4. Cross-league paper revision targets: §5.7 (Table 5.12), §5.7.3 (Table 5.16), §5.4.1 (REB walk-back).

## 5. Discipline guards

1. Threshold adjustment after firing — forbidden.
2. Classifier redefinition — forbidden. Verdicts read from `ncaa_w_position_adjudication_v10.json`.
3. NCAA W Stan re-fit — forbidden.
4. Statistical-test substitution — forbidden.
5. Selective reporting — all 12 per-cell statistics × 2 buckets reported regardless.
6. Walk-back rescue — forbidden.
7. Adding observables — forbidden.
8. Fleet independence — each of the 1,149 subagents adjudicates independently.
9. Lower-commitment default — agent prompt §2.4 instructs adjudicator to default to LOWER-COMMITMENT bucket.
10. Pre-filter scope locked — 1,149 candidates fixed at this SHA. Metadata `F` with height < 75" NOT in scope; remain non-Center.

## 6. Output artifacts

Under `C:/NCAA D1 Womens/audit_runs/test_1_replication/sloan_adjudicated/`:

- `ncaa_w_position_adjudication_v10.json` — 1,149-verdict output.
- `n_in_lift_table.parquet`.
- `variance_ratios_metadata_surgical.parquet`, `variance_ratios_metadata_stan.parquet`.
- `variance_ratios_adjudicated_surgical.parquet`, `variance_ratios_adjudicated_stan.parquet`.
- `dispositions.json`.
- `aggregate_verdict.md`.
- `SLOAN_ADJUDICATED_NCAA_W_RESULTS.md`.

## 7. Timing and commitment

- **Lock event:** git commit to NBAProjections `main`; SHA in `SHA_LOCK.txt`.
- **Adjudication fires:** once, after sign-off. 1,149-Sonnet-subagent fleet via Workflow tool.
- **Analysis fires:** once after adjudication artifact written. Single batch.
- **No re-runs.**

## 8. Sign-off

- **Filed by:** Claude Code (claude-opus-4-7[1m])
- **Sign-off requested from:** mr.nathanhumphrey@gmail.com
- **Repo:** https://github.com/mrnathanhumphrey-droid/NBAProjections
- **Cross-paper anchor SHAs:** NBA `e52505f`; WNBA + NCAA M pre-regs in this session.

---

**End of draft v1.0.**
