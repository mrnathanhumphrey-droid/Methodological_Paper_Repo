"""Build NCAA D1 Men's + NCAA D1 Women's adjudication candidate profiles.

Per pre-reg SHA 28e3dc7 (`SLOAN_PRE_REG_TEST_1_NCAA_M_ADJUDICATED_v1.0_LOCKED.md`
and `SLOAN_PRE_REG_TEST_1_NCAA_W_ADJUDICATED_v1.0_LOCKED.md`).

NCAA M scope: 2,135 = 1,714 metadata-F with height>=80 + 417 metadata-C + 4 hyphenated.
NCAA W scope: 1,149 = 453 metadata-F with height>=75 + 398 metadata-C + 298 hyphenated.

Usage: python build_ncaa_candidate_profiles.py m
       python build_ncaa_candidate_profiles.py w
"""
import json
import sys
from pathlib import Path

import pandas as pd

CONFIG = {
    "m": {
        "root": Path("C:/NCAA D1 Mens"),
        "league": "NCAA_M",
        "height_F_floor": 80,
        "height_C_short": 80,  # all metadata-C, no height cap
        "seasons_in_window": [2024, 2025],
        "pre_reg_file": "RMD_SRC_PIPELINE/SLOAN_PRE_REG_TEST_1_NCAA_M_ADJUDICATED_v1.0_LOCKED.md",
    },
    "w": {
        "root": Path("C:/NCAA D1 Womens"),
        "league": "NCAA_W",
        "height_F_floor": 75,
        "height_C_short": 75,
        "seasons_in_window": [2024, 2025],
        "pre_reg_file": "RMD_SRC_PIPELINE/SLOAN_PRE_REG_TEST_1_NCAA_W_ADJUDICATED_v1.0_LOCKED.md",
    },
}

MIN_GP_PER_SEASON = 10


def is_hyphenated(pos: str) -> bool:
    return isinstance(pos, str) and "-" in pos


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in CONFIG:
        print("Usage: python build_ncaa_candidate_profiles.py {m|w}")
        sys.exit(1)

    cfg = CONFIG[sys.argv[1]]
    ROOT = cfg["root"]
    META_PATH = ROOT / "data/processed/player_metadata.csv"
    GAMES_PATH = ROOT / "data/processed/player_game_logs.csv"
    CLASS_PATH = ROOT / "data/processed/class_year.csv"
    OUT_DIR = ROOT / "audit_runs/test_1_replication/sloan_adjudicated"
    OUT_PATH = OUT_DIR / f"{cfg['league'].lower()}_candidate_profiles.json"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    meta = pd.read_csv(META_PATH)
    meta["position"] = meta["position"].fillna("Unknown")
    meta["height_inches"] = pd.to_numeric(meta["height_inches"], errors="coerce")

    # Scope: F-tall + all C + hyphenated
    f_tall_mask = (meta["position"] == "F") & (meta["height_inches"] >= cfg["height_F_floor"])
    c_mask = (meta["position"] == "C")
    hyph_mask = meta["position"].apply(is_hyphenated)

    scope = meta[f_tall_mask | c_mask | hyph_mask].copy()
    print(f"{cfg['league']} candidates: {len(scope)} "
          f"(F-tall={f_tall_mask.sum()}, C={c_mask.sum()}, hyph={hyph_mask.sum()})")

    games = pd.read_csv(GAMES_PATH)
    print(f"{cfg['league']} game logs: {len(games)} rows, columns: {list(games.columns)[:15]}")

    # Season column
    season_col = None
    for c in ["season", "year", "Season", "Year"]:
        if c in games.columns:
            season_col = c
            break
    if season_col is None:
        raise RuntimeError("No season column found in game logs")

    # Stat columns
    stat_cols = {}
    for std_name, candidates in {
        "PTS": ["PTS", "pts", "points"],
        "REB": ["TRB", "REB", "reb", "rebounds", "trb"],
        "AST": ["AST", "ast", "assists"],
        "BLK": ["BLK", "blk", "blocks"],
        "FG3M": ["FG3M", "3PM", "fg3m", "3p", "fg3"],
        "FG3A": ["FG3A", "fg3a", "3pa"],
    }.items():
        for c in candidates:
            if c in games.columns:
                stat_cols[std_name] = c
                break

    if "REB" not in stat_cols and "orb" in games.columns and "drb" in games.columns:
        games["_reb"] = games["orb"].fillna(0) + games["drb"].fillna(0)
        stat_cols["REB"] = "_reb"

    print(f"Stat columns: {stat_cols}")

    games_window = games[games[season_col].isin(cfg["seasons_in_window"])].copy()

    # Slug column
    slug_col = "player_slug" if "player_slug" in games.columns else None
    if slug_col is None:
        for c in ["slug", "player_id", "Player"]:
            if c in games.columns:
                slug_col = c
                break

    # Class year
    class_df = None
    if CLASS_PATH.exists():
        class_df = pd.read_csv(CLASS_PATH)
        print(f"Class year: {len(class_df)} rows, columns: {list(class_df.columns)}")

    profiles = []
    skipped_no_games = 0
    for _, row in scope.iterrows():
        slug = row["player_slug"]
        name = row["full_name"]
        pos = row["position"]
        height = row["height_inches"]

        if slug_col:
            pg = games_window[games_window[slug_col] == slug]
        else:
            pg = games_window.iloc[0:0]

        per_season = {}
        seasons_in_window_count = 0
        for s in cfg["seasons_in_window"]:
            sg = pg[pg[season_col] == s]
            gp = len(sg)
            per_season[str(s)] = {"GP": gp}
            if gp >= MIN_GP_PER_SEASON:
                seasons_in_window_count += 1

        # Career averages over qualifying seasons
        qualifying_games = pd.concat([
            pg[pg[season_col] == s] for s in cfg["seasons_in_window"]
            if (pg[season_col] == s).sum() >= MIN_GP_PER_SEASON
        ]) if seasons_in_window_count > 0 else pg.iloc[0:0]

        if len(qualifying_games) == 0:
            skipped_no_games += 1

        def avg(col_key):
            if col_key not in stat_cols or len(qualifying_games) == 0:
                return None
            v = qualifying_games[stat_cols[col_key]].mean()
            return None if pd.isna(v) else round(float(v), 3)

        avg_pts = avg("PTS")
        avg_reb = avg("REB")
        avg_ast = avg("AST")
        avg_blk = avg("BLK")
        avg_fg3m = avg("FG3M")
        avg_fg3a = avg("FG3A")

        # Class year per season
        cy_2024 = None
        cy_2025 = None
        if class_df is not None:
            cy_rows = class_df[class_df["player_slug"].astype(str) == str(slug)]
            for _, cyr in cy_rows.iterrows():
                if int(cyr["season"]) == 2024:
                    cy_2024 = cyr["class_year"]
                elif int(cyr["season"]) == 2025:
                    cy_2025 = cyr["class_year"]

        # Metadata bucket — Center if pos == 'C' OR primary token is 'C' in hyphenated
        if pos == "C" or (is_hyphenated(pos) and pos.split("-")[0] == "C"):
            metadata_bucket = "Center"
        else:
            metadata_bucket = "non-Center"

        profiles.append({
            "name": name,
            "player_slug": str(slug),
            "metadata_position": pos,
            "metadata_bucket_inclusive": metadata_bucket,
            "height_inches": None if pd.isna(height) else float(height),
            "class_year_2024": None if cy_2024 is None or pd.isna(cy_2024) else str(cy_2024),
            "class_year_2025": None if cy_2025 is None or pd.isna(cy_2025) else str(cy_2025),
            "career_seasons_in_window": seasons_in_window_count,
            "career_avg_PTS_per_game": avg_pts,
            "career_avg_REB_per_game": avg_reb,
            "career_avg_AST_per_game": avg_ast,
            "career_avg_BLK_per_game": avg_blk,
            "career_avg_FG3M_per_game": avg_fg3m,
            "career_avg_FG3A_per_game": avg_fg3a,
        })

    print(f"{cfg['league']}: {len(profiles)} profiles, skipped no-games={skipped_no_games}")

    out = {
        "league": cfg["league"],
        "pre_reg_sha": "28e3dc7",
        "pre_reg_file": cfg["pre_reg_file"],
        "seasons_in_window": cfg["seasons_in_window"],
        "min_gp_per_season": MIN_GP_PER_SEASON,
        "n_candidates": len(profiles),
        "candidates": profiles,
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
