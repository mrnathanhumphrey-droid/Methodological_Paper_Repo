"""Re-fetch NBA combine for 2025 + 2026 to populate measurements.

The cached combine_all_time.parquet has 71 2026 invitees w/ PLAYER_ID + POSITION
but all measurement fields NaN (invitee list was published before combine ran).
The combine ran mid-May 2026; measurements should be live on NBA Stats API by now.

Strategy: pull season-specific combine for 2024-25 AND 2025-26 (the 2025 + 2026
draft classes), then merge into combine_all_time.parquet.
"""
from __future__ import annotations
import sys, time
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import pandas as pd
from nba_api.stats.endpoints import draftcombinestats

OUT = Path("D:/NBA Projections/data/raw/draft/combine_all_time.parquet")


def fetch_season(season_label: str) -> pd.DataFrame:
    print(f"  fetching combine for {season_label}...")
    d = draftcombinestats.DraftCombineStats(season_all_time=season_label, timeout=60)
    df = d.get_data_frames()[0]
    print(f"    -> {len(df)} rows; measurements populated: HEIGHT_WO={df['HEIGHT_WO_SHOES'].notna().sum()}, WINGSPAN={df['WINGSPAN'].notna().sum()}")
    time.sleep(1.0)
    return df


def main():
    existing = pd.read_parquet(OUT)
    print(f"  existing rows: {len(existing)}  seasons covered: {sorted(existing['SEASON'].dropna().unique())[-5:]}")

    new_frames = []
    for season in ["2024-25", "2025-26"]:
        try:
            df = fetch_season(season)
            new_frames.append(df)
        except Exception as e:
            print(f"  ERR {season}: {str(e)[:120]}")

    if not new_frames:
        print("\n  no new data fetched. aborting.")
        return

    fresh = pd.concat(new_frames, ignore_index=True)
    print(f"\n  fresh fetched rows: {len(fresh)}")

    drop_seasons = set(fresh["SEASON"].dropna().unique())
    print(f"  dropping cached rows for seasons: {drop_seasons}")
    kept = existing[~existing["SEASON"].isin(drop_seasons)]
    merged = pd.concat([kept, fresh], ignore_index=True)
    print(f"  merged total rows: {len(merged)}")

    merged.to_parquet(OUT, index=False)
    print(f"  wrote: {OUT}")

    s26 = merged[merged["SEASON"] == "2025-26"]
    print(f"\n=== 2025-26 combine (the 2026 draft class) ===")
    print(f"  rows: {len(s26)}")
    print(f"  measurements populated: HEIGHT_WO={s26['HEIGHT_WO_SHOES'].notna().sum()}, "
              f"WINGSPAN={s26['WINGSPAN'].notna().sum()}, "
              f"MAX_VERT={s26['MAX_VERTICAL_LEAP'].notna().sum()}")
    if len(s26) > 0 and s26["HEIGHT_WO_SHOES"].notna().any():
        sample = s26[s26["HEIGHT_WO_SHOES"].notna()][["PLAYER_NAME", "POSITION",
                                                                                 "HEIGHT_WO_SHOES",
                                                                                 "WINGSPAN", "STANDING_REACH",
                                                                                 "MAX_VERTICAL_LEAP"]].head(15)
        print(sample.to_string(index=False))


if __name__ == "__main__":
    main()
