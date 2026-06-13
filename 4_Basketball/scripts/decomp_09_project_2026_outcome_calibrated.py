"""Apply outcome-calibrated GBM models to the 2026 draft pool.

For each prospect:
  - Look up pre-NBA league label (NCAA conf → tier, intl supplement → mapped)
  - Look up position bucket + age proxy from class year or default 20
  - Predict each Y1 stat + mpg + gp + draft_pick

Surface:
  - Tier band (Lottery 1-14 / Mid-1st 15-30 / Early-2nd 31-45 / Late-2nd 46-60 / Undrafted)
  - Delta vs hand-built composite rank (the disagreement signal)

Outputs:
    data/parquet/draft_2026_outcome_calibrated.parquet
    docs/DRAFT_PREP_2026_OUTCOME_CALIBRATED.md
"""
from __future__ import annotations
import sys, warnings
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb

PQ = Path("D:/NBA Projections/data/parquet")
MODELS = Path("D:/NBA Projections/data/models")
DOCS = Path("D:/NBA Projections/docs")
OUT = PQ / "draft_2026_outcome_calibrated.parquet"
DOC = DOCS / "DRAFT_PREP_2026_OUTCOME_CALIBRATED.md"

NUMERIC_FEATS = ["ppg_pre", "rpg_pre", "apg_pre", "spg_pre", "bpg_pre", "tov_pre", "fg3m_pre",
                                "fg_pct_pre", "fg3_pct_pre", "ft_pct_pre", "pre_nba_age"]
CAT_FEATS = ["pre_nba_league_label", "position_bucket"]

CONF_P5 = {"ACC", "Big Ten", "Big 12", "SEC", "Pac-12", "Big East"}
CONF_MID = {"AAC", "American Athletic", "MWC", "Mountain West", "A-10", "Atlantic 10",
                       "WCC", "West Coast", "CUSA", "Conference USA", "MAC", "Mid-American",
                       "MVC", "Missouri Valley", "Sun Belt", "Horizon"}

INTL_LEAGUE_TO_BUCKET = {
    "Germany BBL": "intl_g_league",
    "NBL Australia": "intl_g_league",
    "ABA League": "intl_g_league",
    "ACB Spain": "unknown",
}


def conf_tier(c):
    if pd.isna(c): return None
    s = str(c)
    if s in CONF_P5: return "P5"
    if s in CONF_MID: return "MID"
    return "LOW"


def position_bucket(p):
    if p is None or (isinstance(p, float) and np.isnan(p)): return "UNK"
    s = str(p).upper()
    if s in ("C", "PF/C"): return "B"
    if s in ("PF",) or "PF" in s: return "B"
    if s in ("SF", "PF") or "F" in s and "G" not in s: return "W"
    if "G" in s: return "G"
    return "UNK"


def tier(pick):
    if pd.isna(pick): return "Undrafted"
    p = float(pick)
    if p <= 14: return "Lottery"
    if p <= 30: return "Mid-1st"
    if p <= 45: return "Early-2nd"
    if p <= 60: return "Late-2nd"
    return "Undrafted"


def main():
    pool = pd.read_parquet(PQ / "draft_2026_candidate_pool.parquet")
    proj_hand = pd.read_parquet(PQ / "draft_2026_projections.parquet")
    sup = pd.read_parquet(PQ / "draft_2026_intl_supplement.parquet")
    ncaa = pd.read_parquet(PQ / "ncaa_player_seasons.parquet")
    gl = pd.read_csv("C:/NCAA D1 Mens/data/processed/player_game_logs.csv",
                                usecols=["player_slug", "team", "season"]).drop_duplicates(["player_slug", "season"])

    sup_lookup = sup.set_index("player_name")[["league", "height_cm"]].to_dict("index")

    school_to_conf = {}
    for _, r in ncaa.dropna(subset=["school", "school_conference"]).iterrows():
        school_to_conf[r["school"]] = r["school_conference"]

    pool = pool.copy()

    def rename_intl_stats(row):
        for s, lbl in [("pts_per40", "ppg_pre"), ("reb_per40", "rpg_pre"),
                                  ("ast_per40", "apg_pre"), ("stl_per40", "spg_pre"),
                                  ("blk_per40", "bpg_pre"), ("tov_per40", "tov_pre"),
                                  ("fg3m_per40", "fg3m_pre"), ("fg_pct", "fg_pct_pre"),
                                  ("fg3_pct", "fg3_pct_pre"), ("ft_pct", "ft_pct_pre")]:
            ncaa_c = f"ncaa_{s}"
            intl_c = f"intl_{s}"
            val = np.nan
            if ncaa_c in row.index and pd.notna(row.get(ncaa_c)):
                val = row[ncaa_c]
            elif intl_c in row.index and pd.notna(row.get(intl_c)):
                val = row[intl_c]
            row[lbl] = val
        return row
    pool = pool.apply(rename_intl_stats, axis=1)

    def school_lookup(row):
        name = row.get("ncaa_match_name")
        if pd.isna(name) or not name: return None
        match = ncaa[ncaa["player_name_raw"] == name]
        if not len(match): return None
        latest = match.sort_values("ncaa_season").iloc[-1]
        return latest.get("school_conference")
    pool["pre_nba_conference"] = pool.apply(school_lookup, axis=1)
    pool["pre_nba_conf_tier"] = pool["pre_nba_conference"].apply(conf_tier)

    def label_league(row):
        if pd.notna(row.get("pre_nba_conf_tier")):
            return f"NCAA_{row['pre_nba_conf_tier']}"
        if row.get("has_intl"):
            intl_lg = sup_lookup.get(row["player_name"], {}).get("league")
            if intl_lg and intl_lg in INTL_LEAGUE_TO_BUCKET:
                return INTL_LEAGUE_TO_BUCKET[intl_lg]
            return "intl_g_league"
        return "NCAA_P5"
    pool["pre_nba_league_label"] = pool.apply(label_league, axis=1)

    pool["pre_nba_age"] = 19.0
    pool.loc[pool["ncaa_n_seasons"] >= 2, "pre_nba_age"] = 20.0
    pool.loc[pool["ncaa_n_seasons"] >= 3, "pre_nba_age"] = 21.0
    pool.loc[pool["ncaa_n_seasons"] >= 4, "pre_nba_age"] = 22.0
    pool.loc[pool["has_intl"] == True, "pre_nba_age"] = 19.0

    pool["position_bucket"] = pool["position"].apply(position_bucket)

    for c in CAT_FEATS:
        pool[c] = pool[c].fillna("unknown").astype(str)

    print("\n=== feature distributions for 2026 pool ===")
    print(pool["pre_nba_league_label"].value_counts().to_string())
    print()
    print(pool["position_bucket"].value_counts().to_string())
    print()

    pred_targets = [
        "nba_y1_pts_per36", "nba_y1_reb_per36", "nba_y1_ast_per36",
        "nba_y1_stl_per36", "nba_y1_blk_per36", "nba_y1_fg3m_per36",
        "nba_y1_tov_per36", "nba_y1_mpg", "nba_y1_gp", "draft_pick",
    ]
    for tgt in pred_targets:
        mp = MODELS / f"outcome_gbm_{tgt}.txt"
        if not mp.exists():
            continue
        model = lgb.Booster(model_file=str(mp))
        X = pool[NUMERIC_FEATS + CAT_FEATS].copy()
        for c in CAT_FEATS:
            X[c] = X[c].astype("category")
        pool[f"oc_{tgt}"] = model.predict(X)

    pool["oc_tier"] = pool["oc_draft_pick"].apply(tier)
    pool["oc_value"] = (
        pool["oc_nba_y1_pts_per36"].fillna(0)
        + pool["oc_nba_y1_reb_per36"].fillna(0)
        + pool["oc_nba_y1_ast_per36"].fillna(0) * 1.5
        + pool["oc_nba_y1_stl_per36"].fillna(0) * 2.0
        + pool["oc_nba_y1_blk_per36"].fillna(0) * 2.0
        + pool["oc_nba_y1_fg3m_per36"].fillna(0) * 0.5
        - pool["oc_nba_y1_tov_per36"].fillna(0)
    ) * (pool["oc_nba_y1_mpg"].fillna(0) / 36.0) * 65
    pool["oc_rank"] = pool["oc_value"].rank(ascending=False, method="dense").astype(int)
    pool["oc_pick_rank"] = pool["oc_draft_pick"].rank(ascending=True, method="dense").astype(int)

    hand = proj_hand[["player_name", "rank", "projected_y1_value", "archetype",
                                    "nearest_comp_1", "nearest_comp_2"]].copy()
    hand.columns = ["player_name", "hand_rank", "hand_value", "archetype", "comp1", "comp2"]
    out = pool[["player_name", "position", "pre_nba_league_label", "pre_nba_conf_tier",
                    "pre_nba_age", "position_bucket",
                    "oc_draft_pick", "oc_pick_rank", "oc_tier", "oc_value", "oc_rank",
                    "oc_nba_y1_pts_per36", "oc_nba_y1_reb_per36", "oc_nba_y1_ast_per36",
                    "oc_nba_y1_blk_per36", "oc_nba_y1_mpg", "oc_nba_y1_gp"]].copy()
    out = out.merge(hand, on="player_name", how="left")
    out["rank_delta"] = out["hand_rank"] - out["oc_rank"]

    out = out.sort_values("oc_rank").reset_index(drop=True)
    out.to_parquet(OUT, index=False)
    out.to_csv(OUT.with_suffix(".csv"), index=False)
    print(f"\nwrote: {OUT}")

    print("\n=== TIER BAND DISTRIBUTION ===")
    print(out["oc_tier"].value_counts().to_string())

    cols_show = ["oc_rank", "player_name", "position", "pre_nba_league_label", "archetype",
                  "oc_tier", "oc_draft_pick", "oc_nba_y1_mpg", "oc_nba_y1_pts_per36",
                  "hand_rank", "rank_delta"]
    print("\n=== TOP 30 by outcome-calibrated rank ===")
    print(out[cols_show].head(30).round(2).to_string(index=False))

    print("\n=== BIGGEST RANK GAPS — hand vs outcome (sorted by |delta|) ===")
    out["abs_delta"] = out["rank_delta"].abs()
    gaps = out.sort_values("abs_delta", ascending=False).head(20)
    print(gaps[["player_name", "position", "pre_nba_league_label", "archetype",
                       "hand_rank", "oc_rank", "rank_delta", "oc_tier", "comp1"]].round(0).to_string(index=False))


if __name__ == "__main__":
    main()
