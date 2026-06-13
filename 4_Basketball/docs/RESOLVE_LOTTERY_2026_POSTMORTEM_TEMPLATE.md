# RESOLVE LOTTERY 2026 — POST-DRAFT RETROSPECTIVE

**Draft date**: {{draft_date}}
**Scored**: {{scoring_date}}
**Pre-reg lock date**: 2026-06-07
**Days between pre-reg and draft**: {{days_locked}}

---

## TL;DR

{{tldr_summary}}

---

## Headline rank deltas

Resolve Pick → Actual Pick (Δ = actual − resolve). Negative Δ = went earlier than we said; positive Δ = went later.

| Resolve | Actual | Δ | Player | Result |
|---:|---:|---:|---|---|
{{rank_delta_table}}

### Aggregate accuracy

- Mean absolute rank delta (lottery picks 1-14): **{{mean_abs_delta_lottery}}**
- Median absolute rank delta: **{{median_abs_delta}}**
- Lottery-pick exact-match count: **{{exact_match_count}} / 14**
- Within-2 picks count: **{{within_2_count}} / 14**
- Within-5 picks count: **{{within_5_count}} / 14**

---

## Bold contrarian calls — receipts

These were locked 2026-06-07 with the **OUR HIGH/CONSENSUS LOW** and **OUR LOW/CONSENSUS HIGH** discipline. Each gets a hit/miss now.

### Our HIGH, Consensus LOW (we said higher than the public)

| Call | Resolve said | Public said | Actual | Verdict |
|---|---|---|---|---|
| Aday Mara | #7 | late-1st / undrafted | {{mara_actual}} | {{mara_verdict}} |
| Caleb Wilson | #6 | mid-1st (15-25) | {{wilson_actual}} | {{wilson_verdict}} |
| Hannes Steinbach | #10 | 2nd round | {{steinbach_actual}} | {{steinbach_verdict}} |
| Ebuka Okorie | #9 | late-2nd / undrafted | {{okorie_actual}} | {{okorie_verdict}} |
| Amari Allen | #5 | mid-1st | {{allen_actual}} | {{allen_verdict}} |

### Our LOW, Consensus HIGH (we said lower than the public)

| Call | Resolve said | Public said | Actual | Verdict |
|---|---|---|---|---|
| Koa Peat | Outside top-14 (v3 #49) | Top-5 | {{peat_actual}} | {{peat_verdict}} |
| Baba Miller | #25 (v3 #53) | Top-15 | {{miller_actual}} | {{miller_verdict}} |
| Karim Lopez | Outside lottery | Mid-1st | {{lopez_actual}} | {{lopez_verdict}} |

### The Top-3 Lock

Locked claim: **at least one of Boozer / Jefferson / Dybantsa goes #1.**

- #1 actual: {{pick1_player}}
- Top-3 actual: {{actual_top3}}
- Verdict: {{top3_lock_verdict}}

### Bold-call hit rate

- OUR HIGH, CONSENSUS LOW calls: {{high_call_hits}} / 5
- OUR LOW, CONSENSUS HIGH calls: {{low_call_hits}} / 3
- Top-3 lock: {{top3_lock_status}}
- **Overall bold-call accuracy: {{overall_bold_pct}}**

---

## Method-comparison breakdown

For each lottery prospect, the Resolve Score blended four signals at locked weights. How did each ingredient do on its own vs the composite?

| Method | Mean |Δ| (lottery) | Best call | Worst call |
|---|---:|---|---|
| **Resolve composite** (synthesizer) | {{resolve_mean_abs}} | {{resolve_best}} | {{resolve_worst}} |
| **v3 outcome-calibrated GBM** | {{v3_mean_abs}} | {{v3_best}} | {{v3_worst}} |
| **Hand-composite production** | {{hand_mean_abs}} | {{hand_best}} | {{hand_worst}} |
| **Advanced-signal NCAA PBP** | {{advanced_mean_abs}} | {{advanced_best}} | {{advanced_worst}} |

Methodology takeaway: {{method_takeaway}}

---

## Honest losses

The picks we got most wrong and the lesson:

{{honest_losses_section}}

---

## Substrate-gap admissions revisited

Pre-reg flagged these gaps. How did they actually play out?

- **Intl prospects** (Kayil #12 LOW CONF, Lopez survivorship-penalized, De Larrea / Suigo dropped): {{intl_eval}}
- **NCAA advanced metrics unconditioned on outcome**: {{advanced_unconditioned_eval}}
- **Defensive metrics weaker for non-Centers**: {{def_metrics_eval}}

---

## What we'd lock for 2027

{{lock_for_2027}}

---

## Receipts & methodology trail

- Pre-reg locked: `D:/NBA Projections/docs/RESOLVE_LOTTERY_2026_06_07.md`
- Resolve composite parquet: `data/parquet/resolve_lottery_2026.parquet`
- v3 GBM parquet: `data/parquet/draft_2026_outcome_calibrated_v3.parquet`
- Hand-composite parquet: `data/parquet/draft_2026_projections.parquet`
- Advanced-metric parquet: `data/parquet/prospect_advanced_metrics_2026.parquet`
- This post-mortem script: `scripts/lottery_2026_postmortem.py`
- Actual draft results input: `data/draft_2026_actual_results.csv`

---

## Cardinal rule held

Zero third-party rankings consumed as input pre-draft. The receipts are honest — pre-reg was sealed before any public mock-draft consensus update, no rank revisions, no whispers.
