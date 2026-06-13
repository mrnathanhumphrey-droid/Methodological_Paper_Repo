"""Generate the 2-page lever-rundown PDF for NBA Projections."""
from fpdf import FPDF
from pathlib import Path

OUT = Path(__file__).parent / "lever_rundown.pdf"

# Each row: (lever, how, result)
# Result starts with [WIN], [LOSS], [PARTIAL], or [IN PROGRESS]
ROWS = [
    ("v4-lite scaffold", "", ""),
    ("TQ + gravity teammate effects",
     "Added teammate-quality + gravity covariates to the per-game NB2 model.",
     "[WIN] Shipped to Wonka. Captures pace + role context cleanly."),
    ("young-on-tank + alpha_promotion",
     "Per-position promotion-rate covariates to capture role expansion on bad teams.",
     "[LOSS] Removed in cross-season ablation - no consistent signal, added noise."),

    ("Avenue 4 - per-position phi", "", ""),
    ("Per-position NB2 overdispersion",
     "Replaced scalar phi with a per-position vector so guards/forwards/centers each get their own variance calibration.",
     "[WIN] 11-stat overnight sweep clean, coverage_80 in [0.77, 0.86] - tight to nominal."),

    ("Shooting-percentage attempts", "", ""),
    ("Joint LKJ 3PT/FT correlation",
     "Cholesky-factored covariance on player random effects to share information across stats.",
     "[LOSS] Hierarchical-pool collapse - all elite shooters projected near league mean."),
    ("Independent 3PT% Stan",
     "Same hierarchical scaffold without the LKJ joint structure, looser priors.",
     "[LOSS] Same collapse - confirmed cause was not the LKJ piece."),
    ("EB Beta-Binomial 3PT% with FT% transfer",
     "Closed-form conjugate update: each player's prior 3PT% set from their FT% via a transfer function, then updated by their attempts.",
     "[WIN] Spread fully recovered: Curry projected 0.405 vs Stan's collapsed 0.36."),
    ("EB-rate * v4-lite FG3A volume",
     "Multiplied the clean EB rate by v4-lite's projected per-36 FG3A.",
     "[LOSS] v4-lite FG3A is bad enough that combined output was 17% worse than modeling makes directly."),
    ("EB-rate * oracle FG3A (sanity)",
     "Multiplied EB rate by ACTUAL test-season FG3A to isolate rate quality from volume quality.",
     "[WIN] 46% improvement - confirms rate generalizes; bottleneck is volume side."),

    ("FG3A volume covariates", "", ""),
    ("team_3PA_rate as single covariate",
     "Added prior-season team three-point attempt rate as a covariate to v4-lite FG3A.",
     "[LOSS] Only 3.7% variance explained among stayers, ~0% among movers - too weak to overcome noise."),

    ("Minutes (mpg) projection", "", ""),
    ("Hierarchical Gaussian on log(mpg)",
     "Stan model with age curve, team_changed flag, prior-mpg regression, rookie indicator.",
     "[LOSS] Collapsed catastrophically - all 641 players projected within 1.5 mpg, KD = 17 mpg vs reality 37."),
    ("Mode-count diagnostic on mpg/48",
     "KDE peak detection on the empirical distribution before choosing model form.",
     "[WIN] Found 3 modes (bench/rotation/star) - confirms unimodal won't work, mixture model needed."),

    ("Turnovers", "", ""),
    ("Own-usage z-score covariate",
     "Added beta_own_usage to v3 Stan to capture within-player usage shifts driving turnovers.",
     "[LOSS] Identifiable with mu_player intercept (R-hat 1.044 on the lift), MAE got worse."),

    ("Opponent strength (Lever 2)", "", ""),
    ("Season-level opp_strength_z",
     "Minutes-weighted opponent defensive rating as a per-row covariate.",
     "[LOSS] Signal too small at season-level granularity (averages out)."),
    ("Ship raw def_rating to Wonka",
     "Exported team_def_rating_history.parquet for week-level use downstream.",
     "[WIN] Wonka uses it for week-level matchup adjustments where the signal lives."),

    ("Pre-fit safety", "", ""),
    ("Empirical-vs-prior calibration ratio",
     "Diagnostic that compares empirical player-level spread to the prior's expected spread before any Stan fit.",
     "[WIN] Caught what would've been the 4th over-shrinkage before any compute. Now standard practice."),

    ("Shot-zone v5 (Stage 1)", "", ""),
    ("Per-zone NB2 volume",
     "Decomposed FGA into 6 zones (RA / paint / mid / lc3 / rc3 / ab3); hierarchical pooling per zone.",
     "[WIN] All zones passed pre-fit calibration, fit landed in 16 min, per-zone phi excellent (RA=17, Paint=10)."),

    ("Shot-zone v5 (Stage 2)", "", ""),
    ("Per-zone binomial-logit efficiency",
     "Player-level FG% by zone with hierarchical pooling, composes with Stage 1 volume.",
     "[WIN] FG-only MAE 0.98 PTS/36 vs 2.38 with league-average FG% - 59% reduction. Stage 1+2 reconstruction in healthy band."),

    ("Shot-zone v5 (Stage 3-4)", "", ""),
    ("Role-slot projection blending (fixed alpha heuristic)",
     "When a player moves teams, blend their intrinsic zone allocation with the role's expected per-36 zone volumes (departing-player avg for trades, own prior per-36 for stayers, team avg for FAs). alpha=1 stayer / 0.5 mover / 0.3 FA.",
     "[WIN] Modest 2.8% MAE improvement on movers+FAs, but big wins on trade-to-smaller-role: Jrue Holiday MIL->BOS error reduced by 3.34 FGA, Bradley Beal WAS->PHX by 3.59. Stayer-breakouts still missed (Brunson)."),

    ("Shot-zone v5 (Stage 5)", "", ""),
    ("Hierarchical alpha learned from history",
     "Per-player alpha estimated inside Stan with partial pooling toward position then league mean. Goal: replace the fixed-alpha heuristic with data-driven estimates.",
     "[LOSS] alpha collapsed to ~0.98 for everyone (kappa_alpha=138, very tight pool). Identifiability gap predicted in design notes: 46% stayer rows give alpha no traction, only 21% trade rows can't override the position pool. Stage 3-4 v1 fixed-alpha heuristic wins."),

    ("v6 drive-volume / FTA (v1, multiplicative)", "", ""),
    ("Multiplicative compose drives + postups",
     "Projected per-36 FTA = drives_per_36 * fta_per_drive_eb + postup_per_36 * fta_per_postup_eb * 1.10 residual.",
     "[LOSS] Drives + post-ups cover only 33% of total FTA; residual factor varies hugely by player (q25=2.18, q75=4.37). Empirical median residual is 2.95, not 1.10. Even with calibrated factor still loses to v4-lite."),

    ("v6 v2 (direct NB2 with covariates)", "", ""),
    ("Direct NB2 with drives + paint + postup as per-36 covariates",
     "Reframed as regression: model FTA directly with drives, paint_touches, post_touches as centered per-36 covariates. Lets Stan learn the linear combination.",
     "[WIN] MAE 0.71 beats both naive (0.79, +9.9%) and v4-lite (0.73, +1.9%). Per-position phi 16-22 vs v4-lite's 2.4 - 5-10x precision improvement. The architectural fix the queue review predicted."),

    ("Mpg projection redo", "", ""),
    ("3-component Gaussian mixture on log(mpg)",
     "Bench/rotation/star components with covariate-dependent mixing weights. Built after mode diagnostic detected 3 modes.",
     "[LOSS] MAE 5.37 vs naive 3.68 (-46%). Weighted-average projection compresses extremes (KD: 37 actual, 23 projected). Mixture obscures year-over-year autocorrelation that naive captures cleanly."),
    ("Simple Gaussian regression on log(mpg)",
     "OLS regression with log_prior_mpg + age + team_changed + position dummies, no per-player intercept, no mixture.",
     "[LOSS] MAE 3.82 vs naive 3.68 (-3.8%). Coefficients sane (beta_prior=0.79 mean reversion, beta_team_changed=-0.06) but breakouts (Cam Thomas 22->31, Coby White 24->36) and role-loss cases (Bullock 30->9) unpredictable from public data. Mpg projection is genuinely hard at this granularity; naive is the ship target."),

    ("Defensive STL/BLK diagnostic", "", ""),
    ("Tracking covariates (deflections, rim_dfg_pct) for STL/BLK",
     "Tested whether prior-season tracking metrics explain v4-lite STL/BLK residuals on team-switchers and role-shifters.",
     "[MIXED] BLK: prior_blk alone has r=0.88 with future BLK, fully absorbs the signal. Tracking adds nothing (residual r < 0.10). STL: deflections has marginal signal (partial r=0.21 controlling for prior_stl). BLK stays on v4-lite scaffold."),
    ("STL with deflections covariate (build attempt)",
     "Built season-level NB2 on STL with deflections_per36 as centered covariate, mirroring v6 v2 architecture.",
     "[LOSS] MAE 0.221 - beat naive +9% but lost to v4-lite -16.6% (0.189). Partial r=0.21 wasn't enough to overcome the architecture penalty of season-level vs v4-lite's game-level NB2. v4-lite STL stays as is."),

    ("Shot-zone v5 stayer-breakout absorption", "", ""),
    ("Teammate-departure absorption for stayers",
     "When a stayer's team had significant departures (>=10% of retained minutes), blend their intrinsic with departing players' avg per-36 zone profile, scaled by stayer's minutes share. Cap at 30% volume increase.",
     "[PARTIAL WIN] Brunson NYK->NYK projection improved by +2.90 FGA (15.3->18.2 vs actual 21.7). Stable stayers (KAT) stay neutral. Toronto cohort (Siakam, Anunoby) over-absorbed slightly because not all retained players absorb proportionally to minutes."),

    ("AST + tracking covariates (passing endpoint)", "", ""),
    ("Direct NB2 with passes_made, potential_ast, secondary_ast, drive_ast",
     "Same architecture as v6 v2 FTA but for AST. Tracking covariates have strong effects (potential_ast +0.107, secondary_ast +0.111).",
     "[LOSS] MAE 0.744 vs v4-lite 0.666 (-11.7%). Same architecture penalty as STL deflections - season-level NB2 with covariates loses to v4-lite's game-level scaffold when v4-lite is already well-specified."),

    ("TOV + tracking covariates (drive_tov)", "", ""),
    ("Direct NB2 with drives, drive_tov, post_touch_tov",
     "Same architecture as v6 v2 FTA. Tracking shows huge effects (beta_drive_tov +0.62, beta_post_touch_tov +0.84).",
     "[LOSS] MAE 0.363 vs v4-lite 0.314 (-15.6%). Confirms architectural rule: covariate-augmented season models only beat v4-lite where v4-lite is structurally underspecified (FTA had phi=2.4, AST/TOV/STL/REB do not)."),

    ("Lever 2 (FT% Bayesian shrinkage diagnostic)", "", ""),
    ("Decompose FTM error into FTA-side vs FT%-side",
     "Substitute actual FTA × proj FT% and proj FTA × actual FT% to isolate which side carries FTM error.",
     "[DISCONFIRMED] FTA error 4x larger than FT% error (0.547 vs 0.129). EB FT% modeling would deliver ~0 lift. Saves ~1h of build time."),

    ("FTM compose ship", "", ""),
    ("FTM = v6 v2 FTA × Laplace-smoothed train FT%",
     "Multiply v6 v2 FTA projection by career-train FT% with Laplace prior of 50 attempts at league mean (0.78).",
     "[WIN] MAE 0.583 - beats v4-lite by 3.7% and naive by 10.0%. Has +0.157 bias from FTA over-projection on low-volume players (hierarchical pooling regression-toward-mean). Ship as FTM override."),

    ("Lever 3 (game-script intentional foul)", "", ""),
    ("Team close-game share x low-FT% interaction as FTA covariate",
     "Built team-level close-game frequency from PBP (margin <= 5 in last 3 min of 4th Q). Added intentional_foul_proxy = max(0, 0.78 - career_ft) * close_game_share as 4th covariate to v6 v2 FTA model.",
     "[LOSS] MAE 0.713 vs v6 v2 0.712 (-0.1%). Coefficient came back NEGATIVE (-0.92) - model learned 'low-FT% bigs benched in close games' not 'hacked.' Cheap team-level proxy can't substitute for lineup-level minutes-by-margin engine. Real Hack-a-Shaq mechanism requires player-presence-during-close-late which PBPStats provides; raw nba_api would be 2-3 weeks engineering for ~1.4% lift on 34-player cohort."),
]

LESSONS = [
    "Hierarchical pooling collapses when player obs are sparse and recency-weighted - use empirical-Bayes conjugate updates for rate stats, not Stan hierarchical pooling.",
    "Aggregate covariate fixes (team_3PA_rate, own_usage) don't beat structural factorization. When a stat is downstream of a more fundamental quantity, model the upstream quantity.",
    "Multiplicative composition needs ALL event sources or it systematically undershoots. Direct NB2 regression with all sources as covariates beats compose-then-multiply (v6 v2 vs v6 v1).",
    "Pre-fit calibration ratio (empirical SD vs prior expected SD, target [0.5, 2.0]) is now standard practice. It caught what would've been the 4th hierarchical-pool collapse before any compute.",
    "When fixing one layer surfaces error in an adjacent layer, that's correct progress. Each iteration approaches correct factorization one layer at a time.",
    "Mixture models on heavily autocorrelated stats (mpg) can lose to naive 'predict next = prior'. The mixture's weighted-average projection compresses extremes while naive preserves them. Sometimes the simpler baseline is just genuinely hard to beat.",
    "Hierarchical alpha (per-player learned blending parameter) is unidentifiable when most training data is from stable role contexts. Fixed-alpha heuristics can outperform learned alpha when role-shift training rows are sparse. Validates the design-time skepticism about identifiability.",
    "Fast cheap diagnostics beat fast cheap fits. The defensive STL/BLK diagnostic showed prior-stat history fully absorbs tracking signal for BLK, marginally for STL - saved a 3-5h fit cycle that would have shipped a model with no real lift.",
]


def make_pdf():
    pdf = FPDF(orientation="P", unit="mm", format="Letter")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.set_margins(left=12, top=12, right=12)

    # Page 1
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 7, "NBA Projections - Lever Rundown", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 4, "Plain-English summary of every architectural lever tried (2026-04-29 / 04-30 sessions)",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    section_font = ("Helvetica", "B", 9)
    lever_font = ("Helvetica", "B", 8)
    body_font = ("Helvetica", "", 8)
    LINE = 3.6

    for lever, how, result in ROWS:
        if how == "" and result == "":
            # Section header
            pdf.ln(1)
            pdf.set_font(*section_font)
            pdf.set_fill_color(220, 220, 220)
            pdf.cell(0, 5, f" {lever}", new_x="LMARGIN", new_y="NEXT", fill=True)
            pdf.ln(0.5)
            continue
        # Lever entry
        pdf.set_font(*lever_font)
        pdf.cell(0, LINE + 0.5, lever, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(*body_font)
        pdf.set_x(15)
        pdf.multi_cell(180, LINE, "How: " + how, new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(15)
        pdf.multi_cell(180, LINE, "Result: " + result, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.5)

    # Lessons section (top of page 2 if it didn't fit on 1)
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(180, 180, 220)
    pdf.cell(0, 6, "  Architectural lessons (the wins from the losses)",
             new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(1)
    pdf.set_font("Helvetica", "", 8)
    for i, lesson in enumerate(LESSONS, 1):
        pdf.set_x(15)
        pdf.multi_cell(180, 3.6, f"{i}. {lesson}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.3)

    pdf.output(str(OUT))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    make_pdf()
