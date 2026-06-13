"""Phase 3 step 1: layer per-player def_pts_impact onto Tier 1B as lineup-specific adjustment.

Tier 1B baseline uses opponent's rolling team drtg (10-game rolling, lags lineup composition).
Lineup adjustment captures TODAY's lineup vs. opponent's rolling baseline:
  δ_lineup = lineup_def_pts_impact_today - opp_rolling_lineup_def_pts_impact_baseline
  team_pts_pred_adj = team_pts_pred_tier1b + δ_lineup

For 25-26 prediction, use 24-25 def_pts_impact_per_min (player skill prior).
For each team-game in 25-26: actual lineup × minutes × 24-25 per-min def impact = today's lineup signal.

Validation on 25-26 RS.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from pathlib import Path

PQ = Path("data/parquet")
TIER1B = Path("audit_runs/game_predictions_2025_26_phase2_tier1b/per_team_game_predictions.csv")
OUT_DIR = Path("audit_runs/game_predictions_2025_26_phase3_lineup_def")
OUT_DIR.mkdir(parents=True, exist_ok=True)

ROLLING_BASELINE = 10
HOME_COURT = 1.73 / 2.0


def build_player_def_per_min(prior_season: str = "2024-25") -> pd.DataFrame:
    """Per-player def_pts_impact_per_min from prior season."""
    d = pd.read_parquet(PQ / "player_def_zone_overall.parquet")
    d = d[(d["season"] == prior_season) & (d["season_type"] == "Regular Season")].copy()
    d["def_pts_impact_pg"] = d["pct_plusminus"] * d["d_fga"] * 2.5 / d["gp"].clip(lower=1)
    # Approximate mpg from d_fga and league avg shot rate; or use a fixed denominator
    # def_pts_impact_per_min: amortize per-game over MPG (need MPG from elsewhere)
    # Simpler: use def_pts_impact_pg directly, normalize by 24 mpg (league avg starter)
    # When a player plays X minutes today, contribution = def_pts_impact_pg * (X / mpg_baseline_24)
    # We need actual mpg. Use a join from historical_box_scores 24-25.
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box = box[(box["season"] == prior_season) & (box["season_type"] == "Regular Season")]
    mpg = box.groupby("nba_api_id").agg(
        mpg_prior=("minutes", "mean"),
        gp_prior=("game_id", "count"),
    ).reset_index()
    d = d.merge(mpg, on="nba_api_id", how="left")
    # Avoid divide-by-zero, only use players with >=20 prior games
    d = d[d["gp_prior"].fillna(0) >= 20].copy()
    d["def_pts_impact_per_min"] = d["def_pts_impact_pg"] / d["mpg_prior"].clip(lower=1)
    return d[["nba_api_id", "player_name", "team_abbr", "def_pts_impact_pg",
              "mpg_prior", "def_pts_impact_per_min"]].rename(
        columns={"player_name": "name"}
    )


def compute_lineup_def_per_game(prior: pd.DataFrame) -> pd.DataFrame:
    """For each 25-26 team-game, compute lineup_def_pts_impact = sum over actual roster.

    For players without prior-season def_pts_impact, use league mean 0.0.
    """
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box = box[(box["season"] == "2025-26") & (box["season_type"] == "Regular Season")].copy()
    box["game_date"] = pd.to_datetime(box["game_date"])

    box = box.merge(prior[["nba_api_id", "def_pts_impact_per_min"]], on="nba_api_id", how="left")
    box["player_def_impact_today"] = box["def_pts_impact_per_min"].fillna(0.0) * box["minutes"]

    team_game = box.groupby(["game_id", "team_abbr", "game_date"]).agg(
        lineup_def_pts_impact=("player_def_impact_today", "sum"),
        lineup_def_coverage_min=("def_pts_impact_per_min",
                                  lambda x: float((box.loc[x.index, "minutes"] * x.notna()).sum())),
        lineup_total_min=("minutes", "sum"),
    ).reset_index()
    team_game["lineup_def_coverage_pct"] = (
        team_game["lineup_def_coverage_min"] / team_game["lineup_total_min"].clip(lower=1)
    )
    return team_game


def add_rolling_baseline(lineup: pd.DataFrame) -> pd.DataFrame:
    """For each team's 25-26 games (in date order), compute pre-game rolling baseline of
    lineup_def_pts_impact. This captures opponent's typical lineup defense.
    """
    lineup = lineup.sort_values(["team_abbr", "game_date"]).copy()
    grp = lineup.groupby("team_abbr")
    lineup["rolling_lineup_def_baseline"] = grp["lineup_def_pts_impact"].transform(
        lambda x: x.shift().rolling(window=ROLLING_BASELINE, min_periods=3).mean())
    return lineup


def main():
    print("Loading 24-25 def_pts_impact (player prior) ...")
    prior = build_player_def_per_min("2024-25")
    print(f"  Player priors: {len(prior)} players")
    print(f"  def_pts_impact_per_min range: {prior['def_pts_impact_per_min'].min():.4f} to {prior['def_pts_impact_per_min'].max():.4f}")
    print(f"  median: {prior['def_pts_impact_per_min'].median():.4f}")

    print()
    print("Computing per-team-game lineup def impact (25-26 actual roster + minutes) ...")
    lineup = compute_lineup_def_per_game(prior)
    lineup["game_id"] = lineup["game_id"].astype(str)
    print(f"  Team-games: {len(lineup)}")
    print(f"  Mean lineup_def_pts_impact: {lineup['lineup_def_pts_impact'].mean():+.3f}")
    print(f"  Mean lineup coverage (prior data): {lineup['lineup_def_coverage_pct'].mean():.1%}")
    print(f"  Std lineup_def_pts_impact: {lineup['lineup_def_pts_impact'].std():.3f}")

    print()
    print("Adding rolling baseline ...")
    lineup = add_rolling_baseline(lineup)
    lineup["delta_lineup"] = lineup["lineup_def_pts_impact"] - lineup["rolling_lineup_def_baseline"]
    print(f"  Mean delta_lineup: {lineup['delta_lineup'].mean():+.3f}")
    print(f"  Std delta_lineup: {lineup['delta_lineup'].std():.3f}")

    print()
    print("Loading Tier 1B per-team-game predictions ...")
    t1b = pd.read_csv(TIER1B)
    # game_id normalize: t1b uses int (22500130), box uses zero-padded str (0022500130)
    t1b["game_id"] = t1b["game_id"].astype(int).astype(str).str.zfill(10)
    lineup["game_id"] = lineup["game_id"].astype(str).str.zfill(10)
    t1b["game_date"] = pd.to_datetime(t1b["game_date"])
    print(f"  Tier 1B rows: {len(t1b)}")

    # For each team-game in t1b, attach OPP's lineup_def_pts_impact + rolling baseline
    opp_lineup = lineup[["game_id", "team_abbr", "lineup_def_pts_impact", "rolling_lineup_def_baseline", "delta_lineup"]].rename(
        columns={"team_abbr": "opp_team",
                 "lineup_def_pts_impact": "opp_lineup_def",
                 "rolling_lineup_def_baseline": "opp_lineup_def_baseline",
                 "delta_lineup": "opp_delta_lineup"}
    )
    merged = t1b.merge(opp_lineup, on=["game_id", "opp_team"], how="left")
    # If baseline NaN (early-season opp), use 0 for delta
    merged["opp_delta_lineup"] = merged["opp_delta_lineup"].fillna(0.0)

    # Adjusted prediction: team_pts_pred_adj = team_pts_pred + opp_delta_lineup
    # POSITIVE opp_delta = opp lineup defending WORSE than baseline -> we score MORE
    # NEGATIVE opp_delta = opp lineup defending BETTER than baseline -> we score LESS
    merged["pred_pts_phase3"] = merged["team_pts_pred"] + merged["opp_delta_lineup"]

    # Per-team error
    err_t1b = merged["team_pts_pred"] - merged["pts"]
    err_p3 = merged["pred_pts_phase3"] - merged["pts"]
    print()
    print("=" * 75)
    print("Phase 3 step 1: Tier 1B + lineup-aware defensive adjustment")
    print("=" * 75)
    print(f"Team-games: {len(merged)}")
    print()
    print("Per-team PTS error:")
    print(f"  Tier 1B    -> MAE {err_t1b.abs().mean():.3f}, RMSE {np.sqrt((err_t1b**2).mean()):.3f}, bias {err_t1b.mean():+.3f}")
    print(f"  + lineup   -> MAE {err_p3.abs().mean():.3f}, RMSE {np.sqrt((err_p3**2).mean()):.3f}, bias {err_p3.mean():+.3f}")
    print(f"  delta MAE: {(err_p3.abs().mean() - err_t1b.abs().mean()) / err_t1b.abs().mean() * 100:+.2f}%")

    # Pivot to game-level for margin and win pct
    home_t1b = merged[merged["is_home"]].copy()
    away_t1b = merged[~merged["is_home"]].copy()
    games = home_t1b[["game_id", "team_abbreviation", "team_pts_pred", "pred_pts_phase3", "pts"]].rename(
        columns={"team_abbreviation": "home_team",
                 "team_pts_pred": "home_t1b", "pred_pts_phase3": "home_p3", "pts": "home_actual"}
    ).merge(
        away_t1b[["game_id", "team_abbreviation", "team_pts_pred", "pred_pts_phase3", "pts"]].rename(
            columns={"team_abbreviation": "away_team",
                     "team_pts_pred": "away_t1b", "pred_pts_phase3": "away_p3", "pts": "away_actual"}),
        on="game_id", how="inner"
    )
    games["t1b_margin"] = games["home_t1b"] - games["away_t1b"]
    games["p3_margin"] = games["home_p3"] - games["away_p3"]
    games["actual_margin"] = games["home_actual"] - games["away_actual"]
    games["t1b_correct"] = (games["t1b_margin"] > 0) == (games["actual_margin"] > 0)
    games["p3_correct"] = (games["p3_margin"] > 0) == (games["actual_margin"] > 0)

    print()
    print("MARGIN:")
    print(f"  Tier 1B  RMSE {np.sqrt(((games['t1b_margin'] - games['actual_margin'])**2).mean()):.3f}  "
          f"MAE {(games['t1b_margin'] - games['actual_margin']).abs().mean():.3f}  "
          f"bias {(games['t1b_margin'] - games['actual_margin']).mean():+.3f}")
    print(f"  + lineup RMSE {np.sqrt(((games['p3_margin'] - games['actual_margin'])**2).mean()):.3f}  "
          f"MAE {(games['p3_margin'] - games['actual_margin']).abs().mean():.3f}  "
          f"bias {(games['p3_margin'] - games['actual_margin']).mean():+.3f}")

    print()
    print("WIN PCT:")
    print(f"  Tier 1B:  {games['t1b_correct'].mean():.1%}  (n={len(games)})")
    print(f"  + lineup: {games['p3_correct'].mean():.1%}  (n={len(games)})")
    print(f"  Vegas: ~66%, ELO ~64-65%")

    games.to_csv(OUT_DIR / "per_game_predictions.csv", index=False)
    merged.to_csv(OUT_DIR / "per_team_game_predictions.csv", index=False)


if __name__ == "__main__":
    main()
