"""TPS — Trailing-team Production Split (novel offensive metric, T1).

For each player, compute scoring rate (points per shot) split by game-state:
  TRAILING_5PLUS:   team down 5+ when shot taken
  CLOSE_GAME:       margin within 4 (either side)
  LEADING_5PLUS:    team up 5+

Output:
  - per-bin TS% + per-bin made_per_attempt
  - "trailing premium" = TS% when trailing - TS% overall (positive = clutch comeback scorer)
  - "garbage tax" = TS% when leading - TS% when close (positive = garbage-time inflater)

Min sample: 300 FGA across bins.
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
OUT_PATH = OUT / "tps_2024_25.parquet"
MIN_FGA = 300


def main():
    print("=== loading PBP ===")
    df = pd.read_parquet(PBP)
    shots = df[df["action_type"].isin(["Made Shot","Missed Shot"])].copy()
    print(f"  shots: {len(shots):,}")

    # Score from player's team perspective
    shots["score_home"] = pd.to_numeric(shots["score_home"], errors="coerce")
    shots["score_away"] = pd.to_numeric(shots["score_away"], errors="coerce")
    # 'location' is h/v indicating whether shooter team is home (h) or away (v)
    # When location == 'h', team_diff = home - away; when 'v', team_diff = away - home
    shots["team_diff"] = np.where(shots["location"] == "h",
                                     shots["score_home"] - shots["score_away"],
                                     shots["score_away"] - shots["score_home"])

    # Game-state bins
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

    # Per (player, state): n_fga, n_made, points, EFG
    agg = (shots.groupby(["person_id","state"])
                 .agg(fga=("made","size"), fgm=("made","sum"), pts=("pts","sum"),
                       avg_value=("shot_value", lambda s: pd.to_numeric(s, errors="coerce").mean()))
                 .reset_index())
    agg["efg"] = (agg["fgm"] + 0.5 * (agg["avg_value"] * agg["fgm"] - 2*agg["fgm"]).clip(lower=0)) / agg["fga"]
    # Simpler: PTS per FGA as the headline rate (handles 2 vs 3 cleanly)
    agg["pts_per_fga"] = agg["pts"] / agg["fga"]

    pivoted = agg.pivot_table(index="person_id", columns="state",
                                 values=["fga","fgm","pts","pts_per_fga"], aggfunc="first")
    pivoted.columns = ["_".join(c) for c in pivoted.columns]
    pivoted = pivoted.reset_index()
    pivoted["total_fga"] = pivoted[[c for c in pivoted.columns if c.startswith("fga_")]].sum(axis=1)
    pivoted = pivoted[pivoted["total_fga"] >= MIN_FGA]
    # Overall pts/fga
    pivoted["total_pts"] = pivoted[[c for c in pivoted.columns if c.startswith("pts_") and not c.startswith("pts_per")]].sum(axis=1)
    pivoted["pts_per_fga_overall"] = pivoted["total_pts"] / pivoted["total_fga"]
    pivoted["trailing_premium"] = pivoted.get("pts_per_fga_TRAILING_5PLUS", np.nan) - pivoted["pts_per_fga_overall"]
    pivoted["garbage_tax"] = pivoted.get("pts_per_fga_LEADING_5PLUS", np.nan) - pivoted.get("pts_per_fga_CLOSE_GAME", np.nan)
    pivoted["player_name"] = pivoted["person_id"].map(pid_to_name)
    pivoted = pivoted.sort_values("trailing_premium", ascending=False)

    pivoted.to_parquet(OUT_PATH, index=False)
    pivoted.to_csv(OUT_PATH.with_suffix(".csv"), index=False)
    print(f"\nwrote: {OUT_PATH}  ({len(pivoted)} players)")

    cols = ["player_name","total_fga","pts_per_fga_overall",
            "pts_per_fga_TRAILING_5PLUS","pts_per_fga_CLOSE_GAME","pts_per_fga_LEADING_5PLUS",
            "trailing_premium","garbage_tax"]
    print("\n=== TOP 25 by trailing_premium — SCORE BETTER when team is down 5+ ===")
    print(pivoted[cols].head(25).round(3).to_string(index=False))
    print("\n=== BOTTOM 15 by trailing_premium — FADE when trailing ===")
    print(pivoted[cols].tail(15).round(3).to_string(index=False))
    print("\n=== TOP 15 by garbage_tax — score BETTER when team is comfortably ahead ===")
    print(pivoted.sort_values("garbage_tax", ascending=False)[cols].head(15).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
