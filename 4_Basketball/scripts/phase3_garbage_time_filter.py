"""Phase 3 option 4: garbage-time filter for rolling stats.

Two variants tested:
  V1 (blowout exclusion): Exclude games with |final_margin| > 20 from rolling computation.
  V2 (PBP truncation): Per-game, identify garbage-time start from PBP (period 4, |margin|>20,
      time<5min). Reaggregate team stats up to that moment.

Test on 24-25 only (PBP available). Compare to all-games rolling baseline.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from pathlib import Path

PQ = Path("data/parquet")
SEASON = "2024-25"
ALPHA_BEST = 0.10  # from prior step


def aggregate_team_game(box):
    agg = box.groupby(["season", "game_id", "team_abbr", "game_date", "is_home"]).agg(
        pts=("PTS", "sum"), fga=("FGA", "sum"), fta=("FTA", "sum"),
        oreb=("OREB", "sum"), tov=("TOV", "sum"),
    ).reset_index()
    agg["poss"] = agg["fga"] + 0.44 * agg["fta"] - agg["oreb"] + agg["tov"]
    agg["ortg"] = agg["pts"] / agg["poss"] * 100
    return agg


def attach_opponent(tg):
    opp = tg[["season", "game_id", "team_abbr", "pts", "poss"]].rename(
        columns={"team_abbr": "opp_team", "pts": "opp_pts", "poss": "opp_poss"}
    )
    j = tg.merge(opp, on=["season", "game_id"], how="left")
    j = j[j["team_abbr"] != j["opp_team"]].copy()
    j["drtg"] = j["opp_pts"] / j["opp_poss"] * 100
    return j


def home_court(tg):
    h = tg[tg["is_home"]].set_index("game_id")["pts"]
    a = tg[~tg["is_home"]].set_index("game_id")["pts"]
    return float((h - a).dropna().mean())


def compute_final_margin_from_pbp(pbp):
    """For each game, get final score_home - score_away from last action."""
    pbp = pbp.sort_values(["game_id", "action_number"])
    last = pbp.groupby("game_id").tail(1)[["game_id", "score_home", "score_away"]].copy()
    last["score_home"] = pd.to_numeric(last["score_home"], errors="coerce")
    last["score_away"] = pd.to_numeric(last["score_away"], errors="coerce")
    last["final_margin"] = last["score_home"] - last["score_away"]
    return last[["game_id", "final_margin"]]


def add_ema(df, alpha):
    df = df.sort_values(["season", "team_abbr", "game_date"]).copy()
    grp = df.groupby(["season", "team_abbr"])
    for c in ["ortg", "drtg", "poss"]:
        df[f"ema_{c}"] = grp[c].transform(
            lambda x: x.shift().ewm(alpha=alpha, min_periods=3, adjust=False).mean())
    return df


def evaluate(tg, hc):
    """Apply Tier 1B with EMA stats, evaluate win pct + RMSE."""
    opp = tg[["season", "game_id", "team_abbr", "ema_ortg", "ema_drtg", "ema_poss"]].rename(
        columns={"team_abbr": "opp_team",
                 "ema_ortg": "opp_ema_ortg", "ema_drtg": "opp_ema_drtg", "ema_poss": "opp_ema_poss"}
    )
    m = tg.merge(opp, on=["season", "game_id", "opp_team"], how="left")
    m = m.dropna(subset=["ema_ortg", "ema_drtg", "ema_poss",
                          "opp_ema_ortg", "opp_ema_drtg", "opp_ema_poss"]).copy()
    m["game_pace"] = (m["ema_poss"] + m["opp_ema_poss"]) / 2
    m["team_eff"] = (m["ema_ortg"] + m["opp_ema_drtg"]) / 2
    m["pred"] = m["team_eff"] * m["game_pace"] / 100 + np.where(m["is_home"], hc / 2, -hc / 2)
    m["err"] = m["pred"] - m["pts"]

    home = m[m["is_home"]].copy()
    away = m[~m["is_home"]].copy()
    g = home[["game_id", "pred", "pts"]].rename(columns={"pred": "h", "pts": "ha"}).merge(
        away[["game_id", "pred", "pts"]].rename(columns={"pred": "a", "pts": "aa"}),
        on="game_id", how="inner")
    g["pm"] = g["h"] - g["a"]
    g["am"] = g["ha"] - g["aa"]
    g["c"] = (g["pm"] > 0) == (g["am"] > 0)
    return {
        "n_team_games": len(m),
        "team_pts_mae": m["err"].abs().mean(),
        "n_games": len(g),
        "margin_rmse": float(np.sqrt(((g["pm"] - g["am"]) ** 2).mean())),
        "win_pct": float(g["c"].mean()),
    }


def main():
    print("Loading 24-25 box + PBP ...")
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box = box[(box["season"] == SEASON) & (box["season_type"] == "Regular Season")].copy()
    box["game_date"] = pd.to_datetime(box["game_date"])

    pbp = pd.read_parquet(PQ / "pbp" / f"pbp_{SEASON}.parquet")

    tg = aggregate_team_game(box)
    tg = attach_opponent(tg)
    hc = home_court(tg)
    print(f"  Home court: {hc:+.3f}")

    # Baseline: EMA 0.10 on all games
    tg_baseline = add_ema(tg, ALPHA_BEST)
    baseline = evaluate(tg_baseline, hc)
    print(f"\nBaseline (EMA 0.10, all games): win_pct {baseline['win_pct']:.4f}, "
          f"margin_rmse {baseline['margin_rmse']:.4f}, team_pts_mae {baseline['team_pts_mae']:.4f}")

    # V1: blowout exclusion
    print("\nV1: Blowout exclusion (final |margin| > THRESHOLD games excluded from rolling)")
    fm = compute_final_margin_from_pbp(pbp)
    fm["game_id"] = fm["game_id"].astype(str)
    tg["game_id"] = tg["game_id"].astype(str)
    tg_with_fm = tg.merge(fm, on="game_id", how="left")
    tg_with_fm["abs_margin"] = tg_with_fm["final_margin"].abs()

    for THRESH in [40, 30, 25, 20, 15]:
        # Mask: only include games where this team-game's |margin| <= THRESH
        tg_filt = tg_with_fm[tg_with_fm["abs_margin"] <= THRESH].copy()
        # But we still need to predict ALL games -- the filter only affects ROLLING input
        # Build EMA from filtered, then merge back to ALL games for prediction
        tg_filt = add_ema(tg_filt, ALPHA_BEST)
        # Merge EMA back to all games (for prediction)
        ema_cols = ["season", "game_id", "team_abbr", "ema_ortg", "ema_drtg", "ema_poss"]
        # ... but ema_* in tg_filt is computed against ONLY filtered games per team
        # For prediction on game G, need EMA computed pre-G from all PRIOR filtered games
        # This is tricky because we want to predict G even if G was a blowout.
        # Simpler: filter at the rolling step, predict all games.
        # Need to recompute EMA on filtered data and re-attach. Use the latest EMA available per team
        # before each game's date.

        # Per (team, game_date), find latest EMA from filtered tg
        tg_filt_sorted = tg_filt.sort_values(["season", "team_abbr", "game_date"])
        # ema_* is already shifted (computed from PRIOR games only)
        # Take all rows of tg_filt with their ema_* cols, merge to ALL games by (season, team_abbr) and using game_date <
        ema_history = tg_filt_sorted[["season", "team_abbr", "game_date",
                                        "ema_ortg", "ema_drtg", "ema_poss"]].dropna()

        # For each row in tg (all games), find latest ema_* with game_date <= row's game_date
        tg_pred = tg.copy()
        tg_pred = tg_pred.sort_values(["season", "team_abbr", "game_date"])
        # Use merge_asof
        ema_sorted = ema_history.sort_values(["season", "team_abbr", "game_date"])
        tg_pred = tg_pred.sort_values(["game_date"])
        ema_sorted = ema_sorted.sort_values(["game_date"])
        tg_pred = pd.merge_asof(
            tg_pred, ema_sorted,
            by=["season", "team_abbr"],
            on="game_date", direction="backward", allow_exact_matches=False
        )
        tg_pred = tg_pred.sort_values(["season", "team_abbr", "game_date"])
        res = evaluate(tg_pred, hc)
        delta_wp = (res["win_pct"] - baseline["win_pct"]) * 100
        delta_rmse = res["margin_rmse"] - baseline["margin_rmse"]
        print(f"  thresh={THRESH:>3}: win_pct {res['win_pct']:.4f} ({delta_wp:+.2f}pp)  "
              f"margin_rmse {res['margin_rmse']:.4f} ({delta_rmse:+.4f})  n_games={res['n_games']}")


if __name__ == "__main__":
    main()
