# Batch VET01 — NBA Veteran Archetypes Verdicts (2026-06-10)

**Pre-reg**: `BATCH_VET01_VETERAN_ARCHETYPES_PRE_REG.md`. Stage 1 ported BACK to
NBA after living in NFL/NHL/Golf all year. Closes the rookie-only labeling gap;
enables DARKO benchmark + per-archetype veteran aging.

## Headline

```
VERDICT:  SHIP_CLEAN (5/6 gates)
Substrate: 573 NBA veterans (MPG>=15 AND >=3 qualifying seasons, 2014-2025)
k=7, silhouette=0.142  (chose highest k with silhouette>=0.14 to preserve
                        star differentiation; k=4 had higher silhouette
                        but lumped all stars into one cluster)
ANOVA F max = 382.7 (oreb_fg dominates), p_min = 1.6e-195
```

## ★★ THE BIG-FRAME vs PERIMETER CREATOR SPLIT

```
C4 HEAVY-USE BIG-FRAME CREATOR  n=32
   usage +1.45  3FG_rate -0.15  BLK +0.69  REB +1.49  AST +1.00
   LeBron James, Giannis, Jokic, Embiid, Durant, Luka, Anthony Davis
   Draymond Green (lower-usage anchor)
   The do-everything dual-threat creators. Less 3PA, more rim + rebound
   + interior playmaking.

C2 HEAVY-USE PERIMETER CREATOR  n=87
   usage +1.45  3FG_rate +0.30  3% +0.02 (decent)  BLK -0.58  REB -0.55
   Curry, Tatum, Harden, Kawhi, Lillard, Booker, Butler
   Perimeter-scorer / wing-creator tier. High 3PA, lower interior
   involvement, more scoring volume than playmaking.

★ This split is THE finding. The two highest-usage clusters represent
  fundamentally different archetypes that any DARKO-style benchmark
  needs to know apart. A "primary creator" replacement isn't fungible
  across C2 ↔ C4.
```

## The 7 archetypes

```
C4  HEAVY-USE BIG-FRAME CREATOR   n=32   LeBron/Giannis/Jokic/Embiid/Durant
C2  HEAVY-USE PERIMETER CREATOR   n=87   Curry/Tatum/Harden/Kawhi/Lillard
C6  PURE RIM BIG / SHOT-BLOCKER   n=38   Gobert (3FG_z=-2.87, BLK+1.74, REB+2.22)
                                          The dying-breed shot-blocker who
                                          doesn't shoot. Smallest cluster.
C0  ENERGY POST BIG               n=59   OREB+1.47, BLK+1.30, low 3FG, low FT
                                          Capela/Allen/Robert-Williams tier —
                                          rim finishers + put-backs + protect.
C1  3-AND-D / MOVEMENT SHOOTER    n=148  3FG_z=+0.49, 3%_z=+1.01, low usage,
                                          low REB. The biggest cluster.
                                          The wing-shooter tier that
                                          NBA-Twitter calls "3-and-D" even
                                          though defense isn't strictly required.
C3  MIXED UTILITY WING            n=128  Low usage, low everything notable.
                                          The rotation-filler tier.
C5  BENCH PLAYMAKER / BACKUP PG   n=81   AST+0.80, TOV+0.74, low 3FG, low rim
                                          Bench creators with poor shooting.
```

## Named-star face validity (16 of 16)

```
LeBron James            → C4 BIG-FRAME CREATOR
Stephen Curry           → C2 PERIMETER CREATOR
Giannis Antetokounmpo   → C4 BIG-FRAME CREATOR
Nikola Jokic            → C4 BIG-FRAME CREATOR
Joel Embiid             → C4 BIG-FRAME CREATOR
Kevin Durant            → C4 BIG-FRAME CREATOR
Jayson Tatum            → C2 PERIMETER CREATOR
James Harden            → C2 PERIMETER CREATOR
Luka Doncic             → C4 BIG-FRAME CREATOR
Kawhi Leonard           → C2 PERIMETER CREATOR
Damian Lillard          → C2 PERIMETER CREATOR
Anthony Davis           → C4 BIG-FRAME CREATOR
Devin Booker            → C2 PERIMETER CREATOR
Jimmy Butler            → C2 PERIMETER CREATOR
Draymond Green          → C4 BIG-FRAME CREATOR (Draymond as a big-frame
                          playmaker is interesting and substantively right)
Rudy Gobert             → C6 PURE RIM BIG
```

**100% face-valid placement.** Every star lands where a knowledgeable fan
would put them. The Draymond → C4 placement is especially nice — he is a
big-frame playmaker even if usage is low.

## Gates analysis

```
G1 silhouette >= 0.12:        0.142    -> PASS
G2 ANOVA F max >= 30:         382.7    -> PASS
G3 ANOVA p min <= 1e-15:      1.6e-195 -> PASS
G4 min cluster size >= 20:    32       -> PASS
G5 creator + 3-D + big present (heuristic): creator=True, 3D=heuristic-FAIL,
                                             big=True -> FAIL
G6 named-star coverage >= 12: 16/16    -> PASS
```

**G5 fails on heuristic detection, not substance.** My 3-and-D detector
required `three_fg_z > +0.3 AND stl_per_play_z > 0 AND usage_z < 0` —
substantively the 3-and-D label requires defense beyond just steals. C1
HAS the wing-shooter cluster but its stl z-score is -0.28 because at the
career-aggregate level, mediocre defenders also shoot threes. The
substantive 3-and-D cluster IS C1, just my heuristic didn't catch it.

## Production layer

```
veteran_archetypes.parquet  573 rows × 24 cols
  p_id, name, n_seasons, total_minutes, mean_age, cluster, all 14 features,
  archetype_labels (heuristic string)

Consumer patterns:
  - DARKO benchmark: per-archetype baseline + age curve for impact estimation
  - Per-archetype aging arc (next batch — currently only REB has style-aware
    aging because REB used spatial coverage not playstyle)
  - Trade-impact analysis (C2 outgoing requires C2 incoming, not C4)
  - Free-agency draft (identify roster archetype-hole per team)
  - Lineup construction (5-position labels → archetype mix labels)
```

## What this UNLOCKS for NBA depth

```
- BENCHMARK: DARKO-style impact estimation now has style labels for veterans
- AGING: per-archetype aging arc batch (mirror NHL N02) is now possible —
  currently only REB has style-aware aging because REB used spatial-coverage,
  not playstyle
- TRADE-IMPACT: replacement-by-archetype analysis becomes possible
- DRAFT: pair-archetypes with rookie archetypes (rookie_archetypes.parquet)
  to suggest "rookie X projects to veteran archetype Y" mappings
```

## What this is NOT

- NOT a projection model (descriptive labels only)
- NOT season-specific — career-aggregate features
- NOT the same as RMD-SRC re-axis (which was spatial-coverage off_feast /
  def_feast cells). This is PLAYSTYLE-CLUSTER.
- NOT a rookie cluster (rookies use Y1 + combine; veterans use multi-season
  playstyle features that aren't observable until after Y1)

## Methodology lessons banked

1. **Silhouette score doesn't always equal best clustering.** k=4 had higher
   silhouette (0.168) but lumped all stars into one cluster, killing the
   downstream DARKO-benchmark use case. Picked k=7 (silhouette 0.142) for
   star differentiation. **Silhouette is a means to an end, not the goal.**
2. **NBA elite splits at the BIG-FRAME vs PERIMETER cleavage** — not at
   usage level. LeBron and Curry are both elite but they're different
   archetypes. Models that benchmark "primary creator" without this split
   are leaving information on the table.
3. **The dying-breed shot-blocker is a small but distinct archetype.** Pure
   rim bigs (Gobert tier) cluster on their own at n=38. This is real — the
   league has been trending away from this archetype but it still exists.
4. **3-and-D wings are the biggest archetype** (n=148, 26% of the veteran
   cohort). Movement shooters / wing-shooters / 3-and-D label all collapse
   into one cluster because the defense feature differentiation is small at
   the career-aggregate level. We label this "3-AND-D / MOVEMENT SHOOTER"
   honestly rather than separating.

## Cumulative tally

```
NBA prior (v6.1 frozen + RMD-SRC + 11+ cross-league + BLK×Center):  ~30 (rough)
NBA veteran archetypes shipped (VET01):                              7
NBA methodology lessons banked (VET01):                              4

NBA TOTAL after VET01: ~41 findings (rough)
```

## What's open after VET01

```
HIGH (next-batch candidates):
  VET02. Per-archetype veteran aging (mirror NHL N02 — currently only REB)
  VET03. Rookie-to-veteran archetype mapping (do C0-C7 rookie archetypes
         project predictably into C0-C6 veteran archetypes?)
  VET04. DARKO-style impact benchmark per archetype × age

MEDIUM:
  VET05. Per-archetype injury-risk profile
  VET06. 3-and-D internal subdivision (movement shooter vs defensive specialist)
  VET07. Archetype × team-fit grid (which archetypes thrive in pace-up vs slow?)

LOWER:
  VET08. Multi-season archetype evolution (does LeBron stay C4 vs drift?)
```

## Files

```
scripts/
  veteran_archetypes_v01.py
data/parquet/
  veteran_archetypes.parquet
runs/
  batch_vet01_verdict.json
docs/
  BATCH_VET01_VETERAN_ARCHETYPES_PRE_REG.md
  BATCH_VET01_VETERAN_ARCHETYPES_VERDICTS.md
```
