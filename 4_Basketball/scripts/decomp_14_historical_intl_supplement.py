"""v3 — Historical intl prospect stat supplement (the missing pre-NBA per-40).

Injects pre-NBA per-40 stats from WebFetch scrapes for high-impact historical
intl prospects whose stats were NaN in rookies_master.

Coverage (Wikipedia-sourced 2026-06-07):
  - LaMelo Ball, Alex Sarr, AJ Johnson — NBL Australia
  - Victor Wembanyama, Zaccharie Risacher — LNB France
  - Mario Hezonja, Sasha Vezenkov — ACB Spain
  - Deni Avdija — Israeli Premier League

These are the most-cited prospects who set the league-baseline priors. Hezonja
(4.7 ppg ACB at 18 → #5 pick) and Vezenkov (8.7 ppg ACB at 21 → #57 pick) are
key ANTI-survivor anchors that break the Doncic-tier prior for ACB.

Outputs:
    data/parquet/rookies_outcome_training_v3.parquet
"""
from __future__ import annotations
import sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import numpy as np
import pandas as pd

PQ = Path("D:/NBA Projections/data/parquet")
OUT = PQ / "rookies_outcome_training_v3.parquet"

SUPPLEMENT = [
    {"player_name_raw": "LaMelo Ball", "league": "intl_nbl_australia", "gp": 12, "mpg": 31.2,
        "pts_pg": 17.0, "reb_pg": 7.4, "ast_pg": 6.8, "stl_pg": 1.7, "blk_pg": 0.2,
        "fg_pct": 0.377, "fg3_pct": 0.250, "ft_pct": 0.723},
    {"player_name_raw": "Victor Wembanyama", "league": "intl_lnb_france", "gp": 34, "mpg": 32.1,
        "pts_pg": 21.6, "reb_pg": 10.4, "ast_pg": 2.4, "stl_pg": 0.9, "blk_pg": 3.0,
        "fg_pct": 0.561, "fg3_pct": 0.275, "ft_pct": 0.828},
    {"player_name_raw": "Mario Hezonja", "league": "intl_acb_spain", "gp": 41, "mpg": 14.2,
        "pts_pg": 4.7, "reb_pg": 2.0, "ast_pg": 1.2, "stl_pg": 0.7, "blk_pg": 0.1,
        "fg_pct": 0.456, "fg3_pct": 0.380, "ft_pct": 0.667},
    {"player_name_raw": "Alex Sarr", "league": "intl_nbl_australia", "gp": 27, "mpg": 17.3,
        "pts_pg": 9.4, "reb_pg": 4.3, "ast_pg": 0.9, "stl_pg": 0.4, "blk_pg": 1.5,
        "fg_pct": 0.516, "fg3_pct": 0.286, "ft_pct": 0.710},
    {"player_name_raw": "Sasha Vezenkov", "league": "intl_acb_spain", "gp": 35, "mpg": 18.8,
        "pts_pg": 8.7, "reb_pg": 3.1, "ast_pg": 0.8, "stl_pg": 0.5, "blk_pg": 0.3,
        "fg_pct": 0.528, "fg3_pct": 0.356, "ft_pct": 0.843},
    {"player_name_raw": "Zaccharie Risacher", "league": "intl_lnb_france", "gp": 22, "mpg": 22.0,
        "pts_pg": 10.1, "reb_pg": 3.8, "ast_pg": np.nan, "stl_pg": np.nan, "blk_pg": np.nan,
        "fg_pct": np.nan, "fg3_pct": np.nan, "ft_pct": np.nan},
    {"player_name_raw": "Deni Avdija", "league": "intl_bsl_israel", "gp": np.nan, "mpg": 22.0,
        "pts_pg": 12.9, "reb_pg": 6.3, "ast_pg": 2.7, "stl_pg": np.nan, "blk_pg": np.nan,
        "fg_pct": np.nan, "fg3_pct": np.nan, "ft_pct": np.nan},
    {"player_name_raw": "Frank Ntilikina", "league": "intl_lnb_france", "gp": 45, "mpg": 19.3,
        "pts_pg": 7.2, "reb_pg": 1.9, "ast_pg": 2.1, "stl_pg": np.nan, "blk_pg": np.nan,
        "fg_pct": np.nan, "fg3_pct": np.nan, "ft_pct": np.nan},
    {"player_name_raw": "Jaden Hardy", "league": "g_league", "gp": np.nan, "mpg": 28.0,
        "pts_pg": 17.7, "reb_pg": 4.6, "ast_pg": 3.2, "stl_pg": np.nan, "blk_pg": np.nan,
        "fg_pct": 0.351, "fg3_pct": np.nan, "ft_pct": np.nan},
]


def main():
    train = pd.read_parquet(PQ / "rookies_outcome_training_v2.parquet")
    print(f"  v2 training set: {len(train):,}")

    sup_df = pd.DataFrame(SUPPLEMENT)
    for s, lbl in [("pts", "ppg_pre"), ("reb", "rpg_pre"), ("ast", "apg_pre"),
                                ("stl", "spg_pre"), ("blk", "bpg_pre")]:
        sup_df[lbl] = sup_df[f"{s}_pg"] * 40.0 / sup_df["mpg"]
    sup_df["fg_pct_pre"] = sup_df["fg_pct"]
    sup_df["fg3_pct_pre"] = sup_df["fg3_pct"]
    sup_df["ft_pct_pre"] = sup_df["ft_pct"]

    updates_applied = 0
    for _, srow in sup_df.iterrows():
        name = srow["player_name_raw"]
        mask = train["player_name_raw"] == name
        if not mask.any():
            print(f"  no match in training: {name}")
            continue
        for col in ["ppg_pre", "rpg_pre", "apg_pre", "spg_pre", "bpg_pre",
                              "fg_pct_pre", "fg3_pct_pre", "ft_pct_pre"]:
            val = srow.get(col)
            if pd.notna(val):
                train.loc[mask, col] = val
        if pd.notna(srow.get("league")):
            train.loc[mask, "pre_nba_league_label"] = srow["league"]
        updates_applied += 1
    print(f"  prospects updated: {updates_applied}/{len(SUPPLEMENT)}")

    train.to_parquet(OUT, index=False)
    print(f"\nwrote: {OUT}")

    print("\n=== updated rows preview ===")
    cols = ["player_name_raw", "draft_year", "draft_pick", "pre_nba_league_label",
                  "ppg_pre", "rpg_pre", "apg_pre", "nba_y1_pts_per36", "nba_y1_mpg"]
    sup_names = [s["player_name_raw"] for s in SUPPLEMENT]
    print(train[train["player_name_raw"].isin(sup_names)][cols].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
