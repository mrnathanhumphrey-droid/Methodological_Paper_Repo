"""Scrape 2025-26 NCAA player_box from sportsdataverse hoopR-mbb-data.

Mirrors C:/NCAA D1 Mens/src/build_player_game_logs.py pattern. Single bulk parquet
fetch from github raw, transformed to the player_game_logs.csv schema, appended
to the existing CSV.

After this lands, the 21 unmatched 2026 invitees (Dybantsa / Peterson / Peat /
Yessoufou / Boozer / Burries / Cenac / Acuff / etc.) should have NCAA 2025-26
freshman/soph stats available.
"""
from __future__ import annotations
import sys, time, urllib.request
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import pandas as pd
import numpy as np

UA = "NCAA-D1-Research/1.0 (research; mr.nathanhumphrey@gmail.com)"
SEASON = 2026
URL = f"https://raw.githubusercontent.com/sportsdataverse/hoopR-mbb-data/main/mbb/player_box/parquet/player_box_{SEASON}.parquet"
LOCAL_RAW = Path(f"C:/NCAA D1 Mens/data/raw/player_box_{SEASON}.parquet")
PGL = Path("C:/NCAA D1 Mens/data/processed/player_game_logs.csv")


def minutes_to_mmss(m):
    if pd.isna(m): return ""
    total_seconds = int(round(float(m) * 60))
    mm, ss = divmod(total_seconds, 60)
    return f"{mm}:{ss:02d}"


def safe_div(n, d):
    return np.where((d.notna()) & (d != 0), n / d, np.nan)


def transform(df):
    df = df[df["season_type"].isin({2, 3})].copy()
    out = pd.DataFrame()
    out["team"] = df["team_location"]
    out["player"] = df["athlete_display_name"]
    out["player_slug"] = df["athlete_id"].apply(lambda x: str(int(x)) if pd.notna(x) else "")
    out["mp"] = df["minutes"].apply(minutes_to_mmss)
    out["fg"] = df["field_goals_made"]
    out["fga"] = df["field_goals_attempted"]
    out["fg_pct"] = safe_div(out["fg"], out["fga"])
    out["fg3"] = df["three_point_field_goals_made"]
    out["fg3a"] = df["three_point_field_goals_attempted"]
    out["fg3_pct"] = safe_div(out["fg3"], out["fg3a"])
    out["ft"] = df["free_throws_made"]
    out["fta"] = df["free_throws_attempted"]
    out["ft_pct"] = safe_div(out["ft"], out["fta"])
    out["orb"] = df["offensive_rebounds"]
    out["drb"] = df["defensive_rebounds"]
    out["trb"] = df["rebounds"]
    out["ast"] = df["assists"]
    out["stl"] = df["steals"]
    out["blk"] = df["blocks"]
    out["tov"] = df["turnovers"]
    out["pf"] = df["fouls"]
    out["pts"] = df["points"]
    out["plus_minus"] = np.nan
    out["game_id"] = df["game_id"]
    out["game_date"] = df["game_date"]
    out["season"] = df["season"]
    out["season_type"] = df["season_type"].map({2: "Regular Season", 3: "Postseason"})
    out["pts_calc"] = 2 * (df["field_goals_made"] - df["three_point_field_goals_made"]) + 3 * df["three_point_field_goals_made"] + df["free_throws_made"]
    out["mp_minutes"] = pd.to_numeric(df["minutes"], errors="coerce")
    return out


def main():
    LOCAL_RAW.parent.mkdir(parents=True, exist_ok=True)

    print(f"=== fetching {URL} ===")
    if LOCAL_RAW.exists() and LOCAL_RAW.stat().st_size > 1000:
        print(f"  cached: {LOCAL_RAW.name} ({LOCAL_RAW.stat().st_size:,} bytes)")
    else:
        req = urllib.request.Request(URL, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=180) as r:
            data = r.read()
        LOCAL_RAW.write_bytes(data)
        print(f"  downloaded: {LOCAL_RAW.name} ({len(data):,} bytes)")
        time.sleep(1)

    raw = pd.read_parquet(LOCAL_RAW)
    print(f"  raw rows: {len(raw):,}")
    print(f"  season distribution: {raw['season'].value_counts().to_dict()}")

    out = transform(raw)
    print(f"\n  transformed rows: {len(out):,}")
    print(f"  unique players: {out['player_slug'].nunique():,}")
    print(f"  date range: {out['game_date'].min()} -> {out['game_date'].max()}")
    print(f"  season_type: {out['season_type'].value_counts().to_dict()}")

    print(f"\n=== merging into {PGL} ===")
    existing = pd.read_csv(PGL)
    print(f"  existing rows: {len(existing):,} (seasons: {sorted(existing['season'].unique())})")
    existing = existing[existing["season"] != SEASON]
    print(f"  after dropping any existing season {SEASON}: {len(existing):,}")
    merged = pd.concat([existing, out], ignore_index=True)
    print(f"  merged rows: {len(merged):,}")

    merged.to_csv(PGL, index=False)
    print(f"  wrote: {PGL}")

    s26 = merged[merged["season"] == SEASON]
    print(f"\n=== 2025-26 season summary ===")
    print(f"  rows: {len(s26):,}")
    print(f"  unique players: {s26['player_slug'].nunique():,}")
    print(f"  unique teams: {s26['team'].nunique()}")

    print("\n  top scorers (sum pts ÷ gp) 2025-26:")
    top = s26.groupby(["player_slug", "player"]).agg(gp=("pts", "size"), pts_sum=("pts", "sum")).reset_index()
    top["ppg"] = top["pts_sum"] / top["gp"]
    print(top.sort_values("pts_sum", ascending=False).head(15)[["player", "gp", "ppg"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
