"""Phase 3 option 4 V2: per-game PBP-based garbage-time truncation.

For each game, identify garbage-time start moment from PBP:
  - Period >= 4 AND |margin| > GARBAGE_MARGIN AND seconds_remaining < GARBAGE_TIME
Then derive team-game ortg/drtg/poss using only PRE-GARBAGE plays.

Compare rolling-EMA over truncated stats vs rolling-EMA over full stats.

Test on 24-25 only (PBP available).
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import re
import numpy as np
import pandas as pd
from pathlib import Path

PQ = Path("data/parquet")
SEASON = "2024-25"
ALPHA_BEST = 0.10

# Garbage-time rule (Clutch.fan / Cleaning the Glass style)
GARBAGE_MARGIN = 20    # |margin| > 20 ...
GARBAGE_TIME_REMAIN = 300  # ... in last 5 minutes of period >= 4
PERIOD_GARBAGE = 4     # only applies to period 4+

CLOCK_RE = re.compile(r"PT(\d+)M([\d.]+)S")


def parse_clock(s):
    """ISO 8601 duration like 'PT12M00.00S' -> seconds_remaining."""
    if pd.isna(s):
        return np.nan
    m = CLOCK_RE.match(s)
    if not m:
        return np.nan
    return float(m.group(1)) * 60 + float(m.group(2))


def find_garbage_cutoff(pbp_game: pd.DataFrame):
    """For a single game's PBP (sorted by action_number), find the action_number at which
    garbage time begins. Returns None if game never enters garbage time."""
    p = pbp_game.copy()
    p["score_home"] = pd.to_numeric(p["score_home"], errors="coerce").ffill().fillna(0)
    p["score_away"] = pd.to_numeric(p["score_away"], errors="coerce").ffill().fillna(0)
    p["margin"] = (p["score_home"] - p["score_away"]).abs()
    p["sec_remain"] = p["clock"].map(parse_clock)
    mask = (p["period"] >= PERIOD_GARBAGE) & (p["margin"] > GARBAGE_MARGIN) & (p["sec_remain"] < GARBAGE_TIME_REMAIN)
    if not mask.any():
        return None
    return int(p.loc[mask, "action_number"].min())


def derive_team_pre_garbage_stats(pbp: pd.DataFrame, box: pd.DataFrame):
    """Compute team-game stats only from pre-garbage plays.

    Approach: shot-by-shot via PBP for FGA/FG3A/etc. is doable but complex.
    Simpler: identify garbage-time fraction per team-game via PBP, then deflate box stats proportionally.

    The deflate uses: pre_garbage_time / total_time as scale factor for FGA, FTA, TOV, OREB, PTS.
    Assumes per-minute rates are the same in garbage as non-garbage (likely false; this is an
    approximation that DOES adjust totals but doesn't fix efficiency biases).
    """
    pbp_sorted = pbp.sort_values(["game_id", "action_number"])

    # Per game: find garbage cutoff action_number + duration of pre-garbage time
    # Game total minutes: 48 (or 53/58 with OT). Use PBP to estimate.
    cutoffs = []
    for gid, g in pbp_sorted.groupby("game_id"):
        cut = find_garbage_cutoff(g)
        # If no garbage, frac = 1.0
        # If garbage, estimate fraction of game time pre-garbage
        if cut is None:
            cutoffs.append({"game_id": gid, "pre_garbage_frac": 1.0})
            continue
        # Compute time elapsed at cutoff
        # Sum (period - 1) full quarters * 12 min + (12 - sec_remain/60) of current period
        cutoff_row = g[g["action_number"] == cut].iloc[0]
        sec_remain = parse_clock(cutoff_row["clock"])
        period = cutoff_row["period"]
        # Total elapsed: full periods completed × 12 min + current period elapsed
        elapsed_sec = (period - 1) * 12 * 60 + (12 * 60 - sec_remain)
        # Total game time: use last PBP row's period to determine OTs
        last_period = int(g["period"].max())
        total_sec = max(last_period, 4) * 12 * 60  # ignores OT durations; rough
        if last_period > 4:
            total_sec = 4 * 12 * 60 + (last_period - 4) * 5 * 60  # OTs are 5 min
        cutoffs.append({"game_id": gid, "pre_garbage_frac": min(1.0, elapsed_sec / total_sec)})

    cutoff_df = pd.DataFrame(cutoffs)
    return cutoff_df


def aggregate_team_game_with_dampen(box, cutoffs):
    """Aggregate box to team-game then DAMPEN by pre_garbage_frac per game."""
    box = box.copy()
    box["game_id"] = box["game_id"].astype(str)
    cutoffs["game_id"] = cutoffs["game_id"].astype(str)
    box = box.merge(cutoffs, on="game_id", how="left")
    box["pre_garbage_frac"] = box["pre_garbage_frac"].fillna(1.0)
    # Multiply per-game player stats by the fraction; then aggregate
    for col in ["PTS", "FGA", "FTA", "OREB", "TOV"]:
        box[f"{col}_dampened"] = box[col] * box["pre_garbage_frac"]

    agg = box.groupby(["season", "game_id", "team_abbr", "game_date", "is_home"]).agg(
        pts=("PTS_dampened", "sum"),
        fga=("FGA_dampened", "sum"),
        fta=("FTA_dampened", "sum"),
        oreb=("OREB_dampened", "sum"),
        tov=("TOV_dampened", "sum"),
        # Also keep actual pts for OUTCOME
        pts_actual=("PTS", "sum"),
        pre_garbage_frac=("pre_garbage_frac", "first"),
    ).reset_index()
    agg["poss"] = agg["fga"] + 0.44 * agg["fta"] - agg["oreb"] + agg["tov"]
    agg["ortg"] = agg["pts"] / agg["poss"] * 100
    return agg


def attach_opponent(tg):
    opp = tg[["season", "game_id", "team_abbr", "pts", "poss"]].rename(
        columns={"team_abbr": "opp_team", "pts": "opp_pts", "poss": "opp_poss"})
    j = tg.merge(opp, on=["season", "game_id"], how="left")
    j = j[j["team_abbr"] != j["opp_team"]].copy()
    j["drtg"] = j["opp_pts"] / j["opp_poss"] * 100
    return j


def add_ema(df, alpha):
    df = df.sort_values(["season", "team_abbr", "game_date"]).copy()
    grp = df.groupby(["season", "team_abbr"])
    for c in ["ortg", "drtg", "poss"]:
        df[f"ema_{c}"] = grp[c].transform(
            lambda x: x.shift().ewm(alpha=alpha, min_periods=3, adjust=False).mean())
    return df


def evaluate(tg, pts_col, hc):
    opp = tg[["season", "game_id", "team_abbr", "ema_ortg", "ema_drtg", "ema_poss"]].rename(
        columns={"team_abbr": "opp_team",
                 "ema_ortg": "opp_ema_ortg", "ema_drtg": "opp_ema_drtg", "ema_poss": "opp_ema_poss"})
    m = tg.merge(opp, on=["season", "game_id", "opp_team"], how="left")
    m = m.dropna(subset=["ema_ortg", "ema_drtg", "ema_poss",
                          "opp_ema_ortg", "opp_ema_drtg", "opp_ema_poss"]).copy()
    m["game_pace"] = (m["ema_poss"] + m["opp_ema_poss"]) / 2
    m["team_eff"] = (m["ema_ortg"] + m["opp_ema_drtg"]) / 2
    m["pred"] = m["team_eff"] * m["game_pace"] / 100 + np.where(m["is_home"], hc / 2, -hc / 2)
    m["err"] = m["pred"] - m[pts_col]

    home = m[m["is_home"]].copy()
    away = m[~m["is_home"]].copy()
    g = home[["game_id", "pred", pts_col]].rename(columns={"pred": "h", pts_col: "ha"}).merge(
        away[["game_id", "pred", pts_col]].rename(columns={"pred": "a", pts_col: "aa"}),
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

    print("Computing per-game garbage-time fraction from PBP ...")
    cutoffs = derive_team_pre_garbage_stats(pbp, box)
    print(f"  Games processed: {len(cutoffs)}")
    print(f"  Games with garbage time: {(cutoffs['pre_garbage_frac'] < 1.0).sum()}")
    print(f"  Mean pre-garbage frac: {cutoffs['pre_garbage_frac'].mean():.4f}")
    print(f"  Frac dist of games with garbage:")
    sub = cutoffs[cutoffs["pre_garbage_frac"] < 1.0]
    if len(sub) > 0:
        print(sub["pre_garbage_frac"].describe())

    # Baseline: aggregate without dampening
    print("\nBaseline (no garbage filter):")
    box_base = box.copy()
    box_base["pre_garbage_frac"] = 1.0
    for col in ["PTS", "FGA", "FTA", "OREB", "TOV"]:
        box_base[f"{col}_dampened"] = box_base[col]
    agg_base = box_base.groupby(["season", "game_id", "team_abbr", "game_date", "is_home"]).agg(
        pts=("PTS_dampened", "sum"), fga=("FGA_dampened", "sum"), fta=("FTA_dampened", "sum"),
        oreb=("OREB_dampened", "sum"), tov=("TOV_dampened", "sum"),
        pts_actual=("PTS", "sum"),
    ).reset_index()
    agg_base["poss"] = agg_base["fga"] + 0.44 * agg_base["fta"] - agg_base["oreb"] + agg_base["tov"]
    agg_base["ortg"] = agg_base["pts"] / agg_base["poss"] * 100
    agg_base = attach_opponent(agg_base)
    hc = float((agg_base[agg_base["is_home"]].set_index("game_id")["pts_actual"]
                - agg_base[~agg_base["is_home"]].set_index("game_id")["pts_actual"]).dropna().mean())
    print(f"  Home court: {hc:+.3f}")
    agg_base = add_ema(agg_base, ALPHA_BEST)
    base = evaluate(agg_base, "pts_actual", hc)
    print(f"  win_pct {base['win_pct']:.4f}, margin_rmse {base['margin_rmse']:.4f}, "
          f"team_pts_mae {base['team_pts_mae']:.4f}")

    # V2: dampened stats
    print("\nV2: garbage-time dampened (pre-garbage proportion of each team-game)")
    agg_v2 = aggregate_team_game_with_dampen(box, cutoffs)
    agg_v2 = attach_opponent(agg_v2)
    agg_v2 = add_ema(agg_v2, ALPHA_BEST)
    v2 = evaluate(agg_v2, "pts_actual", hc)
    print(f"  win_pct {v2['win_pct']:.4f}, margin_rmse {v2['margin_rmse']:.4f}, "
          f"team_pts_mae {v2['team_pts_mae']:.4f}")
    print(f"  delta win_pct: {(v2['win_pct'] - base['win_pct']) * 100:+.3f}pp")
    print(f"  delta margin_rmse: {v2['margin_rmse'] - base['margin_rmse']:+.4f}")


if __name__ == "__main__":
    main()
