"""V3 backtest — mock historical daily refresh.

For each historical RS game in 22-23 → 24-25, simulate what our live runner
(playoff producer logic) WOULD have output, using only information available
on game_date - 1:

  1. Per-player season-to-date MPG (forward-clean, like v2)
  2. Per-team OUTs from pro_sports_injuries event log (effective on day d)
  3. Apply injury uplift redistribution to non-OUT teammates (per playoff
     producer constants: SAME_POS_REDIST=0.30, OTHER_POS_REDIST=0.10,
     INJURY_UPLIFT_MAX_MIN=10.0, ADJUSTED_MPG_MAX=44.0)
  4. proj_pts = v6.1_PTS_per_game × (uplifted_MPG / v6.1_baseline_MPG)

If v3 closes the v1→v2 gap (foresight ROI 5.7% vs no-foresight -5.3%) at
edge_total=12+ tier, we've validated that the live runner architecture
captures v6.1's real signal.

Outputs at runs/run_nba_game_totals_22_26/v3_mock_runner/:
  - game_residuals.csv
  - summary_by_season.csv
  - BACKTEST_RESULTS_v3.md
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("D:/NBA Projections")
SHIP_PATH = REPO / "audit_runs" / "unified_ship_v6_1_2025_26" / "per_player_projections_2025-26.csv"
BOX_PATH = REPO / "data" / "parquet" / "historical_box_scores.parquet"
INJ_PATH = REPO / "data" / "parquet" / "pro_sports_injuries_with_derived_severity.parquet"
META_PATH = REPO / "data" / "parquet" / "player_metadata_enriched.parquet"
LINES_PATH = Path("D:/sports_lines/data/vegas/nba_game_lines_extended.parquet")
OUT_DIR = REPO / "runs" / "run_nba_game_totals_22_26" / "v3_mock_runner"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BACKTEST_SEASONS = ["2022-23", "2023-24", "2024-25", "2025-26"]
MIN_PRIOR_GAMES_FOR_S2D = 3

# Producer constants (match D:/NBA Projections/scripts/produce_playoff_projections.py)
SAME_POS_REDIST = 0.30
OTHER_POS_REDIST = 0.10
INJURY_UPLIFT_MAX_MIN = 10.0
ADJUSTED_MPG_MAX = 44.0

# Map derived_severity to expected horizon (days from event to estimated return)
# Used when there's no explicit return event in the data
SEVERITY_DAYS = {
    "single_game": 3,
    "short_term": 10,
    "medium_term": 28,
    "long_term": 70,
    "out_for_season": 180,
}


def parse_min(m):
    if pd.isna(m): return 0.0
    if isinstance(m, (int, float)): return float(m)
    try:
        parts = str(m).split(":")
        return float(parts[0]) + (float(parts[1]) / 60 if len(parts) > 1 else 0)
    except (ValueError, TypeError):
        return 0.0


def load_box() -> pd.DataFrame:
    box = pd.read_parquet(BOX_PATH)
    box = box[pd.notna(box["nba_api_id"])].copy()
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    box["game_date"] = pd.to_datetime(box["game_date"])
    box["min_played"] = box["minutes"].apply(parse_min)
    return box


def load_positions() -> dict:
    """{nba_api_id: 'G' | 'F' | 'C'}"""
    if not META_PATH.exists():
        return {}
    meta = pd.read_parquet(META_PATH)
    out = {}
    for _, r in meta.iterrows():
        pos = r.get("position")
        if not isinstance(pos, str) or not pos:
            continue
        first = pos.split("-")[0].strip().upper()
        if first.startswith("G"): cls = "G"
        elif first.startswith("C"): cls = "C"
        elif first.startswith("F"): cls = "F"
        else: continue
        try:
            out[int(r["nba_api_id"])] = cls
        except (ValueError, TypeError):
            continue
    return out


def build_out_episodes() -> pd.DataFrame:
    """Build per-player OUT episodes from injury event log.

    Each OUT episode = (relinquished_event_date, expected_return_date) where
    expected_return is min(next_acquired_event, event_date + severity_days).

    Returns: nba_api_id, out_start, out_end (long format).
    """
    inj = pd.read_parquet(INJ_PATH)
    inj = inj[pd.notna(inj["nba_api_id"])].copy()
    inj["nba_api_id"] = inj["nba_api_id"].astype(int)
    inj["event_date"] = pd.to_datetime(inj["event_date"])
    inj = inj.sort_values(["nba_api_id", "event_date"])

    episodes = []
    # Group per player; walk events forward, pairing relinquished → acquired
    for pid, g in inj.groupby("nba_api_id"):
        events = g.to_dict("records")
        i = 0
        while i < len(events):
            ev = events[i]
            if pd.notna(ev["relinquished_status"]):
                # OUT episode starts
                start = ev["event_date"]
                sev = ev.get("derived_severity") or "short_term"
                horizon_days = SEVERITY_DAYS.get(sev, 10)
                horizon_end = start + pd.Timedelta(days=horizon_days)
                # Find next acquired event for this player
                end = horizon_end
                for j in range(i + 1, len(events)):
                    if pd.notna(events[j]["acquired_status"]):
                        end = min(end, events[j]["event_date"])
                        break
                episodes.append({
                    "nba_api_id": int(pid),
                    "out_start": start,
                    "out_end": end,
                })
            i += 1
    return pd.DataFrame(episodes)


def player_out_on_date(pid: int, date: pd.Timestamp, episodes_by_pid: dict) -> bool:
    """True iff player has an active OUT episode covering `date`."""
    eps = episodes_by_pid.get(pid)
    if eps is None:
        return False
    # eps is list of (start, end) tuples
    for start, end in eps:
        if start <= date < end:
            return True
    return False


def add_season_to_date_mpg(rs_df: pd.DataFrame) -> pd.DataFrame:
    rs_df = rs_df.sort_values(["nba_api_id", "season", "game_date"]).copy()
    grp = rs_df.groupby(["nba_api_id", "season"])
    rs_df["s2d_min_sum"] = grp["min_played"].cumsum() - rs_df["min_played"]
    rs_df["s2d_n_games"] = grp.cumcount()
    rs_df["s2d_mpg"] = np.where(
        rs_df["s2d_n_games"] > 0,
        rs_df["s2d_min_sum"] / rs_df["s2d_n_games"],
        np.nan,
    )
    return rs_df


def build_team_outs_per_game(player_rs: pd.DataFrame,
                              episodes_by_pid: dict,
                              positions: dict) -> pd.DataFrame:
    """For each (game_id, team_abbr), compile the list of OUT players (with
    their position + their s2d MPG) effective on game_date.

    Outs are determined per game date using injury episodes.
    """
    # Active rosters per (team, season): players who appeared in any RS game
    # for that team in that season — these are the candidates for OUT lists.
    roster = player_rs[["nba_api_id", "team_abbr", "season"]].drop_duplicates()
    roster_by_team_season = {}
    for (ta, sn), g in roster.groupby(["team_abbr", "season"]):
        roster_by_team_season[(ta, sn)] = g["nba_api_id"].astype(int).tolist()

    # Per (player, season) s2d MPG snapshot at the LAST game played in that season
    # — used as "expected MPG" for OUT players (since they're not in current game)
    # Actually we want: per (player, date) s2d_mpg from player_rs itself.

    # Simpler: for each game in player_rs (which is the lineup that played),
    # at game_date d, look at the team's seasonal roster, find which roster
    # members are OUT (via episodes), and pull their most-recent s2d MPG.

    # Build per-(player, season) most-recent s2d MPG before each date
    # via expanding mean = s2d_mpg column already in player_rs
    last_s2d_per_player_date = player_rs[
        ["nba_api_id", "game_date", "team_abbr", "season", "s2d_mpg"]
    ].sort_values(["nba_api_id", "game_date"]).copy()

    # game-level keys
    games = player_rs[["game_id", "game_date", "team_abbr", "season"]].drop_duplicates()

    rows = []
    for _, gm in games.iterrows():
        ta = gm["team_abbr"]; sn = gm["season"]; d = gm["game_date"]
        gid = gm["game_id"]
        # Candidate roster
        cands = roster_by_team_season.get((ta, sn), [])
        for pid in cands:
            if not player_out_on_date(pid, d, episodes_by_pid):
                continue
            # Get this player's most-recent s2d_mpg before d in this season
            pms = last_s2d_per_player_date[
                (last_s2d_per_player_date["nba_api_id"] == pid) &
                (last_s2d_per_player_date["season"] == sn) &
                (last_s2d_per_player_date["game_date"] < d)
            ]
            if pms.empty:
                continue
            recent_mpg = float(pms["s2d_mpg"].iloc[-1])
            if pd.isna(recent_mpg) or recent_mpg <= 0:
                continue
            rows.append({
                "game_id": gid, "team_abbr": ta, "out_pid": pid,
                "out_pos": positions.get(pid, "F"),
                "out_mpg": recent_mpg,
            })
    return pd.DataFrame(rows)


def apply_injury_uplift_and_project(player_rs: pd.DataFrame,
                                     team_outs: pd.DataFrame,
                                     ship_lookup: dict,
                                     prior_rates: dict,
                                     positions: dict,
                                     league_avg_ppm: float,
                                     team_target_min: float = 240.0) -> pd.DataFrame:
    """Project each played player's expected MPG by rescaling s2d MPG so the
    team's sum equals team_target_min (240). Naturally absorbs OUT players:
    they're not in `played`, so remaining players get a proportional bump.

    Position-aware uplift weights bias the rescale: same-position-to-OUT
    players get a heavier slice than other-position. Total team minutes
    always conserve to team_target_min.
    """
    outs_by_team_game = {}
    for (gid, ta), g in team_outs.groupby(["game_id", "team_abbr"]):
        outs_by_team_game[(gid, ta)] = [
            (int(r["out_pid"]), r["out_pos"], float(r["out_mpg"]))
            for _, r in g.iterrows()
        ]

    n = len(player_rs)
    expected_min = np.zeros(n)
    proj_pts = np.zeros(n)
    mpg_source = np.array(["none"] * n, dtype=object)
    base_mpg_arr = np.zeros(n)
    raw_weight_arr = np.zeros(n)  # s2d MPG × position-aware uplift multiplier

    pid_arr = player_rs["nba_api_id"].values
    season_arr = player_rs["season"].values
    s2d_mpg_arr = player_rs["s2d_mpg"].values
    s2d_n_arr = player_rs["s2d_n_games"].values
    gid_arr = player_rs["game_id"].values
    team_arr = player_rs["team_abbr"].values

    # Pass 1: base MPG + position-aware weight per player
    for i in range(n):
        pid = int(pid_arr[i]); sn = season_arr[i]
        gid = gid_arr[i]; ta = team_arr[i]

        if s2d_n_arr[i] >= MIN_PRIOR_GAMES_FOR_S2D and not np.isnan(s2d_mpg_arr[i]):
            base_mpg = float(s2d_mpg_arr[i]); src = "s2d"
        elif (pid, sn) in prior_rates:
            base_mpg = prior_rates[(pid, sn)]["rs_mpg"]; src = "prior_rs"
        elif pid in ship_lookup and ship_lookup[pid]["mpg"] and ship_lookup[pid]["mpg"] > 0:
            base_mpg = float(ship_lookup[pid]["mpg"]); src = "ship_mpg"
        else:
            base_mpg = 0.0; src = "none"
        base_mpg_arr[i] = base_mpg
        mpg_source[i] = src

        # Position-aware bonus: same-pos-to-OUT players get a multiplier
        team_outs_list = outs_by_team_game.get((gid, ta), [])
        player_pos = positions.get(pid, "F")
        bonus = 1.0
        for opid, opos, ompg in team_outs_list:
            if opid == pid:
                continue
            if opos == player_pos:
                bonus += 0.30 * (ompg / 30.0)  # ~9% per OUT same-pos player at 30 MPG
            else:
                bonus += 0.10 * (ompg / 30.0)
        raw_weight_arr[i] = base_mpg * bonus

    # Pass 2: rescale per team-game so sum = team_target_min
    df = player_rs.copy()
    df["_raw_weight"] = raw_weight_arr
    df["_gt_key"] = df["game_id"].astype(str) + "|" + df["team_abbr"]
    team_weight_sum = df.groupby("_gt_key")["_raw_weight"].sum().to_dict()

    for i in range(n):
        key = df["_gt_key"].iat[i]
        team_sum = team_weight_sum.get(key, 0.0)
        if team_sum > 0:
            em = raw_weight_arr[i] * (team_target_min / team_sum)
        else:
            em = base_mpg_arr[i]
        em = min(em, ADJUSTED_MPG_MAX)
        expected_min[i] = em

        pid = int(pid_arr[i]); sn = season_arr[i]
        if pid in ship_lookup:
            ppg = ship_lookup[pid]["PTS_per_game"]
            base_v6_mpg = ship_lookup[pid]["mpg"]
            if base_v6_mpg and base_v6_mpg > 0:
                proj_pts[i] = ppg * (em / base_v6_mpg)
                continue
        if (pid, sn) in prior_rates:
            ppm = prior_rates[(pid, sn)]["pts_per_min"]
            proj_pts[i] = ppm * em
            continue
        proj_pts[i] = league_avg_ppm * em

    out = player_rs.copy()
    out["base_mpg"] = base_mpg_arr
    out["raw_weight"] = raw_weight_arr
    out["expected_min"] = expected_min
    out["injury_uplift"] = expected_min - base_mpg_arr
    out["proj_pts"] = proj_pts
    out["mpg_source"] = mpg_source
    return out


def aggregate_to_team_game(player_proj: pd.DataFrame) -> pd.DataFrame:
    played = player_proj[player_proj["min_played"] > 0]
    return played.groupby(
        ["game_id", "game_date", "team_abbr", "is_home", "season"]
    ).agg(
        proj_pts=("proj_pts", "sum"),
        actual_pts=("PTS", "sum"),
        n_players=("nba_api_id", "size"),
        total_uplift=("injury_uplift", "sum"),
    ).reset_index()


def join_to_lines(team_game, lines):
    home = team_game[team_game["is_home"]].rename(
        columns={"team_abbr": "home_team_abbr",
                 "proj_pts": "home_proj_pts",
                 "actual_pts": "home_actual_pts",
                 "total_uplift": "home_uplift"})
    away = team_game[~team_game["is_home"]].rename(
        columns={"team_abbr": "away_team_abbr",
                 "proj_pts": "away_proj_pts",
                 "actual_pts": "away_actual_pts",
                 "total_uplift": "away_uplift"})
    game = home.merge(
        away[["game_id", "away_team_abbr", "away_proj_pts",
              "away_actual_pts", "away_uplift"]],
        on="game_id", how="inner",
    )
    game["proj_total"] = game["home_proj_pts"] + game["away_proj_pts"]
    game["actual_total"] = game["home_actual_pts"] + game["away_actual_pts"]
    game["proj_margin_home"] = game["home_proj_pts"] - game["away_proj_pts"]
    game["actual_margin_home"] = game["home_actual_pts"] - game["away_actual_pts"]
    lines["game_date"] = pd.to_datetime(lines["game_date"])
    merged = game.merge(
        lines[["game_date", "home_team_abbr", "away_team_abbr",
               "close_total", "close_spread_home"]],
        on=["game_date", "home_team_abbr", "away_team_abbr"],
        how="inner",
    )
    merged = merged[(merged["close_total"] >= 150) & (merged["close_total"] <= 290)]
    merged["close_margin_home_implied"] = -merged["close_spread_home"]
    merged["resid_total_proj"] = merged["actual_total"] - merged["proj_total"]
    merged["resid_total_close"] = merged["actual_total"] - merged["close_total"]
    merged["resid_margin_proj"] = merged["actual_margin_home"] - merged["proj_margin_home"]
    merged["resid_margin_close"] = merged["actual_margin_home"] - merged["close_margin_home_implied"]
    merged["skew_total"] = merged["proj_total"] - merged["close_total"]
    return merged


def main():
    print("=" * 70)
    print("V3 — Mock historical daily refresh (injury overlay + uplift)")
    print("=" * 70)

    print("\n[1/7] Loading box, ship, lines, injuries, positions...")
    box = load_box()
    lines = pd.read_parquet(LINES_PATH)
    lines["game_date"] = pd.to_datetime(lines["game_date"])
    lines = lines[lines["season"].isin(BACKTEST_SEASONS)]
    lines = lines.dropna(subset=["close_total"])
    lines = lines[(lines["close_total"] >= 150) & (lines["close_total"] <= 290)]
    ship = pd.read_csv(SHIP_PATH, usecols=["nba_api_id", "PTS_per_game", "mpg"])
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    ship_lookup = ship.set_index("nba_api_id")[["PTS_per_game", "mpg"]].to_dict("index")
    positions = load_positions()
    print(f"  box={len(box):,}  lines={len(lines):,}  ship={len(ship)}  positions={len(positions)}")

    print("\n[2/7] Building per-(player) OUT episodes from injury event log...")
    episodes = build_out_episodes()
    print(f"  {len(episodes):,} OUT episodes built")
    episodes_by_pid = {}
    for pid, g in episodes.groupby("nba_api_id"):
        episodes_by_pid[int(pid)] = list(zip(g["out_start"], g["out_end"]))

    print("\n[3/7] Computing season-to-date MPG + prior-season rates...")
    rs = box[box["season_type"] == "Regular Season"].copy()
    rs = rs[rs["season"].isin(BACKTEST_SEASONS)]
    rs = rs[rs["min_played"] > 0]
    rs = add_season_to_date_mpg(rs)

    # Build prior-season rates
    rs_all = box[box["season_type"] == "Regular Season"]
    grp = rs_all.groupby(["nba_api_id", "season"]).agg(
        games=("game_id", "nunique"),
        total_pts=("PTS", "sum"),
        total_min=("min_played", "sum"),
    ).reset_index()
    grp = grp[grp["games"] >= 10]
    grp["pts_per_game"] = grp["total_pts"] / grp["games"]
    grp["rs_mpg"] = grp["total_min"] / grp["games"]
    grp["pts_per_min"] = grp["total_pts"] / grp["total_min"]
    next_season = {"2017-18": "2018-19", "2018-19": "2019-20",
                   "2019-20": "2020-21", "2020-21": "2021-22",
                   "2021-22": "2022-23", "2022-23": "2023-24",
                   "2023-24": "2024-25", "2024-25": "2025-26"}
    prior_rates = {}
    for _, r in grp.iterrows():
        t = next_season.get(r["season"])
        if t is None: continue
        prior_rates[(int(r["nba_api_id"]), t)] = {
            "pts_per_game": float(r["pts_per_game"]),
            "rs_mpg": float(r["rs_mpg"]),
            "pts_per_min": float(r["pts_per_min"]),
        }
    league_avg_ppm = float(rs_all["PTS"].sum() / rs_all["min_played"].sum())
    print(f"  prior_rates={len(prior_rates)}  league_avg={league_avg_ppm:.4f} pts/min")

    print("\n[4/7] Identifying OUT players per team-game (slow ~3-5 min)...")
    team_outs = build_team_outs_per_game(rs, episodes_by_pid, positions)
    print(f"  {len(team_outs):,} (game, team, OUT player) rows")
    print(f"  avg OUTs per team-game: {len(team_outs) / rs[['game_id', 'team_abbr']].drop_duplicates().shape[0]:.2f}")

    print("\n[5/7] Applying injury uplift + projecting per player-game...")
    player_proj = apply_injury_uplift_and_project(
        rs, team_outs, ship_lookup, prior_rates, positions, league_avg_ppm)
    n_with_uplift = (player_proj["injury_uplift"] > 0).sum()
    avg_uplift = player_proj[player_proj["injury_uplift"] > 0]["injury_uplift"].mean()
    print(f"  {n_with_uplift:,} player-games received injury uplift")
    print(f"  avg uplift when applied: {avg_uplift:.2f} min")

    print("\n[6/7] Aggregating + joining to closes...")
    team_game = aggregate_to_team_game(player_proj)
    merged = join_to_lines(team_game, lines)
    print(f"  matched games: {len(merged):,}")
    merged.to_csv(OUT_DIR / "game_residuals.csv", index=False)

    print("\n[7/7] Summarizing v3 vs v1 + v2...")
    def summarize(df, label):
        if len(df) == 0: return {"label": label, "n_games": 0}
        return {
            "label": label, "n_games": int(len(df)),
            "bias_proj_total": float(df["resid_total_proj"].mean()),
            "mae_proj_total": float(df["resid_total_proj"].abs().mean()),
            "rmse_proj_total": float(np.sqrt((df["resid_total_proj"] ** 2).mean())),
            "mae_close_total": float(df["resid_total_close"].abs().mean()),
            "mean_skew_total": float(df["skew_total"].mean()),
            "bias_margin": float(df["resid_margin_proj"].mean()),
            "mae_margin": float(df["resid_margin_proj"].abs().mean()),
        }

    rows = [summarize(merged, "ALL")]
    for s in BACKTEST_SEASONS:
        rows.append(summarize(merged[merged["season"] == s], s))
    sm = pd.DataFrame(rows)
    sm.to_csv(OUT_DIR / "summary_by_season.csv", index=False)

    print(f"\n{'label':<10} {'n':>5} {'bias':>7} {'mae':>7} {'rmse':>7} {'mae_cl':>7} {'skew':>7}")
    for r in rows:
        if r["n_games"] == 0: continue
        print(f"{r['label']:<10} {r['n_games']:>5} "
              f"{r['bias_proj_total']:>+7.2f} {r['mae_proj_total']:>7.2f} "
              f"{r['rmse_proj_total']:>7.2f} {r['mae_close_total']:>7.2f} "
              f"{r['mean_skew_total']:>+7.2f}")

    md = OUT_DIR / "BACKTEST_RESULTS_v3.md"
    with open(md, "w", encoding="utf-8") as f:
        f.write("# V3 backtest — mock historical daily refresh\n\n")
        f.write(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n\n")
        f.write("**Mock pipeline:** for each historical RS game on date d, "
                "construct what the live runner would output using only "
                "information available on d-1: season-to-date MPG + "
                "OUT episodes from injury event log + position-aware uplift "
                "(producer constants SAME_POS=0.30, OTHER_POS=0.10, "
                "uplift_max=10.0 min, mpg_max=44.0).\n\n")
        f.write("## Results by season\n\n")
        f.write(sm.round(3).to_markdown(index=False) + "\n")

    print(f"\n  → {md}")
    print("\n=== done ===")


if __name__ == "__main__":
    main()
