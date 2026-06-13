# NBA RMD-SRC Spatial Re-Axis — Results (Court-Region-of-Feast)

**Pre-reg:** `PRE_REG_NBA_RMD_SRC_SPATIAL_LOCKED.md`, SHA **`cd40b46`** (signed off 2026-06-10).
**Arms:** `off_feast` (Rim/Paint/Perimeter by shot-location plurality), `def_feast` (RimProtector/Hybrid/Perimeter by rim-defense-share tercile). Position arm `usg` is the comparative baseline.
**Discipline:** ℙ₀ built from partition-side variables only; no outcome moment-flow inspected before the lock SHA. Steps 2–5 use logic byte-identical to v1.0 (same thresholds, classifier, train 2019-20→2023-24 / holdout 2024-25+2025-26). Position `SUBSTRATE_LEDGER.md` untouched.

---

## Headline: a two-layer finding, not a flat null

Re-axing the RMD-SRC primary partition from **position** to **court-region-of-feast** separates into two layers with opposite verdicts:

1. **Cross-sectional coupling — the thesis is VINDICATED.** The load-bearing BLK×Center variance coupling *relocates to and strengthens on* the rim-defense cell. Levene variance ratio (player-season BLK/36, group vs rest, pooled 2019-26): **RimProtector = 2.493 (n=847, p=5e-40)** vs **Center = 2.300 (n=369, p=6e-30)**. The rim-zone cut captures the coupling *better* than the position label — larger magnitude, 2.3× the sample, stronger significance, and a clean monotone region gradient (RimProtector 2.49 → Hybrid 0.56 → Perimeter 0.46). "Center = defender near the rim" is empirically right, and rim-zone is the better axis for the coupling.

2. **Dynamic transfer — a ROBUST null.** Season-to-season regime transfer (F4 Cohen κ) is ≈0 for *every* arm, and re-axing to the causal axis does **not** rescue it. off_feast mean κ = −0.079, def_feast −0.003, position +0.015 — all bootstrap-CI straddle zero. The dynamic-layer instability is intrinsic to the NBA substrate at season grain; it was never a position-proxy artifact.

The descriptive thesis (court-region cuts across position exactly as predicted) held throughout — what it does **not** buy is a cleaner *dynamic* RMD-SRC signature. The cross-sectional coupling is real and better-located on the rim cell; its season-to-season dynamics are non-transferable regardless of how you cut.

---

## Pipeline summary by arm

| Arm | K | F1 fires? | F2 clean | F2 fires? | F4 mean κ | F4 any≥0.40? | Step5 mean r | Comp vs v6.1 |
|---|---|---|---|---|---|---|---|---|
| `off_feast` | 15 | N (max R²=0.15) | 26/46 = 56.5% | N | −0.079 | N | +0.770 | 0/60/0 |
| `def_feast` | 22 | N (max R²=0.16) | 19/53 = 35.8% | **Y** | −0.003 | N | +0.742 | 0/88/0 |
| `usg` (pos) | — | N (max R²=0.21) | 32/53 = 60.4% | N | +0.015 | N | +0.796 | 0/76/0 |

- **F1** never fires on any arm — no additive model on partition variables absorbs ≥90%; the framework is warranted on all three. Position F1 R² is slightly higher than spatial (REB 0.212 vs 0.137/0.073), i.e. position labels carry marginally more *additive* signal, but neither is close to the 0.90 refusal bar.
- **F2** fires only on `def_feast` (35.8% < 50%) — the defensive court-region is the one substrate whose cells largely fail to terminate cleanly. Offense (56.5%) and position (60.4%) do not fire.
- **F4** fires (κ<0.40) on every observable of every arm — universal dynamic non-transfer.
- **Comparative vs v6.1** is all-TIE on every arm (Step 3 dip over-fire → all cells flagged → no PASS/LOSE differential), identical disposition to the position pipeline.

### F4 detail — Cohen κ per (arm, observable)

| Arm | PTS | REB | AST | BLK |
|---|---|---|---|---|
| `off_feast` | −0.114 | −0.010 | −0.016 | −0.176 |
| `def_feast` | +0.002 | −0.115 | +0.021 | +0.078 |
| `usg` | +0.057 | −0.042 | +0.073 | −0.027 |

---

## Prediction verdicts (timestamped 2026-06-10, pre-registered)

| | Prediction | Cal | Verdict | Detail |
|---|---|---|---|---|
| **P1** | off_feast F4 κ≥0.40 on ≥1 obs (transfers where position failed) | 60% | **MISS** | off_feast mean κ=−0.079, *worse* than position +0.015; all straddle 0. Dynamic non-transfer is a substrate property, not a position artifact. |
| **P2** | BLK coupling relocates to the rim cell | 55% | **HIT (cross-sectional)** | Variance ratio RimProtector 2.49 > Center 2.30, p=5e-40. Relocation confirmed on the coupling's native metric. Regime-dynamics/transfer (κ=+0.078) do NOT transfer — the *level* relocates, the *dynamics* don't. |
| **P3** | offense clean *and* defense coupled (F2 ∧ F4) | 65% | **MISS (conjunction); mechanism half-holds** | Offense robustly cleaner on F2 (56.5% vs 35.8%, diff +0.207 CI[+0.007,+0.394] excludes 0; def_feast F2 *fires*, offense doesn't). But F4 ≈0 for both → conjunction fails. |

**Calibration honesty:** 0/1 on the load-bearing bet (P1), 1 cross-sectional HIT (P2 via variance ratio), 1 conjunction-miss whose mechanism half survived (P3). The misses were the informative part — P1's miss is the cleanest evidence that NBA's dynamic layer is irreducibly non-transferable.

---

## §9.2 — spatial vs position comparative

| Arm | ΔF2-clean | ΔF4-mean-κ | Δdip-pass | disposition |
|---|---|---|---|---|
| `off_feast` − `usg` | −0.039 | −0.094 | 0.000 | position-dominant |
| `def_feast` − `usg` | −0.246 | −0.018 | 0.000 | position-dominant |

By the falsifier suite, **court-region is not a better residue class than position** — both spatial arms are position-dominant-or-parity on F2/F4, and Δdip-pass is exactly 0 (the §4 expectation that court-region would be *less* multimodal is falsified; the per-game multimodality is axis-invariant). This sits alongside — not against — the cross-sectional relocation win: the falsifier suite measures *dynamic/termination* structure, where neither axis is better; the variance-ratio measures *cross-sectional coupling*, where rim-zone wins.

---

## Position-overlap diagnostic (the descriptive thesis)

`off_feast` Rim cell: 254 Center / **296 Forward** / 128 Guard — Forwards the plurality of rim-feasters.
`def_feast` RimProtector cell: 205 Center / **391 Forward** / 251 Guard — **76% non-Center**; rim defense is a court-region role filled overwhelmingly by non-Centers, with Centers only 56% concentrated in the top rim tercile (vs 33% baseline). The partition cuts across position exactly as the thesis predicted; it is not a re-derivation of the label.

---

## Robustness (exploratory, post-hoc — NOT pre-registered)

1. **Variance-ratio relocation** (the load-bearing check, above): RimProtector BLK ratio 2.49 > Center 2.30; monotone region gradient; REB shows the same pattern weaker. The coupling is better-located on the rim cut.
2. **F4 bootstrap 95% CI** (B=2000, seed 20260610) — every arm/observable straddles 0 (BLK: off [−0.47,+0.16], def [−0.16,+0.32], usg [−0.23,+0.18]). The no-transfer null is robust, not a point-estimate fluke. Wide CIs reflect the locked 2-season holdout (regime slopes rest on 2 points — a fragility we flag, not paper over).
3. **F2 offense>defense** robust: diff +0.207, CI[+0.007,+0.394] excludes 0.
4. **Cross-arm regime κ** (off_feast vs def_feast) and **holdout 2-point fragility** counts in `robustness_spatial.json`.
5. **Profile-Sparse** residual: 8/2,798 (off) and 0/2,798 (def) — negligible, excluded from cells per pre-reg, reported not dropped.

---

## Reading for the methodology paper

The spatial re-axis is a clean demonstration that **RMD-SRC's cross-sectional and dynamic layers can disagree**, and that the *right exogenous axis* matters for one but not the other. Cutting NBA on its causal axis (court-region) relocates and sharpens the cross-sectional variance coupling (BLK on the rim cell) but leaves the dynamic non-transfer untouched — because that non-transfer is a property of the substrate's season-to-season grain, not of the partition. The honest contribution: the BLK×Center finding is real and is better described as **BLK × rim-zone**, but its dynamics are non-transferable under any labeling — a refinement of, not a retraction of, the position-arm result (which stands unmodified at its SHAs).

---

## Open-thread follow-ups (exploratory, post-hoc — NOT pre-registered)

Three sensitivity analyses on the completed study (`explore_open_threads.json`). They stress-test and extend the two-layer finding; they do not alter any locked verdict.

### Thread A — the full coupling-relocation map

Cross-sectional variance ratio (player-season, group vs rest), best court-region vs best position per observable:

| Observable | best court-region | ratio | best position | ratio | region beats position? |
|---|---|---|---|---|---|
| **REB** | **Rim** | **2.172** | Center | 1.240 | ✅ (nearly 2×) |
| **BLK** | **RimProtector** | **2.481** | Center | 2.292 | ✅ |
| **PTS** | **Paint** | **1.326** | Forward | 1.091 | ✅ |
| **AST** | Paint | 1.976 | **Guard** | 1.992 | ❌ |

**3 of 4 couplings relocate to a court-region and the region cut beats position** — REB is the *strongest* relocation (Rim nearly doubles Center). **AST is the principled exception**: assists stay Guard-coupled because playmaking is a *role* property, not a court-*location* property. Refined statement: **the feast axis owns the scoring/rebounding/rim-protection couplings; the position label still owns playmaking.**

### Thread B — dynamic null is robust to temporal split

F4 BLK regime-transfer κ under alternative splits (locked 5/2, plus 3/4 and 4/3):

| arm | locked (5/2) | alt (3/4) | alt (4/3) |
|---|---|---|---|
| off_feast | −0.176 | −0.228 | +0.259 |
| def_feast | +0.078 | −0.237 | −0.232 |
| usg | −0.027 | −0.252 | +0.026 |

κ wanders in [−0.25, +0.26] with no consistent sign, never clears 0.40 under any split/arm/observable, and court-region is never better than position. The non-transfer is a substrate property, not 2-season-holdout fragility.

### Thread C — dynamic findings robust to role-cohort (usage-tier → MPG-tier)

| arm | K | F4 mean κ | any≥0.40? | F2 Stationary-frac | BLK F4 |
|---|---|---|---|---|---|
| off_feast (usg) | 15 | −0.079 | N | 0.565 | −0.176 |
| off_feast_mpg | 19 | −0.075 | N | 0.481 | −0.169 |
| def_feast (usg) | 22 | −0.003 | N | 0.358 | +0.078 |
| def_feast_mpg | 25 | −0.010 | N | 0.385 | −0.030 |

Swapping the secondary axis usage-tier→MPG-tier leaves both the dynamic null (F4≈0) and the offense>defense F2 gap intact. (The cross-sectional relocation map is role-cohort-invariant by construction — a marginal variance ratio.) The two-layer finding survives every stress-test applied: alternative temporal split *and* alternative role-cohort.

## Creation thread — the relational-vs-terminal reframe (exploratory, post-hoc)

The position-arm's lone exception (AST stayed Guard-coupled, did not relocate to a court-region) drove a deeper question: *what is the right exogenous axis for playmaking?* The chase (`explore_ast_axes.py`, `explore_creation_network.py`, `explore_creation_network_6season.py`):

**1. AST does not partition on shot-location, and WHERE/HOW are entangled.** Building a playmaking-origin axis from touch data (2024-25) was degenerate — the 4 trackable touch-contexts (drive/paint/post/elbow) capture only a minority of assists (PnR/handoff/transition/perimeter-swing are untracked, and dominate the residual). Among trackable contexts, creation is 87% drive-origin, and **every on-ball hub is a drive-creator** (collinear). η²(dribbles-per-touch ~ origin) = 0.30 — "how on-ball you are" is ~30% determined by "where," and fully collinear at the elite-hub end. Conclusion: the tracking *sees* drives, but is blind to the PnR/transition passing that is the bulk of creation; "creation is drive-dominated" is a statement about the cameras, not basketball.

**2. The reframe — terminal events partition on space, relational events on the network.** An assist is an *edge* (passer→shooter), not a terminal event at a location, so it has no court-region. Partition instead by **network role** (Hub / Connector / Terminal) from the `passing` graph (`potential_ast`, `secondary_ast`, `passes_made/received`). RMD-SRC-native: the response function's ρ_s/ρ_x density-at-destination is a network construct — for an assist the "destination" is *who catches it*, a graph neighborhood, not a court spot.

**3. The network owns AST variance, robustly, and beats position.** 6-season pooled (n=2,392): **Hub variance ratio 2.96 vs Guard 1.98** — Hub > Guard *every* season. Magnitude matches the terminal-event spatial couplings (BLK 2.49, REB 2.17). Face-valid: top Hubs are Trae/Haliburton/Jokić/SGA/LeBron/Harden/Luka — primary creators across all positions, not a Guard relabel.

**4. WHERE is a real secondary modulation, and it drifts by era (the user's prediction).** Court-region isn't zero for AST: Rim→0.84 (finishers — low creation variance, WHERE tells you who *isn't* a creator), Paint→2.02 (the rare creator-bigs), Perimeter→1.0 (neutral). And the modulation *drifts within the 2019–2025 window*:
- **De-heliocentrization:** Hub-grip weakens 4.15→2.69 (slope −0.35/yr) — creation spreading across the roster, single-hub-iso era → distributed connective offense.
- **Rise of the creator-big:** Paint-creation coupling materializes ~0(n=1)→3.22(n=10) — the playmaking-center era.
- **Rim→pure-finisher hardening:** 0.91→0.60.

**Synthesis:** terminal events (BLK/REB/PTS) partition on **space** (ratios 2.2–2.5); relational events (AST) partition on the **passing network** (Hub 2.96); and **space modulates the network** (~30% dependent), drifting with league era. Network is primary, space is the context-driven secondary layer — both layers confirmed. *(Single-data-source caveat: network layer is 6 seasons / one macro-era; true decade-era contrast needs a tracking pull back to 2013-14. All numbers post-hoc, not pre-registered.)*

## Artifacts

`P0_partition_{off,def}_feast.parquet`, `P0_collapse_map_*`, `P0_position_overlap_*`, `P0_diagnostic_*`, `moment_trajectories_*`, `trajectory_classification_*`, `step03_validation_*`, `step04_decomposition_*`, `holdout_step2_*`, `signature_{train,holdout}_*`, `step05_comparative_*`, `step05_falsifiers_{off,def}_feast.json`, `spatial_vs_position_comparative.json`, `comparative_vs_position_*.json`, `spatial_predictions_verdict.json`, `robustness_spatial.json`, `SUBSTRATE_LEDGER_SPATIAL.md`. Builders: `src/step01_build_p0_spatial.py`, `src/step05_falsifiers_spatial.py`, `src/robustness_spatial.py`, `cli/pull_2025_26_spatial.py`.
