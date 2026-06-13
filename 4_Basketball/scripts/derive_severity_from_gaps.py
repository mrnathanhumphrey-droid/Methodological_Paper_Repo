"""Path 1 severity derivation — gap-based inference from PST + box scores.

For each 'relinquished' PST event (player went out), count the gap until they
played their NEXT game (using their team's schedule). Map gap to severity.

  0-1 team games missed: single_game (rest day, GTD, etc.)
  2-5:                   short_term  (DTD that lasted ~a week)
  6-15:                  medium_term (sprain/strain ~3-4 weeks)
  16-40:                 long_term   (significant injury)
  40+ or season end:     out_for_season

Output:
  data/parquet/pro_sports_injuries_with_derived_severity.parquet
    — same as input plus columns: derived_severity, games_missed, gap_method
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(".")
PST_PATH = REPO / "data" / "parquet" / "pro_sports_injuries.parquet"
BOX_PATH = REPO / "data" / "parquet" / "historical_box_scores.parquet"
META_PATH = REPO / "data" / "parquet" / "player_metadata_enriched.parquet"
OUT_PATH = REPO / "data" / "parquet" / "pro_sports_injuries_with_derived_severity.parquet"


def games_missed_to_severity(g: int) -> str:
    if g <= 1: return "single_game"
    if g <= 5: return "short_term"
    if g <= 15: return "medium_term"
    if g <= 40: return "long_term"
    return "out_for_season"


def main():
    print("Loading PST + box scores + metadata...")
    pst = pd.read_parquet(PST_PATH)
    box = pd.read_parquet(BOX_PATH)
    meta = pd.read_parquet(META_PATH)

    box["minutes"] = pd.to_numeric(box["minutes"], errors="coerce")
    box = box.dropna(subset=["minutes"])
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    box["game_date"] = pd.to_datetime(box["game_date"])

    pst["event_date"] = pd.to_datetime(pst["event_date"])

    # Resolve player_name_raw -> nba_api_id
    name_to_id = {str(n).strip().lower(): int(i) for n, i in
                  zip(meta["name"], meta["nba_api_id"]) if pd.notna(n) and pd.notna(i)}
    pst["nba_api_id"] = pst["player_name_raw"].astype(str).str.strip().str.lower().map(name_to_id).astype("Int64")

    # Build team schedule: per (team_abbr, season), sorted list of game_dates
    team_schedule = box.groupby(["team_abbr", "season"])["game_date"].apply(
        lambda x: np.array(sorted(x.unique()))).to_dict()

    # Build player game appearances: per nba_api_id, sorted array of (game_date, team)
    player_games = box.sort_values("game_date").groupby("nba_api_id").apply(
        lambda x: list(zip(x["game_date"].tolist(), x["team_abbr"].tolist(), x["season"].tolist())),
        include_groups=False,
    ).to_dict()

    # Filter to relinquished events (player went OUT)
    rel = pst[pst["side"] == "relinquished"].copy()
    print(f"Relinquished events: {len(rel)}")
    rel = rel.dropna(subset=["nba_api_id", "event_date"])
    print(f"  with resolved nba_api_id + valid date: {len(rel)}")

    # Function: given (nba_api_id, event_date), count team-games player missed before next appearance
    def derive_gap(nba_id, event_date, team_abbr):
        nba_id = int(nba_id)
        appearances = player_games.get(nba_id, [])
        if not appearances:
            return None, "no_appearances"
        # Find next appearance after event_date
        next_play = None
        for d, t, _ in appearances:
            if d >= event_date:
                next_play = d
                break
        if next_play is None:
            # Player never played again this season -> out_for_season tier
            return 999, "no_return_season"
        # Find the season + team to count games missed
        # Use team_abbr from the event if present, else default to team of next appearance
        if team_abbr is None or pd.isna(team_abbr):
            team_abbr = next((t for d, t, _ in appearances if d >= event_date), None)
        if team_abbr is None:
            return None, "no_team"
        # Find which season this event is in (use the next play's season)
        season = next((s for d, t, s in appearances if d == next_play), None)
        sched = team_schedule.get((team_abbr, season))
        if sched is None or len(sched) == 0:
            return None, "no_schedule"
        # Count games in (event_date, next_play) exclusive of both
        gap = int(((sched > event_date) & (sched < next_play)).sum())
        return gap, "team_schedule_gap"

    print("\nDeriving gap-based severity for each relinquished event...")
    gaps = []
    methods = []
    for i, r in rel.iterrows():
        gap, method = derive_gap(r["nba_api_id"], r["event_date"], r.get("team_abbr"))
        gaps.append(gap)
        methods.append(method)
    rel["games_missed"] = gaps
    rel["gap_method"] = methods
    rel["derived_severity"] = rel["games_missed"].apply(
        lambda g: games_missed_to_severity(g) if g is not None and not pd.isna(g) else None)

    print()
    print(f"Method distribution:")
    print(rel["gap_method"].value_counts().to_string())
    print()
    print(f"Derived severity distribution:")
    print(rel["derived_severity"].value_counts(dropna=False).to_string())
    print()
    print(f"Coverage: {rel['derived_severity'].notna().sum()} / {len(rel)} = "
          f"{100*rel['derived_severity'].notna().mean():.1f}%")

    # Now backfill the full PST table — for non-relinquished events leave derived_severity null
    pst_out = pst.copy()
    pst_out["games_missed"] = None
    pst_out["gap_method"] = None
    pst_out["derived_severity"] = None
    pst_out.loc[rel.index, "games_missed"] = rel["games_missed"].values
    pst_out.loc[rel.index, "gap_method"] = rel["gap_method"].values
    pst_out.loc[rel.index, "derived_severity"] = rel["derived_severity"].values

    pst_out.to_parquet(OUT_PATH, index=False)
    print(f"\nSaved enriched parquet -> {OUT_PATH}")

    # Validation spot-checks
    print("\n=== Spot-checks ===")
    pst_out["pname_l"] = pst_out["player_name_raw"].astype(str).str.lower()

    # Klay Thompson June 2019 ACL → out_for_season
    klay = pst_out[(pst_out["pname_l"].str.contains("klay thompson", na=False)) &
                   (pst_out["event_date"].dt.year == 2019) &
                   (pst_out["event_date"].dt.month >= 6)]
    if len(klay) > 0:
        print(f"  Klay 2019 ACL events: {len(klay)} found")
        for _, r in klay.iterrows():
            print(f"    {r['event_date'].date()} {r['relinquished_status']} games_missed={r['games_missed']} "
                  f"derived={r['derived_severity']}  notes={r['notes_raw']}")

    # Embiid Jan 2024 meniscus
    emb = pst_out[(pst_out["pname_l"].str.contains("embiid", na=False)) &
                  (pst_out["event_date"].dt.year == 2024) &
                  (pst_out["event_date"].dt.month <= 3) &
                  (pst_out["side"] == "relinquished")]
    if len(emb) > 0:
        print(f"\n  Embiid 2024 Jan-Mar relinquished events: {len(emb)}")
        for _, r in emb.head(5).iterrows():
            print(f"    {r['event_date'].date()} games_missed={r['games_missed']} "
                  f"derived={r['derived_severity']}  notes={r['notes_raw']}")

    # Compare derived_severity to existing severity (where both present)
    rel_with_existing = rel.dropna(subset=["derived_severity"])
    if "severity" in rel_with_existing.columns:
        both = rel_with_existing[rel_with_existing["severity"].notna()]
        if len(both) > 0:
            print(f"\n  Agreement with regex-extracted severity (n={len(both)}):")
            print(both.groupby(["severity", "derived_severity"]).size().to_string())


if __name__ == "__main__":
    main()
