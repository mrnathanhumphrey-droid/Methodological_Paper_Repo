"""Inject intl prospect stats captured via WebFetch into a supplement parquet.

Source attribution per-row (kept in `source` column). Currently captures:
  - Luigi Suigo: FULL 2025-26 ABA League (KK Mega Basket) per-game stats — Wikipedia
  - Karim Lopez: partial 2024-25 NBL (NZ Breakers) — Wikipedia (GP, PPG, RPG only)
  - Jack Kayil: partial 2024-25 ABA League (KK Mega Basket) — Wikipedia (PPG, GP only)
  - Sergio De Larrea: meta only (height, team), no stats captured

Per-40 derived from per-game × (40 / mpg). For rows without MPG, leaves stats NaN
and flags `data_status` accordingly.
"""
from __future__ import annotations
import sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path("D:/NBA Projections/data/parquet/draft_2026_intl_supplement.parquet")

ROWS = [
    {
        "player_name": "Luigi Suigo", "position": "C",
        "league": "ABA League", "team": "KK Mega Basket", "season": "2025-26",
        "height_cm": 221,
        "gp": 26, "mpg": 17.9,
        "pts_pg": 7.9, "reb_pg": 5.1, "ast_pg": 0.7,
        "stl_pg": 0.5, "blk_pg": 1.0, "tov_pg": np.nan, "fg3m_pg": np.nan,
        "fg_pct": 0.535, "fg3_pct": 0.271, "ft_pct": 0.647,
        "data_status": "FULL", "source": "wikipedia",
    },
    {
        "player_name": "Karim Lopez", "position": "SF",
        "league": "NBL Australia", "team": "NZ Breakers", "season": "2025-26",
        "height_cm": 206,
        "gp": 30, "mpg": 25.6,
        "pts_pg": 11.9, "reb_pg": 6.1, "ast_pg": 1.9,
        "stl_pg": 1.2, "blk_pg": 1.0, "tov_pg": 1.5, "fg3m_pg": np.nan,
        "fg_pct": 0.490, "fg3_pct": np.nan, "ft_pct": 0.740,
        "data_status": "FULL", "source": "nzbreakers.basketball + duckduckgo",
    },
    {
        "player_name": "Jack Kayil", "position": "PG",
        "league": "Germany BBL", "team": "Alba Berlin", "season": "2025-26",
        "height_cm": 191,
        "gp": 38, "mpg": 21.2,
        "pts_pg": 12.6, "reb_pg": 2.7, "ast_pg": 3.5,
        "stl_pg": 0.9, "blk_pg": 0.1, "tov_pg": 2.2, "fg3m_pg": 1.74,
        "fg_pct": 0.398, "fg3_pct": 0.337, "ft_pct": 0.786,
        "data_status": "FULL", "source": "scoutbasketball.com + albaberlin.de",
    },
    {
        "player_name": "Sergio De Larrea", "position": "PG",
        "league": "ACB Spain", "team": "Valencia Basket", "season": "2024-25",
        "height_cm": 196,
        "gp": 30, "mpg": 17.2,
        "pts_pg": 9.6, "reb_pg": 3.0, "ast_pg": 3.7,
        "stl_pg": np.nan, "blk_pg": np.nan, "tov_pg": np.nan, "fg3m_pg": np.nan,
        "fg_pct": np.nan, "fg3_pct": np.nan, "ft_pct": np.nan,
        "data_status": "PARTIAL_PRIOR_SEASON", "source": "basketnews.com + basketballstats.net",
    },
]


def main():
    df = pd.DataFrame(ROWS)
    for s in ["pts", "reb", "ast", "stl", "blk", "tov", "fg3m"]:
        df[f"{s}_per40"] = df[f"{s}_pg"] * 40.0 / df["mpg"]
    df.to_parquet(OUT, index=False)
    df.to_csv(OUT.with_suffix(".csv"), index=False)
    print(f"wrote: {OUT}")
    print(df[["player_name", "league", "season", "data_status", "gp", "mpg",
                  "pts_per40", "reb_per40", "ast_per40", "blk_per40"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
