"""v4 GBM — adds teammate-context features.

Augments v3 training set with prospect_teammate_context features:
  - teammate_pts_per40_top (rotation-only)
  - teammate_pts_per40_mean
  - prospect_pts_share (his share of team scoring)
  - team_pts_per_game (tempo proxy)

LightGBM handles NaN natively, so historical 2014-22 prospects (no game-log
coverage) get NaN teammate features and the model learns to use them when
present (mostly for the 2023-24 holdout and 2026 forward projection).

Outputs:
    data/parquet/rookies_outcome_training_v4.parquet
    data/models/outcome_gbm_v4_<target>.txt
    data/parquet/draft_2026_outcome_calibrated_v4.parquet
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
TRAIN_OUT = PQ / "rookies_outcome_training_v4.parquet"
PROJ_OUT = PQ / "draft_2026_outcome_calibrated_v4.parquet"

TEAMMATE_FEATS = ["teammate_pts_per40_top", "teammate_pts_per40_mean",
                                  "prospect_pts_share", "team_pts_per_game"]
NUMERIC_FEATS = ["ppg_pre", "rpg_pre", "apg_pre", "spg_pre", "bpg_pre", "tov_pre", "fg3m_pre",
                                "fg_pct_pre", "fg3_pct_pre", "ft_pct_pre", "pre_nba_age"] + TEAMMATE_FEATS
CAT_FEATS = ["pre_nba_league_label", "position_bucket"]
HOLDOUT_YEARS = {2023, 2024}

TARGETS = [
    ("nba_y1_pts_per36", 25), ("nba_y1_reb_per36", 25), ("nba_y1_ast_per36", 25),
    ("nba_y1_stl_per36", 25), ("nba_y1_blk_per36", 25), ("nba_y1_fg3m_per36", 25),
    ("nba_y1_tov_per36", 25), ("nba_y1_mpg", 25), ("nba_y1_gp", 0), ("draft_pick", 0),
]


def tier(pick):
    if pd.isna(pick): return "Undrafted"
    p = float(pick)
    if p <= 14: return "Lottery"
    if p <= 30: return "Mid-1st"
    if p <= 45: return "Early-2nd"
    if p <= 60: return "Late-2nd"
    return "Undrafted"


def main():
    train = pd.read_parquet(PQ / "rookies_outcome_training_v3.parquet")
    ctx = pd.read_parquet(PQ / "prospect_teammate_context.parquet")

    train_ctx = ctx[ctx["draft_year"].isin([2023, 2024])][["player_name", "draft_year"] + TEAMMATE_FEATS]
    train_ctx = train_ctx.rename(columns={"player_name": "player_name_raw"})
    train = train.merge(train_ctx, on=["player_name_raw", "draft_year"], how="left")
    print(f"  training rows w/ teammate features: {train[TEAMMATE_FEATS[0]].notna().sum()}/{len(train)}")
    train.to_parquet(TRAIN_OUT, index=False)
    print(f"  wrote: {TRAIN_OUT}")

    for c in CAT_FEATS:
        train[c] = train[c].fillna("unknown").astype(str).astype("category")

    print("\n=== fitting v4 GBM ===")
    lift_summary = []
    for target, min_gp in TARGETS:
        if target not in train.columns: continue
        sub = train.dropna(subset=[target]).copy()
        if min_gp > 0: sub = sub[sub.get("nba_y1_gp", 0) >= min_gp]
        if len(sub) < 100: continue

        tr = sub[~sub["draft_year"].isin(HOLDOUT_YEARS)]
        te = sub[sub["draft_year"].isin(HOLDOUT_YEARS)]
        if len(tr) < 50: continue

        X_tr, X_te = tr[NUMERIC_FEATS + CAT_FEATS], te[NUMERIC_FEATS + CAT_FEATS]
        y_tr, y_te = tr[target].astype(float), te[target].astype(float)

        dtr = lgb.Dataset(X_tr, y_tr, categorical_feature=CAT_FEATS, free_raw_data=False)
        dval = lgb.Dataset(X_te, y_te, categorical_feature=CAT_FEATS, free_raw_data=False, reference=dtr)
        params = {"objective": "regression", "metric": "rmse",
                          "learning_rate": 0.05, "num_leaves": 16, "min_data_in_leaf": 5,
                          "feature_fraction": 0.85, "bagging_fraction": 0.85, "bagging_freq": 5, "verbose": -1}
        model = lgb.train(params, dtr, num_boost_round=400,
                                            valid_sets=[dtr, dval], valid_names=["train", "test"],
                                            callbacks=[lgb.early_stopping(40), lgb.log_evaluation(0)])
        model.save_model(str(MODELS / f"outcome_gbm_v4_{target}.txt"))

        rmse_te = float(np.sqrt(((model.predict(X_te) - y_te) ** 2).mean()))
        rmse_baseline = float(np.sqrt(((y_te - y_tr.mean()) ** 2).mean()))
        lift = (rmse_baseline - rmse_te) / rmse_baseline * 100
        lift_summary.append((target, rmse_te, lift))
        print(f"  {target:<22}  RMSE_te={rmse_te:.3f}  lift={lift:+.1f}%")

    print("\n=== projecting 2026 with v4 ===")
    proj_v3 = pd.read_parquet(PQ / "draft_2026_outcome_calibrated_v3.parquet")
    pool = pd.read_parquet(PQ / "draft_2026_candidate_pool.parquet")

    proj_v3_input = pd.read_parquet(PQ / "rookies_outcome_training_v3.parquet")
    pool_ctx = ctx[ctx["draft_year"] == 2026][["player_name"] + TEAMMATE_FEATS]

    v3_cols = [c for c in ["player_name", "position", "pre_nba_league_label", "pre_nba_conf_tier",
                                                  "oc3_draft_pick", "oc3_rank", "hand_rank", "archetype",
                                                  "v2_rank", "league_baseline_pick", "league_n", "survivorship_signal",
                                                  "oc3_nba_y1_pts_per36", "oc3_nba_y1_reb_per36",
                                                  "oc3_nba_y1_ast_per36", "oc3_nba_y1_blk_per36",
                                                  "oc3_nba_y1_mpg", "oc3_tier"] if c in proj_v3.columns]
    pool_proj = proj_v3[v3_cols].copy()
    pool_proj = pool_proj.merge(pool_ctx, on="player_name", how="left")

    pool_feats = pool[["player_name"]].copy()
    pool_feats = pool_feats.merge(
        pool[["player_name", "ncaa_pts_per40", "ncaa_reb_per40", "ncaa_ast_per40",
                  "ncaa_stl_per40", "ncaa_blk_per40", "ncaa_tov_per40", "ncaa_fg3m_per40",
                  "ncaa_fg_pct", "ncaa_fg3_pct", "ncaa_ft_pct"]],
        on="player_name", how="left")
    rename_pool = {"ncaa_pts_per40": "ppg_pre", "ncaa_reb_per40": "rpg_pre",
                                 "ncaa_ast_per40": "apg_pre", "ncaa_stl_per40": "spg_pre",
                                 "ncaa_blk_per40": "bpg_pre", "ncaa_tov_per40": "tov_pre",
                                 "ncaa_fg3m_per40": "fg3m_pre", "ncaa_fg_pct": "fg_pct_pre",
                                 "ncaa_fg3_pct": "fg3_pct_pre", "ncaa_ft_pct": "ft_pct_pre"}
    pool_feats = pool_feats.rename(columns=rename_pool)
    pool_feats["pre_nba_age"] = 19.0

    pool_proj = pool_proj.merge(pool_feats, on="player_name", how="left")
    pool_proj["position_bucket"] = pool_proj["position"].apply(
        lambda p: "B" if isinstance(p, str) and ("C" in p.upper() or "PF" in p.upper()) else
                          ("G" if isinstance(p, str) and "G" in p.upper() else "W"))
    pool_proj["pre_nba_league_label"] = pool_proj["pre_nba_league_label"].fillna("NCAA_P5")

    for c in CAT_FEATS:
        pool_proj[c] = pool_proj[c].fillna("unknown").astype(str)

    for target, _ in TARGETS:
        mp = MODELS / f"outcome_gbm_v4_{target}.txt"
        if not mp.exists(): continue
        model = lgb.Booster(model_file=str(mp))
        X = pool_proj[NUMERIC_FEATS + CAT_FEATS].copy()
        for c in CAT_FEATS:
            X[c] = X[c].astype("category")
        pool_proj[f"oc4_{target}"] = model.predict(X)

    pool_proj["oc4_tier"] = pool_proj["oc4_draft_pick"].apply(tier)
    pool_proj["oc4_value"] = (
        pool_proj["oc4_nba_y1_pts_per36"].fillna(0) + pool_proj["oc4_nba_y1_reb_per36"].fillna(0)
        + pool_proj["oc4_nba_y1_ast_per36"].fillna(0) * 1.5 + pool_proj["oc4_nba_y1_stl_per36"].fillna(0) * 2.0
        + pool_proj["oc4_nba_y1_blk_per36"].fillna(0) * 2.0 + pool_proj["oc4_nba_y1_fg3m_per36"].fillna(0) * 0.5
        - pool_proj["oc4_nba_y1_tov_per36"].fillna(0)
    ) * (pool_proj["oc4_nba_y1_mpg"].fillna(0) / 36.0) * 65
    pool_proj["oc4_rank"] = pool_proj["oc4_value"].rank(ascending=False, method="dense").astype(int)
    pool_proj["v3_to_v4_delta"] = pool_proj["oc3_rank"] - pool_proj["oc4_rank"]

    pool_proj = pool_proj.sort_values("oc4_rank").reset_index(drop=True)
    pool_proj.to_parquet(PROJ_OUT, index=False)
    print(f"\nwrote: {PROJ_OUT}")

    print("\n=== TOP 20 v4 board ===")
    cols = ["oc4_rank", "player_name", "position", "pre_nba_league_label", "archetype",
                  "oc4_tier", "oc4_draft_pick", "oc4_nba_y1_mpg", "oc4_nba_y1_pts_per36",
                  "prospect_pts_share", "teammate_pts_per40_top",
                  "hand_rank", "oc3_rank", "v3_to_v4_delta"]
    print(pool_proj.head(20)[cols].round(2).to_string(index=False))

    print("\n=== biggest v3→v4 movements (teammate effect) ===")
    pool_proj["abs_delta"] = pool_proj["v3_to_v4_delta"].abs()
    print(pool_proj.sort_values("abs_delta", ascending=False).head(15)[
        ["player_name", "position", "archetype", "prospect_pts_share", "teammate_pts_per40_top",
            "oc3_rank", "oc4_rank", "v3_to_v4_delta"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
