"""2026 draft candidate pool builder (v0 — uses substrate-on-disk).

For each of the 71 confirmed 2026 NBA Combine invitees:
  1. Fuzzy-match to existing NCAA player_game_logs (2022-25 seasons) → most-recent NCAA season totals
  2. Fuzzy-match to existing international_player_seasons → most-recent intl season totals
  3. Combine measurables (currently invitee-list only, no measurements live yet)
  4. Combine position

Output:
    data/parquet/draft_2026_candidate_pool.parquet (one row per invitee)
    NCAA-stats: aggregated per-player from game logs for their MOST RECENT season
    intl-stats: pulled if matched
    has_ncaa_24_25 / has_intl flags for v0 confidence
"""
from __future__ import annotations
import sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd
from rapidfuzz import process, fuzz

PQ = Path("D:/NBA Projections/data/parquet")
RAW = Path("D:/NBA Projections/data/raw")
OUT = PQ / "draft_2026_candidate_pool.parquet"


def aggregate_ncaa_season(gl: pd.DataFrame, slug: str, season: int) -> dict:
    sub = gl[(gl["player_slug"] == slug) & (gl["season"] == season)]
    if not len(sub):
        return {}
    sub = sub.copy()
    for c in ["fg", "fga", "fg3", "fg3a", "ft", "fta", "pts", "trb", "ast", "stl", "blk", "tov", "mp_minutes"]:
        sub[c] = pd.to_numeric(sub[c], errors="coerce")
    gp = len(sub)
    mp_total = sub["mp_minutes"].sum()
    if mp_total <= 0:
        return {}
    fact_per40 = 40.0 / (mp_total / gp)
    out = {
        "ncaa_last_season": season,
        "ncaa_gp": gp,
        "ncaa_mpg": float(mp_total / gp),
        "ncaa_pts_per40": float(sub["pts"].sum() / gp) * fact_per40,
        "ncaa_reb_per40": float(sub["trb"].sum() / gp) * fact_per40,
        "ncaa_ast_per40": float(sub["ast"].sum() / gp) * fact_per40,
        "ncaa_stl_per40": float(sub["stl"].sum() / gp) * fact_per40,
        "ncaa_blk_per40": float(sub["blk"].sum() / gp) * fact_per40,
        "ncaa_tov_per40": float(sub["tov"].sum() / gp) * fact_per40,
        "ncaa_fg3m_per40": float(sub["fg3"].sum() / gp) * fact_per40,
        "ncaa_fg_pct": float(sub["fg"].sum() / sub["fga"].sum()) if sub["fga"].sum() > 0 else np.nan,
        "ncaa_fg3_pct": float(sub["fg3"].sum() / sub["fg3a"].sum()) if sub["fg3a"].sum() > 0 else np.nan,
        "ncaa_ft_pct": float(sub["ft"].sum() / sub["fta"].sum()) if sub["fta"].sum() > 0 else np.nan,
    }
    return out


def main():
    print("=== loading sources ===")
    combine = pd.read_parquet(RAW / "draft/combine_all_time.parquet")
    invitees = combine[combine["SEASON"] == "2026"][["PLAYER_NAME", "POSITION", "PLAYER_ID"]].dropna(subset=["PLAYER_NAME"]).reset_index(drop=True)
    print(f"  2026 invitees: {len(invitees)}")

    gl = pd.read_csv("C:/NCAA D1 Mens/data/processed/player_game_logs.csv",
                                usecols=["player", "player_slug", "season", "season_type",
                                                "fg", "fga", "fg3", "fg3a", "ft", "fta", "pts", "trb",
                                                "ast", "stl", "blk", "tov", "mp_minutes"])
    gl = gl[gl["season_type"] == "Regular Season"]
    name_slug = gl[["player", "player_slug"]].drop_duplicates("player_slug")
    name_list = name_slug["player"].dropna().tolist()
    slug_lookup = dict(zip(name_slug["player"], name_slug["player_slug"]))
    print(f"  NCAA unique players in panel: {len(name_slug):,}")

    intl = pd.read_parquet(PQ / "international_player_seasons.parquet")
    intl_24 = intl[intl["season"].astype(str).str.contains("2024-25", na=False)].copy()
    intl_names = intl_24["player_name_raw"].dropna().tolist()
    print(f"  intl 2024-25 players: {len(intl_names)}")

    sup_path = PQ / "draft_2026_intl_supplement.parquet"
    sup = pd.read_parquet(sup_path) if sup_path.exists() else pd.DataFrame()
    sup_names = sup["player_name"].dropna().tolist() if len(sup) else []
    print(f"  intl supplement rows: {len(sup)}")

    NAME_ALIASES = {
        "Anicet Dybantsa": "AJ Dybantsa",
        "Labaron Philon": "Labaron Philon Jr.",
        "Christopher Cenac Jr.": "Chris Cenac Jr.",
        "Nathaniel Ament": "Nate Ament",
    }
    invitees["PLAYER_NAME"] = invitees["PLAYER_NAME"].replace(NAME_ALIASES)
    invitees = invitees.drop_duplicates("PLAYER_NAME", keep="first").reset_index(drop=True)

    extras = [
        {"PLAYER_NAME": "Cameron Boozer", "POSITION": "PF", "PLAYER_ID": None},
    ]
    extra_df = pd.DataFrame(extras)
    have_names = set(invitees["PLAYER_NAME"].dropna().str.lower())
    extra_df = extra_df[~extra_df["PLAYER_NAME"].str.lower().isin(have_names)]
    if len(extra_df):
        print(f"  adding {len(extra_df)} known-prospects-not-on-combine-list: {extra_df['PLAYER_NAME'].tolist()}")
        invitees = pd.concat([invitees, extra_df], ignore_index=True)

    rows = []
    for _, inv in invitees.iterrows():
        name = inv["PLAYER_NAME"]
        row = {"player_name": name, "position": inv["POSITION"], "combine_player_id": inv["PLAYER_ID"]}

        best_ncaa = process.extractOne(name, name_list, scorer=fuzz.token_sort_ratio, score_cutoff=85)
        if best_ncaa:
            slug = slug_lookup[best_ncaa[0]]
            player_seasons_arr = gl[gl["player_slug"] == slug]["season"].unique()
            player_seasons = sorted(player_seasons_arr.tolist())
            if len(player_seasons):
                latest = int(max(player_seasons))
                stats = aggregate_ncaa_season(gl, slug, latest)
                if latest < 2026 and 2026 in player_seasons_arr:
                    latest = 2026
                    stats = aggregate_ncaa_season(gl, slug, latest)
                row["ncaa_match_name"] = best_ncaa[0]
                row["ncaa_match_score"] = best_ncaa[1]
                row["ncaa_match_slug"] = slug
                row["ncaa_n_seasons"] = len(player_seasons)
                row.update(stats)
                row["has_ncaa"] = True
            else:
                row["has_ncaa"] = False
        else:
            row["has_ncaa"] = False

        if not row.get("has_ncaa") and len(sup) and name in sup_names:
            srow = sup[sup["player_name"] == name].iloc[0]
            if pd.notna(srow.get("pts_per40")):
                row["intl_match_name"] = name
                row["intl_match_score"] = 100.0
                row["intl_league"] = srow.get("league")
                row["intl_team"] = srow.get("team")
                row["intl_gp"] = srow.get("gp")
                row["intl_mpg"] = srow.get("mpg")
                for s in ["pts", "reb", "ast", "stl", "blk", "tov", "fg3m"]:
                    col = f"{s}_per40"
                    if col in srow.index:
                        row[f"intl_{col}"] = srow[col]
                for p in ["fg_pct", "fg3_pct", "ft_pct"]:
                    if p in srow.index:
                        row[f"intl_{p}"] = srow[p]
                row["has_intl"] = True

        if row.get("has_intl"):
            pass
        elif not row.get("has_ncaa"):
            best_intl = process.extractOne(name, intl_names, scorer=fuzz.token_sort_ratio, score_cutoff=88)
            if best_intl:
                irow = intl_24[intl_24["player_name_raw"] == best_intl[0]].iloc[0]
                row["intl_match_name"] = best_intl[0]
                row["intl_match_score"] = best_intl[1]
                row["intl_league"] = irow.get("league")
                row["intl_team"] = irow.get("team")
                row["intl_gp"] = irow.get("gp")
                row["intl_mpg"] = irow.get("mpg")
                for s in ["pts", "reb", "ast", "stl", "blk", "tov", "fg3m"]:
                    col = f"{s}_per40"
                    if col in irow.index:
                        row[f"intl_{col}"] = irow[col]
                for p in ["fg_pct", "fg3_pct", "ft_pct"]:
                    if p in irow.index:
                        row[f"intl_{p}"] = irow[p]
                row["has_intl"] = True
            else:
                row["has_intl"] = False
        else:
            row["has_intl"] = False

        rows.append(row)

    pool = pd.DataFrame(rows)
    pool["has_pre_nba"] = pool["has_ncaa"] | pool["has_intl"]
    print(f"\n=== coverage ===")
    print(f"  has_ncaa: {pool['has_ncaa'].sum()}")
    print(f"  has_intl: {pool['has_intl'].sum()}")
    print(f"  has_pre_nba (either): {pool['has_pre_nba'].sum()}")
    print(f"  missing (combine-list only): {(~pool['has_pre_nba']).sum()}")

    pool.to_parquet(OUT, index=False)
    pool.to_csv(OUT.with_suffix(".csv"), index=False)
    print(f"\nwrote: {OUT}")
    print(f"  rows: {len(pool)}, cols: {len(pool.columns)}")

    print("\n=== sample matched (top 10 NCAA) ===")
    n = pool[pool["has_ncaa"]].head(10)
    print(n[["player_name", "position", "ncaa_match_name", "ncaa_last_season",
                  "ncaa_gp", "ncaa_pts_per40", "ncaa_reb_per40", "ncaa_ast_per40",
                  "ncaa_blk_per40"]].round(2).to_string(index=False))

    print("\n=== sample unmatched (likely freshmen / intl-needing-refresh) ===")
    u = pool[~pool["has_pre_nba"]]
    print(u[["player_name", "position"]].to_string(index=False))


if __name__ == "__main__":
    main()
