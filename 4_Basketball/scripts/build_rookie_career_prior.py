"""Build unified rookie career-prior table.

Joins draft + NCAA + international + combine + preseason boxes per nba_api_id.
Slots into v6 architecture as the "career data" position for rookies (parallel
to player_career_season_totals_rs for veterans).

Output:
    data/parquet/rookie_career_prior.parquet

One row per nba_api_id. Source columns prefixed:
    draft_*    from nba_draft_data
    ncaa_*     from ncaa_to_nba_rookie_join
    intl_*     from international_to_nba_rookie_join
    combine_*  from nba_combine_measurables
    preseason_* aggregated from preseason_player_boxes (rookie-year preseason)
"""
from __future__ import annotations

import sys
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(".")
PQ = REPO / "data" / "parquet"
OUT_PATH = PQ / "rookie_career_prior.parquet"


def main():
    print("Loading source parquets...")
    draft = pd.read_parquet(PQ / "nba_draft_data.parquet")
    ncaa = pd.read_parquet(PQ / "ncaa_to_nba_rookie_join.parquet")
    intl = pd.read_parquet(PQ / "international_to_nba_rookie_join.parquet")
    combine = pd.read_parquet(PQ / "nba_combine_measurables.parquet")
    preseason = pd.read_parquet(PQ / "preseason_player_boxes.parquet")

    print(f"  draft:     {len(draft):>6} rows")
    print(f"  ncaa:      {len(ncaa):>6} rows")
    print(f"  intl:      {len(intl):>6} rows")
    print(f"  combine:   {len(combine):>6} rows")
    print(f"  preseason: {len(preseason):>6} rows")

    # ---- Spine: draft data, restricted to rows with resolved nba_api_id
    spine = draft.dropna(subset=["nba_api_id"]).copy()
    spine["nba_api_id"] = spine["nba_api_id"].astype(int)
    spine = spine.rename(columns={
        "draft_pick": "draft_pick",
        "draft_year": "draft_year",
        "draft_round": "draft_round",
        "drafted_by_team": "draft_team",
        "player_name_raw": "draft_player_name_raw",
        "pre_nba_team": "draft_pre_nba_team",
        "pre_nba_team_type": "draft_pre_nba_team_type",
    })[["nba_api_id", "draft_player_name_raw", "draft_year", "draft_round",
         "draft_pick", "draft_team", "draft_pre_nba_team", "draft_pre_nba_team_type"]]

    # Some rookies (undrafted) won't be in nba_draft_data. Add them later from
    # the union of NCAA/intl/combine ids that aren't already in the spine.
    pre_undrafted_ids = set(spine["nba_api_id"])

    extra_ids = (
        set(ncaa["nba_api_id"].dropna().astype(int))
        | set(intl["nba_api_id"].dropna().astype(int))
        | set(combine["nba_api_id"].dropna().astype(int))
    ) - pre_undrafted_ids
    if extra_ids:
        print(f"  + {len(extra_ids)} undrafted/missing-from-draft ids added to spine")
        extra = pd.DataFrame({
            "nba_api_id": sorted(extra_ids),
            "draft_player_name_raw": pd.NA,
            "draft_year": pd.NA,
            "draft_round": pd.NA,
            "draft_pick": pd.NA,
            "draft_team": pd.NA,
            "draft_pre_nba_team": pd.NA,
            "draft_pre_nba_team_type": pd.NA,
        })
        spine = pd.concat([spine, extra], ignore_index=True)

    print(f"  spine: {len(spine)} rows")

    # ---- NCAA join (prefix ncaa_)
    ncaa = ncaa.dropna(subset=["nba_api_id"]).copy()
    ncaa["nba_api_id"] = ncaa["nba_api_id"].astype(int)
    ncaa_keep = [
        "nba_api_id", "ncaa_school", "ncaa_last_season", "ncaa_class_at_draft",
        "years_in_college", "gp", "mpg",
        "pts_pg", "reb_pg", "ast_pg", "stl_pg", "blk_pg", "tov_pg",
        "fgm_pg", "fga_pg", "fg3m_pg", "fg3a_pg", "ftm_pg", "fta_pg",
        "fg_pct", "fg3_pct", "ft_pct",
        "pts_per40", "reb_per40", "ast_per40", "stl_per40", "blk_per40",
        "tov_per40", "fgm_per40", "fga_per40",
    ]
    ncaa_keep = [c for c in ncaa_keep if c in ncaa.columns]
    ncaa_sub = ncaa[ncaa_keep].copy()
    rename_map = {c: f"ncaa_{c}" for c in ncaa_sub.columns if c != "nba_api_id"
                  and not c.startswith("ncaa_")}
    ncaa_sub = ncaa_sub.rename(columns=rename_map)
    # NCAA join may have multiple rows per id (rare); keep last_season row
    if ncaa_sub["nba_api_id"].duplicated().any():
        if "ncaa_ncaa_last_season" in ncaa_sub.columns:
            ncaa_sub = ncaa_sub.sort_values("ncaa_ncaa_last_season").groupby(
                "nba_api_id", as_index=False).last()
        else:
            ncaa_sub = ncaa_sub.drop_duplicates(subset=["nba_api_id"], keep="last")

    # ---- International join (prefix intl_)
    intl = intl.dropna(subset=["nba_api_id"]).copy()
    intl["nba_api_id"] = intl["nba_api_id"].astype(int)
    intl_keep = ["nba_api_id", "league", "last_pre_nba_season", "last_team",
                 "years_pre_nba", "gp", "mpg",
                 "pts_per40", "reb_per40", "ast_per40", "stl_per40", "blk_per40",
                 "tov_per40", "fg3m_per40", "fg_pct", "fg3_pct", "ft_pct"]
    intl_keep = [c for c in intl_keep if c in intl.columns]
    intl_sub = intl[intl_keep].copy()
    intl_sub = intl_sub.rename(columns={c: f"intl_{c}" for c in intl_sub.columns
                                         if c != "nba_api_id"})
    if intl_sub["nba_api_id"].duplicated().any():
        intl_sub = intl_sub.sort_values("intl_last_pre_nba_season").groupby(
            "nba_api_id", as_index=False).last()

    # ---- Combine join (prefix combine_)
    combine = combine.dropna(subset=["nba_api_id"]).copy()
    combine["nba_api_id"] = combine["nba_api_id"].astype(int)
    combine_keep = [
        "nba_api_id", "position",
        "height_no_shoes_inches", "height_with_shoes_inches", "weight_lbs",
        "wingspan_inches", "standing_reach_inches", "body_fat_pct",
        "hand_length_inches", "hand_width_inches",
        "standing_vertical_inches", "max_vertical_inches",
        "lane_agility_seconds", "modified_lane_agility_seconds",
        "three_quarter_sprint_seconds", "bench_press_reps",
    ]
    combine_keep = [c for c in combine_keep if c in combine.columns]
    combine_sub = combine[combine_keep].copy()
    combine_sub = combine_sub.rename(columns={c: f"combine_{c}" for c in combine_sub.columns
                                                if c != "nba_api_id"})
    combine_sub = combine_sub.drop_duplicates(subset=["nba_api_id"], keep="last")

    # ---- Preseason aggregation (player-rookie-year preseason boxes)
    # For each player, find their FIRST NBA preseason (= rookie-year preseason),
    # then aggregate gp/mpg/per-game stats.
    print("\nAggregating preseason boxes...")
    pre = preseason.copy()
    pre["player_id"] = pd.to_numeric(pre["player_id"], errors="coerce")
    pre = pre.dropna(subset=["player_id"])
    pre["player_id"] = pre["player_id"].astype(int)
    # Convert mins
    def parse_min(x):
        if pd.isna(x): return np.nan
        s = str(x)
        if ":" in s:
            try:
                a, b = s.split(":")
                return float(a) + float(b) / 60.0
            except Exception:
                return np.nan
        try:
            return float(s)
        except Exception:
            return np.nan
    pre["min_num"] = pre["min"].apply(parse_min)

    # Find each player's first NBA preseason (= rookie year)
    first_pre_season = pre.groupby("player_id")["season"].min().reset_index()
    first_pre_season.columns = ["player_id", "rookie_preseason"]
    pre_rookie = pre.merge(first_pre_season, on="player_id")
    pre_rookie = pre_rookie[pre_rookie["season"] == pre_rookie["rookie_preseason"]]

    # Aggregate
    agg_cols = ["min_num", "fgm", "fga", "fg3m", "fg3a", "ftm", "fta",
                "oreb", "dreb", "reb", "ast", "stl", "blk", "to", "pf", "pts"]
    agg_cols = [c for c in agg_cols if c in pre_rookie.columns]
    agg = pre_rookie.groupby("player_id").agg(
        preseason_rookie_year=("rookie_preseason", "first"),
        preseason_gp=("game_id", "nunique"),
        **{c: (c, "sum") for c in agg_cols},
    ).reset_index()

    # Per-game derivations
    if "preseason_gp" in agg.columns:
        for stat in ["pts", "reb", "ast", "stl", "blk", "to", "fgm", "fga",
                     "fg3m", "fg3a", "ftm", "fta", "min_num"]:
            if stat in agg.columns:
                pg = agg[stat] / agg["preseason_gp"].replace(0, np.nan)
                agg[f"preseason_{stat}_pg"] = pg
    if "fgm" in agg.columns and "fga" in agg.columns:
        agg["preseason_fg_pct"] = agg["fgm"] / agg["fga"].replace(0, np.nan)
    if "fg3m" in agg.columns and "fg3a" in agg.columns:
        agg["preseason_fg3_pct"] = agg["fg3m"] / agg["fg3a"].replace(0, np.nan)
    if "ftm" in agg.columns and "fta" in agg.columns:
        agg["preseason_ft_pct"] = agg["ftm"] / agg["fta"].replace(0, np.nan)

    # Drop raw sums to keep the table tidy; keep mpg + pg + pcts
    keep_cols = ["player_id", "preseason_rookie_year", "preseason_gp",
                 "preseason_min_num_pg",
                 "preseason_pts_pg", "preseason_reb_pg", "preseason_ast_pg",
                 "preseason_stl_pg", "preseason_blk_pg", "preseason_to_pg",
                 "preseason_fgm_pg", "preseason_fga_pg",
                 "preseason_fg3m_pg", "preseason_fg3a_pg",
                 "preseason_ftm_pg", "preseason_fta_pg",
                 "preseason_fg_pct", "preseason_fg3_pct", "preseason_ft_pct"]
    keep_cols = [c for c in keep_cols if c in agg.columns]
    pre_agg = agg[keep_cols].copy()
    pre_agg = pre_agg.rename(columns={
        "player_id": "nba_api_id",
        "preseason_min_num_pg": "preseason_mpg",
    })

    # ---- Merge everything onto spine
    print("\nMerging onto spine...")
    out = spine.copy()
    out = out.merge(ncaa_sub, on="nba_api_id", how="left")
    out = out.merge(intl_sub, on="nba_api_id", how="left")
    out = out.merge(combine_sub, on="nba_api_id", how="left")
    out = out.merge(pre_agg, on="nba_api_id", how="left")

    # Per-source coverage flags
    out["has_ncaa"] = out["ncaa_gp"].notna() if "ncaa_gp" in out.columns else False
    out["has_intl"] = out["intl_gp"].notna() if "intl_gp" in out.columns else False
    out["has_combine"] = out["combine_position"].notna() if "combine_position" in out.columns else False
    out["has_preseason"] = out["preseason_gp"].notna() if "preseason_gp" in out.columns else False
    out["has_any_prior"] = out["has_ncaa"] | out["has_intl"]

    print(f"\nUnified table: {len(out)} rows")
    print(f"  NCAA prior:      {int(out['has_ncaa'].sum()):>4}")
    print(f"  Intl prior:      {int(out['has_intl'].sum()):>4}")
    print(f"  Combine data:    {int(out['has_combine'].sum()):>4}")
    print(f"  Preseason data:  {int(out['has_preseason'].sum()):>4}")
    print(f"  Any career-prior: {int(out['has_any_prior'].sum()):>4}")
    print(f"  No prior at all:  {int((~out['has_any_prior']).sum()):>4}")

    # Spot-checks
    print("\n=== Spot-checks ===")
    # Wemby (ID 1641705)
    for label, pid in [("Wembanyama", 1641705), ("Holmgren", 1631096),
                       ("Scoot Henderson", 1641705)]:  # we'll fix Scoot below
        pass
    # Look up by name in spine
    spine_with_meta = out
    for name in ["Wembanyama", "Holmgren", "Scoot Henderson", "LaMelo",
                 "Edey", "Sarr", "Wagner"]:
        # use draft_player_name_raw (may have encoding issue) and a fuzzy contains
        m = spine_with_meta[
            spine_with_meta["draft_player_name_raw"].astype(str)
            .str.lower().str.contains(name.lower(), na=False)
        ]
        if len(m) == 0:
            print(f"  {name}: not found in draft data (encoding?)")
            continue
        r = m.iloc[0]
        print(f"  {r['draft_player_name_raw']!s:<30} draft={r['draft_year']} "
              f"pick={r['draft_pick']} pre_team={r['draft_pre_nba_team']} "
              f"ncaa={'Y' if r['has_ncaa'] else '-'} intl={'Y' if r['has_intl'] else '-'} "
              f"combine={'Y' if r['has_combine'] else '-'} preseason={'Y' if r['has_preseason'] else '-'}")

    # Save
    out.to_parquet(OUT_PATH, index=False)
    print(f"\nSaved -> {OUT_PATH}")
    print(f"  cols: {len(out.columns)}")


if __name__ == "__main__":
    main()
