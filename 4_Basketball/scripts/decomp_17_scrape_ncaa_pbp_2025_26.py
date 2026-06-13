"""Pull NCAA 2025-26 play-by-play from sportsdataverse hoopR-mbb-data.

Same source as the player_box pull. The PBP parquet has every action (FGA, FGM,
AST recipients via 'assisting' player_id, fouls, blocks, steals, etc.) — the
substrate we need for prospect-level advanced metrics.

Output:
    C:/NCAA D1 Mens/data/raw/play_by_play_2026.parquet
    summary printed (rows, columns, sample for one prospect)
"""
from __future__ import annotations
import sys, urllib.request, time
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import pandas as pd

UA = "NCAA-D1-Research/1.0 (research; mr.nathanhumphrey@gmail.com)"
SEASON = 2026
URL = f"https://raw.githubusercontent.com/sportsdataverse/hoopR-mbb-data/main/mbb/pbp/parquet/play_by_play_{SEASON}.parquet"
LOCAL = Path(f"C:/NCAA D1 Mens/data/raw/play_by_play_{SEASON}.parquet")


def main():
    LOCAL.parent.mkdir(parents=True, exist_ok=True)
    if LOCAL.exists() and LOCAL.stat().st_size > 1000:
        print(f"  cached: {LOCAL.name} ({LOCAL.stat().st_size:,} bytes)")
    else:
        print(f"=== fetching {URL} ===")
        req = urllib.request.Request(URL, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=240) as r:
            data = r.read()
        LOCAL.write_bytes(data)
        print(f"  downloaded: {LOCAL.name} ({len(data):,} bytes)")
        time.sleep(1)

    pbp = pd.read_parquet(LOCAL)
    print(f"\n  rows: {len(pbp):,}")
    print(f"  cols: {pbp.columns.tolist()[:30]}")
    print()
    print(f"  date range: {pbp['game_date'].min()} -> {pbp['game_date'].max()}" if 'game_date' in pbp.columns else "")
    print(f"  unique games: {pbp['game_id'].nunique() if 'game_id' in pbp.columns else 'no game_id'}")
    print(f"  unique players (athlete_id_1): {pbp['athlete_id_1'].nunique() if 'athlete_id_1' in pbp.columns else 'no athlete_id_1'}")
    print()
    print("=== sample row ===")
    print(pbp.head(1).T.to_string())

    if 'type_text' in pbp.columns:
        print("\n=== top 30 type_text values ===")
        print(pbp['type_text'].value_counts().head(30).to_string())


if __name__ == "__main__":
    main()
