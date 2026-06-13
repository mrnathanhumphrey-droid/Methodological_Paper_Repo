"""Validate minutes-weighted MPG redistribution vs the no-redistribution baseline.

For each clean-1-OUT team-game in the test season(s), score two predictions
of each ACTIVE player's actual minutes:

  - Baseline (no redistribution): predicted = expected_min (rolling 5-game prior)
  - Minutes-weighted: predicted = expected_min + freed × (expected_min / sum_active_expected_min)

Compute MAE of predicted vs actual on each method.

Test seasons: 2024-25 + 2025-26 (held out from cross-season calib at 22-23/23-24/24-25).
Actually we calibrate-free for this method, so we can validate on ANY season.
Using 23-24 + 24-25 + 25-26 as the test set for max sample.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

import numpy as np
import pandas as pd
from pathlib import Path

PQ = Path("data/parquet")
TEST_SEASONS = ["2023-24", "2024-25", "2025-26"]
MIN_OUT_EXPECTED_MIN = 18.0
ROLLING = 5
MIN_PRIOR = 3


def main():
    panel = pd.read_parquet(PQ / "mpg_redistribution_training_panel.parquet")
    panel["game_date"] = pd.to_datetime(panel["game_date"])
    print(f"Panel rows: {len(panel)}")
    panel_test = panel[panel["season"].isin(TEST_SEASONS)].copy()
    print(f"After season filter to {TEST_SEASONS}: {len(panel_test)}")

    # Identify clean-1-OUT team-games (test seasons only)
    inactive = panel_test[~panel_test["is_active"]].dropna(subset=["expected_min"])
    inactive = inactive[inactive["expected_min"] >= MIN_OUT_EXPECTED_MIN]
    grp = inactive.groupby(["team_abbr", "game_date"]).agg(
        n_heavy_out=("nba_api_id", "nunique"),
        out_pid=("nba_api_id", "first"),
        out_position=("position", "first"),
        out_expected_min=("expected_min", "first"),
    ).reset_index()
    clean = grp[grp["n_heavy_out"] == 1].copy()
    print(f"Clean-1-OUT team-games in test seasons: {len(clean)}")

    # Active players on those team-games
    active = panel_test[panel_test["is_active"]].dropna(subset=["expected_min"]).copy()
    rows = active.merge(
        clean[["team_abbr", "game_date", "out_pid", "out_expected_min"]],
        on=["team_abbr", "game_date"], how="inner"
    )
    rows = rows[rows["nba_api_id"] != rows["out_pid"]]
    print(f"Active-player rows: {len(rows)}")

    # Per (team, game_date): compute sum_active_expected
    team_sum = rows.groupby(["team_abbr", "game_date"])["expected_min"].sum().reset_index(
        name="sum_active_expected_min"
    )
    rows = rows.merge(team_sum, on=["team_abbr", "game_date"], how="left")

    # Baseline: predicted = expected_min
    rows["pred_baseline"] = rows["expected_min"]
    # Minutes-weighted: predicted = expected_min × (1 + freed / sum_active)
    rows["pred_mwt"] = rows["expected_min"] * (
        1.0 + rows["out_expected_min"] / rows["sum_active_expected_min"]
    )
    # Errors
    rows["err_baseline"] = rows["minutes"] - rows["pred_baseline"]
    rows["err_mwt"] = rows["minutes"] - rows["pred_mwt"]

    mae_base = rows["err_baseline"].abs().mean()
    mae_mwt = rows["err_mwt"].abs().mean()
    bias_base = rows["err_baseline"].mean()
    bias_mwt = rows["err_mwt"].mean()
    delta_pct = (mae_mwt - mae_base) / mae_base * 100

    print()
    print("=" * 70)
    print(f"MAE of predicted MPG on clean-1-OUT team-games (n={len(rows)})")
    print("=" * 70)
    print(f"  No redistribution baseline:    MAE={mae_base:.4f}  bias={bias_base:+.4f}")
    print(f"  Minutes-weighted (proposed):   MAE={mae_mwt:.4f}  bias={bias_mwt:+.4f}")
    print(f"  delta MAE pct: {delta_pct:+.2f}%   "
          f"({'IMPROVEMENT' if delta_pct < 0 else 'REGRESSION'})")

    # Break down by player's depth bin to see who benefits
    print()
    print("Per-depth-bin MAE breakdown:")
    print(f"  {'depth_bin':<10} {'n':>6} {'mae_base':>10} {'mae_mwt':>10} {'delta_%':>9}")
    for db, g in rows.groupby("depth_bin"):
        eb = g["err_baseline"].abs().mean()
        em = g["err_mwt"].abs().mean()
        dp = (em - eb) / eb * 100 if eb > 0 else 0
        print(f"  {int(db):<10} {len(g):>6} {eb:>10.4f} {em:>10.4f} {dp:>+8.2f}%")

    # Break down by player's actual minutes shift
    print()
    print("Per-shift-magnitude breakdown:")
    rows["shift_bin"] = pd.cut(rows["minutes"] - rows["expected_min"],
                                bins=[-100, -10, -3, 3, 10, 100],
                                labels=["big_dn", "mid_dn", "stable", "mid_up", "big_up"])
    for sb, g in rows.groupby("shift_bin", observed=True):
        eb = g["err_baseline"].abs().mean()
        em = g["err_mwt"].abs().mean()
        dp = (em - eb) / eb * 100 if eb > 0 else 0
        print(f"  {sb:<10} {len(g):>6} {eb:>10.4f} {em:>10.4f} {dp:>+8.2f}%")


if __name__ == "__main__":
    main()
