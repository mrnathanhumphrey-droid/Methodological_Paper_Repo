"""Phase 3 option 3: ELO-style recency weighting (EMA instead of rolling-10g equal-weight).

Test α grid (smoothing factor) for EMA of team ortg/drtg/pace.
α corresponds to half-life via ln(2)/-ln(1-α). Smaller α = longer memory.

Compare against rolling-10g baseline on multi-season (24-25 + 25-26) n=2364.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from pathlib import Path

PQ = Path("data/parquet")
SEASONS = ["2024-25", "2025-26"]


def aggregate_team_game(box: pd.DataFrame) -> pd.DataFrame:
    agg = box.groupby(["season", "game_id", "team_abbr", "game_date", "is_home"]).agg(
        pts=("PTS", "sum"),
        fga=("FGA", "sum"),
        fta=("FTA", "sum"),
        oreb=("OREB", "sum"),
        tov=("TOV", "sum"),
    ).reset_index()
    agg["poss"] = agg["fga"] + 0.44 * agg["fta"] - agg["oreb"] + agg["tov"]
    agg["ortg"] = agg["pts"] / agg["poss"] * 100
    return agg


def attach_opponent(tg: pd.DataFrame) -> pd.DataFrame:
    opp = tg[["season", "game_id", "team_abbr", "pts", "poss"]].rename(
        columns={"team_abbr": "opp_team", "pts": "opp_pts", "poss": "opp_poss"}
    )
    joined = tg.merge(opp, on=["season", "game_id"], how="left")
    joined = joined[joined["team_abbr"] != joined["opp_team"]].copy()
    joined["drtg"] = joined["opp_pts"] / joined["opp_poss"] * 100
    return joined


def add_ema_within_season(df: pd.DataFrame, alpha: float) -> pd.DataFrame:
    """EMA with given alpha, computed within (season, team_abbr), pre-game (shift before EMA)."""
    df = df.sort_values(["season", "team_abbr", "game_date"]).copy()
    grp = df.groupby(["season", "team_abbr"])
    for col in ["ortg", "drtg", "poss"]:
        df[f"ema_{col}"] = grp[col].transform(
            lambda x: x.shift().ewm(alpha=alpha, min_periods=3, adjust=False).mean()
        )
    return df


def add_rolling_within_season(df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    """Equal-weight rolling baseline."""
    df = df.sort_values(["season", "team_abbr", "game_date"]).copy()
    grp = df.groupby(["season", "team_abbr"])
    for col in ["ortg", "drtg", "poss"]:
        df[f"roll_{col}"] = grp[col].transform(
            lambda x: x.shift().rolling(window=window, min_periods=3).mean())
    return df


def attach_opp_stats(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """Each team-game row gets opponent's stats with the given prefix."""
    cols = [f"{prefix}_{c}" for c in ["ortg", "drtg", "poss"]]
    opp = df[["season", "game_id", "team_abbr"] + cols].rename(
        columns={"team_abbr": "opp_team",
                 **{c: f"opp_{c}" for c in cols}}
    )
    return df.merge(opp, on=["season", "game_id", "opp_team"], how="left")


def home_court_advantage(df: pd.DataFrame, season: str) -> float:
    s = df[df["season"] == season]
    home_pts = s[s["is_home"]].set_index("game_id")["pts"]
    away_pts = s[~s["is_home"]].set_index("game_id")["pts"]
    margins = (home_pts - away_pts).dropna()
    return float(margins.mean())


def evaluate(tg_v, prefix, hc_per_season):
    tg = tg_v.copy()
    pace_col, ortg_col, drtg_col = f"{prefix}_poss", f"{prefix}_ortg", f"{prefix}_drtg"
    opp_pace, opp_ortg, opp_drtg = f"opp_{pace_col}", f"opp_{ortg_col}", f"opp_{drtg_col}"

    tg = tg.dropna(subset=[pace_col, ortg_col, drtg_col, opp_pace, opp_ortg, opp_drtg]).copy()
    tg["hc_half"] = tg["season"].map({s: v / 2 for s, v in hc_per_season.items()})
    tg["game_pace"] = (tg[pace_col] + tg[opp_pace]) / 2
    tg["team_eff"] = (tg[ortg_col] + tg[opp_drtg]) / 2
    tg["team_pts_pred"] = tg["team_eff"] * tg["game_pace"] / 100 + np.where(
        tg["is_home"], tg["hc_half"], -tg["hc_half"]
    )
    tg["err"] = tg["team_pts_pred"] - tg["pts"]

    home = tg[tg["is_home"]].copy()
    away = tg[~tg["is_home"]].copy()
    games = home[["season", "game_id", "team_pts_pred", "pts"]].rename(
        columns={"team_pts_pred": "home_pred", "pts": "home_actual"}
    ).merge(
        away[["game_id", "team_pts_pred", "pts"]].rename(
            columns={"team_pts_pred": "away_pred", "pts": "away_actual"}),
        on="game_id", how="inner"
    )
    games["pred_margin"] = games["home_pred"] - games["away_pred"]
    games["actual_margin"] = games["home_actual"] - games["away_actual"]
    games["correct"] = (games["pred_margin"] > 0) == (games["actual_margin"] > 0)
    err_m = games["pred_margin"] - games["actual_margin"]

    return {
        "n_team_games": len(tg),
        "team_pts_mae": tg["err"].abs().mean(),
        "team_pts_rmse": np.sqrt((tg["err"] ** 2).mean()),
        "team_pts_bias": tg["err"].mean(),
        "n_games": len(games),
        "margin_rmse": np.sqrt((err_m ** 2).mean()),
        "margin_mae": err_m.abs().mean(),
        "margin_bias": err_m.mean(),
        "win_pct": games["correct"].mean(),
    }


def main():
    print("Loading multi-season box scores ...")
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box = box[(box["season"].isin(SEASONS)) & (box["season_type"] == "Regular Season")].copy()
    box["game_date"] = pd.to_datetime(box["game_date"])

    tg = aggregate_team_game(box)
    tg = attach_opponent(tg)

    hc_per_season = {s: home_court_advantage(tg, s) for s in SEASONS}
    print(f"Home court per season: {hc_per_season}")

    # Baseline: rolling-10g
    print("\nAdding rolling-10g baseline ...")
    tg_with = add_rolling_within_season(tg, window=10)
    tg_with = attach_opp_stats(tg_with, "roll")

    baseline = evaluate(tg_with, "roll", hc_per_season)
    print(f"  Rolling-10g baseline: win_pct {baseline['win_pct']:.2%}, margin_rmse {baseline['margin_rmse']:.4f}, team_pts_mae {baseline['team_pts_mae']:.4f}")

    # EMA grid
    print("\nTesting EMA grid:")
    print(f"  {'alpha':>6} {'half_life':>11} {'win_pct':>9} {'margin_rmse':>13} {'team_pts_mae':>14} {'n_games':>8}")
    print(f"  {'roll_10':>6} {'~5.0':>11} {baseline['win_pct']:>9.4f} {baseline['margin_rmse']:>13.4f} {baseline['team_pts_mae']:>14.4f} {baseline['n_games']:>8}  <-- baseline")

    rows = []
    for alpha in [0.05, 0.075, 0.10, 0.125, 0.15, 0.18, 0.20, 0.25, 0.30, 0.40]:
        tg_ema = add_ema_within_season(tg, alpha=alpha)
        tg_ema = attach_opp_stats(tg_ema, "ema")
        res = evaluate(tg_ema, "ema", hc_per_season)
        res["alpha"] = alpha
        res["half_life"] = np.log(2) / -np.log(1 - alpha)
        rows.append(res)
        print(f"  {alpha:>6.3f} {res['half_life']:>11.2f} {res['win_pct']:>9.4f} {res['margin_rmse']:>13.4f} {res['team_pts_mae']:>14.4f} {res['n_games']:>8}")

    df_ema = pd.DataFrame(rows)
    print()
    best_winpct = df_ema.loc[df_ema["win_pct"].idxmax()]
    print(f"Best win pct: alpha={best_winpct['alpha']}, win_pct={best_winpct['win_pct']:.4f}")
    best_rmse = df_ema.loc[df_ema["margin_rmse"].idxmin()]
    print(f"Best RMSE:    alpha={best_rmse['alpha']}, margin_rmse={best_rmse['margin_rmse']:.4f}")

    df_ema.to_csv(Path("audit_runs") / "phase3_elo_recency_grid.csv", index=False)


if __name__ == "__main__":
    main()
