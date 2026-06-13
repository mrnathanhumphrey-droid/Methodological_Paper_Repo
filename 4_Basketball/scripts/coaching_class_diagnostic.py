"""Add coaching_change as a class candidate; rerun per-stat noise-floor.

Two coaching flags to test:
  - new_hc_this_season  (binary: team's HC differs from prior season)
  - mid_season_change   (binary: HC was replaced mid-season — usually performance signal)

For each (stat, flag) pair, compute SNR on 23-24 cohort PTS/etc residuals.
Compare to existing top-1 classes to see if coaching-change is the new winner
for any stat.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "scripts")

from pathlib import Path
import numpy as np
import pandas as pd

from ablation_harness import load_baseline

REPO = Path(".")
PQ = REPO / "data" / "parquet"
STATS = ["PTS", "REB", "AST", "STL", "BLK", "TOV", "FTA", "FTM"]


def main():
    base = load_baseline()
    base["nba_api_id"] = base["nba_api_id"].astype(int)

    # Per-player team_2324
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    s23 = box[box["season"] == "2023-24"]
    team_23 = s23.groupby("nba_api_id")["team_abbr"].agg(
        lambda x: x.value_counts().idxmax()).reset_index()
    team_23.columns = ["nba_api_id", "team_2324"]
    df = base.merge(team_23, on="nba_api_id", how="left")

    # Coaching flags for 2023-24
    cf = pd.read_parquet(PQ / "coaching_change_flags.parquet")
    cf_23 = cf[cf["season"] == "2023-24"][["team_abbr", "new_coach_this_season",
                                              "mid_season_change", "new_hire_type"]]
    df = df.merge(cf_23, left_on="team_2324", right_on="team_abbr", how="left")
    df["new_coach_this_season"] = df["new_coach_this_season"].fillna(False)
    df["mid_season_change"] = df["mid_season_change"].fillna(False)

    # Per-stat residuals
    for s in STATS:
        proj, actual = f"{s}_proj", f"{s}_actual"
        if proj in df.columns and actual in df.columns:
            df[f"{s}_residual"] = df[actual] - df[proj]

    # Coverage stats
    print(f"Cohort: {len(df)}")
    print(f"On team with new HC in 23-24: {df['new_coach_this_season'].sum()}")
    print(f"On team with mid-season HC change in 23-24: {df['mid_season_change'].sum()}")
    print(f"Teams with new HC in 23-24:")
    new_hc = cf_23[cf_23["new_coach_this_season"]]
    if len(new_hc) > 0:
        print(new_hc[["team_abbr", "new_hire_type"]].to_string(index=False))
    print(f"Teams with mid-season change:")
    msc = cf_23[cf_23["mid_season_change"]]
    if len(msc) > 0:
        print(msc[["team_abbr"]].to_string(index=False))

    # Noise floor for each (stat, coaching flag)
    def nf(df, cls, res_col):
        sub = df.dropna(subset=[cls, res_col]).copy()
        grouped = sub.groupby(cls, observed=True)[res_col].agg(["mean", "count"]).reset_index()
        grouped = grouped[grouped["count"] >= 2]
        if len(grouped) < 2:
            return None
        sd_obs = grouped["mean"].std(ddof=1)
        var = sub[res_col].var(ddof=1)
        n_per = grouped["count"].mean()
        se = np.sqrt(var / n_per)
        snr = sd_obs / se if se > 0 else np.nan
        return {"snr": snr, "means": dict(zip(grouped[cls], grouped["mean"])),
                "counts": dict(zip(grouped[cls], grouped["count"]))}

    print("\n" + "=" * 78)
    print("COACHING-CLASS PER-STAT SNR (23-24 cohort)")
    print("=" * 78)
    print(f"{'stat':<5}  {'class':<24}  {'SNR':>5}  verdict   class effect")
    print("-" * 78)
    for s in STATS:
        for c in ["new_coach_this_season", "mid_season_change"]:
            r = nf(df, c, f"{s}_residual")
            if r is None:
                continue
            v = ("REAL" if r["snr"] >= 1.5
                 else "marginal" if r["snr"] >= 1.05
                 else "noise")
            t = r["means"].get(True, np.nan)
            f = r["means"].get(False, np.nan)
            n_t = r["counts"].get(True, 0)
            n_f = r["counts"].get(False, 0)
            print(f"{s:<5}  {c:<24}  {r['snr']:>5.2f}  {v:<8}  "
                  f"True n={n_t}: {t:+.3f}  False n={n_f}: {f:+.3f}")

    # Compare to existing top-1 winners from per_stat_class_snr_matrix
    print("\n" + "=" * 78)
    print("COMPARE TO EXISTING TOP-1 CLASS PER STAT")
    print("=" * 78)
    snr_existing = pd.read_parquet(PQ / "per_stat_class_snr_matrix.parquet")
    print(f"{'stat':<5}  {'existing top class':<24}  {'existing SNR':>12}  "
          f"{'coach SNR':>10}  {'coach beats?':>14}")
    print("-" * 80)
    for s in STATS:
        existing = snr_existing[snr_existing["stat"] == s].sort_values(
            "snr", ascending=False)
        if len(existing) == 0:
            continue
        top = existing.iloc[0]
        # Best coaching SNR for this stat
        coach_snrs = []
        for c in ["new_coach_this_season", "mid_season_change"]:
            r = nf(df, c, f"{s}_residual")
            if r is not None:
                coach_snrs.append((c, r["snr"]))
        if not coach_snrs:
            continue
        coach_snrs.sort(key=lambda x: -x[1])
        best_coach_cls, best_coach_snr = coach_snrs[0]
        beats = "YES" if best_coach_snr > top["snr"] else "no"
        print(f"{s:<5}  {top['class']:<24}  {top['snr']:>12.2f}  "
              f"{best_coach_snr:>10.2f}  ({best_coach_cls}) {beats}")


if __name__ == "__main__":
    main()
