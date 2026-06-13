"""FDQ v2 — Foul-Draw Quality with raised threshold.

V1 used n_and1 >= 5 which let small-N players noise the top. V2 raises to
n_and1 >= 20 and also shrinks toward league-mean leverage to penalize
small-sample chuckers.

Output: D:/NBA Projections/data/results/fdq_v2_2024_25.parquet
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
OUT_PATH = OUT / "fdq_v2_2024_25.parquet"
MIN_AND1 = 20
SHRINK_LAMBDA = 20  # in units of and-1 events


def main():
    df = pd.read_parquet(PBP)
    df_sorted = df.sort_values(["game_id","period","action_number"]).reset_index(drop=True)
    df_sorted["next_action"] = df_sorted.groupby(["game_id","period"])["action_type"].shift(-1)
    is_and1 = (df_sorted["action_type"] == "Made Shot") & (df_sorted["next_action"] == "Foul")
    print(f"  And-1 candidates: {is_and1.sum():,}")

    # leverage
    def clk_to_min(s):
        if not isinstance(s, str) or not s.startswith("PT"): return np.nan
        m = re.match(r"PT(\d+)M([\d.]+)S", s)
        if m: return float(m.group(1)) + float(m.group(2))/60
        return np.nan
    df_sorted["clock_min"] = df_sorted["clock"].map(clk_to_min)
    df_sorted["score_home"] = pd.to_numeric(df_sorted["score_home"], errors="coerce")
    df_sorted["score_away"] = pd.to_numeric(df_sorted["score_away"], errors="coerce")
    df_sorted["score_diff_abs"] = (df_sorted["score_home"] - df_sorted["score_away"]).abs()
    df_sorted["leverage"] = (
        ((df_sorted["period"] >= 4) & (df_sorted["clock_min"] <= 5) & (df_sorted["score_diff_abs"] <= 5))
        .astype(int) * 2 + 1
    )

    pid_to_name = (df.dropna(subset=["player_name","person_id"])
                      .drop_duplicates(subset=["person_id"])
                      .set_index("person_id")["player_name"].to_dict())

    and1_df = df_sorted[is_and1][["person_id","leverage"]].copy()
    league_lev = float(and1_df["leverage"].mean())
    print(f"  league mean leverage on and-1s: {league_lev:.4f}")

    fdq = (and1_df.groupby("person_id")
                    .agg(and1_count=("leverage","size"),
                         fdq_avg=("leverage","mean"))
                    .reset_index())
    fdq["player_name"] = fdq["person_id"].map(pid_to_name)
    # Bayesian shrinkage
    n = fdq["and1_count"]
    fdq["fdq_shrunk"] = (n * fdq["fdq_avg"] + SHRINK_LAMBDA * league_lev) / (n + SHRINK_LAMBDA)
    fdq = fdq[fdq["and1_count"] >= MIN_AND1].sort_values("fdq_shrunk", ascending=False)

    fdq.to_parquet(OUT_PATH, index=False)
    fdq.to_csv(OUT_PATH.with_suffix(".csv"), index=False)
    print(f"  qualifying: {len(fdq)} players (n>={MIN_AND1})")
    print(f"\nwrote: {OUT_PATH}")

    cols = ["player_name","and1_count","fdq_avg","fdq_shrunk"]
    print("\n=== TOP 20 by shrunk FDQ ===")
    print(fdq[cols].head(20).round(4).to_string(index=False))
    print("\n=== BOTTOM 10 by shrunk FDQ ===")
    print(fdq[cols].tail(10).round(4).to_string(index=False))


if __name__ == "__main__":
    main()
