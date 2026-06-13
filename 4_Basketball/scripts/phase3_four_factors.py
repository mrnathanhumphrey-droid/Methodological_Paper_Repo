"""Phase 3 lever #3: Four Factors decomposition.

Dean Oliver's Four Factors of offensive/defensive efficiency:
  eFG% = (FGM + 0.5 * FG3M) / FGA
  TOV% = TOV / (FGA + 0.44 * FTA + TOV)
  ORB% = OREB / (OREB + opp_DREB)
  FTr  = FTA / FGA  (free throw rate)

Default weights (Dean Oliver): 0.4 eFG, 0.25 TOV, 0.20 ORB, 0.15 FTr.

Approach:
  Build per-team-game four-factor metrics (offense + defense).
  EMA each at alpha=0.10.
  Predict team_ortg via 4F-derived expected efficiency vs aggregate ortg.

Compare to Tier 1B+EMA baseline (66.71% combined).
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from pathlib import Path

PQ = Path("data/parquet")
SEASONS = ["2024-25", "2025-26"]
ALPHA = 0.10


def aggregate_team_game(box):
    """Per (game_id, team_abbr) aggregate raw stats incl FGM, FG3M, FTM, DREB."""
    agg = box.groupby(["season", "game_id", "team_abbr", "game_date", "is_home"]).agg(
        pts=("PTS", "sum"),
        fgm=("FGM", "sum"), fga=("FGA", "sum"),
        fg3m=("FG3M", "sum"), fg3a=("FG3A", "sum"),
        ftm=("FTM", "sum"), fta=("FTA", "sum"),
        oreb=("OREB", "sum"), dreb=("DREB", "sum"),
        tov=("TOV", "sum"),
    ).reset_index()
    # Possessions (per Dean Oliver standard)
    agg["poss"] = agg["fga"] + 0.44 * agg["fta"] - agg["oreb"] + agg["tov"]
    agg["ortg"] = agg["pts"] / agg["poss"] * 100
    # Four factors -- offense
    agg["efg"] = (agg["fgm"] + 0.5 * agg["fg3m"]) / agg["fga"].clip(lower=1)
    agg["tov_pct"] = agg["tov"] / (agg["fga"] + 0.44 * agg["fta"] + agg["tov"]).clip(lower=1)
    agg["ftr"] = agg["fta"] / agg["fga"].clip(lower=1)
    # ORB% needs opp DREB -- compute via join later
    return agg


def attach_opp_stats(tg):
    opp = tg[["season", "game_id", "team_abbr",
              "pts", "poss", "efg", "tov_pct", "ftr", "oreb", "dreb"]].rename(
        columns={"team_abbr": "opp_team",
                 "pts": "opp_pts", "poss": "opp_poss",
                 "efg": "opp_efg", "tov_pct": "opp_tov_pct", "ftr": "opp_ftr",
                 "oreb": "opp_oreb", "dreb": "opp_dreb"})
    j = tg.merge(opp, on=["season", "game_id"], how="left")
    j = j[j["team_abbr"] != j["opp_team"]].copy()
    # ORB% = own OREB / (own OREB + opp DREB)
    j["orb_pct"] = j["oreb"] / (j["oreb"] + j["opp_dreb"]).clip(lower=1)
    # Defensive four factors (perspective: what we give up)
    j["d_efg"] = j["opp_efg"]
    j["d_tov_pct"] = j["opp_tov_pct"]
    j["d_orb_pct"] = j["opp_oreb"] / (j["opp_oreb"] + j["dreb"]).clip(lower=1)
    j["d_ftr"] = j["opp_ftr"]
    j["drtg"] = j["opp_pts"] / j["opp_poss"] * 100
    return j


def add_ema_within_season(df, alpha):
    df = df.sort_values(["season", "team_abbr", "game_date"]).copy()
    grp = df.groupby(["season", "team_abbr"])
    for c in ["efg", "tov_pct", "orb_pct", "ftr",
              "d_efg", "d_tov_pct", "d_orb_pct", "d_ftr",
              "ortg", "drtg", "poss"]:
        df[f"ema_{c}"] = grp[c].transform(
            lambda x: x.shift().ewm(alpha=alpha, min_periods=3, adjust=False).mean())
    return df


def four_factor_expected_ortg(df, weights=(0.40, 0.25, 0.20, 0.15)):
    """Compute expected ORTG from team's offense 4F vs opp's defense 4F.

    For each factor F: relative_strength_F = ema_F_offense - ema_F_defense_opp
    Combine: efficiency_index = w_efg * Δ_efg - w_tov * Δ_tov + w_orb * Δ_orb + w_ftr * Δ_ftr
    (note tov is "good when high gives more turnovers", so for offensive we want low tov_pct;
     subtract: offense_tov - opp_def_tov = (own TOV%) - (forced TOV%) -- but wait that's wrong direction)

    Cleanest: predict the four factors then plug into a known ortg formula.
    Approach:
      pred_efg = (ema_efg_offense + ema_d_efg_opp_defense_relative) — implies expected eFG today
      We'll use simple averaging for each factor between team's offense and opp's defense:
        pred_efg = (ema_efg + ema_d_efg_opp) / 2
        pred_tov_pct = (ema_tov_pct + ema_d_tov_pct_opp) / 2
        pred_orb_pct = (ema_orb_pct + ema_d_orb_pct_opp) / 2  (note opp's d_orb_pct = opp gave up our OREB)
        pred_ftr = (ema_ftr + ema_d_ftr_opp) / 2

    Then ORTG via Dean Oliver approximation:
        pts_per_100 ~= (eFG% * 2 * FGA + FTM) / poss * 100
      Simpler: pts_per_poss = eFG% * (1 - TOV%) * 2 + FTr * 0.76  (rough; not exact)

    For first pass, use regression coefs from literature:
      ortg ≈ 100 + 200*(eFG% - league_avg_eFG) - 250*(TOV% - league_avg_TOV) +
              200*(ORB% - league_avg_ORB) + 50*(FTr - league_avg_FTr)
    (Hand-calibrated rough coefs; will refine if signal looks real)
    """
    LEAGUE_AVG = {"efg": 0.540, "tov_pct": 0.135, "orb_pct": 0.270, "ftr": 0.250}
    COEFS = {"efg": 200.0, "tov_pct": -250.0, "orb_pct": 100.0, "ftr": 50.0}

    df = df.copy()
    for fac in ["efg", "tov_pct", "orb_pct", "ftr"]:
        df[f"pred_{fac}"] = (df[f"ema_{fac}"] + df[f"ema_d_{fac}_opp"]) / 2

    df["ortg_4f"] = 110.0  # league average baseline
    for fac, coef in COEFS.items():
        df["ortg_4f"] += coef * (df[f"pred_{fac}"] - LEAGUE_AVG[fac])
    return df


def attach_opp_ema(df):
    """For each team-game, attach opponent's EMA stats."""
    ema_cols = [c for c in df.columns if c.startswith("ema_")]
    keep = ["season", "game_id", "team_abbr"] + ema_cols
    opp = df[keep].rename(
        columns={"team_abbr": "opp_team", **{c: f"{c}_opp" for c in ema_cols}}
    )
    return df.merge(opp, on=["season", "game_id", "opp_team"], how="left")


def main():
    print("Loading multi-season box ...")
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box = box[(box["season"].isin(SEASONS)) & (box["season_type"] == "Regular Season")].copy()
    box["game_date"] = pd.to_datetime(box["game_date"])

    tg = aggregate_team_game(box)
    tg = attach_opp_stats(tg)
    print(f"Team-games: {len(tg)}")

    # Per-season home court
    hc_per_season = {}
    for s in SEASONS:
        ss = tg[tg["season"] == s]
        h = ss[ss["is_home"]].set_index("game_id")["pts"]
        a = ss[~ss["is_home"]].set_index("game_id")["pts"]
        hc_per_season[s] = float((h - a).dropna().mean())

    tg = add_ema_within_season(tg, ALPHA)
    tg = attach_opp_ema(tg)

    # Method A: predict team_ortg via 4F decomposition
    tg = four_factor_expected_ortg(tg)

    # Method B: baseline (ortg + opp_drtg)/2 with EMA (the locked Tier 1B+EMA)
    tg["ortg_baseline"] = (tg["ema_ortg"] + tg["ema_drtg_opp"]) / 2

    # Filter to rows with valid EMA
    tg_v = tg.dropna(subset=["ema_ortg", "ema_drtg_opp", "ema_efg", "ema_tov_pct",
                              "ema_orb_pct", "ema_ftr",
                              "ema_d_efg_opp", "ema_d_tov_pct_opp",
                              "ema_d_orb_pct_opp", "ema_d_ftr_opp",
                              "ema_poss", "ema_poss_opp"]).copy()

    # Pace from EMA
    tg_v["game_pace"] = (tg_v["ema_poss"] + tg_v["ema_poss_opp"]) / 2
    tg_v["hc_half"] = tg_v["season"].map({s: v / 2 for s, v in hc_per_season.items()})

    print()
    print(f"Method A (4F decomposition): pred_pts = ortg_4f × game_pace / 100 + hc/2")
    tg_v["pts_4f"] = tg_v["ortg_4f"] * tg_v["game_pace"] / 100 + np.where(
        tg_v["is_home"], tg_v["hc_half"], -tg_v["hc_half"])
    print(f"Method B (baseline): pred_pts = (ortg + opp_drtg)/2 × game_pace / 100 + hc/2")
    tg_v["pts_baseline"] = tg_v["ortg_baseline"] * tg_v["game_pace"] / 100 + np.where(
        tg_v["is_home"], tg_v["hc_half"], -tg_v["hc_half"])

    # Per-team errors
    for col, label in [("pts_baseline", "Baseline (ortg + opp_drtg)/2"),
                        ("pts_4f", "Method A: 4F decomposition")]:
        err = tg_v[col] - tg_v["pts"]
        print(f"\n  {label}:")
        print(f"    Per-team PTS MAE: {err.abs().mean():.4f}  RMSE: {np.sqrt((err**2).mean()):.4f}  bias: {err.mean():+.4f}")

    # Game-level
    print()
    print("=" * 75)
    print("Game-level comparison")
    print("=" * 75)
    home = tg_v[tg_v["is_home"]].copy()
    away = tg_v[~tg_v["is_home"]].copy()
    for col, label in [("pts_baseline", "Tier 1B+EMA baseline"),
                        ("pts_4f", "4F decomposition")]:
        g = home[["season", "game_id", col, "pts"]].rename(
            columns={col: "h", "pts": "ha"}
        ).merge(
            away[["game_id", col, "pts"]].rename(columns={col: "a", "pts": "aa"}),
            on="game_id", how="inner"
        )
        g["pm"] = g["h"] - g["a"]
        g["am"] = g["ha"] - g["aa"]
        g["c"] = (g["pm"] > 0) == (g["am"] > 0)
        print(f"\n{label}:")
        for s in SEASONS + ["combined"]:
            sub = g if s == "combined" else g[g["season"] == s]
            if len(sub) == 0:
                continue
            rmse = np.sqrt(((sub["pm"] - sub["am"]) ** 2).mean())
            print(f"  {s} (n={len(sub)}): win_pct {sub['c'].mean():.4f}  margin_rmse {rmse:.4f}")


if __name__ == "__main__":
    main()
