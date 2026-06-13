"""Build teammate-context features for prospects.

For each player-team-season, compute features from their TEAMMATES' production:
  - teammate_pts_per40_mean: average of all teammates' per-40 pts (proxy for "is this player carrying or supported")
  - teammate_pts_per40_top: best teammate's per-40 (the "is there another star on this roster")
  - teammate_n_drafted: count of teammates also drafted into NBA (historical only, leakage-free since drafted-2026 isn't yet drafted)
  - team_pace_proxy: team mp per game (proxy for tempo)
  - prospect_share_pts: prospect's pts / team total pts
  - prospect_share_ast: prospect's ast / team total ast
  - team_offensive_strength: weighted avg of all team players' pts/40

Covers seasons 2023-2026 (4 NCAA seasons logged). For historical training, this
applies to 2023+2024 NBA drafts (~100 prospects). For 2026 pool, all 67 NCAA.

Outputs:
    data/parquet/prospect_teammate_context.parquet
    augmented training set adds teammate features
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
OUT = PQ / "prospect_teammate_context.parquet"


def per40(series_total, mp_total):
    return (series_total / mp_total.replace(0, np.nan)) * 40.0


def main():
    gl = pd.read_csv("C:/NCAA D1 Mens/data/processed/player_game_logs.csv",
                                usecols=["team", "player", "player_slug", "season",
                                                "game_id", "pts", "trb", "ast", "stl", "blk",
                                                "tov", "mp_minutes", "season_type"])
    gl = gl[gl["season_type"] == "Regular Season"].copy()
    print(f"  game logs (RS only): {len(gl):,}")

    team_season = (gl.dropna(subset=["player_slug", "team", "season"])
                                  .groupby(["season", "team", "player", "player_slug"])
                                  .agg(games=("game_id", "nunique"),
                                              pts=("pts", "sum"), reb=("trb", "sum"),
                                              ast=("ast", "sum"), stl=("stl", "sum"),
                                              blk=("blk", "sum"), tov=("tov", "sum"),
                                              mp=("mp_minutes", "sum"))
                                  .reset_index())
    team_season["pts_per40"] = per40(team_season["pts"], team_season["mp"])
    team_season["reb_per40"] = per40(team_season["reb"], team_season["mp"])
    team_season["ast_per40"] = per40(team_season["ast"], team_season["mp"])
    print(f"  player-team-season rows: {len(team_season):,}")

    rookies = pd.read_parquet(PQ / "rookies_outcome_training_v3.parquet")
    pool = pd.read_parquet(PQ / "draft_2026_candidate_pool.parquet")

    historical_24 = rookies[rookies["draft_year"].isin([2023, 2024])].copy()
    print(f"  historical 2023-24 prospects: {len(historical_24)}")
    print(f"  2026 pool: {len(pool)}")

    name_pool = team_season["player"].dropna().unique().tolist()

    def fuzzy_find(name, season):
        if pd.isna(name): return None, None
        best = process.extractOne(name, name_pool, scorer=fuzz.token_sort_ratio, score_cutoff=85)
        if not best: return None, None
        matched_name = best[0]
        team_rows = team_season[(team_season["player"] == matched_name) & (team_season["season"] == season)]
        if not len(team_rows): return matched_name, None
        team_rows = team_rows.sort_values("mp", ascending=False)
        return matched_name, team_rows.iloc[0]["team"]

    rows = []
    print("\n=== building teammate context ===")
    for _, r in pd.concat([
        historical_24[["player_name_raw", "draft_year"]].rename(columns={"player_name_raw": "name"}).assign(source="historical"),
        pool[["player_name"]].rename(columns={"player_name": "name"}).assign(draft_year=2026, source="2026")
    ]).iterrows():
        name = r["name"]
        season = int(r["draft_year"])
        matched, team = fuzzy_find(name, season)
        if not matched or not team:
            rows.append({"player_name": name, "draft_year": season, "matched": False,
                                  "team": None, "n_teammates": 0})
            continue

        team_ts = team_season[(team_season["season"] == season) & (team_season["team"] == team)].copy()
        self_mask = team_ts["player"] == matched
        teammates = team_ts[~self_mask & (team_ts["mp"] >= 100)]
        if not len(teammates):
            rows.append({"player_name": name, "draft_year": season, "matched": True,
                                  "team": team, "n_teammates": 0})
            continue

        prospect = team_ts[self_mask].iloc[0] if self_mask.any() else None
        team_total_pts = float(team_ts["pts"].sum())
        team_total_ast = float(team_ts["ast"].sum())

        tm_pts40 = teammates["pts_per40"].dropna()
        tm_reb40 = teammates["reb_per40"].dropna()
        tm_ast40 = teammates["ast_per40"].dropna()

        rec = {
            "player_name": name, "draft_year": season, "matched": True,
            "team": team, "n_teammates": len(teammates),
            "teammate_pts_per40_mean": float(tm_pts40.mean()) if len(tm_pts40) else None,
            "teammate_pts_per40_top": float(tm_pts40.max()) if len(tm_pts40) else None,
            "teammate_reb_per40_top": float(tm_reb40.max()) if len(tm_reb40) else None,
            "teammate_ast_per40_top": float(tm_ast40.max()) if len(tm_ast40) else None,
            "teammate_total_pts_share_top": float(teammates["pts"].max() / team_total_pts) if team_total_pts > 0 else None,
            "team_pts_per_game": float(team_total_pts / team_ts["games"].max()) if team_ts["games"].max() > 0 else None,
        }
        if prospect is not None and team_total_pts > 0:
            rec["prospect_pts_share"] = float(prospect["pts"] / team_total_pts)
            rec["prospect_ast_share"] = float(prospect["ast"] / team_total_ast) if team_total_ast > 0 else None
        rows.append(rec)

    ctx = pd.DataFrame(rows)
    ctx.to_parquet(OUT, index=False)
    print(f"\nwrote: {OUT}")
    print(f"  rows: {len(ctx)}")
    print(f"  matched: {ctx['matched'].sum()}/{len(ctx)}")

    print("\n=== sample 2026 prospects with teammate context ===")
    s26 = ctx[(ctx["draft_year"] == 2026) & ctx["matched"]]
    cols = ["player_name", "team", "teammate_pts_per40_top", "teammate_pts_per40_mean",
              "prospect_pts_share", "team_pts_per_game"]
    cols = [c for c in cols if c in s26.columns]
    print(s26[cols].sort_values("prospect_pts_share", ascending=False).head(15).round(2).to_string(index=False))

    print("\n=== 2026 prospects with MOST stacked rosters (highest teammate_pts_per40_top) ===")
    print(s26.sort_values("teammate_pts_per40_top", ascending=False).head(10)[cols].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
