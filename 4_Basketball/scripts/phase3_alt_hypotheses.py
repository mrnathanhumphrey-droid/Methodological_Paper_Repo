"""Test alternative hypotheses for residual structure after roster-lag falsification.

Hypothesis A: SCHEDULING artifacts (testable from box scores alone)
  - B2B (1 day rest): does miss rate concentrate here?
  - B2B2B (3 games in 4 nights): same question
  - Long road trips (5+ road games in last 7)
  - Days-into-season (early/late season)
  - Rest-mismatch between teams

Hypothesis B: STOCHASTIC VARIANCE (3PT shot luck)
  - For each game, compute team 3PT% deviation from rolling mean
  - Are coin-flip-blowout misses concentrated in high-3PT-variance games?

Hypothesis C: SEASON-LEVEL PARITY (why does 23-24 specifically fail?)
  - Compute season parity: std dev of team win pct
  - Trade-deadline volume (rough proxy from injury feed)
  - League scoring variance

For each, compute coin-flip miss rate stratified by the feature.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from pathlib import Path

PRED = Path("audit_runs/walkforward_allseasons/per_game_predictions.csv")
PQ = Path("data/parquet")


def load_team_dates():
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box = box[box["season_type"] == "Regular Season"].copy()
    box["game_date"] = pd.to_datetime(box["game_date"])
    box = box[box["season"].isin(["2018-19", "2019-20", "2020-21", "2021-22",
                                    "2022-23", "2023-24", "2024-25", "2025-26"])]
    team_games = box[["season", "game_id", "team_abbr", "game_date", "is_home"]].drop_duplicates()
    team_games = team_games.sort_values(["team_abbr", "game_date"])
    team_games["prev_date"] = team_games.groupby("team_abbr")["game_date"].shift(1)
    team_games["days_rest"] = (team_games["game_date"] - team_games["prev_date"]).dt.days
    team_games["is_b2b"] = (team_games["days_rest"] == 1).astype(int)

    # B2B2B = 3 games in 4 nights = days_rest=1 AND prev game also was b2b
    team_games["prev_b2b"] = team_games.groupby("team_abbr")["is_b2b"].shift(1)
    team_games["is_b2b2b"] = ((team_games["is_b2b"] == 1) & (team_games["prev_b2b"] == 1)).astype(int)

    # Road trip: count of away games in last 7 team-games
    team_games["is_away"] = (~team_games["is_home"]).astype(int)
    team_games["road_in_last7"] = team_games.groupby("team_abbr")["is_away"].transform(
        lambda x: x.shift().rolling(7, min_periods=1).sum())

    # Days-into-season
    team_games["season_start"] = team_games.groupby("season")["game_date"].transform("min")
    team_games["days_into_season"] = (team_games["game_date"] - team_games["season_start"]).dt.days

    return team_games[["season", "game_id", "team_abbr", "is_home", "days_rest",
                        "is_b2b", "is_b2b2b", "road_in_last7", "days_into_season"]]


def main():
    g = pd.read_csv(PRED)
    g["abs_pred_margin"] = g["pred_margin"].abs()
    g["abs_actual_margin"] = g["actual_margin"].abs()
    g["is_coin_flip"] = g["abs_pred_margin"] <= 2
    g["is_big_miss"] = g["is_coin_flip"] & (g["abs_actual_margin"] > 10) & (~g["correct"])
    g["game_id"] = g["game_id"].astype(str).str.zfill(10)
    print(f"Total games: {len(g)}")
    print(f"Coin flips: {g['is_coin_flip'].sum()}")
    print(f"Big-miss coin flips: {g['is_big_miss'].sum()} ({g['is_big_miss'].sum()/g['is_coin_flip'].sum():.2%} of coin flips)")

    print()
    print("Loading team game features (rest, b2b, road, days-into-season) ...")
    tf = load_team_dates()
    tf["game_id"] = tf["game_id"].astype(str).str.zfill(10)
    home_feat = tf[tf["is_home"]].rename(
        columns={"days_rest": "h_rest", "is_b2b": "h_b2b", "is_b2b2b": "h_b2b2b",
                 "road_in_last7": "h_road7", "team_abbr": "home_team",
                 "days_into_season": "h_dis"}).drop(columns=["is_home"])
    away_feat = tf[~tf["is_home"]].rename(
        columns={"days_rest": "a_rest", "is_b2b": "a_b2b", "is_b2b2b": "a_b2b2b",
                 "road_in_last7": "a_road7", "team_abbr": "away_team",
                 "days_into_season": "a_dis"}).drop(columns=["is_home"])
    g = g.merge(home_feat[["game_id", "h_rest", "h_b2b", "h_b2b2b", "h_road7", "h_dis"]],
                on="game_id", how="left")
    g = g.merge(away_feat[["game_id", "a_rest", "a_b2b", "a_b2b2b", "a_road7"]],
                on="game_id", how="left")
    g["rest_diff"] = g["h_rest"] - g["a_rest"]
    g["b2b_either"] = ((g["h_b2b"] == 1) | (g["a_b2b"] == 1)).astype(int)
    g["b2b2b_either"] = ((g["h_b2b2b"] == 1) | (g["a_b2b2b"] == 1)).astype(int)

    # ==================================================================
    # H-A: SCHEDULING artifacts
    # ==================================================================
    print()
    print("=" * 78)
    print("H-A: Scheduling artifacts -- does miss rate concentrate?")
    print("=" * 78)

    # B2B effect on coin-flip miss rate
    print("\n  Coin-flip win pct by B2B status:")
    for label, mask in [("neither team B2B", g["b2b_either"] == 0),
                         ("at least one B2B", g["b2b_either"] == 1)]:
        sub = g[g["is_coin_flip"] & mask]
        print(f"    {label}: n={len(sub):>5} win_pct={sub['correct'].mean():.4f}")

    print("\n  Coin-flip big-miss rate by B2B status:")
    for label, mask in [("neither B2B", g["b2b_either"] == 0),
                         ("at least one B2B", g["b2b_either"] == 1)]:
        sub = g[mask]
        flips = sub[sub["is_coin_flip"]]
        bm = flips["is_big_miss"]
        print(f"    {label}: coin flips n={len(flips):>5} big-miss rate {bm.mean():.4f}")

    # B2B2B effect
    print("\n  Coin-flip win pct by B2B2B status:")
    for label, mask in [("no B2B2B", g["b2b2b_either"] == 0),
                         ("either team B2B2B", g["b2b2b_either"] == 1)]:
        sub = g[g["is_coin_flip"] & mask]
        print(f"    {label}: n={len(sub):>5} win_pct={sub['correct'].mean():.4f}")

    # Road trip length
    print("\n  Coin-flip win pct by away team's recent road trip length:")
    g["a_road_bin"] = pd.cut(g["a_road7"], bins=[-0.1, 1.5, 3.5, 5.5, 7.5],
                              labels=["<=1", "2-3", "4-5", "6-7"])
    for b, sub in g[g["is_coin_flip"]].groupby("a_road_bin", observed=True):
        print(f"    away road in last 7 = {b}: n={len(sub):>5} win_pct={sub['correct'].mean():.4f}")

    # Days-into-season
    print("\n  Coin-flip win pct by days-into-season:")
    g["dis_bin"] = pd.cut(g["h_dis"], bins=[0, 30, 60, 90, 120, 200],
                           labels=["<30d", "30-60", "60-90", "90-120", "120+"])
    for b, sub in g[g["is_coin_flip"]].groupby("dis_bin", observed=True):
        print(f"    {b}: n={len(sub):>5} win_pct={sub['correct'].mean():.4f}")

    # Rest mismatch
    print("\n  Coin-flip win pct by rest_diff (home rest minus away rest):")
    g["rd_bin"] = pd.cut(g["rest_diff"], bins=[-5.5, -1.5, -0.5, 0.5, 1.5, 5.5],
                          labels=["home_-2+", "home_-1", "even", "home_+1", "home_+2+"])
    for b, sub in g[g["is_coin_flip"]].groupby("rd_bin", observed=True):
        print(f"    {b}: n={len(sub):>4} win_pct={sub['correct'].mean():.4f}")

    # ==================================================================
    # H-B: 3PT VARIANCE (need box scores for 3pt rate)
    # ==================================================================
    print()
    print("=" * 78)
    print("H-B: 3PT variance -- do high-3PT-variance games concentrate misses?")
    print("=" * 78)
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box = box[box["season_type"] == "Regular Season"].copy()
    box["game_date"] = pd.to_datetime(box["game_date"])
    box = box[box["season"].isin(["2018-19", "2019-20", "2020-21", "2021-22",
                                    "2022-23", "2023-24", "2024-25", "2025-26"])]
    team_g = box.groupby(["season", "game_id", "team_abbr", "game_date"]).agg(
        fg3m=("FG3M", "sum"), fg3a=("FG3A", "sum")).reset_index()
    team_g["fg3_pct"] = team_g["fg3m"] / team_g["fg3a"].clip(lower=1)
    # Per-team rolling 10g mean of fg3_pct -- pre-game baseline
    team_g = team_g.sort_values(["team_abbr", "game_date"])
    team_g["roll_fg3_pct"] = team_g.groupby("team_abbr")["fg3_pct"].transform(
        lambda x: x.shift().rolling(10, min_periods=3).mean())
    team_g["fg3_deviation"] = team_g["fg3_pct"] - team_g["roll_fg3_pct"]
    team_g["fg3_abs_dev"] = team_g["fg3_deviation"].abs()
    team_g["game_id"] = team_g["game_id"].astype(str).str.zfill(10)

    # Per-game: max abs deviation between two teams
    max_dev = team_g.groupby("game_id")["fg3_abs_dev"].max().reset_index(name="max_fg3_dev")
    g = g.merge(max_dev, on="game_id", how="left")

    print("\n  Coin-flip win pct by max 3PT deviation in the game:")
    g["fg3_bin"] = pd.cut(g["max_fg3_dev"], bins=[0, 0.05, 0.10, 0.15, 0.20, 1.0],
                           labels=["<5%", "5-10%", "10-15%", "15-20%", "20%+"])
    for b, sub in g[g["is_coin_flip"]].groupby("fg3_bin", observed=True):
        print(f"    max 3PT_pct deviation {b}: n={len(sub):>4} win_pct={sub['correct'].mean():.4f}")

    print("\n  Coin-flip big-miss rate by max 3PT deviation:")
    for b, sub in g.groupby("fg3_bin", observed=True):
        flips = sub[sub["is_coin_flip"]]
        if len(flips) == 0:
            continue
        print(f"    {b}: coin flips n={len(flips):>4} big-miss rate {flips['is_big_miss'].mean():.4f}")

    # ==================================================================
    # H-C: SEASON PARITY -- does std-of-team-win-pct correlate with our acc?
    # ==================================================================
    print()
    print("=" * 78)
    print("H-C: Season-level parity -- is 23-24's failure tied to league parity?")
    print("=" * 78)
    print("\n  Per-season: std of team win pct (smaller = more parity = more coin flips)")
    for s in sorted(g["season"].unique()):
        season_box = box[box["season"] == s]
        team_records = season_box.groupby("team_abbr").agg(
            wins=("win", "sum"), n=("game_id", "count")).reset_index()
        team_records["win_pct"] = team_records["wins"] / team_records["n"]
        season_g = g[g["season"] == s]
        avg_winpct = season_g["correct"].mean()
        flip_rate = season_g["is_coin_flip"].mean()
        bm_rate = season_g[season_g["is_coin_flip"]]["is_big_miss"].mean() if season_g["is_coin_flip"].sum() > 0 else 0
        print(f"    {s}: parity_std={team_records['win_pct'].std():.4f}  "
              f"our_win_pct={avg_winpct:.4f}  flip_rate={flip_rate:.4f}  big_miss_in_flips={bm_rate:.4f}")


if __name__ == "__main__":
    main()
