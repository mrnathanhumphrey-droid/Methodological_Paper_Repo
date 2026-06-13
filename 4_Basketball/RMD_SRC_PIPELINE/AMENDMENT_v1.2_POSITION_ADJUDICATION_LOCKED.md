# Amendment v1.2 — Position bucket adjudication for multi-eligible players

**Type:** New analytical arm pair (additive). Does NOT amend or retract any operationalization, threshold, falsifier, or disposition in `PRE_REG_NBA_RMD_SRC_FULL_LOCKED.md` (v1.0, SHA `db0ed9a899c28691183cd5b640f460c10f3c2a75`) or `AMENDMENT_v1.1_MPG_TIER_PARALLEL_ARM_LOCKED.md` (v1.1, SHA `4d0602df832d5a45402a212acf48b19a4dfee070`). The v1.0 usage-tier and v1.1 MPG-tier arms stand as the canonical first-two arms; this amendment adds two adjudicated-position arms (`usg_adj`, `mpg_adj`) and a Positionless 4th-position bucket.

**Authored:** 2026-06-01.
**Status:** DRAFT v1.2 — pre-sign-off. Lock event is a git commit of this file (renamed to `AMENDMENT_v1.2_POSITION_ADJUDICATION_LOCKED.md`) plus an update to `SHA_LOCK.txt` recording the amendment commit-SHA. The adjudication agent fleet does not fire until this SHA exists.
**Author:** Claude Code (claude-opus-4-7[1m]).
**Filed before:** any inspection of any cell-level statistic that depends on the adjudication outcome. The Yahoo eligibility data was inspected at the count level (230 adjudication targets identified) and at the bucket-set distribution level. No observable values were inspected in the process of writing this amendment.

## 1. Why this exists

The v1.0 / v1.1 partition uses the inclusive Test 1 classifier on `player_metadata_enriched.position` strings. That classifier handles hyphenated metadata strings (`C-F`, `F-C`) cleanly — but the qualifying-union for 2019-26 contains zero hyphenated strings. The modern NBA metadata pipeline assigns single canonical position labels (Center, Forward, Guard) that systematically lose hybrid-big and hybrid-wing information.

Yahoo eligible-position data covers this gap for 496 of the 792 qualifying-union players:
- **196 are multi-bucket** under the inclusive Test 1 → bucket projection: their Yahoo eligibilities span 2 or 3 position buckets.
- **34 are single-bucket but disagree with metadata**: Yahoo says Forward only, metadata says Center, or similar.
- **266 are single-bucket and agree with metadata**: no adjudication needed.
- **296 have no Yahoo eligibility data**: default to metadata single-label (as v1.0 / v1.1).

The 230 multi-bucket or disagreement cases are the adjudication targets. For each, the metadata's single-label assignment is potentially wrong — but the right answer is not "put them in all eligible buckets" (that breaks the residue-class disjoint-partition assumption load-bearing for RMD-SRC, as discussed in the v1.1 sign-off thread). The right answer is per-player adjudication with auxiliary signal: height, era, Yahoo primary position, career rebound / assist / block / 3PT profile.

**The kick-back disposition is first-class.** Some adjudication targets will be flagged by the adjudicator as **`no_fit`** — too positionless for any of Center / Forward / Guard to be the best fit. The adjudication output preserves that disposition; `no_fit` players route to a new 4th position bucket called **`Positionless`**.

The `Positionless` bucket is itself a testable substrate hypothesis. If the bucket materializes with enough volume to clear the sparse-cell floor and survives Step 3 response validation, its regime classification per observable becomes a substantive finding about modern positionless basketball — a substrate finding distinct from the Center / Forward / Guard residue classes.

## 2. Locked operationalizations

### 2.1 Adjudication scope

The full scope is exactly **230 players** in the 2019-26 qualifying union, comprising:
- 196 with multi-bucket Yahoo eligibility (≥ 2 of {Center, Forward, Guard} implied)
- 34 with single-bucket Yahoo eligibility that disagrees with the v1.0 / v1.1 metadata bucket

The 562 non-adjudicated players (296 No-Yahoo + 266 Yahoo-agrees-metadata) keep their v1.0 / v1.1 bucket assignment in the adjudicated arms. Their bucket assignment is preserved verbatim from `P0_partition_{usg,mpg}.parquet`.

### 2.2 Adjudication agent fleet

One independent general-purpose subagent per player. 230 agents total. Each agent receives exactly one player's profile and returns exactly one structured verdict. No batching, no inter-agent communication, no shared state.

### 2.3 Locked adjudication agent prompt template

The template is fixed at this SHA. Any modification to the prompt requires a new amendment.

```
You are adjudicating a single NBA player's best-fit position bucket for a
methodology paper substrate. The bucket choices are:
  Center, Forward, Guard, or no_fit.

You will NOT be told what the methodology paper concludes about position.
Your only job is to pick the bucket that best reflects this player's
on-court archetype across the 2019-20 through 2025-26 NBA seasons,
using ONLY the data provided in this prompt.

Decision criteria (in priority order):
  1. Career on-court archetype during the 2019-26 window: where does this
     player primarily defend, and where does the offense use them?
  2. Height: > 6'10" leans Center; 6'7" - 6'10" can be either Forward or
     Center depending on role; < 6'7" leans Guard or stretch-3 Forward.
  3. Yahoo primary_position as a tie-breaker between two close options.
  4. Career counting-stat profile: high REB / BLK with low AST → Center
     archetype; balanced REB / AST with moderate BLK → Forward archetype;
     high AST with low REB → Guard archetype.
  5. Era and rotation context: a player who debuted before 2010 may have
     played a different role earlier than what defines them in the
     2019-26 window. The window is what matters.

The `no_fit` disposition: choose `no_fit` ONLY if the player's archetype
is genuinely positionless in the 2019-26 window (truly straddles 2+
buckets without a primary one). `no_fit` is a real disposition, not a
fallback when uncertain. If you can pick a primary bucket with even
modest confidence, do so.

Output exactly this JSON shape (no other text):
{
  "assignment": "Center" | "Forward" | "Guard" | "no_fit",
  "confidence": "high" | "medium" | "low",
  "rationale": "<one paragraph, 2-4 sentences>",
  "no_fit_reason": "<populated only if assignment is no_fit>"
}

The player to adjudicate:
  name: <player_name>
  metadata_position: <metadata position string>
  metadata_bucket_v1: <Center | Forward | Guard from v1.0 inclusive Test 1>
  yahoo_eligible_positions: <comma-separated list>
  yahoo_primary_position: <primary or null>
  height_inches: <height>
  debut_year: <year>
  last_seen_season: <season>
  career_avg_REB_per36: <number>
  career_avg_AST_per36: <number>
  career_avg_BLK_per36: <number>
  career_avg_FG3M_per36: <number>
```

### 2.4 Structured output schema (StructuredOutput tool enforced)

The adjudication workflow uses the StructuredOutput tool with this schema:

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

If any agent fails to return a valid verdict (after the schema's built-in retry), the player is marked `agent_failure` and routed to the v1.0 / v1.1 metadata bucket. Agent-failure count is reported in the substrate ledger.

### 2.5 Adjudication output artifact

The 230 verdicts are written to `RMD_SRC_PIPELINE/results/position_adjudication_v12.json` as a list of objects:

```json
{
  "locked_at_sha_v12": "<v1.2 SHA, recorded in SHA_LOCK.txt>",
  "verdicts": [
    {
      "nba_api_id": <int>,
      "name": "<player name>",
      "metadata_bucket_v1": "<Center|Forward|Guard>",
      "adjudicated_bucket": "<Center|Forward|Guard|Positionless>",
      "confidence": "<high|medium|low>",
      "rationale": "<agent's paragraph>",
      "no_fit_reason": "<empty unless Positionless>"
    },
    ...
  ]
}
```

This file's SHA256 is recorded in `MANIFEST.txt` and is the load-bearing audit artifact for v1.2's downstream arms. Re-running the adjudication after the file is written is a §6 violation.

`adjudicated_bucket == "Positionless"` is the case where the agent returned `assignment: "no_fit"`. The `Positionless` label is the substrate name; `no_fit` is the agent's verdict naming.

### 2.6 Position axis grows: 3 → 4 buckets

The adjudicated arms (`usg_adj`, `mpg_adj`) use a 4-bucket position axis:
- **Center**: as in v1.0, plus adjudication-bucketed Center.
- **Forward**: as in v1.0, plus adjudication-bucketed Forward.
- **Guard**: as in v1.0, plus adjudication-bucketed Guard.
- **Positionless**: the adjudication's `no_fit` verdicts.

The Cartesian product grows: 4 positions × 4 years-pro × 3 role-cohort = **48 candidate cells**. The sparse-cell collapse rule is unchanged (< 50 player-seasons total OR < 5 in any season → merge with nearest neighbor, preferring role-cohort then years-pro then position).

**Adjacency map (Positionless)**: Positionless has no natural position-axis adjacency to Center / Forward / Guard. The collapse rule for sparse Positionless cells: walk role-cohort first, then years-pro. **Positionless does NOT merge to Center / Forward / Guard via the position axis.** If a sparse Positionless cell has no Positionless-internal merge candidate (all Positionless cells exhausted), it is reported as `un_collapsible_Positionless` in the substrate ledger and dropped from the partition; the player-seasons it contained are reported separately as substrate-shape data.

### 2.7 Pipeline observables, time axis, train/holdout, decomposition gates, falsifier thresholds

All identical to v1.0 / v1.1:
- Observables: PTS_per36, REB_per36, AST_per36, BLK_per36.
- Time axis: 7 seasons, 2019-20 → 2025-26.
- Train: 2019-20 → 2023-24. Holdout: 2024-25 + 2025-26.
- Step 2 thresholds: `ε_μ = 0.02`, `ε_σ² = 0.05`.
- Step 4a axes: `opp_DEF_RTG_tertile` and `home_away` (two-axis, ≥ 0.10 cleanness gate).
- F1 ≥ 0.90, F2 < 0.50, F3 < 0.30, F4 κ < 0.40.
- Step 5: r ≥ 0.80 (partition-level signature transfer).
- Comparative arm vs v6.1 LOCKED: per-cell regime-label recovery, per-cell r ≥ 0.50.

## 3. Cross-arm comparison expansion

The v1.1 cross-arm κ matrix was 2-way (usg × mpg). v1.2 expands it to a **4-arm regime-agreement matrix** per observable:

| | usg | mpg | usg_adj | mpg_adj |
|---|---|---|---|---|
| usg | 1.00 | κ | κ | κ |
| mpg | κ | 1.00 | κ | κ |
| usg_adj | κ | κ | 1.00 | κ |
| mpg_adj | κ | κ | κ | 1.00 |

Six off-diagonal Cohen κ values per observable × 4 observables = 24 κ values. Locked agreement bands (κ ≥ 0.60 high, [0.30, 0.60) partial, < 0.30 low) carry over from v1.1 §3.1.

**Specific contrasts of substantive interest, pre-committed:**
- **`usg` vs `usg_adj`** isolates the adjudication's effect on regime classification, controlling for role-cohort definition. If κ ≥ 0.60, adjudication's effect on regime is small at the cohort scale; if κ < 0.30, the adjudication substantially changes per-cell regime labels.
- **`mpg` vs `mpg_adj`** same logic for the MPG-tier arm.
- **`usg_adj` vs `mpg_adj`** is the post-adjudication two-arm comparison; expected to be similar to `usg` vs `mpg` in v1.1 if adjudication is consistent across cohort definitions.

## 4. Comparative arm vs v6.1 LOCKED — 4-arm version

Each of the four arms produces its own PASS / TIE / LOSE verdict per cell vs v6.1 LOCKED, per v1.0 §9. The headline cross-arm differential is reported as four columns:

| (cell × observable) | v1.0 (usg) verdict | v1.1 (mpg) verdict | v1.2 (usg_adj) verdict | v1.2 (mpg_adj) verdict |

A row where the metadata-bucketed arms (usg, mpg) PASS while the adjudicated arms (usg_adj, mpg_adj) LOSE indicates that the metadata's mis-bucketing was producing an artifactual PASS; the honest verdict per cell is what the adjudication produces. Reported in the substrate ledger as a finding regardless of frequency.

## 5. Adjudicated arm Positionless-bucket reporting commitments

The Positionless bucket is reported with the following pre-committed dispositions:

- **n_Positionless = 0** (no agent returned `no_fit`): the adjudication confirms the 3-bucket position partition is sufficient. Reported as substantive negative for the Positionless hypothesis.
- **0 < n_Positionless < SPARSE_TOTAL_FLOOR (50)**: Positionless cells collapse along role-cohort/years-pro axes. Reported as substrate-shape data with the per-player list named in the ledger.
- **n_Positionless ≥ 50** with at least one (Positionless × years-pro × role-cohort) cell surviving the sparse-cell floor: regime classification runs on the surviving cell(s). The regime label per observable becomes a substantive finding about positionless-basketball substrate.

All three dispositions are publishable. The headline disposition is reported in the substrate ledger.

## 6. Discipline guards

- **v1.0 and v1.1 results stand at their SHAs.** No file at SHA `db0ed9a` or `4d0602d` is modified. P0_partition_{usg,mpg}.parquet, P0_collapse_map_{usg,mpg}.json, P0_diagnostic_{usg,mpg}.md remain as v1.0 / v1.1 artifacts.
- **The adjudication agent fleet runs once.** Re-running the adjudication after `position_adjudication_v12.json` is written invalidates v1.2's downstream arms. If a methodological flaw in the adjudication is discovered, the response is a new amendment (v1.3) with a different adjudication protocol, not re-running v1.2.
- **No retroactive prompt edits.** The agent prompt template at §2.3 is locked. Any modification (re-wording, additional decision criteria, different signal set) requires v1.3.
- **`no_fit` is the agent's verdict, not the analyst's.** No human intervention modifies any verdict. Agent failure (schema-invalid output after retry) routes to v1.0 metadata bucket, not to Positionless.
- **The 230-player scope is locked.** Adding or removing adjudication targets after seeing the verdict distribution is a violation.
- **No cherry-picking by confidence.** Low-confidence verdicts are treated the same as high-confidence verdicts. The confidence field is reported but does not gate the verdict's effect on the partition.

## 7. Outputs (v1.2 artifacts)

All under `RMD_SRC_PIPELINE/results/`:

- `position_adjudication_v12.json` — the 230-verdict adjudication output.
- `P0_partition_usg_adj.parquet` — usg arm with adjudicated position bucketing.
- `P0_collapse_map_usg_adj.json`
- `P0_diagnostic_usg_adj.md`
- `P0_partition_mpg_adj.parquet` — mpg arm with adjudicated position bucketing.
- `P0_collapse_map_mpg_adj.json`
- `P0_diagnostic_mpg_adj.md`
- (Subsequent steps: per-arm trajectory / classification / decomposition artifacts with `_usg_adj` and `_mpg_adj` suffixes.)
- `crossarm_regime_kappa_4way.json` — 4-arm κ matrix.
- `crossarm_PASS_TIE_LOSE_4col.parquet` — 4-arm PASS/TIE/LOSE per cell per observable.
- `crossarm_F1_F4_4way_matrix.json` — F1–F4 firings per arm.

## 8. Sign-off

- **Filed by:** Claude Code (claude-opus-4-7[1m])
- **Sign-off requested from:** mr.nathanhumphrey@gmail.com
- **Repo:** https://github.com/mrnathanhumphrey-droid/NBAProjections
- **Lock event:** rename this file to `AMENDMENT_v1.2_POSITION_ADJUDICATION_LOCKED.md`; git add; git commit; append the new commit-SHA to `RMD_SRC_PIPELINE/SHA_LOCK.txt` under a `## v1.2 amendment` section. Then spawn the 230-agent adjudication fleet via the Workflow tool. Then re-run Step 0/1 with `--arm usg_adj` and `--arm mpg_adj`. Then proceed to Step 2 on all four arms.

---

**End of draft v1.2.**
