"""Phase 3 contextual layer: fresh-injury adjustment on top of 60% SRS + 40% Tier 1B+EMA.

Hypothesis: rolling efficiency lags roster reality by 5-10 games. Games WITHIN that lag
where high-MPG players just got announced OUT are where we miss.

Layer architecture:
  For each (game_date, team):
    1. Identify FRESH_OUT players = OUT events after team's game N-5
       (i.e., player whose absence hasn't yet propagated into rolling drtg)
    2. For each fresh-OUT player, compute their pre-injury rolling-5g per-min PTS contribution
    3. Sum to get expected team offense lost this game
    4. Apply: team_pts_pred -= fresh_out_loss

  Then run walk-forward backtest, compare to baseline 60% SRS + 40% EMA.

Validation:
  - Headline: combined win pct ≥ 66% would be Vegas-beating
  - Per-season: does 23-24 (big-miss season) improve most?
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from pathlib import Path

PQ = Path("data/parquet")
OUT_DIR = Path("audit_runs/walkforward_injury_layer")
OUT_DIR.mkdir(parents=True, exist_ok=True)

KEEP_SEASONS = ["2018-19", "2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]
ALPHA = 0.10
MIN_GAMES_FOR_SRS = 5
W_SRS = 0.60
FRESH_OUT_LOOKBACK_GAMES = 5  # if player went OUT within last 5 games, consider fresh
OUT_STATUSES = {"out_indefinitely", "placed_on_il"}  # exclude DTD


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


def add_ema(df, alpha):
    df = df.sort_values(["season", "team_abbr", "game_date"]).copy()
    grp = df.groupby(["season", "team_abbr"])
    for c in ["ortg", "drtg", "poss"]:
        df[f"ema_{c}"] = grp[c].transform(
            lambda x: x.shift().ewm(alpha=alpha, min_periods=3, adjust=False).mean())
    return df


def attach_opp_ema(df):
    cols = ["ema_ortg", "ema_drtg", "ema_poss"]
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
    try:
        r = np.linalg.solve(A_reg, m)
    except np.linalg.LinAlgError:
        return None
    r = r - r.mean()
    return {teams[i]: float(r[i]) for i in range(n)}


def build_fresh_out_layer(box, inj):
    """For each (game_date, team), compute fresh-OUT PTS lost.

    Approach:
      - For each team-game row, find each player on that team's 30-day-prior box history
      - Check if they have OUT event between (game_date - FRESH_OUT_LOOKBACK_GAMES games ago) and game_date
        with no return event in same window
      - For each such player, look up their pre-OUT 5-game-rolling PTS-per-min × MPG
      - Sum
    """
    # Pre-build per-player rolling PTS-per-min
    box = box.sort_values(["nba_api_id", "game_date"]).copy()
    box["pts_per_min"] = np.where(box["minutes"] > 0, box["PTS"] / box["minutes"], np.nan)
    grp = box.groupby("nba_api_id")
    # 5-game rolling pre-game (shift first)
    box["roll_ppm"] = grp["pts_per_min"].transform(
        lambda x: x.shift().rolling(5, min_periods=2).mean())
    box["roll_mpg"] = grp["minutes"].transform(
        lambda x: x.shift().rolling(5, min_periods=2).mean())
    # team for each player on each game_date
    box["player_team_on_date"] = box["team_abbr"]

    # Build injury status events
    inj = inj.copy()
    inj["event_date"] = pd.to_datetime(inj["event_date"])
    # OUT events: relinquished_status in {out_indefinitely, placed_on_il}
    out_events = inj[inj["relinquished_status"].isin(OUT_STATUSES)][
        ["nba_api_id", "team_abbr", "event_date"]
    ].rename(columns={"event_date": "out_date", "team_abbr": "inj_team_abbr"})
    out_events = out_events.dropna(subset=["nba_api_id"])
    # Return events: acquired_status in {activated_from_il, returned_to_lineup}
    return_events = inj[inj["acquired_status"].isin({"activated_from_il", "returned_to_lineup"})][
        ["nba_api_id", "team_abbr", "event_date"]
    ].rename(columns={"event_date": "return_date", "team_abbr": "ret_team_abbr"})
    return_events = return_events.dropna(subset=["nba_api_id"])

    # For each team-game row (per team), find players currently OUT
    # Use box data + injury events to derive fresh-OUT status per game
    print(f"  OUT events: {len(out_events)}")
    print(f"  Return events: {len(return_events)}")

    # Compute fresh-OUT loss per team-game
    # Step 1: per-team, ordered game dates
    team_games = box[["team_abbr", "game_date"]].drop_duplicates().sort_values(
        ["team_abbr", "game_date"]).reset_index(drop=True)
    team_games["team_game_rank"] = team_games.groupby("team_abbr").cumcount()

    # Step 2: for each (team_abbr, game_date), find date for game N - FRESH_OUT_LOOKBACK_GAMES
    team_games_lookup = team_games.set_index(["team_abbr", "team_game_rank"])
    box_with_rank = box.merge(team_games, on=["team_abbr", "game_date"], how="left")

    # For each (player, game_date, team), check if there's an OUT event in [game_date - 30 days, game_date]
    # that's "fresh" — i.e., OUT event is after the game N-5 date
    # Simplification: define fresh-OUT as player's last appearance was 1-5 games ago (per team's calendar)
    # and they have an OUT event after that

    # Per-team game schedule
    team_dates = box.groupby("team_abbr")["game_date"].apply(lambda x: np.array(sorted(x.unique()))).to_dict()

    # Per player per team rolling per-min before each absence
    # Build (player, team, game_date) -> (roll_ppm, roll_mpg) lookup from box
    box_lookup = box[["nba_api_id", "team_abbr", "game_date", "roll_ppm", "roll_mpg"]].copy()
    box_lookup = box_lookup.set_index(["nba_api_id", "team_abbr", "game_date"])

    # For each player, build (out_date, team) events
    # Compute fresh-OUT contribution per team-game
    fresh_out = []
    out_by_player = out_events.set_index("nba_api_id").sort_index()
    return_by_player = return_events.set_index("nba_api_id").sort_index()

    # For efficiency, build per-team-date "active roster" via box appearances 30 days prior
    # For each team-game, gather players who appeared in box for that team in last 60 days
    print("  Building roster-active membership per team-game ...")
    team_game_records = sorted(set(zip(box["team_abbr"], box["game_date"])))
    print(f"  Team-game date combinations: {len(team_game_records)}")

    # Per (team, date) -> list of (player, last_appearance_date, roll_ppm, roll_mpg)
    box_sorted = box.sort_values(["team_abbr", "nba_api_id", "game_date"])
    # Per (team, player), get list of game_dates with roll_ppm, roll_mpg
    box_indexed = box_sorted.set_index(["team_abbr", "nba_api_id"])

    # Build per-player team-date map
    # For each (team_abbr, game_date) in team_games, find players who played for that team in last 30 days
    # and who currently have an OUT event without return between that out and game_date
    # AND the OUT event was after their N-5 game appearance for that team

    # Approach optimized:
    # For each player, find absence periods (out_date, return_date)
    # For each team-game, sum over players whose absence period contains game_date
    # AND game_date < absence_start + FRESH_OUT_LOOKBACK_GAMES_in_calendar (rough 14 days)
    # AND we have a roll_ppm and roll_mpg for them prior to absence_start

    # Build per-player absence intervals
    print("  Building per-player absence intervals ...")
    player_absences = {}
    for pid in out_events["nba_api_id"].unique():
        outs = out_events[out_events["nba_api_id"] == pid].sort_values("out_date")["out_date"].values
        rets = return_events[return_events["nba_api_id"] == pid].sort_values("return_date")["return_date"].values
        intervals = []
        rj = 0
        for od in outs:
            # find next return after od
            while rj < len(rets) and rets[rj] <= od:
                rj += 1
            ret_date = rets[rj] if rj < len(rets) else pd.Timestamp("2099-01-01")
            intervals.append((pd.Timestamp(od), pd.Timestamp(ret_date)))
        player_absences[pid] = intervals

    print(f"  Players with absences: {len(player_absences)}")

    # For each team-game, identify fresh-OUT players
    # FRESH_OUT_DAYS = how recent OUT event must be (in calendar days)
    FRESH_DAYS = 14  # ~5 games at NBA cadence

    # Build per-team player rolling lookup: list of (player, game_date, roll_ppm, roll_mpg)
    print("  Computing fresh-OUT lost contribution per team-game ...")
    team_box = box[["team_abbr", "nba_api_id", "game_date", "roll_ppm", "roll_mpg"]].copy()
    team_box["game_date"] = pd.to_datetime(team_box["game_date"])
    team_box_by_pair = team_box.groupby(["team_abbr", "nba_api_id"])

    fresh_out_by_team_game = []
    for (team_abbr, game_date) in team_game_records:
        gd = pd.Timestamp(game_date)
        # Players on this team in last 30 days with valid roll stats
        recent_box = box[
            (box["team_abbr"] == team_abbr) &
            (box["game_date"] >= gd - pd.Timedelta(days=30)) &
            (box["game_date"] < gd) &
            (box["roll_ppm"].notna()) &
            (box["roll_mpg"].notna())
        ]
        # Take their latest entry per player
        if len(recent_box) == 0:
            fresh_out_by_team_game.append({
                "team_abbr": team_abbr, "game_date": game_date,
                "fresh_out_pts_loss": 0.0, "fresh_out_count": 0,
            })
            continue
        latest = recent_box.sort_values("game_date").groupby("nba_api_id").tail(1)
        # Among these, who has a fresh OUT event between (gd - FRESH_DAYS) and gd?
        loss = 0.0
        count = 0
        for _, r in latest.iterrows():
            pid = r["nba_api_id"]
            if pid not in player_absences:
                continue
            for od, rd in player_absences[pid]:
                if (od <= gd) and (rd > gd) and (od >= gd - pd.Timedelta(days=FRESH_DAYS)):
                    # Fresh OUT: player has been OUT for less than FRESH_DAYS
                    # Use their pre-OUT rolling MPG × roll_ppm
                    pts_lost = r["roll_mpg"] * r["roll_ppm"]
                    loss += pts_lost
                    count += 1
                    break  # don't double-count same player
        fresh_out_by_team_game.append({
            "team_abbr": team_abbr, "game_date": game_date,
            "fresh_out_pts_loss": loss, "fresh_out_count": count,
        })

    fout_df = pd.DataFrame(fresh_out_by_team_game)
    return fout_df


def home_court_advantage(tg):
    out = {}
    for s, g in tg.groupby("season"):
        h = g[g["is_home"]].set_index("game_id")["pts"]
        a = g[~g["is_home"]].set_index("game_id")["pts"]
        out[s] = float((h - a).dropna().mean())
    return out


def main():
    print("Loading box scores ...")
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box = box[(box["season_type"] == "Regular Season") & (box["season"].isin(KEEP_SEASONS))].copy()
    box["game_date"] = pd.to_datetime(box["game_date"])
    print(f"  Box rows: {len(box)}")

    print("Loading injury feed ...")
    inj = pd.read_parquet(PQ / "pro_sports_injuries.parquet")
    print(f"  Injury rows: {len(inj)}")

    # Build fresh-OUT layer
    print()
    print("=" * 70)
    print("Building fresh-OUT contribution per team-game ...")
    print("=" * 70)
    fout = build_fresh_out_layer(box, inj)
    fout.to_csv(OUT_DIR / "fresh_out_per_team_game.csv", index=False)
    print()
    print(f"Fresh-OUT distribution:")
    print(fout["fresh_out_pts_loss"].describe())
    print(f"Games with >=1 fresh-OUT player: {(fout['fresh_out_count'] > 0).sum()}")
    print(f"Games with >=2 fresh-OUT players: {(fout['fresh_out_count'] >= 2).sum()}")
    print(f"Mean PTS loss per game (when any fresh-OUT): "
          f"{fout[fout['fresh_out_count'] > 0]['fresh_out_pts_loss'].mean():.3f}")

    # Build base model (Tier 1B+EMA + SRS blend) — same as walk-forward
    tg = aggregate_team_game(box)
    tg = attach_opp(tg)
    tg = tg.sort_values(["season", "game_date", "game_id"]).reset_index(drop=True)
    hc_per_season = home_court_advantage(tg)
    tg["hc_half"] = tg["season"].map({s: v / 2 for s, v in hc_per_season.items()})

    tg = add_ema(tg, ALPHA)
    tg = attach_opp_ema(tg)

    print()
    print("Computing SRS per (season, date) ...")
    srs_lookup = {}
    for season in KEEP_SEASONS:
        season_tg = tg[tg["season"] == season]
        dates = sorted(season_tg["game_date"].unique())
        for d in dates:
            before = season_tg[season_tg["game_date"] < d]
            counts = before.groupby("team_abbr").size()
            if len(counts) < 28 or (counts < MIN_GAMES_FOR_SRS).any():
                continue
            sol = solve_srs(before)
            if sol is not None:
                srs_lookup[(season, d)] = sol

    def get_srs(row, which):
        s = srs_lookup.get((row["season"], row["game_date"]), {})
        return s.get(row[which], np.nan)

    tg["r_team"] = tg.apply(lambda r: get_srs(r, "team_abbr"), axis=1)
    tg["r_opp"] = tg.apply(lambda r: get_srs(r, "opp_team"), axis=1)
    sign = np.where(tg["is_home"], 1, -1)
    tg["srs_pred_margin"] = (tg["r_team"] - tg["r_opp"]) + sign * tg["hc_half"] * 2
    LEAGUE_AVG_PTS = tg.groupby("season")["pts"].mean().to_dict()
    tg["league_avg_pts"] = tg["season"].map(LEAGUE_AVG_PTS)
    tg["pred_pts_srs"] = tg["league_avg_pts"] + tg["srs_pred_margin"] / 2

    tg["pred_pts_ema"] = (tg["ema_ortg"] + tg["opp_ema_drtg"]) / 2 * \
                          ((tg["ema_poss"] + tg["opp_ema_poss"]) / 2) / 100 + \
                          np.where(tg["is_home"], tg["hc_half"], -tg["hc_half"])

    tg_v = tg.dropna(subset=["pred_pts_srs", "pred_pts_ema"]).copy()
    tg_v["pred_pts_base"] = W_SRS * tg_v["pred_pts_srs"] + (1 - W_SRS) * tg_v["pred_pts_ema"]

    # Merge fresh-OUT
    tg_v = tg_v.merge(fout, on=["team_abbr", "game_date"], how="left")
    tg_v["fresh_out_pts_loss"] = tg_v["fresh_out_pts_loss"].fillna(0.0)
    tg_v["fresh_out_count"] = tg_v["fresh_out_count"].fillna(0).astype(int)

    # Apply injury adjustment: each team's prediction reduced by their fresh-OUT loss
    # Test multiple scale factors (uncertainty: how much of "lost MPG x ppm" actually shows up)
    print()
    print("=" * 70)
    print("Walk-forward with injury layer at multiple scales")
    print("=" * 70)

    home_v = tg_v[tg_v["is_home"]].copy()
    away_v = tg_v[~tg_v["is_home"]].copy()

    def evaluate_at_scale(scale):
        h = home_v.copy()
        a = away_v.copy()
        h["pred_pts"] = h["pred_pts_base"] - scale * h["fresh_out_pts_loss"]
        a["pred_pts"] = a["pred_pts_base"] - scale * a["fresh_out_pts_loss"]
        games = h[["season", "game_id", "pred_pts", "pts", "fresh_out_pts_loss"]].rename(
            columns={"pred_pts": "h", "pts": "ha", "fresh_out_pts_loss": "h_inj"}
        ).merge(
            a[["game_id", "pred_pts", "pts", "fresh_out_pts_loss"]].rename(
                columns={"pred_pts": "a", "pts": "aa", "fresh_out_pts_loss": "a_inj"}),
            on="game_id", how="inner")
        games["pm"] = games["h"] - games["a"]
        games["am"] = games["ha"] - games["aa"]
        games["correct"] = (games["pm"] > 0) == (games["am"] > 0)
        return games

    results = []
    print(f"  {'scale':>7} {'win_pct':>10} {'18-19':>8} {'19-20':>8} {'20-21':>8} {'21-22':>8} {'22-23':>8} {'23-24':>8} {'24-25':>8} {'25-26':>8} {'rmse':>8}")
    for scale in [0.0, 0.5, 1.0, 1.5, 2.0]:
        games = evaluate_at_scale(scale)
        wp_all = games["correct"].mean()
        err = games["pm"] - games["am"]
        rmse = np.sqrt((err ** 2).mean())
        wp_by_season = games.groupby("season")["correct"].mean()
        marker = "  <-- baseline" if scale == 0.0 else ""
        print(f"  {scale:>7.2f} {wp_all:>10.4f} ", end="")
        for s in KEEP_SEASONS:
            val = wp_by_season.get(s, float("nan"))
            print(f"{val:>8.4f} ", end="")
        print(f"{rmse:>8.4f}{marker}")
        results.append({"scale": scale, "win_pct": wp_all, "rmse": rmse,
                        **{f"wp_{s}": wp_by_season.get(s, float("nan")) for s in KEEP_SEASONS}})

    pd.DataFrame(results).to_csv(OUT_DIR / "injury_layer_grid_results.csv", index=False)


if __name__ == "__main__":
    main()
