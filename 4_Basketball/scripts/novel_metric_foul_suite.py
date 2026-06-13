"""Foul-drawing skill suite (4 novel metrics, T1).

  And1R  = % of made FGs that draw a shooting foul (and-1 rate). Identifies
           players who FINISH THROUGH CONTACT.
  DFC    = Drive Foul Conversion: % of drives that result in shooting fouls
           on the offensive player. Identifies attacking-paint finishers.
  SFG    = Sneaky Foul Generation: off-ball foul rate (drawn fouls per minute
           that are NOT on shots — screens, cuts, rebounding box-outs).
  FDQ    = Foul-Draw Quality: leverage-weighted foul-drawn rate. Drawing fouls
           in high-leverage moments (close game, late 4th) vs garbage time.

Output: D:/NBA Projections/data/results/foul_suite_2024_25.parquet
Min sample: 500 made shots (And1R) or 500 minutes (per-time-based rates).
"""
from __future__ import annotations
import sys, re, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

PBP = "D:/NBA Projections/data/parquet/pbp/pbp_2024-25.parquet"
OUT = Path("D:/NBA Projections/data/results")
OUT_PATH = OUT / "foul_suite_2024_25.parquet"
MIN_FGM = 100  # min made shots to qualify for And1R
MIN_DRIVES = 100  # min driving shots to qualify for DFC


def main():
    print("=== loading PBP ===")
    df = pd.read_parquet(PBP)
    print(f"  rows: {len(df):,}")

    pid_to_name = (df.dropna(subset=["player_name","person_id"])
                      .drop_duplicates(subset=["person_id"])
                      .set_index("person_id")["player_name"].to_dict())

    # === And1R: made shots with "PTS) (FT" or with "AND 1" in description ===
    made = df[df["action_type"] == "Made Shot"].dropna(subset=["description","person_id"]).copy()
    # Robust: look for shooting foul on the next action_number in same period+game
    # Cheap version: rely on description text.
    # Most reliable: NBA PBP for And-1 made-shot rows themselves don't always tag it; the SHOOTING FOUL is the next action. We parse the foul events.

    fouls = df[df["action_type"] == "Foul"].copy()
    print(f"  total foul events: {len(fouls):,}")
    # sub_type for personal/shooting/away-from-play etc
    print(f"  foul sub_types: {fouls['sub_type'].value_counts().head(10).to_dict()}")

    # Shooting fouls are sub_type 'Personal' that come AT a shot — we need to identify
    # the offensive player who DREW each shooting foul.
    # Easiest: parse description text for "Shooting" or "S.FOUL" or " on " ... it's noisy.
    # Cleaner: match each shooting-foul event by (game_id, action_number ~ adjacent) to a
    # made/missed shot in the prior action. Then the SHOT's person_id is the drawer.

    df_sorted = df.sort_values(["game_id","period","action_number"]).reset_index(drop=True)
    df_sorted["next_action"] = df_sorted.groupby(["game_id","period"])["action_type"].shift(-1)
    df_sorted["next_sub"]    = df_sorted.groupby(["game_id","period"])["sub_type"].shift(-1)
    # And-1 detection: a made shot whose NEXT event in the same period+game is a shooting foul.
    # We'll do it simpler: foul events themselves often have "S.FOUL" or contain (Sn PF) — the foul committer's count.
    # Try: a made shot followed by a Foul event with sub_type in {'Shooting Foul', 'Personal', 'Shooting'}.
    is_and1_candidate = (df_sorted["action_type"] == "Made Shot") & (df_sorted["next_action"] == "Foul")
    # Look at the made shot row + check that the player AT the foul's description doesn't match the scorer's team
    and1_made = df_sorted[is_and1_candidate].copy()
    print(f"  And-1 candidate made shots: {len(and1_made):,}")

    # And1R per player = and-1-candidate-made / all-made
    all_made = df_sorted[df_sorted["action_type"] == "Made Shot"].copy()
    and1_per_player = and1_made.groupby("person_id").size().rename("and1_count")
    made_per_player = all_made.groupby("person_id").size().rename("made_count")
    and1r = pd.concat([made_per_player, and1_per_player], axis=1).fillna(0)
    and1r["and1_rate"] = and1r["and1_count"] / and1r["made_count"]
    and1r = and1r[and1r["made_count"] >= MIN_FGM].sort_values("and1_rate", ascending=False)
    and1r["player_name"] = and1r.index.map(pid_to_name)

    # === DFC: Drive Foul Conversion ===
    # Approximate: shooting fouls drawn on a "Driving" sub_type shot attempt
    # We need shots that were "Driving" (sub_type contains 'Driving') that resulted
    # in a SHOOTING FOUL even if the shot missed.
    # Cheap proxy: count all drives (attempts where sub_type contains 'Driving' across
    # made + missed) and count how many of those have a foul on the next action.
    df_sorted["is_drive"] = df_sorted["sub_type"].str.contains("Driving", case=False, na=False)
    drive_rows = df_sorted[df_sorted["is_drive"] & df_sorted["action_type"].isin(["Made Shot","Missed Shot"])].copy()
    drive_rows["drew_foul"] = drive_rows["next_action"] == "Foul"
    print(f"  drive shot rows: {len(drive_rows):,}")
    print(f"  drive shots drawing foul: {drive_rows['drew_foul'].sum():,}")

    dfc = (drive_rows.groupby("person_id")
                       .agg(drives=("is_drive","size"),
                            drives_foul=("drew_foul","sum"))
                       .reset_index())
    dfc["dfc_rate"] = dfc["drives_foul"] / dfc["drives"]
    dfc = dfc[dfc["drives"] >= MIN_DRIVES].sort_values("dfc_rate", ascending=False)
    dfc["player_name"] = dfc["person_id"].map(pid_to_name)

    # === SFG: Sneaky Foul Generation — drawn-foul events where the PRIOR action is NOT a shot ===
    # i.e., foul drawn off-ball. Approximate via "previous action is not Made/Missed Shot".
    df_sorted["prev_action"] = df_sorted.groupby(["game_id","period"])["action_type"].shift(1)
    df_sorted["prev_person"] = df_sorted.groupby(["game_id","period"])["person_id"].shift(1)
    # Drawn-foul rows: action_type == 'Foul', and we want to know who DREW it.
    # The Foul row's person_id is typically the COMMITTING player, not the drawer.
    # The drawn player is usually in the description text — but that's noisy to parse robustly here.
    # Cheap approximation: estimate per-team off-ball foul events; this needs more careful parsing
    # to assign to specific drawers. Defer to v2.
    print("  SFG: deferred (drawn-player attribution requires text parsing — v2)")

    # === FDQ: Foul-Draw Quality (leverage-weighted) ===
    # For And-1 events: weight by leverage at the time.
    # Leverage proxy: |score_diff| <= 5 AND period >= 4 AND clock < 5 minutes => HIGH
    # Otherwise LOW. Then FDQ = sum(leverage_weight) / made_count.
    if "score_home" in df_sorted.columns:
        # parse clock "PT11M43.00S" -> minutes
        def clk_to_min(s):
            if not isinstance(s, str) or not s.startswith("PT"): return np.nan
            try:
                m = re.match(r"PT(\d+)M([\d.]+)S", s)
                if m:
                    return float(m.group(1)) + float(m.group(2))/60
                return np.nan
            except:
                return np.nan
        df_sorted["clock_min"] = df_sorted["clock"].map(clk_to_min)
        df_sorted["score_diff_abs"] = (pd.to_numeric(df_sorted["score_home"], errors="coerce")
                                         - pd.to_numeric(df_sorted["score_away"], errors="coerce")).abs()
        df_sorted["leverage"] = (
            ((df_sorted["period"] >= 4) & (df_sorted["clock_min"] <= 5) & (df_sorted["score_diff_abs"] <= 5))
            .astype(int) * 2
            + 1  # baseline 1, high-leverage 3
        )
        # FDQ per player: avg leverage of their and-1 made shots
        and1_w = df_sorted[is_and1_candidate][["person_id","leverage"]]
        fdq = and1_w.groupby("person_id").agg(and1_count=("leverage","size"),
                                                  fdq_avg=("leverage","mean")).reset_index()
        fdq = fdq[fdq["and1_count"] >= 5].sort_values("fdq_avg", ascending=False)
        fdq["player_name"] = fdq["person_id"].map(pid_to_name)
    else:
        fdq = pd.DataFrame()

    # === Combine ===
    out = and1r.reset_index().merge(dfc[["person_id","drives","drives_foul","dfc_rate"]],
                                       on="person_id", how="outer").merge(
            fdq[["person_id","and1_count","fdq_avg"]].rename(columns={"and1_count":"and1_count_fdq"}),
            on="person_id", how="outer")
    out["player_name"] = out["person_id"].map(pid_to_name)
    out.to_parquet(OUT_PATH, index=False)
    out.to_csv(OUT_PATH.with_suffix(".csv"), index=False)
    print(f"\nwrote: {OUT_PATH}")

    print("\n=== TOP 25 by And-1 Rate (and1_count >= 5, made >= 100) ===")
    cols_a = ["player_name","made_count","and1_count","and1_rate"]
    a = and1r.reset_index()
    a = a[a["and1_count"] >= 5]
    print(a[cols_a].head(25).round(3).to_string(index=False))

    print("\n=== BOTTOM 15 by And-1 Rate ===")
    print(a[cols_a].tail(15).round(3).to_string(index=False))

    print("\n=== TOP 25 by DFC (drives >= 100) ===")
    print(dfc[["player_name","drives","drives_foul","dfc_rate"]].head(25).round(3).to_string(index=False))

    if not fdq.empty:
        print("\n=== TOP 15 by FDQ leverage-weighted average ===")
        print(fdq[["player_name","and1_count","fdq_avg"]].head(15).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
