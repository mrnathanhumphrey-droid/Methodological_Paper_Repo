"""V2 backtest — live-formula simulation with season-to-date MPG.

Mimics what a daily RS runner would do: at game date `d`, use the player's
cumulative MPG up to (but NOT including) date `d` as the expected-minutes
input. Avoids the perfect-foresight problem in v1 where actual game minutes
were used.

Per-player MPG priority (forward-clean):
  1. Season-to-date MPG (if ≥3 prior RS games this season)
  2. Prior-season RS MPG (warm-up for early-season games)
  3. v6.1 ship MPG (final fallback)

PTS projection formula:
  expected_min = season_to_date_MPG
  proj_pts = v6.1_PTS_per_game × (expected_min / v6.1_mpg)

For non-ship players (rookies / late signings): use prior-season per-min PTS
× expected_min, OR league-average per-min × expected_min if no prior.

Team-game projection: sum proj_pts over players who actually appeared (lineup
foresight; matches live system which knows active roster pre-game).

Outputs in runs/run_nba_game_totals_22_26/v2_live_formula/:
  - game_residuals.csv
  - summary_by_season.csv
  - BACKTEST_RESULTS_v2.md
  - v1_vs_v2_comparison.csv (head-to-head per-season)
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
LINES_PATH = Path("D:/sports_lines/data/vegas/nba_game_lines_extended.parquet")
OUT_DIR = REPO / "runs" / "run_nba_game_totals_22_26" / "v2_live_formula"
OUT_DIR.mkdir(parents=True, exist_ok=True)
V1_RESIDUALS = REPO / "runs" / "run_nba_game_totals_22_26" / "game_residuals.csv"

BACKTEST_SEASONS = ["2022-23", "2023-24", "2024-25", "2025-26"]
MIN_PRIOR_GAMES_FOR_S2D = 3


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


def build_prior_season_rates(box: pd.DataFrame) -> dict:
    rs = box[box["season_type"] == "Regular Season"]
    grp = rs.groupby(["nba_api_id", "season"]).agg(
        games=("game_id", "nunique"),
        total_pts=("PTS", "sum"),
        total_min=("min_played", "sum"),
    ).reset_index()
    grp = grp[grp["games"] >= 10]
    grp["pts_per_game"] = grp["total_pts"] / grp["games"]
    grp["rs_mpg"] = grp["total_min"] / grp["games"]
    grp["pts_per_min"] = grp["total_pts"] / grp["total_min"]
    rates = {}
    next_season = {"2017-18": "2018-19", "2018-19": "2019-20",
                   "2019-20": "2020-21", "2020-21": "2021-22",
                   "2021-22": "2022-23", "2022-23": "2023-24",
                   "2023-24": "2024-25", "2024-25": "2025-26"}
    for _, r in grp.iterrows():
        target = next_season.get(r["season"])
        if target is None:
            continue
        rates[(int(r["nba_api_id"]), target)] = {
            "pts_per_game": float(r["pts_per_game"]),
            "rs_mpg": float(r["rs_mpg"]),
            "pts_per_min": float(r["pts_per_min"]),
        }
    return rates


def compute_league_avg_pts_per_min(box: pd.DataFrame) -> float:
    rs = box[box["season_type"] == "Regular Season"]
    return float(rs["PTS"].sum() / rs["min_played"].sum())


def add_season_to_date_mpg(rs_df: pd.DataFrame) -> pd.DataFrame:
    """For each (player, season), compute expanding-mean MPG using only
    games STRICTLY before the current date. Avoids look-ahead.
    """
    rs_df = rs_df.sort_values(["nba_api_id", "season", "game_date"]).copy()
    # Cumulative MPG = expanding mean of min_played, lagged by 1 game
    grp = rs_df.groupby(["nba_api_id", "season"])
    rs_df["s2d_min_sum"] = grp["min_played"].cumsum() - rs_df["min_played"]
    rs_df["s2d_n_games"] = grp.cumcount()  # 0-indexed: # games BEFORE this one
    rs_df["s2d_mpg"] = np.where(
        rs_df["s2d_n_games"] > 0,
        rs_df["s2d_min_sum"] / rs_df["s2d_n_games"],
        np.nan,
    )
    rs_df["s2d_pts_sum"] = grp["PTS"].cumsum() - rs_df["PTS"]
    rs_df["s2d_pts_per_min"] = np.where(
        rs_df["s2d_min_sum"] > 0,
        rs_df["s2d_pts_sum"] / rs_df["s2d_min_sum"],
        np.nan,
    )
    return rs_df


def project_player_games_v2(rs_df: pd.DataFrame, ship: pd.DataFrame,
                             prior_rates: dict,
                             league_avg_ppm: float) -> pd.DataFrame:
    """V2 live-formula projection.

    expected_min:
      s2d_mpg if n_prior >= MIN_PRIOR_GAMES_FOR_S2D, else prior_season_mpg,
      else v6.1 mpg.

    proj_pts:
      Ship player → v6.1_PTS_per_game × (expected_min / v6.1_mpg)
      Non-ship + has prior → prior_pts_per_min × expected_min
      No prior → league_avg_ppm × expected_min
    """
    ship_lookup = ship.set_index("nba_api_id")[["PTS_per_game", "mpg"]].to_dict("index")

    n = len(rs_df)
    expected_min = np.zeros(n)
    proj_pts = np.zeros(n)
    mpg_source = np.array(["none"] * n, dtype=object)
    pts_source = np.array(["none"] * n, dtype=object)

    pid_arr = rs_df["nba_api_id"].values
    season_arr = rs_df["season"].values
    s2d_mpg = rs_df["s2d_mpg"].values
    s2d_n = rs_df["s2d_n_games"].values

    for i in range(n):
        pid = int(pid_arr[i])
        season = season_arr[i]

        # ── expected_min decision tree ────────────────────────────────
        if s2d_n[i] >= MIN_PRIOR_GAMES_FOR_S2D and not np.isnan(s2d_mpg[i]):
            em = float(s2d_mpg[i])
            mpg_source[i] = "s2d"
        elif (pid, season) in prior_rates:
            em = prior_rates[(pid, season)]["rs_mpg"]
            mpg_source[i] = "prior_rs"
        elif pid in ship_lookup and ship_lookup[pid]["mpg"] and ship_lookup[pid]["mpg"] > 0:
            em = float(ship_lookup[pid]["mpg"])
            mpg_source[i] = "ship_mpg"
        else:
            em = 0.0
            mpg_source[i] = "none"
        expected_min[i] = em

        # ── proj_pts decision tree ────────────────────────────────────
        if pid in ship_lookup:
            ppg = ship_lookup[pid]["PTS_per_game"]
            base_mpg = ship_lookup[pid]["mpg"]
            if base_mpg and base_mpg > 0:
                proj_pts[i] = ppg * (em / base_mpg)
                pts_source[i] = "ship"
                continue
        if (pid, season) in prior_rates:
            ppm = prior_rates[(pid, season)]["pts_per_min"]
            proj_pts[i] = ppm * em
            pts_source[i] = "prior_rs"
            continue
        proj_pts[i] = league_avg_ppm * em
        pts_source[i] = "league_avg"

    out = rs_df.copy()
    out["expected_min"] = expected_min
    out["proj_pts"] = proj_pts
    out["mpg_source"] = mpg_source
    out["pts_source"] = pts_source
    return out


def aggregate_to_team_game(player_proj: pd.DataFrame) -> pd.DataFrame:
    """Lineup foresight: only project players who actually played."""
    played = player_proj[player_proj["min_played"] > 0]
    agg = played.groupby(
        ["game_id", "game_date", "team_abbr", "is_home", "season"]
    ).agg(
        proj_pts=("proj_pts", "sum"),
        actual_pts=("PTS", "sum"),
        n_players=("nba_api_id", "size"),
        n_s2d=("mpg_source", lambda s: (s == "s2d").sum()),
        n_prior=("mpg_source", lambda s: (s == "prior_rs").sum()),
        n_ship_mpg=("mpg_source", lambda s: (s == "ship_mpg").sum()),
    ).reset_index()
    return agg


def join_to_lines(team_game: pd.DataFrame, lines: pd.DataFrame) -> pd.DataFrame:
    home = team_game[team_game["is_home"]].rename(
        columns={"team_abbr": "home_team_abbr",
                 "proj_pts": "home_proj_pts",
                 "actual_pts": "home_actual_pts"})
    away = team_game[~team_game["is_home"]].rename(
        columns={"team_abbr": "away_team_abbr",
                 "proj_pts": "away_proj_pts",
                 "actual_pts": "away_actual_pts"})
    game = home.merge(
        away[["game_id", "away_team_abbr", "away_proj_pts", "away_actual_pts"]],
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


def summarize(df: pd.DataFrame, label: str) -> dict:
    out = {"label": label, "n_games": int(len(df))}
    if len(df) == 0:
        return out
    out["bias_proj_total"] = float(df["resid_total_proj"].mean())
    out["mae_proj_total"] = float(df["resid_total_proj"].abs().mean())
    out["rmse_proj_total"] = float(np.sqrt((df["resid_total_proj"] ** 2).mean()))
    out["mae_close_total"] = float(df["resid_total_close"].abs().mean())
    out["rmse_close_total"] = float(np.sqrt((df["resid_total_close"] ** 2).mean()))
    out["bias_proj_margin"] = float(df["resid_margin_proj"].mean())
    out["mae_proj_margin"] = float(df["resid_margin_proj"].abs().mean())
    out["mae_close_margin"] = float(df["resid_margin_close"].abs().mean())
    out["mean_skew_total"] = float(df["skew_total"].mean())
    return out


def main():
    print("=" * 70)
    print("V2 backtest — live-formula simulation (season-to-date MPG)")
    print("=" * 70)

    print("\n[1/6] Loading data...")
    box = load_box()
    lines = pd.read_parquet(LINES_PATH)
    lines["game_date"] = pd.to_datetime(lines["game_date"])
    lines = lines[lines["season"].isin(BACKTEST_SEASONS)]
    lines = lines.dropna(subset=["close_total"])
    n_pre = len(lines)
    lines = lines[(lines["close_total"] >= 150) & (lines["close_total"] <= 290)]
    print(f"  lines: {len(lines):,} (filtered {n_pre - len(lines)} implausible)")
    ship = pd.read_csv(SHIP_PATH, usecols=["nba_api_id", "PTS_per_game", "mpg"])
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    print(f"  ship: {len(ship)} players")

    print("\n[2/6] Prior-season rates + league-avg per-min...")
    prior_rates = build_prior_season_rates(box)
    league_avg_ppm = compute_league_avg_pts_per_min(box)
    print(f"  prior cells: {len(prior_rates)}  league avg: {league_avg_ppm:.4f} pts/min")

    print("\n[3/6] Computing season-to-date MPG per player-season...")
    rs = box[box["season_type"] == "Regular Season"].copy()
    rs = rs[rs["season"].isin(BACKTEST_SEASONS)]
    rs = rs[rs["min_played"] > 0]
    rs = add_season_to_date_mpg(rs)
    print(f"  {len(rs):,} player-game rows with s2d MPG")

    print("\n[4/6] Projecting per player-game (live formula)...")
    player_proj = project_player_games_v2(rs, ship, prior_rates, league_avg_ppm)
    mpg_counts = player_proj["mpg_source"].value_counts()
    pts_counts = player_proj["pts_source"].value_counts()
    print(f"  mpg sources: {mpg_counts.to_dict()}")
    print(f"  pts sources: {pts_counts.to_dict()}")

    print("\n[5/6] Aggregating + joining to closes...")
    team_game = aggregate_to_team_game(player_proj)
    merged = join_to_lines(team_game, lines)
    print(f"  matched games: {len(merged):,}")
    merged.to_csv(OUT_DIR / "game_residuals.csv", index=False)

    print("\n[6/6] Summarizing v1 vs v2...")
    summaries_v2 = [summarize(merged, "ALL")]
    for season in BACKTEST_SEASONS:
        summaries_v2.append(summarize(merged[merged["season"] == season], season))
    sm_v2 = pd.DataFrame(summaries_v2)
    sm_v2.to_csv(OUT_DIR / "summary_by_season.csv", index=False)

    # V1 comparison
    if V1_RESIDUALS.exists():
        v1 = pd.read_csv(V1_RESIDUALS)
        summaries_v1 = [summarize(v1, "ALL")]
        for season in BACKTEST_SEASONS:
            summaries_v1.append(summarize(v1[v1["season"] == season], season))
        sm_v1 = pd.DataFrame(summaries_v1)

        comp = pd.DataFrame({
            "label": sm_v2["label"],
            "n_v2": sm_v2["n_games"],
            "v1_bias": sm_v1["bias_proj_total"],
            "v2_bias": sm_v2["bias_proj_total"],
            "v1_mae": sm_v1["mae_proj_total"],
            "v2_mae": sm_v2["mae_proj_total"],
            "v1_rmse": sm_v2["rmse_proj_total"],  # placeholder
            "v2_rmse": sm_v2["rmse_proj_total"],
            "vegas_mae": sm_v2["mae_close_total"],
            "vegas_rmse": sm_v2["rmse_close_total"],
        })
        comp["Δ_bias"] = comp["v2_bias"] - comp["v1_bias"]
        comp["Δ_mae"] = comp["v2_mae"] - comp["v1_mae"]
        comp.to_csv(OUT_DIR / "v1_vs_v2_comparison.csv", index=False)

        print("\n=== V1 vs V2 comparison ===")
        print(f"{'label':<10} {'n':>5} {'v1_bias':>8} {'v2_bias':>8} {'Δ':>6}  "
              f"{'v1_mae':>7} {'v2_mae':>7} {'Δ':>6}  {'vegas':>7}")
        for _, r in comp.iterrows():
            if r["n_v2"] == 0: continue
            print(f"{r['label']:<10} {int(r['n_v2']):>5} "
                  f"{r['v1_bias']:>+8.2f} {r['v2_bias']:>+8.2f} "
                  f"{r['Δ_bias']:>+6.2f}  "
                  f"{r['v1_mae']:>7.2f} {r['v2_mae']:>7.2f} "
                  f"{r['Δ_mae']:>+6.2f}  "
                  f"{r['vegas_mae']:>7.2f}")

    # Markdown writeup
    md = OUT_DIR / "BACKTEST_RESULTS_v2.md"
    with open(md, "w", encoding="utf-8") as f:
        f.write(f"# V2 backtest — live-formula simulation\n\n")
        f.write(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n\n")
        f.write("**Live formula:** expected_min = season-to-date MPG before game date "
                "(forward-clean). proj_pts = v6.1_PTS_per_game × (expected_min / v6.1_mpg) "
                "for ship players; pts_per_min × expected_min for fallback.\n\n")
        f.write("## V2 results by season\n\n")
        f.write(sm_v2.round(3).to_markdown(index=False) + "\n\n")
        if V1_RESIDUALS.exists():
            f.write("## V1 (actual-min) vs V2 (live-formula) comparison\n\n")
            f.write(comp.round(3).to_markdown(index=False) + "\n")
    print(f"\n  → {md}")
    print("\n=== done ===")


if __name__ == "__main__":
    main()
