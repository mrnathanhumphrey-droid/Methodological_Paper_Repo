"""How does our 65.31% combined win pct break down by:
  (a) prediction confidence (|pred_margin| bucket)
  (b) time within season (early/mid/late)
  (c) per-month variance

This tells us if 65.31% is meaningful "per game" or just an average across very
different game types.
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
    print(f"Total games: {len(g)}")
    g["abs_pred_margin"] = g["pred_margin"].abs()

    # (a) Confidence buckets
    print()
    print("=" * 75)
    print("(a) Win pct by prediction CONFIDENCE (|pred_margin| bucket)")
    print("=" * 75)
    bins = [0, 2, 4, 6, 8, 10, 12, 15, 50]
    labels = ["0-2", "2-4", "4-6", "6-8", "8-10", "10-12", "12-15", "15+"]
    g["conf_bin"] = pd.cut(g["abs_pred_margin"], bins=bins, labels=labels)
    table = g.groupby("conf_bin", observed=True).agg(
        n=("correct", "count"),
        win_pct=("correct", "mean"),
        actual_margin_mean=("actual_margin", lambda x: x.abs().mean()),
    ).reset_index()
    table["cumulative_n"] = table["n"].cumsum()
    table["cumulative_winpct"] = (table["n"] * table["win_pct"]).cumsum() / table["cumulative_n"]
    print(f"  {'bucket':>8} {'n':>6} {'win_pct':>9} {'actual_|margin|':>16} {'cum_n':>8} {'cum_wp':>9}")
    for _, r in table.iterrows():
        print(f"  {r['conf_bin']:>8} {r['n']:>6} {r['win_pct']:>9.4f} "
              f"{r['actual_margin_mean']:>16.2f} {r['cumulative_n']:>8} {r['cumulative_winpct']:>9.4f}")

    # 95% CI on overall 65.31%
    n = len(g)
    p = g["correct"].mean()
    se = np.sqrt(p * (1 - p) / n)
    print(f"\nOverall: {p:.4f} ± 1.96·SE = [{p - 1.96*se:.4f}, {p + 1.96*se:.4f}]  (95% CI)")

    # (b) Time within season
    print()
    print("=" * 75)
    print("(b) Win pct by TIME WITHIN SEASON (which game # for season's predictions)")
    print("=" * 75)
    g["game_date"] = pd.to_datetime(g["game_date"]) if "game_date" in g.columns else pd.NaT
    # Need to derive position within season for each game
    if "season" in g.columns:
        # Order games per season, bucket by quartile
        g_sorted = g.sort_values(["season", "game_id"]).reset_index(drop=True)
        g_sorted["season_rank"] = g_sorted.groupby("season").cumcount()
        g_sorted["n_per_season"] = g_sorted.groupby("season")["game_id"].transform("count")
        g_sorted["pct_into_season"] = g_sorted["season_rank"] / g_sorted["n_per_season"]
        g_sorted["season_qtr"] = pd.cut(g_sorted["pct_into_season"],
                                          bins=[0, 0.25, 0.5, 0.75, 1.01],
                                          labels=["Q1 (early)", "Q2", "Q3", "Q4 (late)"])
        print(f"  {'period':>14} {'n':>6} {'win_pct':>9} {'rmse':>8}")
        for q, sub in g_sorted.groupby("season_qtr", observed=True):
            err = sub["pred_margin"] - sub["actual_margin"]
            print(f"  {q:>14} {len(sub):>6} {sub['correct'].mean():>9.4f} "
                  f"{np.sqrt((err**2).mean()):>8.3f}")

    # (c) Per-confidence relative to actual margin distribution
    print()
    print("=" * 75)
    print("(c) When we're MOST confident (top 25% by |pred_margin|), how accurate are we?")
    print("=" * 75)
    g_sorted_conf = g.sort_values("abs_pred_margin", ascending=False).reset_index(drop=True)
    for top_pct in [10, 25, 33, 50, 75]:
        n_top = int(len(g_sorted_conf) * top_pct / 100)
        top = g_sorted_conf.head(n_top)
        print(f"  Top {top_pct}% confidence (n={n_top}, |pred_margin| > {top['abs_pred_margin'].min():.2f}): "
              f"win_pct {top['correct'].mean():.4f}")

    # (d) bootstrap CI on overall
    print()
    print("=" * 75)
    print("(d) Bootstrap 95% CI on overall 8-season win pct")
    print("=" * 75)
    np.random.seed(42)
    boots = []
    for _ in range(2000):
        idx = np.random.choice(n, n, replace=True)
        boots.append(g["correct"].iloc[idx].mean())
    boots = np.array(boots)
    print(f"  Bootstrap mean: {boots.mean():.4f}")
    print(f"  95% CI:         [{np.percentile(boots, 2.5):.4f}, {np.percentile(boots, 97.5):.4f}]")
    print(f"  SD:             {boots.std():.4f}")


if __name__ == "__main__":
    main()
