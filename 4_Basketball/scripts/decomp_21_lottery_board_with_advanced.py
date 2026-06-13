"""Augment v3 lottery board with advanced metrics + teammate context.

The v3 GBM stays the predictive model. This script ADDS columns to the v3
board for transparency:
  - STD (shot type diversity)
  - PSI (pass spread index)
  - ft_rate_per40 (foul-drawing rate)
  - def_event_rate_per40
  - prospect_pts_share (teammate context)
  - teammate_pts_per40_top

Outputs:
    data/parquet/draft_2026_lottery_board_final.parquet
    data/parquet/draft_2026_lottery_board_final.csv
"""
from __future__ import annotations
import sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import pandas as pd

PQ = Path("D:/NBA Projections/data/parquet")
OUT = PQ / "draft_2026_lottery_board_final.parquet"


def main():
    board = pd.read_parquet(PQ / "draft_2026_outcome_calibrated_v3.parquet")
    adv = pd.read_parquet(PQ / "prospect_advanced_metrics_2026.parquet")
    ctx = pd.read_parquet(PQ / "prospect_teammate_context.parquet")

    ctx_26 = ctx[ctx["draft_year"] == 2026][["player_name", "team",
                                                                            "prospect_pts_share",
                                                                            "teammate_pts_per40_top",
                                                                            "team_pts_per_game"]]

    adv_keep = adv[["player_name", "mp_total", "STD", "PSI",
                                "ft_rate_per40", "def_event_rate_per40",
                                "n_assists_made", "n_blocks", "n_steals"]]

    out = board.merge(ctx_26, on="player_name", how="left")
    out = out.merge(adv_keep, on="player_name", how="left")

    out.to_parquet(OUT, index=False)
    out.to_csv(OUT.with_suffix(".csv"), index=False)
    print(f"wrote: {OUT}")

    print("\n=== TOP 20 v3 BOARD WITH ADVANCED METRICS + TEAMMATE CONTEXT ===\n")
    cols = ["oc3_rank", "player_name", "position", "archetype", "oc3_tier",
                  "oc3_draft_pick", "prospect_pts_share", "teammate_pts_per40_top",
                  "STD", "PSI", "ft_rate_per40", "def_event_rate_per40",
                  "survivorship_signal"]
    cols = [c for c in cols if c in out.columns]
    print(out.sort_values("oc3_rank").head(20)[cols].round(2).to_string(index=False))

    print("\n=== ADVANCED METRIC STANDOUTS by category ===")
    print("\nTop 8 redistributors (PSI), min 30 assists:")
    psi_sub = out[out["n_assists_made"] >= 30].sort_values("PSI", ascending=False).head(8)
    print(psi_sub[["player_name", "position", "oc3_rank", "PSI", "n_assists_made"]].round(2).to_string(index=False))

    print("\nTop 8 foul-drawers (FT rate per-40):")
    ft_sub = out.sort_values("ft_rate_per40", ascending=False).head(8)
    print(ft_sub[["player_name", "position", "oc3_rank", "ft_rate_per40"]].round(2).to_string(index=False))

    print("\nTop 8 versatile scorers (STD):")
    std_sub = out.sort_values("STD", ascending=False).head(8)
    print(std_sub[["player_name", "position", "oc3_rank", "STD", "ft_rate_per40"]].round(2).to_string(index=False))

    print("\nTop 8 defensive engines (def event rate):")
    def_sub = out.sort_values("def_event_rate_per40", ascending=False).head(8)
    print(def_sub[["player_name", "position", "oc3_rank", "def_event_rate_per40",
                          "n_blocks", "n_steals"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
