"""STD — Shot-Type Diversity (novel offensive metric, T1).

Per player, Shannon entropy of their shot distribution across the 7 SHOT_ZONE_BASIC
zones (Restricted Area, In The Paint Non-RA, Mid-Range, Above the Break 3,
Left Corner 3, Right Corner 3, Backcourt).

Same v2 framework as PSI:
  - Min sample (FGA >= 200) kills small-N inflation
  - Baseline = TEAM shot-zone distribution (the natural offensive profile)
  - spread_premium = H_player - H_team
      > 0  player has MORE diverse shot diet than team profile (versatile)
      < 0  player is MORE SPECIALIZED than team profile (one-track)

Output: per-player STD with team-baseline-normalized diversity + concentration
specialty (which zone the player overrepresents vs team).

Face-validity bet:
  TOP (versatile): Jokic / LeBron / KAT / Tatum / Doncic-type all-around scorers
  BOTTOM (specialized): pure spot-up shooters (corner-3 only) OR pure rim
    attackers (Capela/Drummond) — players with NARROW shot diets
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
OUT_PATH = OUT / "std_2024_25.parquet"
MIN_FGA = 200


def main():
    print("=== loading shotchart ===")
    df = pd.read_parquet(SHOT)
    print(f"  rows: {len(df):,}")
    # Determine each player's primary team (modal TEAM_ID)
    primary = (df.groupby("PLAYER_ID")["TEAM_ID"]
                  .agg(lambda s: s.value_counts().idxmax())
                  .reset_index().rename(columns={"TEAM_ID":"primary_team"}))
    df = df.merge(primary, on="PLAYER_ID")
    df = df[df["TEAM_ID"] == df["primary_team"]]  # filter to shots on primary team

    # Team-level zone distribution
    team_zone = df.groupby(["TEAM_ID","SHOT_ZONE_BASIC"]).size().reset_index(name="team_shots")
    team_total = team_zone.groupby("TEAM_ID")["team_shots"].sum().reset_index().rename(columns={"team_shots":"team_total"})
    team_zone = team_zone.merge(team_total, on="TEAM_ID")
    team_zone["team_share"] = team_zone["team_shots"] / team_zone["team_total"]

    pid_to_name = df.drop_duplicates(subset=["PLAYER_ID"]).set_index("PLAYER_ID")["PLAYER_NAME"].to_dict()

    rows = []
    for pid, sub in df.groupby("PLAYER_ID"):
        n = len(sub)
        if n < MIN_FGA: continue
        team = int(sub["primary_team"].iloc[0])
        zone_counts = sub["SHOT_ZONE_BASIC"].value_counts()
        zones = zone_counts.index.values
        p = zone_counts.values / n

        # Baseline: team distribution on the SAME support
        team_sub = team_zone[team_zone["TEAM_ID"] == team].set_index("SHOT_ZONE_BASIC")["team_share"]
        baseline = np.array([team_sub.get(z, 1e-6) for z in zones])
        baseline = baseline / baseline.sum()

        H_p = -np.sum(p * np.log(p + 1e-12))
        H_b = -np.sum(baseline * np.log(baseline + 1e-12))
        kl  = float(np.sum(p * np.log((p + 1e-12) / (baseline + 1e-12))))
        spread_premium = H_p - H_b

        hhi = float(np.sum(p**2))
        top_zone = str(zone_counts.index[0])
        top_zone_share = float(zone_counts.iloc[0] / n)
        # Specialty = which zone is most overrepresented vs team
        diff = p - baseline
        specialty_idx = int(np.argmax(diff))
        specialty_zone = str(zones[specialty_idx])
        specialty_lift = float(diff[specialty_idx])

        # FG% overall (for context)
        fg_pct = float(sub["SHOT_MADE_FLAG"].mean())
        # 3PT volume share (interpretive)
        is_three = sub["SHOT_TYPE"].eq("3PT Field Goal").mean()

        rows.append({
            "player_id":   int(pid),
            "player_name": pid_to_name.get(int(pid), str(pid)),
            "primary_team": team,
            "n_fga":       int(n),
            "H_player":    float(H_p),
            "H_baseline":  float(H_b),
            "spread_premium": float(spread_premium),
            "kl_to_baseline": float(kl),
            "hhi":         float(hhi),
            "top_zone":    top_zone,
            "top_zone_share": top_zone_share,
            "specialty_zone": specialty_zone,
            "specialty_lift": specialty_lift,
            "fg_pct":      fg_pct,
            "three_share": float(is_three),
        })
    std = pd.DataFrame(rows)
    print(f"  qualifying shooters (n>={MIN_FGA}): {len(std)}")

    std.to_parquet(OUT_PATH, index=False)
    std.to_csv(OUT_PATH.with_suffix(".csv"), index=False)
    print(f"\nwrote: {OUT_PATH}")

    cols_show = ["player_name","n_fga","H_player","H_baseline","spread_premium",
                  "top_zone","top_zone_share","specialty_zone","specialty_lift",
                  "three_share","fg_pct"]

    print("\n=== TOP 25 by spread_premium — VERSATILE (more diverse than team profile) ===")
    print(std.sort_values("spread_premium", ascending=False)[cols_show].head(25).round(3).to_string(index=False))

    print("\n=== BOTTOM 25 by spread_premium — SPECIALIZED (more concentrated than team profile) ===")
    print(std.sort_values("spread_premium", ascending=True)[cols_show].head(25).round(3).to_string(index=False))

    # Breakdown by specialty
    print("\n=== Bottom-25 specialists by SPECIALTY ZONE ===")
    bot = std.sort_values("spread_premium", ascending=True).head(60).copy()
    print(bot["specialty_zone"].value_counts().to_string())


if __name__ == "__main__":
    main()
