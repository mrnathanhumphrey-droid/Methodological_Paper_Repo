# v2.0 GEO_F4 Re-slice — Verdict Memo

**Status**: 6-arm package fired against PRE_REG v2.0 (`prereg/PRE_REG_v2.0_GEO_F4_reslice.md`, locked at commit `2d7f321`). This memo records the results and the verdict in §4.6 form.

**Run record**: `results/v2_geo_f4_reslice/v2_results.json` (script: `src/rmd_src/v2_geo_f4_reslice.py`).

**Bottom line**: the original GEO_F4 fire stands and the substantive reading sharpens — **the rank-3 latent structure is stationary across 2012–2021; raw-corridor "regimes" are noise around that stationary structure.** Both the "classifier-overfit-on-transferable-continuous-substrate" reading and the "dynamics genuinely don't decompose" reading are ruled out by the package; the verdict is a stronger third reading not enumerated in the pre-reg matrix.

---

## Results table

### Division (n=72 corridors, top-15 for ARM C)

| Arm | Quantity | Bar | Observed | Verdict |
|---|---|---|---|---|
| A | r_μ̇ (train ↔ holdout) | ≥0.40 @ p<0.025 | **−0.197** (p=0.097) | FAIL |
| A | r_σ̇² | ≥0.40 @ p<0.025 | **−0.102** (p=0.395) | FAIL |
| B | latent factors 3/3 in same-or-adjacent 3×3 cell | 3/3 | **3/3** | PASS (caveat: trivial — see below) |
| C | top-15 κ | ≥0.40 | **−0.034** | FAIL |
| E | bootstrap κ_observed | — | **+0.075** | — |
| E | bootstrap 95% CI for κ | — | **[−0.066, +0.211]** | excludes 0.40 |
| E | P(bootstrap κ ≥ 0.40) | — | **0.000** | original fire is sampling-stable |
| F | κ at thresholds × 0.5 / × 1.0 / × 2.0 | — | **−0.064 / +0.075 / +0.014** | FAIL at any threshold |
| D-A pre-COVID | r_μ̇ / r_σ̇² | ≥0.40 | **−0.211 / −0.076** | FAIL |
| D-B pre-COVID | latent 3/3 | 3/3 | **3/3** | PASS (caveat: ARM B test has near-zero power on n=2 holdout) |
| D-C pre-COVID | top-15 κ | ≥0.40 | **+0.211** | FAIL (closer to bar than full but still well below) |

### State (n=513 corridors, top-100 for ARM C)

| Arm | Quantity | Bar | Observed | Verdict |
|---|---|---|---|---|
| A | r_μ̇ | ≥0.40 @ p<0.025 | **−0.013** (p=0.77) | FAIL |
| A | r_σ̇² | ≥0.40 @ p<0.025 | **−0.001** (p=0.98) | FAIL |
| C | top-100 κ | ≥0.40 | **+0.040** | FAIL |
| E | bootstrap κ_obs | — | **−0.002** | — |
| E | bootstrap 95% CI | — | **[−0.052, +0.045]** | excludes 0.40 |
| E | P(bootstrap κ ≥ 0.40) | — | **0.000** | original fire is sampling-stable |
| F | κ at × 0.5 / × 1.0 / × 2.0 | — | **−0.021 / −0.002 / −0.009** | FAIL at any threshold |
| D-A pre-COVID | r_μ̇ / r_σ̇² | ≥0.40 | **−0.030 / −0.072** | FAIL |
| D-C pre-COVID | top-100 κ | ≥0.40 | **+0.054** | FAIL |

ARM B does not exist at state resolution (no division-level PARAFAC for state).

---

## ARM B honest read (load-bearing caveat)

ARM B passes 3/3 at both full and pre-COVID holdout — **but the slopes are tiny and within ±1.5 SE of zero**. Per-factor full-holdout numbers:

| Factor | train (μ̇, σ̇²) | hold (μ̇, σ̇²) | train cell → hold cell |
|---|---|---|---|
| 0 | (−0.0012, −0.0110) | (−0.0044, +0.0082) | (0, −1) → (0, 0) — adjacent |
| 1 | (+0.0006, −0.0004) | (+0.0085, +0.0273) | (0, 0) → (+1, 0) — adjacent |
| 2 | (−0.0033, −0.0082) | (−0.0069, +0.0118) | (0, 0) → (−1, 0) — adjacent |

The cell-adjacency test passes because **every slope across both periods sits in the near-zero zone** (within ±1.5 × SE of 0). This is not "the latent factors' dynamics transfer"; it is "the latent factors have no measurable dynamic content in either period." The pre-reg acknowledged this design limit, and it landed exactly on it.

**Substantive read**: the rank-3 latent structure is *stationary* across 2012–2021. The PARAFAC static loadings replicated (Tucker 0.95 from Stage 4) AND the per-year strength of each latent factor is flat. There is no "dynamic structure in latent space to transfer" — there is also no "dynamic structure to fail to transfer." The latent layer is genuinely stationary.

This is **not the "classifier-overfit-on-stable-continuous-substrate" verdict** I would have written if ARM A had also passed. And it is **not the "dynamics genuinely don't decompose" verdict** of the original GEO_F4 reading either. It is a third, sharper reading.

---

## The verdict (§4.6, in close-to-final form)

The three transferring vs non-transferring objects in the substrate compose to one consistent picture:

1. **Gravity** (mass + distance) transfers (pseudo-R² 0.63 → 0.74) — confirmed in v1.0.
2. **PARAFAC rank-3 static loadings** transfer (Tucker congruence 0.95) — confirmed in v1.0.
3. **Per-year strength of each latent factor** is statistically indistinguishable from constant across the entire 2012–2021 window (ARM B: every (μ̇, σ̇²) slope is within ±1.5 × SE of 0 in both train and pre-COVID and full holdout).
4. **Raw-corridor regime labels** do not transfer at any classifier-threshold or threshold scaling (original v1.0 κ −0.06 / 0.02; ARM C top-N κ −0.03 / +0.04; ARM F threshold-scaled κ all <0.10; ARM E bootstrap CI excludes 0.40).
5. **Raw-corridor continuous slope coordinates** also do not transfer (ARM A r_μ̇ −0.20 / −0.01, r_σ̇² −0.10 / 0.00).
6. **COVID is not the confound** (ARM D-A r values identical sign and magnitude on pre-COVID-only holdout; D-C kappas slightly improve but stay well below 0.40).

**Substantive reading**: the substrate's transferable structure is the *gravity + rank-3 latent loadings* layer. The latent loadings are stationary across the decade. Raw-corridor "regime" classification is reading noise around that stationary structure; the (μ̇, σ̇²) slopes per corridor are sampling artifacts of finite-year fits to a process with no real dynamic component above the latent-3D level.

The original GEO_F4 fire was *firing on the right thing*: there is no decade-transferable regime structure at the raw-corridor level, because there is no real raw-corridor regime structure in the first place — at the relevant analytical granularity (rank-3 latent), the substrate is *stationary*. This is a strictly stronger reading than the pre-reg matrix entry I'd labeled "conservation-law reading reinforced"; the conservation-law metaphor turns out to be even cleaner — there is conservation BECAUSE the relevant structure is stationary.

---

## Methodology-paper §4.5 / §4.6 ledger

- **§4.5**: GEO_F4 fires on raw corridors. Unchanged from v1.0. Headline of the geographic arm's dynamic layer.
- **§4.6** (new, v2.0): The six-arm re-slice. The classifier-overfit hypothesis and the COVID-confound hypothesis are both ruled out. The substrate is stationary at the rank-3 latent level (ARM B 3/3 trivial-pass, fully reported as the stationarity verdict). Raw-corridor slope coordinates also do not transfer (ARM A FAIL at both resolutions, both windows). The original GEO_F4 result is *substrate-correct*: it fires because the underlying structure does not have transferable dynamic content above the static-latent layer.
- **Abstract**: §4.5 result reported as drafted ("dynamic regime classification fails: GEO_F4 fires, κ ≈ 0 vs 0.40 bar at both resolutions"). §4.6 verdict reported as: "v2.0 re-slice rules out the classifier-overfit and COVID-confound diagnoses; rank-3 latent layer is stationary across 2012–2021; raw-corridor regimes are noise around a stationary substrate."

The discipline guards held:
- Original §4.5 stands.
- Language is "re-slice locates where structure DOES and DOESN'T transfer", never "re-slice rescues GEO_F4."
- No thresholds tuned (ARM F was diagnostic only and confirmed threshold-insensitivity).
- All six arms reported, including ARM B's caveated trivial-pass.

---

## What v2.0 does NOT do (preserved limits)

- It does not transform the substrate's interpretation of the *static* structure. Stage 4's rank-3 latent corridors remain (Pacific-→Southeast, Northeast-→Southeast retiree, contrast) with the same substantive reading.
- It does not bear on the v1.7 opportunity-moment pull taxonomy result (r=0.999 held-out signature) — that arm is static-and-positive and the v2.0 verdict adds nothing to it.
- It does not change the desperation-seam reading (push-side invisibility in ACS, two-mirrors synthesis with SDP). v2.0 is internal to the pull-side dynamic layer.

---

## Provenance

Pre-reg locked: `prereg/PRE_REG_v2.0_GEO_F4_reslice.md` at commit `2d7f321`, 2026-05-31.
Script: `src/rmd_src/v2_geo_f4_reslice.py`.
Results JSON: `results/v2_geo_f4_reslice/v2_results.json`.
PARAFAC re-fit: rank=3, `tensorly.parafac` with `random_state=0`, training-window (2012–2017) residual cube at division resolution. Static factor loadings extracted; year-mode trajectories built by weighting raw-corridor μ, σ² at each year by (A_ik · B_jk).
