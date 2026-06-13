# 41 — Probe 14: Monte Carlo cleaning-ROI — revises Probe 13

**Status:** Stochastic generalization of Probe 13's deterministic cleaning-ROI sketch. Includes empirical DKA rain DOY probabilities, seasonal deposition, saturating soiling model, and natural-rain partial cleaning calibrated against DKA's observed 3.87 %/yr at ~3.5 operational/yr. **Result substantially revises Probe 13.**
**Date:** 2026-06-01
**Substrate:** D:/Renewables/Solar/

---

## 1. Why this probe

Probe 13 / memo 40 reported optimal scheduled cleaning interval ≈ 156 days (~$47/kW/yr) for DKA-class arid commercial PV. Honest caveat in §5: that model ignored natural-rain cleaning. This probe relaxes that caveat with a stochastic year-long simulation.

Pre-decision before running:
- **If MC confirms Probe 13:** deterministic shortcut was OK
- **If MC revises Probe 13:** report which assumptions did the work and how they should propagate

Outcome: MC substantially revises. Below.

---

## 2. Model

### Calibration
- Match DKA observed 3.87 %/yr net annual loss when running scheduled T=104 days (~3.5 cleanings/yr, matching observed regime)
- One free parameter: f_rain = fractional soiling reduction per rain event ≥1 mm
- **Calibrated f_rain = 0.233** — each rain event removes 23.3% of current soiling burden

### Process
- Daily timestep, 365 days/year
- Seasonal deposition: wet (Oct-Mar) 0.173 %/day, dry (Apr-Sep) 0.128 %/day (Probe 5c)
- Saturating: ds/dt = r × (1 − s/s_sat), s_sat = 25% (cap on accumulable soiling)
- Rain at empirical DKA DOY probability (overall ~29 rain-days/yr, ~8%/day average)
- Each rain event: soiling × (1 − f_rain) = soiling × 0.767
- Operational cleaning per strategy: full restore to s=0
- Cost: $10/kW per cleaning, $0.10/kWh electricity, 5.5 kWh/kW/day yield

### Strategies evaluated
| Class | Variants |
|---|---|
| NONE | No operational cleaning at all |
| Scheduled | Clean every T days, T ∈ {60, 90, 120, 156, 180, 250, 365} |
| Pure-opportunistic | Clean K days after each rain, K ∈ {0, 1, 2, 3, 4, 5, 7} |
| Mixed (opp + min interval) | Lag=3d with min-interval ∈ {30, 60, 90} days |
| Threshold | Clean when soiling exceeds X%, X ∈ {3, 5, 8, 10, 15} |

N = 2000 simulated years per strategy.

---

## 3. Results

| Strategy | Loss % (mean) | N/yr | Cleaning $ | Soiling $ | **Total $/kW/yr** |
|---|---|---|---|---|---|
| **NONE** | 6.51 | 0.00 | $0 | $13.07 | **$13.07** ← **LOWEST** |
| threshold=10% | 5.12 | 0.98 | $9.83 | $10.28 | $20.11 |
| sched_T=365d | 6.46 | 1.00 | $10.00 | $12.97 | $22.97 |
| threshold=8% | 4.25 | 1.95 | $19.55 | $8.45 | $28.00 |
| sched_T=250d | 5.48 | 2.00 | $20.00 | $11.01 | $31.01 |
| sched_T=156d | 4.80 | 3.00 | $30.00 | $9.63 | $39.63 |
| opp_lag=3d_min=90d | 4.35 | 3.80 | $38.00 | $8.73 | $46.77 |
| sched_T=120d | 4.24 | 4.00 | $40.00 | $8.52 | $48.52 |
| threshold=5% | 2.76 | 5.56 | $55.55 | $5.55 | $61.17 |
| opp_lag=7d | 2.33 | 13.27 | $132.69 | $4.68 | $137.39 |
| **opp_lag=2d** (pure) | 2.22 | 22.45 | $224.46 | $4.45 | **$228.92** |
| opp_lag=0d | 2.22 | 29.36 | $293.61 | $4.46 | $298.02 |

---

## 4. Three substrate-revising findings

### 4.1 NO operational cleaning beats every cleaning strategy at DKA baseline assumptions

At $10/kW cleaning cost and $0.10/kWh electricity, NONE wins at $13.07/kW/yr. The cheapest cleaning strategy (threshold=10%, ~1/yr) costs $20.11 — **$7/kW/yr worse than not cleaning at all.**

Why: natural rain at DKA bounds soiling at steady-state ~6.5%. Without operational cleaning, soiling fluctuates around ~6% (matching the MC mean 6.51%). Adding 1 cleaning/yr at $10/kW recovers only ~2.5% of that loss — not enough to pay for the cleaning.

Analytical sanity check: steady-state with no cleaning satisfies r(1−s/s_sat) = rain_rate × f_rain × s → with r=0.15 %/day, sat=25%, rain=0.08/day, f=0.233 → s ≈ 6.1%. Matches MC mean within sampling noise.

### 4.2 Probe 13's optimum was systematically over-cleaning-biased

Probe 13 / memo 40 reported $46.89/kW/yr at 156-day cleaning as the optimum. MC says the SAME strategy actually costs $39.63/kW/yr (slightly lower because rain cleaning helps even at 3/yr cleaning) — but the strategy itself is 3× worse than NONE.

The deterministic model assumed soiling grows linearly without bound. Realistically, rain caps it. Including this cap eliminates most of the value of operational cleaning at standard cost assumptions.

### 4.3 Pure-opportunistic strategies are economically TERRIBLE

opp_lag=2d cleans 22.45×/yr (because there are ~29 rain events and most fall outside the min-interval). Cost $228.92/kW/yr. 18× worse than NONE.

The substrate's observed ~3.5/yr operational regime at DKA is NOT well modeled by pure opportunistic. It's best modeled as opp_lag=3d_min=90d (3.8/yr, $46.77) — opportunistic with a hard 90-day spacing constraint.

This implies DKA's operator behavior is "clean after rain BUT only if it's been ≥90 days since the last cleaning." Probes 9-11 captured the "lag 2-4 days post-rain" signature but didn't characterize the spacing constraint. New substrate inference about the operator behavior.

---

## 5. So why does DKA clean at all?

If the model is right, DKA's observed ~3.5/yr cleaning regime costs them **~$33/kW/yr more** than not cleaning ($46.77 vs $13.07). Plausible explanations:

1. **DKA is a research facility, not profit-maximizing.** Data quality / consistency requires periodic clean-baseline calibration. Cleaning serves the science mission.
2. **Cleaning cost at DKA is much lower than $10/kW.** Site-local labor + amortized equipment may put true cost at $1-2/kW per cleaning. At $2/kW: threshold=8% becomes $12.30/yr vs NONE $13.07 — basically tied. At $1/kW: cleaning starts to win.
3. **Cleaning has non-electricity benefits not captured by the model.** Panel inspection during cleaning catches faults; dust removal extends junction-box reliability; calibration against soiled vs cleaned baselines is itself valuable.
4. **The model under-estimates soiling damage.** Real soiling may cause cell hotspots that accelerate degradation; permanent soiling fraction (un-cleanable cementation per CLM-093); ESG / appearance value.

The MC says DKA's behavior is economically suboptimal at retail cost assumptions; site-specific cost realities may differ.

---

## 6. What gets RIGHT vs WRONG when MC vs Probe 13 disagree

| Question | Probe 13 (deterministic) | Probe 14 (MC) | Which is right? |
|---|---|---|---|
| Optimal cleaning frequency for arid sites | 2-3/yr | 0-1/yr | MC (rain accounted for) |
| Cost of "no cleaning" | not modeled (assumed catastrophic) | $13/kW/yr (modest) | MC |
| Cost of DKA observed regime | $50/kW/yr (~10% above optimum) | $47/kW/yr (~3.6× above optimum) | MC |
| Whether lag-2-4 is economically rational | yes | only with min-interval constraint | MC |
| Whether DKA is near-optimal | yes | no (~3.6× cost vs NONE) | MC |
| Order-of-magnitude per-kW cost | ~$50/kW/yr | $13-50/kW/yr depending on strategy | both reasonable bracket |

Probe 13's framing now reads as a "scheduled-only worst case" comparator; Probe 14 is the substrate's defensible economic model.

---

## 7. Sensitivity on cleaning cost (where does cleaning become worth it?)

Quick check: at what $C/kW per cleaning does threshold=8% beat NONE?
- threshold=8%: 1.95 cleanings × $C + $8.45 soiling = $1.95C + $8.45
- NONE: $13.07
- 1.95C + 8.45 < 13.07 → C < $2.37/kW per cleaning

**At cleaning cost ≤ $2.37/kW (i.e., ≤ $2.40 per kW per cleaning), threshold=8% becomes worth doing.** This is plausibly achievable for site-local-labor operations. Above that, NONE wins.

Sensitivity on electricity price:
- At $0.20/kWh (double baseline): NONE = $26.13, threshold=8% = $19.55 + $16.90 = $36.46 — NONE still wins
- At $0.40/kWh: NONE = $52.26, threshold=8% = $19.55 + $33.79 = $53.34 — still tied
- Electricity price would need to be very high before cleaning at $10/kW becomes worth it

---

## 8. Honest caveats

1. **Calibration assumes the substrate's V2 inference (~3.5 operational/yr at DKA) is approximately correct.** If the actual rate is 1/yr (matching DKA's public "annual cleaning"), the f_rain calibration changes — would need to refit.
2. **Saturation level (s_sat = 25%) is assumed, not measured.** Lit supports 15-35% depending on tilt + climate. If s_sat is lower (say 15%), natural cleaning is even more effective and cleaning even less worth it. If higher (35%), cleaning becomes more valuable.
3. **No correlation between rain events.** Real rain may come in clusters (storm seasons); model uses independent draws from DOY probabilities. Probably understates burst-clean events.
4. **No deposition variability within season.** Real days have variable deposition; model uses fixed wet/dry rates. Probably averages out.
5. **Single fixed cleaning cost.** Real cleanings cost more if site is far/large/inaccessible.
6. **Linear electricity value.** Real time-of-use markets may pay more for clean-output hours.

These caveats don't change the headline (NONE beats cleaning at standard assumptions) but soften specific numbers.

---

## 9. Substrate-substantive implications

1. **For commercial arid sites considering V2 methodology:** the operational regime V2 detects may not be economically optimal at the site's actual costs. V2 tells you OPERATIONAL CLEANING IS HAPPENING; whether it should is a separate question that depends on site-specific cleaning cost vs electricity value.
2. **For DKA specifically:** the ~3.5/yr regime suggests cleaning cost is below $2.50/kW (otherwise the operator is over-cleaning). Either site-local labor is cheap or non-electricity benefits dominate.
3. **For substrate Track 3 (DKA case study) publication:** revise §3 of memo 30 (post-wet-season cleaning recommendation) to note that economic ROI depends critically on cleaning cost; at typical utility cleaning costs ($10/kW), NO operational cleaning may be optimal at arid sites with regular rain.
4. **For substrate Track 1 (V2 methodology paper):** V2 detects cleaning regime independently of whether the cleaning is economically rational. This is a feature — the methodology can identify operator behavior patterns regardless of their optimality.

---

## 10. CLM updates

- **CLM-113 (Probe 13 optimum) DOWNGRADED**: deterministic estimate was over-cleaning-biased; MC shows NONE beats all cleaning strategies at baseline assumptions. Probe 13's $47/yr 156-day optimum is correct WITHIN the scheduled-only / no-natural-cleaning framework but not the global optimum
- **CLM-115 NEW:** MC model NONE-vs-cleaning crossover at cleaning cost ≈ $2.37/kW per cleaning (assuming $0.10/kWh, threshold=8% strategy). DKA's observed ~3.5/yr regime is suboptimal at standard cost assumptions unless cleaning cost ≤ $2.37/kW or non-electricity benefits dominate
- **CLM-116 NEW:** DKA's observed operational regime is best modeled as "opportunistic-post-rain with 90-day minimum interval" (3.8/yr, lag=3d, min=90d) — NOT pure lag-2-4-day cleaning (which would yield ~22/yr). Probes 9-11 captured the lag signature but missed the spacing constraint
- **CLM-117 NEW:** Steady-state soiling at DKA with no operational cleaning ≈ 6.1% analytical, 6.51% MC — natural rain alone bounds the system. Substrate-substantive: operational cleaning at arid sites with regular rain has limited marginal value at standard costs

---

## 11. What this closes

- Substrate Track 3 (DKA case study) economics — now characterized with honest cost crossover
- Comparison of strategy classes (scheduled vs opportunistic vs threshold vs mixed)
- Identification of DKA operator behavior pattern (opp + min-interval) as inference refinement

## 12. What this opens

- Cross-site MC for MA (much lower natural cleaning value because climate is humid and cleaning frequency matters differently)
- Cost-aware V2 reporting: "your fleet is doing X operational cleanings/yr — given your assumed cleaning cost $C, is this above/below the economic optimum?"
- Sensitivity to s_sat — would benefit from a literature anchor on saturating-soiling parameters

---

## 13. Artifacts

- `code/probe14_cleaning_monte_carlo.py`
- `data/processed/probe14_monte_carlo_strategies.csv`
- `data/processed/probe14_calibration.json`

---

**END Probe 14** — Monte Carlo substantially revises Probe 13. At DKA baseline cost assumptions, NO operational cleaning beats every cleaning strategy ($13.07/kW/yr vs $20+ for any cleaning). DKA's observed ~3.5/yr regime is economically suboptimal at retail costs but reasonable at site-local cleaning costs ≤ $2.50/kW. Substrate-substantive: natural rain bounds soiling at ~6.5% steady-state at DKA; operational cleaning has limited marginal economic value.
