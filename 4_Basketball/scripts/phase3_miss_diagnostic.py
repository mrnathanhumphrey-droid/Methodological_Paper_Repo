"""Diagnostic on where we miss — focused on:
  (a) 23-24 coin-flip anomaly: 42.9% win pct, +50% worse than other seasons
  (b) 3-6 actual margin bucket within coin flips: 48.9% (worse than random)
  (c) Team-specific blind spots: do we systematically misjudge specific teams?
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
    g["err"] = g["pred_margin"] - g["actual_margin"]
    g["abs_err"] = g["err"].abs()

    # (a) 23-24 deep dive
    print("=" * 80)
    print("(a) 23-24 deep dive: why are coin flips 42.9%?")
    print("=" * 80)
    s23 = g[g["season"] == "2023-24"].copy()
    print(f"  Total 23-24 games: {len(s23)}")
    print(f"  Overall 23-24 win pct: {s23['correct'].mean():.4f}")
    print(f"  Overall 23-24 margin RMSE: {np.sqrt((s23['err']**2).mean()):.4f}")

    s23_flip = s23[s23["abs_pred_margin"] <= 2]
    print(f"  Coin-flip 23-24 games: {len(s23_flip)}")
    print(f"  Win pct on coin flips: {s23_flip['correct'].mean():.4f}")

    # Where do 23-24 coin flips actually land?
    am_bins = [0, 3, 6, 10, 15, 20, 50]
    am_labels = ["0-3", "3-6", "6-10", "10-15", "15-20", "20+"]
    s23_flip["actual_bin"] = pd.cut(s23_flip["abs_actual_margin"], bins=am_bins, labels=am_labels)
    print()
    print("  23-24 coin-flip games by actual margin:")
    print(f"  {'actual_|margin|':>16} {'n':>6} {'win_pct':>9}")
    for b, sub in s23_flip.groupby("actual_bin", observed=True):
        print(f"  {b:>16} {len(sub):>6} {sub['correct'].mean():>9.4f}")

    # Which teams produce the most 23-24 coin-flip MISSES?
    s23_miss = s23_flip[~s23_flip["correct"]]
    print()
    print(f"  23-24 coin-flip MISSES: {len(s23_miss)}")
    home_miss = s23_miss.groupby("home_team").size().reset_index(name="n_miss_as_home")
    away_miss = s23_miss.groupby("away_team").size().reset_index(name="n_miss_as_away")
    home_total = s23.groupby("home_team").size().reset_index(name="n_home")
    away_total = s23.groupby("away_team").size().reset_index(name="n_away")
    teams = pd.concat([home_miss.rename(columns={"home_team": "team", "n_miss_as_home": "n_miss_h"}).set_index("team"),
                        away_miss.rename(columns={"away_team": "team", "n_miss_as_away": "n_miss_a"}).set_index("team")],
                       axis=1).reset_index().fillna(0)
    teams["n_miss"] = teams["n_miss_h"] + teams["n_miss_a"]
    teams = teams.sort_values("n_miss", ascending=False)
    print()
    print("  Teams w/ most coin-flip MISSES in 23-24:")
    print(f"  {'team':>6} {'n_miss':>8}")
    for _, r in teams.head(10).iterrows():
        print(f"  {r['team']:>6} {int(r['n_miss']):>8}")

    # (b) 3-6 actual margin bucket -- worse than random
    print()
    print("=" * 80)
    print("(b) 3-6 actual margin bucket: 48.9% win pct in coin flips")
    print("=" * 80)
    flips = g[g["abs_pred_margin"] <= 2]
    bucket_3_6 = flips[(flips["abs_actual_margin"] > 3) & (flips["abs_actual_margin"] <= 6)]
    print(f"  Count: {len(bucket_3_6)}")
    print(f"  Win pct: {bucket_3_6['correct'].mean():.4f}")
    # When we predict HOME (margin > 0) but margin is small and actual is 3-6 in other direction
    # Pattern: we predicted home win by 0-2, actual was away win by 3-6 -- missed by ~5-8 pts
    bucket_3_6_h_pred = bucket_3_6[bucket_3_6["pred_margin"] > 0]
    bucket_3_6_a_pred = bucket_3_6[bucket_3_6["pred_margin"] <= 0]
    print(f"  Predicted HOME (n={len(bucket_3_6_h_pred)}): win_pct {bucket_3_6_h_pred['correct'].mean():.4f}")
    print(f"  Predicted AWAY (n={len(bucket_3_6_a_pred)}): win_pct {bucket_3_6_a_pred['correct'].mean():.4f}")

    # Per-season for the 3-6 bucket
    print()
    print("  Per-season win pct in coin-flip 3-6 bucket:")
    for s, sub in bucket_3_6.groupby("season"):
        print(f"  {s}: n={len(sub):>4} win_pct={sub['correct'].mean():.4f}")

    # (c) Team-specific blind spots
    print()
    print("=" * 80)
    print("(c) Team-specific blind spots (worst win pct by team, min 100 games)")
    print("=" * 80)
    home_g = g[["home_team", "correct", "err", "abs_err", "season", "game_id"]].rename(
        columns={"home_team": "team"})
    home_g["was_home"] = True
    away_g = g[["away_team", "correct", "err", "abs_err", "season", "game_id"]].rename(
        columns={"away_team": "team"})
    away_g["was_home"] = False
    # Flip correctness sign for away team perspective:
    # correctness is from HOME perspective: if home win == predicted, correct=True.
    # For "did we get this team's outcome right" we just use the same 'correct' since 50% rate doesn't depend on home/away
    all_team = pd.concat([home_g, away_g])
    team_acc = all_team.groupby("team").agg(
        n=("correct", "count"),
        win_pct=("correct", "mean"),
        margin_mae=("abs_err", "mean"),
    ).reset_index()
    team_acc = team_acc[team_acc["n"] >= 100].sort_values("win_pct")
    print(f"  {'team':>6} {'n':>6} {'win_pct':>9} {'margin_mae':>11}")
    print("  -- Worst-predicted teams: --")
    for _, r in team_acc.head(8).iterrows():
        print(f"  {r['team']:>6} {r['n']:>6} {r['win_pct']:>9.4f} {r['margin_mae']:>11.4f}")
    print("  -- Best-predicted teams: --")
    for _, r in team_acc.tail(8).iterrows():
        print(f"  {r['team']:>6} {r['n']:>6} {r['win_pct']:>9.4f} {r['margin_mae']:>11.4f}")

    # (d) Misses by mid-season vs late-season for coin flips
    print()
    print("=" * 80)
    print("(d) Coin-flip games where margin pred was wrong AND actual margin big (>10)")
    print("    These are the 'real team strength gap missed' cases")
    print("=" * 80)
    flips_big_miss = flips[~flips["correct"] & (flips["abs_actual_margin"] > 10)].copy()
    print(f"  Count: {len(flips_big_miss)}  ({len(flips_big_miss)/len(flips):.2%} of coin flips)")
    # By season
    print()
    print("  Per-season distribution of 'big-miss' coin flips:")
    for s, sub in flips_big_miss.groupby("season"):
        s_total = len(flips[flips["season"] == s])
        print(f"  {s}: n={len(sub):>4}  ({len(sub)/s_total:.2%} of season's flips)")


if __name__ == "__main__":
    main()
