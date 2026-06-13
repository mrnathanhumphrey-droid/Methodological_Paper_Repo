"""Rebuild playoffs/extra_rounds/_manifest.parquet from the fetched
traditional_t0+t1 (the manifest accumulator in fetch_playoff_extra_rounds.py
had a closure bug that kept overwriting). Game metadata derived from the
traditional table; round/matchup_idx/game_in_series via the same heuristic
as the fetcher.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import pandas as pd

REPO = Path(".")
EXTRA = REPO / "data" / "parquet" / "playoffs" / "extra_rounds"

t0 = pd.read_parquet(EXTRA / "traditional_t0.parquet")
t1 = pd.read_parquet(EXTRA / "traditional_t1.parquet")

# Per game: pull (gameId, teamId, season) — one row per game per team
g = pd.concat([t0, t1], ignore_index=True)
team_per_game = (g.groupby("gameId")
                  .agg(season=("season", "first"),
                       teams=("teamId", lambda x: sorted(set(x))))
                  .reset_index())

# Need game_date per game — from BoxScoreSummaryV2's GameDate, which we didn't
# fetch separately. Derive from existing nba_api Schedule (data/parquet/schedule.parquet)
sched = pd.read_parquet(REPO / "data" / "parquet" / "schedule.parquet")
sched_cols = {c.lower(): c for c in sched.columns}
gid_col = sched_cols.get("game_id") or sched_cols.get("gameid")
date_col = sched_cols.get("game_date") or sched_cols.get("gamedate")
if not gid_col or not date_col:
    raise RuntimeError(f"schedule.parquet has no game_id/game_date in cols: {sched.columns.tolist()}")
sched_lookup = dict(zip(sched[gid_col].astype(str), sched[date_col]))

rows = []
for _, r in team_per_game.iterrows():
    teams = r["teams"]
    if len(teams) != 2:
        continue
    rows.append({
        "game_id": str(r["gameId"]),
        "season": r["season"],
        "season_end_year": int(r["season"].split("-")[0]) + 1,
        "game_date": pd.to_datetime(sched_lookup.get(str(r["gameId"]))).date()
                     if str(r["gameId"]) in sched_lookup else None,
        "round": 0,
        "matchup_idx": 0,
        "game_in_series": 0,
        "home_team_abbr": "",
        "away_team_abbr": "",
        "home_team_id": int(teams[0]),
        "away_team_id": int(teams[1]),
    })

m = pd.DataFrame(rows)

# Heuristic round assignment per season: sort series by first game_date, first
# 8 series = R1, next 4 = R2, next 2 = R3, last 1 = R4. Since we only have R2-4
# games here, the resulting "round" labels start at 2.
for season in m["season"].unique():
    sub = m[m["season"] == season].copy()
    sub["pair"] = sub.apply(
        lambda r: tuple(sorted([r["home_team_id"], r["away_team_id"]])), axis=1,
    )
    sub = sub.sort_values(["game_date", "game_id"])
    sub["game_in_series"] = sub.groupby("pair").cumcount() + 1

    pairs_chrono = sub.drop_duplicates("pair").sort_values("game_date")
    pair_to_round = {}
    for i, p in enumerate(pairs_chrono["pair"].tolist()):
        # In extra_rounds we only have R2/3/4: 4 pairs (R2) + 2 pairs (R3) + 1 pair (R4)
        if i < 4:
            pair_to_round[p] = 2
        elif i < 6:
            pair_to_round[p] = 3
        else:
            pair_to_round[p] = 4
    sub["round"] = sub["pair"].map(pair_to_round)

    for r in [2, 3, 4]:
        r_pairs = (sub[sub["round"] == r].drop_duplicates("pair")
                                          .sort_values("game_date")["pair"].tolist())
        for i, p in enumerate(r_pairs):
            sub.loc[sub["pair"] == p, "matchup_idx"] = i + 1

    m.loc[m["season"] == season, "round"] = sub["round"].values
    m.loc[m["season"] == season, "matchup_idx"] = sub["matchup_idx"].values
    m.loc[m["season"] == season, "game_in_series"] = sub["game_in_series"].values

m = m.sort_values(["season", "round", "matchup_idx", "game_in_series"]).reset_index(drop=True)
m.to_parquet(EXTRA / "_manifest.parquet", index=False)
print(f"Wrote {EXTRA / '_manifest.parquet'}  ({len(m)} rows)")
print()
print("Per (season, round):")
print(m.groupby(["season", "round"]).size())
