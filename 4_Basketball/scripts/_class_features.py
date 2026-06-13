"""Canonical attach_class_features for residual-class diagnostics.

Centralized 2026-05-02 to fix two bugs:
  1. draft_pick was being fetched from nba_draft_data.parquet (2014-2025 only),
     bucketing pre-2014 vets as "undrafted." Now uses metadata's draft_pick
     (populated for all players via CommonPlayerInfo, with 0 = nba_api's
     "undrafted" sentinel).
  2. years_pro = target_year - draft_year produced years_pro=2023 for
     truly-undrafted players (draft_year=0), falling outside pd.cut's bin
     range and creating a spurious NaN bucket. Now uses metadata's
     debut_year, which is populated for all players including undrafted.

Class features attached:
  - position           (from metadata)
  - age                (from birth_date, snapped to target_year-10-24)
  - age_bucket         (<=24, 25-26, 27-29, 30-32, 33+)
  - years_pro          (target_year - debut_year)
  - years_pro_bucket   (rookie, 1-3, 4-7, 8-12, 13+)
  - draft_pick         (from metadata; 0 = undrafted)
  - draft_pick_tier    (top5, lottery, late_first, second, undrafted)
  - team_for_season    (modal team in box scores for the season)
  - new_coach_this_season  (from coaching_change_flags)
  - mid_season_change  (from coaching_change_flags)
  - offseason_traded   (from pro_sports_transactions, Apr 15 - Oct 24 of target_year)
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

PQ = Path("data") / "parquet"


def _pick_bucket(p):
    if pd.isna(p):
        return "undrafted"
    p = int(p)
    if p == 0:
        return "undrafted"          # nba_api's sentinel for undrafted
    if p <= 5:
        return "top5"
    if p <= 14:
        return "lottery"
    if p <= 30:
        return "late_first"
    return "second"


def attach_class_features(df: pd.DataFrame, target_year: int) -> pd.DataFrame:
    """Attach all residual-class features to df. Returns a new DataFrame.

    df must have an `nba_api_id` column. target_year is the season-start year
    (e.g. 2023 for the 2023-24 season).
    """
    meta = pd.read_parquet(PQ / "player_metadata_enriched.parquet")
    df = df.merge(meta[["nba_api_id", "position", "birth_date",
                          "draft_year", "draft_pick", "debut_year"]],
                  on="nba_api_id", how="left")

    # Age + age bucket
    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
    df["age"] = (pd.Timestamp(f"{target_year}-10-24") - df["birth_date"]).dt.days / 365.25
    df["age_bucket"] = pd.cut(df["age"], bins=[0, 24, 27, 30, 33, 50],
                                labels=["<=24", "25-26", "27-29", "30-32", "33+"]).astype(str)

    # Years pro from debut_year (handles undrafted correctly)
    df["years_pro"] = target_year - df["debut_year"]
    df["years_pro_bucket"] = pd.cut(df["years_pro"], bins=[-1, 0, 3, 7, 12, 30],
                                      labels=["rookie", "1-3", "4-7", "8-12", "13+"]).astype(str)

    # Draft pick tier (uses metadata's draft_pick — covers all 1529 players)
    df["draft_pick_tier"] = df["draft_pick"].apply(_pick_bucket)

    # Modal team for season (used to join coaching change flags)
    box = pd.read_parquet(PQ / "historical_box_scores.parquet")
    box["nba_api_id"] = box["nba_api_id"].astype(int)
    season_label = f"{target_year}-{str(target_year+1)[2:]}"
    s = box[box["season"] == season_label]
    if len(s) > 0:
        team = s.groupby("nba_api_id")["team_abbr"].agg(
            lambda x: x.value_counts().idxmax()).reset_index()
        team.columns = ["nba_api_id", "team_for_season"]
        df = df.merge(team, on="nba_api_id", how="left")
    else:
        df["team_for_season"] = pd.NA

    # Coaching changes
    cf = pd.read_parquet(PQ / "coaching_change_flags.parquet")
    cf_s = cf[cf["season"] == season_label][["team_abbr", "new_coach_this_season",
                                                "mid_season_change"]]
    df = df.merge(cf_s, left_on="team_for_season", right_on="team_abbr",
                   how="left", suffixes=("", "_cf"))
    df["new_coach_this_season"] = df["new_coach_this_season"].fillna(False).astype(bool)
    df["mid_season_change"] = df["mid_season_change"].fillna(False).astype(bool)

    # Offseason trades
    tx = pd.read_parquet(PQ / "pro_sports_transactions.parquet")
    tx["event_date"] = pd.to_datetime(tx["event_date"])
    if "transaction_type" in tx.columns:
        traded = set(tx[(tx["transaction_type"] == "trade") &
                        (tx["event_date"] >= pd.Timestamp(f"{target_year}-04-15")) &
                        (tx["event_date"] <= pd.Timestamp(f"{target_year}-10-24")) &
                        (tx["nba_api_id"].notna())]["nba_api_id"].astype(int))
        df["offseason_traded"] = df["nba_api_id"].astype(int).isin(traded)
    else:
        df["offseason_traded"] = False

    return df
