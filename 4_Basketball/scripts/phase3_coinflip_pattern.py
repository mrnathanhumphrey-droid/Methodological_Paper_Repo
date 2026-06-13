"""Pattern analysis on coin-flip games (|pred_margin| <= 2) from 8-season walk-forward.

We hit only 53.28% on these 2166 games. Looking for systematic patterns:
  - Home/away win rate skew
  - Team-level: do specific teams produce more coin flips?
  - SRS-strength-gap (similar-strength teams vs apparent mismatches we underrate)
  - Time-within-season concentration
  - Actual margin distribution -- are these close games or blowouts we underestimated?
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from pathlib import Path

PRED = Path("audit_runs/walkforward_allseasons/per_game_predictions.csv")


def main():
    g = pd.read_csv(PRED)
    g["abs_pred_margin"] = g["pred_margin"].abs()
    g["abs_actual_margin"] = g["actual_margin"].abs()
    print(f"Total games: {len(g)}")

    flips = g[g["abs_pred_margin"] <= 2].copy()
    print(f"Coin-flip games (|pred_margin| <= 2): {len(flips)}")

    # 1. Home win rate in coin flips
    print()
    print("=" * 75)
    print("1. Home/away skew in coin flips")
    print("=" * 75)
    print(f"  Overall home win rate in coin flips: {(flips['actual_margin'] > 0).mean():.4f}")
    print(f"  Overall home win rate in all games:  {(g['actual_margin'] > 0).mean():.4f}")
    print(f"  Our predicted home wins in coin flips: {(flips['pred_margin'] > 0).mean():.4f}")

    # 2. Where the coin flips actually land in actual margin
    print()
    print("=" * 75)
    print("2. Actual margin distribution within 'coin flip' predictions")
    print("=" * 75)
    am_bins = [0, 3, 6, 10, 15, 20, 50]
    am_labels = ["0-3", "3-6", "6-10", "10-15", "15-20", "20+"]
    flips["actual_bin"] = pd.cut(flips["abs_actual_margin"], bins=am_bins, labels=am_labels)
    table = flips.groupby("actual_bin", observed=True).agg(
        n=("correct", "count"),
        win_pct=("correct", "mean"),
    ).reset_index()
    print(f"  {'actual_|margin|':>16} {'n':>6} {'fraction':>10} {'win_pct':>9}")
    for _, r in table.iterrows():
        frac = r["n"] / len(flips)
        print(f"  {r['actual_bin']:>16} {r['n']:>6} {frac:>10.2%} {r['win_pct']:>9.4f}")

    # 3. Per-season coin flip rate
    print()
    print("=" * 75)
    print("3. Coin flip incidence + win pct by season")
    print("=" * 75)
    print(f"  {'season':<10} {'n_total':>8} {'n_flip':>7} {'flip_rate':>10} {'flip_winpct':>13}")
    for s in sorted(g["season"].unique()):
        sub = g[g["season"] == s]
        f = sub[sub["abs_pred_margin"] <= 2]
        print(f"  {s:<10} {len(sub):>8} {len(f):>7} {len(f)/len(sub):>10.4f} {f['correct'].mean():>13.4f}")

    # 4. Per-team coin-flip rates (which teams produce most coin flips?)
    print()
    print("=" * 75)
    print("4. Top 10 teams by coin-flip rate (as home or away participant)")
    print("=" * 75)
    home_flips = flips[["season", "game_id", "home_team"]].rename(columns={"home_team": "team"})
    away_flips = flips[["season", "game_id", "away_team"]].rename(columns={"away_team": "team"})
    team_flips = pd.concat([home_flips, away_flips])
    team_flip_counts = team_flips.groupby("team").size().reset_index(name="n_flip_games")

    home_all = g[["season", "game_id", "home_team"]].rename(columns={"home_team": "team"})
    away_all = g[["season", "game_id", "away_team"]].rename(columns={"away_team": "team"})
    team_all = pd.concat([home_all, away_all])
    team_total = team_all.groupby("team").size().reset_index(name="n_total_games")

    team_rate = team_total.merge(team_flip_counts, on="team", how="left")
    team_rate["n_flip_games"] = team_rate["n_flip_games"].fillna(0).astype(int)
    team_rate["flip_rate"] = team_rate["n_flip_games"] / team_rate["n_total_games"]
    team_rate = team_rate.sort_values("flip_rate", ascending=False)
    print(f"  {'team':>6} {'n_games':>8} {'n_flip':>7} {'flip_rate':>10}")
    for _, r in team_rate.head(10).iterrows():
        print(f"  {r['team']:>6} {r['n_total_games']:>8} {r['n_flip_games']:>7} {r['flip_rate']:>10.4f}")
    print(f"\n  Bottom 5 (teams with FEWEST coin flips):")
    for _, r in team_rate.tail(5).iterrows():
        print(f"  {r['team']:>6} {r['n_total_games']:>8} {r['n_flip_games']:>7} {r['flip_rate']:>10.4f}")

    # 5. Are coin flips concentrated at season starts (low data) or any time?
    print()
    print("=" * 75)
    print("5. Coin flip rate by time within season")
    print("=" * 75)
    g_sorted = g.sort_values(["season", "game_id"]).reset_index(drop=True)
    g_sorted["season_rank"] = g_sorted.groupby("season").cumcount()
    g_sorted["n_per_season"] = g_sorted.groupby("season")["game_id"].transform("count")
    g_sorted["pct_into_season"] = g_sorted["season_rank"] / g_sorted["n_per_season"]
    g_sorted["q"] = pd.cut(g_sorted["pct_into_season"], bins=[0, 0.25, 0.5, 0.75, 1.01],
                            labels=["Q1 (early)", "Q2", "Q3", "Q4 (late)"])
    print(f"  {'period':>14} {'n':>6} {'n_flip':>7} {'flip_rate':>10} {'flip_winpct':>13}")
    for q, sub in g_sorted.groupby("q", observed=True):
        f = sub[sub["abs_pred_margin"] <= 2]
        print(f"  {q:>14} {len(sub):>6} {len(f):>7} {len(f)/len(sub):>10.4f} {f['correct'].mean():>13.4f}")


if __name__ == "__main__":
    main()
