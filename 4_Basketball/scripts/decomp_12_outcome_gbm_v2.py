"""Refit outcome-calibrated GBM with v2 league labels (real intl buckets).

Same architecture as decomp_08 but consumes rookies_outcome_training_v2.parquet
which has proper intl league categoricals (acb_spain, nbl_australia, etc.).

Outputs:
    data/models/outcome_gbm_v2_<target>.txt
    data/parquet/rookies_outcome_gbm_v2_league_effects.parquet
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
LEAGUE_OUT = PQ / "rookies_outcome_gbm_v2_league_effects.parquet"

NUMERIC_FEATS = ["ppg_pre", "rpg_pre", "apg_pre", "spg_pre", "bpg_pre", "tov_pre", "fg3m_pre",
                                "fg_pct_pre", "fg3_pct_pre", "ft_pct_pre", "pre_nba_age"]
CAT_FEATS = ["pre_nba_league_label", "position_bucket"]

TARGETS = [
    ("nba_y1_pts_per36", 25),
    ("nba_y1_reb_per36", 25),
    ("nba_y1_ast_per36", 25),
    ("nba_y1_stl_per36", 25),
    ("nba_y1_blk_per36", 25),
    ("nba_y1_fg3m_per36", 25),
    ("nba_y1_tov_per36", 25),
    ("nba_y1_mpg", 25),
    ("nba_y1_gp", 0),
    ("draft_pick", 0),
]

HOLDOUT_YEARS = {2023, 2024}


def main():
    df = pd.read_parquet(PQ / "rookies_outcome_training_v2.parquet")
    print(f"  training set v2: {len(df):,}")
    print(f"  league distribution:")
    print(df["pre_nba_league_label"].value_counts().to_string())
    print()

    for c in CAT_FEATS:
        df[c] = df[c].fillna("unknown").astype(str).astype("category")

    league_rows = []
    for target, min_gp in TARGETS:
        if target not in df.columns:
            continue
        sub = df.dropna(subset=[target]).copy()
        if min_gp > 0:
            sub = sub[sub.get("nba_y1_gp", 0) >= min_gp]
        if len(sub) < 100:
            continue

        train = sub[~sub["draft_year"].isin(HOLDOUT_YEARS)].copy()
        test = sub[sub["draft_year"].isin(HOLDOUT_YEARS)].copy()
        if len(train) < 50:
            continue

        X_tr = train[NUMERIC_FEATS + CAT_FEATS]
        y_tr = train[target].astype(float)
        X_te = test[NUMERIC_FEATS + CAT_FEATS]
        y_te = test[target].astype(float)
        X_all = sub[NUMERIC_FEATS + CAT_FEATS]

        dtr = lgb.Dataset(X_tr, y_tr, categorical_feature=CAT_FEATS, free_raw_data=False)
        dval = lgb.Dataset(X_te, y_te, categorical_feature=CAT_FEATS, free_raw_data=False, reference=dtr)
        params = {"objective": "regression", "metric": "rmse",
                          "learning_rate": 0.05, "num_leaves": 16, "min_data_in_leaf": 5,
                          "feature_fraction": 0.85, "bagging_fraction": 0.85, "bagging_freq": 5,
                          "verbose": -1}
        model = lgb.train(params, dtr, num_boost_round=400,
                                            valid_sets=[dtr, dval], valid_names=["train", "test"],
                                            callbacks=[lgb.early_stopping(40), lgb.log_evaluation(0)])

        model_path = MODELS / f"outcome_gbm_v2_{target}.txt"
        model.save_model(str(model_path))

        rmse_te = float(np.sqrt(((model.predict(X_te) - y_te) ** 2).mean()))
        rmse_baseline = float(np.sqrt(((y_te - y_tr.mean()) ** 2).mean()))
        lift = (rmse_baseline - rmse_te) / rmse_baseline * 100.0
        print(f"  {target:<22} test_n={len(test):>3}  RMSE_te={rmse_te:.3f}  baseline={rmse_baseline:.3f}  lift={lift:+.1f}%")

        pred_all = model.predict(X_all)
        for lg in df["pre_nba_league_label"].cat.categories:
            mask = sub["pre_nba_league_label"] == lg
            if mask.sum() < 2:
                continue
            league_rows.append({
                "target": target, "league": lg, "n": int(mask.sum()),
                "mean_actual": float(sub.loc[mask, target].mean()),
                "mean_pred": float(pred_all[mask.values].mean()),
            })

    eff = pd.DataFrame(league_rows)
    eff.to_parquet(LEAGUE_OUT, index=False)
    print(f"\nwrote: {LEAGUE_OUT}")

    print("\n=== V2 LEAGUE EFFECT TABLE — mean actual Y1 outcome by league ===")
    for target in ["nba_y1_pts_per36", "nba_y1_ast_per36", "nba_y1_mpg", "draft_pick"]:
        sub = eff[eff["target"] == target].sort_values(
            "mean_actual", ascending=(target == "draft_pick"))
        if len(sub):
            print(f"\n  {target}:")
            print(sub[["league", "n", "mean_actual", "mean_pred"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
