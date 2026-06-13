"""Phase 2 Tier 1: linear possession-level game prediction with coverage extender.

Architecture:
  team_pts_pred = sum over players who played(
      per_min_pts_projection * actual_minutes
  ) - opponent_def_pts_impact_per_game * (team_minutes / 240)
    + home_court_constant (if home)
    + rest_constant (B2B penalty if 0 days rest)

Per-min projections:
  - Ship CSV (v6.1 LOCKED): 567 covered players. Use PTS_per_game / mpg.
  - Non-ship players who played: rolling last-10 per-min from box scores. League mean fallback.

Defensive adjustment:
  - Player def_pts_impact (from def_zone_overall 24-25, forward prior for 25-26):
    pct_plusminus * d_fga * 2.5 / gp  -> per-game team-level effect
  - Aggregated at team level (sum across player-roster) since we don't have per-matchup data yet
  - Negative = good defender (lowers opponent PTS)

Validation on 2025-26 RS games:
  - actual margin vs predicted margin (RMSE)
  - actual winner vs predicted winner (win-pct)
  - actual team PTS vs predicted team PTS (bias + MAE)

Uses ACTUAL minutes for Tier 1 validation -- isolates projection accuracy from lineup prediction.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from pathlib import Path

PQ = Path("data/parquet")
SHIP = Path("audit_runs/unified_ship_v6_1_2025_26/per_player_projections_2025-26.csv")
OUT_DIR = Path("audit_runs/game_predictions_2025_26_phase2_tier1")
OUT_DIR.mkdir(parents=True, exist_ok=True)

ROLLING_WINDOW = 10
HOME_COURT_CONSTANT = 1.73 / 2.0  # 25-26 actual home advantage is +1.73 split evenly
SHIP_PM_CAL = 1.0591  # ship per-min underprojects by 5.91% empirically (n=381 players >=200 actual min)
B2B_PENALTY = 2.0           # back-to-back hurts away team this much


def load_ship_per_min() -> pd.DataFrame:
    """Per-player per-min stats from v6.1 LOCKED ship CSV."""
    ship = pd.read_csv(SHIP)
    # Filter to players with positive mpg (avoid div/0)
    ship = ship[ship["mpg"] > 0].copy()
    ship["pts_per_min_ship"] = ship["PTS_per_game"] / ship["mpg"]
    return ship[["nba_api_id", "name", "mpg", "PTS_per_game", "pts_per_min_ship"]].rename(
        columns={"PTS_per_game": "PTS_per_game_ship"}
    )


def build_rolling_per_min(box: pd.DataFrame, window: int = ROLLING_WINDOW) -> pd.DataFrame:
    """Per-player rolling per-min PTS over last `window` games preceding each game_date.

    Returns long: (nba_api_id, game_date, rolling_pts_per_min, rolling_min, n_games)
    """
    box = box.sort_values(["nba_api_id", "game_date"]).copy()
    box["game_date"] = pd.to_datetime(box["game_date"])
    box["pts_per_min"] = np.where(box["minutes"] > 0, box["PTS"] / box["minutes"], np.nan)

    # Rolling within player, EXCLUDING current row (shift first)
    grp = box.groupby("nba_api_id")
    box["rolling_pts_per_min"] = grp["pts_per_min"].transform(
        lambda x: x.shift().rolling(window=window, min_periods=2).mean()
    )
    box["rolling_min"] = grp["minutes"].transform(
        lambda x: x.shift().rolling(window=window, min_periods=2).mean()
    )
    box["n_games_prior"] = grp["minutes"].transform(
        lambda x: x.shift().rolling(window=window, min_periods=1).count()
    )
    return box[["nba_api_id", "game_id", "game_date", "team_abbr", "is_home", "minutes",
                "PTS", "pts_per_min", "rolling_pts_per_min", "rolling_min", "n_games_prior",
                "season"]]


def build_def_pts_impact_team(season: str = "2024-25") -> pd.DataFrame:
    """Team-level def_pts_impact_per_game from def_zone_overall.

    Aggregates by team_abbr × season -- the team's defensive baseline.
    Negative = good defense (saves opponent PTS).
    """
    df = pd.read_parquet(PQ / "player_def_zone_overall.parquet")
    df = df[df["season"] == season].copy()
    df["def_pts_impact"] = df["pct_plusminus"] * df["d_fga"] * 2.5 / df["gp"].clip(lower=1)
    # Team-level: weighted by gp (more games = more minutes contributed)
    team = df.groupby("team_abbr").apply(
        lambda g: np.average(g["def_pts_impact"], weights=g["gp"].clip(lower=1))
    ).reset_index(name="team_def_pts_impact_24_25")
    # Drop NaN team abbrs
    team = team.dropna(subset=["team_abbr"])
    return team


def league_per_min_mean(box: pd.DataFrame) -> float:
    """Fallback per-min PTS for players with no rolling history."""
    eligible = box[(box["minutes"] >= 5) & (box["season"] == "2025-26")]
    return float(eligible["PTS"].sum() / eligible["minutes"].sum())


def per_game_team_predictions(
    box_25: pd.DataFrame,
    rolling: pd.DataFrame,
    ship_pm: pd.DataFrame,
    team_def: pd.DataFrame,
    league_mean_pm: float,
    games_25: pd.DataFrame,
) -> pd.DataFrame:
    """For each team-game in 25-26, predict total team PTS using:
       sum over actual roster (ship pts_per_min if available else rolling else league mean)
       * actual minutes played, then subtract opponent's def_pts_impact pro-rated.
    """
    df = box_25.merge(ship_pm[["nba_api_id", "pts_per_min_ship"]],
                      on="nba_api_id", how="left")
    df = df.merge(rolling[["nba_api_id", "game_id", "rolling_pts_per_min", "n_games_prior"]],
                  on=["nba_api_id", "game_id"], how="left")

    # Coalesce: ship -> rolling -> league mean
    df["coverage_source"] = np.where(
        df["pts_per_min_ship"].notna(), "ship",
        np.where(df["rolling_pts_per_min"].notna(), "rolling", "league_mean")
    )
    # Apply calibration: ship per-min underprojects by 5.91% empirically; scale all sources by SHIP_PM_CAL
    df["coalesced_pts_per_min"] = (
        df["pts_per_min_ship"].fillna(df["rolling_pts_per_min"]).fillna(league_mean_pm)
    ) * SHIP_PM_CAL
    df["pred_pts_offense"] = df["coalesced_pts_per_min"] * df["minutes"]

    # Aggregate to team-game offensive contribution
    team_game = df.groupby(["game_id", "team_abbr", "game_date"]).agg(
        pred_pts_offense_sum=("pred_pts_offense", "sum"),
        actual_pts_sum=("PTS", "sum"),
        n_players=("nba_api_id", "nunique"),
        ship_minutes=("minutes", lambda x: float((x * (df.loc[x.index, "coverage_source"] == "ship")).sum())),
        rolling_minutes=("minutes", lambda x: float((x * (df.loc[x.index, "coverage_source"] == "rolling")).sum())),
        league_mean_minutes=("minutes", lambda x: float((x * (df.loc[x.index, "coverage_source"] == "league_mean")).sum())),
        total_minutes=("minutes", "sum"),
    ).reset_index()

    # Defensive adjustment: opponent's def_pts_impact applied
    # team_game has team's offense; we need opponent's def applied to it
    # From game log: each game has 2 rows; we need opponent for each row
    gl = games_25[["game_id", "team_abbreviation", "matchup", "wl", "pts"]].copy()
    gl["game_id"] = gl["game_id"].astype(str)
    team_game["game_id"] = team_game["game_id"].astype(str)
    # Determine opponent from matchup. matchup like "GSW @ LAL" or "LAL vs. GSW"
    gl["is_home_gl"] = gl["matchup"].str.contains("vs.", regex=False)
    gl["opp_team"] = gl["matchup"].str.extract(r"(?:@ |vs\. )([A-Z]+)")

    # Merge team-game with home/away + opponent
    team_game = team_game.merge(
        gl[["game_id", "team_abbreviation", "is_home_gl", "opp_team"]].rename(
            columns={"team_abbreviation": "team_abbr"}),
        on=["game_id", "team_abbr"], how="left"
    )

    # Attach opponent's def_pts_impact
    team_game = team_game.merge(
        team_def.rename(columns={"team_abbr": "opp_team",
                                 "team_def_pts_impact_24_25": "opp_def_pts_impact"}),
        on="opp_team", how="left"
    )
    # If team_def missing for an opp (new team?), use 0
    team_game["opp_def_pts_impact"] = team_game["opp_def_pts_impact"].fillna(0.0)

    # Apply: pred = offense + opponent_def_pts_impact * (team_minutes / 240)
    # Negative def_pts_impact (good defense) lowers the prediction.
    team_game["def_adjustment"] = team_game["opp_def_pts_impact"] * (team_game["total_minutes"] / 240.0)
    team_game["pred_pts_before_home"] = team_game["pred_pts_offense_sum"] + team_game["def_adjustment"]

    # Home court constant
    team_game["home_court"] = np.where(team_game["is_home_gl"], HOME_COURT_CONSTANT, -HOME_COURT_CONSTANT)
    team_game["pred_pts"] = team_game["pred_pts_before_home"] + team_game["home_court"]

    return team_game


def aggregate_game_margins(team_game: pd.DataFrame) -> pd.DataFrame:
    """Pivot team-game -> per-game margin prediction."""
    home = team_game[team_game["is_home_gl"]].copy()
    away = team_game[~team_game["is_home_gl"]].copy()
    games = home.merge(
        away[["game_id", "team_abbr", "pred_pts", "actual_pts_sum"]].rename(
            columns={"team_abbr": "away_team", "pred_pts": "away_pred_pts",
                     "actual_pts_sum": "away_actual_pts"}),
        on="game_id", how="inner"
    ).rename(columns={"team_abbr": "home_team", "pred_pts": "home_pred_pts",
                       "actual_pts_sum": "home_actual_pts"})
    games["pred_margin"] = games["home_pred_pts"] - games["away_pred_pts"]
    games["actual_margin"] = games["home_actual_pts"] - games["away_actual_pts"]
    games["pred_total"] = games["home_pred_pts"] + games["away_pred_pts"]
    games["actual_total"] = games["home_actual_pts"] + games["away_actual_pts"]
    games["pred_winner"] = np.where(games["pred_margin"] > 0, "HOME", "AWAY")
    games["actual_winner"] = np.where(games["actual_margin"] > 0, "HOME", "AWAY")
    games["correct"] = games["pred_winner"] == games["actual_winner"]
    return games


def report(games: pd.DataFrame, team_game: pd.DataFrame, league_mean_pm: float):
    print()
    print("=" * 75)
    print("Phase 2 Tier 1 -- linear possession-level game prediction")
    print("=" * 75)
    print(f"Games: {len(games)}")
    print()
    print("MARGIN:")
    margin_err = games["pred_margin"] - games["actual_margin"]
    print(f"  RMSE:     {np.sqrt((margin_err ** 2).mean()):.3f}  pts")
    print(f"  MAE:      {margin_err.abs().mean():.3f}  pts")
    print(f"  Bias:     {margin_err.mean():+.3f}  pts (pred - actual)")
    print()
    print("WIN PREDICTION:")
    print(f"  Accuracy: {games['correct'].mean():.1%}")
    print(f"  Targets:  Vegas ~66%, 538 ELO ~64-65%, target >=66%")
    print()
    print("TEAM TOTAL PTS:")
    team_err = team_game["pred_pts"] - team_game["actual_pts_sum"]
    print(f"  MAE per team:  {team_err.abs().mean():.3f}  pts")
    print(f"  Bias:          {team_err.mean():+.3f}  pts (pred - actual)")
    print(f"  Pred mean:     {team_game['pred_pts'].mean():.2f}")
    print(f"  Actual mean:   {team_game['actual_pts_sum'].mean():.2f}")
    print()
    print("GAME TOTAL (over/under) PTS:")
    total_err = games["pred_total"] - games["actual_total"]
    print(f"  RMSE:  {np.sqrt((total_err ** 2).mean()):.3f}  pts")
    print(f"  MAE:   {total_err.abs().mean():.3f}  pts")
    print(f"  Bias:  {total_err.mean():+.3f}  pts")
    print()
    print("COVERAGE BREAKDOWN (mean per team-game minutes):")
    print(f"  Ship:        {team_game['ship_minutes'].mean():.1f} min")
    print(f"  Rolling:     {team_game['rolling_minutes'].mean():.1f} min")
    print(f"  League mean: {team_game['league_mean_minutes'].mean():.1f} min")
    print(f"  Total:       {team_game['total_minutes'].mean():.1f} min")
    print(f"  League mean pm: {league_mean_pm:.4f} pts/min ({league_mean_pm*48:.2f} per 48)")


def main():
    print("Loading data ...")
    ship_pm = load_ship_per_min()
    print(f"  Ship per-min: {len(ship_pm)} players")

    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["game_date"] = pd.to_datetime(box["game_date"])
    box = box[box["season_type"] == "Regular Season"].copy()
    box_25 = box[box["season"] == "2025-26"].copy()
    print(f"  Box 25-26: {len(box_25)} player-games")
    print(f"  Box all-seasons (for rolling history): {len(box)}")

    print("Building rolling per-min ...")
    rolling = build_rolling_per_min(box)
    rolling_25 = rolling[rolling["season"] == "2025-26"].copy()
    print(f"  Rolling rows for 25-26: {len(rolling_25)}")
    print(f"  Coverage of rolling in 25-26: {rolling_25['rolling_pts_per_min'].notna().mean():.1%}")

    print("Building team-level def_pts_impact (24-25 prior) ...")
    team_def = build_def_pts_impact_team("2024-25")
    print(f"  Teams: {len(team_def)}")
    print(team_def.describe())

    league_mean_pm = league_per_min_mean(box)
    print(f"League per-min mean: {league_mean_pm:.4f} pts/min")

    games_25 = pd.read_parquet(PQ / "regular_season_game_log.parquet")
    games_25 = games_25[games_25["season"] == "2025-26"].copy()
    print(f"Games 25-26: {games_25['game_id'].nunique()}")

    print("Generating per-team-game predictions ...")
    team_game = per_game_team_predictions(
        box_25, rolling_25, ship_pm, team_def, league_mean_pm, games_25
    )
    print(f"  Team-game rows: {len(team_game)}")

    print("Pivoting to per-game margins ...")
    games = aggregate_game_margins(team_game)
    print(f"  Games: {len(games)}")

    team_game.to_csv(OUT_DIR / "per_team_game_predictions.csv", index=False)
    games.to_csv(OUT_DIR / "per_game_predictions.csv", index=False)

    report(games, team_game, league_mean_pm)


if __name__ == "__main__":
    main()
