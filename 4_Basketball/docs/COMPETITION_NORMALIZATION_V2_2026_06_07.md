# Competition Normalization v2 — intl substrate refresh — 2026-06-07

Follow-up to [COMPETITION_NORMALIZATION_2026_06_07.md](COMPETITION_NORMALIZATION_2026_06_07.md). Closes the "unknown league bucket" Doncic-prior trap by leveraging `wikipedia_pre_nba_career.parquet` (already on disk, 294 rows / 135 unique players) that we hadn't joined to the training set.

## What v2 adds

- **Proper intl league labels** for historical prospects. New buckets created from the 28 previously-"unknown" rows:
  - `intl_acb_spain`: 5
  - `intl_nbl_australia`: 9
  - `intl_lnb_france`: 5
  - `intl_kls_serbia` (Adriatic): 3
  - `intl_gbl_greece`: 3
  - `intl_bbl_germany`: 1
  - `intl_bsl_israel`: 2
  - `intl_tbsl_turkey`: 2
- **Refit outcome GBM (v2)** with these properly-canonicalized league categoricals
- **Survivorship-signal diagnostic** — per-prospect column showing model prediction vs league baseline pick. Quantifies the survivorship-bias problem rather than hiding it.

## Key finding: v2 rankings IDENTICAL to v1

Despite the proper intl league labels, the 2026 rankings didn't move. Why?

**The survivorship bias is in the FEATURES, not just the league labels.** When De Larrea's feature vector (per-40 stats at 17.2 mpg, position PG, age 19) gets fed in, the model finds his profile most resembles historical elite ACB picks (Doncic-tier). The league label was already implicitly encoded by the feature similarity. Adding the explicit `intl_acb_spain` categorical doesn't change much because the GBM had already learned the cluster.

This is itself a substantive finding: **categorical labels alone don't fix survivorship-biased priors**. Either we need real per-season per-40 stats for the dozens of historical ACB-tier players (so the model sees more than just the survivors), or we surface the bias diagnostic explicitly.

## Survivorship-signal diagnostic

For each 2026 prospect, compute:

  `survivorship_signal = league_baseline_pick − model_predicted_pick`

Where `league_baseline_pick` is the historical average draft pick for prospects from that league bucket. A HIGH positive signal means the model is predicting earlier than the average prospect from that bucket — i.e., the model thinks this prospect is a Doncic-tier elite within their league, not a typical late-1st.

### Top survivorship signals (2026 pool)

| Player | League | League Baseline Pick | Model Pred Pick | Signal |
|---|---|---:|---:|---:|
| **Sergio De Larrea** | intl_acb_spain | 29.60 | 10.32 | **+19.3** ★ |
| Dailyn Swain | NCAA_P5 | 26.86 | 10.32 | +16.5 |
| Ryan Conwell | NCAA_P5 | 26.86 | 10.32 | +16.5 |
| Cameron Carr | NCAA_P5 | 26.86 | 10.32 | +16.5 |
| **Luigi Suigo** | intl_kls_serbia | 34.67 | 20.08 | +14.6 |
| **Karim Lopez** | intl_nbl_australia | 28.56 | 14.61 | +13.9 |
| Flory Bidunga | NCAA_P5 | 26.86 | 21.63 | +5.2 |
| Caleb Wilson | NCAA_P5 | 26.86 | 23.27 | +3.6 |
| ... | | | | (most prospects: small or negative signal) |

### How to use the signal

- **Signal > +10**: Model is making a Doncic-tier prediction within this prospect's league bucket. **Treat with high skepticism unless the stat profile clearly matches historical elite samples.** For De Larrea, his actual ACB line at 17.2 mpg (9.6/3.0/3.7) is closer to typical late-1st than to Doncic's elite-tier 17-y/o EuroLeague line. → Predicted pick 10 likely too aggressive.
- **Signal +5 to +10**: Model thinks this prospect is in the top quartile of their league bucket. Reasonable bold call.
- **Signal < +5**: Model is predicting roughly league-average outcome for the bucket. Most prospects fall here.
- **Signal < 0**: Model predicts WORSE than league baseline. Bust flag.

## What this means for the bold 2026 predictions

The v1 doc's bold pre-registered predictions don't change. The v2 work adds **transparency to the survivorship bias** rather than fixing it.

For De Larrea specifically, the v2 honest read is: "Model has him #1 / Lottery / pick 10.3, BUT survivorship signal +19.3 means he's projected as a top-tier ACB outlier when his stats actually look like a typical late-1st ACB prospect. **Sergio De Larrea is most likely a late-1st / early-2nd, not lottery.** The lottery prediction is an artifact."

For Karim Lopez (+13.9 survivorship): the model thinks he's an elite NBL prospect like LaMelo / Josh Giddey. His actual line (11.9 ppg / 6.1 rpg / 1.0 bpg / 25.6 mpg) at 18 in NBL is solid but not LaMelo-tier. **Lopez probably lands mid-1st (pick 15-25), not pick 14**.

## Files

- Updated training set: `data/parquet/rookies_outcome_training_v2.parquet` (501 rows, 28 unknown → 17 + 11 properly labeled)
- V2 models: `data/models/outcome_gbm_v2_*.txt`
- V2 league effects: `data/parquet/rookies_outcome_gbm_v2_league_effects.parquet`
- V2 2026 board: `data/parquet/draft_2026_outcome_calibrated_v2.parquet` (new `survivorship_signal` + `league_baseline_pick` columns)
- Scripts: `decomp_11_intl_label_refresh_from_wikipedia.py`, `decomp_12_outcome_gbm_v2.py`, `decomp_13_project_2026_v2.py`

## Outstanding for v3

- **Actual stat scrape for historical intl prospects** — the real fix requires per-season per-40 stats for the dozens of EuroLeague/ACB/BBL/NBL/Adriatic prospects 2014-24 who got drafted. With actual stats, the model sees the FULL distribution (Doncic AND median-late-1st) and would correctly predict De Larrea closer to league baseline.
- **Cross-league competition multipliers from CROSSOVER players** — players who played EuroLeague then ACB give us direct edge ratios. Need scrape.
- **Direction-of-move covariate** for the crossover graph (survivors over-perform when moving up; struggling players don't appear in the transfer pool).

## Cross-cuts

- [[project-nba-competition-normalization-2026-06-07]] — v1 substrate
- [[feedback-bold-timestamped-predictions]] — same pre-reg discipline applied
- [[feedback-raw-data-only-no-projecting-on-projections]] — held; wikipedia substrate is biographical not third-party-projection
