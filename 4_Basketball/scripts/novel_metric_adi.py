"""ADI — Action Diversity Index (novel offensive metric, T1).

Same scaffolding as STD but on ACTION_TYPE instead of SHOT_ZONE_BASIC.
Measures HOW the player shoots (jump shot vs pull-up vs step-back vs floater
vs dunk vs layup variants), NOT WHERE.

A player can have low STD (one zone) but high ADI (many shot types within
that zone). The two metrics decompose shot diet on two orthogonal axes:
  STD = WHERE (zone)
  ADI = HOW  (action type)

Min FGA 200, baseline = team ACTION_TYPE distribution.
"""
from __future__ import annotations
import sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

SHOT = "D:/NBA Projections/data/parquet/shotchart/shotchart_2024-25.parquet"
OUT = Path("D:/NBA Projections/data/results")
OUT_PATH = OUT / "adi_2024_25.parquet"
MIN_FGA = 200


def main():
    print("=== loading shotchart ===")
    df = pd.read_parquet(SHOT)
    primary = (df.groupby("PLAYER_ID")["TEAM_ID"]
                  .agg(lambda s: s.value_counts().idxmax())
                  .reset_index().rename(columns={"TEAM_ID":"primary_team"}))
    df = df.merge(primary, on="PLAYER_ID")
    df = df[df["TEAM_ID"] == df["primary_team"]]
    print(f"  shots: {len(df):,}")
    print(f"  action_type distinct values: {df['ACTION_TYPE'].nunique()}")
    print(f"  top 10 action_types: {df['ACTION_TYPE'].value_counts().head(10).to_dict()}")

    team_action = df.groupby(["TEAM_ID","ACTION_TYPE"]).size().reset_index(name="team_shots")
    team_total = team_action.groupby("TEAM_ID")["team_shots"].sum().reset_index().rename(columns={"team_shots":"team_total"})
    team_action = team_action.merge(team_total, on="TEAM_ID")
    team_action["team_share"] = team_action["team_shots"] / team_action["team_total"]

    pid_to_name = df.drop_duplicates(subset=["PLAYER_ID"]).set_index("PLAYER_ID")["PLAYER_NAME"].to_dict()

    rows = []
    for pid, sub in df.groupby("PLAYER_ID"):
        n = len(sub)
        if n < MIN_FGA: continue
        team = int(sub["primary_team"].iloc[0])
        act_counts = sub["ACTION_TYPE"].value_counts()
        acts = act_counts.index.values
        p = act_counts.values / n
        team_sub = team_action[team_action["TEAM_ID"] == team].set_index("ACTION_TYPE")["team_share"]
        baseline = np.array([team_sub.get(a, 1e-6) for a in acts])
        baseline = baseline / baseline.sum()
        H_p = -np.sum(p * np.log(p + 1e-12))
        H_b = -np.sum(baseline * np.log(baseline + 1e-12))
        spread = H_p - H_b
        top_action = str(act_counts.index[0])
        top_action_share = float(act_counts.iloc[0] / n)
        diff = p - baseline
        specialty_idx = int(np.argmax(diff))
        specialty_action = str(acts[specialty_idx])
        specialty_lift = float(diff[specialty_idx])
        rows.append({
            "player_id":   int(pid),
            "player_name": pid_to_name.get(int(pid), str(pid)),
            "primary_team": team,
            "n_fga":       int(n),
            "n_actions":   int(len(p)),
            "H_player":    float(H_p),
            "H_baseline":  float(H_b),
            "spread_premium": float(spread),
            "top_action":  top_action,
            "top_action_share": top_action_share,
            "specialty_action": specialty_action,
            "specialty_lift": specialty_lift,
        })
    adi = pd.DataFrame(rows)
    print(f"\n  qualifying shooters (n>={MIN_FGA}): {len(adi)}")
    adi.to_parquet(OUT_PATH, index=False)
    adi.to_csv(OUT_PATH.with_suffix(".csv"), index=False)
    print(f"wrote: {OUT_PATH}")

    cols = ["player_name","n_fga","n_actions","H_player","H_baseline","spread_premium",
             "top_action","top_action_share","specialty_action","specialty_lift"]
    print("\n=== TOP 25 by spread_premium — uses MANY shot types ===")
    print(adi.sort_values("spread_premium", ascending=False)[cols].head(25).round(3).to_string(index=False))
    print("\n=== BOTTOM 25 by spread_premium — uses FEW shot types ===")
    print(adi.sort_values("spread_premium", ascending=True)[cols].head(25).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
