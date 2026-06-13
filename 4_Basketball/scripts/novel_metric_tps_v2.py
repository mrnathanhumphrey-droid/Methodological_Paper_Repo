"""TPS v2 — Trailing-team Production with Bayesian shrinkage.

V1 effect sizes per player were small (0.01-0.15 pts/FGA) and noisy. V2 shrinks
each per-state rate toward the league mean for that state with effective-FGA
lambda. Then surfaces posterior rates + signed premium.

Output: D:/NBA Projections/data/results/tps_v2_2024_25.parquet
"""
from __future__ import annotations
import sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

PBP = "D:/NBA Projections/data/parquet/pbp/pbp_2024-25.parquet"
OUT = Path("D:/NBA Projections/data/results")
OUT_PATH = OUT / "tps_v2_2024_25.parquet"
MIN_FGA = 300
SHRINK_LAMBDA = 200  # FGA equivalence


def main():
    df = pd.read_parquet(PBP)
    shots = df[df["action_type"].isin(["Made Shot","Missed Shot"])].copy()
    shots["score_home"] = pd.to_numeric(shots["score_home"], errors="coerce")
    shots["score_away"] = pd.to_numeric(shots["score_away"], errors="coerce")
    shots["team_diff"] = np.where(shots["location"] == "h",
                                     shots["score_home"] - shots["score_away"],
                                     shots["score_away"] - shots["score_home"])
    def bin_state(d):
        if pd.isna(d): return None
        if d <= -5: return "TRAILING_5PLUS"
        if d >=  5: return "LEADING_5PLUS"
        return "CLOSE_GAME"
    shots["state"] = shots["team_diff"].apply(bin_state)
    shots = shots.dropna(subset=["state","person_id"]).copy()
    shots["made"] = (shots["action_type"] == "Made Shot").astype(int)
    shots["pts"]  = shots["made"] * pd.to_numeric(shots["shot_value"], errors="coerce").fillna(2)

    pid_to_name = (df.dropna(subset=["player_name","person_id"])
                      .drop_duplicates(subset=["person_id"])
                      .set_index("person_id")["player_name"].to_dict())

    # League means per state
    league = shots.groupby("state").agg(league_pts=("pts","sum"), league_fga=("pts","size")).reset_index()
    league["league_pts_per_fga"] = league["league_pts"] / league["league_fga"]
    league_map = dict(zip(league["state"], league["league_pts_per_fga"]))
    print("league mean pts/FGA by state:")
    print(league.to_string(index=False))

    # Per-player per-state
    agg = (shots.groupby(["person_id","state"])
                 .agg(fga=("pts","size"), pts=("pts","sum"))
                 .reset_index())
    agg["raw_rate"] = agg["pts"] / agg["fga"]
    agg["league_mean"] = agg["state"].map(league_map)
    # Bayesian shrinkage
    agg["shrunk_rate"] = (agg["fga"] * agg["raw_rate"] + SHRINK_LAMBDA * agg["league_mean"]) / (agg["fga"] + SHRINK_LAMBDA)

    # Pivot
    pivoted = agg.pivot_table(index="person_id", columns="state",
                                 values=["fga","raw_rate","shrunk_rate"], aggfunc="first")
    pivoted.columns = ["_".join(c) for c in pivoted.columns]
    pivoted = pivoted.reset_index()
    pivoted["total_fga"] = pivoted[[c for c in pivoted.columns if c.startswith("fga_")]].sum(axis=1)
    pivoted = pivoted[pivoted["total_fga"] >= MIN_FGA]

    # Overall mean across states (weighted)
    pivoted["overall_shrunk"] = sum(
        pivoted.get(f"fga_{st}", 0) * pivoted.get(f"shrunk_rate_{st}", 0)
        for st in ["TRAILING_5PLUS","CLOSE_GAME","LEADING_5PLUS"]
    ) / pivoted["total_fga"]

    # Trailing premium (shrunk)
    pivoted["trailing_premium_shrunk"] = pivoted.get("shrunk_rate_TRAILING_5PLUS", np.nan) - pivoted["overall_shrunk"]
    pivoted["leading_premium_shrunk"]  = pivoted.get("shrunk_rate_LEADING_5PLUS",  np.nan) - pivoted["overall_shrunk"]
    pivoted["clutch_premium_shrunk"]   = pivoted.get("shrunk_rate_CLOSE_GAME", np.nan)    - pivoted["overall_shrunk"]
    pivoted["player_name"] = pivoted["person_id"].map(pid_to_name)
    pivoted = pivoted.sort_values("trailing_premium_shrunk", ascending=False)

    pivoted.to_parquet(OUT_PATH, index=False)
    pivoted.to_csv(OUT_PATH.with_suffix(".csv"), index=False)
    print(f"\nwrote: {OUT_PATH}  ({len(pivoted)} players)")

    cols = ["player_name","total_fga",
             "shrunk_rate_TRAILING_5PLUS","shrunk_rate_CLOSE_GAME","shrunk_rate_LEADING_5PLUS",
             "trailing_premium_shrunk","clutch_premium_shrunk","leading_premium_shrunk"]
    print("\n=== TOP 20 by SHRUNK trailing_premium — comeback scorers ===")
    print(pivoted[cols].head(20).round(3).to_string(index=False))
    print("\n=== BOTTOM 10 by SHRUNK trailing_premium — fade when down ===")
    print(pivoted[cols].tail(10).round(3).to_string(index=False))
    print("\n=== TOP 15 by SHRUNK clutch_premium — close-game scorers ===")
    print(pivoted.sort_values("clutch_premium_shrunk", ascending=False)[cols].head(15).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
