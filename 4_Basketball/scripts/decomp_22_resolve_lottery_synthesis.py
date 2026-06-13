"""Synthesize the Resolve Lottery: Top 14 board with weighted signal blend.

Resolve Score formula (defensible weighted blend):
  resolve_score = (
        0.45 * v3_rank_pct          # outcome-calibrated model (primary)
      + 0.20 * hand_rank_pct        # production composite (secondary)
      + 0.30 * advanced_signal_pct  # PSI + STD + FT_rate + def_event_rate
      + survivorship_penalty        # negative if survivorship_signal > 5
  )

Top 14 by resolve_score = OUR LOTTERY.

Output:
    data/parquet/resolve_lottery_2026.parquet
"""
from __future__ import annotations
import sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

PQ = Path("D:/NBA Projections/data/parquet")
OUT = PQ / "resolve_lottery_2026.parquet"


def pct_rank(series, ascending_better=False):
    """Convert rank to 0-1 score. If lower-rank-is-better (rank #1 = best), set ascending_better=False."""
    if ascending_better:
        return (series - series.min()) / (series.max() - series.min())
    return 1.0 - (series - series.min()) / (series.max() - series.min())


def zscore_pct(series):
    s = series.fillna(series.mean())
    z = (s - s.mean()) / s.std(ddof=0)
    return 1 / (1 + np.exp(-z))  # logistic squash to 0-1


def main():
    board = pd.read_parquet(PQ / "draft_2026_lottery_board_final.parquet")
    print(f"  prospects in pool: {len(board)}")

    board["v3_rank_pct"] = 1.0 - (board["oc3_rank"] - 1) / (board["oc3_rank"].max() - 1)
    board["hand_rank_pct"] = 1.0 - (board["hand_rank"] - 1) / (board["hand_rank"].max() - 1)

    adv_metrics = {
        "STD": board["STD"], "PSI": board["PSI"],
        "ft_rate_per40": board["ft_rate_per40"],
        "def_event_rate_per40": board["def_event_rate_per40"],
    }
    adv_scores = []
    for col, s in adv_metrics.items():
        if s.notna().any():
            adv_scores.append(zscore_pct(s))
    board["advanced_signal_pct"] = pd.concat(adv_scores, axis=1).mean(axis=1) if adv_scores else 0.5
    board["advanced_signal_pct"] = board["advanced_signal_pct"].fillna(0.5)

    board["survivorship_penalty"] = np.where(
        board["survivorship_signal"].fillna(0) > 5,
        -0.03 * (board["survivorship_signal"].fillna(0) - 5),
        0.0
    )

    intl_low_n_mask = (
        board["pre_nba_league_label"].astype(str).str.startswith("intl_")
        & (board["league_n"].fillna(0) < 10)
        & board["STD"].isna()
    )
    board["intl_low_n_penalty"] = np.where(intl_low_n_mask, -0.12, 0.0)

    board["resolve_score"] = (
        0.45 * board["v3_rank_pct"]
        + 0.20 * board["hand_rank_pct"]
        + 0.30 * board["advanced_signal_pct"]
        + board["survivorship_penalty"]
        + board["intl_low_n_penalty"]
    )

    board = board.sort_values("resolve_score", ascending=False).reset_index(drop=True)
    board["resolve_rank"] = board.index + 1

    board.to_parquet(OUT, index=False)
    board.to_csv(OUT.with_suffix(".csv"), index=False)
    print(f"  wrote: {OUT}")

    print("\n=== RESOLVE LOTTERY 2026 — Top 14 ===\n")
    cols = ["resolve_rank", "player_name", "position", "pre_nba_league_label", "archetype",
                  "resolve_score", "oc3_rank", "hand_rank", "advanced_signal_pct",
                  "survivorship_signal", "STD", "PSI", "ft_rate_per40", "def_event_rate_per40"]
    cols = [c for c in cols if c in board.columns]
    print(board.head(14)[cols].round(2).to_string(index=False))

    print("\n=== Outside Lottery (15-25 — Mid-1st) ===\n")
    print(board.iloc[14:25][cols].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
