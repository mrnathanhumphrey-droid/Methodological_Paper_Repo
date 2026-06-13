"""Multi-season Tier 1B backtest on 24-25 + 25-26 RS for sharper coefficients.

Source: historical_box_scores.parquet (player-games) -> aggregate to team-games.

Build Tier 1B (rolling 10g team ortg/drtg/pace) per season, then validate.
Rolling window resets at season boundary (no cross-season bleed).

Validation: margin RMSE / MAE, team PTS MAE, win pct on each season + combined.

Foundation for testing ELO recency + garbage-time filter on the larger n.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from pathlib import Path

PQ = Path("data/parquet")
SEASONS = ["2024-25", "2025-26"]
OUT_DIR = Path("audit_runs/game_predictions_multiseason_tier1b")
OUT_DIR.mkdir(parents=True, exist_ok=True)

ROLLING = 10
HOME_COURT = 1.73 / 2.0  # will recompute per season


def aggregate_team_game(box: pd.DataFrame) -> pd.DataFrame:
    """Aggregate player-game box scores to team-game table."""
    agg = box.groupby(["season", "game_id", "team_abbr", "game_date", "is_home"]).agg(
        pts=("PTS", "sum"),
        fga=("FGA", "sum"),
        fta=("FTA", "sum"),
        oreb=("OREB", "sum"),
        tov=("TOV", "sum"),
        minutes=("minutes", "sum"),
    ).reset_index()
    # Possessions estimate
    agg["poss"] = agg["fga"] + 0.44 * agg["fta"] - agg["oreb"] + agg["tov"]
    agg["ortg"] = agg["pts"] / agg["poss"] * 100
    return agg


def attach_opponent(tg: pd.DataFrame) -> pd.DataFrame:
    """Each row gets its opponent's pts/poss for the same game."""
    opp = tg[["season", "game_id", "team_abbr", "pts", "poss"]].rename(
        columns={"team_abbr": "opp_team",
                 "pts": "opp_pts", "poss": "opp_poss"}
    )
    # Cross-merge within game_id: self joins to OTHER team in the same game
    joined = tg.merge(opp, on=["season", "game_id"], how="left")
    joined = joined[joined["team_abbr"] != joined["opp_team"]].copy()
    joined["drtg"] = joined["opp_pts"] / joined["opp_poss"] * 100
    return joined


def add_rolling_within_season(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["season", "team_abbr", "game_date"]).copy()
    grp = df.groupby(["season", "team_abbr"])
    df["roll_ortg"] = grp["ortg"].transform(
        lambda x: x.shift().rolling(window=ROLLING, min_periods=3).mean())
    df["roll_drtg"] = grp["drtg"].transform(
        lambda x: x.shift().rolling(window=ROLLING, min_periods=3).mean())
    df["roll_pace"] = grp["poss"].transform(
        lambda x: x.shift().rolling(window=ROLLING, min_periods=3).mean())
    return df


def attach_opp_rolling(df: pd.DataFrame) -> pd.DataFrame:
    """Each team-game row gets opponent's rolling stats (computed pre-game)."""
    opp_roll = df[["season", "game_id", "team_abbr", "roll_ortg", "roll_drtg", "roll_pace"]].rename(
        columns={"team_abbr": "opp_team",
                 "roll_ortg": "opp_roll_ortg",
                 "roll_drtg": "opp_roll_drtg",
                 "roll_pace": "opp_roll_pace"}
    )
    return df.merge(opp_roll, on=["season", "game_id", "opp_team"], how="left")


def home_court_advantage(df: pd.DataFrame, season: str) -> float:
    """Estimate per-season home advantage from actual margins."""
    s = df[df["season"] == season]
    home_pts = s[s["is_home"]].set_index("game_id")["pts"]
    away_pts = s[~s["is_home"]].set_index("game_id")["pts"]
    margins = home_pts - away_pts
    margins = margins.dropna()
    return float(margins.mean())


def main():
    print("Loading multi-season box scores ...")
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box = box[(box["season"].isin(SEASONS)) & (box["season_type"] == "Regular Season")].copy()
    box["game_date"] = pd.to_datetime(box["game_date"])
    print(f"  Box rows: {len(box)}")

    print("Aggregating to team-game ...")
    tg = aggregate_team_game(box)
    print(f"  Team-games: {len(tg)}")
    tg = attach_opponent(tg)
    print(f"  After opp join: {len(tg)}")
    tg = add_rolling_within_season(tg)
    tg = attach_opp_rolling(tg)

    # Per-season home court advantage
    hc_per_season = {}
    for s in SEASONS:
        hc_per_season[s] = home_court_advantage(tg, s)
    print()
    print("Per-season home court advantage:")
    for s, v in hc_per_season.items():
        print(f"  {s}: {v:+.3f}")
    hc_combined = float(np.mean(list(hc_per_season.values())))
    print(f"  combined: {hc_combined:+.3f}")
    tg["hc_half"] = tg["season"].map({s: v / 2 for s, v in hc_per_season.items()})

    # Filter to rows with valid rolling stats
    tg_v = tg.dropna(subset=["roll_ortg", "roll_drtg", "roll_pace",
                              "opp_roll_ortg", "opp_roll_drtg", "opp_roll_pace"]).copy()
    print(f"Team-games with rolling stats: {len(tg_v)}")

    # Tier 1B
    tg_v["game_pace"] = (tg_v["roll_pace"] + tg_v["opp_roll_pace"]) / 2
    tg_v["team_eff"] = (tg_v["roll_ortg"] + tg_v["opp_roll_drtg"]) / 2
    tg_v["team_pts_pred"] = tg_v["team_eff"] * tg_v["game_pace"] / 100 + np.where(
        tg_v["is_home"], tg_v["hc_half"], -tg_v["hc_half"]
    )

    # Per-team errors
    tg_v["err"] = tg_v["team_pts_pred"] - tg_v["pts"]

    # Per-season + combined
    print()
    print("=" * 75)
    print("Multi-season Tier 1B")
    print("=" * 75)
    for s in SEASONS + ["combined"]:
        sub = tg_v if s == "combined" else tg_v[tg_v["season"] == s]
        if len(sub) == 0:
            continue
        print(f"\n{s} (n={len(sub)} team-games):")
        print(f"  PTS MAE: {sub['err'].abs().mean():.4f}  RMSE: {np.sqrt((sub['err']**2).mean()):.4f}  bias: {sub['err'].mean():+.4f}")

    # Game-level margins/win pct per season + combined
    home = tg_v[tg_v["is_home"]].copy()
    away = tg_v[~tg_v["is_home"]].copy()
    games = home[["season", "game_id", "team_abbr", "team_pts_pred", "pts"]].rename(
        columns={"team_abbr": "home_team", "team_pts_pred": "home_pred", "pts": "home_actual"}
    ).merge(
        away[["game_id", "team_abbr", "team_pts_pred", "pts"]].rename(
            columns={"team_abbr": "away_team", "team_pts_pred": "away_pred", "pts": "away_actual"}),
        on="game_id", how="inner"
    )
    games["pred_margin"] = games["home_pred"] - games["away_pred"]
    games["actual_margin"] = games["home_actual"] - games["away_actual"]
    games["correct"] = (games["pred_margin"] > 0) == (games["actual_margin"] > 0)

    print()
    print("=" * 75)
    print("MARGIN / WIN PCT")
    print("=" * 75)
    for s in SEASONS + ["combined"]:
        sub = games if s == "combined" else games[games["season"] == s]
        if len(sub) == 0:
            continue
        err_m = sub["pred_margin"] - sub["actual_margin"]
        print(f"\n{s} (n={len(sub)} games):")
        print(f"  Margin RMSE: {np.sqrt((err_m**2).mean()):.4f}  MAE: {err_m.abs().mean():.4f}  bias: {err_m.mean():+.4f}")
        print(f"  Win pct:     {sub['correct'].mean():.2%}")

    tg_v.to_csv(OUT_DIR / "per_team_game_predictions.csv", index=False)
    games.to_csv(OUT_DIR / "per_game_predictions.csv", index=False)
    print(f"\nWrote: {OUT_DIR}/per_team_game_predictions.csv  ({len(tg_v)} rows)")
    print(f"Wrote: {OUT_DIR}/per_game_predictions.csv         ({len(games)} rows)")


if __name__ == "__main__":
    main()
