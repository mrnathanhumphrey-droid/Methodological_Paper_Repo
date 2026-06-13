"""Backtest game totals + spread vs Vegas closing lines.

Approach A (conditional on actual minutes):
  For each player-game, project pts via:
    proj_player_pts = per_game × (actual_min / RS_mpg)
  where per_game + RS_mpg come from:
    - v6.1 25-26 ship (for ship players)
    - prior-season RS rate (for non-ship players; avoids in-season look-ahead)

  Aggregate to team-game: home_proj_pts, away_proj_pts.
  Project total = home + away; project margin = home - away.

  Compare to close_total, close_spread_home from
  D:/sports_lines/data/vegas/nba_game_lines_extended.parquet.

Outputs in runs/run_nba_game_totals_22_26/:
  - game_residuals.csv (per game: proj, close, actual + residuals)
  - summary_by_season.csv
  - summary_by_stratum.csv (close vs blowout, pace tier, OT, b2b)
  - bias_calibration.csv (proj vs close skew, hit-floor rate)
  - BACKTEST_RESULTS.md

Scope: 22-23 + 23-24 + 24-25 RS games (excluding playoffs since playoff
regime multiplier overlays are season-specific; can run a separate playoff
backtest if desired).
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
OUT_DIR = REPO / "runs" / "run_nba_game_totals_22_26"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BACKTEST_SEASONS = ["2022-23", "2023-24", "2024-25", "2025-26"]
PRIOR_SEASON = {"2022-23": "2021-22", "2023-24": "2022-23",
                "2024-25": "2023-24", "2025-26": "2024-25"}


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
    """{(pid, season): {'pts_per_game': ..., 'rs_mpg': ...}} from PRIOR season RS."""
    rs = box[box["season_type"] == "Regular Season"]
    # Aggregate per (player, season): games played, total PTS, total min
    grp = rs.groupby(["nba_api_id", "season"]).agg(
        games=("game_id", "nunique"),
        total_pts=("PTS", "sum"),
        total_min=("min_played", "sum"),
    ).reset_index()
    grp = grp[grp["games"] >= 10]  # min sample for stable rate
    grp["pts_per_game"] = grp["total_pts"] / grp["games"]
    grp["rs_mpg"] = grp["total_min"] / grp["games"]
    # Index by (pid, season-that-this-data-projects-FOR)
    # E.g. player's 21-22 stats → used for 22-23 projection
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
        }
    return rates


def compute_league_avg_pts_per_min(box: pd.DataFrame) -> float:
    """League-average PTS/min across RS games — fallback for rookies / late
    signings with no prior-season record. Computed from box scores so it
    naturally reflects the era's scoring environment.
    """
    rs = box[box["season_type"] == "Regular Season"]
    total_pts = float(rs["PTS"].sum())
    total_min = float(rs["min_played"].sum())
    return total_pts / total_min if total_min > 0 else 0.42


def project_player_games(box: pd.DataFrame, ship: pd.DataFrame,
                         prior_rates: dict,
                         league_avg_ppm: float) -> pd.DataFrame:
    """Per player-game, project PTS via per_game × (min / RS_mpg).

    Source priority:
      1. v6.1 ship (PTS_per_game, mpg)
      2. Prior-season RS rate
      3. League-average PTS/min × actual minutes (rookies / late signings)
    """
    rs = box[box["season_type"] == "Regular Season"].copy()
    rs = rs[rs["season"].isin(BACKTEST_SEASONS)]
    rs = rs[rs["min_played"] > 0]

    ship_lookup = ship.set_index("nba_api_id")[["PTS_per_game", "mpg"]].to_dict("index")

    proj_pts = np.zeros(len(rs))
    source = np.array(["none"] * len(rs), dtype=object)

    pid_arr = rs["nba_api_id"].values
    min_arr = rs["min_played"].values
    season_arr = rs["season"].values

    for i in range(len(rs)):
        pid = int(pid_arr[i])
        min_g = float(min_arr[i])
        if pid in ship_lookup:
            ppg = ship_lookup[pid]["PTS_per_game"]
            rs_mpg = ship_lookup[pid]["mpg"]
            if rs_mpg and rs_mpg > 0:
                proj_pts[i] = ppg * (min_g / rs_mpg)
                source[i] = "ship"
                continue
        # Fallback to prior-season RS rate
        key = (pid, season_arr[i])
        if key in prior_rates:
            r = prior_rates[key]
            if r["rs_mpg"] > 0:
                proj_pts[i] = r["pts_per_game"] * (min_g / r["rs_mpg"])
                source[i] = "prior_rs"
                continue
        # League-average per-minute rate × actual minutes — robust low-info
        # fallback for rookies + late signings with no prior season.
        proj_pts[i] = league_avg_ppm * min_g
        source[i] = "league_avg"
    rs = rs.copy()
    rs["proj_pts"] = proj_pts
    rs["proj_source"] = source
    return rs


def aggregate_to_team_game(player_proj: pd.DataFrame) -> pd.DataFrame:
    """Sum proj_pts per team-game; include actual final from PTS sum."""
    agg = player_proj.groupby(
        ["game_id", "game_date", "team_abbr", "is_home", "season"]
    ).agg(
        proj_pts=("proj_pts", "sum"),
        actual_pts=("PTS", "sum"),
        n_players=("nba_api_id", "size"),
        n_ship=("proj_source", lambda s: (s == "ship").sum()),
        n_prior=("proj_source", lambda s: (s == "prior_rs").sum()),
        n_none=("proj_source", lambda s: (s == "none").sum()),
        coverage_pct=("proj_source",
                       lambda s: 100 * ((s == "ship").sum() + (s == "prior_rs").sum()) / len(s)),
    ).reset_index()
    return agg


def join_to_lines(team_game: pd.DataFrame, lines: pd.DataFrame) -> pd.DataFrame:
    """Wide form: one row per game with home + away projections + close lines."""
    home = team_game[team_game["is_home"]].rename(
        columns={"team_abbr": "home_team_abbr",
                 "proj_pts": "home_proj_pts",
                 "actual_pts": "home_actual_pts",
                 "coverage_pct": "home_coverage_pct"})
    away = team_game[~team_game["is_home"]].rename(
        columns={"team_abbr": "away_team_abbr",
                 "proj_pts": "away_proj_pts",
                 "actual_pts": "away_actual_pts",
                 "coverage_pct": "away_coverage_pct"})
    game = home.merge(
        away[["game_id", "away_team_abbr", "away_proj_pts",
              "away_actual_pts", "away_coverage_pct"]],
        on="game_id", how="inner",
    )

    game["proj_total"] = game["home_proj_pts"] + game["away_proj_pts"]
    game["actual_total"] = game["home_actual_pts"] + game["away_actual_pts"]
    game["proj_margin_home"] = game["home_proj_pts"] - game["away_proj_pts"]
    game["actual_margin_home"] = game["home_actual_pts"] - game["away_actual_pts"]

    lines["game_date"] = pd.to_datetime(lines["game_date"])
    merged = game.merge(
        lines[["game_date", "home_team_abbr", "away_team_abbr",
               "close_total", "close_spread_home", "home_ml", "away_ml"]],
        on=["game_date", "home_team_abbr", "away_team_abbr"],
        how="inner",
    )

    # Residuals
    # Vegas spread is signed home (negative = home favored). Our margin is
    # home-away; "spread_home" sign-flipped for comparable units: a -7 spread
    # implies home is expected to win by 7, so projected margin should ≈ +7.
    merged["close_margin_home_implied"] = -merged["close_spread_home"]

    merged["resid_total_proj"] = merged["actual_total"] - merged["proj_total"]
    merged["resid_total_close"] = merged["actual_total"] - merged["close_total"]
    merged["resid_margin_proj"] = merged["actual_margin_home"] - merged["proj_margin_home"]
    merged["resid_margin_close"] = merged["actual_margin_home"] - merged["close_margin_home_implied"]

    merged["skew_total"] = merged["proj_total"] - merged["close_total"]
    merged["skew_margin"] = merged["proj_margin_home"] - merged["close_margin_home_implied"]

    return merged


def summarize(df: pd.DataFrame, label: str = "all") -> dict:
    out = {"label": label, "n_games": int(len(df))}
    if len(df) == 0:
        return out
    out["mean_proj_total"] = float(df["proj_total"].mean())
    out["mean_close_total"] = float(df["close_total"].mean())
    out["mean_actual_total"] = float(df["actual_total"].mean())

    out["bias_proj_total"] = float(df["resid_total_proj"].mean())
    out["bias_close_total"] = float(df["resid_total_close"].mean())

    out["mae_proj_total"] = float(df["resid_total_proj"].abs().mean())
    out["mae_close_total"] = float(df["resid_total_close"].abs().mean())
    out["rmse_proj_total"] = float(np.sqrt((df["resid_total_proj"] ** 2).mean()))
    out["rmse_close_total"] = float(np.sqrt((df["resid_total_close"] ** 2).mean()))

    out["bias_proj_margin"] = float(df["resid_margin_proj"].mean())
    out["bias_close_margin"] = float(df["resid_margin_close"].mean())
    out["mae_proj_margin"] = float(df["resid_margin_proj"].abs().mean())
    out["mae_close_margin"] = float(df["resid_margin_close"].abs().mean())

    out["mean_skew_total"] = float(df["skew_total"].mean())
    out["mean_skew_margin"] = float(df["skew_margin"].mean())

    # "Hit the floor": when proj < close, how often does actual go under close?
    proj_under = df[df["proj_total"] < df["close_total"]]
    proj_over = df[df["proj_total"] > df["close_total"]]
    if len(proj_under):
        out["proj_under_close_actual_under_rate"] = float(
            (proj_under["actual_total"] < proj_under["close_total"]).mean())
        out["n_proj_under"] = int(len(proj_under))
    if len(proj_over):
        out["proj_over_close_actual_over_rate"] = float(
            (proj_over["actual_total"] > proj_over["close_total"]).mean())
        out["n_proj_over"] = int(len(proj_over))

    # Spread version
    home_proj_favored = df[df["proj_margin_home"] > df["close_margin_home_implied"]]
    if len(home_proj_favored):
        # If we project home to cover the close spread, did they?
        out["proj_home_covers_actual_covers_rate"] = float(
            (home_proj_favored["actual_margin_home"] >
             home_proj_favored["close_margin_home_implied"]).mean())
    return out


def main():
    print("=" * 70)
    print("Game totals + spread backtest vs Vegas closes (Approach A: cond. on min)")
    print("=" * 70)

    print("\n[1/5] Loading data...")
    box = load_box()
    print(f"  box: {len(box):,} rows  seasons: {sorted(box['season'].unique())}")
    if not LINES_PATH.exists():
        print(f"  ERROR: {LINES_PATH} not found — run consolidate_game_lines.py first")
        return
    lines = pd.read_parquet(LINES_PATH)
    lines["game_date"] = pd.to_datetime(lines["game_date"])
    lines = lines[lines["season"].isin(BACKTEST_SEASONS)]
    lines = lines.dropna(subset=["close_total"])
    # Filter out corrupt SBR-parsed rows where close_total slipped to the
    # spread value (~1-20). NBA game totals are always >150 in modern era.
    n_pre = len(lines)
    lines = lines[(lines["close_total"] >= 150) & (lines["close_total"] <= 290)]
    n_drop = n_pre - len(lines)
    if n_drop > 0:
        print(f"  filtered {n_drop} games with implausible close_total (<150 or >290)")
    print(f"  lines: {len(lines):,} games with close_total in backtest seasons")
    ship = pd.read_csv(SHIP_PATH, usecols=["nba_api_id", "PTS_per_game", "mpg"])
    ship["nba_api_id"] = ship["nba_api_id"].astype(int)
    print(f"  ship: {len(ship)} players")

    print("\n[2/5] Building prior-season RS rate fallback + league-avg per-min...")
    prior_rates = build_prior_season_rates(box)
    league_avg_ppm = compute_league_avg_pts_per_min(box)
    print(f"  {len(prior_rates)} (player, target_season) prior-rate cells")
    print(f"  league avg PTS/min = {league_avg_ppm:.4f}")

    print("\n[3/5] Projecting per player-game...")
    player_proj = project_player_games(box, ship, prior_rates, league_avg_ppm)
    src_counts = player_proj["proj_source"].value_counts()
    print(f"  player-games projected: {len(player_proj):,}")
    print(f"  source breakdown: {src_counts.to_dict()}")
    print(f"  coverage %: {100 * (1 - src_counts.get('none', 0) / len(player_proj)):.2f}%")

    print("\n[4/5] Aggregating to team-game + joining to closing lines...")
    team_game = aggregate_to_team_game(player_proj)
    merged = join_to_lines(team_game, lines)
    print(f"  matched games: {len(merged):,}")

    merged.to_csv(OUT_DIR / "game_residuals.csv", index=False)
    print(f"  → {OUT_DIR / 'game_residuals.csv'}")

    print("\n[5/5] Computing summaries...")
    # Overall + per-season
    summaries = [summarize(merged, "ALL")]
    for season in BACKTEST_SEASONS:
        sub = merged[merged["season"] == season]
        summaries.append(summarize(sub, season))

    summary_df = pd.DataFrame(summaries)
    summary_df.to_csv(OUT_DIR / "summary_by_season.csv", index=False)
    print(f"  → {OUT_DIR / 'summary_by_season.csv'}")

    # Stratifications
    strat_rows = []
    # By proj_total quantile (low/mid/high totals)
    merged["proj_total_q"] = pd.qcut(merged["proj_total"], 4,
                                      labels=["Q1_low", "Q2", "Q3", "Q4_high"])
    for q, sub in merged.groupby("proj_total_q"):
        strat_rows.append(summarize(sub, f"proj_total_{q}"))
    # By spread tier (blowout vs close)
    merged["spread_tier"] = pd.cut(
        merged["close_spread_home"].abs(),
        bins=[-0.01, 3, 7, 12, 100],
        labels=["pickem", "short", "med", "long"])
    for t, sub in merged.groupby("spread_tier"):
        strat_rows.append(summarize(sub, f"spread_{t}"))
    # By coverage tier (where our model is thin)
    merged["min_coverage"] = merged[["home_coverage_pct", "away_coverage_pct"]].min(axis=1)
    merged["cov_tier"] = pd.cut(
        merged["min_coverage"], bins=[0, 80, 95, 100.01],
        labels=["thin", "medium", "full"])
    for t, sub in merged.groupby("cov_tier"):
        strat_rows.append(summarize(sub, f"coverage_{t}"))

    strat_df = pd.DataFrame(strat_rows)
    strat_df.to_csv(OUT_DIR / "summary_by_stratum.csv", index=False)
    print(f"  → {OUT_DIR / 'summary_by_stratum.csv'}")

    # Top-line print
    print("\n=== HEADLINE ===")
    print(f"{'label':<14} {'n':>5} {'bias_pT':>8} {'mae_pT':>7} {'rmse_pT':>8} "
          f"{'mae_cT':>7} {'rmse_cT':>8} {'skew_T':>7}")
    for s in summaries:
        if s["n_games"] == 0: continue
        print(f"{s['label']:<14} {s['n_games']:>5} "
              f"{s['bias_proj_total']:>+8.2f} {s['mae_proj_total']:>7.2f} "
              f"{s['rmse_proj_total']:>8.2f} "
              f"{s['mae_close_total']:>7.2f} {s['rmse_close_total']:>8.2f} "
              f"{s['mean_skew_total']:>+7.2f}")
    print()
    print("Columns:")
    print("  bias_pT = mean(actual - projected) total  (+ = we under-projected)")
    print("  mae/rmse_pT = miss on total vs OUR projection")
    print("  mae/rmse_cT = miss on total vs VEGAS close (lower = harder to beat)")
    print("  skew_T = mean(proj - close)  (+ = we project high, - = we project low)")

    # Write markdown
    md_path = OUT_DIR / "BACKTEST_RESULTS.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Game Totals + Spread Backtest vs Vegas Close\n\n")
        f.write(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n\n")
        f.write(f"**Design:** Approach A (conditional on actual minutes). "
                f"For each player-game, project PTS via "
                f"`v6.1 PTS_per_game × (actual_min / RS_mpg)`. "
                f"Players not in v6.1 25-26 ship fall back to prior-season "
                f"RS rate. Aggregate to team-game, compare home_proj+away_proj "
                f"to Vegas close_total + close_spread_home.\n\n")
        f.write(f"**Scope:** RS games in {', '.join(BACKTEST_SEASONS)}.\n\n")
        f.write(f"**Matched games:** {len(merged):,}\n\n")
        f.write("## By season\n\n")
        f.write(summary_df.round(3).to_markdown(index=False) + "\n\n")
        f.write("## By stratum\n\n")
        f.write(strat_df.round(3).to_markdown(index=False) + "\n")
    print(f"\n  → {md_path}")
    print("\n=== done ===")


if __name__ == "__main__":
    main()
