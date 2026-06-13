"""STD-pos — Position-Normalized Shot-Type Diversity (v2 of STD).

V1 STD was heavily position-determined (Centers cluster at bottom because their
shot diet is positionally constrained). V2 normalizes against position cohort:
who is the MOST versatile shooter for their archetype?

Joins shotchart to bbref per_game positions. Then for each position:
  pos_baseline = position-median entropy of shot-zone distribution
  std_pos_premium = H_player - pos_baseline

Top by std_pos_premium WITHIN each position = the versatile archetype outlier.
"""
from __future__ import annotations
import sys, warnings, re
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

SHOT = "D:/NBA Projections/data/parquet/shotchart/shotchart_2024-25.parquet"
ROSTERS = "D:/NBA Projections/data/parquet/sportradar_rosters.parquet"
OUT = Path("D:/NBA Projections/data/results")
OUT_PATH = OUT / "std_pos_2024_25.parquet"
MIN_FGA = 200


def normalize_name(s):
    if not isinstance(s, str): return ""
    s = re.sub(r"[^\w\s]", " ", s.lower())
    return " ".join(s.split())


def main():
    print("=== loading shotchart 2024-25 ===")
    df = pd.read_parquet(SHOT)
    primary = (df.groupby("PLAYER_ID")["TEAM_ID"]
                  .agg(lambda s: s.value_counts().idxmax())
                  .reset_index().rename(columns={"TEAM_ID":"primary_team"}))
    df = df.merge(primary, on="PLAYER_ID")
    df = df[df["TEAM_ID"] == df["primary_team"]]

    pid_to_name = df.drop_duplicates(subset=["PLAYER_ID"]).set_index("PLAYER_ID")["PLAYER_NAME"].to_dict()

    # === sportradar_rosters position lookup ===
    rost = pd.read_parquet(ROSTERS)
    rost["norm_name"] = rost["player_name"].map(normalize_name)
    rost_unique = rost.drop_duplicates(subset=["norm_name"], keep="first")
    pos_lookup = dict(zip(rost_unique["norm_name"], rost_unique["primary_position"]))
    print(f"  position lookup: {len(pos_lookup)} players")

    rows = []
    for pid, sub in df.groupby("PLAYER_ID"):
        n = len(sub)
        if n < MIN_FGA: continue
        name = pid_to_name.get(int(pid), str(pid))
        pos = pos_lookup.get(normalize_name(name))
        if pos is None or pos not in ("PG","SG","SF","PF","C"): continue
        zc = sub["SHOT_ZONE_BASIC"].value_counts()
        p = zc.values / n
        H_p = -np.sum(p * np.log(p + 1e-12))
        rows.append({
            "player_id":   int(pid),
            "player_name": name,
            "position":    pos,
            "n_fga":       int(n),
            "H_player":    float(H_p),
            "top_zone":    str(zc.index[0]),
            "top_zone_share": float(zc.iloc[0] / n),
        })
    pos_df = pd.DataFrame(rows)
    print(f"  qualifying players w/ position: {len(pos_df)}")

    # Position cohort median + residual
    pos_med = pos_df.groupby("position")["H_player"].median().to_dict()
    pos_df["pos_median_H"] = pos_df["position"].map(pos_med)
    pos_df["std_pos_premium"] = pos_df["H_player"] - pos_df["pos_median_H"]
    # Rank within position
    pos_df["rank_in_pos"] = pos_df.groupby("position")["std_pos_premium"].rank(ascending=False, method="min").astype(int)
    pos_df = pos_df.sort_values(["position","std_pos_premium"], ascending=[True,False])

    pos_df.to_parquet(OUT_PATH, index=False)
    pos_df.to_csv(OUT_PATH.with_suffix(".csv"), index=False)
    print(f"\nwrote: {OUT_PATH}")

    print("\n=== position cohort medians (H_player) ===")
    print(pd.Series(pos_med).round(3).to_string())

    for pos_label in ["PG","SG","SF","PF","C"]:
        print(f"\n=== TOP 10 most versatile within {pos_label} ===")
        sub = pos_df[pos_df["position"]==pos_label].head(10)
        cols = ["rank_in_pos","player_name","n_fga","H_player","std_pos_premium","top_zone","top_zone_share"]
        print(sub[cols].round(3).to_string(index=False))
        print(f"=== BOTTOM 5 most specialized within {pos_label} ===")
        tail = pos_df[pos_df["position"]==pos_label].tail(5)
        print(tail[cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
