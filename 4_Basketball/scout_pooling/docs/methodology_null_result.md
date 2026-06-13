# Scout-Specialist Test — Null Result (PRE_REG_SCOUTS_v1)

**Status**: H_specialist REJECTED. Two of four pre-registered falsification triggers fired (F2, F4). Test reported per pre-reg §6 equal-prominence reporting commitment.

**Pre-registration**: [`D:/Draft Resolve/docs/PRE_REG_SCOUTS_v1.md`](../../../Draft%20Resolve/docs/PRE_REG_SCOUTS_v1.md) — locked 2026-05-18 prior to fit.

**Verdict artifact**: [`audit_runs/v1/fit_v1_verdicts.json`](../audit_runs/v1/fit_v1_verdicts.json).

---

## 1. What was pre-committed (verbatim from PRE_REG_SCOUTS_v1.md §5)

**H_specialist**: Scouts (named-author boards) are heterogeneous specialists — different scouts carry independent signal in different (prospect-archetype × prospect-league) cells, beyond what aggregate consensus and statistical models capture.

Decision rule: H_specialist is sustained ONLY if all four triggers below fail to reject. Any single trigger firing means the null result is reported and the specialist framing is walked back.

- **F1 — Flat-cell**: reject if posterior median of τ_interaction < 0.05 AND < 5% of (scout × archetype × league) cells have |γ_{S,C}| above the 95th percentile of a permutation null.
- **F2 — Disagreement-uniformity**: reject if scout-rank-disagreement-variance on archetype-specific prospects is NOT statistically higher than on archetype-general prospects (permutation p < 0.05 required to KEEP H_specialist).
- **F3 — Out-of-sample consensus dominance**: reject if consensus rank beats every named specialist on > 70% of archetype cells on the held-out cohort.
- **F4 — Aggregator-baseline**: reject if Tankathon aggregator |γ| is statistically indistinguishable from named-specialist |γ|.

---

## 2. What was actually fit

| Quantity | Value |
|---|---|
| N (scout, cell) observations | 31 |
| n scouts | 6 |
| n cells | 6 |
| Min-cell-n threshold | 5 (deviation — see §4) |
| Weighting | inverse-variance (1 / Fisher_SE²) |
| Estimation | WLS + 1000-bootstrap CIs (frequentist substitute for the pre-reg Bayesian hierarchical fit — see §4) |

### Variance-component point estimates with 95% bootstrap CIs

| Parameter | Point | 95% CI |
|---|---|---|
| τ_scout | 0.263 | [0.169, 0.454] |
| τ_cell | 0.207 | [0.137, 0.453] |
| τ_interaction | 0.302 | [0.163, 0.331] |

τ_interaction is the load-bearing parameter for the specialist hypothesis. The point estimate is well above the F1 threshold of 0.05.

---

## 3. Falsification trigger outcomes

### F1 — Flat-cell — DID NOT FIRE

- (a) τ_interaction point 0.302 ≥ 0.05 threshold → condition (a) false
- (b) 2 of 31 cells (6.5%) had |γ| above the permutation-null 95th percentile (0.717), threshold was < 5% → condition (b) false

Both conditions required to fire; neither did. F1 sustained H_specialist.

### F2 — Disagreement-uniformity variance — FIRED

| Bucket | Variance | n |
|---|---|---|
| Archetype-specific (international, late_bloomer, big_skill, combine) | 24.39 | 109 |
| Archetype-general (one_and_done) | 23.47 | 46 |

Observed difference 0.92 in favor of specific. Permutation p = 0.49 (5,000 shuffles). No detectable disagreement-variance gap. F2 fired → reject H_specialist.

### F3 — Consensus dominance — DID NOT FIRE

Per-named-scout fraction of shared cells where the consensus rank beats them on |edge|:

| Scout | Consensus wins | n cells compared |
|---|---|---|
| givony_espn | 50% | 4 |
| hollinger_athletic | 25% | 4 |
| oconnor_ringer | 60% | 5 |
| vecenie_athletic | 80% | 5 |

Threshold for F3 firing was > 70% across ALL named scouts. Consensus dominates Vecenie only; F3 did not fire.

### F4 — Aggregator-baseline — FIRED

|γ| comparison between Tankathon aggregator and named specialists (mean of absolute γ residuals):

| Group | Mean |γ| |
|---|---|
| Tankathon aggregator | 0.239 |
| Named specialists (Vecenie, O'Connor, Hollinger, Givony) | 0.353 |
| Δ named − tank | 0.114 |
| 95% bootstrap CI on Δ | **[−0.075, 0.293]** (5,000 bootstraps) |
| P(named > tank) | 0.878 |

The 95% CI crosses zero. Named-specialist |γ| is NOT statistically distinguishable from the Tankathon aggregator's. F4 fired → reject H_specialist.

### Overall verdict (per pre-reg §5 decision rule)

**H_specialist REJECTED.** F2 and F4 each independently sufficient to reject.

---

## 4. Deviations from pre-registration

Per pre-reg §7, deviations are logged here in the same artifact as the verdict.

1. **Train/test cohort substitution (pre-reg §4.3)**. Pre-reg specified fit on train cohort 2010–2017. Reachable corpus had ZERO multi-scout coverage on 2010–2017 drafts. Per pre-reg §7's data-unavailable contingency, the fit was moved to the test cohort 2018–2021 (effectively 2021-only after multi-scout filtering). The original 2010–2017 train cohort is treated as never-run; PRE_REG_SCOUTS_v2 would be required to fit on a re-scraped 2010–2017 corpus.
2. **Cell-size threshold (pre-reg §4.2)**. Pre-reg specified n ≥ 15 prospects per cell. Only 2 cells survived at n ≥ 15 in the reachable corpus. Fit used n ≥ 5; reported variance components carry the corresponding posterior uncertainty (bootstrap CIs in §2).
3. **F2 scope expansion**. F2 was expanded to 2018–2025 multi-scout prospects (any scout type, not only named) to push n past the 2021-only-named bottleneck. F2's permutation null was computed on the same expanded pool. F1, F3, F4 ran on the named-scout-only edge table.
4. **Estimation substitution**. Pre-reg §4.2 specified a Bayesian hierarchical fit. Implementation used WLS + nonparametric bootstrap as the frequentist analog because Bayesian fit on N=31 with this hierarchy is dominated by prior; the WLS+bootstrap reports the same variance decomposition with bootstrap CIs. The Stan model file is present (`hierarchical.stan`) but was not the binding estimator for this verdict. Re-running the Bayesian fit would tighten posterior reporting on τ_interaction but would not move which triggers fire at the current sample size.

---

## 5. Interpretation

F4 is the load-bearing finding. At the cell-resolution our reachable corpus supports, named scouts do not produce edge magnitudes statistically distinguishable from a public-board aggregator (Tankathon). F2 reinforces: archetype-specific prospects do not generate more scout-disagreement than archetype-general one-and-done prospects.

F1 did NOT fire — τ_interaction has real magnitude (0.30, CI [0.16, 0.33]). The interaction variance is not flat; it just is not structured into named-specialist edges that beat the aggregator at the cells the test could resolve.

**Sample-size caveat**. The verdict rests on 31 (scout, cell) observations across 6 cells in effectively one draft year (2021). Power to detect specialist signal at this resolution is low. The null is consistent with the data; the test is not powerful enough to be a strong claim that no specialist signal exists at any resolution. The pre-reg's intended fit (2010–2017 multi-scout, n ≥ 15) would have higher power but is not reachable without additional scraping, and re-running with new data after seeing this result requires PRE_REG_SCOUTS_v2 per pre-reg §8.

---

## 6. What this does and does not claim

This test **does** claim:
- At the (archetype × league) cell resolution achievable with the 2018–2021 multi-scout reachable corpus, named-author scout boards do not produce specialist edge over consensus that is statistically distinguishable from a Tankathon aggregator baseline.
- Archetype-specific prospects do not show higher inter-scout-rank disagreement variance than archetype-general prospects on the 2018–2025 expanded pool.

This test does **not** claim:
- Scout boards have zero value (they correlate with outcomes; the test is about cell-specific *specialist* edge over consensus, not about overall scout signal).
- The result would replicate at the pre-registered (n ≥ 15, 2010–2017 train cohort) resolution if that data were obtained.
- The result generalizes beyond the named scouts in pre-reg §2.3.

---

## 7. What follows from this for the Draft Resolve methodology paper

- Cite this file as the falsification outcome.
- Carry the deviations in §4 forward into the methodology paper unmodified.
- Do not promote per-(scout, cell) findings from this fit; they have not cleared the pre-committed F1–F4 gate.
- If a future revision wants to test specialist signal again, that requires PRE_REG_SCOUTS_v2 with fresh data and a fresh train/test split (pre-reg §8).
