"""rookies_master.parquet — extends rookie_career_prior with NBA Year-1 outcome.

Builds the spine table for the full rookie decomp set. Pre-NBA features (combine,
NCAA/intl per-40 stats, draft slot) joined with first NBA season totals as the
Year-1 outcome target.

Outputs:
    data/parquet/rookies_master.parquet  (one row per nba_api_id w/ pre-NBA + NBA Y1/Y2/Y3)

Coverage: 2014-2024 draft years (where pre-NBA priors exist).
"""
from __future__ import annotations
import sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

PQ = Path("D:/NBA Projections/data/parquet")
OUT = PQ / "rookies_master.parquet"


def first_n_seasons(career: pd.DataFrame, n: int = 3) -> pd.DataFrame:
    """For each player_id, return wide table of first N NBA regular-season totals."""
    c = career[career["league_id"] == "00"].copy()
    c["season_start_year"] = c["season_id"].str[:4].astype(int)
    c = c.sort_values(["player_id", "season_start_year"])
    c["season_idx"] = c.groupby("player_id").cumcount() + 1
    c = c[c["season_idx"] <= n]

    keep_stats = ["gp", "gs", "min", "fgm", "fga", "fg_pct", "fg3m", "fg3a", "fg3_pct",
                       "ftm", "fta", "ft_pct", "oreb", "dreb", "reb", "ast", "stl",
                       "blk", "tov", "pf", "pts", "player_age"]
    keep_stats = [s for s in keep_stats if s in c.columns]

    pieces = []
    for i in range(1, n + 1):
        sub = c[c["season_idx"] == i][["player_id"] + keep_stats].copy()
        sub.columns = ["nba_api_id"] + [f"nba_y{i}_{s}" for s in keep_stats]
        if i == 1:
            sub_season = c[c["season_idx"] == 1][["player_id", "season_id", "season_start_year"]]
            sub_season.columns = ["nba_api_id", "rookie_season_id", "rookie_season_start"]
            sub = sub.merge(sub_season, on="nba_api_id", how="left")
        pieces.append(sub)

    out = pieces[0]
    for p in pieces[1:]:
        out = out.merge(p, on="nba_api_id", how="left")
    return out


def add_per36(df: pd.DataFrame, year_label: str) -> pd.DataFrame:
    mn = df.get(f"nba_{year_label}_min")
    if mn is None:
        return df
    for stat in ["pts", "reb", "ast", "stl", "blk", "tov", "fgm", "fga", "fg3m", "fg3a", "ftm", "fta", "oreb", "dreb"]:
        col = f"nba_{year_label}_{stat}"
        if col in df.columns:
            df[f"nba_{year_label}_{stat}_per36"] = (df[col] / mn.replace(0, np.nan)) * 36.0
    gp = df.get(f"nba_{year_label}_gp")
    if gp is not None:
        for stat in ["pts", "reb", "ast", "stl", "blk", "tov"]:
            col = f"nba_{year_label}_{stat}"
            if col in df.columns:
                df[f"nba_{year_label}_{stat}_pg"] = df[col] / gp.replace(0, np.nan)
        df[f"nba_{year_label}_mpg"] = df[f"nba_{year_label}_min"] / gp.replace(0, np.nan)
    return df


def main():
    print("=== loading ===")
    rc = pd.read_parquet(PQ / "rookie_career_prior.parquet")
    career = pd.read_parquet(PQ / "player_career_season_totals_rs.parquet")
    draft = pd.read_parquet(PQ / "nba_draft_data.parquet")
    combine = pd.read_parquet(PQ / "nba_combine_measurables.parquet")
    ncaa_full = pd.read_parquet(PQ / "ncaa_to_nba_rookie_join.parquet")
    intl_full = pd.read_parquet(PQ / "international_to_nba_rookie_join.parquet")
    print(f"  rookie_career_prior: {len(rc):,}")
    print(f"  career season totals: {len(career):,}")
    print(f"  draft: {len(draft):,}, combine: {len(combine):,}, ncaa: {len(ncaa_full):,}, intl: {len(intl_full):,}")

    nba_y = first_n_seasons(career, n=3)
    for lbl in ["y1", "y2", "y3"]:
        nba_y = add_per36(nba_y, lbl)
    print(f"  NBA-Y1-Y3 wide: {len(nba_y):,} unique players")

    rc["nba_api_id"] = pd.to_numeric(rc["nba_api_id"], errors="coerce").astype("Int64")
    rc = rc.dropna(subset=["nba_api_id"])

    draft = draft.dropna(subset=["nba_api_id"]).copy()
    draft["nba_api_id"] = draft["nba_api_id"].astype("Int64")
    draft_keep = ["nba_api_id", "draft_pick", "draft_round", "draft_year",
                       "drafted_by_team", "player_name_raw", "pre_nba_team", "pre_nba_team_type"]
    draft_keep = [c for c in draft_keep if c in draft.columns]
    draft_sub = draft[draft_keep].drop_duplicates("nba_api_id", keep="last")

    combine = combine.dropna(subset=["nba_api_id"]).copy()
    combine["nba_api_id"] = combine["nba_api_id"].astype("Int64")
    comb_keep = ["nba_api_id", "position",
                       "height_no_shoes_inches", "height_with_shoes_inches", "weight_lbs",
                       "wingspan_inches", "standing_reach_inches", "body_fat_pct",
                       "hand_length_inches", "hand_width_inches",
                       "standing_vertical_inches", "max_vertical_inches",
                       "lane_agility_seconds", "modified_lane_agility_seconds",
                       "three_quarter_sprint_seconds", "bench_press_reps"]
    comb_keep = [c for c in comb_keep if c in combine.columns]
    combine_sub = combine[comb_keep].drop_duplicates("nba_api_id", keep="last").rename(
        columns={c: f"combine_{c}" for c in comb_keep if c != "nba_api_id"})

    ncaa_full = ncaa_full.dropna(subset=["nba_api_id"]).copy()
    ncaa_full["nba_api_id"] = ncaa_full["nba_api_id"].astype("Int64")
    ncaa_full = ncaa_full.drop_duplicates("nba_api_id", keep="last")
    ncaa_cols = [c for c in ncaa_full.columns if c != "nba_api_id" and c != "player_name_raw"]
    ncaa_sub = ncaa_full[["nba_api_id"] + ncaa_cols].rename(columns={c: f"ncaa_{c}" for c in ncaa_cols})

    intl_full = intl_full.dropna(subset=["nba_api_id"]).copy()
    intl_full["nba_api_id"] = intl_full["nba_api_id"].astype("Int64")
    intl_full = intl_full.drop_duplicates("nba_api_id", keep="last")
    intl_cols = [c for c in intl_full.columns if c != "nba_api_id"]
    intl_sub = intl_full[["nba_api_id"] + intl_cols].rename(columns={c: f"intl_{c}" for c in intl_cols})

    nba_y["nba_api_id"] = nba_y["nba_api_id"].astype("Int64")

    out = draft_sub.merge(combine_sub, on="nba_api_id", how="left")
    out = out.merge(ncaa_sub, on="nba_api_id", how="left")
    out = out.merge(intl_sub, on="nba_api_id", how="left")
    out = out.merge(nba_y, on="nba_api_id", how="left")

    out["has_ncaa"] = out.filter(like="ncaa_").notna().any(axis=1)
    out["has_intl"] = out.filter(like="intl_").notna().any(axis=1)
    out["has_combine"] = out.filter(like="combine_").notna().any(axis=1)
    out["has_nba_y1"] = out["nba_y1_gp"].notna() if "nba_y1_gp" in out.columns else False
    out["has_nba_y2"] = out["nba_y2_gp"].notna() if "nba_y2_gp" in out.columns else False
    out["has_nba_y3"] = out["nba_y3_gp"].notna() if "nba_y3_gp" in out.columns else False

    if "draft_year" in out.columns:
        out["draft_year"] = pd.to_numeric(out["draft_year"], errors="coerce")

    out.to_parquet(OUT, index=False)
    print(f"\nwrote: {OUT}")
    print(f"  rows: {len(out):,}")
    print(f"  cols: {len(out.columns)}")
    print(f"  has_ncaa:    {int(out['has_ncaa'].sum()):>4}")
    print(f"  has_intl:    {int(out['has_intl'].sum()):>4}")
    print(f"  has_combine: {int(out['has_combine'].sum()):>4}")
    print(f"  has_nba_y1:  {int(out['has_nba_y1'].sum()):>4}")
    print(f"  has_nba_y2:  {int(out['has_nba_y2'].sum()):>4}")
    print(f"  has_nba_y3:  {int(out['has_nba_y3'].sum()):>4}")

    print("\n=== draft-year coverage ===")
    print(out.groupby("draft_year").agg(
        n=("nba_api_id", "count"),
        ncaa=("has_ncaa", "sum"),
        intl=("has_intl", "sum"),
        combine=("has_combine", "sum"),
        y1=("has_nba_y1", "sum"),
        y2=("has_nba_y2", "sum"),
        y3=("has_nba_y3", "sum"),
    ).to_string())


if __name__ == "__main__":
    main()
