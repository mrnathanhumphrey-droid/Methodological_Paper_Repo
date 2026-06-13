"""Re-project 2026 pool with v2 outcome GBM (proper intl league buckets).

Same as decomp_09 but uses outcome_gbm_v2_*.txt models and maps 2026 intl
prospects to specific league buckets (not "unknown" or "intl_g_league" catch-all).

Outputs:
    data/parquet/draft_2026_outcome_calibrated_v2.parquet
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
OUT = PQ / "draft_2026_outcome_calibrated_v2.parquet"

NUMERIC_FEATS = ["ppg_pre", "rpg_pre", "apg_pre", "spg_pre", "bpg_pre", "tov_pre", "fg3m_pre",
                                "fg_pct_pre", "fg3_pct_pre", "ft_pct_pre", "pre_nba_age"]
CAT_FEATS = ["pre_nba_league_label", "position_bucket"]

CONF_P5 = {"ACC", "Big Ten", "Big 12", "SEC", "Pac-12", "Big East"}
CONF_MID = {"AAC", "American Athletic", "MWC", "Mountain West", "A-10", "Atlantic 10",
                       "WCC", "West Coast", "CUSA", "Conference USA", "MAC", "Mid-American",
                       "MVC", "Missouri Valley", "Sun Belt", "Horizon"}

INTL_LEAGUE_TO_V2_BUCKET = {
    "Germany BBL": "intl_bbl_germany",
    "NBL Australia": "intl_nbl_australia",
    "ABA League": "intl_kls_serbia",
    "ACB Spain": "intl_acb_spain",
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
    if s in ("C", "PF/C") or "C" in s and "F" not in s: return "B"
    if s in ("PF",) or "PF" in s: return "B"
    if "F" in s and "G" not in s: return "W"
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
    pool = pd.read_parquet(PQ / "draft_2026_candidate_pool.parquet").copy()
    proj_v1 = pd.read_parquet(PQ / "draft_2026_outcome_calibrated.parquet")
    proj_hand = pd.read_parquet(PQ / "draft_2026_projections.parquet")
    sup = pd.read_parquet(PQ / "draft_2026_intl_supplement.parquet")
    ncaa = pd.read_parquet(PQ / "ncaa_player_seasons.parquet")
    sup_lookup = sup.set_index("player_name")["league"].to_dict()

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
        return match.sort_values("ncaa_season").iloc[-1].get("school_conference")
    pool["pre_nba_conference"] = pool.apply(school_lookup, axis=1)
    pool["pre_nba_conf_tier"] = pool["pre_nba_conference"].apply(conf_tier)

    def label_league_v2(row):
        if pd.notna(row.get("pre_nba_conf_tier")):
            return f"NCAA_{row['pre_nba_conf_tier']}"
        if row.get("has_intl"):
            intl_lg = sup_lookup.get(row["player_name"])
            if intl_lg and intl_lg in INTL_LEAGUE_TO_V2_BUCKET:
                return INTL_LEAGUE_TO_V2_BUCKET[intl_lg]
            return "intl_g_league"
        return "NCAA_P5"
    pool["pre_nba_league_label"] = pool.apply(label_league_v2, axis=1)

    pool["pre_nba_age"] = 19.0
    pool.loc[pool["ncaa_n_seasons"] >= 2, "pre_nba_age"] = 20.0
    pool.loc[pool["ncaa_n_seasons"] >= 3, "pre_nba_age"] = 21.0
    pool.loc[pool["ncaa_n_seasons"] >= 4, "pre_nba_age"] = 22.0
    pool.loc[pool["has_intl"] == True, "pre_nba_age"] = 19.0
    pool["position_bucket"] = pool["position"].apply(position_bucket)

    for c in CAT_FEATS:
        pool[c] = pool[c].fillna("unknown").astype(str)

    print("=== 2026 pool league_label_v2 distribution ===")
    print(pool["pre_nba_league_label"].value_counts().to_string())
    print()

    targets = ["nba_y1_pts_per36", "nba_y1_reb_per36", "nba_y1_ast_per36",
                       "nba_y1_stl_per36", "nba_y1_blk_per36", "nba_y1_fg3m_per36",
                       "nba_y1_tov_per36", "nba_y1_mpg", "nba_y1_gp", "draft_pick"]
    for tgt in targets:
        mp = MODELS / f"outcome_gbm_v2_{tgt}.txt"
        if not mp.exists():
            continue
        model = lgb.Booster(model_file=str(mp))
        X = pool[NUMERIC_FEATS + CAT_FEATS].copy()
        for c in CAT_FEATS:
            X[c] = X[c].astype("category")
        pool[f"oc2_{tgt}"] = model.predict(X)

    pool["oc2_tier"] = pool["oc2_draft_pick"].apply(tier)
    pool["oc2_value"] = (
        pool["oc2_nba_y1_pts_per36"].fillna(0)
        + pool["oc2_nba_y1_reb_per36"].fillna(0)
        + pool["oc2_nba_y1_ast_per36"].fillna(0) * 1.5
        + pool["oc2_nba_y1_stl_per36"].fillna(0) * 2.0
        + pool["oc2_nba_y1_blk_per36"].fillna(0) * 2.0
        + pool["oc2_nba_y1_fg3m_per36"].fillna(0) * 0.5
        - pool["oc2_nba_y1_tov_per36"].fillna(0)
    ) * (pool["oc2_nba_y1_mpg"].fillna(0) / 36.0) * 65
    pool["oc2_rank"] = pool["oc2_value"].rank(ascending=False, method="dense").astype(int)
    pool["oc2_pick_rank"] = pool["oc2_draft_pick"].rank(ascending=True, method="dense").astype(int)

    v1_lookup = proj_v1[["player_name", "oc_rank", "oc_draft_pick", "oc_tier"]].rename(
        columns={"oc_rank": "v1_rank", "oc_draft_pick": "v1_pick", "oc_tier": "v1_tier"})
    hand = proj_hand[["player_name", "rank", "archetype",
                                    "nearest_comp_1"]].rename(columns={"rank": "hand_rank"})
    out = pool[["player_name", "position", "pre_nba_league_label", "pre_nba_conf_tier",
                    "oc2_draft_pick", "oc2_pick_rank", "oc2_tier", "oc2_value", "oc2_rank",
                    "oc2_nba_y1_pts_per36", "oc2_nba_y1_reb_per36", "oc2_nba_y1_ast_per36",
                    "oc2_nba_y1_blk_per36", "oc2_nba_y1_mpg"]].copy()
    out = out.merge(v1_lookup, on="player_name", how="left")
    out = out.merge(hand, on="player_name", how="left")
    out["v1_to_v2_delta"] = out["v1_rank"] - out["oc2_rank"]

    eff_v2 = pd.read_parquet(PQ / "rookies_outcome_gbm_v2_league_effects.parquet")
    pick_baseline = eff_v2[eff_v2["target"] == "draft_pick"][["league", "mean_actual"]].rename(
        columns={"league": "pre_nba_league_label", "mean_actual": "league_baseline_pick"})
    pick_n = eff_v2[eff_v2["target"] == "draft_pick"][["league", "n"]].rename(
        columns={"league": "pre_nba_league_label", "n": "league_n"})
    out = out.merge(pick_baseline, on="pre_nba_league_label", how="left")
    out = out.merge(pick_n, on="pre_nba_league_label", how="left")
    out["survivorship_signal"] = out["league_baseline_pick"] - out["oc2_draft_pick"]

    out = out.sort_values("oc2_rank").reset_index(drop=True)
    out.to_parquet(OUT, index=False)
    out.to_csv(OUT.with_suffix(".csv"), index=False)
    print(f"wrote: {OUT}")

    print("\n=== V2 TIER BAND DIST ===")
    print(out["oc2_tier"].value_counts().to_string())

    print("\n=== V1 vs V2 — intl 4 with survivorship-baseline diagnostic ===")
    intl4 = out[out["player_name"].isin(["Sergio De Larrea", "Jack Kayil", "Karim Lopez", "Luigi Suigo"])]
    print(intl4[["player_name", "pre_nba_league_label", "league_n", "league_baseline_pick",
                       "oc2_draft_pick", "survivorship_signal", "oc2_rank", "oc2_tier",
                       "hand_rank"]].round(2).to_string(index=False))

    print("\n=== TOP 20 SURVIVORSHIP SIGNALS (prospects where model predicts much earlier pick than league baseline) ===")
    print(out.dropna(subset=["survivorship_signal"]).sort_values(
        "survivorship_signal", ascending=False).head(20)[
            ["player_name", "pre_nba_league_label", "league_n", "league_baseline_pick",
                "oc2_draft_pick", "survivorship_signal", "oc2_rank"]].round(2).to_string(index=False))

    print("\n=== TOP 15 v2 board ===")
    print(out.head(15)[["oc2_rank", "player_name", "position", "pre_nba_league_label",
                            "archetype", "oc2_tier", "oc2_draft_pick", "oc2_nba_y1_mpg",
                            "oc2_nba_y1_pts_per36", "hand_rank", "v1_rank"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
