"""Phase 3 step 2: add rest/B2B adjustment to Tier 1B.

Rest effect derived from 25-26 data (in-sample for validation; will need backtest with prior):
  - +0.71 PTS per rest-day differential (OLS coef on margin ~ rest_diff)
  - B2B teams score ~0.96 PTS less

Adjustment per team-game:
  rest_adj = REST_COEF * (team_rest - team_rest_baseline) - B2B_PENALTY * is_b2b
  Where baseline is the typical rest (use 2 days, the modal value)

team_pts_pred_p3 = team_pts_pred_tier1b + rest_adj

Validation on 25-26 RS (in-sample for coef calibration but on full season).
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from pathlib import Path

PQ = Path("data/parquet")
TIER1B = Path("audit_runs/game_predictions_2025_26_phase2_tier1b/per_team_game_predictions.csv")
OUT_DIR = Path("audit_runs/game_predictions_2025_26_phase3_rest_b2b")
OUT_DIR.mkdir(parents=True, exist_ok=True)

REST_COEF = 0.50          # per-team coef on (rest - baseline); ~half of game-level 0.71 since applied each side
B2B_PENALTY = 0.96        # B2B teams score 0.96 PTS less than non-B2B (mean delta)
REST_BASELINE = 2.0       # modal rest days


def build_rest_panel() -> pd.DataFrame:
    gl = pd.read_parquet(PQ / "regular_season_game_log.parquet")
    gl = gl[gl["season"] == "2025-26"].copy()
    gl["game_date"] = pd.to_datetime(gl["game_date"])
    gl = gl.sort_values(["team_abbreviation", "game_date"])
    gl["prev_date"] = gl.groupby("team_abbreviation")["game_date"].shift(1)
    gl["days_rest"] = (gl["game_date"] - gl["prev_date"]).dt.days
    gl["is_b2b"] = (gl["days_rest"] == 1).astype(int)
    return gl[["game_id", "team_abbreviation", "days_rest", "is_b2b"]]


def main():
    print("Building rest panel ...")
    rest = build_rest_panel()
    rest["game_id"] = rest["game_id"].astype(int).astype(str).str.zfill(10)
    print(f"  Rest rows: {len(rest)}")

    print("Loading Tier 1B per-team-game predictions ...")
    t1b = pd.read_csv(TIER1B)
    t1b["game_id"] = t1b["game_id"].astype(int).astype(str).str.zfill(10)
    print(f"  Tier 1B rows: {len(t1b)}")

    merged = t1b.merge(rest, on=["game_id", "team_abbreviation"], how="left")
    # First games of season have no prior -> days_rest NaN, treat as baseline
    merged["days_rest"] = merged["days_rest"].fillna(REST_BASELINE)
    merged["is_b2b"] = merged["is_b2b"].fillna(0).astype(int)

    # Compute rest adjustment
    merged["rest_delta"] = merged["days_rest"] - REST_BASELINE
    merged["rest_adj"] = REST_COEF * merged["rest_delta"] - B2B_PENALTY * merged["is_b2b"]

    # Apply
    merged["pred_pts_p3"] = merged["team_pts_pred"] + merged["rest_adj"]

    # Per-team error
    err_t1b = merged["team_pts_pred"] - merged["pts"]
    err_p3 = merged["pred_pts_p3"] - merged["pts"]
    print()
    print("=" * 75)
    print("Phase 3 step 2: Tier 1B + rest/B2B adjustment")
    print("=" * 75)
    print(f"Team-games: {len(merged)}")
    print()
    print("Per-team PTS error:")
    print(f"  Tier 1B    -> MAE {err_t1b.abs().mean():.4f}, RMSE {np.sqrt((err_t1b**2).mean()):.4f}, bias {err_t1b.mean():+.4f}")
    print(f"  + rest/B2B -> MAE {err_p3.abs().mean():.4f}, RMSE {np.sqrt((err_p3**2).mean()):.4f}, bias {err_p3.mean():+.4f}")
    delta_mae = (err_p3.abs().mean() - err_t1b.abs().mean()) / err_t1b.abs().mean() * 100
    print(f"  delta MAE: {delta_mae:+.3f}%")

    # Pivot to game-level
    home_t1b = merged[merged["is_home"]].copy()
    away_t1b = merged[~merged["is_home"]].copy()
    games = home_t1b[["game_id", "team_abbreviation", "team_pts_pred", "pred_pts_p3", "pts", "rest_adj", "days_rest", "is_b2b"]].rename(
        columns={"team_abbreviation": "home_team",
                 "team_pts_pred": "home_t1b", "pred_pts_p3": "home_p3", "pts": "home_actual",
                 "rest_adj": "home_rest_adj", "days_rest": "home_rest", "is_b2b": "home_b2b"}
    ).merge(
        away_t1b[["game_id", "team_abbreviation", "team_pts_pred", "pred_pts_p3", "pts", "rest_adj", "days_rest", "is_b2b"]].rename(
            columns={"team_abbreviation": "away_team",
                     "team_pts_pred": "away_t1b", "pred_pts_p3": "away_p3", "pts": "away_actual",
                     "rest_adj": "away_rest_adj", "days_rest": "away_rest", "is_b2b": "away_b2b"}),
        on="game_id", how="inner"
    )
    games["t1b_margin"] = games["home_t1b"] - games["away_t1b"]
    games["p3_margin"] = games["home_p3"] - games["away_p3"]
    games["actual_margin"] = games["home_actual"] - games["away_actual"]
    games["t1b_correct"] = (games["t1b_margin"] > 0) == (games["actual_margin"] > 0)
    games["p3_correct"] = (games["p3_margin"] > 0) == (games["actual_margin"] > 0)

    print()
    print("MARGIN:")
    err_m_t1b = games["t1b_margin"] - games["actual_margin"]
    err_m_p3 = games["p3_margin"] - games["actual_margin"]
    print(f"  Tier 1B    RMSE {np.sqrt((err_m_t1b**2).mean()):.4f}  MAE {err_m_t1b.abs().mean():.4f}  bias {err_m_t1b.mean():+.4f}")
    print(f"  + rest/B2B RMSE {np.sqrt((err_m_p3**2).mean()):.4f}  MAE {err_m_p3.abs().mean():.4f}  bias {err_m_p3.mean():+.4f}")
    print()
    print("WIN PCT:")
    print(f"  Tier 1B:    {games['t1b_correct'].mean():.2%}  (n={len(games)})")
    print(f"  + rest/B2B: {games['p3_correct'].mean():.2%}  (n={len(games)})")
    delta_wp = (games['p3_correct'].mean() - games['t1b_correct'].mean()) * 100
    print(f"  delta:      {delta_wp:+.2f}pp")

    # Diagnostic: when does rest adjustment FLIP the prediction?
    flipped = games[games["t1b_correct"] != games["p3_correct"]]
    flipped_better = flipped[flipped["p3_correct"]]
    flipped_worse = flipped[~flipped["p3_correct"]]
    print()
    print(f"Predictions flipped by rest adj: {len(flipped)}")
    print(f"  Flipped CORRECT: {len(flipped_better)}")
    print(f"  Flipped WRONG:   {len(flipped_worse)}")

    games.to_csv(OUT_DIR / "per_game_predictions.csv", index=False)
    merged.to_csv(OUT_DIR / "per_team_game_predictions.csv", index=False)


if __name__ == "__main__":
    main()
