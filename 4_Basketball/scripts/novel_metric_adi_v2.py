"""ADI v2 — Action Diversity Index with COLLAPSED RIM TAXONOMY.

V1 failure: the action_type taxonomy has 10+ fine-grained rim-attack labels
(Cutting Dunk, Alley Oop, Tip Layup, Putback, Finger Roll, etc.) but only
3-4 perimeter labels. So Centers naturally ranked highest in ADI v1 because
their action vocabulary at the rim is granular.

V2 fix: collapse to a 7-category macro taxonomy:
  RIM        - all dunks, layups, tips, finger rolls
  FLOATER    - driving floating jumpers
  JUMPER     - standard jump shot, step-back, fadeaway
  PULLUP     - pullup, running jump shots
  HOOK       - hook shots, turnaround hooks
  POST_UP    - turnaround jumper, turnaround fadeaway
  OTHER      - anything not matching above

Then Shannon entropy over the 7 cells, team baseline as before.
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
OUT_PATH = OUT / "adi_v2_2024_25.parquet"
MIN_FGA = 200


def classify_action(action_type: str) -> str:
    if not isinstance(action_type, str): return "OTHER"
    a = action_type.lower()
    # Rim attacks first (any of these wins)
    if any(k in a for k in ["dunk", "layup", "finger roll", "tip"]):
        return "RIM"
    if "hook" in a:
        # Turnaround hook = post; plain hook = rim-adjacent
        if "turnaround" in a:
            return "POST_UP"
        return "HOOK"
    if "floating" in a:
        return "FLOATER"
    if "pullup" in a or "pull-up" in a or "running jump" in a:
        return "PULLUP"
    if "step back" in a or "stepback" in a or "fadeaway" in a:
        return "JUMPER"
    if "turnaround" in a:
        return "POST_UP"
    if "jump shot" in a:
        return "JUMPER"
    return "OTHER"


def main():
    print("=== loading shotchart ===")
    df = pd.read_parquet(SHOT)
    primary = (df.groupby("PLAYER_ID")["TEAM_ID"]
                  .agg(lambda s: s.value_counts().idxmax())
                  .reset_index().rename(columns={"TEAM_ID":"primary_team"}))
    df = df.merge(primary, on="PLAYER_ID")
    df = df[df["TEAM_ID"] == df["primary_team"]].copy()

    df["macro_action"] = df["ACTION_TYPE"].map(classify_action)
    print(f"  macro_action distribution:")
    print(df["macro_action"].value_counts().to_string())

    pid_to_name = df.drop_duplicates(subset=["PLAYER_ID"]).set_index("PLAYER_ID")["PLAYER_NAME"].to_dict()

    # Team baseline
    team_macro = df.groupby(["TEAM_ID","macro_action"]).size().reset_index(name="team_shots")
    team_total = team_macro.groupby("TEAM_ID")["team_shots"].sum().reset_index().rename(columns={"team_shots":"team_total"})
    team_macro = team_macro.merge(team_total, on="TEAM_ID")
    team_macro["team_share"] = team_macro["team_shots"] / team_macro["team_total"]

    rows = []
    for pid, sub in df.groupby("PLAYER_ID"):
        n = len(sub)
        if n < MIN_FGA: continue
        team = int(sub["primary_team"].iloc[0])
        mc = sub["macro_action"].value_counts()
        cats = mc.index.values
        p = mc.values / n
        team_sub = team_macro[team_macro["TEAM_ID"] == team].set_index("macro_action")["team_share"]
        baseline = np.array([team_sub.get(c, 1e-6) for c in cats])
        baseline = baseline / baseline.sum()
        H_p = -np.sum(p * np.log(p + 1e-12))
        H_b = -np.sum(baseline * np.log(baseline + 1e-12))
        spread = H_p - H_b
        top_cat = str(mc.index[0])
        top_cat_share = float(mc.iloc[0] / n)
        diff = p - baseline
        specialty_idx = int(np.argmax(diff))
        specialty_cat = str(cats[specialty_idx])
        specialty_lift = float(diff[specialty_idx])
        rows.append({
            "player_id":   int(pid),
            "player_name": pid_to_name.get(int(pid), str(pid)),
            "primary_team": team,
            "n_fga":       int(n),
            "n_categories": int(len(p)),
            "H_player":    float(H_p),
            "H_baseline":  float(H_b),
            "spread_premium": float(spread),
            "top_category": top_cat,
            "top_category_share": top_cat_share,
            "specialty":    specialty_cat,
            "specialty_lift": specialty_lift,
        })
    adi = pd.DataFrame(rows)
    print(f"\n  qualifying shooters (n>={MIN_FGA}): {len(adi)}")
    adi.to_parquet(OUT_PATH, index=False)
    adi.to_csv(OUT_PATH.with_suffix(".csv"), index=False)
    print(f"wrote: {OUT_PATH}")

    cols = ["player_name","n_fga","n_categories","H_player","H_baseline","spread_premium",
             "top_category","top_category_share","specialty","specialty_lift"]
    print("\n=== TOP 25 by spread_premium — uses MANY action macros vs team ===")
    print(adi.sort_values("spread_premium", ascending=False)[cols].head(25).round(3).to_string(index=False))
    print("\n=== BOTTOM 25 by spread_premium — uses FEW action macros vs team ===")
    print(adi.sort_values("spread_premium", ascending=True)[cols].head(25).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
