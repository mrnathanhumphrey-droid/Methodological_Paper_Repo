// Sloan adjudicated Test 1 cross-league adjudication fleet.
// Pre-reg SHA: 28e3dc7 (WNBA + NCAA M + NCAA W pre-regs locked 2026-06-01).
//
// Args: { league: "WNBA" | "NCAA_M" | "NCAA_W",
//         profiles: [<candidate profile objects>],
//         chunk_idx: <int>, chunk_total: <int> }
//
// Each candidate gets one independent Sonnet subagent with the league-specific
// locked prompt template + locked structured-output schema. Returns the list
// of {profile, verdict} pairs for downstream merge into the per-league
// position_adjudication_v10.json artifact.

export const meta = {
  name: 'sloan-cross-league-adjudication',
  description: 'Per-candidate position adjudication for Sloan cross-league Test 1 (one Sonnet subagent per player).',
  phases: [
    { title: 'Adjudicate', detail: 'Independent verdict per candidate' },
  ],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    assignment: { type: 'string', enum: ['Center', 'Forward', 'Guard', 'no_fit'] },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    rationale: { type: 'string', maxLength: 600 },
    no_fit_reason: { type: 'string', maxLength: 400 },
  },
  required: ['assignment', 'confidence', 'rationale'],
}

const PROMPTS = {
  WNBA: (p) => `You are adjudicating a single WNBA player's best-fit position bucket for a methodology paper substrate. The bucket choices are: Center, Forward, Guard, or no_fit.

You will NOT be told what the methodology paper concludes about position. Your only job is to pick the bucket that best reflects this player's on-court archetype across the 2023 through 2025 WNBA seasons, using ONLY the data provided in this prompt.

Decision criteria (in priority order):
  1. Career on-court archetype during the 2023-2025 window: where does this player primarily defend, and where does the offense use them?
  2. Height: >= 78" leans Center; 75-77" can be Forward or Center depending on role; <= 74" leans Guard or stretch-3 Forward. Adjust for WNBA scale (WNBA centers are typically 6'4"-6'8").
  3. Metadata position string as a tie-breaker. Hyphenated tokens carry information: Forward-Center weights toward Forward primary, Center-Forward toward Center primary, etc.
  4. Career counting-stat profile: high REB / BLK with low AST -> Center archetype; balanced REB / AST with moderate BLK -> Forward archetype; high AST with low REB -> Guard archetype.
  5. WNBA era context: the 2023-2025 window covers the small-ball-friendly modern WNBA where stretch-bigs are increasingly common. Default to the LOWER-COMMITMENT bucket (Forward over Center) when the on-court archetype is genuinely ambiguous.

The no_fit disposition: choose no_fit ONLY if the player's archetype is genuinely positionless (truly straddles 2+ buckets without a primary one). no_fit is a real disposition, not a fallback when uncertain.

The player to adjudicate:
  name: ${p.name}
  player_slug: ${p.player_slug}
  metadata_position: ${p.metadata_position}
  metadata_bucket_inclusive: ${p.metadata_bucket_inclusive}
  height_inches: ${p.height_inches ?? 'null'}
  career_seasons_in_window: ${p.career_seasons_in_window}
  career_avg_PTS_per_game: ${p.career_avg_PTS_per_game ?? 'null'}
  career_avg_REB_per_game: ${p.career_avg_REB_per_game ?? 'null'}
  career_avg_AST_per_game: ${p.career_avg_AST_per_game ?? 'null'}
  career_avg_BLK_per_game: ${p.career_avg_BLK_per_game ?? 'null'}
  career_avg_FG3M_per_game: ${p.career_avg_FG3M_per_game ?? 'null'}

If career averages are null because the player did not play in the 2023-2025 window, adjudicate from metadata position and height alone, and set confidence appropriately.`,

  NCAA_M: (p) => `You are adjudicating a single NCAA D1 Men's college basketball player's best-fit position bucket for a methodology paper substrate. The bucket choices are: Center, Forward, Guard, or no_fit.

You will NOT be told what the methodology paper concludes about position. Your only job is to pick the bucket that best reflects this player's on-court archetype across the 2024 and 2025 NCAA D1 Men's seasons, using ONLY the data provided in this prompt.

Decision criteria (in priority order):
  1. On-court archetype in the 2024-2025 window: defense and offense role.
  2. Height: >= 82" (6'10") strongly leans Center; 80-81" can be either Forward or Center depending on role; < 80" defaults to Forward at this label tier. NCAA D1 Men's center height range is typically 6'8"-7'0", lower than NBA. Be calibrated to the NCAA scale.
  3. Career counting-stat profile: high REB / BLK with low AST and low FG3M attempts -> Center archetype; balanced REB / AST with moderate BLK and modest 3PT activity -> stretch-Forward archetype; high AST with low REB -> Guard archetype.
  4. Class year: a senior with a defined role gives stronger signal than a freshman whose role is unsettled. Weight the most recent season's archetype heavily for upperclassmen; use multi-season averaging more for underclassmen.
  5. Default to the LOWER-COMMITMENT bucket (Forward over Center) when the on-court archetype is genuinely ambiguous. The Center bucket is for paint-bound 5s; do not assign stretch-4s to Center.

The no_fit disposition: choose no_fit ONLY if the player's archetype is genuinely positionless. Not a fallback when uncertain.

The player to adjudicate:
  name: ${p.name}
  player_slug: ${p.player_slug}
  metadata_position: ${p.metadata_position}
  metadata_bucket_inclusive: ${p.metadata_bucket_inclusive}
  height_inches: ${p.height_inches ?? 'null'}
  class_year_2024: ${p.class_year_2024 ?? 'null'}
  class_year_2025: ${p.class_year_2025 ?? 'null'}
  career_avg_PTS_per_game: ${p.career_avg_PTS_per_game ?? 'null'}
  career_avg_REB_per_game: ${p.career_avg_REB_per_game ?? 'null'}
  career_avg_AST_per_game: ${p.career_avg_AST_per_game ?? 'null'}
  career_avg_BLK_per_game: ${p.career_avg_BLK_per_game ?? 'null'}
  career_avg_FG3M_per_game: ${p.career_avg_FG3M_per_game ?? 'null'}
  career_avg_FG3A_per_game: ${p.career_avg_FG3A_per_game ?? 'null'}

If career averages are null because the player did not play in the 2024-2025 window, adjudicate from metadata position and height alone, and set confidence appropriately.`,

  NCAA_W: (p) => `You are adjudicating a single NCAA D1 Women's college basketball player's best-fit position bucket for a methodology paper substrate. The bucket choices are: Center, Forward, Guard, or no_fit.

You will NOT be told what the methodology paper concludes about position. Your only job is to pick the bucket that best reflects this player's on-court archetype across the 2024 and 2025 NCAA D1 Women's seasons, using ONLY the data provided in this prompt.

Decision criteria (in priority order):
  1. On-court archetype in the 2024-2025 window.
  2. Height: >= 76" (6'4") strongly leans Center; 74-75" can be either Forward or Center depending on role; < 74" defaults to Forward at this label tier. NCAA D1 Women's center height range is typically 6'2"-6'8", lower than NCAA Men's. Be calibrated to NCAA W scale.
  3. Career counting-stat profile: high REB / BLK with low AST and low FG3M attempts -> Center archetype; balanced REB / AST with moderate BLK and modest 3PT activity -> stretch-Forward archetype; high AST with low REB -> Guard archetype.
  4. Class year: weight the most recent season heavily for upperclassmen (Jr / Sr / Gr); use multi-season averaging for underclassmen.
  5. Hyphenated metadata position string carries information: G-F leans Forward, F-C leans Center, F-G leans Forward.
  6. Default to the LOWER-COMMITMENT bucket (Forward over Center) when the on-court archetype is genuinely ambiguous.

The no_fit disposition: choose no_fit ONLY if the player's archetype is genuinely positionless. Not a fallback when uncertain.

The player to adjudicate:
  name: ${p.name}
  player_slug: ${p.player_slug}
  metadata_position: ${p.metadata_position}
  metadata_bucket_inclusive: ${p.metadata_bucket_inclusive}
  height_inches: ${p.height_inches ?? 'null'}
  class_year_2024: ${p.class_year_2024 ?? 'null'}
  class_year_2025: ${p.class_year_2025 ?? 'null'}
  career_avg_PTS_per_game: ${p.career_avg_PTS_per_game ?? 'null'}
  career_avg_REB_per_game: ${p.career_avg_REB_per_game ?? 'null'}
  career_avg_AST_per_game: ${p.career_avg_AST_per_game ?? 'null'}
  career_avg_BLK_per_game: ${p.career_avg_BLK_per_game ?? 'null'}
  career_avg_FG3M_per_game: ${p.career_avg_FG3M_per_game ?? 'null'}
  career_avg_FG3A_per_game: ${p.career_avg_FG3A_per_game ?? 'null'}

If career averages are null because the player did not play in the 2024-2025 window, adjudicate from metadata position and height alone, and set confidence appropriately.`,
}

const { league, profiles, chunk_idx, chunk_total } = args

if (!PROMPTS[league]) {
  throw new Error(`Unknown league: ${league}. Must be WNBA, NCAA_M, or NCAA_W.`)
}

const promptBuilder = PROMPTS[league]

log(`Sloan cross-league adjudication: ${league} chunk ${chunk_idx}/${chunk_total} - ${profiles.length} candidates`)

phase('Adjudicate')

const verdicts = await parallel(
  profiles.map((p, idx) => () =>
    agent(promptBuilder(p), {
      label: `${league}:${chunk_idx}:${idx}:${p.player_slug}`,
      schema: VERDICT_SCHEMA,
      model: 'sonnet',
    }).then(v => ({
      profile: p,
      verdict: v,
    })).catch(err => ({
      profile: p,
      verdict: null,
      agent_failure_reason: String(err).slice(0, 200),
    }))
  )
)

const n_total = verdicts.length
const n_success = verdicts.filter(v => v.verdict !== null).length
const n_failed = verdicts.filter(v => v.verdict === null).length

const bucket_counts = {}
for (const v of verdicts) {
  if (v.verdict) {
    const a = v.verdict.assignment
    bucket_counts[a] = (bucket_counts[a] || 0) + 1
  }
}

log(`${league} chunk ${chunk_idx}/${chunk_total}: ${n_success}/${n_total} success, buckets: ${JSON.stringify(bucket_counts)}`)

return {
  league,
  chunk_idx,
  chunk_total,
  n_total,
  n_success,
  n_failed,
  bucket_counts,
  verdicts,
}
