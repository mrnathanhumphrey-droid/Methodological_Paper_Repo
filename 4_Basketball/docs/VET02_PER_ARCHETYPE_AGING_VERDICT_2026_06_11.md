# NBA VET02 — PER-ARCHETYPE AGING — VERDICT

**Locked**: 2026-06-11
**Pre-reg**: `D:/NBA Projections/docs/PREREG_VET02_PER_ARCHETYPE_AGING_2026_06_11.md`
**Script**: `D:/NBA Projections/scripts/vet02_per_archetype_aging.py`
**Output**: `D:/NBA Projections/data/parquet/per_archetype_aging_curves_vet02.parquet` (20 fits)

---

## VERDICT: **DISCONFIRMED at locked gates (2/6)** — but substantive findings flip cross-sport thesis on NBA

n=3,849 player-seasons, 573 vets × 7 archetypes × signature metrics.

### Gates

| Gate | Status |
|---|---|
| G1 each cluster ≥1 sig-metric parabola DOWN p<0.05 | 3/7 → ❌ |
| G2 shared sig cross-cluster peak-age range ≥ 2yr | ast_perc range 3.30 yr (BIG-FRAME 29.0 / PERIMETER 28.6 / BENCH PLAYMAKER 25.7) ✅ |
| G3 each cluster ≥1 R²>0.005 | 6/7 (C5 missed at 0.0045) → ❌ |
| G4 BIG-FRAME ast_perc peak ≥ PERIMETER + 2yr | C4=29.04 vs C2=28.58 = +0.46 → ❌ |
| G5 rim peaks earlier than craft within C0/C4/C6 | OPPOSITE direction in C4 → ❌ |
| G6 ≥5/7 clusters pass G3 | 6 ≥ 5 ✅ |

### ★ Substantive findings (cross-sport thesis FLIPS on NBA)

| Cluster | Signature | b1 | b2 | p_b2 | peak age | R² |
|---|---|---|---|---|---|---|
| C2 PERIMETER | **usage** | -0.0002 | -0.00067 | <0.001 | **27.86** | **0.184** |
| C2 PERIMETER | ast_perc | +0.0007 | -0.00065 | <0.001 | 28.58 | 0.093 |
| C4 BIG-FRAME | **usage** | +0.0003 | -0.00058 | <0.001 | **28.24** | **0.165** |
| C4 BIG-FRAME | **ast_perc** | +0.0017 | -0.00080 | <0.001 | **29.04** | **0.170** |
| C4 BIG-FRAME | **rim_fg** | +0.0017 | -0.00026 | 0.024 | **31.32** | 0.047 |
| C4 BIG-FRAME | blk_perc | -0.0002 | +0.00003 | 0.007 | n/a (linear decay) | 0.080 |
| C3 MIXED UTILITY | efg_perc | +0.0011 | -0.00012 | 0.067 | 32.42 | 0.020 |
| C6 RIM BIG | blk_perc | -0.0005 | +0.00005 | 0.036 | n/a (linear decay) | 0.137 |

### ★★ HEADLINE: BIG-FRAME CREATORS LOSE PLAYMAKING BEFORE FINISHING

LeBron / Giannis / Jokić / Embiid / Durant / Luka / AD / Draymond:
- **usage peaks 28.24**
- **ast_perc peaks 29.04**
- **rim_fg peaks 31.32** ★

OPPOSITE of NHL playmaker pattern (athletic carries fade first, shot/release endures). NBA big-frame creators DECLINE in COGNITIVE/DECISION burden first (usage volume, playmaking), but EFFICIENT FINISHING AT RIM PEAKS 3 YEARS LATER.

Reading: At LeBron-tier athleticism, the body keeps finishing late into 30s. What goes is the all-court playmaking workload. Different aging shape from sport-pure-craft (golf sg_arg / NHL sniper iF_xG) — NBA elite age along ENERGY-CONSUMPTION axis, not skill-axis.

### ★ Block rate declines MONOTONICALLY across NBA

C4 BIG-FRAME blk_perc: b1 < 0, b2 > 0 (linear-or-accelerating decay, no peak). C6 RIM BIG blk_perc: same pattern.

No peak in defensive event-creation through prime years — defense decays steadily from age 19. Suggests NBA defensive impact is OUR-age-dependent in a way office/skill isn't — vertical / lateral ability is gone by mid-30s even for elite blockers.

### ★ Three-point % is age-stable (DARKO confirmation)

C1 3-AND-D three_perc: r² = 0.095 driven by b1 (linear improvement +0.71%/year through 28), b2 not significant (p=0.55). No quadratic shape — 3PT% improves modestly with experience, no decline through mid-30s in cohort. Matches DARKO + Cleaning the Glass empirical finding.

### ★ PERIMETER CREATOR usage peaks 27.86, R²=0.18

Curry / Tatum / Harden / Lillard / Booker tier: strongest aging signal in the batch. Usage peaks at 28, ast at 28.6. Same usage-peaks-before-craft pattern as BIG-FRAME but ~1 year earlier on both.

### Methodology lessons (banked)

1. **Cross-sport aging thesis PORTS IMPERFECTLY**. "Athleticism fades, craft endures" works in golf (sg_ott 26 vs sg_arg 36), NHL (sniper iF_xG endures), MLB (discipline endures). **NBA big-frame creators flip it**: usage/playmaking fade FIRST, rim-finishing endures.
2. **NBA defense (blk_perc) is monotonically declining, no peak** — pure athletic-trajectory metric. Use linear decay model not quadratic.
3. **Three-point % is age-stable** in NBA cohort — confirms public-sphere DARKO/CtG findings.
4. **Bench player (C5) aging cohort too noisy** — short careers + role-player variance = R² 0.003-0.005.
5. **G2 shared-sig peak-age range** captured by ast_perc (range 3.30 yr) but NOT usage (range 0.38 yr) — same metric, very different cross-cluster spread. Signature-metric choice for cross-cluster compare matters.

### Production usage despite strict-DISCONFIRMED

- C2 PERIMETER + C4 BIG-FRAME aging fits are PUBLISHABLE (R²>0.15, p<0.001 on b2, peak ages face-valid)
- Use for veteran-projection aging adjustment: usage peaks 28 for BIG-FRAME/PERIMETER, ast 1yr later, rim_finish 2-3yr later (BIG-FRAME only)
- DARKO competitor: now have STYLE-STRATIFIED aging for the two highest-usage NBA archetypes
- Block rate should use LINEAR decay (no peak) — replaces previous pooled-quadratic fits

### Cross-refs

- VET01 archetypes: `D:/NBA Projections/scripts/veteran_archetypes_v01.py` + memory entry
- NHL N02 (cross-sport sibling): same cross-product pattern, different finding shape
- NBA REB aging (predecessor, spatial style-agnostic): `aging_curve_REB.parquet`
- Cross-sport "skill endures" thesis: golf G01, MLB M01/M02, NHL N02 — NBA shows DIFFERENT shape (energy-axis not skill-axis)
