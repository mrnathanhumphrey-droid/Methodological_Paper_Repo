"""Phase 2 Tier 1B: team-level efficiency model.

team_pts_pred = team_ortg_rolling × game_pace_pred + opponent_drtg_adj + home_court

Where:
  team_ortg_rolling = rolling 10-game team PTS / poss
  team_drtg_rolling = rolling 10-game opponent PTS / poss
  game_pace_pred    = mean of home and away team rolling pace
  pace = FGA + 0.44*FTA - OREB + TOV (per team-game)

For 25-26 prediction at game G: use rolling stats from games BEFORE G.

Compare vs Tier 1A (per-player aggregation, scripts/phase2_possession_aggregator_v1.py).
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from pathlib import Path

PQ = Path("data/parquet")
OUT_DIR = Path("audit_runs/game_predictions_2025_26_phase2_tier1b")
OUT_DIR.mkdir(parents=True, exist_ok=True)

ROLLING = 10
HOME_COURT = 1.73 / 2.0  # 25-26 actual half-advantage


def build_team_game_table() -> pd.DataFrame:
    """Build per-team-per-game table with pace + opponent context."""
    gl = pd.read_parquet(PQ / "regular_season_game_log.parquet")
    gl = gl[gl["season"] == "2025-26"].copy()
    gl["game_date"] = pd.to_datetime(gl["game_date"])
    gl["is_home"] = gl["matchup"].str.contains("vs.", regex=False)
    gl["opp_team"] = gl["matchup"].str.extract(r"(?:@ |vs\. )([A-Z]+)")
    # Possessions estimate
    gl["poss"] = gl["fga"] + 0.44 * gl["fta"] - gl["oreb"] + gl["tov"]
    gl["ortg"] = gl["pts"] / gl["poss"] * 100  # per 100 poss
    # Opponent's PTS = "drtg input" -- need to merge from opponent row
    # Join self with opp on game_id + team_abbr<>opp_team
    self_cols = ["game_id", "game_date", "team_abbreviation", "is_home", "opp_team",
                 "pts", "poss", "ortg"]
    opp = gl[["game_id", "team_abbreviation", "pts", "poss"]].rename(
        columns={"team_abbreviation": "opp_team",
                 "pts": "opp_pts", "poss": "opp_poss"}
    )
    df = gl[self_cols].merge(opp, on=["game_id", "opp_team"], how="left")
    df["drtg"] = df["opp_pts"] / df["opp_poss"] * 100  # team's defensive rating from this game
    return df.sort_values(["team_abbreviation", "game_date"]).reset_index(drop=True)


def add_rolling(df: pd.DataFrame) -> pd.DataFrame:
    """Add rolling pre-game-date stats (excluding the current game)."""
    df = df.sort_values(["team_abbreviation", "game_date"]).copy()
    grp = df.groupby("team_abbreviation")
    df["roll_ortg"] = grp["ortg"].transform(
        lambda x: x.shift().rolling(window=ROLLING, min_periods=3).mean())
    df["roll_drtg"] = grp["drtg"].transform(
        lambda x: x.shift().rolling(window=ROLLING, min_periods=3).mean())
    df["roll_pace"] = grp["poss"].transform(
        lambda x: x.shift().rolling(window=ROLLING, min_periods=3).mean())
    return df


def main():
    df = build_team_game_table()
    print(f"Team-games: {len(df)}")
    df = add_rolling(df)

    # For each team-game, also need OPPONENT's rolling stats
    opp_roll = df[["game_id", "team_abbreviation", "roll_ortg", "roll_drtg", "roll_pace"]].rename(
        columns={"team_abbreviation": "opp_team",
                 "roll_ortg": "opp_roll_ortg",
                 "roll_drtg": "opp_roll_drtg",
                 "roll_pace": "opp_roll_pace"}
    )
    df = df.merge(opp_roll, on=["game_id", "opp_team"], how="left")

    # Drop early games where rolling not yet available
    df_v = df.dropna(subset=["roll_ortg", "roll_drtg", "roll_pace",
                              "opp_roll_ortg", "opp_roll_drtg", "opp_roll_pace"]).copy()
    print(f"Team-games with rolling stats available: {len(df_v)}")

    # Tier 1B formula:
    # game_pace = mean(team_pace, opp_pace)
    # team_pts_pred = team_ortg vs opp_drtg combined × game_pace / 100
    # Specifically: take harmonic-or-weighted mean of team_ortg and opp_drtg
    # Standard: (team_ortg + opp_drtg) / 2 -- weights each equally
    df_v["game_pace"] = (df_v["roll_pace"] + df_v["opp_roll_pace"]) / 2
    df_v["team_eff_pred"] = (df_v["roll_ortg"] + df_v["opp_roll_drtg"]) / 2
    df_v["team_pts_pred_raw"] = df_v["team_eff_pred"] * df_v["game_pace"] / 100
    # Home court split
    df_v["home_court_adj"] = np.where(df_v["is_home"], HOME_COURT, -HOME_COURT)
    df_v["team_pts_pred"] = df_v["team_pts_pred_raw"] + df_v["home_court_adj"]

    # Stats
    err = df_v["team_pts_pred"] - df_v["pts"]
    print()
    print("=" * 70)
    print("Phase 2 Tier 1B: team-level efficiency (rolling 10g)")
    print("=" * 70)
    print(f"Team-games evaluated: {len(df_v)}")
    print(f"  Team PTS MAE:    {err.abs().mean():.3f}")
    print(f"  Team PTS RMSE:   {np.sqrt((err**2).mean()):.3f}")
    print(f"  Team PTS bias:   {err.mean():+.3f}")
    print(f"  Pred mean:       {df_v['team_pts_pred'].mean():.2f}")
    print(f"  Actual mean:     {df_v['pts'].mean():.2f}")

    # Pivot to game-level
    home = df_v[df_v["is_home"]].copy()
    away = df_v[~df_v["is_home"]].copy()
    games = home[["game_id", "team_abbreviation", "team_pts_pred", "pts"]].rename(
        columns={"team_abbreviation": "home_team", "team_pts_pred": "home_pred",
                 "pts": "home_actual"}
    ).merge(
        away[["game_id", "team_abbreviation", "team_pts_pred", "pts"]].rename(
            columns={"team_abbreviation": "away_team", "team_pts_pred": "away_pred",
                     "pts": "away_actual"}),
        on="game_id", how="inner"
    )
    games["pred_margin"] = games["home_pred"] - games["away_pred"]
    games["actual_margin"] = games["home_actual"] - games["away_actual"]
    games["correct"] = (games["pred_margin"] > 0) == (games["actual_margin"] > 0)

    print()
    print("MARGIN:")
    err_m = games["pred_margin"] - games["actual_margin"]
    print(f"  RMSE:     {np.sqrt((err_m**2).mean()):.3f}  pts")
    print(f"  MAE:      {err_m.abs().mean():.3f}  pts")
    print(f"  Bias:     {err_m.mean():+.3f}  pts")
    print()
    print("WIN PREDICTION:")
    print(f"  Accuracy: {games['correct'].mean():.1%}  (n={len(games)})")
    print(f"  Targets:  Vegas ~66%, 538 ELO ~64-65%")
    print()
    games["pred_total"] = games["home_pred"] + games["away_pred"]
    games["actual_total"] = games["home_actual"] + games["away_actual"]
    err_t = games["pred_total"] - games["actual_total"]
    print("GAME TOTAL:")
    print(f"  RMSE:  {np.sqrt((err_t**2).mean()):.3f}  pts")
    print(f"  MAE:   {err_t.abs().mean():.3f}  pts")
    print(f"  Bias:  {err_t.mean():+.3f}  pts")

    games.to_csv(OUT_DIR / "per_game_predictions.csv", index=False)
    df_v.to_csv(OUT_DIR / "per_team_game_predictions.csv", index=False)


if __name__ == "__main__":
    main()
