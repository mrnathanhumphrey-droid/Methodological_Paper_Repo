"""Extract inactive player lists from Sportradar game summaries.

For each SR game summary JSON, identify:
  - Inactive players (played=False) per team
  - Starters (starter=True) per team
  - Total team minutes (sanity check ≈ 240)

Output: D:/NBA Projections/data/parquet/sr_inactive_per_game.parquet
        Per row: (game_id_sr, game_date, team_abbr, nba_api_id_or_sr_id,
                  player_name, is_inactive, is_starter)

Joining to historical_box_scores: needs sr_id ↔ nba_api_id mapping. SR game IDs
don't match nba_api game_ids, but team_abbr + game_date does. We use that
composite key for downstream backtest joins.
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

SR_DIR = Path("D:/sports_lines/data/sportradar/game_summaries")
OUT_PATH = Path("D:/NBA Projections/data/parquet/sr_inactive_per_game.parquet")
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# SR uses "alias" like "OKC", "SAS" — usually matches NBA abbr. Special cases:
SR_TO_NBA_ABBR = {
    # Most aliases match directly; this is the override table
    "NOP": "NOP", "LAC": "LAC", "GSW": "GSW",
}


def extract_one(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  {path.name}: parse err {e}")
        return []
    rows = []
    game_id_sr = data.get("id")
    scheduled = data.get("scheduled")
    try:
        game_date = pd.to_datetime(scheduled).tz_convert(None).date() if scheduled else None
    except Exception:
        try:
            game_date = pd.to_datetime(scheduled).date()
        except Exception:
            game_date = None

    for side in ("home", "away"):
        team = data.get(side, {})
        team_abbr = team.get("alias", "")
        nba_abbr = SR_TO_NBA_ABBR.get(team_abbr, team_abbr)
        for p in team.get("players", []) or []:
            rows.append({
                "game_id_sr": game_id_sr,
                "game_date": game_date,
                "team_abbr": nba_abbr,
                "sr_player_id": p.get("id"),
                "player_name": p.get("full_name") or p.get("first_name", "") + " " + p.get("last_name", ""),
                "primary_position": p.get("primary_position"),
                "is_inactive": not p.get("played", False),
                "is_starter": bool(p.get("starter")),
                "is_active": bool(p.get("active")),
            })
    return rows


def main():
    files = sorted(SR_DIR.glob("*.json"))
    print(f"Parsing {len(files)} SR game summaries...")

    all_rows = []
    for i, f in enumerate(files, 1):
        rows = extract_one(f)
        all_rows.extend(rows)
        if i % 200 == 0:
            print(f"  [{i}/{len(files)}] {len(all_rows):,} rows so far")

    df = pd.DataFrame(all_rows)
    if df.empty:
        print("No rows extracted")
        return

    df["game_date"] = pd.to_datetime(df["game_date"])
    print(f"\nTotal: {len(df):,} player-game rows")
    print(f"  unique games: {df['game_id_sr'].nunique()}")
    print(f"  unique teams: {df['team_abbr'].nunique()}")
    print(f"  date range: {df['game_date'].min().date()} → {df['game_date'].max().date()}")
    print(f"\nInactive rate per game: {df.groupby('game_id_sr')['is_inactive'].sum().mean():.2f} avg")
    print(f"Starter rate per team-game: {df.groupby(['game_id_sr', 'team_abbr'])['is_starter'].sum().mean():.2f} avg")

    df.to_parquet(OUT_PATH, index=False)
    print(f"\n→ {OUT_PATH}")


if __name__ == "__main__":
    main()
