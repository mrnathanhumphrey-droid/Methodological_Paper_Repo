"""Produce daily AST projections for nba_ev consumption.

Forward-clean methodology (validated 2026-05-26 in backtest_player_props_rolling_clean):
  - Prior-season RS AST per-game, Bayesian shrunk toward league mean (k=30)
  - Today's season-to-date MPG (strictly prior games this season)
  - proj_ast = shrunk_ast_per_game × (s2d_mpg / shrunk_baseline_mpg)

Contract (mirrors playoff_projections.parquet):
  Path: D:/NBA Projections/audit_runs/{date}/ast_projections.parquet
  Required fields per row:
    - nba_api_id        (int)
    - game_date         (string YYYY-MM-DD)
    - player_name       (str)
    - proj_ast          (float, post-shrinkage projection)
    - prior_ast_per_game (float, before MPG adjustment)
    - prior_mpg         (float, baseline)
    - s2d_mpg           (float, this season's actual to-date)
    - n_prior_games     (int, sample size for prior-season rate)
    - mpg_source        ('s2d'|'prior_mpg_fallback')

recommend.py consumption: for each player-game with a live AST line, compute
edge = proj_ast - line. Bet OVER if edge ≥ +EDGE_THRESHOLD, UNDER if ≤ -EDGE_THRESHOLD.
Recommended threshold: 1.0 assists (validated +8.7% ROI at edges ≥ 1.85).

Usage:
  python scripts/produce_ast_projections.py
  python scripts/produce_ast_projections.py --date 2026-05-27
  python scripts/produce_ast_projections.py --date 2026-05-27 --dry-run
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import argparse
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("D:/NBA Projections")
BOX_PATH = REPO / "data" / "parquet" / "historical_box_scores.parquet"
PLAYOFFS_R1 = REPO / "data" / "parquet" / "playoffs" / "round1"
PLAYOFFS_EXTRA = REPO / "data" / "parquet" / "playoffs" / "extra_rounds"
AUDIT_BASE = REPO / "audit_runs"

SHRINK_K = 30
MIN_PRIOR_GAMES_FOR_S2D = 5
EDGE_THRESHOLD_DEFAULT = 1.0  # assists

NEXT_SEASON = {
    "2017-18": "2018-19", "2018-19": "2019-20", "2019-20": "2020-21",
    "2020-21": "2021-22", "2021-22": "2022-23", "2022-23": "2023-24",
    "2023-24": "2024-25", "2024-25": "2025-26", "2025-26": "2026-27",
}


def parse_min(m):
    if pd.isna(m): return 0.0
    if isinstance(m, (int, float)): return float(m)
    try:
        parts = str(m).split(":")
        return float(parts[0]) + (float(parts[1]) / 60 if len(parts) > 1 else 0)
    except (ValueError, TypeError):
        return 0.0


def today_et() -> str:
    now = datetime.now(timezone.utc)
    et_offset = timedelta(hours=-4) if 3 <= now.month <= 10 else timedelta(hours=-5)
    return (now + et_offset).date().isoformat()


def current_nba_season(date_iso: str | None = None) -> str:
    d = pd.Timestamp(date_iso or today_et())
    y = d.year
    return f"{y}-{str(y + 1)[-2:]}" if d.month >= 8 else f"{y - 1}-{str(y)[-2:]}"


def load_box() -> pd.DataFrame:
    cols = ["nba_api_id", "game_id", "game_date", "season", "season_type",
            "minutes", "AST"]
    box = pd.read_parquet(BOX_PATH, columns=cols)
    box = box[pd.notna(box["nba_api_id"])].copy()
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    box["game_date"] = pd.to_datetime(box["game_date"])
    box["min_played"] = box["minutes"].apply(parse_min)
    return box


def build_prior_season_rates(box: pd.DataFrame, target_season: str) -> tuple[dict, float]:
    """{(pid, target_season): {ast_per_game, mpg, n}} shrunk toward league mean."""
    rs = box[(box["season_type"] == "Regular Season") & (box["min_played"] >= 5)]
    league_mean = float(rs["AST"].mean())

    prior_season = None
    for s, ns in NEXT_SEASON.items():
        if ns == target_season:
            prior_season = s
            break
    # Pool all prior seasons through the one immediately before target
    # (most-recent prior season carries the freshest rate but use all priors
    # for richer sample). Simpler v1: use only immediate prior season.

    grp = rs.groupby(["nba_api_id", "season"]).agg(
        games=("game_id", "nunique"),
        total_ast=("AST", "sum"),
        total_min=("min_played", "sum"),
    ).reset_index()
    grp = grp[grp["season"] == prior_season]
    if grp.empty:
        return {}, league_mean

    out = {}
    for _, r in grp.iterrows():
        n = int(r["games"])
        rate = r["total_ast"] / n
        mpg = r["total_min"] / n
        shrunk_rate = (n * rate + SHRINK_K * league_mean) / (n + SHRINK_K)
        out[int(r["nba_api_id"])] = {
            "ast_per_game": shrunk_rate,
            "mpg": mpg,
            "n_prior_games": n,
        }
    return out, league_mean


def s2d_mpg_through_yesterday(box: pd.DataFrame, target_date: str,
                                season: str) -> dict:
    """{pid: s2d_mpg} computed from games STRICTLY before target_date."""
    cutoff = pd.Timestamp(target_date)
    sub = box[(box["season_type"] == "Regular Season") &
              (box["season"] == season) &
              (box["min_played"] > 0) &
              (box["game_date"] < cutoff)]
    grp = sub.groupby("nba_api_id").agg(
        total_min=("min_played", "sum"),
        games=("game_id", "nunique"),
    ).reset_index()
    grp = grp[grp["games"] >= MIN_PRIOR_GAMES_FOR_S2D]
    return dict(zip(grp["nba_api_id"].astype(int),
                     grp["total_min"] / grp["games"]))


def active_cohort_for_date(target_date: str, season: str) -> pd.DataFrame:
    """Players expected to play on target_date.

    During RS: from LeagueGameLog or schedule. During playoffs: from round1
    + extra_rounds active player traditional tables (matches the playoff
    producer's cohort definition).
    """
    frames = []
    for src in [PLAYOFFS_R1, PLAYOFFS_EXTRA]:
        for fn in ["traditional_t0.parquet", "traditional_t1.parquet"]:
            p = src / fn
            if not p.exists(): continue
            df_full = pd.read_parquet(p)
            wanted = [c for c in ["personId", "season", "gameId", "minutes",
                                    "firstName", "familyName"]
                       if c in df_full.columns]
            sub = df_full[wanted]
            sub = sub[sub["season"] == season]
            frames.append(sub)
    if not frames:
        return pd.DataFrame(columns=["nba_api_id", "name"])
    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=["personId"])
    df["personId"] = df["personId"].astype(int)
    df["min_played"] = df["minutes"].apply(parse_min)
    df = df[df["min_played"] > 0]
    df["nba_api_id"] = df["personId"].astype(int)
    df["name"] = df["firstName"].fillna("") + " " + df["familyName"].fillna("")
    return df[["nba_api_id", "name"]].drop_duplicates()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=today_et())
    ap.add_argument("--season", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--edge-threshold", type=float, default=EDGE_THRESHOLD_DEFAULT)
    args = ap.parse_args()

    date_iso = args.date
    season = args.season or current_nba_season(date_iso)
    print(f"=== AST projections for {date_iso}  (season={season}) ===")

    print("\n[1/4] Loading box scores...")
    box = load_box()
    print(f"  {len(box):,} rows")

    print("\n[2/4] Building prior-season shrunk AST rates...")
    prior_rates, league_mean = build_prior_season_rates(box, season)
    print(f"  {len(prior_rates):,} players with prior-season data")
    print(f"  league mean AST: {league_mean:.3f}/game (shrinkage target)")

    print("\n[3/4] Computing s2d MPG through yesterday...")
    s2d_lookup = s2d_mpg_through_yesterday(box, date_iso, season)
    print(f"  {len(s2d_lookup):,} players with s2d MPG (≥{MIN_PRIOR_GAMES_FOR_S2D} prior games)")

    print("\n[4/4] Determining active cohort + projecting...")
    cohort = active_cohort_for_date(date_iso, season)
    print(f"  active cohort: {len(cohort)} players")

    rows = []
    for _, p in cohort.iterrows():
        pid = int(p["nba_api_id"])
        name = p["name"]
        prior = prior_rates.get(pid)
        if prior is None:
            # No prior season — skip (live system can fall back if needed)
            continue
        base_mpg = prior["mpg"]
        if base_mpg <= 0:
            continue
        s2d = s2d_lookup.get(pid)
        if s2d is None:
            # No s2d MPG yet — early-season; use prior MPG as forecast
            expected_mpg = base_mpg
            mpg_source = "prior_mpg_fallback"
        else:
            expected_mpg = float(s2d)
            mpg_source = "s2d"
        proj_ast = prior["ast_per_game"] * (expected_mpg / base_mpg)
        rows.append({
            "nba_api_id": pid,
            "game_date": date_iso,
            "player_name": name,
            "proj_ast": proj_ast,
            "prior_ast_per_game": prior["ast_per_game"],
            "prior_mpg": base_mpg,
            "s2d_mpg": s2d if s2d is not None else np.nan,
            "expected_mpg": expected_mpg,
            "n_prior_games": prior["n_prior_games"],
            "mpg_source": mpg_source,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        print("  no projections to emit")
        return
    print(f"  emitted {len(df)} player projections")
    print(f"  proj_ast: min={df['proj_ast'].min():.2f} "
          f"median={df['proj_ast'].median():.2f} max={df['proj_ast'].max():.2f}")
    print(f"  mpg_source breakdown: {df['mpg_source'].value_counts().to_dict()}")

    if args.dry_run:
        print("\nFirst 10 rows:")
        print(df.sort_values("proj_ast", ascending=False).head(10).to_string(index=False))
        print(f"\n[dry-run] not writing")
        return

    out_dir = AUDIT_BASE / date_iso
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ast_projections.parquet"
    df.to_parquet(out_path, index=False)
    print(f"\n  → {out_path}")

    sidecar = {
        "produced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bet_date": date_iso,
        "season": season,
        "n_rows": len(df),
        "method": "rolling-clean prior-season Bayesian-shrunk AST × s2d_mpg ratio",
        "shrinkage_k": SHRINK_K,
        "min_prior_games_for_s2d": MIN_PRIOR_GAMES_FOR_S2D,
        "league_mean_ast_per_game": league_mean,
        "recommended_edge_threshold": args.edge_threshold,
        "backtest_validation": (
            "Forward-clean backtest 2026-05-26: AST market 56.7% WR / +3.95% ROI "
            "on n=7,717. Big-edge tier (≥1.85): 59.5% WR / +8.7% ROI."
        ),
    }
    with open(out_dir / "ast_projections_metadata.json", "w") as f:
        json.dump(sidecar, f, indent=2, default=str)
    print(f"  → {out_dir / 'ast_projections_metadata.json'}")


if __name__ == "__main__":
    main()
