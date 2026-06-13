"""Team-level aggregation of daily RS player projections.

Reads audit_runs/rs_projections_{date}/rs_projections.parquet (produced by
produce_regular_season_projections.py), aggregates per (game_id, team_abbr)
into team box totals + per-game totals/spreads.

Cross-check vs game_predictions team-pts model where overlap exists.

Usage:
    python scripts/produce_team_aggregations.py YYYY-MM-DD
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path("D:/NBA Projections")
GAME_PRED = ROOT / "audit_runs/game_predictions_2025_26_phase3_rest_b2b/per_team_game_predictions.csv"

RAW_STATS = ["PTS", "REB", "AST", "BLK", "STL", "TOV", "FG3M"]
MA_PAIR_STATS = ["FGM", "FGA", "FTM", "FTA", "FG3A"]
ALL_BOX_STATS = RAW_STATS + MA_PAIR_STATS


def main():
    p = argparse.ArgumentParser()
    p.add_argument("target_date", help="YYYY-MM-DD")
    args = p.parse_args()
    target = pd.to_datetime(args.target_date).normalize()

    in_dir = ROOT / f"audit_runs/rs_projections_{target.date().isoformat()}"
    in_path = in_dir / "rs_projections.parquet"
    if not in_path.exists():
        print(f"  ERROR: player projections not found at {in_path}")
        print(f"  Run produce_regular_season_projections.py {target.date()} first.")
        sys.exit(1)

    print(f"=== Team aggregation for {target.date()} ===")
    proj = pd.read_parquet(in_path)
    print(f"  player-rows loaded: {len(proj):,}")

    wide = proj.pivot_table(
        index=["game_id", "team_abbr", "opp_team_abbr", "is_home", "nba_api_id", "name"],
        columns="stat", values="projected_mean",
        aggfunc="first",
    ).reset_index()

    team_agg = (
        wide.groupby(["game_id", "team_abbr", "opp_team_abbr", "is_home"], observed=True)[ALL_BOX_STATS]
            .sum()
            .reset_index()
    )
    team_agg = team_agg.rename(columns={s: f"team_{s}" for s in ALL_BOX_STATS})
    print(f"  team-game rows: {len(team_agg):,}")

    team_agg["team_FG_PCT"] = np.where(team_agg["team_FGA"] > 0, team_agg["team_FGM"] / team_agg["team_FGA"], np.nan)
    team_agg["team_FT_PCT"] = np.where(team_agg["team_FTA"] > 0, team_agg["team_FTM"] / team_agg["team_FTA"], np.nan)
    team_agg["team_FG3_PCT"] = np.where(team_agg["team_FG3A"] > 0, team_agg["team_FG3M"] / team_agg["team_FG3A"], np.nan)
    team_agg["game_date"] = target.date().isoformat()

    team_agg.to_parquet(in_dir / "team_aggregations.parquet", index=False)
    print(f"  Wrote {in_dir / 'team_aggregations.parquet'}")

    stat_cols = [f"team_{s}" for s in ALL_BOX_STATS] + ["team_FG_PCT", "team_FT_PCT", "team_FG3_PCT"]

    home = team_agg[team_agg["is_home"] == True].copy()
    home = home.rename(columns={"team_abbr": "home_team", "opp_team_abbr": "away_team"})
    home = home.rename(columns={c: c.replace("team_", "home_") for c in stat_cols})
    home = home.drop(columns=["is_home"])

    away = team_agg[team_agg["is_home"] == False].copy()
    away = away.rename(columns={"team_abbr": "away_team_x"})
    away = away.rename(columns={c: c.replace("team_", "away_") for c in stat_cols})
    away_cols_to_keep = ["game_id", "away_team_x"] + [c.replace("team_", "away_") for c in stat_cols]
    away = away[away_cols_to_keep].rename(columns={"away_team_x": "away_team"})

    games = home.merge(away, on=["game_id", "away_team"], how="inner")
    games["projected_total"] = games["home_PTS"] + games["away_PTS"]
    games["projected_spread"] = games["home_PTS"] - games["away_PTS"]

    front_cols = ["game_id", "game_date", "home_team", "away_team",
                  "projected_total", "projected_spread",
                  "home_PTS", "away_PTS"]
    other_cols = [c for c in games.columns if c not in front_cols]
    games = games[front_cols + other_cols]

    games.to_parquet(in_dir / "game_aggregations.parquet", index=False)
    print(f"  Wrote {in_dir / 'game_aggregations.parquet'}")
    print(f"  game-level rows: {len(games):,}")

    print("\n=== Cross-check vs game_predictions team-pts model ===")
    if GAME_PRED.exists():
        gp = pd.read_csv(GAME_PRED)
        gp["game_id"] = gp["game_id"].astype(str).str.zfill(10)
        team_agg_for_check = team_agg.copy()
        team_agg_for_check["game_id"] = team_agg_for_check["game_id"].astype(str).str.zfill(10)
        merged = team_agg_for_check.merge(
            gp[["game_id", "team_abbreviation", "team_pts_pred", "pts"]],
            left_on=["game_id", "team_abbr"],
            right_on=["game_id", "team_abbreviation"], how="inner"
        )
        if len(merged) == 0:
            print("  No overlapping team-game rows with game_predictions on this date.")
        else:
            merged["delta_player_sum_vs_gp"] = merged["team_PTS"] - merged["team_pts_pred"]
            merged["err_player_sum_vs_actual"] = merged["team_PTS"] - merged["pts"]
            merged["err_gp_vs_actual"] = merged["team_pts_pred"] - merged["pts"]
            print(f"  rows checked: {len(merged):,}")
            print(f"  PLAYER-SUM team_PTS:         "
                  f"MAE vs actual {merged['err_player_sum_vs_actual'].abs().mean():.3f}, "
                  f"RMSE {np.sqrt((merged['err_player_sum_vs_actual']**2).mean()):.3f}")
            print(f"  GAME_PRED team_pts_pred:     "
                  f"MAE vs actual {merged['err_gp_vs_actual'].abs().mean():.3f}, "
                  f"RMSE {np.sqrt((merged['err_gp_vs_actual']**2).mean()):.3f}")
            print(f"  Δ (player_sum - game_pred):  "
                  f"mean {merged['delta_player_sum_vs_gp'].mean():+.3f}, "
                  f"abs mean {merged['delta_player_sum_vs_gp'].abs().mean():.3f}")
    else:
        print(f"  game_predictions file not found at {GAME_PRED}; skipping cross-check.")


if __name__ == "__main__":
    main()
