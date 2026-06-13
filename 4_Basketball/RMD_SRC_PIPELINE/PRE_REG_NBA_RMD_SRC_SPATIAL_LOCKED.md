# Pre-Registration — NBA RMD-SRC Spatial Re-Axis (Court-Region-of-Feast Partition)

**Substrate:** NBA per-game player statistics (regular season), re-axed on **where the player feasts on the court** rather than nominal position.
**Status:** LOCKED — signed off by mr.nathanhumphrey@gmail.com 2026-06-10. The lock event is the git commit of this file to `main`; the commit-SHA is recorded under `## spatial re-axis` in `RMD_SRC_PIPELINE/SHA_LOCK.txt` and is the load-bearing discipline gate. No outcome-moment-flow compute fires before that SHA exists.
**Author:** Claude Code (claude-opus-4-8[1m]).
**Filed before:** any inspection of any (μ, σ²) trajectory, regime label, response coefficient, F1–F4 firing value, or comparative-arm metric on the PTS/REB/AST/BLK observables under the spatial partition. The partition-construction smoke test (2026-06-10, §1.3) inspected only shot-location and defensive-contest distributions — i.e. the partition-side variables — and **zero outcome (PTS/REB/AST/BLK) moment-flow statistics**. The pre-reg wall (RMD-SRC Step 0: ℙ₀ built from observables independent of the modeled outcome, locked before outcome statistics) is intact.
**Companion:** additive to `PRE_REG_NBA_RMD_SRC_FULL_LOCKED.md` (v1.0, SHA `db0ed9a899c28691183cd5b640f460c10f3c2a75`) and its amendments v1.1–v1.3. This re-axis does NOT modify, retract, or re-score any artifact at those SHAs.

---

## 1. Why this exists

### 1.1 The thesis

The position-partition pipeline established that the load-bearing structural cell in NBA — across four leagues — is **BLK × Center** (variance-ratio band [1.64, 2.01]), with **REB × Center** [1.24, 2.37] and **PTS × Center** directional ~0.83. The v1.2 amendment existed precisely because metadata position labels mis-bucket the players who carry this signal: 48 players flipped buckets under adjudication, every flip a case where the nominal label and the on-court reality disagreed.

The hypothesis of this re-axis: **"Center" is a lossy positional proxy for a court-region role — "the player who operates near the rim."** The BLK × Center coupling is not a property of the position label; it is a property of **the rim zone**, populated by players of every position. If that is true, partitioning the substrate on **court-region-of-feast** (the causal axis) rather than position (its proxy) should:

- recover the same structural coupling, re-attached to the rim cell rather than the Center cell;
- come out **cleaner on the dynamic layer** — the position partition *failed* F4 regime-transfer (κ ≈ ±0.02 on all observables) and Step 3 dip-over-fired at 100% ("mixed cleanness, sub-positions emerged"). The RMD-SRC reading of that failure is *position is a fragmenting aggregate*. Court-region, if it is the true residue class, should transfer where position did not.

### 1.2 What is being swapped

Exactly one thing: the **primary partition axis**, position → court-region-of-feast. The secondary axes (years-pro, role-cohort), the four observables, the time axis, the train/holdout split, and every F1–F4 / Step-2 / Step-5 threshold are **held identical to v1.0** so that the comparison isolates the effect of the axis swap. The observables are *not* changed — the whole point is to ask whether the **same** PTS/REB/AST/BLK come out cleaner under a court-region partition than under position.

### 1.3 Partition-side smoke test (2026-06-10, informs §2.2 bucket definitions, pre-lock)

Read-only, partition-construction-only (no outcome moment-flow). Findings that motivate the locked bucket rules below:

- **Offensive feast cuts across position.** 2023-24 plurality-zone × position confusion: rim-feasters were 89 Forwards / 69 Centers / 35 Guards; above-break-3 feasters were 116 Guards / 75 Forwards / **12 stretch Centers**. The spatial cut is **not** a re-derivation of the position label.
- **Plurality-of-5-zones is sparse** (Paint 28 / Corner3 10 / Mid 5 in-season) → the locked offensive rule collapses to **3 regions** (§2.2.1).
- **The court binary is balanced:** Interior (Rim+Paint) 226 vs Perimeter 220 in-season — the literal "split the court" cut, both far above the n≥50 floor.
- **Defensive rim-protection also cuts across position:** deduped 2023-24 RimProtector tercile = 63 Center / 62 Forward / 46 Guard (more non-Center than Center). Centers only 61% concentrated in the top rim tercile (vs 33% baseline).
- **Stability asymmetry (drives §7 predictions):** offensive Interior/Perimeter binary is **86.0% sticky** season-to-season (1567/1823 consecutive pairs); defensive RimDef/PerimDef is **67.8% sticky** (1484/2188). The offensive court-region is a clean time-axis; the defensive one is noisier.

---

## 2. Locked operationalizations

### 2.1 Data scope (identical to v1.0 §2.1 except where the spatial partition requires additions)

- **Seasons:** 2019-20 through 2025-26 inclusive (seven). The spatial source parquets were extended to **full seven-season coverage** on 2026-06-10 via `cli/pull_2025_26_spatial.py` (idempotent append of 2025-26 Regular Season: 582 shot-location / ~580 def-zone player rows, in line with prior seasons). Partition and outcome sides now both span seven seasons; the seven-season split (§2.5) is the locked case.
- **Games:** regular-season only. Playoffs/play-in excluded (governed by `PRE_REGISTRATION_NBA_PLAYOFFS_25_26.md`, not amended here).
- **Outcome source parquet:** `D:/NBA Projections/data/parquet/historical_box_scores.parquet` (locked at HEAD at lock time) — **the same file as v1.0.**
- **Partition source parquets (NEW):**
  - Offensive feast: `data/parquet/shot_locations_player.parquet` (zone FGA).
  - Defensive feast: `data/parquet/player_def_zone_lt6.parquet` + `data/parquet/player_def_zone_overall.parquet` (defensive contest FGA by zone).
- **Player inclusion (outcome side, identical to v1.0):** ≥ 20 games AND ≥ 10 MPG in the season. Partition computed per (player, season).
- **Player inclusion (partition side, NEW, locked):** to receive a court-region assignment a player-season must additionally clear a **profile-stability floor** — offensive arm: ≥ 50 total zone FGA in the season; defensive arm: ≥ 3.0 defensive contests per game (`d_fga_overall / gp ≥ 3.0`). A player-season clearing the outcome filter but not the partition floor is **routed to a `Profile-Sparse` residual bucket**, reported in the substrate ledger and excluded from cell-level conclusions (not silently dropped).
- **Traded-player dedup (locked):** partition zone counts are **summed across all team rows within a (player, season)** before computing shares. (The smoke test's first defensive pass cross-multiplied team rows — 1,161 rows for a 763-row season; the locked rule sums them to 561 clean profiles.)

### 2.2 P0 partition (Step 0/1) — TWO parallel spatial arms

Both arms use the axis structure **court-region × years-pro × role-cohort**, swapping only the court-region definition. Years-pro and role-cohort are **verbatim from v1.0 §2.2** (Rookie/Soph-Early/Mid/Deep-vet; High/Mid/Low usage-tier on prior-season USG%, rookie→Mid default).

#### 2.2.1 Arm `off_feast` — offensive court-region (3 regions)

Per (player, season), normalize zone FGA to shares over `{ra, paint, mid, lc3, rc3, ab3}` (deduped per §2.1). Assign region by the locked rule:

- **Rim** — `ra` share is the plurality (restricted-area feast: rim-runners, slashers).
- **Paint** — `paint` (non-RA paint) share is the plurality (post/floater feast).
- **Perimeter** — plurality among `{mid, lc3, rc3, ab3}` (any perimeter zone, 2 or 3) exceeds both `ra` and `paint` (spacing/shot-creation feast).

The **Interior = Rim ∪ Paint** binary is the headline "split the court" reading; the 3-region split is the partition that runs the pipeline. Region adjacency for sparse-cell collapse is **linear: Rim ↔ Paint ↔ Perimeter** (Rim and Perimeter are not directly adjacent).

#### 2.2.2 Arm `def_feast` — defensive court-region (3 regions)

Per (player, season), compute **rim-defense share** `= d_fga(lt6) / d_fga(overall)` (deduped per §2.1). Assign region by **within-season tercile** of rim-defense share among partition-floor-clearing players:

- **RimProtector** — top tercile of rim-defense share.
- **Hybrid** — middle tercile.
- **Perimeter** — bottom tercile.

Within-season terciles are the locked rule (reproducible, balanced-by-construction, and computed on the partition-construction variable — the defensive contest distribution — never on a modeled outcome). Region adjacency for collapse is **linear: RimProtector ↔ Hybrid ↔ Perimeter**.

*Rationale for differing rules across arms:* offensive feast has a natural discrete zone-argmax; defensive rim-share is continuous, so terciles are the natural discretization. Each is the canonical rule for its data shape; both are absolute/reproducible and locked here.

#### 2.2.3 Cells and collapse (both arms)

Cartesian product per arm: **3 region × 4 years-pro × 3 role-cohort = 36 candidate cells.** Sparse-cell collapse rule is **identical to v1.0 §2.2**: a cell with < 50 player-seasons total OR < 5 in any single season merges with its nearest neighbor, preferring **role-cohort first, then years-pro, then region** (region collapse follows the linear adjacency above). Final K is data-determined and logged to `P0_collapse_map_{off_feast,def_feast}.json`.

#### 2.2.4 Exogeneity argument (the load-bearing methodological guard)

RMD-SRC Step 0 requires ℙ₀ independent of the **outcome** being modeled. The court-region is built from shot-**location-shape** (zone *shares*) and defensive-contest-**distribution**, not from the level observables:

- **PTS/REB/AST/BLK_per36 are level/rate outcomes; the partition is distribution-shape.** A rim-feaster and a perimeter-feaster can both score 20/36; a rim-feaster and a perimeter-feaster can both grab 8 REB/36. The partition does not mechanically determine the outcome level.
- **Cleanest cases are fully independent:** `off_feast` (offensive partition) × BLK_per36 (defensive outcome); `def_feast` (defensive partition) × {PTS, AST, FG3}.
- **The one related pair — `def_feast` × BLK_per36 — is the intended test, not a confound:** rim-defense *share* (contest distribution) and BLK *rate* (block conversions) are related but distinct (a high-rim-contest player may convert few blocks). The RMD-SRC question — does BLK variance *concentrate over time* within the rim cell — is well-posed and is precisely the relocation of the BLK × Center coupling we are testing. This dependence is documented here ex ante and is **not** a partition-redefinition pathway.

### 2.3 Observables (identical to v1.0 §2.3, LOCKED unchanged)

PTS_per36, REB_per36, AST_per36, BLK_per36. Per-36 normalization. Four parallel pipeline runs per arm; Bonferroni α = 0.0125 for any cross-observable significance claim; per-observable falsifier thresholds are absolute and not Bonferroni-adjusted.

### 2.4 Time axis (identical to v1.0 §2.4)

Season axis. For each (cell, observable, season), μ_s and σ²_s are the cell-membership-weighted sample mean and variance over qualifying (player, game) outcome records. **Note:** a player's *cell membership can change season-to-season* as their feast region shifts (86% offensive / 68% defensive stickiness, §1.3) — this is intended; the trajectory is a property of the **cell**, populated by whichever players feast there that season, not of a fixed roster.

### 2.5 Train / holdout split

- **LOCKED (seven-season):** train **2019-20→2023-24** (5 seasons), holdout **2024-25 + 2025-26** (2 seasons). Identical to v1.0. (The 2025-26 spatial vintage is present as of the 2026-06-10 pull, so this is the operative split; the six-season fallback contemplated in the v0.1 draft is moot.)

Step 2 labels, Step 3 coefficients, Step 4 decomposition, and the comparative posterior fit on the training window only. Holdout reserved for F4, Step 5, and comparative per-cell recovery.

## 3. Step 2 — five-regime trajectory taxonomy

**Identical to v1.0 §3** in every operational detail: OLS μ̇ and σ̇² on season-index; normalized rates `r_μ`, `r_σ²`; thresholds **`ε_μ = 0.02`, `ε_σ² = 0.05`**; the deterministic five-regime + Edge classifier (Stationary / Concentrating / Diffusing / Contracting / Drifting / Edge) exactly as v1.0 §3.2. Edge cells reported separately, excluded from F2/F4 headlines.

## 4. Step 3 — response validation

**Identical to v1.0 §4:** (1) Hartigan dip on the pooled within-cell distribution, PASS if `p_dip ≥ 0.05`; (2) permutation-stability over the training-season index, PASS if modal regime in ≥ 60%; (3) LOSO over training seasons, PASS if ≥ 3/5 (≥ 3/4 in the six-season fallback) folds agree. Clean = all three PASS.

**Pre-committed expectation (not a threshold change):** v1.0's Check-1 dip over-fired at 100% — a substrate-shape signature of pooled multimodality. The spatial re-axis's directional prediction (§7 P1) is that court-region cells are **less multimodal** than position cells (cutting on the causal axis reduces within-cell heterogeneity). The dip-pass fraction under the spatial partition vs the position partition is a reported headline. The threshold itself is unchanged.

## 5. Step 4 — decomposition

**Identical to v1.0 §5** (4a → 4b → 4c, applied only to response-validated non-Stationary cells). 4a candidate axes **`opp_DEF_RTG_tertile`** and **`home_away`**, ≥ 0.10 absolute cleanness-improvement gate, deterministic resolution. 4b continuous covariate `prior_season_per36_value_self`, R² ≥ 0.30 reduction + flip-to-Stationary. 4c null. All three outcomes publishable. The 4a candidate set is exhausted at two axes; a third is a §11 violation.

## 6. Step 5 — held-out transfer

**Identical to v1.0 §6:** per-(cell, observable) 4-tuple signature (regime label, σ_within, ρ_LOSO, β_role-cohort); refit Step 2+3 on holdout; **partition-level mean Pearson r ≥ 0.80** across the four signature columns over K cells = PASS.

## 7. Step 6 — mechanism inference + BOLD prospective predictions (timestamped 2026-06-10)

Per the user's standing posture on bold, justified, pre-registered predictions, three prospective-tier claims are committed **now, before any outcome compute**:

- **P1 — the headline falsifiable bet: court-region transfers where position did not.** At least one observable under the `off_feast` arm achieves **F4 κ ≥ 0.40** (clearing the transfer falsifier that the position partition *failed* at κ ≈ ±0.02 on all four observables). *Justification:* offensive court-region is 86% time-sticky vs position's failed transfer; if it is the true residue class, regime labels should persist across windows. **Calibration: 60%.** A miss (spatial F4 also < 0.40) is the strongest evidence that the NBA dynamic layer is irreducibly non-transferable regardless of axis — itself publishable.
- **P2 — the BLK coupling relocates to the rim cell.** Under `def_feast`, the **BLK_per36 × RimProtector** cell classifies as Concentrating or Stationary-tight, and its within-cell BLK variance-ratio against the partition baseline lands in the position-arm's established BLK × Center band-direction (tightening). *Justification:* the BLK × Center coupling is, by thesis, a rim-zone property; the RimProtector cell is the rim zone, populated 63C/62F/46G. **Calibration: 55%.**
- **P3 — the cross-current: offense is the clean substrate, defense carries the coupling but not the cleanness.** The `off_feast` arm reports a **higher F2 clean fraction** and **higher mean F4 κ** than the `def_feast` arm. *Justification:* offensive feast is 86% sticky, defensive 68%; the cleanest spatial substrate is offensive, but the load-bearing coupling (BLK × rim) lives in the noisier defensive substrate. **Calibration: 65%.** This directional contrast, if it holds, *is* the Step-6 mechanism signature: court-region is a clean residue class on the side where role is self-selected (where you shoot) and a noisy one on the side where role is scheme-imposed (whom you guard).

Retrospective-tier (named after Step 4) and post-hoc-tier (named after Step 5) mechanisms are forward-watch only, per v1.0 §7.

## 8. F1–F4 falsifier suite (paper-canon thresholds, LOCKED identical to v1.0 §8)

F1 fires if additive-model R² ≥ 0.90 on any observable. F2 fires if clean-termination fraction `n_clean/(K×4) < 0.50`. F3 fires if successful-sub-partition `R²_sub < 0.30`. F4 fires if regime-label Cohen κ < 0.40 on any observable. All four reported per observable per arm with bootstrap 95% CI (B=1000 cell-resample), regardless of firing.

## 9. Comparative arm — TWO comparisons

### 9.1 vs Traditional partial pooling (v6.1 LOCKED) — identical to v1.0 §9

Per-(cell, observable) PASS/TIE/LOSE against the v6.1 LOCKED posterior (Method B verdict synthesized as "Stationary"; per-cell transfer r ≥ 0.50 for PASS). v6.1 is used as-deployed; no re-tuning.

### 9.2 vs the position partition (NEW) — the axis-swap comparative

The locked position-arm results (`usg` / `usg_adj` at SHAs in `SUBSTRATE_LEDGER.md`) are the read-only baseline. Per observable, the spatial arms are scored against the position arm on three pre-committed metrics:

- **Δ F2 clean fraction** (spatial − position): does court-region terminate cleaner than position?
- **Δ F4 κ** (spatial − position): does court-region transfer where position did not?
- **Δ Step-3 dip-pass fraction** (spatial − position): is court-region less multimodal than position?

**Disposition (pre-committed, all publishable):**
- **Spatial-dominant** (Δ > 0 and Δ F4 κ crosses 0.40 on ≥ 1 observable): court-region is a better residue class than position for NBA. The methodology paper's NBA §4.2 gains a substrate-refinement finding — *the position partition was a proxy; the causal axis is court-region.*
- **Parity** (Δ ≈ 0): position and court-region are interchangeable axes; the BLK coupling is axis-invariant. Reported honestly.
- **Position-dominant** (Δ < 0): the nominal label carries information the spatial shape does not (e.g. defensive scheme assignment beyond contest distribution). Reported honestly; would falsify the §1.1 thesis.

## 10. Preservation of prior work (NON-OVERWRITE)

No file at v1.0/v1.1/v1.2/v1.3 SHAs is modified or re-scored. The position arms (`usg`, `mpg`, `usg_adj`, `mpg_adj`) stand as the canonical position application. This re-axis is additive: it adds two spatial arms (`off_feast`, `def_feast`) to the substrate ledger. The cross-league Sloan adjudicated results and the BLK/REB/PTS × Center findings stand unmodified; this pre-reg *tests a relocation hypothesis* about them, it does not retract them.

## 11. Discipline guards (explicit violations)

- **Threshold adjustment after firing:** every threshold in §3–§9 is locked identical to v1.0. Adjusting any after compute invalidates the affected outcome.
- **Partition-rule adjustment:** the offensive plurality-of-3-regions rule (§2.2.1), the defensive within-season-tercile rule (§2.2.2), the profile-stability floors (≥50 FGA / ≥3 contests/g), and the traded-player sum-dedup are locked. Switching offensive to a binary, or defensive to absolute thresholds, after seeing cell behavior is a violation — a new rule requires a new pre-reg.
- **Region-count change:** 3 regions per arm is locked. Splitting Perimeter into Mid/Corner3/AB3, or merging Rim/Paint, post-hoc is a violation (it is available *only* as a Step-4a categorical sub-partition, which is itself outside the locked 4a candidate set and therefore a new-pre-reg item).
- **Observable substitution / window adjustment / third 4a axis / selective F1–F4 reporting / selective comparative reporting / Method-B re-tuning / post-hoc mechanism promotion:** all violations, identical to v1.0 §11.
- **Outcome peeking before lock:** any inspection of PTS/REB/AST/BLK moment-flow under the spatial partition before the lock SHA exists invalidates the pre-registration.
- **Arm cherry-picking:** both `off_feast` and `def_feast` arms, all four observables, all K cells, contribute to every headline. Reporting only the cleaner arm is a violation.

## 12. Output artifacts

All under `RMD_SRC_PIPELINE/results/`, suffixed `_off_feast` and `_def_feast`:

- `P0_partition_{arm}.parquet` — per (player, season) → region, cell_id (+ `Profile-Sparse` flag).
- `P0_collapse_map_{arm}.json` — merge log + final K.
- `P0_position_overlap_{arm}.parquet` — region × position(v1.0 bucket) confusion (the proxy-vs-causal-axis diagnostic).
- `moment_trajectories_{arm}.parquet`, `trajectory_classification_{arm}.parquet`, `step3_validation_{arm}.parquet`, `step4_decomposition_{arm}.parquet`, `step5_transfer_{arm}.parquet` — as v1.0 §12.
- `F1_F4_summary_{arm}.json` — per observable + bootstrap CI + fires flag.
- `comparative_per_cell_{arm}.parquet` + `comparative_headline_{arm}.json` — vs v6.1.
- `comparative_vs_position_{arm}.json` — Δ F2 / Δ F4 κ / Δ dip-pass vs the locked position arms (§9.2).
- `mechanism_inference_{arm}.md` — incl. P1/P2/P3 verdicts with calibration.
- `substrate_ledger_spatial.md`, `RESULTS_SPATIAL.md` — umbrella, every number cites its artifact row.

## 13. Sign-off

- **Filed by:** Claude Code (claude-opus-4-8[1m]).
- **Sign-off requested from:** mr.nathanhumphrey@gmail.com.
- **Repo:** https://github.com/mrnathanhumphrey-droid/NBAProjections.
- **Lock event:** rename this file to `PRE_REG_NBA_RMD_SRC_SPATIAL_LOCKED.md`; git add; git commit; append the commit-SHA to `RMD_SRC_PIPELINE/SHA_LOCK.txt` under `## spatial re-axis`. No outcome-moment-flow compute fires until that SHA exists. First post-lock step: build `P0_partition_{off_feast,def_feast}.parquet` + the position-overlap diagnostic, then proceed to Step 1.

---

**End of draft v0.1.**
