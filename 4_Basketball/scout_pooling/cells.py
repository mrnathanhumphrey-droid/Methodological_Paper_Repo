"""Cell-assignment per PRE_REG_SCOUTS_v1.md §2.1 and §2.2.

Each prospect (nba_api_id) → (archetype, league) cell pair.

ARCHETYPES (§2.1) — priority order. Each prospect gets the FIRST archetype
they qualify for, falling through to 'general' if none match:
  1. international       — pre_nba_team_type ∈ {non_ncaa, international, intl_other}
  2. one_and_done        — NCAA + year_class=='Fr' + draft_age<19.5
  3. late_bloomer        — NCAA + year_class=='Sr' + BPM lift >2 vs prior season
  4. defensive_specialist — NCAA + (stl_pct + blk_pct) ≥ 6 + usage<22
  5. two_way_wing        — NCAA + height ∈ [76,81] + usage ∈ [18,25] + fg3_pct≥0.34
                           + ast_pct≥12 + (stl_pct+blk_pct)≥4
  6. big_skill_question   — NCAA + height≥81 + fg3a per game ≥ 1.5
  7. combine_athlete     — (max_vert≥38 OR lane_agility≤10.8) + college BPM<6
  8. g_league_ignite     — pre_nba_team_type=='g_league' + draft_age≤20
  9. general             — none of the above

LEAGUES (§2.2) — orthogonal to archetype:
  NCAA_power     — NCAA + conference ∈ {B10, ACC, B12, SEC, BE, P12, P10}
  NCAA_mid_major — NCAA + other conference
  G_League       — pre_nba_team_type=='g_league'
  International  — pre_nba_team_type ∈ {non_ncaa, international, intl_other}
  High_School    — pre_nba_team_type=='high_school'
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DR = Path(r"D:\Draft Resolve\data\parquet")

NCAA_POWER = {"B10", "ACC", "B12", "SEC", "BE", "P12", "P10", "BIG10", "BIG12",
              "Big 10", "Big 12", "Pac 12", "Pac 10", "Big East"}


def load_inputs() -> dict[str, pd.DataFrame]:
    return {
        "universe": pd.read_parquet(DR / "prospect_universe.parquet"),
        "outcome": pd.read_parquet(DR / "draft_outcome.parquet"),
        "join": pd.read_parquet(DR / "prospect_pre_draft_join.parquet"),
        "bt": pd.read_parquet(DR / "pre_draft_record.parquet"),
        "combine": pd.read_parquet(DR / "combine_record.parquet"),
        "gleague": pd.read_parquet(DR / "pre_draft_gleague.parquet"),
    }


def _last_pre_draft_bt(join: pd.DataFrame, bt: pd.DataFrame) -> pd.DataFrame:
    """One row per joined prospect: latest pre-draft Bart Torvik season."""
    j = join.merge(bt, left_on="bt_player_id", right_on="bt_player_id", how="inner",
                    suffixes=("_join", "_bt"))
    j = j.sort_values(["nba_api_id", "year"]).drop_duplicates("nba_api_id", keep="last")
    return j


def _bpm_lift(join: pd.DataFrame, bt: pd.DataFrame) -> pd.Series:
    """Senior-year BPM lift over prior season per prospect (NaN if missing)."""
    j = join.merge(bt, on="bt_player_id", how="inner", suffixes=("", "_bt"))
    j = j.sort_values(["nba_api_id", "year"])
    j["prev_bpm"] = j.groupby("nba_api_id")["bpm"].shift(1)
    last = j.drop_duplicates("nba_api_id", keep="last")
    lift = last["bpm"] - last["prev_bpm"]
    return pd.Series(lift.values, index=last["nba_api_id"].values)


def assign(df_inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    universe = df_inputs["universe"].copy()
    outcome = df_inputs["outcome"]
    join = df_inputs["join"]
    bt = df_inputs["bt"]
    combine = df_inputs["combine"]

    bt_last = _last_pre_draft_bt(join, bt)
    bpm_lift = _bpm_lift(join, bt)

    universe = universe.merge(
        outcome[["nba_api_id", "pre_nba_team_type"]].drop_duplicates("nba_api_id"),
        on="nba_api_id", how="left",
    )
    universe = universe.merge(
        bt_last[["nba_api_id", "year_class", "conference", "usage", "fg3_pct",
                  "fg3a", "ast_pct", "stl_pct", "blk_pct", "bpm", "gp"]],
        on="nba_api_id", how="left",
    )
    universe = universe.merge(
        combine[["nba_api_id", "max_vertical_inches", "lane_agility_seconds"]],
        on="nba_api_id", how="left",
    )
    universe["bpm_lift"] = universe["nba_api_id"].map(bpm_lift)

    fg3a_pg = universe["fg3a"] / universe["gp"].clip(lower=1)
    is_ncaa = universe["pre_nba_team_type"].fillna("").isin(["ncaa"])
    is_intl = universe["pre_nba_team_type"].fillna("").isin(
        ["non_ncaa", "international", "intl_other"]
    )
    is_g_league = universe["pre_nba_team_type"].fillna("") == "g_league"
    is_high_school = universe["pre_nba_team_type"].fillna("") == "high_school"

    one_and_done = (is_ncaa & (universe["year_class"] == "Fr") &
                    (universe["draft_age"] < 19.5))
    late_bloomer = (is_ncaa & (universe["year_class"] == "Sr") &
                    (universe["bpm_lift"] > 2.0))
    defensive_specialist = (is_ncaa &
                            ((universe["stl_pct"] + universe["blk_pct"]) >= 6) &
                            (universe["usage"] < 22))
    two_way_wing = (is_ncaa &
                    universe["height_inches"].between(76, 81) &
                    universe["usage"].between(18, 25) &
                    (universe["fg3_pct"] >= 0.34) &
                    (universe["ast_pct"] >= 12) &
                    ((universe["stl_pct"] + universe["blk_pct"]) >= 4))
    big_skill_question = (is_ncaa & (universe["height_inches"] >= 81) &
                          (fg3a_pg >= 1.5))
    combine_athlete = (((universe["max_vertical_inches"] >= 38) |
                       (universe["lane_agility_seconds"] <= 10.8)) &
                       (universe["bpm"] < 6))
    g_league_ignite = is_g_league & (universe["draft_age"] <= 20)

    archetype = pd.Series("general", index=universe.index, dtype="object")
    archetype[is_intl] = "international"
    archetype[one_and_done & (archetype == "general")] = "one_and_done"
    archetype[late_bloomer & (archetype == "general")] = "late_bloomer"
    archetype[defensive_specialist & (archetype == "general")] = "defensive_specialist"
    archetype[two_way_wing & (archetype == "general")] = "two_way_wing"
    archetype[big_skill_question & (archetype == "general")] = "big_skill_question"
    archetype[combine_athlete & (archetype == "general")] = "combine_athlete"
    archetype[g_league_ignite & (archetype == "general")] = "g_league_ignite"
    universe["archetype"] = archetype

    league = pd.Series("Unknown", index=universe.index, dtype="object")
    league[is_intl] = "International"
    league[is_g_league] = "G_League"
    league[is_high_school] = "High_School"
    league[is_ncaa & universe["conference"].isin(NCAA_POWER)] = "NCAA_power"
    league[is_ncaa & ~universe["conference"].isin(NCAA_POWER)] = "NCAA_mid_major"
    universe["league"] = league
    universe["cell"] = universe["archetype"] + "::" + universe["league"]

    return universe[["nba_api_id", "draft_year", "draft_pick", "drafted",
                     "draft_age", "height_inches", "pre_nba_team_type",
                     "year_class", "conference", "usage", "bpm", "bpm_lift",
                     "max_vertical_inches", "lane_agility_seconds",
                     "archetype", "league", "cell"]]


if __name__ == "__main__":
    inputs = load_inputs()
    out = assign(inputs)
    print(f"Cells assigned for {len(out)} prospects")
    print("\nArchetype counts:")
    print(out["archetype"].value_counts().to_string())
    print("\nLeague counts:")
    print(out["league"].value_counts().to_string())
    print("\nCell counts (top 15):")
    print(out["cell"].value_counts().head(15).to_string())
    out_path = Path(__file__).parent / "audit_runs" / "v1" / "prospect_cells.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(out_path, index=False)
    print(f"\nWrote {out_path}")
