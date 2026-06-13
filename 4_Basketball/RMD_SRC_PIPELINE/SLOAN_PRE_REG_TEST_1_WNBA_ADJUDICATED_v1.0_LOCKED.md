# Pre-Registration — WNBA Adjudicated-Position Test 1 Re-Validation

## Inclusivity Correction on the WNBA Center Cells of the Cross-League Variance-Asymmetry Test

**Date filed:** 2026-06-01
**Filed before:** any inspection of variance ratio, Levene's p, bootstrap CI, or any per-cell statistic on WNBA residuals computed under adjudicated position bucketing. The metadata-bucketed WNBA Test 1 results (cross-league paper §5.6, Table 5.9; §5.6.1, Table 5.10) are visible and locked at their existing reported values; the adjudicated-bucket-derived per-cell statistics have not been computed at any cell level.
**Status:** Sloan-grade Tier-1 pre-registration. Single document covering three Tier-1 hypotheses (BLK × Center, PTS × Center, REB × Center walk-back validation) for the WNBA cells of the cross-league claim. Locks via git commit to the NBAProjections repository. Single-test α = 0.05 per cell, per the existing cross-league paper protocol.
**Sloan paper:** *Partial pooling of residual classes: theory, application to basketball projections, and measurable noise-floor reduction* (working title), draft state at `paper_draft/section_5_empirical_validation.md`. This pre-registration extends §5.6–§5.6.1 with an adjudicated WNBA arm reported alongside the existing metadata arm.
**Cross-paper anchor:** companion to the NBA Sloan adjudicated pre-reg at commit `e52505f` (filed 2026-06-01, locked SHA in `SHA_LOCK.txt`). This WNBA pre-reg shares the cross-league §5 disposition framework but lives as its own SHA-locked document because the adjudication signal stack and prompt template differ from NBA's (no Yahoo eligibility data for WNBA).

---

## 1. Why this exists

The cross-league paper §5.6 reports WNBA Test 1 results under a 3-way classifier sensitivity matrix (inclusive / strict / primary) showing substantive label-sensitivity at the metadata level. Inclusive classifier gives n_in = 24/24/28 across 2023/2024/2025; strict gives n_in = 14/16/18; primary gives n_in = 17/19/22 — a difference of 10-12 players per season cell depending on how hyphenated metadata strings (Forward-Center / Center-Forward / Guard-Forward / Forward-Guard) are bucketed.

Both 3-way classifier variants in §5.6 partition by hyphenation-string parsing — they do not adjudicate on-court archetype. A player labeled `Forward` whose on-court role is paint-5 (e.g., the WNBA analogue of Anthony Davis / Giannis Antetokounmpo) is bucketed as non-Center under all three classifiers, despite carrying a Center on-court archetype that contributes to the variance asymmetry hypothesis.

Independent diagnostic work on the NBA arm under RMD-SRC v1.2 amendment (committed 2026-06-01 at `1bfdb4c`) established that 46 of 230 multi-eligible NBA players were systematically mis-bucketed as Forward by metadata while their on-court archetype is Center. The Sloan adjudicated NBA arm (committed 2026-06-01 at `e52505f`) tested whether this mis-bucketing was driving the cross-league finding's NBA contribution: result was 3/3 BLK × Center PERSISTS, 2/3 PTS × Center DIRECTIONAL-PERSISTS, and 3/3 REB × Center WALK-BACK FALSIFIED — the original §5.4.1 retraction was a power problem hidden by metadata mis-bucketing of 46 modern bigs.

This WNBA pre-registration tests the same question for the WNBA contribution to the 11/11 cross-league claim. The WNBA inclusivity correction is more comprehensive than NBA's: in addition to the 80 metadata-hyphenated players that the existing 3-way classifier sensitivity already addresses, we also adjudicate ~31 metadata-Forward bigs (height ≥ 76") whose on-court archetype may be Center despite the single-token metadata label. We also adjudicate any metadata-Center with unusually short height (height ≤ 73", which yields ~1 candidate per the metadata snapshot).

The adjudicated Center bucket includes the metadata Center bucket as a strict superset plus modern stretch-bigs whose on-court archetype is Center, minus any metadata Centers reclassified to Forward by the adjudication.

## 2. Locked operationalizations

### 2.1 Substrate scope

- **Seasons:** 2023, 2024, 2025 WNBA regular season. Three seasons, exactly matching the existing WNBA cross-season Test 1 design in cross-league paper §5.6 (Table 5.9) and §5.6.1 (Table 5.10).
- **Source:** `C:/WNBA Projections/data/processed/player_game_logs.csv` (basketball-reference player game logs, same as existing §5.6).
- **Cohort selection:** per the existing WNBA Test 1 protocol (qualifying union with GP ≥ 10 per season per cell), exactly matching the cohort used to produce Table 5.9 (surgical) and Table 5.10 (Stan). The cohort definition is read from the existing WNBA audit run at `C:/WNBA Projections/audit_runs/test_1_replication/wnba_sensitivity_3way.csv` row-set; no cohort re-derivation.
- **Observable space:** three per-game stats — BLK, PTS, REB — exactly matching existing Test 1 protocol (not per-36).

### 2.2 Residual baselines (two, one per existing arm)

**Surgical arm:**
- Residual = actual_S(p, g) − career_mean_S(p) computed under the same surgical projection method as cross-league paper §5.6 / Table 5.9.

**Stan arm (load-bearing for walk-back validation):**
- Residual = actual_S(p, g) − E_stan(p, g, S) under the existing WNBA hierarchical NB2 Stan posterior fit reported in §5.6.1 (Table 5.10).
- The Stan posterior is **read-only** at its existing snapshot at `C:/WNBA Projections/audit_runs/stan_robustness/wnba_stan_per_player_projections.csv`. No re-fit. No re-conditioning on adjudicated positions. The model parameters are frozen; only the player → bucket assignment that determines Center vs non-Center for the variance comparison changes.

Both arms are reported in parallel. The walk-back validation hypothesis (H3) is load-bearing on the Stan arm.

### 2.3 Position classifier — locked

**Metadata bucket (control, matching existing §5.6 inclusive classifier):**
- **Center:** `position` string in {`Center`, `Center-Forward`, `Forward-Center`}.
- **Non-Center:** all other position strings.

(The strict and primary classifiers are documented in §5.6 for sensitivity but the load-bearing comparison is metadata-inclusive vs adjudicated, matching the NBA adjudicated pre-reg's two-arm structure.)

**Adjudicated bucket (load-bearing, NEW):**

The adjudication scope is exactly **112 players**, the union of:
- 80 metadata-hyphenated players (any position string containing `-`):
  - 33 Forward-Center
  - 26 Guard-Forward
  - 12 Center-Forward
  - 9 Forward-Guard
- 31 metadata-Forward players with `height_inches ≥ 76` (modern stretch-big candidates)
- 1 metadata-Center player with `height_inches ≤ 73` (small-Center adjudication candidate)

Counts verified against the metadata snapshot at lock time. Adjudication scope is locked at this SHA; adding or removing candidates after seeing per-player residuals is a §5 violation.

The 508 non-adjudicated WNBA players (metadata-Forward height < 76 + metadata-Guard non-hyphenated + metadata-Center height > 73) keep their inclusive-classifier metadata bucket assignment in the adjudicated arm.

### 2.4 Adjudication method — INDEPENDENT SUBAGENT FLEET (mirrors NBA v1.2)

The 112 adjudication verdicts are produced by **112 independent Sonnet subagents**, one per player. No batching, no inter-agent communication, no shared state. This mirrors the NBA v1.2 adjudication method (`AMENDMENT_v1.2_POSITION_ADJUDICATION_LOCKED.md` §2.2) for methodological parity across leagues.

**Locked agent prompt template (WNBA-adapted, fixed at this SHA):**

```
You are adjudicating a single WNBA player's best-fit position bucket for a
methodology paper substrate. The bucket choices are:
  Center, Forward, Guard, or no_fit.

You will NOT be told what the methodology paper concludes about position.
Your only job is to pick the bucket that best reflects this player's
on-court archetype across the 2023 through 2025 WNBA seasons, using ONLY
the data provided in this prompt.

Decision criteria (in priority order):
  1. Career on-court archetype during the 2023–2025 window: where does this
     player primarily defend, and where does the offense use them?
  2. Height: >= 78" leans Center; 75-77" can be Forward or Center
     depending on role; <= 74" leans Guard or stretch-3 Forward. Adjust
     for WNBA scale (WNBA centers are typically 6'4"–6'8").
  3. Metadata position string as a tie-breaker. Hyphenated tokens carry
     information: Forward-Center weights toward Forward primary,
     Center-Forward toward Center primary, etc.
  4. Career counting-stat profile: high REB / BLK with low AST -> Center
     archetype; balanced REB / AST with moderate BLK -> Forward archetype;
     high AST with low REB -> Guard archetype.
  5. WNBA era context: the 2023-2025 window covers the small-ball-friendly
     modern WNBA where stretch-bigs are increasingly common. Default to
     the LOWER-COMMITMENT bucket (Forward over Center) when the on-court
     archetype is genuinely ambiguous.

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
  metadata_bucket_inclusive: <Center | non-Center per WNBA paper §5.6>
  height_inches: <height>
  career_seasons_in_window: <count of 2023/2024/2025 seasons with GP >= 10>
  career_avg_PTS_per_game: <number>
  career_avg_REB_per_game: <number>
  career_avg_AST_per_game: <number>
  career_avg_BLK_per_game: <number>
  career_avg_FG3M_per_game: <number, attempts as proxy for stretch role>
```

**Structured output schema** (enforced via StructuredOutput):

```json
{
  "type": "object",
  "properties": {
    "assignment": {"type": "string",
                    "enum": ["Center", "Forward", "Guard", "no_fit"]},
    "confidence": {"type": "string",
                    "enum": ["high", "medium", "low"]},
    "rationale":  {"type": "string", "maxLength": 600},
    "no_fit_reason": {"type": "string", "maxLength": 400}
  },
  "required": ["assignment", "confidence", "rationale"]
}
```

If any agent fails to return a valid verdict (after the schema's built-in retry), the player is marked `agent_failure` and routed to the metadata bucket. Agent-failure count is reported.

**Decision criteria summary (mirrors agent prompt §2.4):**

1. **Career on-court archetype during the 2023–2025 WNBA window:** where does this player primarily defend, and where does the offense use them? (Read from career box-score signature: REB per game, BLK per game, AST per game, and FG3M per game across the three seasons.)
2. **Height:** ≥ 78" leans Center; 75–77" can be Forward or Center depending on role; ≤ 74" leans Guard or stretch-3 Forward.
3. **Metadata position string as a tie-breaker between two close options.** Hyphenated tokens carry information: `Forward-Center` weights toward Forward primary, `Center-Forward` weights toward Center primary, etc.
4. **Career counting-stat profile:** high REB / BLK with low AST → Center archetype; balanced REB / AST with moderate BLK → Forward archetype; high AST with low REB → Guard archetype. Use per-36 normalization when minutes data is available; otherwise use per-game.
5. **WNBA era context:** the 2023–2025 window covers the small-ball-friendly modern WNBA where stretch-bigs are increasingly common. Modern stretch-Forwards (height ≥ 76") who play paint-5 on defense are the adjudication's primary mis-bucket candidates.

**Bucket choices:** `Center`, `Forward`, `Guard`, or `no_fit`. The `no_fit` disposition routes to a `Positionless` bucket per the NBA v1.2 precedent. (For variance-ratio purposes, `Positionless` is reported separately but treated as non-Center.)

**Output artifact:** the 112 verdicts are aggregated into `C:/WNBA Projections/audit_runs/test_1_replication/wnba_position_adjudication_v10.json` with the same shape as NBA v1.2 (`position_adjudication_v12.json`). This file's SHA256 is recorded in `RMD_SRC_PIPELINE/SHA_LOCK.txt` under a `## Sloan WNBA adjudicated Test 1` section.

### 2.5 Test statistic — Levene's variance ratio (load-bearing)

Per (season, observable, arm), under each bucketing arm (metadata, adjudicated):
- σ_Center = sample SD of residuals across qualifying (Center player, game) records.
- σ_non-Center = sample SD of residuals across qualifying (non-Center player, game) records.
- **Variance ratio = σ_Center / σ_non-Center.**
- **Bootstrap 95% CI on the ratio: B = 1,000 resamples**, cluster on player to preserve player-level variance structure, per existing Test 1 protocol. Seed = 20260601.
- **Levene's test (median-centered) on residual²** — load-bearing.
- p_F (two-sided F-test) and p_Bartlett reported as supplementary.

### 2.6 Power gate (pre-committed)

For each cell, the adjudicated cohort must materially expand the Center population for the cell to be a valid test of the inclusivity correction:

```
n_in_adjudicated / n_in_metadata ≥ 1.20
```

Note: NBA used 1.30 because NBA's adjudication-add was ~46 players against a metadata Center pool of 21–71. WNBA's adjudication-add is smaller (~10–18 players from the ~32 metadata-Forward-height-≥-76 + hyphenated cohorts that pass the GP filter) against a metadata Center pool of 24–28. The 1.20 floor reflects this scale; any tighter and the WNBA cells fail the gate even before firing.

If any cell fails the 1.20 gate, that cell is POWER-LIMITED and reports "inconclusive — adjudication did not materially expand cohort."

## 3. Tier-1 Hypotheses

Three hypotheses, each tested independently per season cell × per arm (surgical, Stan).

### 3.1 H1 — BLK × Center under adjudicated bucketing

Existing claim (cross-league paper §5.6, Table 5.9 / §5.6.1, Table 5.10): σ_Center / σ_non-Center > 1.0 in WNBA at ratios within the cross-league [1.26, 2.03] band. WNBA inclusive cells: 2023 ratio 1.94 (p=0.0002, n_in=24), 2024 ratio 1.91 (p=0.0002, n_in=24), 2025 ratio 1.90 (p<1e-5, n_in=28).

Per-cell decision rule under adjudicated bucketing × Stan arm:

| Condition | Disposition |
|---|---|
| Bootstrap CI on adjudicated ratio overlaps [1.26, 2.03] AND p_levene < 0.05 | **PERSISTS** |
| CI overlaps [1.26, 2.03] AND p_levene ≥ 0.05 | **PERSISTS-DIRECTIONAL** |
| CI below 1.26 but lower bound > 1.0 AND p_levene < 0.05 | **ATTENUATES** |
| CI brackets 1.0 | **REGIME-NULL** |
| CI fully below 1.0 | **INVERTED** |
| Power-limited per §2.6 | **INCONCLUSIVE** |

Aggregate H1 verdict (across 3 WNBA cells, Stan arm):
- 3/3 PERSISTS or PERSISTS-DIRECTIONAL → "BLK × Center WNBA under adjudication: cross-league finding robust at WNBA cohort scale."
- 2/3 PERSISTS → magnitude attenuation in one cell; cross-league claim preserved at the WNBA contribution layer.
- ≤ 1/3 PERSISTS → WNBA contribution to 11/11 claim falsified or weakened.

### 3.2 H2 — PTS × Center under adjudicated bucketing

Existing claim: σ_Center / σ_non-Center < 1.0 in WNBA. Inclusive cells: 2023 ratio 0.94 (p=0.61), 2024 ratio 0.84 (p=0.42), 2025 ratio 1.00 (p=0.97) — all directional or null at WNBA cohort scale, none formally significant.

Per-cell decision rule:

| Condition | Disposition |
|---|---|
| CI overlaps [0.76, 1.02] AND ratio < 1.0 | **DIRECTIONAL-PERSISTS** |
| CI overlaps 1.0 (no clear direction) | **NULL** |
| CI fully > 1.0 | **INVERTED** |
| Power-limited per §2.6 | **INCONCLUSIVE** |

Aggregate H2 verdict: as NBA pre-reg §3.2 framework — 3/3, 2/3, 1/3, 0/3 dispositions.

### 3.3 H3 — REB × Center walk-back validation under adjudicated bucketing

Existing claim (cross-league paper §5.6.1, Table 5.10): WNBA Stan REB × Center does not couple (0/3 cells null under hierarchical NB2 posterior), in contrast to surgical projection which couples 3/3 (Table 5.9 ratios 1.48, 1.39, 1.36, all p < 0.05). The §5.4.1 walk-back framing: surgical/Stan disagreement is method-driven (Stan absorbs position mean into `mu_position[Center]`).

**Alternative reading (the test):** the Stan walk-back is a power problem hidden by metadata Center mis-bucketing. The 10–18 metadata-Forward-but-adjudicated-Center modern WNBA bigs (whose REB profiles cluster with Centers) would resurrect coupling under adjudication.

Per-cell decision rule under adjudicated Stan REB residuals:

| Condition | Disposition |
|---|---|
| CI overlaps 1.0 AND p_levene > 0.05 | **WALK-BACK UPHELD** |
| CI fully > 1.0 AND p_levene < 0.05 | **WALK-BACK FALSIFIED** |
| CI fully < 1.0 | **WALK-BACK FALSIFIED — INVERTED** |
| Power-limited per §2.6 | **INCONCLUSIVE** |

Aggregate H3 verdict:
- 3/3 WALK-BACK UPHELD → walk-back is robust to inclusivity correction at WNBA scale. Cross-league §5.4.1 retraction reinforced at the WNBA contribution layer.
- ≥ 1 WALK-BACK FALSIFIED → walk-back overturned at WNBA layer. If NBA already FALSIFIED 3/3 (which it did, per `SLOAN_ADJUDICATED_RESULTS.md`), and WNBA also FALSIFIES, the cross-league §5.4.1 retraction must be reopened across two leagues.

### 3.4 H4 (power-gate sanity, not a finding)

Per cell, lift = n_in_adj / n_in_meta, gate ≥ 1.20 per §2.6. Report all 9 cells (3 seasons × 3 observables) with lift and gate disposition regardless of outcome.

## 4. Aggregate report framework

After per-cell, per-hypothesis dispositions are determined, the aggregate verdict is reported as a 3 × 3 table (3 hypotheses × 3 cells) under each arm (surgical, Stan).

The two arms are reported in parallel. The Stan arm is the load-bearing arm for the H3 walk-back validation. The surgical arm is reported as the secondary diagnostic showing how the adjudication shifts the surgical-method finding (which was already coupled under metadata).

The cross-league paper revision target is §5.6 (Table 5.9 surgical), §5.6.1 (Table 5.10 Stan), and §5.4.1 (REB walk-back). If H3 returns WALK-BACK FALSIFIED in WNBA in addition to NBA (which it already did), §5.4.1 is reopened across two leagues and the cross-league position-vs-career-stage asymmetry is rewritten as "REB × Center couples cross-league under both surgical and adjudicated-Stan; the Stan walk-back was a metadata-bucketing artifact across leagues."

## 5. Discipline guards

Each item is an explicit pre-registration violation.

1. **Threshold adjustment after firing.** The [1.26, 2.03] BLK band, [0.76, 1.02] PTS band, 1.20 power gate, and per-cell decision-rule conditions are locked.
2. **Classifier redefinition.** The adjudicated bucket is read verbatim from `wnba_position_adjudication_v10.json` once written. Re-running the adjudication, re-judging any verdict, or modifying the override map after seeing residuals is a violation.
3. **Stan model re-fit.** The WNBA Stan posterior at `wnba_stan_per_player_projections.csv` is read-only. No re-fit. No re-conditioning.
4. **Statistical-test substitution.** Levene's variance ratio is load-bearing. Bartlett / F-test are supplementary only.
5. **Selective reporting.** All 18 per-cell statistics (3 seasons × 3 observables × 2 arms surgical/Stan) and both bucketing arms (metadata, adjudicated) are reported regardless of disposition.
6. **Walk-back rescue.** If H3 returns WALK-BACK FALSIFIED, the response is to revise §5.4.1 honestly, not to find a methodology footnote that rescues the walk-back. The cross-league §3 discipline of preserving walk-backs equal-prominence applies to walk-backs OF walk-backs as well.
7. **Adding observables.** BLK, PTS, REB are locked. STL × Center / AST × Center require a new pre-reg.
8. **Fleet independence.** Each of the 112 subagents adjudicates independently; no batching, no shared state, no inter-agent communication. Re-running the fleet after the artifact is written is a violation; any methodological flaw triggers a new pre-reg (v1.1), not a re-fire.
9. **Lower-commitment default.** The agent prompt §2.4 instructs the adjudicator to default to the LOWER-COMMITMENT bucket (Forward over Center) when the on-court archetype is genuinely ambiguous, controlling for any per-agent confirmation bias toward Center over-assignment. Net Center add count is reported in the artifact; if it materially exceeds the NBA flip-rate band (NBA was 46/230 = 20.0% Forward→Center), the artifact is flagged for review (the review does NOT modify the verdicts; it produces a methodology footnote).

## 6. Output artifacts

All outputs under `C:/WNBA Projections/audit_runs/test_1_replication/sloan_adjudicated/`:

- `wnba_position_adjudication_v10.json` — the 112-verdict adjudication output (canonical artifact).
- `n_in_lift_table.parquet` — per (season, observable, arm): n_in_metadata, n_in_adjudicated, lift_ratio, power_gate_pass.
- `variance_ratios_metadata_surgical.parquet`, `variance_ratios_metadata_stan.parquet` — replicates existing §5.6 / §5.6.1.
- `variance_ratios_adjudicated_surgical.parquet`, `variance_ratios_adjudicated_stan.parquet` — load-bearing new.
- `dispositions.json` — per (season, observable, arm, bucket): disposition per §3.
- `aggregate_verdict.md` — the 3 × 3 disposition table under each arm plus the headline narrative.
- `SLOAN_ADJUDICATED_WNBA_RESULTS.md` — the umbrella report. Companion `.docx` produced via existing script.

## 7. Timing and commitment

- **Lock event:** git commit of this file to NBAProjections `main`, commit SHA recorded in `RMD_SRC_PIPELINE/SHA_LOCK.txt` under a `## Sloan WNBA adjudicated Test 1` section.
- **Adjudication fires:** once, after sign-off. 112-Sonnet-subagent fleet via Workflow tool, mirroring NBA v1.2 methodology.
- **Analysis fires:** once, after the adjudication artifact is written. Single batch.
- **No re-runs.** Methodological flaws → new pre-reg, not re-fire.
- **No re-fits of WNBA Stan.**
- **Final report:** `SLOAN_ADJUDICATED_WNBA_RESULTS.md` produced after analysis.

## 8. Sign-off

- **Filed by:** Claude Code (claude-opus-4-7[1m])
- **Sign-off requested from:** mr.nathanhumphrey@gmail.com
- **Repo:** https://github.com/mrnathanhumphrey-droid/NBAProjections
- **Cross-paper anchor SHAs (input):**
  - NBA Sloan adjudicated Test 1 pre-reg: `e52505f`.
  - NBA v1.2 amendment + adjudication artifact: `1bfdb4c` + SHA256 `eb615269f09159e0d0ceaf071812b84750578d81a9a53b01dff5a1ac2ac9dcbd`.
- **Lock event:** rename this file (it is already drafted under the `_LOCKED.md` suffix; lock event is the git commit of this exact path). Append commit-SHA to `SHA_LOCK.txt`.

---

**End of draft v1.0.**
