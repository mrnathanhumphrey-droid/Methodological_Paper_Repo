# Pre-registration — 2026-27 forward Probe

**Date written:** 2026-05-05 (committed before the 2026-27 NBA preseason exists)
**Status when written:** 2026-27 NBA regular season has not yet started (typical season opener: late October 2026, ~5 months from now). 2026-27 box scores, preseason projections, and any associated residuals do not yet exist. This document is dated and archived before any 2026-27 data is observable.

## Why this exists

This pre-registration extends the multi-season-pre-registration discipline applied across 23-24, 24-25, and 25-26 (multi-season pre-registration document at [audit_runs/probe_b_prime_coarse/PRE_REGISTRATION_multi_season.md](file:///D:/NBA%20Projections/audit_runs/probe_b_prime_coarse/PRE_REGISTRATION_multi_season.md)). That earlier document committed a Tier-1 hypothesis (`top_record + early_season + home` theme) before the 23-24 / 24-25 multi-season residuals existed. The multi-season Probe yielded NULL on that Tier-1 hypothesis (Section 5.3 of the paper draft).

In separate exploratory analysis on the 23-25 pooled residuals at a coarser 24-config space, two cohorts independently flagged a different theme (`high_defense_opponent + bottom_record + away`) at nominal but not Bonferroni-corrected significance. This observation is reported in Section 5.5.1 of the paper draft as exploratory.

A natural temptation is to elevate this exploratory theme to Tier-1 status for 26-27. **We explicitly do not.** Promoting an observed theme to Tier-1 status for the next pre-registration cycle would convert post-hoc theme discovery into a privileged future test, which is exactly the discipline failure that pre-registration is designed to prevent. The discipline survives only if the only themes receiving single-test α = 0.05 treatment are themes committed before any informative data exists.

This document fixes the 26-27 protocol with that discipline.

## The pre-registered hypothesis (single Tier-1, carried forward unchanged)

**Hypothesis Tier-1:** When the 2026-27 forward residuals exist and are processed through the same Probe pipeline (per-game residuals from a v6.1-LOCKED-architecture 26-27 forward ship, tagged with the 72-config space `opp_class × record_tier × season_phase × home_away`, clustered at k* via average linkage on combined moment + characteristic-function distance), the outlier cluster will be dominated by configurations sharing the joint theme:

```
top_record_tier (current-season win pct >= 0.55 as of game date)
   + early_season (game_date < 26-27 All-Star OR team_game_n <= 30)
   + home_away = home
```

This is the *same* theme committed in the multi-season pre-registration (May 2026). It failed across 23-25. The 26-27 retest provides additional null evidence on the same hypothesis if it fails again, or genuine confirmation of residue-class structure on novel data if it succeeds.

**Decision rule:**
- **Tier-1 CONFIRMED**: outlier cluster at k* contains ≥ 2 configurations sharing the theme AND p < 0.05 single-test (no Bonferroni since pre-registered) AND k* ∈ [4, 16] gate met.
- **Tier-1 FAILED**: any of the above conditions not met. Reported as additional null evidence on the original hypothesis, accumulating across two pre-registration cycles.

## The exploratory `high_bottom_away` theme

Section 5.5.1 reports that two cohorts (soph Guard / PTS at p = 0.037 and vet Forward / AST at p = 0.083) independently flagged outlier configurations sharing a `high_defense_opponent + bottom_record + away` theme in the 23-25-pooled 24-config Probe.

**This theme is NOT pre-registered as Tier-1 for 26-27.** It is treated like any other unanticipated theme that might appear in the 26-27 exploratory analysis: subject to Bonferroni correction at the cell-count of the 26-27 probe, with no privileged single-test α treatment.

**Decision rule for `high_bottom_away` (and any other non-pre-registered theme) in 26-27:**

- **EXPLORATORY-CONFIRMED**: a theme (including `high_bottom_away`) survives Bonferroni-corrected α at the 26-27 probe's cell-count AND appears in at least one cohort's outlier cluster at k* AND k* ∈ [4, 16].
- **NOT CONFIRMED**: the theme does not survive Bonferroni correction.

If `high_bottom_away` survives Bonferroni in 26-27, the publishable framing is "exploratory observation in 23-25 replicates on novel 26-27 data under Bonferroni-corrected exploratory testing." The bar is appropriately higher than Tier-1's bar precisely because the theme was not pre-registered.

If `high_bottom_away` does not survive Bonferroni in 26-27, the publishable framing is "the 23-25 exploratory observation does not replicate on novel data; over-fitting to the 23-25 window is the most likely explanation."

## Outcomes locked here

When the 26-27 residuals are available and processed:

### Outcome 1 — Tier-1 confirms
`top_record + early + home` survives single-test α = 0.05 AND k* ∈ [4, 16] in at least one cohort × stat cell.
- **Paper response:** the original Tier-1 hypothesis revives. Genuine residue-class structure of the originally-predicted form has been detected on truly out-of-sample data after a multi-season failure. Strong evidence for the framework's predictions.
- **Methodology section response:** report the cycle as "the prediction was made before the 23-25 data existed; failed across 23-25; was carried forward unchanged into the 26-27 pre-registration; confirmed on novel 26-27 data." This is the strongest pre-registration outcome available.

### Outcome 2 — Tier-2 confirms (Bonferroni-survived exploratory hit)
Some theme (whether or not it includes `high_bottom_away`) survives Bonferroni-corrected α in the 26-27 probe.
- **Paper response:** publishable exploratory replication. The theme that survives is reported as the genuine finding, with explicit notation of whether it was previously observed in 23-25 exploratory analysis or is a new emergence.
- **Methodology section response:** the strict-significance pipeline is functioning as designed. Tier-2 hits at Bonferroni-corrected α are credible findings that survived appropriate correction; Tier-1 hits are stronger because they were committed in advance.

### Outcome 3 — Both null
Tier-1 fails AND no Tier-2 theme survives Bonferroni.
- **Paper response:** the multi-season-pooled-plus-26-27-forward null is the most decisive available negative on the contextual residue-class hypothesis. After four seasons of testing including one pre-registered hypothesis and an exploratory follow-up cycle, structure of the predicted form is not detectable in NBA box-score-only contextual axes.
- **Methodology section response:** the framework's predicted asymmetric structure (Section 5.2) is supported; the framework's predicted contextual structure (Section 5.3 and §5.5) is not. Two distinct claims; one supported, one not. Reported with equal prominence.

### Outcome 4 — Tier-1 confirms AND Tier-2 confirms
The strongest available outcome.
- **Paper response:** combined evidence for both pre-registered structure and Bonferroni-survived exploratory structure. The framework's predictions track multiple residue-class axes.

## What this document does NOT do

- It does not pre-register the `high_bottom_away` theme. That theme remains exploratory in this paper; it gets no privileged future test.
- It does not pre-register additional themes from any other exploratory analysis on the 23-25 data window. The discipline is that pre-registered themes are committed before informative data; we have already used the 23-25 window for theme discovery, so additional themes cannot be promoted from that window without violating the discipline.
- It does not commit specific cohort sample sizes for 26-27 (those depend on the 26-27 cohort widening pipeline output, which has not yet been run). The 26-27 ship cohort is expected to be of comparable size to the 25-26 ship's 567 players.

## Test pipeline (to be run when 26-27 residuals exist)

1. Generate 26-27 forward ship using the same v6.1 LOCKED architecture (Stan posterior + cohort widening hybrid v3 + LOCKED offsets), as in 25-26.
2. Score against 26-27 actuals; produce per-player and per-game residuals.
3. Tag per-game residuals with the 72-config space using prior-season (25-26) defensive rating quartile for opp_class, rolling current-season win pct for record_tier, calendar phase for season_phase, `is_home` for home_away.
4. For each cohort × stat cell (9 cohorts × 3 stats = 27, with insufficient-sample cells dropped), run hierarchical agglomerative clustering with average linkage on combined moment + CF distance.
5. Compute bootstrap null at 500 reps per cell.
6. Report against the decision rules above.

## Signature

Pre-registered before 26-27 residuals exist. Located alongside the multi-season pre-registration at [audit_runs/probe_b_2627_pre_registration/](file:///D:/NBA%20Projections/audit_runs/probe_b_2627_pre_registration/).

- Local time of writing: 2026-05-05, evening
- Multi-season pre-registration that this extends: [audit_runs/probe_b_prime_coarse/PRE_REGISTRATION_multi_season.md](file:///D:/NBA%20Projections/audit_runs/probe_b_prime_coarse/PRE_REGISTRATION_multi_season.md)
- Section 5 of paper draft that incorporates this pre-registration: [paper_draft/section_5_empirical_validation.md](file:///D:/NBA%20Projections/paper_draft/section_5_empirical_validation.md)
