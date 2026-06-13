# MPG Post-Mortem: where we hit the ceiling and what's next

*Briefing for Claude Desktop. No code requested — this is for narrative analysis and strategy thinking.*

## The problem in one paragraph

Our NBA projection engine ships independent per-game stat projections (PTS, REB, AST, STL, BLK, TOV, FG%, FT%, 3PM and the underlying volume/make pairs). On the 2023-24 backtest our v6 ship beats consensus on 5 of 9 fantasy categories (REB, BLK, TOV, FG%, FT%) and loses on PTS, AST, STL, FG3M, MPG. The losses are nearly all downstream of MPG: our PTS *per-36* beats consensus, but our MPG MAE is 2.99 vs theirs 2.63 — a 14% gap that propagates to roughly a 6-9% loss on every per-game stat that runs through MPG. This document is about why we can't close that 14% gap with historical data alone, what we tried, what worked, and where we go from here.

## What we tried, in order

**Career-weighted MPG (shipped in v2 and forward)**: blend prior-season MPG with a 3-year exponentially-weighted career average plus an age-decline curve, weighted 30/70 (prior/career). This shipped because it beat naive (predict prior season) by 6.3%. The career-blend is now baked into v6.

**Chronic injury flag from games-missed percentage**: compute `1 - (sum_gp_last_3_years / sum_max_scheduled)` per player and use it to discount projected MPG. Result: signal is real on the broad universe (MAE 0.21 vs naive 0.24, r=0.36) but disappears once you filter to the established NBA cohort that actually matters for fantasy projections. In that filtered cohort the league baseline (predict everyone gets the league average GP rate) beats the chronic flag because established NBA regulars are extremely homogeneous in availability — most healthy rotation players play 60-70+ games regardless. The Embiid/Kawhi outliers are *salient* but they don't separate cleanly enough from the rest of the chronic-flagged universe for a single number to capture them. Wonka's hand-curated 4-tier system (Low/Medium/High/Very High) outperforms a games-missed formula because the *categorical* knowledge is what matters — knee surgery vs ankle sprain history vs Achilles rupture aren't equivalent even at the same games-missed rate.

**TOV and AST decomposition (touches × TOV-per-touch; potential_ast × conversion rate)**: data is in our tracking parquets. The diagnostic test using oracle volume looked like a huge win (TOV decomp -29%, AST decomp -61% per-game MAE), but the gain was an artifact of comparing decomp-with-actual-MPG against ship-with-projected-MPG. Apples-to-apples per-36 comparison showed the decomposition lost: TOV per-36 -3.8%, AST per-36 -8.3%. Confirmed the architectural rule: **decomp only beats hierarchical pooling where the aggregate model is structurally underspecified**. v4-lite captures AST and TOV directly better than the volume × rate split.

**Covariate additions on rate stats (FT% as predictor of 3PT%, AST as predictor of TOV)**: an in-sample diagnostic suggested a 12.7% MAE improvement on FG3M from adding career FT% as a regressor on career 3PT%. When applied to the actual ship cohort, the v8 build was a 2.3% regression because v6's existing prior+career blend on 3PT% already beats the simple career-3PT% baseline the diagnostic compared against. Same shape on TOV. Lesson: improvements measured against a stripped-down baseline don't necessarily survive against the well-tuned v6 blend.

**Role-state-aware MPG (off-season trade detection + slot allocation)**: the most promising idea on paper. We can detect off-season trades trivially from box scores (last team in season N vs first team in season N+1 with at least 5 games). We have lineups_ctg historicals to derive depth-chart-like role inference. The diagnostic split MPG miss cohorts cleanly: stable stars MAE 1.91, off-season trades MAE 3.79 (+0.76 bias), mid-season-only trades MAE 3.56 (+2.48 bias). The off-season trade cohort's bias is small relative to its noise — a flat correction barely moves the MAE. Mid-season trades are unpredictable preseason. Realistic ceiling for a properly-built role-state model: ~0.2-0.3 MAE off the overall (2.99 → 2.70-2.80). Real but not close to consensus 2.63.

## What actually worked: the in-season update mechanism

This is the one that made everything else feel small.

The architecture: at each game checkpoint K (=5, 10, 20, 40, 60), blend the v6 preseason MPG with observed-through-K MPG using a Bayesian formula. Sweep blend weights to find the optimum. The optimum prior strength turned out to be W=5 (preseason worth ~5 equivalent-games of in-season observation), which is much smaller than I initially expected.

The MAE curve as a function of K (with optimal W=5):
- K=0 (pure preseason): 2.99
- K=5 (Halloween): 2.45 (-18% vs preseason; already beats consensus 2.63)
- K=10 (mid-November): 2.14 (-29% vs preseason; beats consensus by 19%)
- K=20 (Christmas): 1.80 (-40% vs preseason; beats consensus by 32%)
- K=40 (mid-January): 1.06
- K=60 (All-Star break): 0.50

By cohort at K=20 with the blend:
- True stayers: 2.62 → 1.77 (-32%)
- Off-season trades: 3.71 → 1.69 (-54%) — biggest cohort improvement
- Mid-season trades that have already happened by Dec: 3.77 → 2.28 (-40%)

The reading is straightforward: **observed minutes are far more informative than any historical prior, very quickly**. Five games is enough information to start dominating preseason career patterns. By Christmas the preseason source is essentially noise relative to the in-season signal.

This explains why consensus beats us at preseason (they have analyst-curation we lack) but not necessarily at mid-November. Once the season begins, the analyst's preseason MPG projection is also stale relative to what the player is actually doing on the court. The data catches up to and surpasses the curation.

**Trade-aware refinement**: an obvious worry was that the Bayesian blend would be naive about mid-season trades — averaging pre-trade games on the old team with post-trade games on the new team would mis-project a player whose role collapsed after the trade. We tested this explicitly: built a "trade-aware" version that resets the observation window to post-trade only, and compared to the naive blend. At K=20 the two are essentially identical (overall MAE 1.81 vs 1.80; on the mid-season trade cohort 2.25 vs 2.16 — naive marginally wins). The reason: with prior strength W=5, observed games dominate the prior so heavily that by K=20 the post-trade observations have already outweighed the pre-trade on a sheer-count basis. The blend handles trades implicitly, not via detection. At earlier checkpoints (K=5 or K=10) explicit trade detection probably *would* help — worth implementing for the live system but not a structural ceiling concern.

## The two ceilings

**Pure-data preseason ceiling**: ~2.99 MPG MAE. We can't close to consensus's 2.63 from historical data alone because the gap is human-curation-only signal: depth chart announcements, summer league observations, training camp battles, trade rumors before they're official, coach-stated rotation plans, injury status going into camp.

**Pure-data in-season ceiling**: drops fast. By game 5 we're at 2.45 (already better than consensus's 2.63 preseason). By Christmas we're at 1.80, beating consensus by 32%.

The strategic implication: **pure-data approaches can never beat consensus at preseason, but can dominate them in-season**. For products that are preseason-only (fantasy auctions like Wonka), the analyst-curation gap is irreducible from historical data. For products that update in-season (DFS, prop betting, in-season fantasy management), our data approach is structurally superior to the analyst-curated approach within ~1-2 weeks of opening night.

## The independence question

We considered ingesting consensus MPG projections directly (FantasyPros, Hashtag Basketball) as input to our model. This would close the preseason gap by definition. We rejected it because:
1. Independence is a load-bearing design commitment of this project. Per the project memory, the audit-CSV contract with Wonka is the firewall against "two Bayesian systems co-designed by one mind collapsing signals into self-reference."
2. If our edge is "we beat FantasyPros," and we ingest FantasyPros, the edge collapses on every MPG-driven stat by construction.
3. For the eyes-only betting layer, ingesting consensus is incestuous — we'd be modeling against the same crowd whose forecasts we consumed.

The legitimate way to close the preseason gap is to do the human curation ourselves from primary sources. We have a fetcher brief drafted to scrape Pro Sports Transactions DB (injuries + transactions back to ~2014), Basketball-Reference per-season transactions (mid-season trade dates), Spotrac contracts (expiring contracts as trade-probability proxy), NBA.com summer league + preseason box scores, and NBA.com official injury reports. That work is independent — primary data, not analyst opinion.

## Open questions for strategy thinking

A few things I want sharper thinking on, where Desktop's research-mode framing could help:

**1.** For DFS / prop markets, the in-season update mechanism gives us a real edge from game 5 onward. Markets are priced by the consensus crowd's preseason views, plus reactive in-season updates that lag observed data. How much edge is actually capturable here vs how much is already priced in by mid-season? Is the 1.8 MAE we'd hit at K=20 enough to clear the vig on prop bets, or is it just enough to be at the table?

**2.** For preseason fantasy auctions (Wonka), our MPG MAE 2.99 is structurally worse than consensus 2.63. We win on 5 of 9 cats anyway because rate stats (FG%, FT%) and certain volume stats (REB, BLK, TOV) don't require analyst curation. Is the right framing for Wonka users "we're better at the cats consensus is bad at, worse at the cats consensus is good at" — and if so, does that actually matter for auction strategy, where you can compose a roster from selectively-strong projections?

**3.** The chronic injury flag failed because it conflated NBA-roster-status with health. Wonka's hand-curated 4-tier system works because human knows the *category* of injury. Could we automate the curation by mining Pro Sports Transactions DB body-part text for injury type, then encode something like "chronic Achilles" vs "chronic knee" vs "freak ankle one-time" as separate features? That's a distinct architecture from the simple games-missed flag.

**4.** The in-season update mechanism is a different product than the preseason ship. Should we structure the project as two distinct deliverables — "preseason ship for auctions" and "live ship for DFS/in-season" — with separate audit pipelines? Or one ship with a flag that flips after game 5?

**5.** The fetcher brief covers the primary-source scrape stack. Realistic build is 30-50 hours engineering. Is the right move to do this fetch work *before* we operationalize the in-season update mechanism (because in-season already gets us most of the way), or to focus on the in-season build first because it dominates the EV math?

## Bottom line

The MPG ceiling we hit pure-data-only is real and structural at preseason. We close it in two ways:
- **Slow path**: scrape primary sources to do the curation ourselves (preseason gap closes from data, not analyst feeds).
- **Fast path**: in-season update mechanism dominates analyst curation within 5-10 games of opening night.

The slow path is independent and robust but engineering-heavy. The fast path is essentially free (Bayesian blend of preseason career-data with weekly observations) and produces meaningful out-performance starting at K=5.

For our purposes, doing both is the answer: ship v6 preseason, fire the in-season update from game 5 onward, and pursue the scrape work in parallel to close the residual preseason gap over time. The preseason ceiling improves incrementally as the scrape stack matures; the in-season mechanism closes the rest.

The "alpha" framing is real but I want to be honest about it: the alpha is in the in-season layer, not the preseason layer, and it shows up against props/DFS markets that price off the consensus's mid-season-staleness, not against fantasy auctions which happen before game 5.
