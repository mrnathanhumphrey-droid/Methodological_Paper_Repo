"""Build WNBA adjudication candidate profiles for the Sloan adjudicated Test 1 fleet.

Per pre-reg SHA 28e3dc7 (`SLOAN_PRE_REG_TEST_1_WNBA_ADJUDICATED_v1.0_LOCKED.md`).

Scope: 112 candidates = 80 hyphenated + 31 metadata-Forward height>=76 + 1
metadata-Center height<=73.

Output: `C:/WNBA Projections/audit_runs/test_1_replication/sloan_adjudicated/wnba_candidate_profiles.json`
"""
import json
import os
from pathlib import Path

import pandas as pd

ROOT = Path("C:/WNBA Projections")
META_PATH = ROOT / "data/processed/player_metadata.csv"
GAMES_PATH = ROOT / "data/processed/player_game_logs.csv"
OUT_DIR = ROOT / "audit_runs/test_1_replication/sloan_adjudicated"
OUT_PATH = OUT_DIR / "wnba_candidate_profiles.json"

SEASONS_IN_WINDOW = [2023, 2024, 2025]
MIN_GP_PER_SEASON = 10


def is_hyphenated(pos: str) -> bool:
    return isinstance(pos, str) and "-" in pos


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    meta = pd.read_csv(META_PATH)
    meta["position"] = meta["position"].fillna("Unknown")
    meta["height_inches"] = pd.to_numeric(meta["height_inches"], errors="coerce")

    # Build adjudication scope per pre-reg §2.3
    hyph_mask = meta["position"].apply(is_hyphenated)
    tall_fwd_mask = (meta["position"] == "Forward") & (meta["height_inches"] >= 76)
    short_ctr_mask = (meta["position"] == "Center") & (meta["height_inches"] <= 73)

    scope = meta[hyph_mask | tall_fwd_mask | short_ctr_mask].copy()
    print(f"WNBA candidates: {len(scope)} "
          f"(hyph={hyph_mask.sum()}, tall_fwd={tall_fwd_mask.sum()}, short_ctr={short_ctr_mask.sum()})")

    # Load game logs and compute career averages within the 2023-2025 window
    games = pd.read_csv(GAMES_PATH)
    print(f"WNBA game logs: {len(games)} rows, columns: {list(games.columns)[:15]}")

    # Try to identify season column
    season_col = None
    for cand in ["season", "year", "Season", "Year"]:
        if cand in games.columns:
            season_col = cand
            break
    if season_col is None:
        raise RuntimeError("No season column found in game logs")

    # Stat columns — basketball-reference names
    stat_cols = {}
    for std_name, candidates in {
        "PTS": ["PTS", "pts", "points"],
        "REB": ["TRB", "REB", "reb", "rebounds", "trb"],
        "AST": ["AST", "ast", "assists"],
        "BLK": ["BLK", "blk", "blocks"],
        "FG3M": ["FG3M", "3PM", "fg3m", "3p", "fg3"],
    }.items():
        for c in candidates:
            if c in games.columns:
                stat_cols[std_name] = c
                break

    # If REB not found but orb + drb are, synthesize it
    if "REB" not in stat_cols and "orb" in games.columns and "drb" in games.columns:
        games["_reb"] = games["orb"].fillna(0) + games["drb"].fillna(0)
        stat_cols["REB"] = "_reb"

    print(f"Stat columns mapped: {stat_cols}")

    # Filter to window (note: must filter AFTER synthesizing _reb so it survives)
    games_window = games[games[season_col].isin(SEASONS_IN_WINDOW)].copy()
    print(f"WNBA game logs in window: {len(games_window)} rows")

    # Identify player_slug column in games
    slug_col = "player_slug" if "player_slug" in games.columns else None
    if slug_col is None:
        # Try alternative joins
        for c in ["slug", "player_id", "Player"]:
            if c in games.columns:
                slug_col = c
                break
    print(f"Slug column in games: {slug_col}")

    profiles = []
    for _, row in scope.iterrows():
        slug = row["player_slug"]
        name = row["full_name"]
        pos = row["position"]
        height = row["height_inches"]
        weight = row.get("weight_lbs", None)

        # Find this player's game logs
        if slug_col:
            pg = games_window[games_window[slug_col] == slug]
        else:
            pg = games_window.iloc[0:0]

        # Per-season GP and career averages
        per_season = {}
        seasons_in_window_count = 0
        for s in SEASONS_IN_WINDOW:
            sg = pg[pg[season_col] == s]
            gp = len(sg)
            per_season[str(s)] = {"GP": gp}
            if gp >= MIN_GP_PER_SEASON:
                seasons_in_window_count += 1

        # Career averages over qualifying seasons (GP >= 10)
        qualifying_games = pd.concat([
            pg[pg[season_col] == s] for s in SEASONS_IN_WINDOW
            if (pg[season_col] == s).sum() >= MIN_GP_PER_SEASON
        ]) if seasons_in_window_count > 0 else pg.iloc[0:0]

        if len(qualifying_games) > 0:
            avg_pts = float(qualifying_games[stat_cols["PTS"]].mean()) if "PTS" in stat_cols else None
            avg_reb = float(qualifying_games[stat_cols["REB"]].mean()) if "REB" in stat_cols else None
            avg_ast = float(qualifying_games[stat_cols["AST"]].mean()) if "AST" in stat_cols else None
            avg_blk = float(qualifying_games[stat_cols["BLK"]].mean()) if "BLK" in stat_cols else None
            avg_fg3m = float(qualifying_games[stat_cols["FG3M"]].mean()) if "FG3M" in stat_cols else None
        else:
            avg_pts = avg_reb = avg_ast = avg_blk = avg_fg3m = None

        # Metadata bucket per pre-reg §2.3 (inclusive: Center, Center-Forward, Forward-Center)
        if pos in ("Center", "Center-Forward", "Forward-Center"):
            metadata_bucket = "Center"
        else:
            metadata_bucket = "non-Center"

        profiles.append({
            "name": name,
            "player_slug": slug,
            "metadata_position": pos,
            "metadata_bucket_inclusive": metadata_bucket,
            "height_inches": None if pd.isna(height) else float(height),
            "career_seasons_in_window": seasons_in_window_count,
            "career_avg_PTS_per_game": None if avg_pts is None else round(avg_pts, 3),
            "career_avg_REB_per_game": None if avg_reb is None else round(avg_reb, 3),
            "career_avg_AST_per_game": None if avg_ast is None else round(avg_ast, 3),
            "career_avg_BLK_per_game": None if avg_blk is None else round(avg_blk, 3),
            "career_avg_FG3M_per_game": None if avg_fg3m is None else round(avg_fg3m, 3),
        })

    out = {
        "league": "WNBA",
        "pre_reg_sha": "28e3dc7",
        "pre_reg_file": "RMD_SRC_PIPELINE/SLOAN_PRE_REG_TEST_1_WNBA_ADJUDICATED_v1.0_LOCKED.md",
        "seasons_in_window": SEASONS_IN_WINDOW,
        "min_gp_per_season": MIN_GP_PER_SEASON,
        "n_candidates": len(profiles),
        "candidates": profiles,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"Wrote {OUT_PATH}: {len(profiles)} candidates")


if __name__ == "__main__":
    main()
