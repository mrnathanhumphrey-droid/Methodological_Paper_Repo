"""Build prior-season-rate FG3M baseline ships for 22-23 and 24-25.

The phase4_v4_quadratic_tq_g pipeline only produced FG3M for 23-24 target. Stan
refits for FG3M on other seasons are out of compute budget (~30h each per
project memory). This baseline uses each player's PRIOR REGULAR SEASON FG3M
per-game rate from historical_box_scores as a proxy projection, formatted to
match the phase4 ship schema so the backtest pipeline can consume it
identically.

Output:
  audit_runs/fg3m_prior_season_baseline_2022-23/per_player_projections.csv
  audit_runs/fg3m_prior_season_baseline_2024-25/per_player_projections.csv

Schema matches phase4 ships:
  nba_api_id, name, proj_mean, proj_sd, proj_q05, proj_q25, proj_q75,
  proj_q95, actual, actual_minutes, actual_games, error, abs_error,
  z_error, stat, test_season

proj_sd is set to per-player FG3M sd across regular-season games of the prior
season (a Poisson-like proxy). Quantiles derived as proj_mean +/- z*sd assuming
Gaussian for backtest use.

Caveats documented in BACKTEST_PLAYOFFS_22_25.md §6: this baseline is not a Stan
fit; it omits aging, team-quality, and gravity adjustments. Multipliers fit on
this baseline reflect the mean shift from regular season to playoff, not from a
v4-lite Stan projection to playoff.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"

PRIOR_SEASON = {
    "2022-23": "2021-22",
    "2024-25": "2023-24",
}


def _prior_season_per_game_rate(target_season: str) -> pd.DataFrame:
    prior = PRIOR_SEASON[target_season]
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box = box[box["season"] == prior].copy()
    box["FG3M"] = pd.to_numeric(box["FG3M"], errors="coerce").fillna(0)
    box["minutes"] = pd.to_numeric(box["minutes"], errors="coerce").fillna(0)
    # Filter to non-zero minutes (DNPs not informative)
    box = box[box["minutes"] > 0]

    grouped = box.groupby("nba_api_id").agg(
        gp=("game_id", "nunique"),
        total_min=("minutes", "sum"),
        fg3m_total=("FG3M", "sum"),
        fg3m_sd_per_game=("FG3M", "std"),
    ).reset_index()
    grouped["FG3M_per_game"] = grouped["fg3m_total"] / grouped["gp"]
    grouped["proj_sd"] = grouped["fg3m_sd_per_game"].fillna(
        grouped["fg3m_sd_per_game"].median()
    )
    return grouped


def _attach_target_season_actuals(df: pd.DataFrame, target_season: str) -> pd.DataFrame:
    """Attach the player's ACTUAL FG3M per-game from the regular-season game log
    of the target season (used as the 'actual' column in phase4 ship schema).
    """
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box = box[box["season"] == target_season].copy()
    box["FG3M"] = pd.to_numeric(box["FG3M"], errors="coerce").fillna(0)
    box["minutes"] = pd.to_numeric(box["minutes"], errors="coerce").fillna(0)
    box = box[box["minutes"] > 0]
    actuals = box.groupby("nba_api_id").agg(
        actual_games=("game_id", "nunique"),
        actual_minutes=("minutes", "sum"),
        actual_total=("FG3M", "sum"),
    ).reset_index()
    actuals["actual"] = actuals["actual_total"] / actuals["actual_games"]
    return df.merge(actuals[["nba_api_id", "actual", "actual_minutes",
                              "actual_games"]],
                    on="nba_api_id", how="left")


def _attach_player_name(df: pd.DataFrame) -> pd.DataFrame:
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    name_col = "full_name" if "full_name" in meta.columns else (
        "player_name" if "player_name" in meta.columns else None
    )
    if name_col is None:
        df["name"] = ""
        return df
    nm = meta[["nba_api_id", name_col]].drop_duplicates("nba_api_id")
    nm = nm.rename(columns={name_col: "name"})
    return df.merge(nm, on="nba_api_id", how="left")


def build_for_season(target_season: str) -> pd.DataFrame:
    rate = _prior_season_per_game_rate(target_season)
    rate = _attach_target_season_actuals(rate, target_season)
    rate = _attach_player_name(rate)

    df = pd.DataFrame({
        "nba_api_id": rate["nba_api_id"].astype(int),
        "name": rate["name"].fillna(""),
        "proj_mean": rate["FG3M_per_game"].astype(float),
        "proj_sd": rate["proj_sd"].astype(float),
        "actual": rate["actual"].astype(float),
        "actual_minutes": rate["actual_minutes"].astype(float),
        "actual_games": rate["actual_games"].astype(float),
    })
    # Gaussian quantiles
    z05, z25, z75, z95 = -1.6449, -0.6745, 0.6745, 1.6449
    df["proj_q05"] = df["proj_mean"] + z05 * df["proj_sd"]
    df["proj_q25"] = df["proj_mean"] + z25 * df["proj_sd"]
    df["proj_q75"] = df["proj_mean"] + z75 * df["proj_sd"]
    df["proj_q95"] = df["proj_mean"] + z95 * df["proj_sd"]
    df["error"] = df["actual"] - df["proj_mean"]
    df["abs_error"] = df["error"].abs()
    df["z_error"] = df["error"] / df["proj_sd"].where(df["proj_sd"] > 0, np.nan)
    df["stat"] = "FG3M"
    df["test_season"] = target_season

    # Drop rows missing actuals (didn't play target season's regular season)
    df = df.dropna(subset=["actual", "proj_mean"])
    df = df[(df["proj_mean"] >= 0) & (df["actual_games"] >= 5)]
    return df


def main():
    for target_season in ["2022-23", "2024-25"]:
        out_dir = REPO / "audit_runs" / f"fg3m_prior_season_baseline_{target_season}"
        out_dir.mkdir(parents=True, exist_ok=True)
        df = build_for_season(target_season)
        out_path = out_dir / "per_player_projections.csv"
        df.to_csv(out_path, index=False)
        print(f"Wrote {out_path}  ({len(df)} players)")
        print(f"  mean proj_mean: {df['proj_mean'].mean():.3f}")
        print(f"  mean actual:    {df['actual'].mean():.3f}")
        print(f"  MAE (RS->RS):   {df['abs_error'].mean():.3f}")


if __name__ == "__main__":
    main()
