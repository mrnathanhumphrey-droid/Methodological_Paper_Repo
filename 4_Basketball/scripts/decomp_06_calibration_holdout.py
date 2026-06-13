"""Honest calibration check on 2022-2023 rookies.

Retrain archetype priors and translation factors using ONLY 2014-2021 draft
years, then project 2022-2023 rookies and check what % land inside the 50/80/95
intervals we forecast.

Reports per-stat coverage rates. Well-calibrated = 50/80/95 hit rates near targets.
"""
from __future__ import annotations
import sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

PQ = Path("D:/NBA Projections/data/parquet")
HOLDOUT_YEARS = [2022, 2023]
TRAIN_MAX_YEAR = 2021
MIN_GP_Y1 = 25

STATS_PER36 = ["pts_per36", "reb_per36", "ast_per36", "stl_per36", "blk_per36",
                       "fg3m_per36", "tov_per36"]
EXTRA = ["mpg", "gp"]
ALL_STATS = STATS_PER36 + EXTRA


def main():
    print("=== loading ===")
    m = pd.read_parquet(PQ / "rookies_master.parquet")
    arch_all = pd.read_parquet(PQ / "rookie_archetypes.parquet")[["nba_api_id", "archetype"]]
    m = m.merge(arch_all, on="nba_api_id", how="left")

    train = m[(m["draft_year"] <= TRAIN_MAX_YEAR) & m["has_nba_y1"]
                       & (m["nba_y1_gp"] >= MIN_GP_Y1)].copy()
    holdout = m[m["draft_year"].isin(HOLDOUT_YEARS) & m["has_nba_y1"]
                         & (m["nba_y1_gp"] >= MIN_GP_Y1)].copy()
    print(f"  train rows: {len(train):,}  holdout rows: {len(holdout):,}")

    archetype_intervals = {}
    for arch_lbl, grp in train.groupby("archetype"):
        d = {"n": len(grp)}
        for stat in ALL_STATS:
            col = f"nba_y1_{stat}"
            if col in grp.columns:
                vals = grp[col].dropna()
                if len(vals) >= 5:
                    d[f"{stat}_p25"] = vals.quantile(0.25)
                    d[f"{stat}_p75"] = vals.quantile(0.75)
                    d[f"{stat}_p10"] = vals.quantile(0.10)
                    d[f"{stat}_p90"] = vals.quantile(0.90)
                    d[f"{stat}_p025"] = vals.quantile(0.025)
                    d[f"{stat}_p975"] = vals.quantile(0.975)
                    d[f"{stat}_mean"] = vals.mean()
        archetype_intervals[arch_lbl] = d

    print(f"  {len(archetype_intervals)} archetypes trained")

    results = []
    for _, row in holdout.iterrows():
        arch_lbl = row["archetype"]
        if arch_lbl not in archetype_intervals:
            continue
        ai = archetype_intervals[arch_lbl]
        for stat in ALL_STATS:
            actual_col = f"nba_y1_{stat}"
            if actual_col not in row.index:
                continue
            actual = row[actual_col]
            if pd.isna(actual):
                continue
            if f"{stat}_p25" not in ai:
                continue
            results.append({
                "player": row.get("player_name_raw"),
                "archetype": arch_lbl,
                "stat": stat,
                "actual": actual,
                "p025": ai[f"{stat}_p025"],
                "p10": ai[f"{stat}_p10"],
                "p25": ai[f"{stat}_p25"],
                "p75": ai[f"{stat}_p75"],
                "p90": ai[f"{stat}_p90"],
                "p975": ai[f"{stat}_p975"],
                "mean": ai[f"{stat}_mean"],
            })
    R = pd.DataFrame(results)

    R["in_50"] = (R["actual"] >= R["p25"]) & (R["actual"] <= R["p75"])
    R["in_80"] = (R["actual"] >= R["p10"]) & (R["actual"] <= R["p90"])
    R["in_95"] = (R["actual"] >= R["p025"]) & (R["actual"] <= R["p975"])
    R["err"] = R["actual"] - R["mean"]

    print(f"\n=== overall coverage (all stats) ===")
    print(f"  50% target: actual {R['in_50'].mean():.1%} (n={len(R)})")
    print(f"  80% target: actual {R['in_80'].mean():.1%}")
    print(f"  95% target: actual {R['in_95'].mean():.1%}")

    print(f"\n=== per-stat coverage ===")
    cov = R.groupby("stat").agg(
        n=("in_50", "size"),
        cov50=("in_50", "mean"),
        cov80=("in_80", "mean"),
        cov95=("in_95", "mean"),
        mae=("err", lambda s: s.abs().mean()),
        bias=("err", "mean"),
    ).round(3)
    print(cov.to_string())

    print(f"\n=== per-archetype coverage (50% interval hit rate) ===")
    arch_cov = R.groupby("archetype").agg(n=("in_50","size"), cov50=("in_50","mean"),
                                                                cov80=("in_80","mean"),
                                                                cov95=("in_95","mean")).round(3)
    print(arch_cov.to_string())


if __name__ == "__main__":
    main()
