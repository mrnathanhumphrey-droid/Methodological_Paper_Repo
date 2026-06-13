"""Phase 3 levers 2/3/4 tested against locked blend (60% SRS + 40% Tier 1B+EMA).

Lever 2: SoS-corrected EMA
  Adjust each game's raw ortg by (league_avg_drtg - opp_drtg_at_that_time) so the team's
  rolling reflects "as if every opponent were average". Then EMA the adjusted series.
  Q: does this add signal BEYOND the SRS we already blend in?

Lever 3: Multiplicative defense
  team_eff = team_ortg × (opp_drtg / league_avg_drtg)
  vs current additive (team_ortg + opp_drtg) / 2
  Q: does the multiplicative form capture interactions the additive misses?

Lever 4: Streak/momentum
  ema_3 - ema_10 as a "current form differential" — if recent (last 3-5g) outperforms
  medium rolling, add positive momentum signal.

For each lever, two integrations tested:
  (a) replace EMA component in blend with lever variant
  (b) add lever output as extra adjustment to existing blend
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
ALPHA_FAST = 0.25  # for streak/momentum
MIN_GAMES_FOR_SRS = 5


def aggregate_team_game(box):
    agg = box.groupby(["season", "game_id", "team_abbr", "game_date", "is_home"]).agg(
        pts=("PTS", "sum"),
        fga=("FGA", "sum"), fta=("FTA", "sum"),
        oreb=("OREB", "sum"), tov=("TOV", "sum"),
    ).reset_index()
    agg["poss"] = agg["fga"] + 0.44 * agg["fta"] - agg["oreb"] + agg["tov"]
    agg["ortg"] = agg["pts"] / agg["poss"] * 100
    return agg


def attach_opp(tg):
    opp = tg[["season", "game_id", "team_abbr", "pts", "poss"]].rename(
        columns={"team_abbr": "opp_team", "pts": "opp_pts", "poss": "opp_poss"})
    j = tg.merge(opp, on=["season", "game_id"], how="left")
    j = j[j["team_abbr"] != j["opp_team"]].copy()
    j["drtg"] = j["opp_pts"] / j["opp_poss"] * 100
    j["margin"] = j["pts"] - j["opp_pts"]
    return j


def add_ema_within_season(df, alpha, suffix=""):
    df = df.sort_values(["season", "team_abbr", "game_date"]).copy()
    grp = df.groupby(["season", "team_abbr"])
    for c in ["ortg", "drtg", "poss"]:
        df[f"ema{suffix}_{c}"] = grp[c].transform(
            lambda x: x.shift().ewm(alpha=alpha, min_periods=3, adjust=False).mean())
    return df


def attach_opp_ema(df, suffix=""):
    cols = [f"ema{suffix}_{c}" for c in ["ortg", "drtg", "poss"]]
    opp = df[["season", "game_id", "team_abbr"] + cols].rename(
        columns={"team_abbr": "opp_team", **{c: f"opp_{c}" for c in cols}})
    return df.merge(opp, on=["season", "game_id", "opp_team"], how="left")


def solve_srs(tg_before, reg=0.01):
    teams = sorted(set(tg_before["team_abbr"]) | set(tg_before["opp_team"]))
    n = len(teams)
    idx = {t: i for i, t in enumerate(teams)}
    A = np.eye(n)
    m = np.zeros(n)
    means = tg_before.groupby("team_abbr")["margin"].mean()
    for t, i in idx.items():
        if t in means.index:
            m[i] = means[t]
        sub = tg_before[tg_before["team_abbr"] == t]
        if len(sub) > 0:
            opp_counts = sub.groupby("opp_team").size()
            n_t = len(sub)
            for opp, c in opp_counts.items():
                if opp in idx:
                    A[i, idx[opp]] -= c / n_t
    A_reg = A + reg * np.eye(n)
    r = np.linalg.solve(A_reg, m)
    r = r - r.mean()
    return {teams[i]: float(r[i]) for i in range(n)}


def build_sos_corrected_ortg(tg):
    """Lever 2: For each game's ortg, adjust by (league_avg_drtg - opp_team_rolling_drtg).

    Need to know opponent's rolling drtg AT the time of the game (pre-game).
    Use ema_drtg already computed. league_avg_drtg from mean of all rolling drtgs.
    """
    LEAGUE_AVG = float(tg["ema_drtg"].mean())  # rough; ~110
    # Need opponent's ema_drtg at game time
    opp = tg[["season", "game_id", "team_abbr", "ema_drtg"]].rename(
        columns={"team_abbr": "opp_team", "ema_drtg": "opp_ema_drtg_at_game"})
    tg2 = tg.merge(opp, on=["season", "game_id", "opp_team"], how="left")
    # SoS-correct each game's ortg: if opp had strong defense (low drtg), bump UP our recorded ortg
    tg2["ortg_sos"] = tg2["ortg"] + (tg2["opp_ema_drtg_at_game"] - LEAGUE_AVG)
    tg2["drtg_sos"] = tg2["drtg"] + (tg2["opp_ema_drtg_at_game"] - LEAGUE_AVG)
    # Note: drtg sos correction needs opp's ema_ortg not opp's ema_drtg
    # Re-do: drtg correction uses opp's offensive strength
    opp2 = tg[["season", "game_id", "team_abbr", "ema_ortg"]].rename(
        columns={"team_abbr": "opp_team", "ema_ortg": "opp_ema_ortg_at_game"})
    tg2 = tg2.merge(opp2, on=["season", "game_id", "opp_team"], how="left")
    LEAGUE_AVG_ORTG = float(tg["ema_ortg"].mean())
    tg2["drtg_sos"] = tg2["drtg"] + (LEAGUE_AVG_ORTG - tg2["opp_ema_ortg_at_game"])
    return tg2, LEAGUE_AVG, LEAGUE_AVG_ORTG


def add_sos_corrected_ema(df, alpha=ALPHA):
    df = df.sort_values(["season", "team_abbr", "game_date"]).copy()
    grp = df.groupby(["season", "team_abbr"])
    for c in ["ortg_sos", "drtg_sos"]:
        df[f"ema_{c}"] = grp[c].transform(
            lambda x: x.shift().ewm(alpha=alpha, min_periods=3, adjust=False).mean())
    return df


def attach_opp_sos_ema(df):
    cols = ["ema_ortg_sos", "ema_drtg_sos"]
    opp = df[["season", "game_id", "team_abbr"] + cols].rename(
        columns={"team_abbr": "opp_team", **{c: f"opp_{c}" for c in cols}})
    return df.merge(opp, on=["season", "game_id", "opp_team"], how="left")


def evaluate_game_level(df, pred_col, label):
    df = df.copy()
    home = df[df["is_home"]].copy()
    away = df[~df["is_home"]].copy()
    g = home[["season", "game_id", pred_col, "pts"]].rename(
        columns={pred_col: "h", "pts": "ha"}).merge(
        away[["game_id", pred_col, "pts"]].rename(columns={pred_col: "a", "pts": "aa"}),
        on="game_id", how="inner")
    g["pm"] = g["h"] - g["a"]
    g["am"] = g["ha"] - g["aa"]
    g["c"] = (g["pm"] > 0) == (g["am"] > 0)
    rmse = float(np.sqrt(((g["pm"] - g["am"]) ** 2).mean()))
    wp24 = float(g[g["season"] == "2024-25"]["c"].mean()) if (g["season"] == "2024-25").any() else float("nan")
    wp25 = float(g[g["season"] == "2025-26"]["c"].mean()) if (g["season"] == "2025-26").any() else float("nan")
    return {
        "label": label, "n": len(g),
        "win_pct": float(g["c"].mean()), "wp_24": wp24, "wp_25": wp25,
        "margin_rmse": rmse,
    }


def main():
    print("Loading multi-season box ...")
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box = box[(box["season"].isin(SEASONS)) & (box["season_type"] == "Regular Season")].copy()
    box["game_date"] = pd.to_datetime(box["game_date"])

    tg = aggregate_team_game(box)
    tg = attach_opp(tg)
    tg = tg.sort_values(["season", "game_date", "game_id"]).reset_index(drop=True)

    hc_per_season = {}
    for s in SEASONS:
        ss = tg[tg["season"] == s]
        h = ss[ss["is_home"]].set_index("game_id")["pts"]
        a = ss[~ss["is_home"]].set_index("game_id")["pts"]
        hc_per_season[s] = float((h - a).dropna().mean())
    tg["hc_half"] = tg["season"].map({s: v / 2 for s, v in hc_per_season.items()})

    # Build EMA (alpha=0.10) and EMA-fast (alpha=0.25)
    tg = add_ema_within_season(tg, ALPHA, "")
    tg = add_ema_within_season(tg, ALPHA_FAST, "_fast")
    tg = attach_opp_ema(tg, "")
    tg = attach_opp_ema(tg, "_fast")

    # SRS predictions
    print("Computing SRS at each date ...")
    srs_lookup = {}
    for season in SEASONS:
        season_tg = tg[tg["season"] == season]
        dates = sorted(season_tg["game_date"].unique())
        for d in dates:
            before = season_tg[season_tg["game_date"] < d]
            counts = before.groupby("team_abbr").size()
            if len(counts) < 30 or (counts < MIN_GAMES_FOR_SRS).any():
                continue
            try:
                srs_lookup[(season, d)] = solve_srs(before)
            except np.linalg.LinAlgError:
                continue

    def gr(row, which):
        s = srs_lookup.get((row["season"], row["game_date"]), {})
        return s.get(row[which], np.nan)

    tg["r_team"] = tg.apply(lambda r: gr(r, "team_abbr"), axis=1)
    tg["r_opp"] = tg.apply(lambda r: gr(r, "opp_team"), axis=1)
    sign = np.where(tg["is_home"], 1, -1)
    tg["srs_pred_margin"] = (tg["r_team"] - tg["r_opp"]) + sign * tg["hc_half"] * 2
    LEAGUE_AVG_PTS = float(tg["pts"].mean())
    tg["pred_pts_srs"] = LEAGUE_AVG_PTS + tg["srs_pred_margin"] / 2

    # Baseline EMA (additive defense)
    tg["pred_pts_ema_add"] = (tg["ema_ortg"] + tg["opp_ema_drtg"]) / 2 * \
                              ((tg["ema_poss"] + tg["opp_ema_poss"]) / 2) / 100 + \
                              np.where(tg["is_home"], tg["hc_half"], -tg["hc_half"])

    # Filter to predictable rows
    df = tg.dropna(subset=["pred_pts_srs", "pred_pts_ema_add",
                            "ema_ortg", "ema_drtg", "ema_poss",
                            "opp_ema_ortg", "opp_ema_drtg", "opp_ema_poss"]).copy()
    print(f"Predictable rows: {len(df)}")

    # Locked baseline: 60% SRS + 40% EMA-additive
    df["pred_pts_locked"] = 0.6 * df["pred_pts_srs"] + 0.4 * df["pred_pts_ema_add"]

    print()
    print("=" * 78)
    print("Locked baseline (60% SRS + 40% Tier 1B+EMA additive)")
    print("=" * 78)
    base = evaluate_game_level(df, "pred_pts_locked", "Locked")
    print(f"  n_games {base['n']}  win_pct {base['win_pct']:.4f}  "
          f"(24-25 {base['wp_24']:.4f}, 25-26 {base['wp_25']:.4f})  "
          f"rmse {base['margin_rmse']:.4f}")

    # =========================================================================
    # LEVER 3: Multiplicative defense
    # =========================================================================
    print()
    print("=" * 78)
    print("LEVER 3: Multiplicative defense (team_ortg * opp_drtg / league_avg_drtg)")
    print("=" * 78)
    LEAGUE_ORTG = float(df["ema_ortg"].mean())
    LEAGUE_DRTG = float(df["ema_drtg"].mean())
    print(f"  League EMA ortg: {LEAGUE_ORTG:.3f}, drtg: {LEAGUE_DRTG:.3f}")

    df["team_eff_mult"] = df["ema_ortg"] * (df["opp_ema_drtg"] / LEAGUE_DRTG)
    df["pred_pts_ema_mult"] = df["team_eff_mult"] * ((df["ema_poss"] + df["opp_ema_poss"]) / 2) / 100 + \
                               np.where(df["is_home"], df["hc_half"], -df["hc_half"])

    for w in [0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]:
        df["pred"] = 0.6 * df["pred_pts_srs"] + 0.4 * (w * df["pred_pts_ema_mult"] + (1 - w) * df["pred_pts_ema_add"])
        r = evaluate_game_level(df, "pred", f"mult-EMA mix w={w:.2f}")
        marker = "  <-- locked baseline" if w == 0.0 else ""
        print(f"  w_mult={w:.2f}: win_pct {r['win_pct']:.4f}  "
              f"(24 {r['wp_24']:.4f}, 25 {r['wp_25']:.4f})  rmse {r['margin_rmse']:.4f}{marker}")

    # =========================================================================
    # LEVER 4: Streak/momentum (ema_fast - ema_slow as adjustment)
    # =========================================================================
    print()
    print("=" * 78)
    print("LEVER 4: Streak / momentum (ema_fast α=0.25 minus ema α=0.10)")
    print("=" * 78)
    df["momentum_ortg"] = df["ema_fast_ortg"] - df["ema_ortg"]
    df["momentum_drtg"] = df["ema_fast_drtg"] - df["ema_drtg"]
    print(f"  momentum_ortg std: {df['momentum_ortg'].std():.3f}")
    print(f"  momentum_drtg std: {df['momentum_drtg'].std():.3f}")

    df["pred_pts_ema_mom"] = df["pred_pts_ema_add"] + 0.5 * df["momentum_ortg"] - 0.5 * df["momentum_drtg"]

    for w in [0.0, 0.25, 0.5, 1.0]:
        df["pred"] = 0.6 * df["pred_pts_srs"] + 0.4 * (df["pred_pts_ema_add"] +
                                                        w * (df["momentum_ortg"] - df["momentum_drtg"]) * 0.5)
        r = evaluate_game_level(df, "pred", f"momentum w={w:.2f}")
        marker = "  <-- locked baseline" if w == 0.0 else ""
        print(f"  mom_weight={w:.2f}: win_pct {r['win_pct']:.4f}  "
              f"(24 {r['wp_24']:.4f}, 25 {r['wp_25']:.4f})  rmse {r['margin_rmse']:.4f}{marker}")

    # =========================================================================
    # LEVER 2: SoS-corrected EMA
    # =========================================================================
    print()
    print("=" * 78)
    print("LEVER 2: SoS-corrected EMA on top of locked blend")
    print("=" * 78)
    # Build SoS-corrected ortg/drtg series
    tg_sos, LADRTG, LAORTG = build_sos_corrected_ortg(tg)
    tg_sos = add_sos_corrected_ema(tg_sos, ALPHA)
    tg_sos = attach_opp_sos_ema(tg_sos)
    # Merge SoS EMA back into df
    df = df.merge(
        tg_sos[["season", "game_id", "team_abbr",
                "ema_ortg_sos", "ema_drtg_sos", "opp_ema_ortg_sos", "opp_ema_drtg_sos"]],
        on=["season", "game_id", "team_abbr"], how="left"
    )
    df = df.dropna(subset=["ema_ortg_sos", "ema_drtg_sos", "opp_ema_drtg_sos"]).copy()
    print(f"After SoS-EMA filter: {len(df)} rows")

    df["pred_pts_ema_sos"] = (df["ema_ortg_sos"] + df["opp_ema_drtg_sos"]) / 2 * \
                              ((df["ema_poss"] + df["opp_ema_poss"]) / 2) / 100 + \
                              np.where(df["is_home"], df["hc_half"], -df["hc_half"])

    for w in [0.0, 0.25, 0.5, 0.75, 1.0]:
        df["pred"] = 0.6 * df["pred_pts_srs"] + 0.4 * (
            (1 - w) * df["pred_pts_ema_add"] + w * df["pred_pts_ema_sos"])
        r = evaluate_game_level(df, "pred", f"sos-EMA mix w={w:.2f}")
        marker = "  <-- locked baseline" if w == 0.0 else ""
        print(f"  w_sos_in_ema={w:.2f}: win_pct {r['win_pct']:.4f}  "
              f"(24 {r['wp_24']:.4f}, 25 {r['wp_25']:.4f})  rmse {r['margin_rmse']:.4f}{marker}")


if __name__ == "__main__":
    main()
