"""LOO MSE + interval-coverage validation for fetchy's two passing soph levers.

Lever 1 (coach continuity): variance tightener — multiply same-HC soph sd by
  empirical ratio (sd_same / sd_diff). Test by interval coverage at 50/80/90:
  if shrunk intervals still cover at nominal rate, lever is calibrated.

Lever 3 (pre-NBA over-performance gap): signed mean shifter — adjust soph
  projection by β_gap × (pre_NBA_per40 − rookie_per40). Test by LOO MSE:
  hold one player out, fit β on the other 735, project held-out, compare
  MAE with vs without lever.

Baseline both tests against H2 baseline (24-25 H2 → 25-26 forward, the
current cohort widening v1 baseline).

Both levers must:
  1. Produce consistent sign of effect across ≥7 of 10 transitions
  2. Pass LOO MSE (Lever 3) or interval coverage (Lever 1)
  3. Have the per-stat magnitude make physical sense
"""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from pathlib import Path
import pandas as pd
import numpy as np

# Reuse pair-building from the test script
sys.path.insert(0, "scripts")
from test_fetchy_soph_levers import (
    load_box_scores, build_rookie_year2_pairs,
    add_coach_continuity, add_pre_nba_gap, per_game_per_36,
)

REPO = Path(".")
PQ = REPO / "data" / "parquet"


# ──────────────────────────────────────────────────────────
# H2 baseline — what the current cohort widening v1 produces
# ──────────────────────────────────────────────────────────

def h2_baseline_per_player(bx, rookie_season):
    """Each rookie's late-half rate stats × full-season MPG (matches
    cohort_widening_2025_26.py logic for sophs)."""
    sub = bx[bx["season"] == rookie_season].sort_values(["nba_api_id", "game_date"]).copy()
    sub["rank"] = sub.groupby("nba_api_id").cumcount()
    sub["gp_total"] = sub.groupby("nba_api_id")["game_id"].transform("count")
    h2 = sub[sub["rank"] >= sub["gp_total"] / 2.0].copy()

    full_per36 = per_game_per_36(sub).rename(columns={"season": "rookie_season"})
    h2_per36 = per_game_per_36(h2).rename(columns={"season": "rookie_season"})

    # Take H2 rate stats with full fallback; full-season MPG always
    full_per36 = full_per36.set_index(["nba_api_id", "rookie_season"])
    h2_per36 = h2_per36.set_index(["nba_api_id", "rookie_season"])
    base = full_per36.copy()
    for c in ["PTS_p36", "REB_p36", "AST_p36", "STL_p36", "BLK_p36", "TOV_p36",
              "FGM_p36", "FGA_p36", "FG3M_p36", "FG3A_p36", "FTM_p36", "FTA_p36"]:
        if c in h2_per36.columns:
            base.loc[h2_per36.index, c] = h2_per36[c].combine_first(full_per36[c])
    base = base.reset_index()
    # Per-game projection = per-36 × mpg/36 (full-season mpg held)
    for stat in ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FGM", "FGA",
                 "FG3M", "FG3A", "FTM", "FTA"]:
        base[f"{stat}_h2pg"] = base[f"{stat}_p36"] * base["mpg"] / 36.0
    return base


def attach_h2_baseline(pair, bx):
    """Each pair gets {stat}_h2pg = the H2 baseline's projection for the soph."""
    seasons = pair["rookie_season"].unique()
    parts = []
    for s in seasons:
        parts.append(h2_baseline_per_player(bx, s))
    h2 = pd.concat(parts, ignore_index=True)
    keep = ["nba_api_id", "rookie_season"] + [c for c in h2.columns if c.endswith("_h2pg")]
    return pair.merge(h2[keep], on=["nba_api_id", "rookie_season"], how="left")


# ──────────────────────────────────────────────────────────
# Lever 3 — LOO MSE: gap-proportional mean shift
# ──────────────────────────────────────────────────────────

def loo_mse_lever3(pair, stats=("PTS", "REB", "AST")):
    """For each held-out player, fit β_gap on remaining N-1, project held-out
    with β × gap added to H2 baseline, compare MAE vs raw H2."""
    print("=" * 78)
    print("LEVER 3 — LOO MSE for pre-NBA gap (mean shifter on top of H2 baseline)")
    print("=" * 78)
    print(f"{'stat':<6} {'n':>5} {'MAE_h2':>9} {'MAE_h2+gap':>12} {'Δ%':>8} {'β_gap_mean':>12} {'sign_repl':>11}")
    print("-" * 78)

    for stat in stats:
        pre_col = f"pre_{stat}_p40"
        rk_p36 = f"{stat}_p36_y1"
        sp_pg_actual = f"{stat}_pg_y2"
        h2_proj_col = f"{stat}_h2pg"

        sub = pair.dropna(subset=[pre_col, rk_p36, sp_pg_actual, h2_proj_col]).copy()
        if len(sub) < 50:
            print(f"  {stat:<6} insufficient (n={len(sub)})")
            continue
        # gap on per-40 scale
        rk_p40 = sub[rk_p36] * 40.0 / 36.0
        sub["gap"] = sub[pre_col] - rk_p40
        # Convert gap (per-40) into an additive on H2 (per-game). We'll fit β
        # directly: residual = actual − h2; residual ~ β × gap.
        sub["residual"] = sub[sp_pg_actual] - sub[h2_proj_col]

        n = len(sub)
        x = sub["gap"].values.astype(float)
        y = sub["residual"].values.astype(float)
        mae_h2 = sub.assign(d=sub[h2_proj_col] - sub[sp_pg_actual])["d"].abs().mean()
        # LOO β
        sse_h2_gap = 0.0
        betas = []
        for i in range(n):
            mask = np.ones(n, dtype=bool); mask[i] = False
            xi, yi = x[mask], y[mask]
            if xi.var(ddof=1) == 0:
                beta = 0.0
            else:
                beta = np.cov(xi, yi, ddof=1)[0, 1] / xi.var(ddof=1)
            betas.append(beta)
            pred_extra = beta * x[i]
            err = (sub[h2_proj_col].iat[i] + pred_extra) - sub[sp_pg_actual].iat[i]
            sse_h2_gap += err ** 2

        mae_h2_gap_loo = np.sqrt(sse_h2_gap / n)
        # actually that's RMSE, recompute MAE
        mae_h2_gap_loo = 0.0
        for i in range(n):
            err = (sub[h2_proj_col].iat[i] + betas[i] * x[i]) - sub[sp_pg_actual].iat[i]
            mae_h2_gap_loo += abs(err)
        mae_h2_gap_loo /= n

        delta_pct = (mae_h2_gap_loo / mae_h2 - 1.0) * 100
        # Per-season sign replication
        season_signs = {}
        for season in sorted(sub["rookie_season"].unique()):
            sub_s = sub[sub["rookie_season"] == season]
            if len(sub_s) < 10: continue
            xs = sub_s["gap"].values; ys = sub_s["residual"].values
            if xs.var(ddof=1) == 0: continue
            b = np.cov(xs, ys, ddof=1)[0, 1] / xs.var(ddof=1)
            season_signs[season] = b > 0
        sign_repl = f"{sum(season_signs.values())}/{len(season_signs)}"

        print(f"  {stat:<6} {n:>5} {mae_h2:>9.3f} {mae_h2_gap_loo:>12.3f} {delta_pct:>+8.2f} "
              f"{np.mean(betas):>12.4f} {sign_repl:>11}")
    print()


# ──────────────────────────────────────────────────────────
# Lever 1 — interval-coverage check for variance tightener
# ──────────────────────────────────────────────────────────

def coverage_lever1(pair, stats=("PTS", "REB", "AST", "FGA")):
    """Apply same_hc sd-tightening empirical ratio. Check that 50/80/90% CIs
    still cover at nominal rates after tightening."""
    print("=" * 78)
    print("LEVER 1 — interval-coverage calibration for coach-continuity sd tightener")
    print("=" * 78)
    print(f"  Hypothesis: same-HC sophs drift less, so we tighten their proj_sd.")
    print(f"  Test: do 50/80/90 intervals stay at nominal coverage after tightening?")
    print()
    sub = pair.dropna(subset=["hc_y1", "hc_y2"]).copy()
    print(f"{'stat':<6} {'tighten_ratio':>14} {'cov50_raw':>11} {'cov50_tight':>13} {'cov80_raw':>11} {'cov80_tight':>13}")
    print("-" * 78)
    for stat in stats:
        actual_col = f"{stat}_pg_y2"
        proj_col = f"{stat}_pg_y1"  # use rookie year as the "projection" proxy
        ss = sub.dropna(subset=[actual_col, proj_col])
        if len(ss) < 50: continue
        # Empirical sd of (actual - proj) for same vs diff HC, that's our sd estimate
        same = ss[ss["same_hc"]]
        diff = ss[~ss["same_hc"]]
        if len(same) < 30 or len(diff) < 30: continue
        sd_same_emp = (same[actual_col] - same[proj_col]).std()
        sd_diff_emp = (diff[actual_col] - diff[proj_col]).std()
        ratio = sd_same_emp / sd_diff_emp

        # Build the "naive" CI using sd_diff for everyone, vs "tightened" using sd_same for same-HC
        residual = ss[actual_col] - ss[proj_col]
        # Naive: assume sd = sd_diff for all
        sd_naive = sd_diff_emp
        # Tightened: same-HC -> sd_same; diff-HC -> sd_diff
        sd_tight = ss["same_hc"].map({True: sd_same_emp, False: sd_diff_emp})

        # Coverage: |residual| / sd
        z_naive = (residual.abs() / sd_naive).values
        z_tight = (residual.abs() / sd_tight).values
        # 50% CI = ±0.6745 sd, 80% = ±1.2816, 90% = ±1.6449
        cov50_n = (z_naive <= 0.6745).mean()
        cov50_t = (z_tight <= 0.6745).mean()
        cov80_n = (z_naive <= 1.2816).mean()
        cov80_t = (z_tight <= 1.2816).mean()
        print(f"  {stat:<6} {ratio:>14.3f} {cov50_n:>11.1%} {cov50_t:>13.1%} {cov80_n:>11.1%} {cov80_t:>13.1%}")
    print()


def main():
    bx = load_box_scores()
    pair = build_rookie_year2_pairs(bx, min_gp=20)
    print(f"Total rookie→soph pairs: {len(pair)}")
    pair = add_coach_continuity(pair, bx)
    pair = add_pre_nba_gap(pair)
    pair = attach_h2_baseline(pair, bx)
    print()
    loo_mse_lever3(pair, stats=("PTS", "REB", "AST", "STL", "BLK", "TOV"))
    coverage_lever1(pair, stats=("PTS", "REB", "AST", "FGA"))


if __name__ == "__main__":
    main()
