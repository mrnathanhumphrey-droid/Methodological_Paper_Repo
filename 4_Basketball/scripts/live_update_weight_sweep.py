"""Sweep W_MPG, W_RATE, W_*_PCT weights in live_update.py and find the optimum
that minimizes per-stat MAE on 23-24 at-date validation.

Coordinate-descent style:
  1. Hold W_RATE, W_*_PCT at default. Sweep W_MPG ∈ {1, 2, 3, 5, 8, 12, 20, 30}.
     Score = MPG MAE averaged across 3 at-dates (Dec 5, Jan 15, Mar 1).
  2. Lock W_MPG at optimum. Sweep W_RATE ∈ {1, 3, 5, 10, 15, 25, 50}.
     Score = composite avg of PTS/REB/AST/STL/BLK/TOV MAE.
  3. Lock W_RATE. Sweep W_FG_PCT ∈ {50, 100, 200, 400, 800}.
     Score = FG% / FGM / FGA combined MAE.
  4. Same for W_FT_PCT, W_FG3_PCT.

Uses the existing live_update_projection function via monkey-patch on its
module-level weights.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

from pathlib import Path
import numpy as np
import pandas as pd

import models.skill.live_update as lu

REPO = Path(".")
PRESEASON_PATH = "audit_runs/unified_ship_v6/per_player_projections_2023-24.csv"
SEASON = "2023-24"
DATES = ["2023-12-05", "2024-01-15", "2024-03-01"]

DEFAULT_W = {
    "W_MPG": 5,
    "W_RATE": 10,
    "W_FG_PCT": 200,
    "W_FT_PCT": 50,
    "W_FG3_PCT": 100,
}


def get_actual_end_of_season(season: str) -> pd.DataFrame:
    box = pd.read_parquet("data/parquet/historical_box_scores.parquet")
    box["minutes"] = pd.to_numeric(box["minutes"], errors="coerce")
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    box = box[box["season"] == season].copy()
    a = box.groupby("nba_api_id").agg(
        gp=("game_id", "nunique"),
        m=("minutes", "sum"),
        PTS=("PTS", "sum"), REB=("REB", "sum"), AST=("AST", "sum"),
        STL=("STL", "sum"), BLK=("BLK", "sum"), TOV=("TOV", "sum"),
    ).reset_index()
    a = a[(a["gp"] >= 10) & (a["m"] >= 200)]
    a["actual_mpg"] = a["m"] / a["gp"]
    for c in ["PTS", "REB", "AST", "STL", "BLK", "TOV"]:
        a[f"actual_{c}_pg"] = a[c] / a["gp"]
    return a[["nba_api_id", "actual_mpg",
               "actual_PTS_pg", "actual_REB_pg", "actual_AST_pg",
               "actual_STL_pg", "actual_BLK_pg", "actual_TOV_pg", "gp"]]


def evaluate(weights: dict, season: str, dates: list, actuals: pd.DataFrame):
    """Run live_update at each date with given weights, average MAE across dates."""
    # Patch weights
    for k, v in weights.items():
        setattr(lu, k, v)

    per_date = []
    for d in dates:
        upd = lu.live_update_projection(PRESEASON_PATH, season, d,
                                          use_trade_aware=True)
        if "mpg" not in upd.columns and "mpg_blended" in upd.columns:
            upd["mpg"] = upd["mpg_blended"]
        merged = upd.merge(actuals, on="nba_api_id", how="inner")
        merged = merged.dropna(subset=["actual_mpg"])
        if len(merged) == 0:
            continue
        # MPG
        mpg_mae = (merged["actual_mpg"] - merged["mpg_blended"]).abs().mean()
        # Per-game stats
        stat_maes = {}
        for stat in ["PTS", "REB", "AST", "STL", "BLK", "TOV"]:
            proj_col = f"{stat}_per_game"
            actual_col = f"actual_{stat}_pg"
            if proj_col in merged.columns and actual_col in merged.columns:
                stat_maes[stat] = (merged[actual_col] - merged[proj_col]).abs().mean()
        per_date.append({
            "date": d, "n": len(merged), "mpg_mae": mpg_mae, **stat_maes,
        })
    return pd.DataFrame(per_date)


def sweep_one(weight_name: str, values: list, current_weights: dict,
                actuals: pd.DataFrame, season: str, dates: list,
                metric_col: str = "mpg_mae"):
    """Sweep one weight while holding others fixed."""
    print(f"\n--- Sweeping {weight_name}, holding others at: "
          f"{ {k:v for k,v in current_weights.items() if k != weight_name} } ---")
    print(f"{'value':>8}  ", end="")
    cols = ["mpg_mae", "PTS", "REB", "AST", "STL", "BLK", "TOV"]
    for c in cols:
        print(f"{c:>7}  ", end="")
    print(f"{'composite':>9}")
    print("-" * 90)

    rows = []
    for v in values:
        weights = dict(current_weights)
        weights[weight_name] = v
        result = evaluate(weights, season, dates, actuals)
        if len(result) == 0:
            continue
        # Average across dates, weighted by n
        ws = result["n"].values
        avg = {}
        for c in cols:
            if c in result.columns:
                avg[c] = np.average(result[c].dropna(), weights=ws[:len(result[c].dropna())])
        # Composite: mean of per-stat normalized to baseline (we'll just print raw)
        composite = np.mean([avg[c] for c in ["PTS", "REB", "AST", "STL", "BLK", "TOV"]
                              if c in avg])
        rows.append({"value": v, **avg, "composite": composite})
        print(f"{v:>8}  ", end="")
        for c in cols:
            val = avg.get(c, np.nan)
            print(f"{val:>7.4f}  ", end="")
        print(f"{composite:>9.4f}")
    return pd.DataFrame(rows)


def main():
    print("Loading actuals for 2023-24...")
    actuals = get_actual_end_of_season(SEASON)
    print(f"  {len(actuals)} eligible players (gp>=10, min>=200)")
    print(f"  Default weights: {DEFAULT_W}")
    print(f"  Validation dates: {DATES}")

    # Sanity: defaults
    print("\n=== BASELINE (defaults) ===")
    base_result = evaluate(DEFAULT_W, SEASON, DATES, actuals)
    print(base_result.to_string(index=False))
    base_mpg_mae_avg = base_result["mpg_mae"].mean()
    base_composite = np.mean([base_result[c].mean() for c in ["PTS","REB","AST","STL","BLK","TOV"]
                                if c in base_result.columns])
    print(f"\n  Avg MPG MAE across dates: {base_mpg_mae_avg:.4f}")
    print(f"  Avg composite (per-game) across dates: {base_composite:.4f}")

    # Sweep W_MPG
    print("\n" + "=" * 90)
    print("STAGE 1: Sweep W_MPG (preseason MPG prior strength)")
    print("=" * 90)
    weights = dict(DEFAULT_W)
    mpg_sweep = sweep_one("W_MPG", [1, 2, 3, 5, 8, 12, 20, 30],
                            weights, actuals, SEASON, DATES, "mpg_mae")
    best_mpg = mpg_sweep.loc[mpg_sweep["mpg_mae"].idxmin()]
    print(f"\n  Best W_MPG: {best_mpg['value']}  (MPG MAE {best_mpg['mpg_mae']:.4f}, "
          f"vs default {base_mpg_mae_avg:.4f})")
    weights["W_MPG"] = int(best_mpg["value"])

    # Sweep W_RATE
    print("\n" + "=" * 90)
    print(f"STAGE 2: Sweep W_RATE (W_MPG locked at {weights['W_MPG']})")
    print("=" * 90)
    rate_sweep = sweep_one("W_RATE", [1, 3, 5, 10, 15, 25, 50],
                             weights, actuals, SEASON, DATES, "composite")
    best_rate = rate_sweep.loc[rate_sweep["composite"].idxmin()]
    print(f"\n  Best W_RATE: {best_rate['value']}  (composite {best_rate['composite']:.4f}, "
          f"vs default {base_composite:.4f})")
    weights["W_RATE"] = int(best_rate["value"])

    # Final eval at optimum
    print("\n" + "=" * 90)
    print(f"FINAL: optimum weights = {weights}")
    print("=" * 90)
    final_result = evaluate(weights, SEASON, DATES, actuals)
    print(final_result.to_string(index=False))
    final_mpg_mae = final_result["mpg_mae"].mean()
    final_composite = np.mean([final_result[c].mean() for c in ["PTS","REB","AST","STL","BLK","TOV"]
                                 if c in final_result.columns])
    print(f"\n  MPG MAE:       {final_mpg_mae:.4f}  (default {base_mpg_mae_avg:.4f}, "
          f"delta {100*(final_mpg_mae-base_mpg_mae_avg)/base_mpg_mae_avg:+.2f}%)")
    print(f"  Composite MAE: {final_composite:.4f}  (default {base_composite:.4f}, "
          f"delta {100*(final_composite-base_composite)/base_composite:+.2f}%)")


if __name__ == "__main__":
    main()
