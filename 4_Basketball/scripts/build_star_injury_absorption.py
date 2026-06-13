"""Build star-injury absorption mapping.

For each meaningful star-out event (player X missed games due to injury per PST,
games_missed >= 5), compute how much each teammate's MPG LIFTED in those
absent-games vs their season baseline (when X was playing).

Output:
    data/parquet/star_injury_absorption.parquet
        Per-event-aggregated absorption: star_id × teammate_id × season ->
        n_baseline_games, baseline_mpg, n_absent_games, absent_mpg, lift_mpg

    data/parquet/star_injury_absorption_team_season.parquet
        Aggregated to (team, season, star_id) -> ranked list of who absorbs.

Definition of "star" for this build: per team-season, top N=3 players by MPG
who played >= 200 minutes total. (Lower the bar for deep-bench-impact stars
later.)
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"
PST_PATH = PQ / "pro_sports_injuries_with_derived_severity.parquet"
BOX_PATH = PQ / "historical_box_scores.parquet"
META_PATH = PQ / "player_metadata_enriched.parquet"
OUT_EVENT = PQ / "star_injury_absorption.parquet"
OUT_TEAM = PQ / "star_injury_absorption_team_season.parquet"

MIN_GAMES_MISSED = 5      # only count events where star missed >= 5 team games
STAR_MIN_MPG = 28.0       # star threshold
STAR_MIN_TOTAL_MIN = 500  # must have played at least 500 min in season


def main():
    print("Loading PST + box scores...")
    pst = pd.read_parquet(PST_PATH)
    box = pd.read_parquet(BOX_PATH)
    meta = pd.read_parquet(META_PATH)

    box["minutes"] = pd.to_numeric(box["minutes"], errors="coerce")
    box = box.dropna(subset=["minutes"])
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    box["game_date"] = pd.to_datetime(box["game_date"])
    pst["event_date"] = pd.to_datetime(pst["event_date"])
    pst["games_missed"] = pd.to_numeric(pst["games_missed"], errors="coerce")

    # Filter PST to substantive star-out events
    rel = pst[(pst["side"] == "relinquished") &
              (pst["games_missed"] >= MIN_GAMES_MISSED) &
              (pst["nba_api_id"].notna())].copy()
    rel["nba_api_id"] = rel["nba_api_id"].astype(int)
    print(f"PST relinquished events with games_missed >= {MIN_GAMES_MISSED}: {len(rel)}")

    # Build star list per team-season from box scores
    print("\nBuilding star list per team-season...")
    season_stats = box.groupby(["nba_api_id", "team_abbr", "season"]).agg(
        gp=("game_date", "nunique"),
        total_min=("minutes", "sum"),
    ).reset_index()
    season_stats["mpg"] = season_stats["total_min"] / season_stats["gp"]

    stars = season_stats[(season_stats["mpg"] >= STAR_MIN_MPG) &
                         (season_stats["total_min"] >= STAR_MIN_TOTAL_MIN)].copy()
    print(f"  star-eligible (mpg>={STAR_MIN_MPG}, min>={STAR_MIN_TOTAL_MIN}): {len(stars)} player-team-seasons")

    star_ids_per_team_season = set(zip(stars["nba_api_id"], stars["team_abbr"], stars["season"]))

    # For each PST event, find what season + team it was in (via player's box appearance after event)
    print("\nResolving PST events to (team, season)...")
    box_min = box[["nba_api_id", "game_date", "team_abbr", "season"]].sort_values("game_date")

    # Most recent appearance BEFORE event_date — best inference of player's team at event time
    def find_team_season_at_event(pid, event_date):
        sub = box_min[box_min["nba_api_id"] == pid]
        if len(sub) == 0:
            return None, None
        before = sub[sub["game_date"] <= event_date]
        if len(before) > 0:
            r = before.iloc[-1]
            return r["team_abbr"], r["season"]
        # Fall back to next appearance after event
        after = sub[sub["game_date"] > event_date]
        if len(after) > 0:
            r = after.iloc[0]
            return r["team_abbr"], r["season"]
        return None, None

    rel["team_at_event"] = None
    rel["season_at_event"] = None
    teams = []
    seasons = []
    for _, r in rel.iterrows():
        t, s = find_team_season_at_event(r["nba_api_id"], r["event_date"])
        teams.append(t)
        seasons.append(s)
    rel["team_at_event"] = teams
    rel["season_at_event"] = seasons

    rel = rel.dropna(subset=["team_at_event", "season_at_event"])
    print(f"  events with resolved team-season: {len(rel)}")

    # Filter to star events only
    rel["is_star_event"] = [
        (pid, t, s) in star_ids_per_team_season
        for pid, t, s in zip(rel["nba_api_id"], rel["team_at_event"], rel["season_at_event"])
    ]
    star_events = rel[rel["is_star_event"]].copy()
    print(f"  star-out events: {len(star_events)}")

    # Build per-team-season game schedule (for identifying absent games)
    print("\nBuilding team game schedules...")
    team_games = box.groupby(["team_abbr", "season"])["game_date"].apply(
        lambda x: sorted(x.unique())).to_dict()

    # Build per-player per-team-season game appearances (set of game_dates)
    print("Building player appearance sets...")
    player_appearance = box.groupby(["nba_api_id", "team_abbr", "season"])["game_date"].apply(
        lambda x: set(x.tolist())).to_dict()

    # Build mapping (team, season, game_date) -> all box rows for that team
    print("Indexing team-game box scores...")
    team_game_box = {(t, s): grp for (t, s), grp in box.groupby(["team_abbr", "season"])}

    # Process each star event
    print("\nComputing absorption per event...")
    absorption_rows = []
    for i, (idx, ev) in enumerate(star_events.iterrows()):
        if i > 0 and i % 50 == 0:
            print(f"  {i}/{len(star_events)}...")
        pid = int(ev["nba_api_id"])
        team = ev["team_at_event"]
        season = ev["season_at_event"]
        event_date = ev["event_date"]
        games_missed = int(ev["games_missed"])

        # Identify absent games: team games in (event_date, event_date + games_missed games]
        sched = team_games.get((team, season), [])
        if not sched:
            continue
        # Games strictly after event_date
        future_games = [g for g in sched if g > event_date]
        if not future_games:
            continue
        absent_games = future_games[:games_missed]
        if not absent_games:
            continue

        # Identify baseline games: team games in this season where this star DID play
        star_appear = player_appearance.get((pid, team, season), set())
        team_box = team_game_box.get((team, season))
        if team_box is None or len(star_appear) == 0:
            continue
        baseline_games = sorted(star_appear)
        if len(baseline_games) < 5:
            continue  # need stable baseline

        # Collect absorption rows for each TEAMMATE
        # Filter team_box to rows where this player is NOT the row (we want teammates)
        teammates = team_box[team_box["nba_api_id"] != pid]

        absent_set = set(absent_games)
        baseline_set = set(baseline_games)

        # Per teammate aggregate
        for tid, tgrp in teammates.groupby("nba_api_id"):
            base = tgrp[tgrp["game_date"].isin(baseline_set)]
            absent = tgrp[tgrp["game_date"].isin(absent_set)]
            if len(base) < 5 or len(absent) < 3:
                continue
            absorption_rows.append({
                "star_id": pid,
                "team_abbr": team,
                "season": season,
                "event_date": event_date,
                "games_missed": games_missed,
                "teammate_id": int(tid),
                "n_baseline_games": len(base),
                "baseline_mpg": float(base["minutes"].mean()),
                "n_absent_games": len(absent),
                "absent_mpg": float(absent["minutes"].mean()),
            })

    print(f"\nAbsorption event-rows: {len(absorption_rows)}")
    if not absorption_rows:
        print("No absorption rows — abort.")
        return
    abs_df = pd.DataFrame(absorption_rows)
    abs_df["lift_mpg"] = abs_df["absent_mpg"] - abs_df["baseline_mpg"]

    # Attach names
    name_map = dict(zip(meta["nba_api_id"].astype(int), meta["name"]))
    abs_df["star_name"] = abs_df["star_id"].map(name_map)
    abs_df["teammate_name"] = abs_df["teammate_id"].map(name_map)

    abs_df = abs_df[["star_id", "star_name", "team_abbr", "season", "event_date",
                     "games_missed", "teammate_id", "teammate_name",
                     "n_baseline_games", "baseline_mpg",
                     "n_absent_games", "absent_mpg", "lift_mpg"]]
    abs_df.to_parquet(OUT_EVENT, index=False)
    print(f"\nSaved per-event absorption -> {OUT_EVENT}")
    print(f"  rows: {len(abs_df)}")

    # Aggregate to team-season-star: weighted by n_absent_games
    print("\nAggregating to (team, season, star_id) team-level...")
    grp = abs_df.groupby(["team_abbr", "season", "star_id", "star_name",
                          "teammate_id", "teammate_name"]).apply(
        lambda d: pd.Series({
            "total_absent_games": d["n_absent_games"].sum(),
            "total_baseline_games": d["n_baseline_games"].sum(),
            "weighted_baseline_mpg": np.average(d["baseline_mpg"], weights=d["n_baseline_games"]),
            "weighted_absent_mpg": np.average(d["absent_mpg"], weights=d["n_absent_games"]),
            "n_events": len(d),
        }), include_groups=False).reset_index()
    grp["weighted_lift_mpg"] = grp["weighted_absent_mpg"] - grp["weighted_baseline_mpg"]
    grp.to_parquet(OUT_TEAM, index=False)
    print(f"Saved team-season absorption -> {OUT_TEAM}")
    print(f"  rows: {len(grp)}")

    # Headline: top absorbers across all events
    print("\n=== Top 15 absorbers (by lift_mpg, min 30 absent games) ===")
    candidates = grp[grp["total_absent_games"] >= 30].copy()
    top = candidates.sort_values("weighted_lift_mpg", ascending=False).head(15)
    for _, r in top.iterrows():
        print(f"  {r['team_abbr']} {r['season']} {r['star_name']!s:<22} OUT -> "
              f"{r['teammate_name']!s:<22} +{r['weighted_lift_mpg']:.1f} mpg "
              f"({r['weighted_baseline_mpg']:.1f} -> {r['weighted_absent_mpg']:.1f}) "
              f"n_absent={r['total_absent_games']:.0f}")


if __name__ == "__main__":
    main()
